# 7. Design History and Roadmap

## How Liens evolved

Liens began as a French-learning prototype with a small wordbank. Its important evolution was not “add more definitions”; it was moving from a flat dictionary demo to a durable, source-independent Language Graph and then protecting that graph from product shortcuts.

This timeline summarizes the decisions a future maintainer needs to understand. The authoritative historical record remains [DECISION_LOG.md](../DECISION_LOG.md).

| Stage | What changed | Why | Rejected alternative |
| --- | --- | --- | --- |
| Prototype wordbank | Initial local SQLite lookup and polished learning UI | Prove an offline-feeling direct-learning flow | Building a cloud-only dictionary/chat interface. |
| Language Object graph | Words, forms, senses, expressions, grammar, sentences, and pronunciation became graph objects | French learning traverses connected objects, not independent pages | Treating inflected forms and grammar as text embedded in a word entry. |
| Stable identity and provenance | Canonical UUIDs plus Object → Fact → Evidence | Saves and imports must survive source replacement; claims need independent support | Auto-increment IDs or attaching one source directly to an object. |
| Learning Layer | Revisioned teaching resources separated from graph facts | Explanations can evolve or be AI-assisted without redefining French | AI text stored as word definitions or canonical facts. |
| Grammar as first-class graph knowledge | Grammar objects, patterns, relations, prerequisites, contrasts, teaching links | Sentence analysis should point to explorable grammar, not emit isolated prose | An AI parser inventing grammar explanations on every request. |
| Production source strategy | FLELex baseline; Lexique/Morphalou morphology; Kaikki senses/relations/pronunciation | Build reproducible, evidence-backed coverage rather than a hard-coded demo list | LLM-generated A1–B2 lexical truth or source-specific schemas. |
| A1 Golden Slice | Morphology, senses, pronunciation, grammar, expressions, examples, audits | Validate a full production pattern on one level before scaling | Expanding levels before the import/audit design was proven. |
| Browser package sharding | Lookup bootstrap plus lazy detail shards | Static browser scale without eagerly loading the full graph | One giant `wordbank-index.json`. |
| Pronunciation representations | One stable Pronunciation Object; Lexique + Kaikki parallel; derived fallback lifecycle | Avoid conflating phonological code, IPA, audio metadata, and TTS | Replacing Lexique with IPA or using lemma IPA for forms. |
| AI Learning Database | Local IndexedDB resource revisions with typed provider methods | Useful help without repeat cost or graph pollution | A visible chatbot, `localStorage`-only drafts, or generic prompt API. |
| Personal Learning Layer | Typed saves, collections, Notebook, lightweight review | Return to meaningful graph objects without copying flashcards | One untyped “saved items” list or a premature SRS algorithm. |
| Vocabulary Library | CEFR/category/frequency discovery over canonical graph | Make vocabulary browsing a textbook-like entry point | Duplicate dictionary database or saved-items-only vocabulary. |
| Native-app navigation | One Back/Forward system; Home resets | Calm, oriented exploration modeled after Apple apps | Browser-style infinite history and duplicate page-level Back controls. |

## Important rejected directions

### “Let AI fill the database automatically”

Rejected for canonical knowledge. AI may fill a learner-facing teaching slot, but it does not own language identity, form links, grammar rules, source provenance, or reviewable facts. The right workflow is AI draft → human/source review → explicit canonical import if warranted.

### “Use one huge comprehensive dictionary JSON”

Rejected because it harms startup performance, Git history, browser memory, and future client compatibility. SQLite is the canonical generated build representation; browser package shards are the runtime transport.

### “Make pronunciation a single IPA field”

Rejected because sources provide different representations and form pronunciation differs from lemma pronunciation. The chosen model supports Lexique code, verified Kaikki IPA, regional variants, audio URL metadata, deterministic fallback IPA, and future local recordings without changing identity.

### “Treat sentence analysis as a general parser”

Rejected as a product model. Liens uses deterministic sentence intelligence only as a gateway into existing graph objects. It does not make completeness claims, and AI analysis cannot invent canonical grammar application.

### “Turn Notebook into Anki”

Rejected. The current Personal Learning Layer supports return and review, but its advantage is graph context. A future scheduler should sequence relationships, forms, senses, grammar, and sentences—not erase them into generic cards.

### “Build a chatbot UI”

Rejected. AI appears inside familiar learning-resource slots on object and sentence pages. The current language object remains the visual anchor.

## Completed capabilities

The verified active release and counts are maintained in [CURRENT_STATE.md](../CURRENT_STATE.md). At a system level, Liens has completed:

- a source-independent A1–C2 lexical graph release;
- local exact/accent-insensitive object and form lookup;
- evidence-backed simple morphology and conjugation projections;
- lexical senses, examples, expressions, selected relations, and first-class grammar topology;
- source-backed Kaikki pronunciation plus Lexique parallel representations and derived fallback lifecycle;
- sharded static browser package loading;
- deterministic Sentence Intelligence;
- language-specific, revisioned local AI learning drafts behind a typed Gemini development adapter;
- typed learner saves, collections, Notebook, and lightweight review;
- CEFR/frequency/category Vocabulary Library;
- native-app branch navigation and Home reset;
- documented import, audit, browser-package, and release recipes.

## Current limitations

These are known limits, not permission to hide them from learners or patch around them with fabricated data:

| Area | Current limitation | Correct next response |
| --- | --- | --- |
| Lexical coverage | Source-backed senses, examples, expressions, and pronunciation are uneven despite broad lexical identity coverage | Continue source-backed enrichment and retain explicit gaps. |
| Grammar | Canonical grammar network is intentionally bounded; Sentence Intelligence supports a limited set of deterministic patterns | Add attributable grammar topology and rules only where structural match is reliable. |
| Conjugation | Simple source-attested forms are strong; compound/periphrastic coverage and teaching resources remain incomplete | Source or curate compound realizations; never fabricate paradigms in UI. |
| Pronunciation | Kaikki IPA does not cover every graph object; browser TTS is only playback | Use verified source coverage; retain Derived from Lexique label where needed; add local audio later. |
| AI transport | Gemini proxy is development-only and API keys are environment based | Build protected production transport, consent, privacy, rate limiting, and observability before public deployment. |
| Personal learning | IndexedDB is device-local; review is lightweight, not a true scheduler | Design account/sync separately and add relationship-aware scheduling after user research. |
| UI implementation | Direct-DOM `app.js` is compact but growing | Introduce internal view/data/navigation boundaries before major UI expansion. |
| Release operations | Source acquisition is explicit/local and release distribution is not fully automated | Add acquisition verification, attribution gates, CI, artifact publishing, and compatibility policy. |

## Recommended next milestones

### Near term: product quality, not more architecture

1. **Learner QA loop.** Test common A1–B2 learner journeys repeatedly; fix broken pages, missing labels, navigation edge cases, visual density, and mobile behavior.
2. **Teaching quality evaluation.** Review generated and prebuilt Learning Resources by object type; improve provider prompts/versioning using real learner feedback; keep drafts distinct.
3. **Source-backed enrichment.** Prioritize high-frequency gaps in senses, examples, grammar links, compound conjugations, and pronunciation coverage. Add only attributable data.
4. **Release reproducibility hardening.** Automate source acquisition verification, license/attribution checks, CI audits, package tests, and artifact publishing.

### Medium term: deepen the learning loop

1. Design a relationship-aware review scheduler using existing learner object identities and review-event history.
2. Add collection management refinement, learner progress signals, and review explanations without turning the product into a flashcard dashboard.
3. Add source-backed compound forms, more grammar network topology, reading passages, and higher-quality example coverage.
4. Split `app.js` into navigation, data-access, view-model, and renderer modules while preserving UI identity and package contract.

### Longer term: production platform

1. Build a secure provider registry and production AI proxy; support multiple providers/local models as configuration, not page changes.
2. Design authentication, encrypted/safe sync, conflict rules, privacy/consent, and portability of personal state using canonical UUID references.
3. Add local audio assets/cached TTS and listening objects without altering pronunciation ownership.
4. Support reading, listening, writing, quizzes, and additional languages as Language Objects and Learning Resources, not separate product silos.
5. Establish editorial review tooling that can promote reviewed source-backed/curated contributions through the canonical import pipeline.

## Decision rule for future proposals

Before approving a proposal, ask:

1. Does it help a learner understand connected language more clearly?
2. Which layer owns its data: canonical graph, learning layer, personal state, or transient UI?
3. Is its provenance and lifecycle explicit?
4. Does it preserve source independence, stable identity, and reproducibility?
5. Does it feel like Liens—calm, local-first, exploratory, and not chatbot-shaped?

If the proposal fails these tests, redesign it before implementation. See [ROADMAP.md](../ROADMAP.md) for active milestone tracking and [DECISION_LOG.md](../DECISION_LOG.md) for the full rationale record.
