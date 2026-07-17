#!/usr/bin/env python3
"""Import declarative lemma-owned verb metadata into the Liens graph."""

from __future__ import annotations

import argparse
import json
import sqlite3
import unicodedata
from pathlib import Path


SOURCE_ID = 'liens_core_conjugation_draft'


def normalise(value: str) -> str:
    return ' '.join(unicodedata.normalize('NFC', value).casefold().replace('’', "'").split())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    entries = json.loads(args.input.read_text(encoding='utf-8'))

    db = sqlite3.connect(args.database)
    db.execute('PRAGMA foreign_keys = ON')
    db.execute(
        "INSERT OR IGNORE INTO sources(id,name,url,license,citation) VALUES (?,?,?,?,?)",
        (SOURCE_ID, 'Liens Core Conjugation Draft', 'app://liens/core-conjugations',
         'Internal review draft', 'Declarative verb metadata; review before promoting to curated content.'),
    )
    for entry in entries:
        lemma = db.execute(
            "SELECT id FROM language_objects WHERE type_code='word' AND normalized_form=? "
            "AND part_of_speech IN ('VER','V') ORDER BY frequency_per_million DESC LIMIT 1",
            (normalise(entry['lemma']),),
        ).fetchone()
        auxiliary = db.execute(
            "SELECT id FROM language_objects WHERE type_code='word' AND normalized_form=? "
            "AND part_of_speech IN ('VER','V') ORDER BY frequency_per_million DESC LIMIT 1",
            (normalise(entry['auxiliary']),),
        ).fetchone()
        if not lemma or not auxiliary:
            raise ValueError(f"Verb or auxiliary not found for {entry['lemma']}")
        db.execute(
            "INSERT OR REPLACE INTO verb_metadata "
            "(object_id,verb_group_code,is_irregular,future_stem,auxiliary_lemma_id,note_en,note_zh,source_id,provenance,confidence,status) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (lemma[0], entry.get('verb_group_code'), int(entry.get('is_irregular', False)),
             entry.get('future_stem'), auxiliary[0], entry.get('note_en'), entry.get('note_zh'),
             SOURCE_ID, 'ai_enriched', 0.78, 'ai_enriched'),
        )
    db.commit()
    print(f'Imported metadata for {len(entries)} verbs.')


if __name__ == '__main__':
    main()
