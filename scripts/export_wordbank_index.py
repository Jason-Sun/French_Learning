#!/usr/bin/env python3
"""Export the local SQLite graph as a browser-readable, network-free index."""
import argparse, json, sqlite3
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
db = sqlite3.connect(args.source); db.row_factory = sqlite3.Row
definitions = {}
for row in db.execute('SELECT * FROM object_definitions ORDER BY position'):
    definitions.setdefault(row['object_id'], []).append(dict(row))
features = {row['object_id']: dict(row) for row in db.execute('SELECT * FROM form_features')}
relationships = {}
for row in db.execute('SELECT source_object_id, target_object_id, relationship_type_code FROM relationships'):
    relationships.setdefault(row['source_object_id'], []).append({'type': row['relationship_type_code'], 'target': row['target_object_id']})
objects = []
for row in db.execute("SELECT * FROM language_objects WHERE type_code IN ('word','inflected_form','expression','idiom','collocation','grammar_construction')"):
    item = dict(row); item['definitions'] = definitions.get(row['id'], []); item['features'] = features.get(row['id']); item['relationships'] = relationships.get(row['id'], [])
    objects.append(item)
payload = {'version': 1, 'objects': objects}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f'Exported {len(objects)} language objects to {args.output}')
