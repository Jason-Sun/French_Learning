# Liens Decision Log

This is an append-only record. Amend historical entries only to correct factual errors; record a new decision when direction changes.

## ADR-020 — Persist AI Learning Resources in a separate local database

**Date:** 2026-07-19
**Status:** Accepted

### Decision

Replace the browser-localStorage AI draft cache with a learner-scoped IndexedDB AI Learning Database. It stores AI Learning Resource revisions, normalized unknown-lookup history, provider/model provenance, timestamps, bounded generation context, and lifecycle state. It remains independent from the canonical SQLite graph and its browser package.

Resolution is canonical source-backed resource → active AI Learning Database resource → online provider. When canonical coverage later occupies a matching supported learning slot, the AI resource is marked `superseded` and retained as history rather than deleted.

### Consequences

Repeat visits can reuse durable local drafts without provider cost, and unknown lookups can be searched by normalized query. AI cannot alter canonical objects, facts, evidence, relationships, or exports. The data remains per browser/device until a future user-state sync policy explicitly includes it.

## ADR-019 — Unknown lookups start with one bounded learning draft

**Date:** 2026-07-19
**Status:** Accepted

### Decision

When a learner searches an item that has no local Language Object, Liens generates and caches only one short English `provisional_lookup` Learning Resource when online assistance is enabled. The unknown query is retained as normalized learner-local recent-lookup history, allowing the learner to reopen the cached learning surface from Home or by searching again. Examples, comparisons, memory tips, common-mistake notes, and reference-language resources are separate explicit requests.

### Consequences

The first encounter remains helpful without treating an unknown word as a reason to generate an entire dictionary entry. Cache reuse makes repeat visits free of new provider calls, while progressive disclosure keeps token cost and cognitive load proportional to learner intent. Neither the draft nor recent history creates a canonical object, fact, relationship, SQLite record, or browser graph search entry.

## ADR-017 — AI learning help is explicit, contextual, and revision-preserving

**Date:** 2026-07-18
**Status:** Accepted

### Decision

AI Learning Resources are generated only when a learner selects a contextual action on a word, sense, grammar object, sentence, or unknown lookup. The first resource is compact and cached locally. Follow-up resources—examples, memory tips, comparisons, and common-mistake notes—are separately requested through progressive disclosure. Local generations retain revisions so future regeneration and history controls can be added without changing resource identity or the surrounding page.

### Consequences

Liens remains anchored to the current Language Object and never opens a chatbot surface. Cache reads cannot trigger an AI call. Unknown lookups produce explicitly provisional, unverified learning notes. Curated or source-backed Learning Resources can later replace the AI draft in the same contextual slot without changing canonical graph data or routes.

## ADR-016 — Gemini is the initial development provider behind typed Learning Resource methods

**Date:** 2026-07-18
**Status:** Accepted

### Decision

Use Gemini as Liens' first live development provider. The browser and Learning Layer request typed, Language Object-oriented operations—such as `generateUsageNote`, `explainGrammar`, and `explainSentence`—rather than prompts or a generic provider call. Gemini prompt construction, model selection, and API-key handling stay inside a local development adapter/server.

### Consequences

`GEMINI_API_KEY` is read only from the local server environment and is never included in browser code. Gemini output remains a labelled, learner-scoped AI Learning Resource draft; it cannot mutate canonical objects, facts, relationships, SQLite, or browser graph exports. Replacing Gemini later requires a new provider adapter implementing the same typed methods, not UI or graph changes.

## ADR-015 — Architecture Freeze v1.0 and generated-artifact boundary

**Date:** 2026-07-17
**Status:** Accepted

### Context

Liens has reached a useful A1 Golden Slice, but its SQLite graph and browser index are large generated files currently present in Git history. This already blocks standard GitHub pushes and would become increasingly harmful as A2–C2, sentences, media, and future clients are added. At the same time, future review, collections, sync, and AI need clear boundaries so they do not corrupt canonical linguistic knowledge.

### Decision

Adopt [Architecture Freeze v1.0](ARCHITECTURE_FREEZE_V1.md) as the living long-term architecture reference.

- The canonical graph remains source-independent, UUID-based, and structured as Object → predicate-based Fact → Evidence, with typed evidence-backed relationships.
- Local SQLite remains the authoritative runtime graph representation; it and browser indexes become generated, immutable release artifacts after a deterministic build/release pipeline is in place.
- Git contains the reproducible recipe: schemas, migrations, importers, pinned manifests, curated inputs, validation, audit, documentation, and release configuration.
- User state is a separate future domain referencing canonical UUIDs; collections and review are not shared Language Objects.
- AI creates drafts and analyses only. Review and explicit promotion are required before any canonical graph change.
- Browser clients access versioned data packages through stable adapters, evolving from the current eager prototype index to sharded/lazy packages as needed.

### Consequences

The next foundation milestone is a reproducible data build and release process, not additional prototype data. Existing branch history is not rewritten by this decision; any migration away from committed generated artifacts happens only after the build is proven and with explicit approval. Future architectural work must amend the Freeze and this log when it changes these boundaries.

## ADR-001 — Language Object Graph as the knowledge source of truth

**Date:** 2026-07 (initial project architecture)  
**Decision:** Model meaningful language elements as stable Language Objects connected through typed relationships in SQLite.  
**Reason:** Words alone cannot represent forms, constructions, sentences, pronunciation, and reusable learning links consistently.  
**Alternatives:** Flat dictionary tables; page-specific JSON; separate isolated vocab/grammar systems.  
**Long-term impact:** New learning content can be added as data and relationships rather than product-specific silos.

## ADR-002 — Local structured resolution before AI

**Date:** 2026-07  
**Decision:** Resolve known language material locally; reserve AI for explicit, structured draft enrichment.  
**Reason:** Core learning knowledge must be reliable, fast, explainable, and usable without an AI call.  
**Alternatives:** Chatbot-first analysis; AI as dictionary source.  
**Long-term impact:** AI cannot silently overwrite curated facts and the app remains useful without it.

## ADR-003 — Static browser projection of SQLite

**Date:** 2026-07  
**Decision:** Keep SQLite as the authoritative graph and export a browser-readable JSON projection for the current static app.  
**Reason:** The app needs local, dependency-free lookup now while preserving a durable database model for future SQLite-WASM or server adapters.  
**Alternatives:** Browser-owned JSON as source of truth; immediate backend dependency.  
**Long-term impact:** Export compatibility is a maintained adapter boundary, not an architectural fork.

## ADR-004 — Deterministic-first Sentence Intelligence

**Date:** 2026-07  
**Decision:** Build local token/object resolution and bounded grammar detection before AI analysis.  
**Reason:** Learners need traceable, linkable analysis, and unknown content must be represented honestly.  
**Alternatives:** Free-form AI sentence explanations; sentence pages without graph references.  
**Long-term impact:** AI can enrich a stable analysis contract instead of replacing it.

## ADR-005 — Graph-native conjugation realizations

**Date:** 2026-07  
**Decision:** Model simple forms and compound/periphrastic realizations as Language Objects with ordered components; organize tenses through learning-group graph data.  
**Reason:** Conjugation is learning content, not an unstructured table, and components must remain explorable.  
**Alternatives:** Hard-coded UI tables; one giant tense dropdown; duplicate strings for compound forms.  
**Long-term impact:** Adding a tense is primarily data work and forms remain connected across pages and sentences.

## ADR-006 — Pronunciation as first-class graph knowledge

**Date:** 2026-07-17  
**Decision:** Represent pronunciation as `pronunciation` Language Objects linked by `has_pronunciation`, with structured details and a replaceable local-first playback provider chain.  
**Reason:** Lemmas and inflected forms have different pronunciations, and audio delivery must not dictate data ownership.  
**Alternatives:** Lemma IPA fallback for forms; UI-owned audio logic; cloud speech API.  
**Long-term impact:** Pronunciation is reusable across words, sentences, conjugation, and future listening features; drafts and regional variants can coexist without schema redesign.

## ADR-007 — Lexical senses are first-class Language Objects

**Decision:** Model each distinct meaning as a `lexical_sense` object linked from its word with `has_sense`; store translations as predicate facts with independent evidence.

**Reason:** A text list of definitions cannot preserve separate sense identity, source provenance, navigation, or future review behavior.

**Alternatives:** Keep senses in `object_definitions`; create a source-specific sense table; let AI split meanings dynamically.

**Long-term impact:** Multiple lexical sources can map records to stable senses, senses can connect to examples, expressions, and relationships, and the browser can present ordered meanings without owning canonical data.

## ADR-008 — Canonical graph edges require independent evidence

**Decision:** Add `relationship_evidence` for new canonical relationship imports, separate from relationship identity and endpoint objects.

**Reason:** A relationship is a linguistic claim in its own right. Its source support must be queryable and revisable just as a predicate fact’s support is.

**Alternatives:** Treat relationship provenance as a column on the edge; infer evidence from either endpoint; store it as importer-only metadata.

**Long-term impact:** Grammar, lexical relations, expressions, and sentence links can retain complete provenance and future conflicts can be represented without graph redesign.

## ADR-009 — Example sentences retain source alignment

**Decision:** Keep an imported example as its own `sentence` object and record source-backed alignment to the illustrated canonical sense.

**Reason:** A sentence linked only to a word loses which meaning it demonstrates and cannot support reliable learner navigation or future analysis.

**Long-term impact:** The graph can connect a word, a sense, a sentence, and later a sentence-analysis instance without conflating their identities.

## ADR-007 — Documentation as a production boundary

**Date:** 2026-07-17  
**Decision:** Maintain this `/docs` system as the project’s durable operating memory.  
**Reason:** Future contributors and AI agents must be able to work from explicit decisions rather than conversation history.  
**Alternatives:** README-only notes; relying on commits and chat logs.  
**Long-term impact:** Architectural review becomes repeatable across years and contributors.

## ADR-008 — Source-independent canonical identities, facts, and Learning Layer

**Date:** 2026-07-17
**Decision:** Canonical Language Objects use permanent source-independent UUID identities. Linguistic knowledge is represented as Object → Fact → Evidence, and explanations live in a general Learning Layer rather than an AI-specific layer.
**Reason:** Imports must be replaceable without breaking saved objects, APIs, or learner history; individual facts require independent provenance and conflict handling; learning material can be AI-, teacher-, human-, or source-authored without becoming canonical truth.
**Alternatives:** Importer-generated object IDs; object-level source attribution only; an AI-only enrichment table.
**Long-term impact:** The graph can evolve across sources and content authors while preserving durable identity and provenance.

## ADR-009 — Predicate facts, immutable learning revisions, and non-canonical analysis

**Date:** 2026-07-17
**Decision:** Canonical knowledge uses predicate-based typed facts with fact-level evidence and lifecycle. Learning Resources have immutable ordered revisions, with at most one published revision. Sentence parser and AI outputs remain non-canonical analysis records that may reference canonical UUIDs and Learning Resource revisions only.
**Reason:** Predicate claims make indexing and conflict handling explicit; revisions preserve teaching-content history; natural-language analysis must enrich graph navigation without redefining linguistic truth.
**Alternatives:** Anonymous property values; destructive edits to explanations; allowing parser/AI outputs to write directly to the graph.
**Long-term impact:** The future parser can support arbitrary French input and AI-assisted explanations without requiring a graph redesign or weakening provenance.

## ADR-010 — Grammar is first-class graph knowledge

**Date:** 2026-07-17
**Decision:** Treat grammar constructions, tenses, moods, patterns, and broad topics as canonical Language Objects classified through shared grammar metadata and linked by typed grammar relationships. Sentence analysis identifies these existing objects; Learning Resources explain them.
**Reason:** A sentence should lead learners into a durable grammar network rather than generate a one-off grammar answer. Keeping identity and relationships canonical preserves exploration, reuse, and review.
**Alternatives:** AI-generated grammar labels per sentence; a parallel grammar database; duplicating each tense or construction as a generic grammar object.
**Long-term impact:** Grammar pages, examples, comparisons, prerequisites, and future review can grow as graph data without changing the sentence-analysis contract.

## ADR-011 — Ordered multi-word components are canonical graph structure

**Date:** 2026-07-17
**Decision:** Store the sequence of an expression, idiom, collocation, or other multi-word object in `multiword_components`, with source-specific support in `multiword_component_evidence`. Keep `contains` as the graph traversal edge, not as the sole representation of composition.

**Reason:** A simple edge cannot distinguish repeated components or preserve word order. Component sequence is structural linguistic knowledge and must remain source-backed rather than be reconstructed from UI text.

**Alternatives:** Encode components in JSON; rely on `contains` edge order; store only the display string.

**Long-term impact:** Multi-word objects can support reliable navigation, matching, source comparison, and future sentence analysis without special cases or schema redesign.

## ADR-012 — Lexical senses render in their owner-word context

**Date:** 2026-07-17
**Decision:** Preserve each lexical sense as a canonical Language Object, but render it as selected expansion state inside its owner word’s learning surface. A direct sense route resolves to the owner word with that sense selected.

**Reason:** A learner exploring several meanings is still learning one word. Replacing the lemma with a long sense label fragments the learning flow and wastes the strongest visual anchor.

**Alternatives:** A full generic page for every sense; a heavy tab route; flatten senses back into one word-level definition.

**Long-term impact:** Sense identity, saving, examples, and graph traversal remain independent, while the browser presents a calmer, scalable learning experience. Source-aligned examples can appear on the matching sense without borrowing unrelated word-level context.

## ADR-013 — French verb groups are evidence-backed derived facts

**Date:** 2026-07-17

**Decision:** Represent `verb_group` as a canonical predicate fact. Derive it with a versioned policy from canonical lemma spelling and, for `-ir` verbs, source-backed present-participle morphology; record both policy and source-record evidence. Leave unsupported cases unclassified.

**Reason:** Group is important learner-facing conjugation knowledge, but the current lexical sources do not directly publish it. A deterministic derivation is more transparent and maintainable than UI heuristics or AI-generated labels.

**Alternatives:** Hard-code groups in the browser; write group values into legacy `verb_metadata` without fact evidence; infer groups with AI; assign every `-ir` verb from spelling alone.

**Long-term impact:** Every group label is queryable, reproducible, and revisable when richer lexical evidence arrives; the UI can distinguish unavailable data from a linguistic claim.

## ADR-014 — Source form analyses project into learning tense paradigms

**Date:** 2026-07-17

**Decision:** Keep imported inflected forms as source assertions, then use a versioned deterministic projection to connect each supported `(mood, tense)` analysis to a verb-specific paradigm and a reusable learning tense. Preserve evidence on every derived graph edge.

**Reason:** A root-level form link makes morphology searchable but does not tell the learning UI which tense table should contain the form. The graph, rather than browser code, must perform that mapping.

**Alternatives:** Filter all lemma forms in the browser; copy conjugation tables into JSON; attach every source tense to a learner selector; create only a special `manger` repair.

**Long-term impact:** Any source-backed form can appear in its correct learning table after a reproducible data projection, while unsupported source tenses remain present in the graph without being falsely advertised as an available learning module.

## ADR-016 — The Learning Layer completes missing teaching slots

**Date:** 2026-07-18

**Decision:** Treat source-backed Learning Resources as the preferred content for a page, then locally cached AI drafts as the next option. When neither exists and online assistance is permitted, the Learning Resource Resolver generates a compact, clearly labelled draft automatically. Secondary resources remain progressively disclosed, but no visible primary learning slot should require the learner to operate an AI feature before receiving help.

**Reason:** Liens should not leave a learner with an empty explanation, example, or sentence-teaching surface simply because the canonical graph has not yet imported a resource. The graph supplies reliable identity, structure, and relationships; the Learning Layer supplies teaching completeness.

**Alternatives:** Require an explicit Generate button for every gap; allow AI to fill canonical fields; show silent generic placeholders.

**Long-term impact:** Provider adapters remain replaceable and learner-facing content remains reviewable, while the canonical graph stays source-backed. The setting is a privacy/network control, not a feature switch; turning it off preserves local graph access and displays an honest availability state.

## ADR-017 — Learning Resource language is an identity dimension

**Date:** 2026-07-18

**Decision:** Identify every Learning Resource by target, kind, context, and BCP-47 language tag. English and reference-language resources are independent resources with separate provenance, cache entries, revisions, and fallback resolution. The provider receives the requested language as typed resource data; prompts remain inside the provider adapter.

**Reason:** A Chinese, Japanese, Korean, or Spanish learning explanation is not an attachment to an English explanation. Making language intrinsic avoids language-specific fields and allows reference-language support to grow without a second Learning Layer.

**Alternatives:** Attach `body_zh` or `translation_zh` to English resources; make Chinese-specific resource kinds; store multilingual teaching text as canonical graph facts.

**Long-term impact:** New languages are configuration and content decisions, not schema or UI rewrites. Existing legacy Chinese display fields remain compatibility data only; new multilingual AI content stays in learner-scoped Learning Resources outside the canonical graph.

## ADR-018 — Browser graph packages separate lookup from object detail

**Date:** 2026-07-18

**Decision:** Export SQLite into a versioned browser package with a normalized lookup bootstrap, a manifest containing byte sizes and SHA-256 checksums, and deterministic Language Object detail shards. The browser loads the lookup projection for local resolution and Sentence Intelligence, then fetches and caches full Object detail only when a learner explores it.

**Reason:** A single eager JSON export became too large to scale across A2–B2 morphology, example sentences, and future media. Search and deterministic parsing need only a compact subset of the graph; definitions, provenance, neighbours, and other detail should not block the first learning interaction.

**Alternatives:** Keep one growing JSON file; query SQLite directly from the static browser immediately; build endpoint-specific API payloads that bypass a shared graph package.

**Long-term impact:** Web, desktop, and mobile clients can share a stable data-package contract. The UI remains graph-oriented while data transport can scale, cache, and move to release assets without changing canonical SQLite structure.

## ADR-019 — Deterministic analysis bounds learner-facing AI grammar

**Date:** 2026-07-19

**Decision:** Serialize the deterministic sentence analysis into every sentence Learning Resource request. The UI presents exact resolved form analyses separately from canonical Grammar Object matches. AI may explain only the listed grammar matches and exact form metadata; it may not infer or name an additional construction. A stricter resource-contract version creates a new local draft key rather than reusing misleading cached guidance.

**Reason:** A form of `aller` can appear in many contexts. Calling every present form of `aller` *futur proche* would make a learning explanation confident but incorrect. The graph must establish what applies; AI teaches that result.

**Alternatives:** Ask the model to be generally careful; let AI infer sentence grammar without structured context; treat an inflected form's surface spelling as one combined teaching object.

**Long-term impact:** Sentence guidance remains useful without silently becoming a second grammar authority. Parser improvements can add canonical matches and form analyses without changing the Learning Layer contract.
