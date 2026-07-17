#!/usr/bin/env python3
"""Add source-backed sentence alignment and lexical-relation extension points."""
from __future__ import annotations
import argparse,hashlib,sqlite3
from pathlib import Path
MIGRATION_ID='20260717_sentence_alignment_schema'
SCHEMA="""
INSERT OR IGNORE INTO relationship_types(code,label,is_directional,description) VALUES
 ('synonym_of','Synonym of',0,'Links lexical objects with a source-backed synonym relation.'),
 ('antonym_of','Antonym of',0,'Links lexical objects with a source-backed antonym relation.');
INSERT OR IGNORE INTO fact_predicates(code,value_kind,label,description) VALUES
 ('english_translation','text','English translation','An evidence-backed English translation for a sentence or multi-word object.');
CREATE TABLE IF NOT EXISTS sentence_source_alignments (
 sentence_object_id TEXT NOT NULL REFERENCES language_objects(id) ON DELETE CASCADE,
 target_canonical_id TEXT NOT NULL REFERENCES canonical_objects(canonical_id) ON DELETE RESTRICT,
 source_record_id TEXT NOT NULL REFERENCES source_records(id),
 start_offset INTEGER, end_offset INTEGER,
 PRIMARY KEY(sentence_object_id,target_canonical_id,source_record_id,start_offset,end_offset)
);
"""
def main():
 p=argparse.ArgumentParser();p.add_argument('--database',type=Path,required=True);a=p.parse_args();db=sqlite3.connect(a.database);db.execute('PRAGMA foreign_keys=ON');db.executescript(SCHEMA);db.execute("INSERT OR IGNORE INTO schema_migrations(id,checksum,description) VALUES (?,?,?)",(MIGRATION_ID,hashlib.sha256(SCHEMA.encode()).hexdigest(),'Source-backed sentence alignment and lexical synonym/antonym relation support.'));db.commit();print('Sentence alignment schema is ready.')
if __name__=='__main__':main()
