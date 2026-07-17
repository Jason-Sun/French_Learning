#!/usr/bin/env python3
"""Export the local SQLite graph as a browser-readable, network-free index."""
import argparse, json, sqlite3, unicodedata
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()


def search_key(value: str) -> str:
    """French-insensitive browser lookup key; canonical text remains untouched."""
    decomposed = unicodedata.normalize('NFD', value.casefold().replace('’', "'"))
    return ''.join(char for char in decomposed if unicodedata.category(char) != 'Mn')


db = sqlite3.connect(args.source); db.row_factory = sqlite3.Row
canonical_ids = {row['language_object_id']: row['canonical_id'] for row in db.execute('SELECT language_object_id,canonical_id FROM canonical_objects')} if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='canonical_objects'").fetchone() else {}
canonical_facts = {}
if canonical_ids:
    for row in db.execute("SELECT f.canonical_subject_id,f.predicate_code,f.lifecycle,cv.value_code,nv.value_number,nv.unit_code,tv.language_code,tv.value_text,ov.value_canonical_id FROM canonical_facts f LEFT JOIN fact_code_values cv ON cv.fact_id=f.id LEFT JOIN fact_number_values nv ON nv.fact_id=f.id LEFT JOIN fact_text_values tv ON tv.fact_id=f.id LEFT JOIN fact_object_values ov ON ov.fact_id=f.id"):
        canonical_facts.setdefault(row['canonical_subject_id'], []).append(dict(row))
definitions = {}
for row in db.execute('SELECT * FROM object_definitions ORDER BY position'):
    definitions.setdefault(row['object_id'], []).append(dict(row))
features = {row['object_id']: dict(row) for row in db.execute('SELECT * FROM form_features')}
verb_metadata = {row['object_id']: dict(row) for row in db.execute('SELECT * FROM verb_metadata')}
tense_metadata = {row['object_id']: dict(row) for row in db.execute('SELECT * FROM conjugation_tense_metadata')}
realizations = {row['object_id']: dict(row) for row in db.execute('SELECT * FROM conjugation_realizations')}
realization_components = {}
for row in db.execute('SELECT * FROM conjugation_realization_components ORDER BY realization_id, position'):
    realization_components.setdefault(row['realization_id'], []).append(dict(row))
teaching_guidance = {row['resource_object_id']: dict(row) for row in db.execute('SELECT * FROM teaching_guidance')}
attributes = {}
for row in db.execute('SELECT object_id,key,value_json FROM object_attributes'):
    attributes.setdefault(row['object_id'], {})[row['key']] = json.loads(row['value_json'])
pronunciations = {}
try:
    pronunciation_rows = db.execute(
        "SELECT edge.source_object_id AS owner_id, detail.*, pronunciation.display_form AS pronunciation_display_form, "
        "source.name AS source_name FROM relationships AS edge "
        "JOIN pronunciation_object_details AS detail ON detail.object_id=edge.target_object_id "
        "JOIN language_objects AS pronunciation ON pronunciation.id=detail.object_id "
        "LEFT JOIN sources AS source ON source.id=detail.source_id "
        "WHERE edge.relationship_type_code='has_pronunciation' "
        "AND detail.review_status <> 'deprecated' "
        "ORDER BY edge.source_object_id, detail.confidence DESC, detail.object_id"
    )
    for row in pronunciation_rows:
        record = dict(row)
        pronunciations.setdefault(record.pop('owner_id'), []).append(record)
except sqlite3.OperationalError:
    # An older, exported database remains usable while it awaits the additive
    # graph-native pronunciation migration.
    for row in db.execute("SELECT * FROM pronunciations WHERE status <> 'deprecated' ORDER BY object_id, confidence DESC, id"):
        pronunciations.setdefault(row['object_id'], []).append(dict(row))
relationships = {}
examples = {}
for row in db.execute('SELECT source_object_id, target_object_id, relationship_type_code FROM relationships'):
    relationships.setdefault(row['source_object_id'], []).append({'type': row['relationship_type_code'], 'target': row['target_object_id']})
    if row['relationship_type_code'] == 'illustrates':
        examples.setdefault(row['target_object_id'], []).append(row['source_object_id'])
base_rows = list(db.execute("SELECT * FROM language_objects WHERE type_code IN ('word','inflected_form','conjugation_realization','expression','idiom','collocation','grammar_construction','sentence','learning_group','conjugation_tense','learning_resource','pronunciation')"))
paradigm_ids = {
    relation['target_object_id'] for relation in db.execute(
        "SELECT target_object_id FROM relationships WHERE relationship_type_code='member_of_paradigm'"
    )
}
paradigm_ids.update(
    row['id'] for row in db.execute(
        "SELECT DISTINCT child.id FROM language_objects AS child "
        "JOIN relationships AS child_link ON child_link.target_object_id=child.id "
        "AND child_link.relationship_type_code='contains' "
        "JOIN relationships AS verb_link ON verb_link.target_object_id=child_link.source_object_id "
        "AND verb_link.relationship_type_code='belongs_to_conjugation' "
        "WHERE child.type_code='conjugation_paradigm'"
    )
)
root_ids = {
    relation['source_object_id'] for relation in db.execute(
        "SELECT source_object_id FROM relationships WHERE relationship_type_code='contains' "
        "AND target_object_id IN ({})".format(','.join('?' for _ in paradigm_ids)),
        tuple(sorted(paradigm_ids)),
    )
} if paradigm_ids else set()
paradigm_ids.update(root_ids)
extra_rows = []
if paradigm_ids:
    placeholders = ','.join('?' for _ in paradigm_ids)
    extra_rows = list(db.execute(
        f"SELECT * FROM language_objects WHERE type_code='conjugation_paradigm' AND id IN ({placeholders})",
        tuple(sorted(paradigm_ids)),
    ))
objects = []
for row in [*base_rows, *extra_rows]:
    item = dict(row); item['canonical_id'] = canonical_ids.get(row['id']); item['facts'] = canonical_facts.get(item['canonical_id'], []); item['search_key'] = search_key(row['normalized_form']); item['definitions'] = definitions.get(row['id'], []); item['features'] = features.get(row['id']); item['verb_metadata'] = verb_metadata.get(row['id']); item['tense_metadata'] = tense_metadata.get(row['id']); item['realization'] = realizations.get(row['id']); item['realization_components'] = realization_components.get(row['id'], []); item['teaching_guidance'] = teaching_guidance.get(row['id']); item['attributes'] = attributes.get(row['id'], {}); item['pronunciations'] = pronunciations.get(row['id'], []); item['relationships'] = relationships.get(row['id'], []); item['examples'] = examples.get(row['id'], [])
    objects.append(item)
payload = {'version': 3, 'objects': objects}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f'Exported {len(objects)} language objects to {args.output}')
