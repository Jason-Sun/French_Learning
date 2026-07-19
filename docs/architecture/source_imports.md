# Source and Import Layer

## Responsibility

Make lexical resources interchangeable importers rather than defining the Language Graph around any one dataset.

## Pipeline

```text
source catalog → frozen release → source records → import run
      → record mapping / explicit exclusion → canonical objects and facts
      → fact evidence → browser export
```

`source_catalogs` stores provider and licence policy. `source_releases` freezes a version, artifact location, checksum, and scope. `source_records` preserves a source-native key. `import_runs` records reproducibility. Each eligible record must be mapped to a canonical object or receive an explicit exclusion reason. Canonical facts use `fact_evidence`; new canonical relationships use `relationship_evidence`.

## Identity contract

Importers do not generate object identities. They submit a source-independent identity key to the canonical identity registry, which resolves an existing canonical UUID or creates it through the core canonical workflow. A source replacement therefore maps to existing canonical IDs rather than invalidating learner data or links.

## Fact and evidence contract

Canonical facts are atomic claims with typed values. Source records support those facts through `fact_evidence`. Multiple releases may support or disagree with the same predicate without changing the object identity. Importers must not write undocumented source assumptions into canonical object fields.

## Acceptance contract

Coverage targets come from a frozen source release, never hard-coded application counts. A successful import has complete eligible-record accounting, no duplicate canonical identities, valid evidence, zero orphaned references, and reproducible run metadata.

## FLELex / Beacco lexical baseline

The production provenance import uses the official TreeTagger / Beacco TSV artifact. Its URL and SHA-256 are frozen in level-scoped manifests; the A1–B2 baseline manifest is `data/wordbank/import-manifests/flelex-beacco-tree-tagger-a1-b2.json`. The raw artifact is downloaded at import time rather than treated as Liens-authored data. The adapter maps source rows through canonical identity keys and never mints Language Object UUIDs.

Each selection is defined by the manifest’s explicit `level` or `levels` list. Its report accounts for every selected row by level as a canonical mapping or explicit exclusion, and evidences the source-supported part of speech, CEFR level, and total frequency facts independently. A multi-level import is one reproducible source release run, not a new identity system.

The canonical lexical-baseline adapter is the one importer allowed to create a new `word` Language Object from FLELex. It derives the source-independent identity `fr|word|POS|normalized lemma`, mints its UUID from that identity, and records three independently evidenced Facts: part of speech, CEFR level, and frequency per million. All other importers resolve that identity; they may not create a fallback word merely because a source mentions one.

The prepared C1/C2 manifest selects 3,155 C1 and 2,314 C2 FLELex rows from the same hash-locked TreeTagger / Beacco release. The generated SQLite and browser package are intentionally not committed by this preparation step; a release build must apply the manifest, run the scope audit, export a package, and publish the generated artifacts outside ordinary Git history. The matching C1/C2 Kaikki and Lexique manifests enrich this same baseline with senses, examples, lexical relations, expressions, morphology, and source-specific pronunciation representations; they never create a fallback lexical identity.

`scripts/build_c1_c2_release.py` is the first end-to-end implementation of that contract. It accepts verified local copies of the FLELex, Kaikki, Lexique, and Morphalou artifacts, writes only to a new external release directory, applies the pinned manifests and deterministic verb derivations, then emits the graph, browser package, individual reports, and a release manifest with artifact checksums. It intentionally does not fetch a mutable upstream URL during a release build.

## Lexique 3.83 CEFR-scoped morphology and pronunciation baseline

Lexique 3.83 supplies source-backed inflected surfaces, lemmas, verb features, gender, number, a Lexique-specific phonological code, and syllabification. Its phonological code is a source representation, not verified IPA.

The morphology and pronunciation adapters select an explicit CEFR-level scope from their manifests and import validated verb, noun, adjective, and function-word analyses. The completed A1 Golden Slice is the reference scope; the same importer contract is parameterized for A2–B2 expansion. For pronouns, articles, and possessive determiners, the adapter adds only gender/number facts asserted for an existing canonical object. Lexique does not establish paradigm links between variants such as `mon` and `ma`, so the importer never manufactures a form relationship from its rows alone.

The production A1–B2 verb morphology import uses the same hash-locked release and the manifest `lexique383-a1-b2-morphology.json`. It records 42,042 source analyses, with four conflicting source rows retained as explicit exclusions. The report is a coverage record, not a claim that every possible French form has been imported.

Every Lexique-created `inflected_form_of` edge has direct row-level relationship evidence. A `member_of_paradigm` edge is a transparent graph derivation from that evidenced form link and an existing verb-paradigm link, so it retains the same source record with `evidence_role = derived_from_asserted_form`; it is never presented as a direct Lexique assertion.

The pronunciation adapter reuses the same immutable source-row identity and attaches two representations to each mapped Language Object: `phonological_code` with `transcription_system = lexique383`, and structured `syllabification`. A deterministic, versioned conversion may also create a clearly labelled non-canonical fallback IPA (`lexique383_derived_ipa_v1`); it is superseded whenever Kaikki supplies source-backed IPA.

Each Lexique `has_pronunciation` edge is evidenced by the same source row that evidences its representations. The graph link is therefore attributable without treating the source phonological code as IPA.

## Kaikki / English Wiktionary pronunciation representations

The pinned Kaikki French release supplies source-backed IPA, regional/dialect and note metadata, and audio URLs. `scripts/import_kaikki_pronunciations.py` maps those records onto the existing source-independent Pronunciation Object for both matched lemmas and matched inflected forms. IPA is stored as a canonical `ipa` representation with row-level evidence; audio URLs are stored as `audio_url` metadata only and do not enable playback. Lexique representations remain untouched on the same object.

The pronunciation report accounts for every eligible source row as a mapped target or an explicit exclusion. Rows that conflict with another lexical identity or lack the features required to create a canonical form remain in `import_exclusions`; they are never silently discarded.

## Morphalou 3.1 complete morphology

Morphalou 3.1 is the complete-paradigm morphology source for Liens' existing
CEFR-scoped verbs. It is distributed under LGPL-LR and records 159,271 lemmas
and 976,570 French inflected forms. The importer accepts only an exact,
normalized Morphalou verb lemma that already resolves to a FLELex word/POS
identity in the selected A1–C2 scope. Therefore it contributes neither new CEFR
classifications nor fallback words.

Every accepted Morphalou form is an `inflected_form` Language Object (or adds
new evidence to the same existing canonical form), with source-backed mood,
tense, person, number, and gender facts. Its `inflected_form_of` relationship
has direct row-level evidence. The source’s full simple paradigms then flow
through the existing deterministic tense-paradigm projection. Unsupported or
unmatched source rows are reported explicitly; no rule-based or LLM-generated
conjugation is substituted for them.

## Kaikki / English Wiktionary lexical-sense baseline

Kaikki's French dictionary is a structured extraction from English Wiktionary. Its frozen releases and CEFR-scoped manifests carry the upstream CC BY-SA/GFDL attribution obligations. It is used for English glosses, not as a CEFR classifier.

The adapter selects explicit CEFR levels from its manifest and matches a source entry only when its French headword and mapped part of speech identify an existing FLELex word in that scope. Each source sense becomes a `lexical_sense` object with a source-neutral semantic key derived from its normalized English gloss set. The source-native sense ID remains solely an immutable source-record mapping. Every English gloss is an `english_gloss` fact with independent evidence; words not present in the frozen source are reported, not fabricated.

When FLELex and Kaikki classify the same French surface differently, a manifest may contain an explicit reviewed POS reconciliation. It names the source POS, target POS, and surface; the import records `mapping_kind = reviewed_pos_reconciliation`. This supplements exact source matches without changing either source representation or canonical object identity. It is a reviewable data decision, never a hidden fallback.

The `has_sense` edge is also source-evidenced from the exact source sense record. A source-backed sense therefore retains both the relationship to its word and the evidence for its English glosses independently.

## Complementary French Wiktionary definition baseline

`Kartmaan/french-dictionary` is a pinned, CC BY-SA 4.0 French
Wiktionary/WiktionaryX-derived release. It supplements the Kaikki extraction
only where an A1–B2 word/POS identity has no existing source-backed sense. Its
facts are `french_definition` values in language `fr`; they are not represented
as English glosses, translations, or AI output.

The adapter accepts only exact normalized source-surface and POS mappings.
Source POS differences, inflected-form analyses, and spelling variants remain
explicit gaps unless a future manifest contains a separately reviewed,
evidence-preserving reconciliation. This keeps source taxonomy intact and
prevents a coverage percentage from introducing an incorrect canonical sense.

The same frozen release supplies short, translated examples and explicit synonym/antonym relations. The importer accepts only extracted `example` records with an English translation and bounded sentence length. Each sentence is independent, retains a source-record alignment to the illustrated sense, and contributes an evidenced `illustrates` edge. A manifest may widen only the *relation-target* scope, allowing (for example) a C1 word to point to an existing A1–C2 synonym; the relation owner remains in the selected import scope. Phrase entries are not automatically relabelled as collocations unless a future source explicitly provides that classification.

The connections importer resolves source-sense records through their canonical lexical-sense targets rather than assuming a particular CEFR import-run name. This keeps A1 and A2–B2 source mappings compatible under one reproducible contract.

## Kaikki / English Wiktionary A1-connected expression baseline

The same hash-locked Kaikki release supplies source entries whose native part of speech is `phrase`. The expression adapter accepts a phrase only when it has an English gloss and every lexical token resolves locally to either a configured-scope lemma or a source-backed inflected form of one. The source phrase selection and the component-resolution scope are independently configurable: a C1/C2 phrase may correctly contain known A1 function words such as *de* or *à*. This is a graph-connectivity rule, **not** a CEFR claim for the phrase itself.

Each accepted record becomes a first-class `expression` object using a source-independent surface identity. Its English translations are independently evidenced facts. Ordered components are stored in `multiword_components`, their source surfaces in `multiword_component_evidence`, and deduplicated `contains` edges carry independent relationship evidence for graph traversal. The importer does not call any Kaikki phrase an idiom or collocation: the source’s `phrase` label alone does not establish either classification.

## Tex A1 grammar baseline

Tex's French Grammar is a CC-BY educational grammar published by COERLL. Its frozen grammar-index artifact supplies a reviewed, bounded A1 topology: grammar topics, indexed constructions, and directly named components. The importer creates first-class Grammar Objects and records evidence for every new topic, component, and relationship. It does not import unbounded prose explanations as canonical facts.
