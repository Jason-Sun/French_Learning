# Sentence Intelligence

## Responsibility

Produce a deterministic, evidence-linked local analysis of a learner sentence using the exported Language Object Graph.

## Current interface

Input: source sentence and optional saved object IDs.  
Output: tokens, resolved object/lemma IDs, analysis nodes, typed edges, recognized expressions, grammar nodes, unknown tokens, learning candidates, provenance, confidence, and transient cache status.

## Canonical boundary

An analysis may resolve spans to canonical UUIDs through `sentence_analysis_object_matches`, including contraction components and overlapping multi-word objects. It remains a per-input, non-canonical record. Deterministic and future AI-assisted analysis may link a Learning Resource revision for learner-facing guidance, but cannot create or overwrite canonical Language Objects, Facts, Evidence, or relationships.

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
