#!/usr/bin/env python3
"""Project the preferred pronunciation representation into browser detail rows.

This is a read model, not a second source of truth.  Kaikki verified IPA wins;
active derived Lexique IPA is used only when no verified IPA is available.
Audio URLs deliberately remain representation metadata until a future playback
provider explicitly opts in.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from pronunciation_model import ensure_representation_schema


def metadata(value: str | None) -> dict:
    try:
        return json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}


def rank(row: sqlite3.Row) -> tuple[int, int, int, float, str]:
    values = metadata(row["value_json"])
    tags = {str(tag).casefold() for tag in values.get("tags", [])}
    if row["transcription_system"] == "ipa" and row["lifecycle"] == "canonical":
        source_rank = 0 if row["catalog_id"] == "kaikki-enwiktionary" else 1
        regional_rank = 0 if not tags else 1 if "france" in tags else 2
        return (0, source_rank, regional_rank, -(row["confidence"] or 0), row["id"])
    if row["transcription_system"] == "lexique383_derived_ipa_v1" and row["lifecycle"] == "derived":
        return (1, 0, 0, -(row["confidence"] or 0), row["id"])
    return (2, 0, 0, -(row["confidence"] or 0), row["id"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    db = sqlite3.connect(args.database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    ensure_representation_schema(db)
    candidates: dict[str, list[sqlite3.Row]] = {}
    for row in db.execute(
        """SELECT representation.*, release.catalog_id
           FROM pronunciation_representations representation
           LEFT JOIN pronunciation_representation_evidence evidence
             ON evidence.representation_id = representation.id
           LEFT JOIN source_records record ON record.id = evidence.source_record_id
           LEFT JOIN source_releases release ON release.id = record.release_id
           WHERE representation.representation_kind = 'ipa'
             AND representation.value_text IS NOT NULL
             AND representation.lifecycle <> 'superseded'
           ORDER BY representation.pronunciation_object_id, representation.id"""
    ):
        candidates.setdefault(row["pronunciation_object_id"], []).append(row)

    db.commit()
    db.execute("BEGIN")
    try:
        projected = {"verified": 0, "derived": 0, "other": 0}
        for pronunciation_id, rows in candidates.items():
            selected = min(rows, key=rank)
            values = metadata(selected["value_json"])
            is_derived = selected["lifecycle"] == "derived"
            status = "derived" if is_derived else "verified" if selected["transcription_system"] == "ipa" else "metadata_ready"
            projected["derived" if is_derived else "verified" if status == "verified" else "other"] += 1
            source_id = "kaikki-enwiktionary" if selected["catalog_id"] == "kaikki-enwiktionary" else None
            variant = ", ".join(values.get("tags", [])) or "standard"
            # This projection owns the displayed IPA only.  Do not erase a
            # pre-existing audio-only detail row for an object with no IPA.
            db.execute("DELETE FROM pronunciation_object_details WHERE object_id = ?", (pronunciation_id,))
            db.execute(
                """INSERT INTO pronunciation_object_details
                   (object_id, ipa, syllables_json, stress_json, variant_code,
                    source_id, provenance, confidence, review_status,
                    representation_lifecycle, transcription_system, representation_metadata_json)
                   VALUES (?, ?, '[]', '[]', ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    pronunciation_id,
                    selected["value_text"],
                    variant,
                    source_id,
                    "derived" if is_derived else "curated",
                    selected["confidence"],
                    status,
                    selected["lifecycle"],
                    selected["transcription_system"],
                    selected["value_json"],
                ),
            )
        db.commit()
    except Exception:
        db.rollback()
        raise

    report = {"browser_projection": projected, "pronunciation_objects_with_displayable_ipa": sum(projected.values()), "audio_playback_implemented": False}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
