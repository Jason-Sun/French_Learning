#!/usr/bin/env python3
"""Idempotently add persistence tables for reproducible sentence analyses."""
import argparse
import sqlite3
from pathlib import Path

parser=argparse.ArgumentParser(); parser.add_argument('--database', type=Path, required=True); args=parser.parse_args()
db=sqlite3.connect(args.database)
db.executescript('''
CREATE TABLE IF NOT EXISTS sentence_analysis_instances (
 id TEXT PRIMARY KEY, sentence TEXT NOT NULL, normalized_sentence TEXT NOT NULL, engine_version TEXT NOT NULL,
 provenance TEXT NOT NULL, confidence REAL NOT NULL, cache_status TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sentence_analysis_nodes (
 id TEXT PRIMARY KEY, analysis_id TEXT NOT NULL REFERENCES sentence_analysis_instances(id) ON DELETE CASCADE,
 node_type TEXT NOT NULL, object_id TEXT REFERENCES language_objects(id), label TEXT NOT NULL,
 start_offset INTEGER, end_offset INTEGER, payload_json TEXT NOT NULL, source TEXT NOT NULL, confidence REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sentence_analysis_edges (
 analysis_id TEXT NOT NULL REFERENCES sentence_analysis_instances(id) ON DELETE CASCADE,
 source_node_id TEXT NOT NULL, target_node_id TEXT NOT NULL, relationship_type TEXT NOT NULL, confidence REAL NOT NULL,
 PRIMARY KEY (analysis_id, source_node_id, target_node_id, relationship_type)
);
CREATE TABLE IF NOT EXISTS sentence_learning_items (
 analysis_id TEXT NOT NULL REFERENCES sentence_analysis_instances(id) ON DELETE CASCADE,
 object_id TEXT REFERENCES language_objects(id), kind TEXT NOT NULL, payload_json TEXT NOT NULL, source TEXT NOT NULL, confidence REAL NOT NULL,
 PRIMARY KEY (analysis_id, object_id, kind)
);
''')
grammar = [
 ('fr:grammar:passé_composé', 'passé composé', 'A2', 'A completed past action built with a present auxiliary and a past participle.'),
 ('fr:grammar:futur_proche', 'futur proche', 'A1', 'Aller in the present tense followed by an infinitive expresses a near or intended future.'),
 ('fr:grammar:negation', 'negation', 'A1', 'Standard negation usually places ne before the verb and pas after it.'),
 ('fr:grammar:reflexive_construction', 'reflexive construction', 'A2', 'A reflexive pronoun refers back to the subject and forms part of the verb construction.'),
 ('fr:grammar:simple_subordinate_clause', 'simple subordinate clause', 'B1', 'A conjunction such as que introduces a clause dependent on another clause.'),
]
for object_id, name, level, explanation in grammar:
    db.execute("INSERT OR IGNORE INTO language_objects (id,type_code,canonical_form,display_form,normalized_form,cefr_level,content_status,provenance) VALUES (?,?,?,?,?,?,?,?)", (object_id, 'grammar_construction', name, name, name.casefold(), level, 'curated', 'curated'))
    db.execute("INSERT OR IGNORE INTO learning_metadata (object_id) VALUES (?)", (object_id,))
    db.execute("INSERT OR IGNORE INTO object_definitions (id,object_id,position,explanation_en,source_kind,confidence) VALUES (?,?,?,?,?,?)", (f'fr:definition:{object_id}', object_id, 1, explanation, 'curated', 1.0))
db.execute("INSERT OR REPLACE INTO metadata VALUES ('sentence_intelligence_schema_version','1')")
db.commit(); print(f'Updated {args.database}')
