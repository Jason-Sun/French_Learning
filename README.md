# Liens — French learning in context

Liens is a learning-first French web app. It treats words, forms, collocations, and sentences as connected learning objects rather than separate dictionary entries or chat messages.

## Run locally

This first demo is dependency-free. From this folder, serve the files with any static web server, then open `index.html` in a browser. For example, with Python installed:

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000`.

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

This runnable local prototype demonstrates the core loop: **Learn → Explore → Save → Review**. It uses a SQLite Language Object Graph as the linguistic source of truth, a generated browser index for static local lookup, deterministic Sentence Intelligence, graph-native conjugation, and graph-native pronunciation. AI enrichment is intentionally not connected yet; when introduced, it will add structured draft knowledge rather than replace local facts or become a visible chatbot.
