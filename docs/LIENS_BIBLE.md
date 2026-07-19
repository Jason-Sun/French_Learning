# Liens Bible

**Status:** Living product constitution

Liens should change slowly in spirit, even when it changes quickly in capability. This document is the highest-level reference for product identity. When a design or engineering choice is ambiguous, preserve this document's intent before optimizing for speed, novelty, or implementation convenience.

Architecture belongs in [Architecture Freeze v1.0](ARCHITECTURE_FREEZE_V1.md). Current features belong in [Current State](CURRENT_STATE.md). Liens' identity belongs here.

## 1. Vision

Liens is a language learning environment built on a connected Language Knowledge Graph. It helps a learner understand French as a living system: words, forms, meanings, grammar, pronunciation, expressions, and sentences lead naturally to one another.

Liens is not:

- a dictionary that stops at a definition;
- a translator that replaces understanding with an answer;
- a fixed language course that forces every learner down one path;
- a flashcard collector optimized for accumulation;
- an AI chatbot whose conversation is the product;
- a database browser wearing a learning interface.

Liens can include capabilities associated with all of those tools, but each must serve learning through connected understanding.

## 2. Product philosophy

- **Teach, do not merely define.** Facts matter only when they help a learner make sense of language.
- **Context creates meaning.** A word is better understood through its senses, forms, patterns, examples, and neighbours than through an isolated gloss.
- **Exploration is learning.** Every meaningful object should open a useful next step; there should be no intentional dead ends.
- **Reduce friction, not thought.** Liens should remove unnecessary searching, copying, and tool switching without pretending that learning requires no effort.
- **Keep the learner oriented.** Preserve a clear anchor—usually the word, sentence, or grammar concept the learner came for—while allowing depth around it.
- **Calm beats completeness on one screen.** Show what is useful now, then reveal depth progressively.
- **The graph serves the learner.** Connections exist to make patterns visible, not to display a clever data model.

The recurring learning loop is:

**Learn → Explore → Save → Review**

## 3. Language Object philosophy

French is not divided into separate products called vocabulary, grammar, pronunciation, and examples. It is one connected language. Liens represents its meaningful elements as Language Objects so they can be learned, linked, and revisited consistently.

Examples include:

- words and lexical senses;
- inflected forms;
- expressions and collocations;
- grammar concepts and sentence patterns;
- sentences and examples;
- pronunciation and conjugation;
- future reading, listening, writing, and exercise material.

Collections and Review Items are the learner's relationship with these objects: they help the learner return to language with purpose. They must never turn the product into a pile of disconnected saved cards.

The learner should experience a natural language environment, not object types, relationships, IDs, or source records. The graph is canonical underneath; the experience above it must feel human.

## 4. UX philosophy

Liens should feel calm, minimal, smooth, continuous, and premium.

- Search accepts language as the learner has it: a word, form, expression, or sentence. The learner should not need to classify the input first.
- Direct resolution is preferable to an unnecessary results page.
- Visual anchors stay stable whenever possible. Exploring a sense should still feel like exploring the same word; exploring grammar in a sentence should preserve the sentence as context.
- Navigation is simple and trustworthy: it follows a native-app path, not browser history. Back and Forward appear only when a meaningful adjacent destination exists; navigating to a new destination discards the old Forward branch. Home (the Liens logo or Home control) begins a fresh exploration session and clears both directions.
- Progressive disclosure prevents a rich graph from becoming visual noise. Common and relevant information appears first; detail opens in place or on a deliberate next step.
- Motion explains continuity, focus, or a state change. It never exists merely to decorate, delay, or impress.
- Touch, keyboard, and screen-reader interaction deserve the same clarity as pointer interaction.

The learner should feel they are moving through one connected French world, not opening and closing isolated application pages.

## 5. Teaching philosophy

Liens should behave more like an excellent teacher than a reference book.

An excellent teacher does not only say *what* something is. They reveal:

- what it means here;
- why this form, construction, or word choice is used;
- what pattern the learner can reuse;
- what it connects to;
- what contrast or common mistake will make the idea clearer.

Teaching should build intuition through repeated, connected encounters. It should prioritize understanding, context, patterns, and relationships over exhaustive fact lists. Precision remains essential, but precision without guidance is not enough.

English is always available as a bridge. Chinese is an optional learner preference. Neither translation should replace engagement with French itself.

## 6. AI philosophy

AI is an assistant, not Liens' authority and not Liens' personality. It should be felt as quiet teaching continuity, never as a chatbot destination or a feature the learner must learn to operate.

The Language Graph guarantees trustworthy structure. The Learning Layer strives for completeness. When a source-backed teaching resource is absent, Liens may automatically create and locally cache a clearly labelled AI learning draft in that resource's place. A learner should receive useful guidance rather than an empty learning slot, while always being able to distinguish generated help from reviewed knowledge.

Learning Resources are language-specific. A resource is identified by its target, kind, context, and language; it is never an English resource with an attached translation field for another language. English is the primary teaching language. Reference languages such as Chinese are optional parallel resources that help a learner confirm meaning without creating a separate product or teaching system.

AI may:

- explain known graph knowledge in different ways;
- personalize learning guidance using learner-authorized context;
- analyze unfamiliar input and identify candidates for exploration;
- create clearly labeled, locally cached drafts, temporary assistance, or learning-resource revisions when a learning slot has no better resource;
- surface gaps that need source-backed or editorial work.

AI may not silently modify canonical linguistic knowledge, conceal uncertainty, or present generated content as curated truth. Approved knowledge retains provenance. A confident answer is never more valuable than an honest one.

## 7. Engineering philosophy

Engineering choices should protect the learning experience for years, not only the next demo.

- Preserve graph integrity, stable identity, and provenance.
- Keep canonical knowledge reproducible from attributable inputs and deterministic rules.
- Treat generated data packages as releases, not hand-edited truth.
- Keep user learning state separate from shared language knowledge.
- Make local structured knowledge useful before asking AI or a network service.
- Use adapters and explicit contracts so clients can evolve without creating competing models of French.
- Prefer additions to the graph over one-off feature silos.
- Make uncertainty, coverage gaps, and draft status visible rather than inventing confidence.

The system should make the right product behavior easy and shortcuts that damage trust difficult.

## 8. Design philosophy

Liens should be elegant, spacious, learner-first, and timeless.

The typography, rhythm, colour, and motion should make sustained reading and thought feel comfortable. The interface should recede when the language deserves attention and become clear when the learner needs orientation or choice.

Avoid interfaces that feel like:

- an IDE;
- an analytics dashboard;
- an admin panel;
- a dense grammar table;
- a gamified collection machine;
- a chat window pretending to teach.

Premium does not mean ornate. It means considered hierarchy, legible detail, deliberate empty space, and no interaction that asks for attention without returning understanding.

## 9. Long-term vision

Over time, Liens can become richer in every direction: a deeper French graph, more useful review, sentence-level guidance, carefully governed AI tutoring, reading and listening environments, collaborative curation, and perhaps additional languages.

Those possibilities are expansions, not reinventions. A future feature belongs in Liens only when it strengthens the same promise: help a learner understand and navigate a connected language with clarity, trust, and calm.

## Living document

This document evolves slowly. Do not rewrite it for a feature, a design trend, or a temporary implementation constraint. Update it only when Liens' enduring product identity changes.

When documents disagree:

1. Preserve this document's learner-facing intent.
2. Use the Architecture Freeze to resolve system boundaries.
3. Record a new decision rather than silently redefining either.
