#!/usr/bin/env python3
"""Build a small, graph-native validation set for compound and periphrastic tenses."""

from __future__ import annotations

import argparse
import json
import sqlite3
import unicodedata
from pathlib import Path


SOURCE_ID = 'liens_core_realization_draft'
SUBJECTS = {
    ('1', 'singular'): 'je', ('2', 'singular'): 'tu', ('3', 'singular'): 'il / elle / on',
    ('1', 'plural'): 'nous', ('2', 'plural'): 'vous', ('3', 'plural'): 'ils / elles',
}
PERSONS = [('1', 'singular'), ('2', 'singular'), ('3', 'singular'), ('1', 'plural'), ('2', 'plural'), ('3', 'plural')]


def normalise(value: str) -> str:
    return ' '.join(unicodedata.normalize('NFC', value).casefold().replace('’', "'").split())


def stable_id(kind: str, *parts: str) -> str:
    return f"fr:{kind}:" + ':'.join(normalise(part).replace(' ', '_') for part in parts)


def add_relation(db: sqlite3.Connection, source: str, target: str, relationship_type: str) -> None:
    db.execute("INSERT OR REPLACE INTO relationships(id,source_object_id,target_object_id,relationship_type_code,position,source_kind,confidence) VALUES (?,?,?,?,NULL,'ai_enriched',0.78)", (stable_id('rel', source, relationship_type, target), source, target, relationship_type))


def form_id(db: sqlite3.Connection, lemma_id: str, mood: str, tense: str, person: str | None = None, number: str | None = None) -> str:
    query = """SELECT f.id FROM language_objects f JOIN relationships r ON r.source_object_id=f.id AND r.relationship_type_code='inflected_form_of' JOIN form_features x ON x.object_id=f.id WHERE r.target_object_id=? AND x.mood=? AND x.tense=?"""
    values: list[str] = [lemma_id, mood, tense]
    if person is not None:
        query += ' AND x.person=?'; values.append(person)
    if number is not None:
        query += ' AND x.number=?'; values.append(number)
    row = db.execute(query, values).fetchone()
    if not row:
        raise ValueError(f'Missing form: {lemma_id} {mood} {tense} {person} {number}')
    return row[0]


def paradigm_id(db: sqlite3.Connection, lemma_id: str, tense_object_id: str) -> str:
    row = db.execute("""SELECT p.id FROM relationships v JOIN relationships c ON c.source_object_id=v.target_object_id AND c.relationship_type_code='contains' JOIN language_objects p ON p.id=c.target_object_id JOIN relationships t ON t.source_object_id=p.id AND t.relationship_type_code='realizes_tense' WHERE v.source_object_id=? AND v.relationship_type_code='belongs_to_conjugation' AND t.target_object_id=?""", (lemma_id, tense_object_id)).fetchone()
    if not row:
        raise ValueError(f'Missing paradigm for {lemma_id} / {tense_object_id}')
    return row[0]


def display(subject: str, parts: list[str]) -> str:
    first = parts[0]
    if subject == 'je' and first[:1].lower() in 'aeiouéèêëàâîïôöùûüh':
        subject = "j'"
    return f"{subject}{'' if subject.endswith(chr(39)) else ' '}{' '.join(parts)}"


def insert_realization(db: sqlite3.Connection, lemma_id: str, paradigm: str, kind: str, person: str, number: str, components: list[tuple[str, str]]) -> None:
    component_forms = [db.execute('SELECT display_form FROM language_objects WHERE id=?', (object_id,)).fetchone()[0] for _, object_id in components]
    object_id = stable_id('realization', lemma_id, paradigm, person, number)
    surface = display(SUBJECTS[(person, number)], component_forms)
    db.execute("INSERT OR REPLACE INTO language_objects(id,type_code,canonical_form,display_form,normalized_form,source_id,content_status,provenance) VALUES (?,?,?,?,?,?,?,?)", (object_id, 'conjugation_realization', f'{lemma_id} {kind} {person} {number}', surface, normalise(surface), SOURCE_ID, 'ai_enriched', 'ai_enriched'))
    db.execute("INSERT OR REPLACE INTO conjugation_realizations(object_id,paradigm_id,realization_type,person,number,source_id,confidence,review_status) VALUES (?,?,?,?,?,?,?,?)", (object_id, paradigm, kind, person, number, SOURCE_ID, 0.78, 'draft'))
    for position, (role, component_id) in enumerate(components, 1):
        db.execute("INSERT OR REPLACE INTO conjugation_realization_components(realization_id,position,role_code,object_id) VALUES (?,?,?,?)", (object_id, position, role, component_id))
    db.execute("INSERT OR IGNORE INTO learning_metadata(object_id) VALUES (?)", (object_id,))
    add_relation(db, object_id, paradigm, 'member_of_paradigm')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    verbs = json.loads(args.input.read_text(encoding='utf-8'))
    db = sqlite3.connect(args.database)
    db.execute('PRAGMA foreign_keys = ON')
    db.execute("INSERT OR REPLACE INTO sources(id,name,url,license,citation) VALUES (?,?,?,?,?)", (SOURCE_ID, 'Liens Core Realization Draft', 'app://liens/core-realizations', 'Internal review draft', 'Graph-native compound and periphrastic validation data.'))
    db.execute("DELETE FROM language_objects WHERE type_code='conjugation_realization' AND source_id=?", (SOURCE_ID,))
    avoir_id = db.execute("SELECT id FROM language_objects WHERE type_code='word' AND normalized_form='avoir' AND part_of_speech IN ('VER','V') LIMIT 1").fetchone()[0]
    aller_id = db.execute("SELECT id FROM language_objects WHERE type_code='word' AND normalized_form='aller' AND part_of_speech IN ('VER','V') LIMIT 1").fetchone()[0]
    pc_tense, fp_tense = 'fr:tense:compound_passe_compose', 'fr:tense:periphrastic_futur_proche'
    imported = 0
    for verb in verbs:
        lemma_id = db.execute("SELECT id FROM language_objects WHERE type_code='word' AND normalized_form=? AND part_of_speech IN ('VER','V') LIMIT 1", (normalise(verb['lemma']),)).fetchone()[0]
        auxiliary_id = db.execute('SELECT auxiliary_lemma_id FROM verb_metadata WHERE object_id=?', (lemma_id,)).fetchone()[0]
        pc_paradigm, fp_paradigm = paradigm_id(db, lemma_id, pc_tense), paradigm_id(db, lemma_id, fp_tense)
        participle = form_id(db, lemma_id, 'participle', 'past')
        for person, number in PERSONS:
            auxiliary = form_id(db, auxiliary_id, 'indicative', 'present', person, number)
            aller = form_id(db, aller_id, 'indicative', 'present', person, number)
            insert_realization(db, lemma_id, pc_paradigm, 'compound', person, number, [('auxiliary', auxiliary), ('past_participle', participle)])
            insert_realization(db, lemma_id, fp_paradigm, 'periphrastic', person, number, [('carrier_verb', aller), ('main_infinitive', lemma_id)])
            imported += 2
    db.commit()
    print(f'Imported {imported} graph-native realizations for {len(verbs)} core verbs.')


if __name__ == '__main__':
    main()
