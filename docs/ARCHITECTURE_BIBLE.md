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

`language_objects` supplies stable IDs, canonical and display forms, type, CEFR, part of speech, frequency, provenance, and lifecycle status. Typed `relationships` provide graph navigation. Flexible structured data is held in focused tables such as definitions, attributes, form features, verb metadata, tense metadata, realizations, teaching guidance, and pronunciation details.

Important object types include `word`, `inflected_form`, `expression`, `grammar_construction`, `sentence`, `conjugation_paradigm`, `conjugation_tense`, `conjugation_realization`, `learning_group`, `learning_resource`, and `pronunciation`.

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

Pronunciation is a first-class graph subsystem. A language object links to one or more `pronunciation` objects through `has_pronunciation`. `pronunciation_object_details` stores IPA, syllables, stress, liaison, silent letters, elision, variants, source, confidence, review status, and optional local audio metadata.

The legacy `pronunciations` table remains an import-compatible boundary and is synchronized into graph objects. A form can only display or play its own pronunciation—never its lemma’s pronunciation. The browser provider interface is local recording → cached local TTS → browser speech synthesis. No online provider is currently registered.

## Learning and persistence

Every saved or reviewable item is keyed by a stable Language Object ID. The current static prototype stores saved items and the Chinese-display preference in browser local storage. SQLite provides durable linguistic data; account-level review synchronization is a future persistence concern and must reference IDs rather than copy language content.

## AI enrichment architecture

Future AI output is structured enrichment, not direct truth. It must be attached to an object with source, provenance, confidence, review status, and a draft lifecycle. Curated data is never overwritten by an AI draft. AI must use existing object identities and relation types whenever possible.

## Scalability and extension rule

Listening exercises, cultural notes, grammar lessons, reading passages, quizzes, media, and reviewed AI enrichments should enter as Language Objects and typed data/relationships. A new feature should first ask: what object owns this fact; which existing object reuses it; and which relationship makes it discoverable?

See [architecture/](architecture/) for subsystem contracts.
