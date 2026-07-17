#!/usr/bin/env python3
"""Import reviewable A1 learning content into the Liens knowledge graph."""

from __future__ import annotations

import argparse
import json
import sqlite3
import unicodedata
from pathlib import Path


SOURCE_ID = 'liens_a1_foundation_draft'


def normalise(value: str) -> str:
    return ' '.join(unicodedata.normalize('NFC', value).casefold().replace('’', "'").split())


def stable_id(kind: str, value: str) -> str:
    return f"fr:{kind}:{normalise(value).replace(' ', '_')}"


def word_id(db: sqlite3.Connection, lemma: str, part_of_speech: str | None) -> str:
    query = "SELECT id FROM language_objects WHERE type_code='word' AND normalized_form=?"
    args: list[str] = [normalise(lemma)]
    if part_of_speech:
        query += ' AND part_of_speech=?'
        args.append(part_of_speech)
    query += ' ORDER BY frequency_per_million DESC LIMIT 1'
    row = db.execute(query, args).fetchone()
    if not row:
        raise ValueError(f'No A1 graph object found for {lemma!r} ({part_of_speech or "any POS"})')
    return row[0]


def add_relationship(db: sqlite3.Connection, source: str, target: str) -> None:
    db.execute(
        "INSERT OR REPLACE INTO relationships "
        "(id,source_object_id,target_object_id,relationship_type_code,position,source_kind,confidence) "
        "VALUES (?,?,?,?,NULL,'ai_enriched',0.72)",
        (stable_id('rel', f'{source}:illustrates:{target}'), source, target, 'illustrates'),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    entries = json.loads(args.input.read_text(encoding='utf-8'))

    db = sqlite3.connect(args.database)
    db.execute('PRAGMA foreign_keys = ON')
    db.execute(
        "INSERT OR REPLACE INTO sources(id,name,url,license,citation) VALUES (?,?,?,?,?)",
        (SOURCE_ID, 'Liens A1 Foundation Draft', 'app://liens/a1-foundation-draft',
         'Internal review draft', 'AI-assisted learning content. Review before treating as curated.'),
    )

    imported_examples = 0
    for entry in entries:
        object_id = word_id(db, entry['lemma'], entry.get('part_of_speech'))
        definition_id = stable_id('definition', f"{object_id}:a1-foundation")
        db.execute(
            "INSERT OR REPLACE INTO object_definitions "
            "(id,object_id,position,english_gloss,chinese_gloss,explanation_en,explanation_zh,source_kind,confidence) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (definition_id, object_id, 1, entry['english'], entry['chinese'], entry['note_en'], entry['note_zh'], 'ai_enriched', 0.72),
        )
        if entry.get('ipa'):
            db.execute(
                "INSERT OR REPLACE INTO pronunciations "
                "(id,object_id,ipa,syllables_json,stress_json,source_id,provenance,confidence,status) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (stable_id('pronunciation', object_id), object_id, entry['ipa'],
                 json.dumps(entry.get('syllables', []), ensure_ascii=False),
                 json.dumps(entry.get('stress', []), ensure_ascii=False), SOURCE_ID,
                 'ai_enriched', 0.78, 'needs_review'),
            )
        for example in entry.get('examples', []):
            sentence_id = stable_id('sentence', example['fr'])
            normalized = normalise(example['fr'])
            db.execute(
                "INSERT OR REPLACE INTO language_objects "
                "(id,type_code,canonical_form,display_form,normalized_form,source_id,content_status,provenance) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (sentence_id, 'sentence', example['fr'], example['fr'], normalized, SOURCE_ID, 'ai_enriched', 'ai_enriched'),
            )
            db.execute(
                "INSERT OR REPLACE INTO object_definitions "
                "(id,object_id,position,english_gloss,chinese_gloss,explanation_en,explanation_zh,source_kind,confidence) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (stable_id('definition', f'{sentence_id}:translation'), sentence_id, 1,
                 example['en'], example['zh'], example.get('note_en'), example.get('note_zh'), 'ai_enriched', 0.72),
            )
            add_relationship(db, sentence_id, object_id)
            imported_examples += 1

    db.execute("INSERT INTO metadata(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ('a1_foundation_status', f'{len(entries)} AI-assisted draft entries; review required'))
    db.commit()
    print(f'Imported {len(entries)} A1 draft entries and {imported_examples} linked example sentences.')


if __name__ == '__main__':
    main()
