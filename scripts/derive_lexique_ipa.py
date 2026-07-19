#!/usr/bin/env python3
"""Derive temporary IPA from Lexique 3.83 phonological codes.

The mapping is a deterministic rendering of Lexique's published phoneme-code
table.  It is deliberately stored as a *derived* representation, never as a
source assertion.  A Kaikki IPA representation supersedes it automatically.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path

from pronunciation_model import ensure_representation_schema, stable_id


PIPELINE = "lexique383_to_ipa_v1"
SYSTEM = "lexique383_derived_ipa_v1"

# Lexique's official phoneme-code table, rendered character-for-character as
# IPA.  The source row remains the evidence for the input code—not for a new
# canonical IPA assertion.
LEXIQUE_TO_IPA = {
    "a": "a", "i": "i", "y": "y", "u": "u", "o": "o", "O": "ɔ",
    "e": "e", "E": "ɛ", "°": "ə", "2": "ø", "9": "œ", "5": "ɛ̃",
    "1": "œ̃", "@": "ɑ̃", "§": "ɔ̃", "j": "j", "8": "ɥ", "w": "w",
    "p": "p", "b": "b", "t": "t", "d": "d", "k": "k", "g": "g",
    "f": "f", "v": "v", "s": "s", "z": "z", "S": "ʃ", "Z": "ʒ",
    "m": "m", "n": "n", "N": "ɲ", "l": "l", "R": "ʁ", "x": "x",
    "G": "ŋ",
}


def convert(code: str) -> str | None:
    try:
        return "".join(LEXIQUE_TO_IPA[character] for character in code)
    except KeyError:
        return None


def kaikki_ipa_exists(db: sqlite3.Connection, pronunciation_id: str) -> bool:
    return db.execute(
        """SELECT 1
           FROM pronunciation_representations representation
           JOIN pronunciation_representation_evidence evidence
             ON evidence.representation_id = representation.id
           JOIN source_records record ON record.id = evidence.source_record_id
           JOIN source_releases release ON release.id = record.release_id
           WHERE representation.pronunciation_object_id = ?
             AND representation.representation_kind = 'ipa'
             AND representation.transcription_system = 'ipa'
             AND representation.lifecycle = 'canonical'
             AND release.catalog_id = 'kaikki-enwiktionary'
           LIMIT 1""",
        (pronunciation_id,),
    ).fetchone() is not None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    db = sqlite3.connect(args.database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    ensure_representation_schema(db)

    codes = list(
        db.execute(
            """SELECT * FROM pronunciation_representations
               WHERE representation_kind = 'phonological_code'
                 AND transcription_system = 'lexique383'
               ORDER BY pronunciation_object_id, id"""
        )
    )
    created = 0
    superseded = 0
    excluded = Counter()
    db.commit()
    db.execute("BEGIN")
    try:
        for code in codes:
            pronunciation_id = code["pronunciation_object_id"]
            rendered = convert(code["value_text"] or "")
            if not rendered:
                excluded["unknown_lexique_symbol"] += 1
                continue
            metadata = json.dumps(
                {
                    "derived_from_representation_id": code["id"],
                    "pipeline": PIPELINE,
                    "source_system": "lexique383",
                },
                sort_keys=True,
            )
            representation_id = stable_id(
                "pronunciation-representation",
                f"{pronunciation_id}|ipa|{SYSTEM}|{rendered}|{metadata}",
            )
            lifecycle = "superseded" if kaikki_ipa_exists(db, pronunciation_id) else "derived"
            db.execute(
                """INSERT INTO pronunciation_representations
                   (id, pronunciation_object_id, representation_kind,
                    transcription_system, value_text, value_json, lifecycle, confidence)
                   VALUES (?, ?, 'ipa', ?, ?, ?, ?, 0.65)
                   ON CONFLICT(id) DO UPDATE SET lifecycle = excluded.lifecycle,
                     confidence = excluded.confidence""",
                (representation_id, pronunciation_id, SYSTEM, rendered, metadata, lifecycle),
            )
            for evidence in db.execute(
                """SELECT source_record_id, confidence
                   FROM pronunciation_representation_evidence
                   WHERE representation_id = ?""",
                (code["id"],),
            ):
                db.execute(
                    """INSERT OR IGNORE INTO pronunciation_representation_evidence
                       (representation_id, source_record_id, confidence) VALUES (?, ?, ?)""",
                    (representation_id, evidence["source_record_id"], evidence["confidence"]),
                )
            if lifecycle == "derived":
                created += 1
            else:
                superseded += 1
        db.commit()
    except Exception:
        db.rollback()
        raise

    result = {
        "pipeline": PIPELINE,
        "lexique_code_representations_seen": len(codes),
        "derived_ipa_active": created,
        "derived_ipa_superseded_by_kaikki": superseded,
        "exclusions": dict(sorted(excluded.items())),
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
