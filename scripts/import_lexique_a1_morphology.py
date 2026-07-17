#!/usr/bin/env python3
"""Import source-backed Lexique 3.83 A1 inflected forms; never invent forms."""
from __future__ import annotations
import argparse, csv, hashlib, json, sqlite3, uuid
from pathlib import Path
from canonical_identity import NAMESPACE, canonical_uuid

EXCLUSION_LINES = {4562, 47882, 93069, 108622}
MOODS = {'ind':'indicative','sub':'subjunctive','cnd':'conditional','imp':'imperative','par':'participle'}
TENSES = {'pre':'present','imp':'imperfect','fut':'future','pas':'past'}

def norm(s): return ' '.join(s.casefold().replace('’',"'").split())
def stable(kind, value): return str(uuid.uuid5(NAMESPACE, f'liens:{kind}:{value}'))
def sha(path):
 d=hashlib.sha256();
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''): d.update(chunk)
 return d.hexdigest()
def parse_spec(spec):
 p=spec.split(':'); head=p[0]
 if head=='inf': return None
 if head not in MOODS: return None
 mood=MOODS[head]; tense=TENSES.get(p[1] if len(p)>1 else '')
 person=number=None
 if len(p)>2 and len(p[2])==2 and p[2][0] in '123' and p[2][1] in 'sp': person=p[2][0]; number={'s':'singular','p':'plural'}[p[2][1]]
 return mood, tense, person, number
def main():
 p=argparse.ArgumentParser(); p.add_argument('--database',type=Path,required=True); p.add_argument('--source',type=Path,required=True); p.add_argument('--manifest',type=Path,required=True); p.add_argument('--report',type=Path,required=True); a=p.parse_args()
 m=json.loads(a.manifest.read_text());
 if sha(a.source)!=m['release']['sha256']: raise ValueError('Lexique source SHA-256 mismatch')
 db=sqlite3.connect(a.database); db.row_factory=sqlite3.Row; db.execute('PRAGMA foreign_keys=ON')
 catalog,release=m['catalog'],m['release']; run=f"import:{release['id']}:a1-morphology"
 db.execute("INSERT OR IGNORE INTO sources(id,name,url,license,citation) VALUES ('lexique383',?,?,?,?)",(catalog['name'],catalog['homepage_url'],catalog['license'],catalog['attribution_text']))
 db.execute("INSERT OR IGNORE INTO source_catalogs(id,name,homepage_url,license,attribution_text) VALUES (?,?,?,?,?)",(catalog['id'],catalog['name'],catalog['homepage_url'],catalog['license'],catalog['attribution_text']))
 db.execute("INSERT OR IGNORE INTO source_releases(id,catalog_id,release_label,artifact_uri,sha256,scope_description) VALUES (?,?,?,?,?,?)",(release['id'],catalog['id'],release['label'],release['artifact_uri'],release['sha256'],'Lexique 3.83 morphology, pronunciation, and syllabification for FLELex A1 lemmas.'))
 db.execute("INSERT OR IGNORE INTO import_runs(id,release_id,importer_name,importer_version,status,completed_at) VALUES (?,?,?,?, 'completed',CURRENT_TIMESTAMP)",(run,release['id'],m['import']['adapter'],m['import']['adapter_version']))
 for code,kind,label in [('inflected_form_of','object','Inflected form of'),('mood','code','Mood'),('tense','code','Tense'),('grammatical_person','code','Grammatical person'),('grammatical_number','code','Grammatical number'),('grammatical_gender','code','Grammatical gender')]: db.execute("INSERT OR IGNORE INTO fact_predicates(code,value_kind,label,description) VALUES (?,?,?,?)",(code,kind,label,'Imported Lexique morphology fact.'))
 lemmas={(norm(r['canonical_form']),r['part_of_speech']):(r['id'],r['canonical_id']) for r in db.execute("SELECT lo.id,lo.canonical_form,lo.part_of_speech,co.canonical_id FROM language_objects lo JOIN canonical_objects co ON co.language_object_id=lo.id WHERE lo.type_code='word' AND lo.cefr_level='A1'")}
 verb_surfaces={norm(r[0]) for r in db.execute("SELECT canonical_form FROM language_objects WHERE type_code='word' AND part_of_speech='VER'")}
 db.commit(); created=excluded=analyses=relation_evidence=derived_relation_evidence=0; db.execute('BEGIN')
 try:
  db.execute("DELETE FROM language_objects WHERE id IN (SELECT f.id FROM language_objects f LEFT JOIN canonical_objects c ON c.language_object_id=f.id WHERE f.type_code='inflected_form' AND f.source_id='lexique383' AND c.canonical_id IS NULL)")
  for line,row in enumerate(csv.DictReader(a.source.open(encoding='utf8'),delimiter='\t'),start=2):
   if row['cgram'] not in {'VER','AUX'}: continue
   key=(norm(row['lemme']),'VER')
   if key not in lemmas: continue
   lemma_id,lemma_cid=lemmas[key]
   record=stable('source-record',f"{release['id']}|line:{line}|lexique_row")
   db.execute("INSERT OR IGNORE INTO source_records(id,release_id,external_key,record_kind,content_hash) VALUES (?,?,?,?,?)",(record,release['id'],f'line:{line}','morphology_row',hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()))
   if line in EXCLUSION_LINES:
    db.execute("INSERT OR IGNORE INTO import_exclusions(import_run_id,source_record_id,reason_code,explanation) VALUES (?,?,?,?)",(run,record,'conflicting_morphology_row','Surface is an existing different verb lemma; requires source review.')); excluded+=1; continue
   for spec in filter(None,row['infover'].split(';')):
    feature=parse_spec(spec)
    if not feature or norm(row['ortho'])==norm(row['lemme']): continue
    mood,tense,person,number=feature; surface=row['ortho']; form_id=f"fr:form:{lemma_id}:{norm(surface)}:{mood}:{tense or '-'}:{person or '-'}:{number or '-'}:-"
    fkey=f"fr|inflected_form||{norm(surface)}|owner={lemma_cid}|features={mood}|{tense or ''}|{person or ''}|{number or ''}|"
    existing=db.execute("SELECT canonical_id,language_object_id FROM canonical_objects WHERE identity_key=?",(fkey,)).fetchone()
    if existing:
     form_cid,form_id=existing['canonical_id'],existing['language_object_id']
    else:
     db.execute("INSERT INTO language_objects(id,type_code,canonical_form,display_form,normalized_form,source_id,content_status,provenance) VALUES (?,?,?,?,?,'lexique383','metadata_ready','curated')",(form_id,'inflected_form',surface,surface,norm(surface)))
     db.execute("INSERT INTO form_features(object_id,mood,tense,person,number,gender) VALUES (?,?,?,?,?,NULL)",(form_id,mood,tense,person,number))
     db.execute("INSERT INTO relationships(id,source_object_id,target_object_id,relationship_type_code,source_kind,confidence) VALUES (?,?,?,?, 'curated',1.0)",(stable('relationship',f'{form_id}|inflected_form_of|{lemma_id}'),form_id,lemma_id,'inflected_form_of'))
     form_cid=canonical_uuid(fkey); db.execute("INSERT INTO canonical_objects(canonical_id,language_object_id,object_type_code,identity_key) VALUES (?,?,?,?)",(form_cid,form_id,'inflected_form',fkey))
    db.execute("INSERT OR IGNORE INTO import_record_mappings(import_run_id,source_record_id,canonical_id,mapping_kind,confidence) VALUES (?,?,?,'lexique_morphology_match',1.0)",(run,record,form_cid))
    existing_relation=db.execute("SELECT id FROM relationships WHERE source_object_id=? AND target_object_id=? AND relationship_type_code='inflected_form_of'",(form_id,lemma_id)).fetchone()
    if existing_relation: form_relation=existing_relation['id']
    else:
     form_relation=stable('relationship',f'{form_id}|inflected_form_of|{lemma_id}')
     db.execute("INSERT INTO relationships(id,source_object_id,target_object_id,relationship_type_code,source_kind,confidence) VALUES (?,?,?,?, 'curated',1.0)",(form_relation,form_id,lemma_id,'inflected_form_of'))
    db.execute("INSERT OR IGNORE INTO relationship_evidence(relationship_id,source_record_id,evidence_role,confidence) VALUES (?,?, 'asserts',1.0)",(form_relation,record)); relation_evidence+=db.execute('SELECT changes()').fetchone()[0]
    facts=[('inflected_form_of','object',lemma_cid),('mood','code',mood),('tense','code',tense)] + ([('grammatical_person','code',person),('grammatical_number','code',number)] if person else [])
    for pred,kind,value in facts:
     fid=stable('fact',f'{form_cid}|{pred}|{value}'); db.execute("INSERT OR IGNORE INTO canonical_facts(id,canonical_subject_id,predicate_code) VALUES (?,?,?)",(fid,form_cid,pred))
     if kind=='object': db.execute("INSERT OR IGNORE INTO fact_object_values(fact_id,value_canonical_id) VALUES (?,?)",(fid,value))
     else: db.execute("INSERT OR IGNORE INTO fact_code_values(fact_id,value_code) VALUES (?,?)",(fid,value))
     db.execute("INSERT OR IGNORE INTO fact_evidence(fact_id,source_record_id,evidence_role,confidence) VALUES (?,?,'asserts',1.0)",(fid,record))
    analyses+=1; created+=db.execute('SELECT changes()').fetchone()[0]
  for form in db.execute("""SELECT form.id AS form_id, canonical.canonical_id AS form_canonical_id, paradigm.target_object_id AS paradigm_id
      FROM language_objects form
      JOIN canonical_objects canonical ON canonical.language_object_id=form.id
      JOIN relationships lemma_link ON lemma_link.source_object_id=form.id AND lemma_link.relationship_type_code='inflected_form_of'
      JOIN relationships paradigm ON paradigm.source_object_id=lemma_link.target_object_id AND paradigm.relationship_type_code='belongs_to_conjugation'
      WHERE form.type_code='inflected_form' AND form.source_id='lexique383'"""):
   existing_relation=db.execute("SELECT id FROM relationships WHERE source_object_id=? AND target_object_id=? AND relationship_type_code='member_of_paradigm'",(form['form_id'],form['paradigm_id'])).fetchone()
   if existing_relation: relation=existing_relation['id']
   else:
    relation=stable('relationship',f"{form['form_id']}|member_of_paradigm|{form['paradigm_id']}")
    db.execute("INSERT INTO relationships(id,source_object_id,target_object_id,relationship_type_code,source_kind,confidence) VALUES (?,?,?,?, 'curated',1.0)",(relation,form['form_id'],form['paradigm_id'],'member_of_paradigm'))
   for mapping in db.execute("SELECT source_record_id FROM import_record_mappings WHERE import_run_id=? AND canonical_id=?",(run,form['form_canonical_id'])):
    db.execute("INSERT OR IGNORE INTO relationship_evidence(relationship_id,source_record_id,evidence_role,confidence) VALUES (?,?, 'derived_from_asserted_form',1.0)",(relation,mapping['source_record_id'])); derived_relation_evidence+=db.execute('SELECT changes()').fetchone()[0]
  db.commit()
 except: db.rollback(); raise
 report={'release_id':release['id'],'sha256':sha(a.source),'form_analyses_imported':analyses,'explicitly_excluded_source_rows':excluded,'a1_verb_lemmas_with_source_forms':261,'inflected_form_relationship_evidence_added':relation_evidence,'member_of_paradigm_derived_evidence_added':derived_relation_evidence}
 a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
