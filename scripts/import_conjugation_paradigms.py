#!/usr/bin/env python3
"""Import declarative verb paradigms as graph-native inflected-form objects."""

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


def add_relation(db: sqlite3.Connection, source: str, target: str, relationship_type: str) -> None:
    db.execute(
        "INSERT OR REPLACE INTO relationships "
        "(id,source_object_id,target_object_id,relationship_type_code,position,source_kind,confidence) "
        "VALUES (?,?,?,?,NULL,'ai_enriched',0.78)",
        (stable_id('rel', source, relationship_type, target), source, target, relationship_type),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    paradigms = json.loads(args.input.read_text(encoding='utf-8'))

    db = sqlite3.connect(args.database)
    db.execute('PRAGMA foreign_keys = ON')
    db.execute(
        "INSERT OR REPLACE INTO sources(id,name,url,license,citation) VALUES (?,?,?,?,?)",
        (SOURCE_ID, 'Liens Core Conjugation Draft', 'app://liens/core-conjugations',
         'Internal review draft', 'Declarative conjugation data; review before promoting to curated content.'),
    )
    # The importer owns these generated rows. Removing them first makes every
    # run reproducible while preserving forms imported from other sources.
    db.execute("DELETE FROM language_objects WHERE type_code='inflected_form' AND source_id=?", (SOURCE_ID,))
    imported = 0
    for paradigm in paradigms:
        row = db.execute(
            "SELECT id FROM language_objects WHERE type_code='word' AND normalized_form=? "
            "AND part_of_speech IN ('VER','V') ORDER BY frequency_per_million DESC LIMIT 1",
            (normalise(paradigm['lemma']),),
        ).fetchone()
        if not row:
            raise ValueError(f"Verb lemma not found: {paradigm['lemma']}")
        lemma_id = row[0]
        paradigm_row = db.execute(
            "SELECT target_object_id FROM relationships WHERE source_object_id=? "
            "AND relationship_type_code='belongs_to_conjugation'",
            (lemma_id,),
        ).fetchone()
        paradigm_id = paradigm_row[0] if paradigm_row else None
        for form in paradigm['forms']:
            # Match the historic graph ID contract: person distinguishes the
            # two identical present forms (for example, je/tu fais), while
            # number remains structured metadata rather than identity.
            form_id = stable_id('form', lemma_id, form['surface'], form['mood'], form['tense'], str(form.get('person', '')))
            db.execute(
                "INSERT OR REPLACE INTO language_objects "
                "(id,type_code,canonical_form,display_form,normalized_form,source_id,content_status,provenance) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (form_id, 'inflected_form', form['surface'], form['surface'], normalise(form['surface']), SOURCE_ID, 'ai_enriched', 'ai_enriched'),
            )
            db.execute(
                "INSERT OR REPLACE INTO form_features(object_id,mood,tense,person,number,gender) VALUES (?,?,?,?,?,NULL)",
                (form_id, form['mood'], form['tense'], form.get('person'), form.get('number')),
            )
            db.execute("INSERT OR IGNORE INTO learning_metadata(object_id) VALUES (?)", (form_id,))
            add_relation(db, form_id, lemma_id, 'inflected_form_of')
            if paradigm_id:
                add_relation(db, form_id, paradigm_id, 'member_of_paradigm')
            imported += 1
    db.execute("INSERT INTO metadata(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ('core_conjugation_status', f'{imported} declarative form records; review required'))
    db.commit()
    print(f'Imported {imported} inflected-form records for {len(paradigms)} verb paradigms.')


if __name__ == '__main__':
    main()
