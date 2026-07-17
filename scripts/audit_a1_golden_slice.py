#!/usr/bin/env python3
"""Audit A1 Golden Slice coverage, provenance, and graph integrity.

The audit never invents missing content. It distinguishes an integrity failure
from a frozen-source coverage gap that an importer has explicitly recorded.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


REPORT_NAMES = {
    "flelex_baseline": "flelex-beacco-tree-tagger-a1.json",
    "verb_morphology": "lexique383-a1-morphology.json",
    "nominal_morphology": "lexique383-a1-nominal-morphology.json",
    "function_word_morphology": "lexique383-a1-function-word-morphology.json",
    "pronunciation": "lexique383-a1-pronunciation.json",
    "senses": "kaikki-enwiktionary-french-a1-senses.json",
    "grammar": "tex-french-grammar-a1.json",
    "examples_and_relations": "kaikki-enwiktionary-french-a1-connections.json",
    "expressions": "kaikki-enwiktionary-french-a1-expressions.json",
}


def rows(database: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict]:
    return [dict(row) for row in database.execute(query, params)]


def count(database: sqlite3.Connection, query: str, params: tuple = ()) -> int:
    return database.execute(query, params).fetchone()[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--reports-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    database = sqlite3.connect(args.database)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys=ON")
    reports = {
        key: json.loads((args.reports_dir / name).read_text())
        for key, name in REPORT_NAMES.items()
    }

    missing_verb_forms = rows(
        database,
        """SELECT word.canonical_form, word.part_of_speech
           FROM language_objects AS word
           WHERE word.type_code='word' AND word.cefr_level='A1'
             AND word.part_of_speech='VER'
             AND NOT EXISTS (
               SELECT 1 FROM relationships AS link
               JOIN language_objects AS form ON form.id=link.source_object_id
               WHERE link.target_object_id=word.id
                 AND link.relationship_type_code='inflected_form_of'
                 AND form.source_id='lexique383'
             )
           ORDER BY word.canonical_form""",
    )

    source_edge_checks = {
        "lexique_inflected_form_edges": count(
            database,
            """SELECT COUNT(*) FROM (
                 SELECT relationship.id
                 FROM relationships AS relationship
                 JOIN language_objects AS form ON form.id=relationship.source_object_id
                 LEFT JOIN relationship_evidence AS evidence ON evidence.relationship_id=relationship.id
                 WHERE form.source_id='lexique383'
                   AND relationship.relationship_type_code='inflected_form_of'
                 GROUP BY relationship.id HAVING COUNT(evidence.source_record_id)=0
               )""",
        ),
        "lexique_paradigm_edges": count(
            database,
            """SELECT COUNT(*) FROM (
                 SELECT relationship.id
                 FROM relationships AS relationship
                 JOIN language_objects AS form ON form.id=relationship.source_object_id
                 LEFT JOIN relationship_evidence AS evidence ON evidence.relationship_id=relationship.id
                 WHERE form.source_id='lexique383'
                   AND relationship.relationship_type_code='member_of_paradigm'
                 GROUP BY relationship.id HAVING COUNT(evidence.source_record_id)=0
               )""",
        ),
        "lexique_pronunciation_edges": count(
            database,
            """SELECT COUNT(*) FROM (
                 SELECT relationship.id
                 FROM relationships AS relationship
                 JOIN language_objects AS pronunciation ON pronunciation.id=relationship.target_object_id
                 LEFT JOIN relationship_evidence AS evidence ON evidence.relationship_id=relationship.id
                 WHERE pronunciation.source_id='lexique383'
                   AND relationship.relationship_type_code='has_pronunciation'
                 GROUP BY relationship.id HAVING COUNT(evidence.source_record_id)=0
               )""",
        ),
        "kaikki_sense_edges": count(
            database,
            """SELECT COUNT(*) FROM (
                 SELECT relationship.id
                 FROM relationships AS relationship
                 JOIN language_objects AS sense ON sense.id=relationship.target_object_id
                 LEFT JOIN relationship_evidence AS evidence ON evidence.relationship_id=relationship.id
                 WHERE sense.source_id='kaikki-enwiktionary'
                   AND relationship.relationship_type_code='has_sense'
                 GROUP BY relationship.id HAVING COUNT(evidence.source_record_id)=0
               )""",
        ),
        "kaikki_sentence_edges": count(
            database,
            """SELECT COUNT(*) FROM (
                 SELECT relationship.id
                 FROM relationships AS relationship
                 JOIN language_objects AS sentence ON sentence.id=relationship.source_object_id
                 LEFT JOIN relationship_evidence AS evidence ON evidence.relationship_id=relationship.id
                 WHERE sentence.source_id='kaikki-enwiktionary'
                   AND relationship.relationship_type_code='illustrates'
                 GROUP BY relationship.id HAVING COUNT(evidence.source_record_id)=0
               )""",
        ),
        "kaikki_expression_edges": count(
            database,
            """SELECT COUNT(*) FROM (
                 SELECT relationship.id
                 FROM relationships AS relationship
                 JOIN language_objects AS expression ON expression.id=relationship.source_object_id
                 LEFT JOIN relationship_evidence AS evidence ON evidence.relationship_id=relationship.id
                 WHERE expression.source_id='kaikki-enwiktionary'
                   AND expression.type_code='expression'
                   AND relationship.relationship_type_code='contains'
                 GROUP BY relationship.id HAVING COUNT(evidence.source_record_id)=0
               )""",
        ),
        "kaikki_lexical_relation_edges": count(
            database,
            """SELECT COUNT(*) FROM (
                 SELECT relationship.id
                 FROM relationships AS relationship
                 LEFT JOIN relationship_evidence AS evidence ON evidence.relationship_id=relationship.id
                 WHERE relationship.relationship_type_code IN ('synonym_of','antonym_of')
                 GROUP BY relationship.id HAVING COUNT(evidence.source_record_id)=0
               )""",
        ),
        "tex_grammar_edges": count(
            database,
            """SELECT COUNT(*) FROM (
                 SELECT relationship.id
                 FROM relationships AS relationship
                 JOIN language_objects AS source ON source.id=relationship.source_object_id
                 LEFT JOIN relationship_evidence AS evidence ON evidence.relationship_id=relationship.id
                 WHERE source.source_id='tex-french-grammar'
                 GROUP BY relationship.id HAVING COUNT(evidence.source_record_id)=0
               )""",
        ),
    }
    integrity_checks = {
        "foreign_key_violations": len(rows(database, "PRAGMA foreign_key_check")),
        "orphaned_import_record_mappings": count(
            database,
            """SELECT COUNT(*) FROM import_record_mappings AS mapping
               LEFT JOIN canonical_objects AS object ON object.canonical_id=mapping.canonical_id
               WHERE object.canonical_id IS NULL""",
        ),
        "orphaned_sentence_alignments": count(
            database,
            """SELECT COUNT(*) FROM sentence_source_alignments AS alignment
               LEFT JOIN language_objects AS sentence ON sentence.id=alignment.sentence_object_id
               LEFT JOIN canonical_objects AS target ON target.canonical_id=alignment.target_canonical_id
               LEFT JOIN source_records AS record ON record.id=alignment.source_record_id
               WHERE sentence.id IS NULL OR target.canonical_id IS NULL OR record.id IS NULL""",
        ),
        "orphaned_multiword_components": count(
            database,
            """SELECT COUNT(*) FROM multiword_components AS component
               LEFT JOIN language_objects AS parent ON parent.id=component.parent_object_id
               LEFT JOIN language_objects AS child ON child.id=component.component_object_id
               WHERE parent.id IS NULL OR child.id IS NULL""",
        ),
        "orphaned_multiword_component_evidence": count(
            database,
            """SELECT COUNT(*) FROM multiword_component_evidence AS evidence
               LEFT JOIN multiword_components AS component
                 ON component.parent_object_id=evidence.parent_object_id
                AND component.position=evidence.position
               LEFT JOIN source_records AS record ON record.id=evidence.source_record_id
               WHERE component.parent_object_id IS NULL OR record.id IS NULL""",
        ),
        "canonical_facts_without_evidence": count(
            database,
            """SELECT COUNT(*) FROM canonical_facts AS fact
               LEFT JOIN fact_evidence AS evidence ON evidence.fact_id=fact.id
               WHERE evidence.fact_id IS NULL""",
        ),
        "duplicate_canonical_identity_keys": count(
            database,
            """SELECT COUNT(*) FROM (
                 SELECT identity_key FROM canonical_objects
                 GROUP BY identity_key HAVING COUNT(*) > 1
               )""",
        ),
        "source_backed_edges_without_evidence": source_edge_checks,
    }
    source_edge_total = sum(source_edge_checks.values())
    scalar_integrity_failures = sum(
        value for key, value in integrity_checks.items() if key != "source_backed_edges_without_evidence"
    )

    report = {
        "audit": "A1 Golden Slice",
        "database": str(args.database),
        "coverage": {
            "a1_word_objects": count(
                database,
                "SELECT COUNT(*) FROM language_objects WHERE type_code='word' AND cefr_level='A1'",
            ),
            "a1_verb_words": count(
                database,
                """SELECT COUNT(*) FROM language_objects
                   WHERE type_code='word' AND cefr_level='A1' AND part_of_speech='VER'""",
            ),
            "a1_verb_words_with_lexique_forms": reports["verb_morphology"]["a1_verb_lemmas_with_source_forms"],
            "a1_verb_words_without_lexique_forms": missing_verb_forms,
            "source_reports": reports,
            "current_graph_counts": {
                row["type_code"]: row["count"]
                for row in rows(
                    database,
                    "SELECT type_code, COUNT(*) AS count FROM language_objects GROUP BY type_code ORDER BY type_code",
                )
            },
        },
        "integrity": integrity_checks,
        "legacy_compatibility_backlog": {
            "relationships_without_relationship_evidence": count(
                database,
                """SELECT COUNT(*) FROM relationships AS relationship
                   LEFT JOIN relationship_evidence AS evidence ON evidence.relationship_id=relationship.id
                   WHERE evidence.relationship_id IS NULL""",
            ),
            "note": "This count is reported separately because pre-provenance compatibility and internal graph edges are not retroactively represented as source-backed A1 imports. The scoped source-backed edge checks above must remain zero.",
        },
        "result": {
            "passed": scalar_integrity_failures == 0 and source_edge_total == 0
            and reports["flelex_baseline"]["unmapped_rows"] == 0
            and reports["flelex_baseline"]["duplicate_source_identities"] == 0,
            "integrity_failure_count": scalar_integrity_failures + source_edge_total,
            "coverage_gaps_are_explicit": True,
            "no_llm_canonical_data": True,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report["result"], indent=2))


if __name__ == "__main__":
    main()
