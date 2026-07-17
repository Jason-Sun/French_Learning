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

## Hackathon status

This runnable prototype demonstrates the core product loop: Learn → Explore → Save → Review. The next implementation increment adds a server-side GPT-5.6 analysis layer for arbitrary French input while keeping structured lexical facts and API credentials outside the browser.

## Built with Codex and GPT-5.6

Codex was used to turn the product architecture into the runnable interaction model, connected learning object UI, navigation history, and local review state. GPT-5.6 will be used server-side as an invisible explanation engine: it will return structured, teacher-style context for an input sentence, rather than behave as a visible chatbot.
