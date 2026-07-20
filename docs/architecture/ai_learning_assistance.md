# AI Learning Assistance

## Purpose

AI Learning Assistance fills missing *teaching content* without changing the canonical Language Graph. It is an in-place learning layer, not a chatbot and not an importer.

The browser may use it for a contextual explanation, usage note, memory tip, comparison, common-mistake note, examples, sentence guide, or provisional unknown-lookup note. It never creates a canonical Language Object, Fact, Evidence record, relationship, search entry, or browser graph export.

## Boundary

```text
canonical graph object / deterministic sentence analysis
→ contextual Learning Resource request
→ optional AI provider
→ learner-scoped AI Learning Database
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
  generateLearningResource: async resource => ({ title, body, provider, model, prompt_version }),
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

- target display metadata, canonical ID, and exact morphology when the target is an inflected form;
- resource kind: `explanation`, `usage_note`, `memory_tip`, `examples`, `comparison`, `common_mistake`, `sentence_guide`, or `provisional_lookup`;
- a bounded deterministic graph summary and optional sentence context;
- a constraint that canonical graph writes and relationship/object creation are prohibited.

The returned text is validated as bounded plain-text learning content. A sentence request explicitly identifies its matched grammar objects, resolved form analyses, and matched expressions. Providers may explain those supplied matches, but must not infer or name an additional grammar construction. An inflected-form request identifies the exact morphology of the form page; a provider must not merge other homographic analyses into that page. Drafts are never inserted into SQLite or the generated browser data package.

## UX contract

AI appears only in existing learning-content spaces:

- a meaning lacking an explanation;
- a word/form lacking a contextual learning note;
- a recognised grammar object lacking a teacher guide;
- a sentence after deterministic local analysis, including actions for the sentence, a matched grammar object, a matched form, and another example;
- an unknown single-item lookup.

Known-object slots may be completed automatically when online assistance is enabled, because Liens should not leave an otherwise resolved learning page empty. Unknown lookups use a narrower policy: Liens prepares exactly one compact English `provisional_lookup` draft, then stops. It records the query in a local recent-lookup list so the learner can find the cached learning surface again from Home or by searching the same text. It does not automatically create examples, comparisons, memory tips, common-mistake notes, or a reference-language version.

The first generated note is compact. It is cached locally, labelled `AI-generated` and `Learning draft` (or `Provisional learning note`), and does not behave like a conversation. The learner can then explicitly choose progressive follow-ups—examples, memory tips, comparisons, a common mistake, or a reference-language resource—inside that same contextual surface. Each follow-up is a separate resource and provider call. This keeps an unknown lookup useful without paying for maximum content before the learner needs it. AI must never replace the page anchor or open a chat surface.

Generation is controlled by the learner's AI-assistance preference. When enabled, visible primary teaching slots may be completed automatically; progressive follow-ups remain learner-requested. The static application does not ship a secret or transmit learner text when assistance is disabled.

## AI Learning Database and revisions

`ai-learning-store.js` owns a learner-scoped IndexedDB database named `liens-ai-learning`. It has two stores: `learning_resources` and `recent_lookups`. A resource records its resource key, target ID when one exists, normalized unknown-query key when applicable, kind, language, revision number, body/translation, optional structured payload, provider, model, `prompt_version`, timestamp, lifecycle, and bounded generation context. The generic resource model already accommodates future pronunciation notes and explicitly requested AI conjugation resources, although Liens does not yet render an AI-produced conjugation table. It is a durable local learning layer, not a graph database.

Resolution is strict and cost-aware:

```text
canonical source-backed resource
→ active AI Learning Database resource
→ online provider generation
```

### Prebuilt learning packs

Liens may ship a small, versioned prebuilt Learning Pack for high-value learning
slots. A pack is imported once into the same learner-scoped AI Learning Database
and uses the same resource key, language, provenance, lifecycle, and
supersession rules as an online draft. It is not part of SQLite or the browser
graph package.

Each packed record declares its pack ID, AI provider/model, prompt version, and
creation time, and is labelled as an AI-generated learning draft in the UI. A
record normally targets a canonical object; a `sentence_guide` may instead be
identified by its exact sentence context, without inventing a canonical
Sentence Object. An existing active learner resource is never overwritten by a
shipped default. This allows common material to work without an online provider
while preserving the strict order: canonical coverage first, then a local
learning resource, then an online call only when no resource exists.

Browser drafts are keyed by target/sentence context, resource kind, language, and resource-contract version where a stricter analysis contract supersedes earlier output. Sentence-guide identity normalizes case, accents, and cosmetic terminal punctuation, so `Je vais manger` and `Je vais manger.` reuse the same resource. The active draft is the newest local revision; earlier generated revisions remain in the AI Learning Database rather than being destructively replaced. Unknown lookup recents are separately indexed by normalized query with display text and most-recent-opened time. They are learner-local search history, not Language Objects or graph search entries. The former local-storage draft keys are migrated once into IndexedDB when available.

A normal request returns the active stored draft without contacting a provider. `findProvisionalLookup` allows a normalized unknown query to reopen its stored first note even if it originated under an older cache-key version. The provider may expose only its current prompt version; `needsRegeneration(request)` compares that value with the stored `prompt_version`, so a future calm “Regenerate with the latest prompt” action can create a new revision without deleting the earlier output. Prompt text remains exclusively inside the provider implementation. Neither regeneration nor revision-history controls are part of the current UI.

A reviewed or source-backed Learning Resource remains the preferred rendering for a slot. Replacing an AI draft with curated content therefore requires no object, route, or page redesign: the surrounding contextual surface stays the same while its resource provenance changes.

## Replacement policy

Source-backed and reviewed Learning Resources are the default whenever available. An AI draft is a fallback only. When a canonical learning resource occupies the same supported slot, the resolver renders it first and marks matching active AI revisions `superseded` in the AI Learning Database; they remain available as local provenance history rather than being deleted. A future reviewed or source-backed resource therefore replaces a draft without changing the object, route, or page architecture.

AI-suggested collocations, examples, translations, and grammar connections remain learning drafts. They are not graph objects, canonical facts, sentence objects, or typed relationships until a separate reviewed source/import workflow promotes them.

## Production requirements before live use

- replace the Gemini development server with secure provider/credential transport before deployment; a static browser must never contain a shared provider secret;
- immutable generation-run provenance: provider, model/version, prompt/template version, context/input/output hashes, timestamp, and evaluation status;
- learner privacy, consent, retention, and deletion policy;
- moderation, output schema validation, error handling, and rate/cost controls;
- a review/promotion workflow for content that should later become source-backed or curated;
- migration away from the legacy `ai_generated_content` table rather than expanding it as the long-term authority.
