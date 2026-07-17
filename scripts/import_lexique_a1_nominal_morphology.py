#!/usr/bin/env python3
"""Import Lexique 3.83 A1 noun/adjective inflections with source evidence."""
from __future__ import annotations
import argparse,csv,hashlib,json,sqlite3,uuid
from pathlib import Path
from canonical_identity import NAMESPACE,canonical_uuid
def n(s): return ' '.join(s.casefold().replace('’',"'").split())
def sid(k,v): return str(uuid.uuid5(NAMESPACE,f'liens:{k}:{v}'))
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--database',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();m=json.loads(a.manifest.read_text())
 if digest(a.source)!=m['release']['sha256']:raise ValueError('Lexique source SHA-256 mismatch')
 db=sqlite3.connect(a.database);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON');release=m['release']['id'];run=f'import:{release}:a1-nominal-morphology'
 db.execute("INSERT OR IGNORE INTO import_runs(id,release_id,importer_name,importer_version,status,completed_at) VALUES (?,?,?,?, 'completed',CURRENT_TIMESTAMP)",(run,release,'lexique383_a1_nominal_morphology','1'))
 for code in ('inflected_form_of','grammatical_number','grammatical_gender'):db.execute("INSERT OR IGNORE INTO fact_predicates(code,value_kind,label,description) VALUES (?,?,'Imported morphology','Imported Lexique morphology fact.')",(code,'object' if code=='inflected_form_of' else 'code'))
 lemmas={(n(r['canonical_form']),r['part_of_speech']):(r['id'],r['canonical_id']) for r in db.execute("SELECT lo.id,lo.canonical_form,lo.part_of_speech,co.canonical_id FROM language_objects lo JOIN canonical_objects co ON co.language_object_id=lo.id WHERE lo.type_code='word' AND lo.cefr_level='A1' AND lo.part_of_speech IN ('NOM','ADJ')")}
 forms=relation_evidence=0;db.commit();db.execute('BEGIN')
 try:
  for line,row in enumerate(csv.DictReader(a.source.open(encoding='utf8'),delimiter='\t'),start=2):
   pos={'NOM':'NOM','ADJ':'ADJ'}.get(row['cgram']);key=(n(row['lemme']),pos)
   if not pos or key not in lemmas or n(row['ortho'])==n(row['lemme']):continue
   gender={'m':'masculine','f':'feminine'}.get(row['genre']);number={'s':'singular','p':'plural'}.get(row['nombre'])
   if not gender and not number:continue
   lemma,owner=lemmas[key];surface=row['ortho'];fid=f"fr:form:{lemma}:{n(surface)}:-:-:-:{number or '-'}:{gender or '-'}";fkey=f"fr|inflected_form||{n(surface)}|owner={owner}|features=||||{number or ''}|{gender or ''}"
   old=db.execute('SELECT canonical_id,language_object_id FROM canonical_objects WHERE identity_key=?',(fkey,)).fetchone()
   if old:cid,fid=old['canonical_id'],old['language_object_id']
   else:
    cid=canonical_uuid(fkey);db.execute("INSERT INTO language_objects(id,type_code,canonical_form,display_form,normalized_form,source_id,content_status,provenance) VALUES (?,?,?,?,?,'lexique383','metadata_ready','curated')",(fid,'inflected_form',surface,surface,n(surface)));db.execute('INSERT INTO form_features(object_id,number,gender) VALUES (?,?,?)',(fid,number,gender));db.execute("INSERT INTO relationships(id,source_object_id,target_object_id,relationship_type_code,source_kind,confidence) VALUES (?,?,?,?, 'curated',1)",(sid('relationship',f'{fid}|inflected_form_of|{lemma}'),fid,lemma,'inflected_form_of'));db.execute('INSERT INTO canonical_objects(canonical_id,language_object_id,object_type_code,identity_key) VALUES (?,?,?,?)',(cid,fid,'inflected_form',fkey))
   rec=sid('source-record',f'{release}|line:{line}|lexique_row');db.execute("INSERT OR IGNORE INTO source_records(id,release_id,external_key,record_kind,content_hash) VALUES (?,?,?,?,?)",(rec,release,f'line:{line}','morphology_row',hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()));db.execute("INSERT OR IGNORE INTO import_record_mappings(import_run_id,source_record_id,canonical_id,mapping_kind,confidence) VALUES (?,?,?,'lexique_morphology_match',1)",(run,rec,cid))
   existing_relation=db.execute("SELECT id FROM relationships WHERE source_object_id=? AND target_object_id=? AND relationship_type_code='inflected_form_of'",(fid,lemma)).fetchone()
   if existing_relation:rel=existing_relation['id']
   else:
    rel=sid('relationship',f'{fid}|inflected_form_of|{lemma}');db.execute("INSERT INTO relationships(id,source_object_id,target_object_id,relationship_type_code,source_kind,confidence) VALUES (?,?,?,?, 'curated',1)",(rel,fid,lemma,'inflected_form_of'))
   db.execute("INSERT OR IGNORE INTO relationship_evidence(relationship_id,source_record_id,evidence_role,confidence) VALUES (?,?, 'asserts',1)",(rel,rec));relation_evidence+=db.execute('SELECT changes()').fetchone()[0]
   facts=[('inflected_form_of','object',owner)]+([('grammatical_number','code',number)]if number else[])+([('grammatical_gender','code',gender)]if gender else[])
   for pred,kind,val in facts:
    x=sid('fact',f'{cid}|{pred}|{val}');db.execute('INSERT OR IGNORE INTO canonical_facts(id,canonical_subject_id,predicate_code) VALUES (?,?,?)',(x,cid,pred));db.execute('INSERT OR IGNORE INTO '+('fact_object_values(fact_id,value_canonical_id)' if kind=='object' else 'fact_code_values(fact_id,value_code)')+' VALUES (?,?)',(x,val));db.execute("INSERT OR IGNORE INTO fact_evidence(fact_id,source_record_id,evidence_role,confidence) VALUES (?,?,'asserts',1)",(x,rec));forms+=1
  db.commit()
 except:db.rollback();raise
 out={'release_id':release,'form_analyses_imported':forms,'inflected_form_relationship_evidence_added':relation_evidence};a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
