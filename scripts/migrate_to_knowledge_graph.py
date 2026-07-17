#!/usr/bin/env python3
"""Migrate the v1 Liens wordbank into the Language Object knowledge graph."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def normalise(value: str) -> str:
    return " ".join(value.casefold().replace("’", "'").split())


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE sources (id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL, license TEXT NOT NULL, citation TEXT NOT NULL);
CREATE TABLE object_types (code TEXT PRIMARY KEY, label TEXT NOT NULL, description TEXT NOT NULL);
CREATE TABLE relationship_types (code TEXT PRIMARY KEY, label TEXT NOT NULL, is_directional INTEGER NOT NULL DEFAULT 1, description TEXT NOT NULL);
CREATE TABLE language_objects (
  id TEXT PRIMARY KEY, type_code TEXT NOT NULL REFERENCES object_types(code),
  canonical_form TEXT NOT NULL, display_form TEXT NOT NULL, normalized_form TEXT NOT NULL,
  cefr_level TEXT, part_of_speech TEXT, ipa TEXT, frequency_per_million REAL,
  source_id TEXT REFERENCES sources(id), content_status TEXT NOT NULL,
  provenance TEXT NOT NULL DEFAULT 'curated', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX objects_lookup ON language_objects(normalized_form, type_code);
CREATE INDEX objects_cefr ON language_objects(cefr_level);
CREATE TABLE object_attributes (object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE, key TEXT NOT NULL, value_json TEXT NOT NULL, PRIMARY KEY(object_id, key));
CREATE TABLE object_definitions (
  id TEXT PRIMARY KEY, object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE,
  position INTEGER NOT NULL DEFAULT 1, english_gloss TEXT, chinese_gloss TEXT,
  explanation_en TEXT, explanation_zh TEXT, source_kind TEXT NOT NULL,
  confidence REAL NOT NULL, UNIQUE(object_id, position)
);
CREATE TABLE relationships (
  id TEXT PRIMARY KEY, source_object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE,
  target_object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE,
  relationship_type_code TEXT NOT NULL REFERENCES relationship_types(code),
  position INTEGER, source_kind TEXT NOT NULL DEFAULT 'curated', confidence REAL NOT NULL DEFAULT 1.0,
  UNIQUE(source_object_id, target_object_id, relationship_type_code)
);
CREATE INDEX relationships_from ON relationships(source_object_id, relationship_type_code);
CREATE INDEX relationships_to ON relationships(target_object_id, relationship_type_code);
CREATE TABLE form_features (object_id TEXT PRIMARY KEY REFERENCES language_objects(id) ON DELETE CASCADE, mood TEXT, tense TEXT, person TEXT, number TEXT, gender TEXT);
CREATE TABLE verb_metadata (
  object_id TEXT PRIMARY KEY REFERENCES language_objects(id) ON DELETE CASCADE,
  verb_group_code TEXT, is_irregular INTEGER NOT NULL DEFAULT 0,
  future_stem TEXT, auxiliary_lemma_id TEXT REFERENCES language_objects(id),
  note_en TEXT, note_zh TEXT, source_id TEXT REFERENCES sources(id),
  provenance TEXT NOT NULL DEFAULT 'curated', confidence REAL,
  status TEXT NOT NULL DEFAULT 'metadata_ready', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pronunciations (
  id TEXT PRIMARY KEY, object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE,
  ipa TEXT, syllables_json TEXT NOT NULL DEFAULT '[]', stress_json TEXT NOT NULL DEFAULT '[]',
  variant_code TEXT, audio_source_uri TEXT, local_audio_path TEXT,
  source_id TEXT REFERENCES sources(id), provenance TEXT NOT NULL DEFAULT 'curated',
  confidence REAL, status TEXT NOT NULL DEFAULT 'metadata_ready', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (ipa IS NOT NULL OR audio_source_uri IS NOT NULL OR local_audio_path IS NOT NULL)
);
CREATE INDEX pronunciations_by_object ON pronunciations(object_id, status, confidence DESC);
CREATE TABLE media (id TEXT PRIMARY KEY, object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE, kind TEXT NOT NULL, uri TEXT NOT NULL, license TEXT, source_id TEXT REFERENCES sources(id));
CREATE TABLE learning_metadata (object_id TEXT PRIMARY KEY REFERENCES language_objects(id) ON DELETE CASCADE, save_eligible INTEGER NOT NULL DEFAULT 1, review_eligible INTEGER NOT NULL DEFAULT 1, learning_priority INTEGER NOT NULL DEFAULT 0, tags_json TEXT NOT NULL DEFAULT '[]');
CREATE TABLE ai_generated_content (id TEXT PRIMARY KEY, object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE, content_kind TEXT NOT NULL, payload_json TEXT NOT NULL, model TEXT, prompt_version TEXT, confidence REAL, status TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE review_metadata (learner_id TEXT NOT NULL, object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE, state_json TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(learner_id, object_id));
CREATE VIRTUAL TABLE object_search USING fts5(object_id UNINDEXED, display_form, canonical_form, normalized_form);
CREATE TRIGGER objects_search_insert AFTER INSERT ON language_objects BEGIN INSERT INTO object_search(object_id, display_form, canonical_form, normalized_form) VALUES (new.id, new.display_form, new.canonical_form, new.normalized_form); END;

-- Backwards-compatible read-only lookup contract. IDs are now stable text IDs.
CREATE VIEW lexemes AS SELECT id, canonical_form AS lemma, normalized_form AS normalized_lemma, part_of_speech, cefr_level, frequency_per_million, ipa AS pronunciation_ipa, source_id, content_status FROM language_objects WHERE type_code = 'word';
CREATE VIEW senses AS SELECT d.id, d.object_id AS lexeme_id, d.position, d.english_gloss, d.chinese_gloss, d.explanation_en AS learner_note_en, d.explanation_zh AS learner_note_zh, d.source_kind, d.confidence FROM object_definitions d;
CREATE VIEW forms AS SELECT f.id, r.target_object_id AS lexeme_id, f.display_form AS surface, f.normalized_form AS normalized_surface, x.mood, x.tense, x.person, x.number, x.gender FROM language_objects f JOIN form_features x ON x.object_id=f.id JOIN relationships r ON r.source_object_id=f.id AND r.relationship_type_code='inflected_form_of' WHERE f.type_code='inflected_form';
CREATE VIEW collocations AS SELECT id, display_form AS text, normalized_form AS normalized_text, cefr_level, content_status FROM language_objects WHERE type_code IN ('collocation','expression','idiom');
CREATE VIEW grammar_patterns AS SELECT id, display_form AS name, cefr_level FROM language_objects WHERE type_code='grammar_construction';
CREATE VIEW pronunciation_entries AS SELECT id, object_id, ipa, syllables_json, stress_json, variant_code, audio_source_uri, local_audio_path, source_id, provenance, confidence, status FROM pronunciations;
"""

OBJECT_TYPES = [
    ('word', 'Word', 'A lemma or lexical entry.'), ('inflected_form', 'Inflected form', 'A specific grammatical realization of a word.'),
    ('expression', 'Multi-word expression', 'A fixed or semi-fixed multi-word unit.'), ('idiom', 'Idiom', 'A non-literal conventional expression.'),
    ('collocation', 'Collocation', 'Words that conventionally occur together.'), ('grammar_construction', 'Grammar construction', 'A learnable grammatical structure.'),
    ('sentence_pattern', 'Sentence pattern', 'A reusable syntactic pattern.'), ('conjugation_paradigm', 'Conjugation paradigm', 'A verb and its organized forms.'),
    ('pronunciation', 'Pronunciation', 'A pronunciation learning object.'), ('cefr_concept', 'CEFR concept', 'A level or learning concept.'), ('spelling_exception', 'Spelling exception', 'A non-regular spelling rule or exception.'),
    ('sentence', 'Sentence', 'A complete example sentence.'), ('learning_resource', 'Learning resource', 'An extensible lesson, quiz, passage, or exercise.')
]
RELATIONSHIP_TYPES = [
    ('inflected_form_of', 'Inflected form of', 'Links a form to its lemma.'), ('belongs_to_conjugation', 'Belongs to conjugation', 'Links a verb to its paradigm.'),
    ('member_of_paradigm', 'Member of paradigm', 'Links an inflected form to a paradigm.'), ('contains', 'Contains', 'Links a multiword object to its component object.'),
    ('commonly_used_with', 'Commonly used with', 'A high-value usage connection.'), ('governs_preposition', 'Governs preposition', 'Links a word or construction to a required preposition.'),
    ('expresses', 'Expresses', 'Links an object to a grammatical or semantic concept.'), ('illustrates', 'Illustrates', 'Links an example to the object it illustrates.'),
    ('has_pronunciation', 'Has pronunciation', 'Links an object to pronunciation content.'), ('related_to', 'Related to', 'A safe typed fallback for curated related content.')
]


def oid(kind: str, *parts: object) -> str:
    safe = ':'.join(normalise(str(part)).replace(' ', '_') for part in parts)
    return f'fr:{kind}:{safe}'


def add_relation(db: sqlite3.Connection, source: str, target: str, kind: str) -> None:
    db.execute('INSERT OR IGNORE INTO relationships VALUES (?, ?, ?, ?, NULL, "curated", 1.0)', (oid('rel', source, kind, target), source, target, kind))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True, help='v1 liens-wordbank.sqlite')
    parser.add_argument('--output', type=Path, required=True, help='new liens-knowledge.sqlite')
    args = parser.parse_args()
    if args.output.exists(): args.output.unlink()
    old = sqlite3.connect(args.source); old.row_factory = sqlite3.Row
    db = sqlite3.connect(args.output); db.executescript(SCHEMA)
    db.executemany('INSERT INTO object_types VALUES (?, ?, ?)', OBJECT_TYPES)
    db.executemany('INSERT INTO relationship_types VALUES (?, ?, 1, ?)', RELATIONSHIP_TYPES)
    db.executemany('INSERT INTO sources VALUES (?, ?, ?, ?, ?)', old.execute('SELECT id,name,url,license,citation FROM sources'))
    db.executemany('INSERT INTO metadata VALUES (?, ?)', [('schema_version', '4'), ('architecture', 'Language Object knowledge graph'), ('migration_source', str(args.source)), ('pronunciation_model', 'pronunciations: IPA, syllables, stress, audio references, provenance, confidence')])
    lexeme_map: dict[int, str] = {}
    for row in old.execute('SELECT * FROM lexemes'):
        obj_id = oid('word', row['normalized_lemma'], row['part_of_speech'])
        lexeme_map[row['id']] = obj_id
        db.execute('INSERT INTO language_objects (id,type_code,canonical_form,display_form,normalized_form,cefr_level,part_of_speech,ipa,frequency_per_million,source_id,content_status,provenance) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (obj_id, 'word', row['lemma'], row['lemma'], row['normalized_lemma'], row['cefr_level'], row['part_of_speech'], row['pronunciation_ipa'], row['frequency_per_million'], row['source_id'], row['content_status'], 'curated'))
        if row['pronunciation_ipa']:
            db.execute('INSERT INTO pronunciations (id,object_id,ipa,source_id,provenance,confidence,status) VALUES (?,?,?,?,?,?,?)', (oid('pronunciation', obj_id), obj_id, row['pronunciation_ipa'], row['source_id'], 'curated', 1.0, 'curated'))
        db.execute('INSERT INTO learning_metadata (object_id,learning_priority) VALUES (?, ?)', (obj_id, round(row['frequency_per_million'] or 0)))
        if row['part_of_speech'] in ('VER', 'V'):
            paradigm = oid('paradigm', row['normalized_lemma'])
            db.execute('INSERT OR IGNORE INTO language_objects (id,type_code,canonical_form,display_form,normalized_form,cefr_level,part_of_speech,source_id,content_status,provenance) VALUES (?,?,?,?,?,?,?,?,?,?)', (paradigm, 'conjugation_paradigm', row['lemma'], f"{row['lemma']} conjugation", row['normalized_lemma'], row['cefr_level'], 'VER', row['source_id'], 'metadata_ready', 'curated'))
            db.execute('INSERT OR IGNORE INTO learning_metadata (object_id) VALUES (?)', (paradigm,)); add_relation(db, obj_id, paradigm, 'belongs_to_conjugation')
    for row in old.execute('SELECT * FROM senses'):
        db.execute('INSERT INTO object_definitions VALUES (?,?,?,?,?,?,?,?,?)', (oid('definition', row['id']), lexeme_map[row['lexeme_id']], row['position'], row['english_gloss'], row['chinese_gloss'], row['learner_note_en'], row['learner_note_zh'], row['source_kind'], row['confidence']))
    for row in old.execute('SELECT * FROM forms'):
        word = lexeme_map[row['lexeme_id']]; form = oid('form', word, row['normalized_surface'], row['mood'] or '', row['tense'] or '', row['person'] or '')
        db.execute('INSERT INTO language_objects (id,type_code,canonical_form,display_form,normalized_form,content_status,provenance) VALUES (?,?,?,?,?,?,?)', (form, 'inflected_form', row['surface'], row['surface'], row['normalized_surface'], 'curated', 'curated'))
        db.execute('INSERT INTO form_features VALUES (?,?,?,?,?,?)', (form,row['mood'],row['tense'],row['person'],row['number'],row['gender']))
        db.execute('INSERT INTO learning_metadata (object_id) VALUES (?)', (form,)); add_relation(db, form, word, 'inflected_form_of')
        paradigm = db.execute("SELECT target_object_id FROM relationships WHERE source_object_id=? AND relationship_type_code='belongs_to_conjugation'", (word,)).fetchone()
        if paradigm: add_relation(db, form, paradigm[0], 'member_of_paradigm')
    for row in old.execute('SELECT * FROM grammar_patterns'):
        item = oid('grammar', row['name']); db.execute('INSERT INTO language_objects (id,type_code,canonical_form,display_form,normalized_form,cefr_level,content_status,provenance) VALUES (?,?,?,?,?,?,?,?)', (item,'grammar_construction',row['name'],row['name'],normalise(row['name']),row['cefr_level'],'curated','curated')); db.execute('INSERT INTO learning_metadata (object_id) VALUES (?)', (item,)); db.execute('INSERT INTO object_definitions VALUES (?,?,?,?,?,?,?,?,?)', (oid('definition',item),item,1,None,None,row['explanation_en'],row['explanation_zh'],'curated',1.0))
    for row in old.execute('SELECT * FROM collocations'):
        item = oid('collocation', row['normalized_text']); db.execute('INSERT INTO language_objects (id,type_code,canonical_form,display_form,normalized_form,cefr_level,content_status,provenance) VALUES (?,?,?,?,?,?,?,?)', (item,'collocation',row['text'],row['text'],row['normalized_text'],row['cefr_level'],row['content_status'],'curated')); db.execute('INSERT INTO learning_metadata (object_id) VALUES (?)', (item,))
    # Canonical graph examples: these are objects, not special UI routes.
    def word_id(text: str) -> str | None:
        row = db.execute("SELECT id FROM language_objects WHERE type_code='word' AND normalized_form=? ORDER BY frequency_per_million DESC LIMIT 1", (normalise(text),)).fetchone()
        return row[0] if row else None
    expression = oid('expression', 'avoir besoin de')
    db.execute('INSERT OR IGNORE INTO language_objects (id,type_code,canonical_form,display_form,normalized_form,cefr_level,content_status,provenance) VALUES (?,?,?,?,?,?,?,?)', (expression, 'expression', 'avoir besoin de', 'avoir besoin de', 'avoir besoin de', 'A2', 'curated', 'curated'))
    db.execute('INSERT OR IGNORE INTO learning_metadata (object_id) VALUES (?)', (expression,))
    db.execute('INSERT OR IGNORE INTO object_definitions VALUES (?,?,?,?,?,?,?,?,?)', (oid('definition', expression), expression, 1, 'to need', '需要', 'A high-frequency expression: avoir besoin de + noun or infinitive.', '常用表达：avoir besoin de + 名词或不定式。', 'curated', 1.0))
    for component in ('avoir', 'besoin', 'de'):
        if target := word_id(component): add_relation(db, expression, target, 'contains')
    progressive = oid('grammar', 'être en train de + infinitive')
    db.execute('INSERT OR IGNORE INTO language_objects (id,type_code,canonical_form,display_form,normalized_form,cefr_level,content_status,provenance) VALUES (?,?,?,?,?,?,?,?)', (progressive, 'grammar_construction', 'être en train de + infinitive', 'être en train de + infinitive', 'être en train de + infinitive', 'B1', 'curated', 'curated'))
    db.execute('INSERT OR IGNORE INTO learning_metadata (object_id) VALUES (?)', (progressive,))
    if target := word_id('être'): add_relation(db, progressive, target, 'contains')
    for verb, preposition in (('venir', 'chez'), ('penser', 'à')):
        source, target = word_id(verb), word_id(preposition)
        if source and target: add_relation(db, source, target, 'governs_preposition' if verb == 'penser' else 'commonly_used_with')
    db.commit(); db.execute('VACUUM'); print(f'Migrated {len(lexeme_map)} words into {args.output}')


if __name__ == '__main__': main()
