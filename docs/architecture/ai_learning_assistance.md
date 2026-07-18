# AI Learning Assistance

## Purpose

AI Learning Assistance fills missing *teaching content* without changing the canonical Language Graph. It is an in-place learning layer, not a chatbot and not an importer.

The browser may use it for a contextual explanation, usage note, memory tip, comparison, common-mistake note, examples, sentence guide, or provisional unknown-lookup note. It never creates a canonical Language Object, Fact, Evidence record, relationship, search entry, or browser graph export.

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

`ai-learning.js` exposes `window.LiensLearningAssist`. It has no provider, key, endpoint, or network dependency of its own. It dispatches each typed resource request to an injected `window.LiensAIProvider` method:

```js
{
  id: 'provider-id',
  generateLearningResource: async resource => ({ title, body, provider }),
  generateUsageNote: async resource => ({ title, body, provider }),
  generateMemoryTip: async resource => ({ title, body, provider }),
  generateExamples: async resource => ({ title, body, provider }),
  generateComparison: async resource => ({ title, body, provider }),
  generateCommonMistake: async resource => ({ title, body, provider }),
  explainGrammar: async resource => ({ title, body, provider }),
  explainSentence: async resource => ({ title, body, provider })
}
```

The rest of Liens does not construct prompts or call a generic `generate(prompt)` method. It requests a Learning Resource for a Language Object or sentence context. A provider is responsible for translating that typed request into its own API call and prompt policy.

### Gemini development adapter

The first adapter is `gemini-provider.js` plus `dev_server.py`. The browser adapter forwards typed Learning Resource requests to a same-origin local endpoint. `dev_server.py` reads `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) from the development environment, constructs Gemini-specific prompts server-side, and uses Gemini structured JSON output. The API key is never embedded in browser assets or committed to Git.

This is deliberate development infrastructure only. A future OpenAI, Claude, OpenRouter, or local-model provider implements the same typed methods; the UI, Learning Layer, and canonical graph do not change.

The request is deliberately narrow:

- target display metadata and canonical ID, if a target exists;
- resource kind: `explanation`, `usage_note`, `memory_tip`, `examples`, `comparison`, `common_mistake`, `sentence_guide`, or `provisional_lookup`;
- a bounded graph summary and optional sentence context;
- a constraint that canonical graph writes and relationship/object creation are prohibited.

The returned text is validated as bounded plain-text learning content. It is stored only in browser local storage under a learner-scoped draft key. It is never inserted into SQLite or the generated browser data package.

## UX contract

AI appears only in existing learning-content spaces:

- a meaning lacking an explanation;
- a word/form lacking a contextual learning note;
- a recognised grammar object lacking a teacher guide;
- a sentence after deterministic local analysis, including actions for the sentence, a matched grammar object, a matched form, and another example;
- an unknown single-item lookup.

Generation is always explicit. Liens never requests a draft merely because a learner opened a known object or sentence. A missing learning-content slot is a calm invitation such as `Generate explanation`; an unknown lookup offers `Create a provisional learning note`. When no provider is connected, the invitation remains an honest local-content state and exposes no broken cloud action.

The first generated note is compact. It is cached locally, labelled `AI-generated` and `Learning draft` (or `Provisional learning note`), and does not behave like a conversation. The learner can then choose progressive follow-ups—examples, memory tips, comparisons, or a common mistake—inside that same contextual surface. It must never replace the page anchor or open a chat surface.

Generation is opt-in through the learner's AI-assistance preference. The static application does not ship a secret, call a cloud service, or transmit learner text by default.

## Local cache and future revisions

Browser drafts are keyed by the target/sentence context, resource kind, and language. The active draft is the newest local revision; earlier generated revisions are retained in local storage rather than destructively replaced. A normal request returns the cached draft. The module already supports an explicit regeneration flag for a future `Regenerate` control, and exposes revision retrieval for a future `View previous revisions` control. Neither control is part of the current calm learning UI.

A reviewed or source-backed Learning Resource remains the preferred rendering for a slot. Replacing an AI draft with curated content therefore requires no object, route, or page redesign: the surrounding contextual surface stays the same while its resource provenance changes.

## Replacement policy

Source-backed and reviewed Learning Resources are the default whenever available. An AI draft is a fallback only. A future reviewed or source-backed resource uses the same contextual slot and replaces the draft in normal rendering; the draft remains provenance history, not canonical graph data.

AI-suggested collocations, examples, translations, and grammar connections remain learning drafts. They are not graph objects, canonical facts, sentence objects, or typed relationships until a separate reviewed source/import workflow promotes them.

## Production requirements before live use

- replace the Gemini development server with secure provider/credential transport before deployment; a static browser must never contain a shared provider secret;
- immutable generation-run provenance: provider, model/version, prompt/template version, context/input/output hashes, timestamp, and evaluation status;
- learner privacy, consent, retention, and deletion policy;
- moderation, output schema validation, error handling, and rate/cost controls;
- a review/promotion workflow for content that should later become source-backed or curated;
- migration away from the legacy `ai_generated_content` table rather than expanding it as the long-term authority.
