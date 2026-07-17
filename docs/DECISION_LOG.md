# Liens Decision Log

This is an append-only record. Amend historical entries only to correct factual errors; record a new decision when direction changes.

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
