#!/usr/bin/env python3
"""Seed first-class learning groups and reusable conjugation tense objects."""

from __future__ import annotations

import argparse
import json
import sqlite3
import unicodedata
from pathlib import Path


SOURCE_ID = 'liens_conjugation_learning_catalog'


def normalise(value: str) -> str:
    return ' '.join(unicodedata.normalize('NFC', value).casefold().replace('’', "'").split())


def object_id(kind: str, code: str) -> str:
    return f'fr:{kind}:{normalise(code).replace(" ", "_")}'


def relation_id(source: str, kind: str, target: str) -> str:
    return f'fr:rel:{normalise(source)}:{kind}:{normalise(target)}'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, required=True)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding='utf-8'))
    groups = {group['code']: group for group in catalog['groups']}
    db = sqlite3.connect(args.database)
    db.execute('PRAGMA foreign_keys = ON')
    db.execute("INSERT OR REPLACE INTO sources(id,name,url,license,citation) VALUES (?,?,?,?,?)", (SOURCE_ID, 'Liens Conjugation Learning Catalog', 'app://liens/conjugation-learning-catalog', 'Internal review draft', 'Pedagogical learning-group and tense taxonomy.'))
    for group in groups.values():
        gid = object_id('learning-group', group['code'])
        db.execute("INSERT OR REPLACE INTO language_objects(id,type_code,canonical_form,display_form,normalized_form,cefr_level,source_id,content_status,provenance) VALUES (?,?,?,?,?,?,?,?,?)", (gid, 'learning_group', group['label'], group['label'], normalise(group['label']), group.get('cefr_recommendation'), SOURCE_ID, 'metadata_ready', 'curated'))
        db.execute("INSERT OR REPLACE INTO object_attributes(object_id,key,value_json) VALUES (?,?,?)", (gid, 'learning_group_features', json.dumps({'code': group['code'], 'display_order': group['display_order'], 'cefr_recommendation': group.get('cefr_recommendation')})))
        db.execute("INSERT OR IGNORE INTO learning_metadata(object_id) VALUES (?)", (gid,))
    for tense in catalog['tenses']:
        tid, gid = object_id('tense', tense['code']), object_id('learning-group', tense['group'])
        db.execute("INSERT OR REPLACE INTO language_objects(id,type_code,canonical_form,display_form,normalized_form,cefr_level,source_id,content_status,provenance) VALUES (?,?,?,?,?,?,?,?,?)", (tid, 'conjugation_tense', tense['label'], tense['label'], normalise(tense['label']), tense.get('cefr_recommendation'), SOURCE_ID, 'metadata_ready', 'curated'))
        db.execute("INSERT OR REPLACE INTO conjugation_tense_metadata(object_id,learning_group_id,mood,tense,display_order,cefr_recommendation,formation,source_id,confidence,review_status) VALUES (?,?,?,?,?,?,?,?,?,?)", (tid, gid, tense['mood'], tense['tense'], tense['display_order'], tense.get('cefr_recommendation'), tense.get('formation', 'simple'), SOURCE_ID, 1.0, 'reviewed'))
        db.execute("INSERT OR REPLACE INTO relationships(id,source_object_id,target_object_id,relationship_type_code,position,source_kind,confidence) VALUES (?,?,?,?,?,'curated',1.0)", (relation_id(gid, 'contains', tid), gid, tid, 'contains', tense['display_order']))
        db.execute("INSERT OR IGNORE INTO learning_metadata(object_id) VALUES (?)", (tid,))
    db.commit()
    print(f"Seeded {len(groups)} learning groups and {len(catalog['tenses'])} tense objects.")


if __name__ == '__main__':
    main()
