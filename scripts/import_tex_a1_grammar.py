#!/usr/bin/env python3
"""Import reviewed A1 grammar objects and evidence-backed Tex grammar links."""
from __future__ import annotations
import argparse, hashlib, json, sqlite3, uuid
from pathlib import Path
from canonical_identity import NAMESPACE, canonical_uuid

def sid(kind, value): return str(uuid.uuid5(NAMESPACE, f"liens:{kind}:{value}"))
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()
def norm(value): return ' '.join(value.casefold().replace('’',"'").split())

def main():
    p=argparse.ArgumentParser();p.add_argument('--database',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--catalog',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    m=json.loads(a.manifest.read_text()); data=json.loads(a.catalog.read_text())
    if digest(a.source)!=m['release']['sha256']:raise ValueError('Tex grammar index SHA-256 mismatch')
    db=sqlite3.connect(a.database);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON');catalog=m['catalog'];release=m['release'];run=f"import:{release['id']}:a1-grammar"
    db.execute("INSERT OR IGNORE INTO sources(id,name,url,license,citation) VALUES ('tex-french-grammar',?,?,?,?)",(catalog['name'],catalog['homepage_url'],catalog['license'],catalog['attribution_text']))
    db.execute("INSERT OR IGNORE INTO source_catalogs(id,name,homepage_url,license,attribution_text) VALUES (?,?,?,?,?)",(catalog['id'],catalog['name'],catalog['homepage_url'],catalog['license'],catalog['attribution_text']))
    db.execute("INSERT OR IGNORE INTO source_releases(id,catalog_id,release_label,artifact_uri,sha256,scope_description) VALUES (?,?,?,?,?,?)",(release['id'],catalog['id'],release['label'],release['artifact_uri'],release['sha256'],release['scope']))
    db.execute("INSERT OR IGNORE INTO import_runs(id,release_id,importer_name,importer_version,status,completed_at) VALUES (?,?,?,?, 'completed',CURRENT_TIMESTAMP)",(run,release['id'],m['import']['adapter'],m['import']['adapter_version']))
    db.execute("INSERT OR IGNORE INTO grammar_categories(code,label,description) VALUES ('grammar_topic','Grammar topic','A source-backed grammar navigation topic.')")
    objects={}
    db.commit();db.execute('BEGIN')
    try:
      def record(key,title):
        rid=sid('source-record',f"{release['id']}|{key}");db.execute("INSERT OR IGNORE INTO source_records(id,release_id,external_key,record_kind,content_hash) VALUES (?,?,?,?,?)",(rid,release['id'],key,'grammar_index_entry',hashlib.sha256(title.encode()).hexdigest()));return rid
      def create(entry,topic=False):
        identity=f"fr|{entry.get('type','grammar_topic' if topic else 'grammar_construction')}|{norm(entry['label'])}";cid=canonical_uuid(identity);oid=f"fr:grammar:{entry['key']}";typ='grammar_topic' if topic else entry['type'];rid=record(entry['source_key'],entry['source_title'])
        db.execute("INSERT OR IGNORE INTO language_objects(id,type_code,canonical_form,display_form,normalized_form,cefr_level,source_id,content_status,provenance) VALUES (?,?,?,?,?,?, 'tex-french-grammar','metadata_ready','curated')",(oid,typ,entry['label'],entry['label'],norm(entry['label']),entry.get('cefr')))
        db.execute("INSERT OR IGNORE INTO canonical_objects(canonical_id,language_object_id,object_type_code,identity_key) VALUES (?,?,?,?)",(cid,oid,typ,identity));db.execute("INSERT OR IGNORE INTO grammar_metadata(canonical_object_id,category_code,pedagogical_order,analysis_priority,is_sentence_detectable,review_status) VALUES (?,?,?,?,?, 'reviewed')",(cid,entry['category'],len(objects)+1,100 if typ!='grammar_topic' else 999,0 if topic else 1));db.execute("INSERT OR IGNORE INTO import_record_mappings(import_run_id,source_record_id,canonical_id,mapping_kind,confidence) VALUES (?,?,?,'tex_grammar_object',1)",(run,rid,cid));objects[entry['key']]=(oid,cid,rid)
      for x in data['topics']:create(x,True)
      for x in data['objects']:create(x)
      def edge(source,target,typ,rid):
        eid=sid('relationship',f'{source}|{typ}|{target}');db.execute("INSERT OR IGNORE INTO relationships(id,source_object_id,target_object_id,relationship_type_code,source_kind,confidence) VALUES (?,?,?,?, 'curated',1)",(eid,source,target,typ));db.execute("INSERT OR IGNORE INTO relationship_evidence(relationship_id,source_record_id,confidence) VALUES (?,?,1)",(eid,rid))
      for x in data['objects']: edge(objects[x['key']][0],objects[x['topic']][0],'belongs_to_grammar_topic',objects[x['key']][2])
      for x in data['links']:
        source,rid=objects[x['source']][0],record(x['source_key'],x['source_key']);
        if not db.execute('SELECT 1 FROM language_objects WHERE id=?',(x['target_id'],)).fetchone():raise ValueError(f"missing graph target {x['target_id']}")
        edge(source,x['target_id'],x['type'],rid)
      db.commit()
    except:db.rollback();raise
    report={'release_id':release['id'],'topics_imported':len(data['topics']),'grammar_objects_imported':len(data['objects']),'relationships_imported':len(data['objects'])+len(data['links'])};a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
