#!/usr/bin/env python3
"""Audit a source-backed FLELex lexical-baseline scope without inventing data."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from import_flelex_lexical_baseline import (
    file_hash,
    lexical_identity,
    load_manifest,
    selected_levels,
    selected_rows,
)


def scalar(db: sqlite3.Connection, query: str, params: tuple = ()) -> int:
    return int(db.execute(query, params).fetchone()[0])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    source_hash = file_hash(args.source)
    if source_hash != manifest["release"]["sha256"]:
        raise ValueError("Source SHA-256 does not match the manifest.")
    levels = selected_levels(manifest)
    rows = selected_rows(args.source, set(levels))
    release_id = manifest["release"]["id"]
    run_id = f"import:{release_id}:{'-'.join(level.casefold() for level in levels)}-lexical-baseline"

    db = sqlite3.connect(args.database)
    db.execute("PRAGMA foreign_keys=ON")
    missing: list[str] = []
    invalid_facts: list[str] = []
    mapped = 0
    for row in rows:
        identity = lexical_identity(row.lemma, row.part_of_speech)
        canonical = db.execute(
            """SELECT canonical_id, language_object_id FROM canonical_objects
               WHERE identity_key=?""",
            (identity,),
        ).fetchone()
        if not canonical:
            missing.append(f"{row.lemma} ({row.part_of_speech})")
            continue
        canonical_id, object_id = canonical
        object_row = db.execute(
            "SELECT cefr_level,part_of_speech,frequency_per_million FROM language_objects WHERE id=?",
            (object_id,),
        ).fetchone()
        if not object_row or tuple(object_row) != (row.level, row.part_of_speech, row.frequency):
            invalid_facts.append(f"storage metadata: {row.lemma} ({row.part_of_speech})")
        record = db.execute(
            "SELECT id FROM source_records WHERE release_id=? AND external_key=? AND record_kind='lexical_row'",
            (release_id, row.external_key),
        ).fetchone()
        if not record or not db.execute(
            """SELECT 1 FROM import_record_mappings
               WHERE import_run_id=? AND source_record_id=? AND canonical_id=? AND mapping_kind='lexical_baseline'""",
            (run_id, record[0], canonical_id),
        ).fetchone():
            invalid_facts.append(f"source mapping: {row.lemma} ({row.part_of_speech})")
        for predicate, table, expected in (
            ("part_of_speech", "fact_code_values", row.part_of_speech),
            ("cefr_level", "fact_code_values", row.level),
            ("frequency_per_million", "fact_number_values", row.frequency),
        ):
            column = "value_number" if table == "fact_number_values" else "value_code"
            check = db.execute(
                f"""SELECT 1 FROM canonical_facts fact JOIN {table} value ON value.fact_id=fact.id
                    JOIN fact_evidence evidence ON evidence.fact_id=fact.id
                    WHERE fact.canonical_subject_id=? AND fact.predicate_code=?
                      AND value.{column}=? AND evidence.source_record_id=?""",
                (canonical_id, predicate, expected, record[0] if record else ""),
            ).fetchone()
            if not check:
                invalid_facts.append(f"{predicate}: {row.lemma} ({row.part_of_speech})")
        mapped += 1

    integrity = {
        "foreign_key_violations": len(db.execute("PRAGMA foreign_key_check").fetchall()),
        "duplicate_canonical_identity_keys": scalar(
            db, "SELECT COUNT(*) FROM (SELECT identity_key FROM canonical_objects GROUP BY identity_key HAVING COUNT(*) > 1)"
        ),
        "orphan_canonical_objects": scalar(
            db,
            """SELECT COUNT(*) FROM canonical_objects canonical
               LEFT JOIN language_objects object ON object.id=canonical.language_object_id
               WHERE object.id IS NULL""",
        ),
        "orphan_facts": scalar(
            db,
            """SELECT COUNT(*) FROM canonical_facts fact
               LEFT JOIN canonical_objects object ON object.canonical_id=fact.canonical_subject_id
               WHERE object.canonical_id IS NULL""",
        ),
    }
    report = {
        "audit": "FLELex CEFR lexical baseline",
        "release_id": release_id,
        "source_sha256": source_hash,
        "selection": {"levels": list(levels)},
        "selected_source_rows": len(rows),
        "mapped_source_rows": mapped,
        "missing_canonical_identities": len(missing),
        "invalid_mapping_or_fact_records": len(invalid_facts),
        "integrity": integrity,
        "samples": {"missing": missing[:20], "invalid": invalid_facts[:20]},
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if missing or invalid_facts or any(integrity.values()):
        raise SystemExit("C1/C2 lexical-baseline audit failed.")


if __name__ == "__main__":
    main()
