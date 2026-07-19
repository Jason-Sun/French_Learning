#!/usr/bin/env python3
"""Unify legacy/source-specific pronunciation nodes by their language-object owner.

The graph used to allow importers to name Pronunciation Objects after their
source.  This migration moves those representations and their evidence onto a
single source-independent object per owner.  It is safe to run repeatedly.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from pronunciation_graph import sync_graph
from pronunciation_model import (
    ensure_pronunciation_object,
    ensure_representation_schema,
    pronunciation_object_id,
    pronunciation_relationship_id,
    stable_id,
)


def copy_representation(db: sqlite3.Connection, row: sqlite3.Row, target_id: str) -> None:
    metadata = row["value_json"]
    representation_id = stable_id(
        "pronunciation-representation",
        "|".join(
            [
                target_id,
                row["representation_kind"],
                row["transcription_system"] or "",
                row["value_text"] or "",
                metadata or "",
            ]
        ),
    )
    db.execute(
        """INSERT OR IGNORE INTO pronunciation_representations
           (id, pronunciation_object_id, representation_kind,
            transcription_system, value_text, value_json, lifecycle, confidence)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            representation_id,
            target_id,
            row["representation_kind"],
            row["transcription_system"],
            row["value_text"],
            metadata,
            row["lifecycle"],
            row["confidence"],
        ),
    )
    for evidence in db.execute(
        "SELECT source_record_id, confidence FROM pronunciation_representation_evidence WHERE representation_id = ?",
        (row["id"],),
    ):
        db.execute(
            """INSERT OR IGNORE INTO pronunciation_representation_evidence
               (representation_id, source_record_id, confidence) VALUES (?, ?, ?)""",
            (representation_id, evidence["source_record_id"], evidence["confidence"]),
        )


def legacy_detail_as_representation(db: sqlite3.Connection, detail: sqlite3.Row, target_id: str) -> None:
    if not detail["ipa"]:
        return
    metadata = json.dumps(
        {"migrated_from": detail["object_id"], "variant": detail["variant_code"]},
        ensure_ascii=False,
        sort_keys=True,
    )
    representation_id = stable_id(
        "pronunciation-representation",
        f"{target_id}|ipa|legacy_pronunciations|{detail['ipa']}|{metadata}",
    )
    lifecycle = "canonical" if detail["provenance"] != "ai_enriched" else "draft"
    db.execute(
        """INSERT OR IGNORE INTO pronunciation_representations
           (id, pronunciation_object_id, representation_kind,
            transcription_system, value_text, value_json, lifecycle, confidence)
           VALUES (?, ?, 'ipa', 'legacy_pronunciations', ?, ?, ?, ?)""",
        (representation_id, target_id, detail["ipa"], metadata, lifecycle, detail["confidence"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    db = sqlite3.connect(args.database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    sync_graph(db)
    ensure_representation_schema(db)

    legacy_edges = list(
        db.execute(
            """SELECT edge.id AS relationship_id, edge.source_object_id AS owner_id,
                      edge.target_object_id AS old_pronunciation_id,
                      owner.display_form AS owner_display_form
               FROM relationships edge
               JOIN language_objects pronunciation ON pronunciation.id = edge.target_object_id
               JOIN language_objects owner ON owner.id = edge.source_object_id
               WHERE edge.relationship_type_code = 'has_pronunciation'
                 AND pronunciation.type_code = 'pronunciation'"""
        )
    )
    migrated_objects: set[str] = set()
    migrated_representations = 0
    migrated_details = 0
    db.commit()
    db.execute("BEGIN")
    try:
        for edge in legacy_edges:
            owner_id = edge["owner_id"]
            old_id = edge["old_pronunciation_id"]
            target_id, target_relationship_id = ensure_pronunciation_object(
                db, owner_id, display_form=edge["owner_display_form"]
            )
            if old_id == target_id:
                continue

            representation_rows = list(
                db.execute(
                    "SELECT * FROM pronunciation_representations WHERE pronunciation_object_id = ?",
                    (old_id,),
                )
            )
            for row in representation_rows:
                copy_representation(db, row, target_id)
                migrated_representations += 1

            detail = db.execute(
                "SELECT * FROM pronunciation_object_details WHERE object_id = ?", (old_id,)
            ).fetchone()
            if detail:
                legacy_detail_as_representation(db, detail, target_id)
                migrated_details += 1

            for evidence in db.execute(
                "SELECT source_record_id, confidence FROM relationship_evidence WHERE relationship_id = ?",
                (edge["relationship_id"],),
            ):
                db.execute(
                    """INSERT OR IGNORE INTO relationship_evidence
                       (relationship_id, source_record_id, confidence) VALUES (?, ?, ?)""",
                    (target_relationship_id, evidence["source_record_id"], evidence["confidence"]),
                )

            db.execute("DELETE FROM relationships WHERE id = ?", (edge["relationship_id"],))
            db.execute("DELETE FROM pronunciation_representations WHERE pronunciation_object_id = ?", (old_id,))
            db.execute("DELETE FROM pronunciation_object_details WHERE object_id = ?", (old_id,))
            # Older releases can already have learner resources, source mappings,
            # or historical references pointing at this legacy node.  Removing its
            # canonical identity would break those records.  Retain it as an inert
            # compatibility identity instead: it has no active graph edge, detail,
            # or representation after the migration, while the owner now has one
            # source-independent Pronunciation Object.
            db.execute(
                """UPDATE language_objects
                   SET content_status = 'deprecated', provenance = 'migrated'
                   WHERE id = ?""",
                (old_id,),
            )
            migrated_objects.add(old_id)
        db.commit()
    except Exception:
        db.rollback()
        raise

    result = {
        "legacy_pronunciation_objects_migrated": len(migrated_objects),
        "representations_copied": migrated_representations,
        "legacy_details_projected": migrated_details,
        "source_independent_pronunciation_objects": db.execute(
            "SELECT COUNT(*) FROM language_objects WHERE type_code = 'pronunciation'"
        ).fetchone()[0],
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
