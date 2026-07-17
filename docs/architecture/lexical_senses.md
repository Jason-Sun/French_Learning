# Lexical Senses

## Responsibility

Represent individual meanings as canonical, explorable Language Objects rather than as an anonymous list of text on a word.

## Ownership

```text
word Language Object
  → has_sense
  → lexical_sense Language Object
       → predicate fact (english_gloss)
       → source evidence
```

`lexical_senses` connects each sense object to its owner word's canonical UUID, part of speech, source-neutral semantic key, and display order. The owner word retains its lexical identity; a sense owns only a distinguishable meaning. The `has_sense` relationship makes both directions navigable.

## Identity and provenance

The canonical identity resolver creates a sense UUID from its owner UUID, part of speech, and a normalized semantic key. An importer maps its own immutable source record to that UUID through `import_record_mappings`; it does not make a source record identifier the permanent identity. Future sources may support the same sense with new evidence or a conflicting sense with a distinct semantic key.

`english_gloss` is a predicate-based text fact on the sense object. Every imported gloss has its own `fact_evidence` record. The legacy `object_definitions` table remains a browser-compatibility adapter and is not the canonical store for imported senses.

## Browser contract

The browser export projects ordered sense links onto a word and exports the sense objects themselves. A page can therefore show several meanings while preserving direct routes to each sense. The browser may use the first evidenced English gloss for a compact label, but it must not collapse senses back into a single canonical definition.
