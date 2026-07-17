#!/usr/bin/env python3
"""Make pronunciation representations evidence-backed graph data."""
from __future__ import annotations
import argparse,sqlite3,uuid
from pathlib import Path
from canonical_identity import NAMESPACE
def sid(kind,value):return str(uuid.uuid5(NAMESPACE,f'liens:{kind}:{value}'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--database',type=Path,required=True);a=p.parse_args();db=sqlite3.connect(a.database);db.execute('PRAGMA foreign_keys=ON')
 db.executescript("""
 CREATE TABLE IF NOT EXISTS pronunciation_representations (
   id TEXT PRIMARY KEY, pronunciation_object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE,
   representation_kind TEXT NOT NULL, transcription_system TEXT, value_text TEXT, value_json TEXT,
   lifecycle TEXT NOT NULL DEFAULT 'canonical', confidence REAL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
 );
 CREATE TABLE IF NOT EXISTS pronunciation_representation_evidence (
   representation_id TEXT NOT NULL REFERENCES pronunciation_representations(id) ON DELETE CASCADE,
   source_record_id TEXT NOT NULL REFERENCES source_records(id), confidence REAL NOT NULL DEFAULT 1.0,
   PRIMARY KEY(representation_id,source_record_id)
 );
 CREATE UNIQUE INDEX IF NOT EXISTS pronunciation_representation_identity ON pronunciation_representations(pronunciation_object_id,representation_kind,COALESCE(transcription_system,''),COALESCE(value_text,''));
 """)
 db.execute("INSERT OR IGNORE INTO source_catalogs(id,name,license,attribution_text) VALUES ('liens-pronunciation-legacy','Liens pronunciation legacy','Internal migration metadata','Migrated legacy pronunciation metadata.')")
 db.execute("INSERT OR IGNORE INTO source_releases(id,catalog_id,release_label,scope_description) VALUES ('legacy:liens-pronunciation-legacy','liens-pronunciation-legacy','2026-07-17','Legacy pronunciation records.')")
 for row in db.execute("SELECT p.id,p.ipa,p.syllables_json,p.source_id,p.confidence,p.pronunciation_object_id FROM pronunciations p WHERE p.pronunciation_object_id IS NOT NULL"):
  legacy,ipa,syllables,source,confidence,obj=row; record=sid('source-record',f'legacy-pronunciation|{legacy}')
  db.execute("INSERT OR IGNORE INTO source_records(id,release_id,external_key,record_kind) VALUES (?, 'legacy:liens-pronunciation-legacy',?,'pronunciation_legacy')",(record,legacy))
  for kind,system,text,value_json in [('ipa','ipa',ipa,None),('syllabification','legacy_syllables',None,syllables)]:
   if not text and value_json in (None,'[]'):continue
   rid=sid('pronunciation-representation',f'{obj}|{kind}|{system}|{text or value_json}')
   db.execute("INSERT OR IGNORE INTO pronunciation_representations(id,pronunciation_object_id,representation_kind,transcription_system,value_text,value_json,confidence) VALUES (?,?,?,?,?,?,?)",(rid,obj,kind,system,text,value_json,confidence))
   db.execute("INSERT OR IGNORE INTO pronunciation_representation_evidence(representation_id,source_record_id,confidence) VALUES (?,?,?)",(rid,record,confidence or 1.0))
 db.commit();print('Pronunciation representation layer ready.')
if __name__=='__main__':main()
