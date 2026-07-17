# AI Learning Assistance

## Purpose

AI Learning Assistance fills missing *teaching content* without changing the canonical Language Graph. It is an in-place learning layer, not a chatbot and not an importer.

The browser may use it for a contextual explanation, usage note, sentence guide, or provisional unknown-lookup note. It never creates a canonical Language Object, Fact, Evidence record, relationship, search entry, or browser graph export.

## Boundary

```text
canonical graph object / deterministic sentence analysis
→ contextual Learning Resource request
→ optional AI provider
→ learner-scoped AI draft cache
→ in-place, labelled learning note

reviewed source or editorial workflow
→ normal canonical import / published learning-resource revision
```

An AI draft is not a weaker canonical fact. It is a different class of content entirely.

## Browser contract

`ai-learning.js` exposes `window.LiensLearningAssist`. It has no provider, key, endpoint, or network dependency of its own. A future secure integration supplies `window.LiensAIProvider` with:

```js
{
  id: 'provider-id',
  generate: async request => ({ title, body, provider })
}
```

The request is deliberately narrow:

- target display metadata and canonical ID, if a target exists;
- resource kind: `explanation`, `usage_note`, `sentence_guide`, or `provisional_lookup`;
- a bounded graph summary and optional sentence context;
- a constraint that canonical graph writes and relationship/object creation are prohibited.

The returned text is validated as bounded plain-text learning content. It is stored only in browser local storage under a learner-scoped draft key. It is never inserted into SQLite or `wordbank-index.json`.

## UX contract

AI appears only in existing learning-content spaces:

- a meaning lacking an explanation;
- a word/form lacking a contextual learning note;
- a recognised grammar object lacking a teacher guide;
- a sentence with locally unresolved material;
- an unknown single-item lookup.

When no provider is connected, no AI prompt is shown on the learning page. Settings states this honestly. When a draft exists, it appears in place with `AI-generated` and `Learning draft` labels plus `Not yet verified in Liens.` It must never replace the page anchor or open a chat surface.

Generation is opt-in through the learner's AI-assistance preference. The static application does not ship a secret, call a cloud service, or transmit learner text by default.

## Replacement policy

Source-backed and reviewed Learning Resources are the default whenever available. An AI draft is a fallback only. A future reviewed or source-backed resource uses the same contextual slot and replaces the draft in normal rendering; the draft remains provenance history, not canonical graph data.

AI-suggested collocations, examples, translations, and grammar connections remain learning drafts. They are not graph objects, canonical facts, sentence objects, or typed relationships until a separate reviewed source/import workflow promotes them.

## Production requirements before live use

- secure provider/credential transport; a static browser must never contain a shared provider secret;
- immutable generation-run provenance: provider, model/version, prompt/template version, context/input/output hashes, timestamp, and evaluation status;
- learner privacy, consent, retention, and deletion policy;
- moderation, output schema validation, error handling, and rate/cost controls;
- a review/promotion workflow for content that should later become source-backed or curated;
- migration away from the legacy `ai_generated_content` table rather than expanding it as the long-term authority.
