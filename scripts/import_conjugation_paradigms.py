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


def tense_paradigm_id(lemma_id: str, mood: str, tense: str) -> str:
    return stable_id('paradigm', lemma_id, mood or 'unclassified', tense or 'unclassified')


def materialize_tense_paradigm(
    db: sqlite3.Connection, root_id: str, lemma: str, lemma_id: str, spec: dict
) -> str:
    mood, tense = spec.get('mood') or '', spec.get('tense') or ''
    tense_id = tense_paradigm_id(lemma_id, mood, tense)
    label = spec.get('label') or f"{mood} {tense}".strip()
    features = {
        'mood': mood,
        'tense': tense,
        'label': label,
        'display_order': spec.get('display_order', 999),
        'formation': spec.get('formation', 'simple'),
        'version': 1,
    }
    db.execute(
        "INSERT OR REPLACE INTO language_objects "
        "(id,type_code,canonical_form,display_form,normalized_form,part_of_speech,source_id,content_status,provenance) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (tense_id, 'conjugation_paradigm', f"{lemma} {mood} {tense}", label,
         normalise(f"{lemma} {mood} {tense}"), 'VER', SOURCE_ID, 'metadata_ready', 'ai_enriched'),
    )
    db.execute(
        "INSERT OR REPLACE INTO object_attributes(object_id,key,value_json) VALUES (?,?,?)",
        (tense_id, 'conjugation_features', json.dumps(features)),
    )
    db.execute("INSERT OR IGNORE INTO learning_metadata(object_id) VALUES (?)", (tense_id,))
    add_relation(db, root_id, tense_id, 'contains')
    return tense_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, required=True)
    args = parser.parse_args()
    paradigms = json.loads(args.input.read_text(encoding='utf-8'))
    catalog = json.loads(args.catalog.read_text(encoding='utf-8'))

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
    db.execute("DELETE FROM language_objects WHERE type_code='conjugation_paradigm' AND source_id=?", (SOURCE_ID,))
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
        root_paradigm_id = paradigm_row[0] if paradigm_row else stable_id('paradigm', lemma_id)
        if not paradigm_row:
            db.execute(
                "INSERT OR IGNORE INTO language_objects "
                "(id,type_code,canonical_form,display_form,normalized_form,part_of_speech,source_id,content_status,provenance) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (root_paradigm_id, 'conjugation_paradigm', paradigm['lemma'], f"{paradigm['lemma']} conjugation",
                 normalise(paradigm['lemma']), 'VER', SOURCE_ID, 'metadata_ready', 'ai_enriched'),
            )
            add_relation(db, lemma_id, root_paradigm_id, 'belongs_to_conjugation')
        tense_paradigms: dict[tuple[str, str], str] = {}
        for spec in catalog:
            key = (spec.get('mood') or '', spec.get('tense') or '')
            tense_paradigms[key] = materialize_tense_paradigm(
                db, root_paradigm_id, paradigm['lemma'], lemma_id, spec
            )
        grouped_forms: dict[tuple[str, str], list[dict]] = {}
        for form in paradigm['forms']:
            grouped_forms.setdefault((form.get('mood') or '', form.get('tense') or ''), []).append(form)
        for (mood, tense) in grouped_forms:
            if (mood, tense) not in tense_paradigms:
                tense_paradigms[(mood, tense)] = materialize_tense_paradigm(
                    db, root_paradigm_id, paradigm['lemma'], lemma_id,
                    {'mood': mood, 'tense': tense},
                )
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
            add_relation(db, form_id, tense_paradigms[(form.get('mood') or '', form.get('tense') or '')], 'member_of_paradigm')
            imported += 1
    db.execute("INSERT INTO metadata(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ('core_conjugation_status', f'{imported} declarative form records; review required'))
    db.commit()
    print(f'Imported {imported} inflected-form records for {len(paradigms)} verb paradigms.')


if __name__ == '__main__':
    main()
