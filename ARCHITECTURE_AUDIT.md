# Liens architecture audit — 2026-07

This audit reviews the system as a durable, local-first Language Object graph rather than as a collection of feature pages.

## Strengths retained

- A stable `language_objects` identity layer and typed `relationships` support direct exploration across words, forms, grammar, expressions, conjugation, and learning resources.
- Search normalizes case and French diacritics while preserving canonical French spelling for display.
- Sentence Intelligence resolves existing graph objects first; it creates analysis-specific data rather than silently promoting unreviewed knowledge.
- Conjugation learning groups, tenses, realizations, and teacher guidance are graph data. The browser does not contain a list of French conjugations.
- English remains required, Chinese remains a presentation preference, and provenance distinguishes reviewed material from drafts.

## Weaknesses found and resolved

| Finding | Resolution |
| --- | --- |
| Pronunciation was structured but lived beside the graph as `pronunciations` rows. | Each record is now materialized as a `pronunciation` Language Object with a `has_pronunciation` edge. |
| IPA could be exported without a traversable object identity. | `pronunciation_object_details` owns the data and the browser export includes the node plus a compatible owner adapter. |
| Core forms had no independent pronunciation coverage. | 56 existing forms across eight core verbs now have their own reviewed IPA records. Lemma IPA is never copied as a fallback. |
| Browser playback named concrete mechanisms directly. | The page calls `playPronunciation(LanguageObject)`; the provider chain is local recording → cached local TTS → browser synthesis. |

## Contracts after the refactor

1. A Pronunciation Object is a Language Object of type `pronunciation`.
2. Pronunciation metadata belongs in `pronunciation_object_details`, not in UI state or a lemma field.
3. An owner reaches it only through `has_pronunciation`; any page, sentence token, conjugation row, or expression can reuse that edge.
4. `pronunciations` and `language_objects.ipa` are compatibility/import boundaries. The additive synchronizer preserves them and materializes graph nodes.
5. Draft or AI-generated pronunciation must create a new Pronunciation Object with draft provenance/review status. It must never overwrite a curated object.
6. Remote audio is not a current provider. Audio paths are metadata, and the UI remains independent of how audio is supplied.

## Remaining deliberate boundaries

- The static demo exports a denormalized browser index for fast loading. SQLite remains the source of truth; the exporter is the sole adapter boundary.
- Search indexes every learnable browser object, but product routing intentionally prefers words/forms/expressions over implementation-only pronunciation objects.
- Sentence analyses are ephemeral and reference canonical Language Objects. They do not create permanent graph knowledge until reviewed.
- Learner saves are local browser state in this prototype. A future account sync layer should write review state keyed by `language_object.id`, not copy object content.

## Next architectural rule

Future features—audio caching, pronunciation lessons, AI drafts, listening exercises, or account synchronization—must attach typed data and relationships to existing Language Objects. They should not add UI-owned sources of truth.
