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

This runnable prototype demonstrates the core product loop: Learn → Explore → Save → Review, plus a first local Sentence Intelligence workflow. Multi-word input is analyzed in the browser against the exported Language Object Graph: known forms, expressions, grammar signals, graph relationships, and learning opportunities are rendered without an AI or API call.

## Local sentence exploration

Serve the project as a static site, then enter a sentence such as `Je suis allé à Paris.` or `Il a besoin de temps.` The browser-side Sentence Intelligence adapter produces an analysis instance from the local graph and keeps every recognized word, expression, and grammar object clickable.

## Built with Codex and GPT-5.6

Codex was used to turn the product architecture into the runnable interaction model, connected learning object UI, navigation history, and local review state. GPT-5.6 will be used server-side as an invisible explanation engine: it will return structured, teacher-style context for an input sentence, rather than behave as a visible chatbot.
