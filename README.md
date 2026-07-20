# Liens — French learning in context

Liens is a learning-first French web app. It treats words, forms, collocations, and sentences as connected learning objects rather than separate dictionary entries or chat messages.

## Project overview

Most French-learning tools make learners move between a dictionary, conjugator,
grammar site, translation tool, flashcards, and an AI chat. Liens is an
explorable, local-first Language Graph that brings those learning paths into one
calm interface. A word leads to its forms, senses, pronunciation, grammar,
expressions, examples, and related sentences; a sentence is an entry point into
the same graph, not a dead-end analysis.

The graph is the evidence-backed source of linguistic truth. AI may fill a
missing teaching resource, but it is labelled, cached separately, and never
silently changes canonical knowledge.

## Key features

- **Local Language Graph:** A1–C2 words, forms, senses, expressions, grammar,
  pronunciation representations, and examples are connected as navigable
  Language Objects.
- **Search that understands forms:** Accent-insensitive lookup resolves lemmas,
  inflected forms, and multi-word expressions to their canonical objects.
- **Sentence Intelligence:** Deterministic local analysis identifies tokens,
  known forms, expressions, and grammar before optional teaching enrichment.
- **Learning in context:** Word and sentence pages keep the current object as a
  visual anchor, with graph-native conjugation, pronunciation, and examples.
- **Personal learning:** Save words, senses, forms, expressions, grammar, and
  sentences; organize them in collections; browse a Vocabulary Library; and use
  the lightweight Today’s Review loop.
- **Optional AI Learning Layer:** Clearly labelled drafts and translations are
  cached in a separate browser database, so local graph facts stay trustworthy.

## Getting started

For local graph-only development, serve the files with any static web server. Do not open `index.html` directly with `file://`: the graph is split into fetchable data shards and must be served over HTTP. For example, with Python installed:

```bash
python -m http.server 4182
```

Then visit `http://127.0.0.1:4182/`.

### Test a generated data release

The Language Graph is a generated release artifact and is intentionally not tracked in Git.
Build or obtain a verified local release before serving the app. The generated SQLite
database, browser graph package, and reports are excluded because of their size; a
verified release can be provided separately if required. A local A1–C2 release is
kept outside Git under `releases/`. When that local release is available, the app
automatically prefers the complete package. To pin it explicitly, use:

```text
http://127.0.0.1:4182/?graphRoot=releases/liens-c1-c2/browser
```

The query setting changes only the read-only local graph package; it does not
change the application code or the canonical source database. See
[data/wordbank/README.md](data/wordbank/README.md) for the rebuild inputs and
[docs/ARCHITECTURE_FREEZE_V1.md](docs/ARCHITECTURE_FREEZE_V1.md) for the artifact policy.

## How to test

With a local graph release available, try these small journeys:

1. Search **être**, then open **sommes** from its conjugation table to see a form
   as its own object and return through native Back/Forward navigation.
2. Search **tuer** to inspect senses, pronunciation provenance, examples, and
   related learning resources.
3. Search **Je vais au cinéma ce soir.** to see local token, form, contraction,
   expression, and grammar matching around *futur proche*.
4. Open **Vocabulary**, select a CEFR level and a part of speech, then open a
   word from the frequency-first learning path.
5. Save a word or sentence, open **Notebook**, and enter **Today’s Review**.

## Gemini development assistance

Liens can optionally generate clearly labelled, non-canonical Learning Resource drafts through Gemini. The API key stays in your shell environment; it is never added to browser code or Git.

```bash
export GEMINI_API_KEY='your-key'
python3 dev_server.py --port 4173
```

Open `http://127.0.0.1:4173`, enable **AI learning assistance** in Settings, then use an in-place learning action when Liens has no local teaching note. `GEMINI_MODEL` is optional and defaults to `gemini-3.5-flash`.

This local server is for rapid development only. A backend or edge proxy replaces it before deployment.

## Local pronunciation playback

IPA and audio references live in the Language Object graph. The playback layer is separate from that metadata: it first uses a local cached recording when `local_audio_path` is present, otherwise the browser's local `SpeechSynthesis` provider speaks the object's canonical French form. Neither path uses a server, cloud API, or AI service. Later local-TTS providers can be added without changing the button or pronunciation metadata.

## OpenAI technologies used

**Codex + GPT-5.6 accelerated the build.** Liens was developed iteratively with
Codex using GPT-5.6 for product and graph-architecture decisions, implementation,
schema and importer design, refactoring, debugging, interactive QA, UI iteration,
and the project’s architecture/product handbook. The detailed design history is
preserved in the Liens Book.

**Runtime AI is provider-independent.** The current development adapter uses
Gemini for optional Learning Resource generation: sentence explanations,
translations, usage notes, examples, comparisons, and memory tips. This is
deliberate: GPT-5.6 powered the core development workflow, while the application
keeps a typed provider boundary so OpenAI or another model can be added without
changing the UI or canonical graph. Liens does not currently send runtime user
requests to a GPT-5.6 API; it does not claim that it does.

## Build Week contributions

During Build Week, Liens evolved from a small French-learning prototype into a
local-first learning platform:

- designed a source-independent, provenance-backed Language Graph and deterministic build pipeline;
- expanded the graph through A1–C2 lexical coverage, morphology, senses,
  expressions, examples, grammar, and pronunciation representations;
- built Sentence Intelligence for local word/form/expression/grammar matching;
- added the separate AI Learning Database with revisions, provenance, caching,
  and canonical-replacement rules;
- added Personal Learning Objects, collections, the Vocabulary Library, and the
  first lightweight review loop;
- refined Apple-inspired navigation, exploration-oriented word/sense pages, and
  browser performance; and
- produced the living Architecture & Product Manual documenting the product’s
  decision history and runtime flows.

## Data sources

Canonical linguistic data is imported reproducibly from pinned, attributable
releases. The primary sources include **FLELex / Beacco** (CEFR and frequency),
**Lexique 3.83** (morphology, phonological code, syllabification), **Morphalou
3.1** (simple verb paradigms), **Kaikki / Wiktionary-derived releases** (senses,
examples, expressions, lexical relations, IPA, and audio metadata), and curated
grammar material where available. Source records and evidence remain attached to
facts and relationships.

AI-generated explanations are Learning Resources stored separately in browser
IndexedDB. They never create or modify canonical objects, facts, or relationships;
source-backed content takes precedence when it becomes available.

## Project documentation

The complete product and architecture handbook is [**LIENS_BOOK.md**](docs/LIENS_BOOK.md).
It explains the product philosophy, canonical model, runtime flows, design
rationale, and evolution of Liens. Supporting technical documentation is in
[docs/](docs/README.md).

## Current status

This runnable local prototype demonstrates the core loop: **Learn → Explore → Save → Review**. It uses a SQLite Language Object Graph as the linguistic source of truth, a generated browser index for static local lookup, deterministic Sentence Intelligence, graph-native conjugation, and graph-native pronunciation. Gemini can add structured, labelled Learning Resource drafts through the local development server; it never replaces local facts or becomes a visible chatbot.
