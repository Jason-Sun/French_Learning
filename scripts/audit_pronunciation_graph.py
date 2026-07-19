#!/usr/bin/env python3
"""Validate source, lifecycle, and graph integrity for pronunciation data."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def count(db: sqlite3.Connection, query: str, params: tuple = ()) -> int:
    return int(db.execute(query, params).fetchone()[0])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    db = sqlite3.connect(args.database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")

    foreign_keys = list(db.execute("PRAGMA foreign_key_check"))
    orphan_representations = count(
        db,
        """SELECT COUNT(*) FROM pronunciation_representations representation
           LEFT JOIN language_objects pronunciation ON pronunciation.id = representation.pronunciation_object_id
           WHERE pronunciation.id IS NULL""",
    )
    unevidenced_kaikki = count(
        db,
        """SELECT COUNT(*) FROM pronunciation_representations representation
           WHERE representation.transcription_system IN ('ipa', 'wikimedia_commons')
             AND representation.lifecycle = 'canonical'
             AND representation.value_json LIKE '%\"source_catalog\":\"kaikki-enwiktionary\"%'
             AND NOT EXISTS (
               SELECT 1 FROM pronunciation_representation_evidence evidence
               JOIN source_records record ON record.id = evidence.source_record_id
               JOIN source_releases release ON release.id = record.release_id
               WHERE evidence.representation_id = representation.id
                 AND release.catalog_id = 'kaikki-enwiktionary'
             )""",
    )
    canonical_derived = count(
        db,
        """SELECT COUNT(*) FROM pronunciation_representations
           WHERE transcription_system = 'lexique383_derived_ipa_v1'
             AND lifecycle = 'canonical'""",
    )
    active_derived_with_kaikki = count(
        db,
        """SELECT COUNT(*) FROM pronunciation_representations derived
           WHERE derived.transcription_system = 'lexique383_derived_ipa_v1'
             AND derived.lifecycle = 'derived'
             AND EXISTS (
               SELECT 1 FROM pronunciation_representations verified
               JOIN pronunciation_representation_evidence evidence ON evidence.representation_id = verified.id
               JOIN source_records record ON record.id = evidence.source_record_id
               JOIN source_releases release ON release.id = record.release_id
               WHERE verified.pronunciation_object_id = derived.pronunciation_object_id
                 AND verified.representation_kind = 'ipa'
                 AND verified.transcription_system = 'ipa'
                 AND verified.lifecycle = 'canonical'
                 AND release.catalog_id = 'kaikki-enwiktionary'
             )""",
    )
    old_source_named_active_objects = count(
        db,
        """SELECT COUNT(*) FROM language_objects pronunciation
           WHERE pronunciation.type_code = 'pronunciation'
             AND (pronunciation.id LIKE 'fr:pronunciation:lexique383:%'
                  OR pronunciation.id LIKE 'fr:pronunciation_object:%')
             AND (
               EXISTS (
                 SELECT 1 FROM relationships edge
                 WHERE edge.target_object_id = pronunciation.id
                   AND edge.relationship_type_code = 'has_pronunciation'
               )
               OR EXISTS (
                 SELECT 1 FROM pronunciation_representations representation
                 WHERE representation.pronunciation_object_id = pronunciation.id
               )
               OR EXISTS (
                 SELECT 1 FROM pronunciation_object_details detail
                 WHERE detail.object_id = pronunciation.id
               )
             )""",
    )
    deprecated_compatibility_objects = count(
        db,
        """SELECT COUNT(*) FROM language_objects pronunciation
           WHERE pronunciation.type_code = 'pronunciation'
             AND pronunciation.content_status = 'deprecated'
             AND (pronunciation.id LIKE 'fr:pronunciation:lexique383:%'
                  OR pronunciation.id LIKE 'fr:pronunciation_object:%')""",
    )
    representation_counts = {
        row["key"]: row["count"]
        for row in db.execute(
            """SELECT representation_kind || ':' || COALESCE(transcription_system, '') AS key,
                      COUNT(*) AS count
               FROM pronunciation_representations
               GROUP BY representation_kind, transcription_system
               ORDER BY key"""
        )
    }
    result = {
        "foreign_key_failures": len(foreign_keys),
        "orphan_representations": orphan_representations,
        "unevidenced_kaikki_representations": unevidenced_kaikki,
        "canonical_derived_ipa": canonical_derived,
        "active_derived_ipa_with_kaikki_available": active_derived_with_kaikki,
        "active_source_named_pronunciation_objects": old_source_named_active_objects,
        "deprecated_pronunciation_compatibility_objects": deprecated_compatibility_objects,
        "representation_counts": representation_counts,
    }
    result["passes"] = all(
        result[key] == 0
        for key in (
            "foreign_key_failures",
            "orphan_representations",
            "unevidenced_kaikki_representations",
            "canonical_derived_ipa",
            "active_derived_ipa_with_kaikki_available",
            "active_source_named_pronunciation_objects",
        )
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passes"]:
        raise SystemExit("Pronunciation graph audit failed")


if __name__ == "__main__":
    main()
