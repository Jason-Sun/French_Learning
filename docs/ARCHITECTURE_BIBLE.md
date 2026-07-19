# Liens Architecture Bible

> **Architecture Freeze v1.0:** This document describes the canonical data model and current system. [Architecture Freeze v1.0](ARCHITECTURE_FREEZE_V1.md) defines the long-term layer boundaries, generated-artifact policy, release architecture, AI governance, and mandatory engineering gates. Read both before beginning architectural work.

## Constitutional principles

1. **Knowledge-first; AI-assisted second.** Local structured knowledge is the first source of truth.
2. **The Language Object Graph is the single source of truth.** UI pages, search results, sentence analysis, and review references point to stable object IDs; they do not own duplicate linguistic facts.
3. **Language Objects are the universal abstraction.** New learnable concepts should be modeled as objects plus typed relationships, not as one-off UI state.
4. **Shared linguistic knowledge.** Grammar, pronunciation, conjugation, and expressions are reusable graph knowledge across every product surface.
5. **Data before redesign.** Future expansion should primarily insert objects, metadata, and relationships rather than require browser rewrites.
6. **No hidden inheritance.** An inflected form owns its own facts, including pronunciation. A lemma is linked, never silently substituted.
7. **Compatibility is deliberate.** Additive migrations and browser adapters preserve working lookup paths while the model evolves.

## System overview

Liens is currently a dependency-free static browser application backed by a versioned local SQLite knowledge database and a generated browser data package. SQLite is the authoritative runtime graph representation; the long-term repository source of truth is the deterministic recipe that builds it: schemas, migrations, pinned source manifests, importers, curation, validation, and release configuration.

```text
SQLite Language Object Graph
        ↓ export adapter
browser/manifest.json + lookup.json
        ↓ lazy detail shards
Browser graph adapter + Sentence Intelligence
        ↓
Object / sentence learning surfaces
        ↓
Local learner preferences and saved-object state
```

SQLite is the authoritative runtime linguistic store. The versioned browser package is a read-optimized projection, not a competing database: a normalized lookup bootstrap resolves ordinary queries and deterministic sentence analysis, while full Language Object details load and cache by deterministic shard only when explored. The browser may hold transient sentence analysis and learner state, but it must not become the authoritative source for linguistic knowledge. SQLite and browser packages are release artifacts once the deterministic build foundation described in the Architecture Freeze is complete. When served locally, the browser adapter prefers the available complete release package and falls back to the checked-in portable development package; a read-only `graphRoot` URL parameter may pin an explicitly served release package. Package selection never changes canonical data.

## Language Object Graph

`language_objects` supplies the current browser-compatible representation. The source-independent canonical identity registry owns permanent UUIDv5 `canonical_id` values and canonical identity keys; importers resolve or map to those IDs and never invent identity. External links, learner state, collections, and future APIs must use canonical IDs.

Canonical linguistic assertions are modeled separately as **Language Object → Fact → Evidence**. `canonical_facts` holds an atomic claim; typed value tables hold code, number, text, or object values; `fact_evidence` supports one or more source records per claim. This allows CEFR, IPA, frequency, morphology, and other facts to have independent provenance and future conflict resolution.

Every fact is predicate-based: **Language Object → predicate → typed value → Evidence**. The predicate registry owns value type and query semantics, while a fact lifecycle belongs to the individual claim. Facts never become anonymous JSON values. Conflicting source claims remain separate, evidenced facts until an explicit editorial policy selects or supersedes a claim.

Typed `relationships` provide graph navigation. New canonical relationship imports carry independent `relationship_evidence`, so an edge can be supported, disputed, or superseded without changing either endpoint identity. Flexible structured data is held in focused tables such as definitions, attributes, form features, verb metadata, tense metadata, realizations, teaching guidance, and pronunciation details.

Multi-word objects preserve their actual sequence in `multiword_components`: each ordered position points to a component Language Object. `multiword_component_evidence` records the source surface for that position. A deduplicated `contains` relationship remains the graph-navigation projection, while the component tables retain repeated words and order without encoding either inside a text blob.

Important object types include `word`, `lexical_sense`, `inflected_form`, `expression`, `grammar_construction`, `sentence`, `conjugation_paradigm`, `conjugation_tense`, `conjugation_realization`, `learning_group`, `learning_resource`, and `pronunciation`.

Grammar is first-class graph knowledge, not per-sentence AI output. `grammar_construction`, `conjugation_tense`, and `sentence_pattern` are grammar objects; `grammar_topic` provides broad navigation without duplicating those concepts. Their taxonomy lives in `grammar_metadata`, their identity and structural relationships are canonical, and their learner-facing explanations are revisioned Learning Resources.

Relationships are directional and typed. Examples: `has_sense`, `inflected_form_of`, `belongs_to_conjugation`, `member_of_paradigm`, `contains`, `realizes_tense`, `explains`, `illustrates`, and `has_pronunciation`.

Lexical meaning is graph-native. A `word` links to ordered `lexical_sense` objects through `has_sense`; each sense owns independently evidenced, predicate-based gloss facts. A browser may project a compact gloss, but it must not collapse distinct senses into one canonical definition. The primary learning surface preserves the owner word as the visual anchor and renders a selected sense as contextual expansion state; direct sense links resolve to that owner shell. Source-aligned examples are projected only onto their matching sense.

## Browser and search architecture

The browser loads the compact lookup projection once, builds ID and normalized-form indexes, and resolves input in this order:

```text
user input
→ case/diacritic normalization (original input preserved for display)
→ local object lookup (lemmas, forms, expressions, grammar-capable objects)
→ inflected-form preference when an exact form exists
→ direct object route
→ sentence route for unresolved multi-token input
→ deterministic Sentence Intelligence analysis
```

Canonical spelling is never normalized in stored presentation data. Search normalization is an index key only. Browser pages use graph IDs and relationships, not hard-coded verb or grammar lists.

## Sentence Intelligence

The Sentence Intelligence Layer is a deterministic, local browser adapter over the exported graph. It tokenizes input, resolves forms and lemmas, emits exact form-analysis nodes, handles selected contractions/elisions, detects supported expressions and grammar patterns, emits evidence-linked nodes and edges, and identifies review candidates. Analyses are transient: reusable knowledge is promoted to the main graph only through an explicit reviewed workflow.

It is intentionally not an AI chat system. Its current grammar coverage is bounded; unknown material is surfaced honestly rather than fabricated. The presentation must keep matched Grammar Objects separate from resolved form observations. An AI Learning Resource receives this deterministic result as a read-only contract: it may explain a listed match but may not infer an additional construction or blend several homographic form analyses into one form page.

## Conjugation system

Verb learning is graph-native:

```text
verb → root paradigm → tense paradigm → reusable tense
                          ↓
                    forms or realizations
```

Learning groups (Core A1–A2 and Advanced B1+) contain reusable tense objects. Verb-specific paradigms realize them. Simple forms are `inflected_form` objects; compound and periphrastic forms are `conjugation_realization` objects assembled from ordered component Language Objects. Teaching explanations are `learning_resource` objects, never UI literals. The browser renders pedagogical subject order and one selected tense at a time.

French verb-group classification is a predicate fact, not a browser rule or a property assumed from a lexical importer. The versioned derivation policy uses canonical lemma spelling and, where necessary, source-backed present-participle morphology. Its fact evidence records both the policy run and the source records it derived from. A verb without enough evidence remains unclassified in the UI.

Imported form analyses are not enough by themselves for learner-facing conjugation. A deterministic, evidenced projection maps each supported morphology pair to the shared tense taxonomy and builds the verb-specific tense-paradigm path used by the browser. This makes forms such as `mange`, `manges`, and `mangeons` available under `Présent` without treating the UI as the source of their grouping.

## Pronunciation system

Pronunciation is a first-class graph subsystem. Each language object owns one stable, source-independent `pronunciation` object through `has_pronunciation`. That object owns parallel evidence-backed representations: Lexique phonological code and syllabification, Kaikki verified IPA (including regional/dialect metadata), audio URLs as metadata, and future assets or TTS metadata. IPA is not assumed to be the canonical source representation.

Where Kaikki IPA is absent, the deterministic `lexique383_to_ipa_v1` pipeline may project a temporary IPA representation. It is explicitly `derived`, labelled **Derived from Lexique**, and is automatically superseded by a Kaikki IPA representation for the same pronunciation object. Browser TTS is playback only; it never becomes a graph representation or pronunciation fact.

The legacy `pronunciations` table remains an import-compatible boundary and is synchronized into graph objects. A form can only display or play its own pronunciation—never its lemma’s pronunciation. The browser provider interface is local recording → cached local TTS → browser speech synthesis. No online provider is currently registered.

## Learning and persistence

Every saved or reviewable item is keyed by a stable Language Object ID where a canonical object exists; a learner-entered sentence keeps a separate learner target key plus its original input. The Personal Learning Layer persists typed saved objects, collection memberships, and append-only review events in a separate browser IndexedDB database. It may reference canonical IDs but cannot mutate or become part of SQLite. Learner-scoped AI Learning Resources and unknown-lookup history live in their own IndexedDB AI Learning Database under the same boundary. SQLite provides durable linguistic data; account-level synchronization is a future persistence concern and must reference IDs rather than copy language content.

## Source and Learning Layers

The Source Layer is independent from the graph: source catalogs, frozen releases, import runs, immutable source records, mappings, exclusions, and fact evidence let FLELex, Lexique, Lefff, Wiktionary, commercial datasets, or future sources feed the same canonical schema. No canonical table is shaped around a particular provider.

The Learning Layer contains explanations, teacher notes, memory hints, usage advice, and future exercises as `learning_resource` objects linked to canonical IDs. AI is one authoring mode alongside human, teacher, and imported resources. Learning resources never write canonical linguistic facts; promotion requires an explicit reviewed canonical import.

Learning Resource content is revisioned and immutable. A resource has ordered revisions, with at most one published revision at a time; later authoring supersedes a revision rather than destructively changing it.

The first browser AI-assistance adapter is learner-scoped and non-canonical: it stores labelled AI drafts, revisions, provenance, lifecycle state, and normalized unknown-lookups in a dedicated IndexedDB AI Learning Database, but it never writes SQLite or the browser graph export. Canonical source-backed resources take precedence; an active stored draft is reused before an online provider is called, and is retained as `superseded` history when replaced by canonical content. Its development Gemini adapter is behind typed Language Object/Learning Resource methods, so prompts and Gemini-specific API details remain outside the browser application contract. See [AI Learning Assistance](architecture/ai_learning_assistance.md).

## Natural-language analysis boundary

Future sentence parsing may be deterministic, AI-assisted, or hybrid, but its output remains non-canonical. It may resolve spans to canonical UUIDs, including lemmas, inflected forms, contraction components, expressions, collocations, grammar constructions, and sentence targets. It may attach a Learning Resource revision for an explanation. It must never directly create or overwrite canonical objects, facts, or relationships.

Canonical example sentences are separate `sentence` Language Objects. `sentence_source_alignments` preserves the source-backed link from a sentence span to the canonical sense it illustrates; `illustrates` remains an independently evidenced graph edge.

The analysis role is `grammar_object`, not a specific tense or construction type. It identifies existing grammar nodes and their typed graph paths; AI may explain why a matched node applies but cannot invent or redefine it.

## Scalability and extension rule

Listening exercises, cultural notes, grammar lessons, reading passages, quizzes, media, and reviewed AI enrichments should enter as Language Objects and typed data/relationships. A new feature should first ask: what object owns this fact; which existing object reuses it; and which relationship makes it discoverable?

See [architecture/](architecture/) for subsystem contracts.
