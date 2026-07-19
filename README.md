# Liens — French learning in context

Liens is a learning-first French web app. It treats words, forms, collocations, and sentences as connected learning objects rather than separate dictionary entries or chat messages.

## Run locally

For local graph-only development, serve the files with any static web server. Do not open `index.html` directly with `file://`: the graph is split into fetchable data shards and must be served over HTTP. For example, with Python installed:

```bash
python -m http.server 4182
```

Then visit `http://127.0.0.1:4182/`.

### Test a generated data release

The checked-in browser graph is the portable A1–B2 development package. A generated C1/C2
release is kept outside Git under `releases/`. When that local release is available, the
app automatically prefers the complete A1–C2 package. To pin it explicitly, use:

```text
http://127.0.0.1:4182/?graphRoot=releases/liens-c1-c2/browser
```

The query setting changes only the read-only local graph package; it does not
change the application code or the canonical source database.

## Gemini development assistance

Liens can optionally generate clearly labelled, non-canonical Learning Resource drafts through Gemini. The API key stays in your shell environment; it is never added to browser code or Git.

```bash
export GEMINI_API_KEY='your-key'
python3 dev_server.py --port 4173
```

Open `http://127.0.0.1:4173`, enable **AI learning assistance** in Settings, then use an in-place learning action when Liens has no local teaching note. `GEMINI_MODEL` is optional and defaults to `gemini-3.5-flash`.

This local server is for rapid development only. A backend or edge proxy replaces it before deployment.

## Demo path

1. Search **sommes** to see its link to **être**.
2. Open an example, or search **je suis allé à Paris**.
3. Tap a form in the sentence breakdown to explore the word object.
4. Save a word or sentence; open Vocabulary; start a review.

## Local pronunciation playback

IPA and audio references live in the Language Object graph. The playback layer is separate from that metadata: it first uses a local cached recording when `local_audio_path` is present, otherwise the browser's local `SpeechSynthesis` provider speaks the object's canonical French form. Neither path uses a server, cloud API, or AI service. Later local-TTS providers can be added without changing the button or pronunciation metadata.

## Project documentation

The long-term product and engineering source of truth lives in [docs/](docs/README.md). Start with the Product Bible and Architecture Bible before proposing a feature; use Current State for the verified implementation snapshot and the Decision Log for established architectural choices.

## Current status

This runnable local prototype demonstrates the core loop: **Learn → Explore → Save → Review**. It uses a SQLite Language Object Graph as the linguistic source of truth, a generated browser index for static local lookup, deterministic Sentence Intelligence, graph-native conjugation, and graph-native pronunciation. Gemini can add structured, labelled Learning Resource drafts through the local development server; it never replaces local facts or becomes a visible chatbot.
