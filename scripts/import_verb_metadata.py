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


def stable_id(kind: str, *parts: str) -> str:
    return f"fr:{kind}:" + ':'.join(normalise(part).replace(' ', '_') for part in parts)


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
        explanation_id = stable_id('learning-resource', lemma[0], 'conjugation-explanation')
        db.execute(
            "INSERT OR REPLACE INTO language_objects "
            "(id,type_code,canonical_form,display_form,normalized_form,source_id,content_status,provenance) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (explanation_id, 'learning_resource', f"{entry['lemma']} conjugation explanation",
             f"{entry['lemma']} conjugation explanation", normalise(f"{entry['lemma']} conjugation explanation"),
             SOURCE_ID, 'ai_enriched', 'ai_enriched'),
        )
        db.execute(
            "INSERT OR REPLACE INTO object_definitions "
            "(id,object_id,position,english_gloss,chinese_gloss,explanation_en,explanation_zh,source_kind,confidence) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (stable_id('definition', explanation_id), explanation_id, 1, None, None,
             entry.get('note_en'), entry.get('note_zh'), 'ai_enriched', 0.78),
        )
        db.execute("INSERT OR IGNORE INTO learning_metadata(object_id) VALUES (?)", (explanation_id,))
        db.execute(
            "INSERT OR REPLACE INTO relationships "
            "(id,source_object_id,target_object_id,relationship_type_code,position,source_kind,confidence) "
            "VALUES (?,?,?,?,NULL,'ai_enriched',0.78)",
            (stable_id('rel', lemma[0], 'explains_conjugation', explanation_id), lemma[0], explanation_id, 'explains_conjugation'),
        )
        db.execute(
            "INSERT OR REPLACE INTO verb_metadata "
            "(object_id,verb_group_code,is_irregular,future_stem,auxiliary_lemma_id,note_en,note_zh,source_id,provenance,confidence,status,explanation_object_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (lemma[0], entry.get('verb_group_code'), int(entry.get('is_irregular', False)),
             entry.get('future_stem'), auxiliary[0], entry.get('note_en'), entry.get('note_zh'),
             SOURCE_ID, 'ai_enriched', 0.78, 'ai_enriched', explanation_id),
        )
    db.commit()
    print(f'Imported metadata for {len(entries)} verbs.')


if __name__ == '__main__':
    main()
