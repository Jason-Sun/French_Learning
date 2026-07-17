#!/usr/bin/env python3
"""Import deterministic, structured teaching resources for shared grammar objects."""

from __future__ import annotations

import argparse
import json
import sqlite3
import unicodedata
from pathlib import Path


SOURCE_ID = 'liens_grammar_teaching_draft'


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
    db.execute("INSERT OR REPLACE INTO sources(id,name,url,license,citation) VALUES (?,?,?,?,?)", (SOURCE_ID, 'Liens Grammar Teaching Draft', 'app://liens/grammar-teaching', 'Internal review draft', 'Deterministic teacher-style grammar guidance; review before promotion.'))
    for entry in entries:
        target = db.execute('SELECT id FROM language_objects WHERE id=?', (entry['target_id'],)).fetchone()
        if not target:
            raise ValueError(f"Teaching target not found: {entry['target_id']}")
        resource_id = stable_id('learning-resource', entry['target_id'], 'teacher-guide')
        db.execute("INSERT OR REPLACE INTO language_objects(id,type_code,canonical_form,display_form,normalized_form,source_id,content_status,provenance) VALUES (?,?,?,?,?,?,?,?)", (resource_id, 'learning_resource', entry['title'], entry['title'], normalise(entry['title']), SOURCE_ID, 'ai_enriched', 'ai_enriched'))
        db.execute("INSERT OR REPLACE INTO object_definitions(id,object_id,position,english_gloss,chinese_gloss,explanation_en,explanation_zh,source_kind,confidence) VALUES (?,?,?,?,?,?,?,?,?)", (stable_id('definition', resource_id), resource_id, 1, None, None, entry['why_en'], None, 'ai_enriched', 0.78))
        db.execute("INSERT OR REPLACE INTO teaching_guidance(resource_object_id,why_en,formation_en,common_mistakes_json,related_object_ids_json,source_id,confidence,review_status) VALUES (?,?,?,?,?,?,?,?)", (resource_id, entry['why_en'], entry['formation_en'], json.dumps(entry.get('common_mistakes', [])), json.dumps(entry.get('related_object_ids', [])), SOURCE_ID, 0.78, 'draft'))
        db.execute("INSERT OR REPLACE INTO relationships(id,source_object_id,target_object_id,relationship_type_code,position,source_kind,confidence) VALUES (?,?,?,?,NULL,'ai_enriched',0.78)", (stable_id('rel', resource_id, 'explains', entry['target_id']), resource_id, entry['target_id'], 'explains'))
        db.execute("INSERT OR IGNORE INTO learning_metadata(object_id) VALUES (?)", (resource_id,))
    db.commit()
    print(f'Imported {len(entries)} structured teaching resources.')


if __name__ == '__main__':
    main()
