# Liens — French learning in context

Liens is a French-learning app I built because I wanted a better way to learn French myself.: by following connections between words, forms, grammar, examples, and sentences instead of treating each as a separate lookup.

## Project overview

While learning French, I kept hitting the same friction: a dictionary tells me
what a word means, a conjugator shows a form, a grammar page explains a rule,
and an AI chat helps with a sentence—but none of them remembers the context or
connects the pieces. Liens is my attempt to make that experience feel continuous.

It is local-first and built around an explorable Language Graph. A word can lead
to its forms, senses, pronunciation, grammar, expressions, examples, and related
sentences. A sentence is not a dead end; it is another way into the same network.
The graph holds evidence-backed linguistic knowledge. AI can help when a teaching
note is missing, but its output is labelled, cached separately, and never quietly
rewrites the graph.

## Key features

- **Local Language Graph:** A1–C2 words, forms, senses, expressions, grammar,
  pronunciation, and examples are connected, so exploration does not stop at a
  single definition.
- **Search that understands forms:** Accent-insensitive lookup resolves lemmas,
  inflected forms, and multi-word expressions to their canonical objects.
- **Sentence Intelligence:** Deterministic local analysis identifies tokens,
  known forms, expressions, and grammar before optional teaching enrichment.
- **Learning in context:** Word and sentence pages keep the current object in
  view, with conjugation, pronunciation, and examples close at hand.
- **Personal learning:** Save words, senses, forms, expressions, grammar, and
  sentences; organize them in collections; browse a Vocabulary Library; and use
  the lightweight Today’s Review loop.
- **Optional AI Learning Layer:** When the graph lacks a teaching note, Liens can
  add a clearly labelled draft and cache it locally—without blurring the line
  between generated help and sourced facts.

## Getting started

For local graph-only development, serve the files with any static web server. Do not open `index.html` directly with `file://`: the graph is split into fetchable data shards and must be served over HTTP. For example, with Python installed:

```bash
python -m http.server 4182
```

Then visit `http://127.0.0.1:4182/`.

### Test a generated data release

The Language Graph is a generated release artifact and is intentionally not tracked in Git.
Build or obtain a verified local release before serving the app. The generated SQLite
database, browser graph package, and reports are excluded because they are large;
a verified release can be provided separately if required. A local A1–C2 release is
kept outside Git under `releases/`. When it is available, the app
automatically prefers the complete package. To pin it explicitly, use:

```text
http://127.0.0.1:4182/?graphRoot=releases/liens-c1-c2/browser
```

The query setting changes only the read-only local graph package; it does not
change the application code or the canonical source database. See
[data/wordbank/README.md](data/wordbank/README.md) for the rebuild inputs and
[docs/ARCHITECTURE_FREEZE_V1.md](docs/ARCHITECTURE_FREEZE_V1.md) for the artifact policy.

## How to test

With a local graph release available, these are good ways to get a feel for it:

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

Liens can optionally generate clearly labelled, non-canonical learning drafts through Gemini. The API key stays in your shell environment; it is never added to browser code or Git.

```bash
export GEMINI_API_KEY='your-key'
python3 dev_server.py --port 4173
```

Open `http://127.0.0.1:4173`, enable **AI learning assistance** in Settings, then use an in-place learning action when Liens has no local teaching note. `GEMINI_MODEL` is optional and defaults to `gemini-3.5-flash`.

This local server is for rapid development only. A backend or edge proxy replaces it before deployment.

## Local pronunciation playback

IPA and audio references live in the Language Graph, while playback is deliberately
separate. Liens first uses a local cached recording when `local_audio_path` is
present; otherwise, the browser's `SpeechSynthesis` speaks the canonical French
form. This keeps “the app can say it” separate from “the app has verified
pronunciation data.” Neither path needs a server, cloud API, or AI service.

## OpenAI technologies used

**Codex + GPT-5.6 accelerated the build.** I used Codex with GPT-5.6 throughout
the project: to test product ideas, work through the graph architecture, implement
and refactor the app, design importers and schemas, debug, run QA passes, improve
the UI, and document the decisions. The Liens Book keeps that design history.

**Runtime AI is provider-independent.** The current development adapter uses
Gemini for optional sentence explanations, translations, usage notes, examples,
comparisons, and memory tips. GPT-5.6 was central to building Liens, but the app
does not currently send user requests to a GPT-5.6 API. I kept the provider
boundary typed and narrow so an OpenAI or local provider can be added later
without changing the UI or the canonical graph.

## Build Week contributions

During Build Week, Liens grew from a small French-learning prototype into a
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

Canonical linguistic data comes from pinned, attributable releases, so the graph
can be rebuilt and checked rather than hand-maintained. The primary sources include **FLELex / Beacco** (CEFR and frequency),
**Lexique 3.83** (morphology, phonological code, syllabification), **Morphalou
3.1** (simple verb paradigms), **Kaikki / Wiktionary-derived releases** (senses,
examples, expressions, lexical relations, IPA, and audio metadata), and curated
grammar material where available. Source records and evidence remain attached to
facts and relationships.

AI-generated explanations live separately in browser IndexedDB. They never create
or modify canonical objects, facts, or relationships; sourced content wins when
it becomes available.

## Project documentation

For the full story, see [**LIENS_BOOK.md**](docs/LIENS_BOOK.md): the product
philosophy, data model, runtime flows, design rationale, and evolution of Liens.
Supporting technical documentation is in [docs/](docs/README.md).

## Current status

This runnable local prototype demonstrates the core loop: **Learn → Explore → Save → Review**. It uses a SQLite Language Graph for local lookup, deterministic Sentence Intelligence, graph-native conjugation and pronunciation, and a separate AI Learning Layer. Gemini can add structured, labelled drafts through the local development server; it never replaces local facts or turns Liens into a chatbot.
