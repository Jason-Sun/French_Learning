# Liens local language knowledge graph

`liens-knowledge.sqlite` is the app's local, versioned learning-data store. It is designed to be bundled with a future server or queried in-browser through SQLite WASM; the product must not call AI merely to resolve a core word.

`liens-wordbank.sqlite` remains the v1 import source. `liens-knowledge.sqlite` is the durable v2 schema the app should use.

## Contents

- `language_objects`: the single identity layer for words, forms, expressions, idioms, constructions, paradigms, sentences, media-ready pronunciation objects, and future learning resources.
- `relationships`: directed, typed graph edges. Navigation is a graph traversal, not a page hierarchy.
- `object_definitions`, `object_attributes`, and `form_features`: structured object content without creating a new core table for each future type.
- `pronunciations`: durable, object-linked pronunciation records. Each record may contain IPA, syllables, stress data, an external audio reference, a local cached-audio path, provenance, confidence, and status. Audio is metadata only in this milestone; no playback is implied.
- `learning_metadata`, `review_metadata`, and `media`: learning and delivery information kept distinct from linguistic facts.
- `sources` and `ai_generated_content`: provenance and a hard boundary between curated facts and generated enrichment.
- `sentence_analysis_instances`, `sentence_analysis_nodes`, and `sentence_analysis_edges`: reproducible, non-canonical graphs produced for a specific sentence input.
- `sentence_learning_items`: review and learning opportunities extracted from an analysis without re-parsing the sentence later.

### Core object types

`word`, `inflected_form`, `expression`, `idiom`, `collocation`, `grammar_construction`, `sentence_pattern`, `conjugation_paradigm`, `pronunciation`, `cefr_concept`, `spelling_exception`, `sentence`, and `learning_resource` are seeded in `object_types`. Adding a type is data migration, not a redesign.

### Core relationship types

`inflected_form_of`, `belongs_to_conjugation`, `member_of_paradigm`, `contains`, `commonly_used_with`, `governs_preposition`, `expresses`, `illustrates`, `has_pronunciation`, and `related_to` are seeded in `relationship_types`.

### Pronunciation contract

Pronunciation belongs to a Language Object, never to a UI component. `pronunciations.object_id` supports one or more regional or source variants per object. `ipa` is the current display-ready field; `syllables_json` and `stress_json` preserve structured learning data; `audio_source_uri` and `local_audio_path` reserve future media delivery without coupling the graph to playback. `provenance`, `confidence`, `source_id`, and `status` follow the same curated-versus-enriched policy as the rest of the graph. Pronunciation is never inherited across relationships: an `inflected_form` may link to its lemma with `inflected_form_of`, but it must have its own pronunciation record before IPA or playback is shown.

The legacy `language_objects.ipa` column remains readable for compatibility. New pronunciation writes belong in `pronunciations`.

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

Migration preserves every v1 word, definition, form, grammar pattern, and source record. It assigns deterministic stable IDs such as `fr:word:être:ver` and `fr:form:...`, so a rebuilt database does not create a new identity for the same object.

Sentence analyses deliberately do **not** become global Language Objects automatically. They reference stable objects, retain `engine_version`, `provenance`, `confidence`, and `cache_status`, and can be replayed or discarded independently. Only reviewed reusable knowledge is promoted into the global graph.

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

### Core conjugation import

`core-conjugation-paradigms.json` is declarative graph data, not browser lookup code. Import it with:

```bash
python3 scripts/import_conjugation_paradigms.py \
  --database data/wordbank/liens-knowledge.sqlite \
  --input data/wordbank/core-conjugation-paradigms.json
```

Each record becomes an `inflected_form` Language Object with `form_features`, an `inflected_form_of` edge to its canonical lemma, and a `member_of_paradigm` edge. Search opens the form's own page; its `inflected_form_of` edge provides the explicit, clickable route back to the canonical lemma.

### Tense paradigms and verb metadata

Each verb has a root `conjugation_paradigm` object. Each available mood-tense combination is a separate `conjugation_paradigm` child with a stable ID, `conjugation_features` object attribute, and `member_of_paradigm` edges from its forms. This lets the browser present a textbook-style tense selector without hard-coding verb forms.

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
