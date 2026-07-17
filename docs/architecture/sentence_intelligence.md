# Sentence Intelligence

## Responsibility

Produce a deterministic, evidence-linked local analysis of a learner sentence using the exported Language Object Graph.

## Current interface

Input: source sentence and optional saved object IDs.  
Output: tokens, resolved object/lemma IDs, analysis nodes, typed edges, recognized expressions, grammar nodes, unknown tokens, learning candidates, provenance, confidence, and transient cache status.

## Current behavior

- Tokenizes French text and handles selected contractions and elisions.
- Resolves exact local forms and lemmas.
- Recognizes locally modeled multi-word expressions.
- Detects supported patterns including passé composé, futur proche, negation, reflexive constructions, and a simple subordinate-clause signal.
- Links grammar nodes to structured teacher guidance when present.

## Non-goals

It does not claim complete French parsing, create canonical knowledge automatically, or use AI to conceal uncertainty. Unknown tokens remain visible for later enrichment or learner exploration.

## Evolution rule

Add deterministic rules only when they can emit stable graph references and useful evidence. AI enrichment must consume and extend this structured result, not replace it with opaque prose.
