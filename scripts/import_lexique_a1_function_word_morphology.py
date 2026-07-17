#!/usr/bin/env python3
"""Import evidence-backed gender and number facts for A1 function words.

Lexique does not provide paradigm links between variants such as ``mon`` and
``ma``. This adapter therefore imports only the gender/number facts asserted
for an existing A1 Language Object. It never invents an inflected-form edge.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import uuid
from collections import Counter
from pathlib import Path

from canonical_identity import NAMESPACE


# FLELex and Lexique use different POS taxonomies. These mappings are limited
# to categories whose FLELex A1 objects are demonstrably pronouns/articles/
# possessive determiners rather than broad lexical-category guesses.
LEXIQUE_TO_GRAPH_POS = {
    "ADJ:dem": "PRO",
    "ADJ:ind": "PRO",
    "ADJ:int": "PRO",
    "ADJ:pos": "DET:POS",
    "ART:def": "DET:ART",
    "ART:ind": "DET:ART",
    "PRO:dem": "PRO",
    "PRO:ind": "PRO",
    "PRO:int": "PRO",
    "PRO:per": "PRO",
    "PRO:pos": "DET:POS",
    "PRO:rel": "PRO",
}
GENDER_CODES = {"m": "masculine", "f": "feminine"}
NUMBER_CODES = {"s": "singular", "p": "plural"}


def normalize(value: str) -> str:
    return " ".join(value.casefold().replace("’", "'").split())


def stable_id(kind: str, value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"liens:{kind}:{value}"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    if sha256(args.source) != manifest["release"]["sha256"]:
        raise ValueError("Lexique source SHA-256 mismatch")

    database = sqlite3.connect(args.database)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys=ON")
    release_id = manifest["release"]["id"]
    import_run_id = f"import:{release_id}:a1-function-word-morphology"

    database.execute(
        """INSERT OR IGNORE INTO import_runs
           (id, release_id, importer_name, importer_version, status, completed_at)
           VALUES (?, ?, ?, ?, 'completed', CURRENT_TIMESTAMP)""",
        (import_run_id, release_id, "lexique383_a1_function_word_morphology", "1"),
    )
    for predicate, label in (
        ("grammatical_gender", "Grammatical gender"),
        ("grammatical_number", "Grammatical number"),
    ):
        database.execute(
            """INSERT OR IGNORE INTO fact_predicates
               (code, value_kind, label, description)
               VALUES (?, 'code', ?, 'Imported Lexique morphology fact.')""",
            (predicate, label),
        )

    words = {
        (normalize(row["canonical_form"]), row["part_of_speech"]): (
            row["id"],
            row["canonical_id"],
        )
        for row in database.execute(
            """SELECT object.id, object.canonical_form, object.part_of_speech,
                      canonical.canonical_id
               FROM language_objects object
               JOIN canonical_objects canonical ON canonical.language_object_id = object.id
               WHERE object.type_code = 'word' AND object.cefr_level = 'A1'"""
        )
    }

    eligible_rows = 0
    rows_with_features = 0
    mapped_word_ids: set[str] = set()
    mapped_facts: set[str] = set()
    category_counts: Counter[str] = Counter()
    database.commit()
    database.execute("BEGIN")
    try:
        with args.source.open(encoding="utf8") as source:
            for line_number, row in enumerate(csv.DictReader(source, delimiter="\t"), start=2):
                part_of_speech = LEXIQUE_TO_GRAPH_POS.get(row["cgram"])
                key = (normalize(row["lemme"]), part_of_speech)
                if part_of_speech is None or key not in words:
                    continue

                eligible_rows += 1
                # Lexique does not relate distinct function-word variants to a
                # shared lemma, so a differing surface cannot be safely linked.
                if normalize(row["ortho"]) != normalize(row["lemme"]):
                    continue

                gender = GENDER_CODES.get(row["genre"])
                number = NUMBER_CODES.get(row["nombre"])
                if not gender and not number:
                    continue

                rows_with_features += 1
                object_id, canonical_id = words[key]
                record_id = stable_id(
                    "source-record", f"{release_id}|line:{line_number}|lexique_row"
                )
                database.execute(
                    """INSERT OR IGNORE INTO source_records
                       (id, release_id, external_key, record_kind, content_hash)
                       VALUES (?, ?, ?, 'lexique_row', ?)""",
                    (
                        record_id,
                        release_id,
                        f"line:{line_number}",
                        hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest(),
                    ),
                )
                database.execute(
                    """UPDATE source_records SET record_kind = 'lexique_row'
                       WHERE id = ? AND record_kind IN ('morphology_row', 'phonology_row')""",
                    (record_id,),
                )
                database.execute(
                    """INSERT OR IGNORE INTO import_record_mappings
                       (import_run_id, source_record_id, canonical_id, mapping_kind, confidence)
                       VALUES (?, ?, ?, 'lexique_function_word_morphology_match', 1)""",
                    (import_run_id, record_id, canonical_id),
                )

                for predicate, value in (
                    ("grammatical_gender", gender),
                    ("grammatical_number", number),
                ):
                    if not value:
                        continue
                    fact_id = stable_id("fact", f"{canonical_id}|{predicate}|{value}")
                    database.execute(
                        """INSERT OR IGNORE INTO canonical_facts
                           (id, canonical_subject_id, predicate_code)
                           VALUES (?, ?, ?)""",
                        (fact_id, canonical_id, predicate),
                    )
                    database.execute(
                        """INSERT OR IGNORE INTO fact_code_values(fact_id, value_code)
                           VALUES (?, ?)""",
                        (fact_id, value),
                    )
                    database.execute(
                        """INSERT OR IGNORE INTO fact_evidence
                           (fact_id, source_record_id, evidence_role, confidence)
                           VALUES (?, ?, 'asserts', 1)""",
                        (fact_id, record_id),
                    )
                    mapped_facts.add(fact_id)

                mapped_word_ids.add(object_id)
                category_counts[row["cgram"]] += 1
        database.commit()
    except Exception:
        database.rollback()
        raise

    report = {
        "release_id": release_id,
        "eligible_source_rows": eligible_rows,
        "source_rows_with_gender_or_number": rows_with_features,
        "language_objects_enriched": len(mapped_word_ids),
        "canonical_facts_evidenced": len(mapped_facts),
        "source_categories": dict(sorted(category_counts.items())),
        "not_imported": {
            "variant_surfaces_without_source_paradigm_link": (
                "Lexique records the variants but does not assert a shared lemma relation; "
                "they remain outside the canonical graph until a source can evidence that edge."
            )
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
