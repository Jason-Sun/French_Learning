#!/usr/bin/env python3
"""Import attributable A1 examples and explicit lexical relations from Kaikki."""
from __future__ import annotations
import argparse,hashlib,json,sqlite3,unicodedata,uuid
from pathlib import Path
from canonical_identity import NAMESPACE,canonical_uuid
POS={'noun':'NOM','verb':'VER','adj':'ADJ','adv':'ADV','pron':'PRO','prep':'PRP','conj':'KON','intj':'INT','article':'DET:ART'}
def n(s):return ' '.join(unicodedata.normalize('NFC',s).casefold().replace('’',"'").split())
def sid(k,v):return str(uuid.uuid5(NAMESPACE,f'liens:{k}:{v}'))
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--database',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();m=json.loads(a.manifest.read_text())
 if digest(a.source)!=m['release']['sha256']:raise ValueError('Kaikki source SHA-256 mismatch')
 db=sqlite3.connect(a.database);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON');rid=m['release']['id'];run=f'import:{rid}:a1-connections';db.execute("INSERT OR IGNORE INTO import_runs(id,release_id,importer_name,importer_version,status,completed_at) VALUES (?,?,?,?, 'completed',CURRENT_TIMESTAMP)",(run,rid,'kaikki_enwiktionary_a1_connections','1'))
 words={(n(x['canonical_form']),x['part_of_speech']):(x['id'],x['canonical_id'],x['cefr_level']) for x in db.execute("SELECT o.id,o.canonical_form,o.part_of_speech,o.cefr_level,c.canonical_id FROM language_objects o JOIN canonical_objects c ON c.language_object_id=o.id WHERE o.type_code='word' AND o.cefr_level='A1'")}
 senses={(r['source_record_id']):r['canonical_id'] for r in db.execute("SELECT m.source_record_id,m.canonical_id FROM import_record_mappings m WHERE m.import_run_id=?",(f'import:{rid}:a1-senses',))}
 stats={'sentences':set(),'translations':set(),'illustrates':set(),'relations':set()};db.commit();db.execute('BEGIN')
 try:
  with a.source.open() as f:
   for line in f:
    e=json.loads(line);pos=POS.get(e.get('pos'));key=(n(e.get('word','')),pos)
    if not pos or key not in words:continue
    owner,ownercid,cefr=words[key]
    for order,s in enumerate(e.get('senses',[]),1):
     sk=s.get('id') or f'{e["word"]}:{order}';sr=sid('source-record',f'{rid}|sense:{sk}');sensecid=senses.get(sr)
     if not sensecid:continue
     for exorder,ex in enumerate(s.get('examples',[]),1):
      text=ex.get('text','').strip();translation=(ex.get('translation') or ex.get('english') or '').strip()
      if ex.get('type')!='example' or not text or not translation or len(text)>160:continue
      er=sid('source-record',f'{rid}|example:{sk}:{exorder}');payload={'sense':sk,'example':ex};db.execute("INSERT OR IGNORE INTO source_records(id,release_id,external_key,record_kind,content_hash) VALUES (?,?,?,?,?)",(er,rid,f'example:{sk}:{exorder}','example_sentence',hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest()))
      ident=f'fr|sentence|{n(text)}';cid=canonical_uuid(ident);oid=f'fr:sentence:{hashlib.sha256(ident.encode()).hexdigest()[:20]}';db.execute("INSERT OR IGNORE INTO language_objects(id,type_code,canonical_form,display_form,normalized_form,cefr_level,source_id,content_status,provenance) VALUES (?,?,?, ?,?,?,?,'metadata_ready','curated')",(oid,'sentence',text,text,n(text),cefr,'kaikki-enwiktionary'));db.execute("INSERT OR IGNORE INTO canonical_objects(canonical_id,language_object_id,object_type_code,identity_key) VALUES (?,?, 'sentence',?)",(cid,oid,ident));db.execute("INSERT OR IGNORE INTO import_record_mappings(import_run_id,source_record_id,canonical_id,mapping_kind,confidence) VALUES (?,?,?,'kaikki_example_sentence',1)",(run,er,cid));fid=sid('fact',f'{cid}|english_translation|{n(translation)}');db.execute("INSERT OR IGNORE INTO canonical_facts(id,canonical_subject_id,predicate_code) VALUES (?,?, 'english_translation')",(fid,cid));db.execute("INSERT OR IGNORE INTO fact_text_values(fact_id,language_code,value_text) VALUES (?, 'en',?)",(fid,translation));db.execute("INSERT OR IGNORE INTO fact_evidence(fact_id,source_record_id,evidence_role,confidence) VALUES (?,?,'asserts',1)",(fid,er));rel=sid('relationship',f'{oid}|illustrates|{owner}');db.execute("INSERT OR IGNORE INTO relationships(id,source_object_id,target_object_id,relationship_type_code,source_kind,confidence) VALUES (?,?,?,'illustrates','curated',1)",(rel,oid,owner));db.execute("INSERT OR IGNORE INTO relationship_evidence(relationship_id,source_record_id,confidence) VALUES (?,?,1)",(rel,er));db.execute("INSERT OR IGNORE INTO sentence_source_alignments(sentence_object_id,target_canonical_id,source_record_id) VALUES (?,?,?)",(oid,sensecid,er));stats['sentences'].add(oid);stats['translations'].add(fid);stats['illustrates'].add(rel)
     for kind,reltype in [('synonyms','synonym_of'),('antonyms','antonym_of')]:
      for target in s.get(kind,[]):
       word=target.get('word','') if isinstance(target,dict) else ''; tk=(n(word),pos)
       if tk not in words:continue
       toid=words[tk][0]; rel=sid('relationship',f'{owner}|{reltype}|{toid}');db.execute("INSERT OR IGNORE INTO relationships(id,source_object_id,target_object_id,relationship_type_code,source_kind,confidence) VALUES (?,?,?,?,'curated',1)",(rel,owner,toid,reltype));db.execute("INSERT OR IGNORE INTO relationship_evidence(relationship_id,source_record_id,confidence) VALUES (?,?,1)",(rel,sr));stats['relations'].add(rel)
  db.commit()
 except:db.rollback();raise
 out={'release_id':rid,'sentence_objects_imported':len(stats['sentences']),'english_translation_facts_imported':len(stats['translations']),'illustrates_relationships_imported':len(stats['illustrates']),'synonym_or_antonym_relationships_imported':len(stats['relations'])};a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
