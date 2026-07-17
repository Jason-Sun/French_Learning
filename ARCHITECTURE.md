# Liens architecture

## Sentence Intelligence Layer (SIL)

SIL is a framework-neutral service layer between surface French and the Language Object Graph. It does not make the graph parse sentences: deterministic analysis identifies linguistic evidence first, then maps it to stable graph objects.

```text
surface text → tokenize / expand contractions → resolve local objects
→ recognize multi-word objects → deterministic grammar recognition
→ sentence analysis graph → learning extraction → optional AI explanation
```

`sil/` depends on a small repository interface, not SQLite. `SQLiteKnowledgeRepository` is the current adapter. A browser, mobile, or API adapter can implement the same methods.

## Browser sentence service

`sentence-intelligence.js` is the browser adapter for the v1 deterministic pipeline. It consumes `data/wordbank/wordbank-index.json`, so it makes no API, AI, or server call. Its public interface is:

```js
const engine = new SentenceIntelligence(objects);
const analysis = engine.analyze(sentence, savedObjectIds);
```

`analysis` contains surface-preserving tokens, local Language Object references, expression and grammar nodes, graph edges, unknown tokens, and learning metadata. `app.js` only routes queries and renders this result; no linguistic rules live in the UI.

Every analysis is an instance, not permanent graph knowledge. It has a stable input-derived ID, engine version, provenance, confidence, and cache status. Its nodes reference stable Language Objects; only reviewed reusable knowledge belongs in the global graph.

## v1 scope

The first deterministic milestone supports local lexical/form resolution, contractions, graph-backed expressions, passé composé, futur proche, negation, reflexive signals, simple subordinate-clause signals, and learning-object extraction. AI is intentionally absent from the engine; a future adapter may enrich only unresolved explanations through the persisted `ai_generated_content` boundary.
