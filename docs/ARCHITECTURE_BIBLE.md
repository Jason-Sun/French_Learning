# Liens Architecture Bible

## Constitutional principles

1. **Knowledge-first; AI-assisted second.** Local structured knowledge is the first source of truth.
2. **The Language Object Graph is the single source of truth.** UI pages, search results, sentence analysis, and review references point to stable object IDs; they do not own duplicate linguistic facts.
3. **Language Objects are the universal abstraction.** New learnable concepts should be modeled as objects plus typed relationships, not as one-off UI state.
4. **Shared linguistic knowledge.** Grammar, pronunciation, conjugation, and expressions are reusable graph knowledge across every product surface.
5. **Data before redesign.** Future expansion should primarily insert objects, metadata, and relationships rather than require browser rewrites.
6. **No hidden inheritance.** An inflected form owns its own facts, including pronunciation. A lemma is linked, never silently substituted.
7. **Compatibility is deliberate.** Additive migrations and browser adapters preserve working lookup paths while the model evolves.

## System overview

Liens is currently a dependency-free static browser application backed by a versioned SQLite knowledge database and a generated JSON browser index.

```text
SQLite Language Object Graph
        ↓ export adapter
wordbank-index.json
        ↓ load once
Browser object resolver + Sentence Intelligence
        ↓
Object / sentence learning surfaces
        ↓
Local learner preferences and saved-object state
```

SQLite is the authoritative linguistic store. `wordbank-index.json` is a read-optimized browser projection, not a competing database. The browser may hold transient sentence analysis and learner state, but it must not become the authoritative source for linguistic knowledge.

## Language Object Graph

`language_objects` supplies the current browser-compatible representation. The source-independent canonical identity registry owns permanent UUIDv5 `canonical_id` values and canonical identity keys; importers resolve or map to those IDs and never invent identity. External links, learner state, collections, and future APIs must use canonical IDs.

Canonical linguistic assertions are modeled separately as **Language Object → Fact → Evidence**. `canonical_facts` holds an atomic claim; typed value tables hold code, number, text, or object values; `fact_evidence` supports one or more source records per claim. This allows CEFR, IPA, frequency, morphology, and other facts to have independent provenance and future conflict resolution.

Every fact is predicate-based: **Language Object → predicate → typed value → Evidence**. The predicate registry owns value type and query semantics, while a fact lifecycle belongs to the individual claim. Facts never become anonymous JSON values. Conflicting source claims remain separate, evidenced facts until an explicit editorial policy selects or supersedes a claim.

Typed `relationships` provide graph navigation. Flexible structured data is held in focused tables such as definitions, attributes, form features, verb metadata, tense metadata, realizations, teaching guidance, and pronunciation details.

Important object types include `word`, `inflected_form`, `expression`, `grammar_construction`, `sentence`, `conjugation_paradigm`, `conjugation_tense`, `conjugation_realization`, `learning_group`, `learning_resource`, and `pronunciation`.

Grammar is first-class graph knowledge, not per-sentence AI output. `grammar_construction`, `conjugation_tense`, and `sentence_pattern` are grammar objects; `grammar_topic` provides broad navigation without duplicating those concepts. Their taxonomy lives in `grammar_metadata`, their identity and structural relationships are canonical, and their learner-facing explanations are revisioned Learning Resources.

Relationships are directional and typed. Examples: `inflected_form_of`, `belongs_to_conjugation`, `member_of_paradigm`, `contains`, `realizes_tense`, `explains`, `illustrates`, and `has_pronunciation`.

## Browser and search architecture

The browser loads the exported graph once, builds ID and normalized-form indexes, and resolves input in this order:

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

The Sentence Intelligence Layer is a deterministic, local browser adapter over the exported graph. It tokenizes input, resolves forms and lemmas, handles selected contractions/elisions, detects supported expressions and grammar patterns, emits evidence-linked nodes and edges, and identifies review candidates. Analyses are transient: reusable knowledge is promoted to the main graph only through an explicit reviewed workflow.

It is intentionally not an AI chat system. Its current grammar coverage is bounded; unknown material is surfaced honestly rather than fabricated.

## Conjugation system

Verb learning is graph-native:

```text
verb → root paradigm → tense paradigm → reusable tense
                          ↓
                    forms or realizations
```

Learning groups (Core A1–A2 and Advanced B1+) contain reusable tense objects. Verb-specific paradigms realize them. Simple forms are `inflected_form` objects; compound and periphrastic forms are `conjugation_realization` objects assembled from ordered component Language Objects. Teaching explanations are `learning_resource` objects, never UI literals. The browser renders pedagogical subject order and one selected tense at a time.

## Pronunciation system

Pronunciation is a first-class graph subsystem. A language object links to one or more `pronunciation` objects through `has_pronunciation`. Each Pronunciation Object owns multiple evidence-backed representations: source phonological codes, verified IPA, syllabification, variants, audio assets, and future TTS metadata. IPA is not assumed to be the canonical source representation.

The legacy `pronunciations` table remains an import-compatible boundary and is synchronized into graph objects. A form can only display or play its own pronunciation—never its lemma’s pronunciation. The browser provider interface is local recording → cached local TTS → browser speech synthesis. No online provider is currently registered.

## Learning and persistence

Every saved or reviewable item is keyed by a stable Language Object ID. The current static prototype stores saved items and the Chinese-display preference in browser local storage. SQLite provides durable linguistic data; account-level review synchronization is a future persistence concern and must reference IDs rather than copy language content.

## Source and Learning Layers

The Source Layer is independent from the graph: source catalogs, frozen releases, import runs, immutable source records, mappings, exclusions, and fact evidence let FLELex, Lexique, Lefff, Wiktionary, commercial datasets, or future sources feed the same canonical schema. No canonical table is shaped around a particular provider.

The Learning Layer contains explanations, teacher notes, memory hints, usage advice, and future exercises as `learning_resource` objects linked to canonical IDs. AI is one authoring mode alongside human, teacher, and imported resources. Learning resources never write canonical linguistic facts; promotion requires an explicit reviewed canonical import.

Learning Resource content is revisioned and immutable. A resource has ordered revisions, with at most one published revision at a time; later authoring supersedes a revision rather than destructively changing it.

## Natural-language analysis boundary

Future sentence parsing may be deterministic, AI-assisted, or hybrid, but its output remains non-canonical. It may resolve spans to canonical UUIDs, including lemmas, inflected forms, contraction components, expressions, collocations, grammar constructions, and sentence targets. It may attach a Learning Resource revision for an explanation. It must never directly create or overwrite canonical objects, facts, or relationships.

The analysis role is `grammar_object`, not a specific tense or construction type. It identifies existing grammar nodes and their typed graph paths; AI may explain why a matched node applies but cannot invent or redefine it.

## Scalability and extension rule

Listening exercises, cultural notes, grammar lessons, reading passages, quizzes, media, and reviewed AI enrichments should enter as Language Objects and typed data/relationships. A new feature should first ask: what object owns this fact; which existing object reuses it; and which relationship makes it discoverable?

See [architecture/](architecture/) for subsystem contracts.
