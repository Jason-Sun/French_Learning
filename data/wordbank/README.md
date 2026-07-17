# Liens local language knowledge graph

`liens-knowledge.sqlite` is the app's local, versioned learning-data store. It is designed to be bundled with a future server or queried in-browser through SQLite WASM; the product must not call AI merely to resolve a core word.

`liens-wordbank.sqlite` remains the v1 import source. `liens-knowledge.sqlite` is the durable v2 schema the app should use.

## Contents

- `language_objects`: the single identity layer for words, forms, expressions, idioms, constructions, paradigms, sentences, media-ready pronunciation objects, and future learning resources.
- `canonical_objects`: permanent source-independent UUID identities. Legacy `language_objects.id` remains a browser compatibility key during migration.
- `canonical_facts`, typed fact-value tables, and `fact_evidence`: predicate-based linguistic claims with independently evidenced values.
- `relationships`: directed, typed graph edges. Navigation is a graph traversal, not a page hierarchy.
- `object_definitions`, `object_attributes`, and `form_features`: structured object content without creating a new core table for each future type.
- `pronunciations`: the retained import-compatible record table.
- `pronunciation_object_details`: structured linguistic metadata owned by first-class `pronunciation` Language Objects.
- `learning_metadata`, `review_metadata`, and `media`: learning and delivery information kept distinct from linguistic facts.
- `sources` and `ai_generated_content`: provenance and a hard boundary between curated facts and generated enrichment.
- `sentence_analysis_instances`, `sentence_analysis_nodes`, and `sentence_analysis_edges`: reproducible, non-canonical graphs produced for a specific sentence input.
- `sentence_analysis_object_matches`: non-canonical parser matches from input spans to canonical UUIDs, including contractions and multi-word objects.
- `sentence_learning_items`: review and learning opportunities extracted from an analysis without re-parsing the sentence later.
- `learning_resource_revisions` and `learning_resource_revision_texts`: immutable, ordered revisions for teacher, human, imported, or AI-authored learning content.

### Core object types

`word`, `inflected_form`, `expression`, `idiom`, `collocation`, `grammar_construction`, `sentence_pattern`, `conjugation_paradigm`, `pronunciation`, `cefr_concept`, `spelling_exception`, `sentence`, and `learning_resource` are seeded in `object_types`. Adding a type is data migration, not a redesign.

### Core relationship types

`inflected_form_of`, `belongs_to_conjugation`, `member_of_paradigm`, `contains`, `commonly_used_with`, `governs_preposition`, `expresses`, `illustrates`, `has_pronunciation`, and `related_to` are seeded in `relationship_types`.

### Pronunciation contract

Pronunciation belongs to the graph, never to a UI component. A learnable object links to one or more `pronunciation` Language Objects through `has_pronunciation`. Its `pronunciation_object_details` stores IPA, syllables, stress, liaison, silent letters, elision, regional variant, source, confidence, review status, optional audio URI, and optional local audio path. The browser embeds these graph nodes behind the compatible `object.pronunciations` adapter field, so every surface can reuse the same data without duplicating it.

Pronunciation is never inherited across relationships: an `inflected_form` may link to its lemma with `inflected_form_of`, but it must have its own Pronunciation Object before IPA or playback is shown. The legacy `language_objects.ipa` column and `pronunciations` table remain readable/importable; `scripts/add_graph_native_pronunciation_schema.py` synchronizes them into graph nodes.

For example, `sommes` is an `inflected_form` object with an `inflected_form_of` edge to `être`, plus grammatical features. Every verb is connected to its own `conjugation_paradigm` object.

The included build uses the FLELex / Beacco CEFR classification, retaining entries classified A1, A2, B1, or B2. It produces 8,767 local entries. FLELex is licensed **CC BY-NC-SA 4.0**; this repository must keep attribution and cannot use that imported data commercially without replacing or separately licensing the source.

## Build and migrate

Download `FLELex_TreeTagger_Beacco.txt` from the [FLELex download page](https://cental.uclouvain.be/cefrlex/flelex/download/), then run:

```bash
python3 scripts/build_wordbank.py \
  --source /path/to/FLELex_TreeTagger_Beacco.txt \
  --output data/wordbank/liens-wordbank.sqlite
```

Then migrate the v1 import into the graph:

```bash
python3 scripts/migrate_to_knowledge_graph.py \
  --source data/wordbank/liens-wordbank.sqlite \
  --output data/wordbank/liens-knowledge.sqlite
```

Add the Sentence Intelligence Layer persistence schema after migration:

```bash
python3 scripts/add_sentence_intelligence_schema.py \
  --database data/wordbank/liens-knowledge.sqlite
```

Migration preserves every v1 word, definition, form, grammar pattern, and source record. Legacy deterministic IDs such as `fr:word:être:ver` remain browser-compatible keys; source-independent canonical UUIDs are the permanent external identity for imports, learner state, APIs, and links.

Sentence analyses deliberately do **not** become global Language Objects automatically. They reference stable canonical objects, retain `engine_version`, `provenance`, `confidence`, and `cache_status`, and can be replayed or discarded independently. Only reviewed source/import work may promote reusable knowledge into the global graph.

## Enrichment rule

The database intentionally separates lexical coverage from authored explanations. Every core entry is resolvable locally with CEFR level, part of speech, and frequency. The initial curated starter set has bilingual definitions and teacher-style notes. Future enrichment may add senses, examples, collocations, and explanations, but must set `source_kind = 'ai_enriched'` until reviewed.

English is always displayed. Chinese is stored where available and controlled solely by the learner's `chineseExplanations` preference.

### A1 Foundation import

`a1-foundation-draft.json` is a reviewable, AI-assisted enrichment batch—not a lexical authority. Import it with:

```bash
python3 scripts/import_a1_foundation.py \
  --database data/wordbank/liens-knowledge.sqlite \
  --input data/wordbank/a1-foundation-draft.json
```

The importer creates `ai_enriched` definitions, pronunciation records, first-class sentence objects, and `illustrates` graph edges. The browser exposes this provenance as **AI draft**, so no generated learning content is presented as curated data.

### Graph-native pronunciation and core forms

After any importer that creates legacy pronunciation records, synchronize their graph representation:

```bash
python3 scripts/add_graph_native_pronunciation_schema.py \
  --database data/wordbank/liens-knowledge.sqlite
```

The initial core conjugations have independent, reviewed IPA for each of their 56 inflected-form objects. They are declarative data, not a lemma fallback:

```bash
python3 scripts/import_core_form_pronunciations.py \
  --database data/wordbank/liens-knowledge.sqlite \
  --input data/wordbank/core-form-pronunciations.json
python3 scripts/add_graph_native_pronunciation_schema.py \
  --database data/wordbank/liens-knowledge.sqlite
```

Playback is intentionally outside the database. The static browser chooses a provider in this local-first order: local recording, local cached TTS, browser SpeechSynthesis. A future provider may be registered without changing any page or graph schema. Remote providers are not part of the current stack.

### Core conjugation import

`core-conjugation-paradigms.json` is declarative graph data, not browser lookup code. Import it with:

```bash
python3 scripts/import_conjugation_paradigms.py \
  --database data/wordbank/liens-knowledge.sqlite \
  --input data/wordbank/core-conjugation-paradigms.json \
  --catalog data/wordbank/conjugation-paradigm-catalog.json
```

Each record becomes an `inflected_form` Language Object with `form_features`, an `inflected_form_of` edge to its canonical lemma, and a `member_of_paradigm` edge. Search opens the form's own page; its `inflected_form_of` edge provides the explicit, clickable route back to the canonical lemma.

### Tense paradigms and verb metadata

Each verb has a root `conjugation_paradigm` object. Each catalogued mood-tense combination is a separate `conjugation_paradigm` child with a stable ID and `conjugation_features` object attribute. When forms exist, they add `member_of_paradigm` edges to that child. This lets the browser present a textbook-style tense selector without hard-coding verb forms, while making unfilled paradigms explicit rather than fabricating content.

Learning sequence is graph data too: `learning_group` objects contain reusable `conjugation_tense` objects through `contains`; a verb-specific paradigm points to its reusable tense through `realizes_tense`. `conjugation_tense_metadata` stores CEFR recommendation, group, mood, tense, ordering, formation type, structured explanation/usage-note references, example reference, source, confidence, and review status. Verb-level conjugation explanations are `learning_resource` objects linked with `explains_conjugation`, rather than hard-coded UI copy.

Seed the learning taxonomy before importing verb-specific paradigms:

```bash
python3 scripts/add_conjugation_learning_schema.py --database data/wordbank/liens-knowledge.sqlite
python3 scripts/seed_conjugation_learning_catalog.py \
  --database data/wordbank/liens-knowledge.sqlite \
  --catalog data/wordbank/conjugation-paradigm-catalog.json
```

### Verb realizations and teaching resources

`conjugation_realization` is a first-class Language Object for a person-specific construction. `conjugation_realizations` identifies its paradigm, person, number, and realization type; `conjugation_realization_components` stores ordered component Language Objects and roles. Thus `j'ai eu` is composed from the `ai` auxiliary form and the `eu` past participle, while `je vais avoir` is composed from the `vais` carrier verb form and the `avoir` infinitive.

Structured teacher guidance is a `learning_resource` object linked to the shared tense or grammar object through `explains`. `teaching_guidance` stores why it is used, how it is formed, common mistakes, related objects, provenance, confidence, and review status. Future AI may create only draft resources and draft realizations using these same tables.

`verb_metadata` is lemma-owned data: verb group, irregularity, future stem, auxiliary lemma, explanations, provenance, confidence, and status. It is intentionally separate from `form_features`, which belong only to an inflected form.

## Local lookup contract

The app resolves a typed token locally in this order:

```sql
-- 1. Exact lemma or multiword learning object
SELECT o.*, d.english_gloss, d.chinese_gloss, d.explanation_en
FROM language_objects AS o
LEFT JOIN object_definitions AS d ON d.object_id = o.id
WHERE o.normalized_form = :normalized_input
  AND o.type_code IN ('word', 'expression', 'idiom', 'collocation');

-- 2. Inflected form, such as `sommes` → `être`
SELECT form.*, lemma.*, features.*
FROM language_objects AS form
JOIN form_features AS features ON features.object_id = form.id
JOIN relationships AS r ON r.source_object_id = form.id
  AND r.relationship_type_code = 'inflected_form_of'
JOIN language_objects AS lemma ON lemma.id = r.target_object_id
WHERE form.normalized_form = :normalized_input;
```

The v2 database also provides read-only compatibility views named `lexemes`, `senses`, `forms`, `collocations`, and `grammar_patterns`; existing v1 lookup SQL remains semantically valid while the app adopts graph traversal.

For the present static prototype, add a SQLite-WASM adapter when the wordbank is connected to the browser UI. A future server can use the same file directly. Neither path changes the database schema or requires AI to resolve a core entry.
