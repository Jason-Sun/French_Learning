# 4. Imports and Releases

## Purpose and invariants

Liens grows by importing attributable data into a source-independent canonical graph. The pipeline must scale from A1 to C2 and beyond without changing identity rules or letting source-specific assumptions leak into the application.

The required pipeline is:

```text
pinned artifact → checksum verification → manifest selection
→ importer mapping or explicit exclusion → facts/relationships/representations + evidence
→ audit → browser export → package test → immutable release manifest
```

Every eligible source record is either mapped or explicitly excluded. A successful import is not “it added many rows”; it is reproducible input, zero unexpected duplicate identities, valid evidence, referential integrity, and a coverage report that explains gaps.

## Source strategy

| Source | Canonical contribution | Must not be used for |
| --- | --- | --- |
| FLELex / Beacco TreeTagger | Lexical baseline: CEFR, POS, frequency, word identity creation | Senses, inferred forms, or unverified definitions. |
| Lexique 3.83 | Source-backed forms, morphology, phonological code, syllabification | Treating Lexique code as verified IPA. |
| Morphalou 3.1 | Full simple verb-form morphology for existing CEFR-scoped verbs | Creating new CEFR lexical identities. |
| Kaikki / English Wiktionary | English senses/glosses, phrase material, examples, lexical relations, IPA, variants, audio URL metadata | CEFR classification or unsourced semantic invention. |
| French Wiktionary-derived pinned source | Complementary French definitions/examples/relations where accepted | Replacing a source-backed English sense with generated content. |
| Tex / curated grammar | Bounded canonical grammar topology and teaching structure | Unbounded AI grammar prose as canonical rules. |
| Manual curation | Reviewed gaps/corrections with versioned source release | Anonymous database edits. |
| AI | Learning drafts only | Canonical facts, objects, relationships, CEFR, or source evidence. |

Licenses, attribution, release hashes, and source scope belong in manifests and the resulting release manifest. Do not download a mutable upstream resource during a production build.

## Repository inputs and outputs

```text
data/wordbank/
  import-manifests/     # source URLs, SHA-256, selected CEFR scope, mappings
  import-reports/       # small development/audit reports when appropriate
  *.json                # curated catalogs and deterministic derivation policies
scripts/
  import_*.py           # source-specific adapters
  add_*.py              # additive schema migrations
  derive_*.py           # deterministic, versioned derivations
  project_*.py          # browser/pedagogical projections
  audit_*.py            # integrity and coverage gates
  export_wordbank_index.py
releases/<release>/     # generated external artifact: SQLite, browser/, reports/, manifest
```

The Git repository contains recipes, schemas, manifests, curated policy data, tests, and documentation. It should not contain the complete generated SQLite release or large browser package as normal tracked source.

## Manifests

Each import manifest must at minimum identify:

- catalog and release ID;
- source URL or documented local acquisition route;
- SHA-256 of the exact artifact;
- licence/attribution context where applicable;
- importer/adapter version;
- selected CEFR levels or explicit selection rules;
- reviewed POS reconciliation or mapping rules, if any;
- expected exclusion behavior.

An importer must verify the source hash before changing the graph. Never “update the hash” merely because an upstream download changed; create a reviewed release/mapping decision instead.

## Baseline import ordering

For a new CEFR scope, use the following order unless a documented source dependency requires another one:

1. Add or migrate schema only through an additive migration.
2. Import FLELex lexical baseline. This is the normal path that creates `word` identities.
3. Audit the lexical baseline.
4. Import senses and definitions against existing identities.
5. Import morphology and project source-attested forms into paradigms.
6. Import pronunciation representations and run pronunciation migration/projection/audit.
7. Import expressions, examples, lexical relations, grammar, and other connected objects.
8. Run graph audit.
9. Export and test browser package.
10. Emit an immutable release manifest with hashes.

No enrichment importer creates an ad hoc fallback word simply because its source mentions an unmatched surface.

## Exact operational commands

### Serve the application locally

The browser graph package is fetched with HTTP. Do not rely on `file://` for a full test.

```bash
cd /Users/jason/Documents/Hackathon_French_Learning
python3 dev_server.py --port 4182
open http://127.0.0.1:4182/?graphRoot=releases/liens-c1-c2/browser
```

### Build a new A1–C2 release

`build_c1_c2_release.py` is the canonical coordinated build. It requires verified local copies of the pinned source artifacts and writes to a new, empty output directory.

```bash
cd /Users/jason/Documents/Hackathon_French_Learning

python3 scripts/build_c1_c2_release.py \
  --base-database /absolute/path/to/verified-a1-b2/liens-knowledge.sqlite \
  --output-dir /absolute/path/to/new-release \
  --flelex-source /absolute/path/to/flelex.tsv \
  --kaikki-source /absolute/path/to/kaikki.org-dictionary-French.jsonl \
  --lexique-source /absolute/path/to/Lexique383.tsv \
  --morphalou-source /absolute/path/to/Morphalou3.1.zip \
  --build-id liens-a1-c2-source-release-v2
```

The command copies the base database, applies the C1/C2 lexical baseline and all selected enrichments, runs audits, exports browser data, tests the package, and writes:

```text
new-release/
  liens-knowledge.sqlite
  browser/
    manifest.json
    lookup.json
    objects/
  reports/
  release-manifest.json
```

Never point `--output-dir` at an existing release. The script rejects it to prevent accidental overwrite.

### Re-export browser package after a projection or UI-data change

```bash
python3 scripts/export_wordbank_index.py \
  --source /absolute/path/to/release/liens-knowledge.sqlite \
  --output-dir /absolute/path/to/release/browser

python3 scripts/test_browser_graph_package.py \
  --package-dir /absolute/path/to/release/browser
```

Run this after changing exporter logic, browser projection tables, or generated graph content. UI-only CSS changes do not require it.

### Import a new vocabulary level

1. Create a new FLELex manifest in `data/wordbank/import-manifests/` with pinned hash and CEFR scope.
2. Run the baseline importer and lexical audit:

```bash
python3 scripts/import_flelex_lexical_baseline.py \
  --database /absolute/path/to/release/liens-knowledge.sqlite \
  --source /absolute/path/to/flelex.tsv \
  --manifest data/wordbank/import-manifests/<new-level>.json \
  --report /absolute/path/to/release/reports/flelex-baseline.json

python3 scripts/audit_cefr_lexical_baseline.py \
  --database /absolute/path/to/release/liens-knowledge.sqlite \
  --source /absolute/path/to/flelex.tsv \
  --manifest data/wordbank/import-manifests/<new-level>.json \
  --report /absolute/path/to/release/reports/flelex-baseline-audit.json
```

3. Add source-backed senses, morphology, pronunciation, connections, and expressions with matching manifests.
4. Run the scope and full graph audits before export.

Do not define success as a guessed target count. Validate 100% eligible source-record accounting and graph integrity against the exact pinned release.

### Import morphology

Lexique is used for CEFR-scoped forms and broad morphology; Morphalou fills complete simple verb paradigms for existing CEFR verbs.

```bash
python3 scripts/import_lexique_a1_morphology.py \
  --database /absolute/path/to/release/liens-knowledge.sqlite \
  --source /absolute/path/to/Lexique383.tsv \
  --manifest data/wordbank/import-manifests/lexique383-<scope>-morphology.json \
  --report /absolute/path/to/release/reports/lexique-morphology.json

python3 scripts/import_morphalou_morphology.py \
  --database /absolute/path/to/release/liens-knowledge.sqlite \
  --source /absolute/path/to/Morphalou3.1.zip \
  --manifest data/wordbank/import-manifests/morphalou31-a1-c2-morphology.json \
  --report /absolute/path/to/release/reports/morphalou-morphology.json

python3 scripts/project_lexique_forms_to_tense_paradigms.py \
  --database /absolute/path/to/release/liens-knowledge.sqlite \
  --report /absolute/path/to/release/reports/tense-paradigm-projection.json
```

### Import pronunciation

Pronunciation is representation-based. Keep sources parallel; never overwrite Lexique code with IPA.

```bash
python3 scripts/import_lexique_a1_pronunciation.py \
  --database /absolute/path/to/release/liens-knowledge.sqlite \
  --source /absolute/path/to/Lexique383.tsv \
  --manifest data/wordbank/import-manifests/lexique383-<scope>-pronunciation.json \
  --report /absolute/path/to/release/reports/lexique-pronunciation.json

python3 scripts/migrate_pronunciation_objects.py \
  --database /absolute/path/to/release/liens-knowledge.sqlite \
  --report /absolute/path/to/release/reports/pronunciation-object-migration.json

python3 scripts/import_kaikki_pronunciations.py \
  --database /absolute/path/to/release/liens-knowledge.sqlite \
  --source /absolute/path/to/kaikki.org-dictionary-French.jsonl \
  --manifest data/wordbank/import-manifests/kaikki-enwiktionary-french-a1-c2-pronunciation.json \
  --report /absolute/path/to/release/reports/kaikki-pronunciation.json

python3 scripts/derive_lexique_ipa.py \
  --database /absolute/path/to/release/liens-knowledge.sqlite \
  --report /absolute/path/to/release/reports/lexique-derived-ipa.json

python3 scripts/project_pronunciation_browser_details.py \
  --database /absolute/path/to/release/liens-knowledge.sqlite \
  --report /absolute/path/to/release/reports/pronunciation-browser-projection.json

python3 scripts/audit_pronunciation_graph.py \
  --database /absolute/path/to/release/liens-knowledge.sqlite \
  --report /absolute/path/to/release/reports/pronunciation-graph-audit.json
```

### Import senses, examples, connections, and expressions

The Kaikki adapter names retain historical `a1` script names, but are scope-driven by manifest and may safely operate on other levels:

```bash
python3 scripts/import_kaikki_a1_senses.py --database /path/to/release/liens-knowledge.sqlite --source /path/to/kaikki.jsonl --manifest data/wordbank/import-manifests/kaikki-enwiktionary-french-c1-c2-senses.json --report /path/to/release/reports/kaikki-senses.json
python3 scripts/import_kaikki_a1_connections.py --database /path/to/release/liens-knowledge.sqlite --source /path/to/kaikki.jsonl --manifest data/wordbank/import-manifests/kaikki-enwiktionary-french-c1-c2-connections.json --report /path/to/release/reports/kaikki-connections.json
python3 scripts/import_kaikki_a1_expressions.py --database /path/to/release/liens-knowledge.sqlite --source /path/to/kaikki.jsonl --manifest data/wordbank/import-manifests/kaikki-enwiktionary-french-c1-c2-expressions.json --report /path/to/release/reports/kaikki-expressions.json
```

## Validation gates

| Gate | What it detects |
| --- | --- |
| Source SHA verification | Wrong or changed upstream artifact. |
| Baseline audit | Missing or duplicate lexical identity, unaccounted selected rows, missing facts/evidence. |
| Graph audit | Foreign-key failures, orphans, invalid relationships/evidence, coverage inconsistency. |
| Pronunciation audit | Orphan representations, unevidenced Kaikki values, canonical derived IPA, active source-specific nodes. |
| Browser package test | Bad manifest/shard references, missing objects, integrity mismatch. |
| Focused browser/UI tests | Broken search, object route, pronunciation label, navigation state, or visual regression. |

Before committing importer or schema work, run focused tests plus `git diff --check`. Before publishing a release, run every relevant audit and preserve reports with the release. See [source_imports.md](../architecture/source_imports.md) for source-specific contracts.
