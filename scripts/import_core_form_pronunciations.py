#!/usr/bin/env python3
"""Seed reviewed core-form IPA without ever inheriting a lemma pronunciation."""

from __future__ import annotations

import argparse
import json
import sqlite3
import unicodedata
from pathlib import Path


SOURCE_ID = "liens_core_form_pronunciation"


def normalise(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().replace("’", "'").split())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    db = sqlite3.connect(args.database)
    db.execute("PRAGMA foreign_keys = ON")
    db.execute(
        "INSERT OR REPLACE INTO sources(id,name,url,license,citation) VALUES (?,?,?,?,?)",
        (SOURCE_ID, "Liens Core Form Pronunciation", "app://liens/core-form-pronunciation",
         "Internal reviewed seed", "Independent IPA for the initial core verb forms."),
    )
    imported = 0
    for spec in data:
        lemma = db.execute(
            "SELECT id FROM language_objects WHERE type_code='word' AND normalized_form=? "
            "AND part_of_speech IN ('VER','V') ORDER BY frequency_per_million DESC LIMIT 1",
            (normalise(spec["lemma"]),),
        ).fetchone()
        if not lemma:
            raise ValueError(f"Verb lemma not found: {spec['lemma']}")
        for surface, ipa in spec["forms"].items():
            forms = db.execute(
                "SELECT f.id FROM language_objects AS f JOIN relationships AS r "
                "ON r.source_object_id=f.id AND r.relationship_type_code='inflected_form_of' "
                "WHERE f.type_code='inflected_form' AND r.target_object_id=? AND f.normalized_form=?",
                (lemma[0], normalise(surface)),
            ).fetchall()
            if not forms:
                raise ValueError(f"Form not found: {spec['lemma']} → {surface}")
            for (form_id,) in forms:
                record_id = f"fr:pronunciation:{form_id.removeprefix('fr:')}"
                db.execute(
                    "INSERT INTO pronunciations "
                    "(id,object_id,ipa,variant_code,source_id,provenance,confidence,status) "
                    "VALUES (?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(id) DO UPDATE SET ipa=excluded.ipa, source_id=excluded.source_id, "
                    "provenance=excluded.provenance, confidence=excluded.confidence, status=excluded.status",
                    (record_id, form_id, ipa, "standard", SOURCE_ID, "curated", 0.94, "reviewed"),
                )
                imported += 1
    db.execute(
        "INSERT INTO metadata(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        ("core_form_pronunciation_status", f"{imported} independent core form pronunciations"),
    )
    db.commit()
    print(f"Imported {imported} independent core-form pronunciation records.")


if __name__ == "__main__":
    main()
