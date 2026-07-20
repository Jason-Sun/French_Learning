# 6. Development and Feature Handbook

## Repository map

| Path | Responsibility |
| --- | --- |
| `index.html` | Static application shell and versioned asset loading order. |
| `styles.css` | Visual system, responsive layout, interaction states, and feature-specific presentation. |
| `app.js` | Current UI composition, routing, native-app exploration history, rendering, and feature interaction wiring. |
| `graph-data.js` | Browser package discovery, manifest/lookup loading, lazy shard hydration, integrity-aware graph adapter. |
| `sentence-intelligence.js` | Deterministic local sentence analysis. |
| `personal-learning-store.js` | Learner-owned saves, collections, memberships, review events in IndexedDB. |
| `ai-learning-store.js` | Persistent AI draft and recent-lookup IndexedDB adapter. |
| `ai-learning.js` | Typed Learning Resource resolution, caching, revisions, prebuilt packs, provider dispatch. |
| `gemini-provider.js` | Browser-side Gemini development adapter; no prompts or secret. |
| `dev_server.py` | Static development server plus local Gemini proxy, prompt construction, validation, secret lookup. |
| `scripts/` | Schema migrations, source importers, deterministic derivations, audits, exporters, focused regression tests. |
| `data/wordbank/` | Manifests, curated catalogs, derivation policies, development reports, package fallback data. |
| `data/learning-packs/` | Versioned non-canonical prebuilt AI Learning Resource packs. |
| `releases/` | Symlink or local pointer to generated external release artifacts; do not treat as normal source. |
| `docs/` | Constitution, architecture records, subsystem contracts, and this manual. |
| `tests/` | Python regression tests, currently including pronunciation pipeline coverage. |

## Local development

```bash
cd /Users/jason/Documents/Hackathon_French_Learning
python3 dev_server.py --port 4182
```

Open `http://127.0.0.1:4182/`. To force a specific release package:

```text
http://127.0.0.1:4182/?graphRoot=releases/liens-c1-c2/browser
```

The project is dependency-light static JavaScript. The development server is required for package fetches and optional Gemini endpoints, not for canonical graph access by the app.

## Required development workflow

1. Read `docs/MANUAL.md`, `LIENS_BIBLE.md`, `ARCHITECTURE_FREEZE_V1.md`, `CURRENT_STATE.md`, and relevant subsystem contracts before changing a boundary.
2. Inspect current working tree and preserve unrelated changes.
3. Make the smallest change that satisfies the product contract.
4. Run focused tests and a proportional browser check.
5. Run `git diff --check`.
6. Perform a Documentation Audit before each commit. Update only documents made inaccurate; state explicitly when none are needed.
7. Commit one logical milestone. Do not bundle unrelated UI, schema, generated artifacts, and data-source changes.

The detailed workflow is binding in [CONTRIBUTING.md](../CONTRIBUTING.md) and [AI_DEVELOPMENT_PROTOCOL.md](../AI_DEVELOPMENT_PROTOCOL.md).

## Tests and validation commands

```bash
RUNTIME_NODE=/Users/jason/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node

"$RUNTIME_NODE" --check app.js
"$RUNTIME_NODE" scripts/test_ai_learning.js
"$RUNTIME_NODE" scripts/test_sentence_intelligence.js
python3 tests/test_pronunciation_pipeline.py
git diff --check
```

Use the bundled Node path above in this workspace when `node` is not installed in the shell environment. For a release, also run the importer-specific audit, full graph audit, package export, and `scripts/test_browser_graph_package.py` as documented in [Imports and Releases](04-imports-and-releases.md).

Browser QA should verify the actual learner path, not only DOM state: Home reset; object and inflected-form lookup; sentence analysis; pronunciation labels/playback fallback; Vocabulary pagination and filters; save/notebook/review; Settings; missing/AI-unavailable states; Back/Forward branch behavior; and mobile layout when UI changes affect breakpoints.

## User feature handbook

### Home and Search

**What:** One French search field plus entry points to Today's Review, Vocabulary, Settings, and recent/curated exploration.
**Why:** Learners should not first classify “word search” versus “sentence analysis.”
**Implementation:** `home()`, `resolve()`, `go()` in `app.js`; normalization and package lookup are described in `docs/architecture/search.md`.
**Behavior:** Case and French accents are ignored for lookup, but canonical spelling is always displayed. Exact forms and expressions are resolved before sentence routing.

### Word and lexical-sense pages

**What:** A word remains the page anchor. Source-backed meanings are compact, in-place expandable panels with translations, examples, related knowledge, and save controls.
**Why:** A learner exploring *prendre* should not feel they have left it to open a second dictionary page.
**Implementation:** `objectPage()`, `senseSection()`, and graph hydration in `app.js`; sense schema in `docs/architecture/lexical_senses.md`.
**Behavior:** The page exposes CEFR, POS, frequency, own pronunciation, senses, forms/conjugation, graph links, and Learning Layer slots where present.

### Forms and conjugation

**What:** An inflected form has its own page and pronunciation, with a visible `inflected_form_of` link to the lemma. Lemma pages render data-driven conjugation groups.
**Why:** Forms are meaningful learning objects; using a lemma pronunciation or a hard-coded conjugation table is misleading.
**Implementation:** form features and relations in graph package; `formAnalysisSection()`, `conjugationSection()`, and `verbProfileSection()` in `app.js`; import/projection scripts.
**Behavior:** Core learning group is expanded, Advanced is collapsed, and one tense table is visible at a time. Subject ordering is pedagogical.

### Sentence Learning

**What:** A multi-token query opens a sentence page with local token resolution, form analysis, matched expressions/grammar, unknown tokens, and contextual learning guidance.
**Why:** A sentence is a gateway into graph knowledge, not an exact-string dictionary lookup.
**Implementation:** `sentence-intelligence.js`, `sentencePageIntegrated()` in `app.js`.
**Boundary:** The system only names grammar objects that a deterministic pattern matches. AI may teach the result but not invent grammar truth.

### Pronunciation

**What:** Pages display the object’s preferred local pronunciation representation and a small playback action.
**Why:** Pronunciation belongs to every object, including forms, rather than being a lemma-only UI decoration.
**Implementation:** `pronunciationForObject()`, `pronunciationPlayback` in `app.js`; imports/projection under `scripts/`; `docs/architecture/pronunciation.md`.
**Behavior:** Kaikki verified IPA is preferred; Lexique-derived fallback is labelled **Derived from Lexique**; “No verified IPA yet” is honest; browser TTS is playback-only and never a source of IPA.

### Vocabulary Library

**What:** Browse every canonical word by CEFR level, category, frequency-first or A–Z sort, and 20-word pagination.
**Why:** Discovery should not require already knowing what to search, while avoiding an enormous raw list.
**Implementation:** Vocabulary helpers and `vocabulary()` in `app.js`; canonical browser index from the package.
**Boundary:** It queries the existing graph; it does not copy a dictionary into a second database. Notebook is a separate personal feature.

### Notebook, Collections, and Today's Review

**What:** A learner saves typed objects, organizes them into collections, reads them in List/Card Notebook views, and revisits one calm connection per day.
**Why:** Liens should support return and memory without becoming a generic flashcard collector.
**Implementation:** `personal-learning-store.js`; Notebook/review rendering in `app.js`; contract in `docs/architecture/personal_learning.md`.
**Boundary:** Current review records Again/Good/Easy events but does not claim a spaced-repetition algorithm. Future scheduling must remain relationship-aware and operate on learner objects, not mutate the graph.

### AI Learning Assistance

**What:** Contextual content embedded within existing pages: usage guidance, sentence explanations/translations, examples, memory tips, comparisons, mistakes, and provisional unknown notes.
**Why:** The learner should receive useful help without entering a robot conversation or seeing empty learning slots.
**Implementation:** `ai-learning.js`, `ai-learning-store.js`, `gemini-provider.js`, `dev_server.py`.
**Behavior:** Resources are local-cache-first, labelled AI-generated, language-specific, revisioned, and non-canonical. See [AI chapter](05-ai-and-learning-layer.md).

### Unknown lookup

**What:** A single unknown word can receive a short provisional AI learning note and becomes a searchable recent lookup.
**Why:** Help immediately, but avoid wasting tokens or presenting an invented full lexical record.
**Implementation:** `resolve()`, `missing()`, `rememberRecentLookup()` in `app.js`; provisional lifecycle in `ai-learning.js`.
**Boundary:** No canonical word, sense, form, relation, or CEFR fact is created.

### Settings

**What:** Toggle Chinese reference content and online learning assistance.
**Why:** English remains constant while Chinese is optional; AI is a contextual capability, not a mandatory product mode.
**Implementation:** `settings()` and local preference helpers in `app.js`; browser localStorage for preferences.
**Boundary:** Settings do not alter graph content or existing canonical facts.

### Native-app navigation

**What:** Persistent Back/Forward arrows with state restoration; Home and logo reset exploration.
**Why:** Learners should not manage browser-like history or choose between duplicated Back controls.
**Implementation:** `historyEntry()`, `go()`, `goBack()`, `goForward()`, `resetToHome()` in `app.js`.
**Behavior:** Controls only render when available; a new route after Back clears Forward immediately. This is ADR-023.

## Adding a feature safely

Before implementation, answer these questions in a design note or PR/commit description:

1. Which existing Language Object(s) does this feature expose or strengthen?
2. Does it create canonical data, learner state, or learning content? Choose one owner; do not mix layers.
3. What is the source/provenance rule?
4. How does a learner enter, explore, save, and return from it?
5. Does it preserve the native navigation model and visual anchor?
6. What tests, audit, export, or documentation become necessary?

If the feature cannot answer those questions, it is probably a separate product concept rather than a Liens feature.
