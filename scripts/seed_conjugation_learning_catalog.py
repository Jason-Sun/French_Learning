#!/usr/bin/env python3
"""Seed first-class learning groups and reusable conjugation tense objects."""

from __future__ import annotations

import argparse
import json
import sqlite3
import unicodedata
from pathlib import Path

from canonical_identity import canonical_uuid


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
        db.execute("""INSERT INTO language_objects(id,type_code,canonical_form,display_form,normalized_form,cefr_level,source_id,content_status,provenance)
                      VALUES (?,?,?,?,?,?,?,?,?)
                      ON CONFLICT(id) DO UPDATE SET canonical_form=excluded.canonical_form, display_form=excluded.display_form,
                        normalized_form=excluded.normalized_form, cefr_level=excluded.cefr_level, source_id=excluded.source_id,
                        content_status=excluded.content_status, provenance=excluded.provenance""", (gid, 'learning_group', group['label'], group['label'], normalise(group['label']), group.get('cefr_recommendation'), SOURCE_ID, 'metadata_ready', 'curated'))
        identity_key = f"fr|learning_group|code={normalise(group['code'])}"
        db.execute("INSERT OR IGNORE INTO canonical_objects(canonical_id,language_object_id,object_type_code,identity_key) VALUES (?,?,?,?)", (canonical_uuid(identity_key), gid, 'learning_group', identity_key))
        db.execute("INSERT OR REPLACE INTO object_attributes(object_id,key,value_json) VALUES (?,?,?)", (gid, 'learning_group_features', json.dumps({'code': group['code'], 'display_order': group['display_order'], 'cefr_recommendation': group.get('cefr_recommendation')})))
        db.execute("INSERT OR IGNORE INTO learning_metadata(object_id) VALUES (?)", (gid,))
    for tense in catalog['tenses']:
        tid, gid = object_id('tense', tense['code']), object_id('learning-group', tense['group'])
        db.execute("""INSERT INTO language_objects(id,type_code,canonical_form,display_form,normalized_form,cefr_level,source_id,content_status,provenance)
                      VALUES (?,?,?,?,?,?,?,?,?)
                      ON CONFLICT(id) DO UPDATE SET canonical_form=excluded.canonical_form, display_form=excluded.display_form,
                        normalized_form=excluded.normalized_form, cefr_level=excluded.cefr_level, source_id=excluded.source_id,
                        content_status=excluded.content_status, provenance=excluded.provenance""", (tid, 'conjugation_tense', tense['label'], tense['label'], normalise(tense['label']), tense.get('cefr_recommendation'), SOURCE_ID, 'metadata_ready', 'curated'))
        identity_key = f"fr|conjugation_tense|mood={normalise(tense['mood'])}|tense={normalise(tense['tense'])}"
        db.execute("INSERT OR IGNORE INTO canonical_objects(canonical_id,language_object_id,object_type_code,identity_key) VALUES (?,?,?,?)", (canonical_uuid(identity_key), tid, 'conjugation_tense', identity_key))
        db.execute("""INSERT INTO conjugation_tense_metadata(object_id,learning_group_id,mood,tense,display_order,cefr_recommendation,formation,source_id,confidence,review_status)
                      VALUES (?,?,?,?,?,?,?,?,?,?)
                      ON CONFLICT(object_id) DO UPDATE SET learning_group_id=excluded.learning_group_id, mood=excluded.mood,
                        tense=excluded.tense, display_order=excluded.display_order, cefr_recommendation=excluded.cefr_recommendation,
                        formation=excluded.formation, source_id=excluded.source_id, confidence=excluded.confidence,
                        review_status=excluded.review_status""", (tid, gid, tense['mood'], tense['tense'], tense['display_order'], tense.get('cefr_recommendation'), tense.get('formation', 'simple'), SOURCE_ID, 1.0, 'reviewed'))
        db.execute("""INSERT INTO relationships(id,source_object_id,target_object_id,relationship_type_code,position,source_kind,confidence)
                      VALUES (?,?,?,?,?,'curated',1.0)
                      ON CONFLICT(id) DO UPDATE SET position=excluded.position, source_kind=excluded.source_kind, confidence=excluded.confidence""", (relation_id(gid, 'contains', tid), gid, tid, 'contains', tense['display_order']))
        db.execute("INSERT OR IGNORE INTO learning_metadata(object_id) VALUES (?)", (tid,))
    db.commit()
    print(f"Seeded {len(groups)} learning groups and {len(catalog['tenses'])} tense objects.")


if __name__ == '__main__':
    main()
