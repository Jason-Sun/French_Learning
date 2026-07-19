#!/usr/bin/env python3
"""Audit a CEFR graph scope and its integrity without inventing missing content.

This is a release audit for the current production lexical scope.  It measures
the graph as built, so importer-level POS reconciliation reports cannot be
mistaken for missing Language Objects.  A missing source-backed sense remains
an explicit coverage gap; this script never fills one.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


DEFAULT_LEVELS = ("A1", "A2", "B1", "B2")
VALID_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}


def count(database: sqlite3.Connection, query: str, params: tuple = ()) -> int:
    return database.execute(query, params).fetchone()[0]


def rows(database: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict]:
    return [dict(row) for row in database.execute(query, params)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--levels", nargs="+", default=DEFAULT_LEVELS, choices=sorted(VALID_LEVELS))
    args = parser.parse_args()
    levels = tuple(args.levels)
    placeholders = ",".join("?" for _ in levels)

    database = sqlite3.connect(args.database)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys=ON")

    scoped_words = f"""
        FROM language_objects AS word
        JOIN canonical_objects AS canonical ON canonical.language_object_id = word.id
        WHERE word.type_code = 'word' AND word.cefr_level IN ({placeholders})
    """
    words_with_senses = f"""
        SELECT COUNT(DISTINCT word.id) {scoped_words}
          AND EXISTS (
            SELECT 1 FROM lexical_senses AS sense
            WHERE sense.owner_canonical_id = canonical.canonical_id
          )
    """
    missing_sense_rows = f"""
        SELECT word.canonical_form AS lemma,
               word.part_of_speech,
               word.cefr_level
        {scoped_words}
          AND NOT EXISTS (
            SELECT 1 FROM lexical_senses AS sense
            WHERE sense.owner_canonical_id = canonical.canonical_id
          )
        ORDER BY word.cefr_level, word.canonical_form, word.part_of_speech
    """
    linked_forms = f"""
        SELECT COUNT(DISTINCT form.id)
        FROM language_objects AS form
        JOIN relationships AS relation
          ON relation.source_object_id = form.id
         AND relation.relationship_type_code = 'inflected_form_of'
        JOIN language_objects AS lemma ON lemma.id = relation.target_object_id
        WHERE form.type_code = 'inflected_form'
          AND lemma.type_code = 'word'
          AND lemma.cefr_level IN ({placeholders})
    """
    source_edge_checks = {
        "lexique_inflected_form_edges": count(
            database,
            """SELECT COUNT(*) FROM (
                 SELECT relation.id FROM relationships AS relation
                 JOIN language_objects AS form ON form.id = relation.source_object_id
                 LEFT JOIN relationship_evidence AS evidence ON evidence.relationship_id = relation.id
                 WHERE form.source_id = 'lexique383'
                   AND relation.relationship_type_code = 'inflected_form_of'
                 GROUP BY relation.id HAVING COUNT(evidence.source_record_id) = 0
               )""",
        ),
        "kaikki_sense_edges": count(
            database,
            """SELECT COUNT(*) FROM (
                 SELECT relation.id FROM relationships AS relation
                 JOIN language_objects AS sense ON sense.id = relation.target_object_id
                 LEFT JOIN relationship_evidence AS evidence ON evidence.relationship_id = relation.id
                 WHERE sense.source_id = 'kaikki-enwiktionary'
                   AND relation.relationship_type_code = 'has_sense'
                 GROUP BY relation.id HAVING COUNT(evidence.source_record_id) = 0
               )""",
        ),
        "french_wiktionary_sense_edges": count(
            database,
            """SELECT COUNT(*) FROM (
                 SELECT relation.id FROM relationships AS relation
                 JOIN language_objects AS sense ON sense.id = relation.target_object_id
                 LEFT JOIN relationship_evidence AS evidence ON evidence.relationship_id = relation.id
                 WHERE sense.source_id = 'kartmaan-french-dictionary'
                   AND relation.relationship_type_code = 'has_sense'
                 GROUP BY relation.id HAVING COUNT(evidence.source_record_id) = 0
               )""",
        ),
        "kaikki_sentence_edges": count(
            database,
            """SELECT COUNT(*) FROM (
                 SELECT relation.id FROM relationships AS relation
                 JOIN language_objects AS sentence ON sentence.id = relation.source_object_id
                 LEFT JOIN relationship_evidence AS evidence ON evidence.relationship_id = relation.id
                 WHERE sentence.source_id = 'kaikki-enwiktionary'
                   AND relation.relationship_type_code = 'illustrates'
                 GROUP BY relation.id HAVING COUNT(evidence.source_record_id) = 0
               )""",
        ),
    }
    integrity = {
        "foreign_key_violations": len(rows(database, "PRAGMA foreign_key_check")),
        "orphaned_objects": count(
            database,
            """SELECT COUNT(*) FROM language_objects AS object
               WHERE object.type_code NOT IN ('collection', 'review_item')
                 AND NOT EXISTS (
                   SELECT 1 FROM canonical_objects AS canonical
                   WHERE canonical.language_object_id = object.id
                 )""",
        ),
        "orphaned_facts": count(
            database,
            """SELECT COUNT(*) FROM canonical_facts AS fact
               WHERE NOT EXISTS (
                 SELECT 1 FROM canonical_objects AS canonical
                 WHERE canonical.canonical_id = fact.canonical_subject_id
               )""",
        ),
        "orphaned_relationships": count(
            database,
            """SELECT COUNT(*) FROM relationships AS relation
               WHERE NOT EXISTS (
                 SELECT 1 FROM language_objects AS source WHERE source.id = relation.source_object_id
               ) OR NOT EXISTS (
                 SELECT 1 FROM language_objects AS target WHERE target.id = relation.target_object_id
               )""",
        ),
        "source_backed_edges_without_evidence": source_edge_checks,
    }
    missing_senses = rows(database, missing_sense_rows, levels)
    word_count = count(database, f"SELECT COUNT(*) {scoped_words}", levels)
    word_count_with_senses = count(database, words_with_senses, levels)
    scalar_integrity_failures = sum(
        value for key, value in integrity.items() if key != "source_backed_edges_without_evidence"
    )
    source_edge_failures = sum(source_edge_checks.values())
    report = {
        "audit": f"{'-'.join(levels)} production graph coverage",
        "database": str(args.database),
        "scope": {"cefr_levels": list(levels)},
        "coverage": {
            "word_pos_objects": word_count,
            "word_pos_objects_with_source_backed_senses": word_count_with_senses,
            "word_pos_objects_without_source_backed_senses": len(missing_senses),
            "source_backed_sense_coverage_percent": round(100 * word_count_with_senses / word_count, 2),
            "source_backed_inflected_forms_linked_to_scope": count(database, linked_forms, levels),
            "missing_source_backed_sense_objects": missing_senses,
        },
        "integrity": integrity,
        "result": {
            "passed": scalar_integrity_failures == 0 and source_edge_failures == 0,
            "integrity_failure_count": scalar_integrity_failures + source_edge_failures,
            "coverage_gaps_are_explicit": True,
            "no_llm_canonical_data": True,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            report["result"]
            | {
                key: value
                for key, value in report["coverage"].items()
                if key != "missing_source_backed_sense_objects"
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
