# Pronunciation System

## Responsibility

Model pronunciation as reusable linguistic knowledge, independent from page rendering and audio delivery.

## Data contract

An owner Language Object connects to one or more `pronunciation` objects via `has_pronunciation`. A Pronunciation Object can own multiple evidence-backed `pronunciation_representations`: verified IPA, a source-specific phonological code, syllabification, variant data, audio assets, or future TTS metadata. IPA is one representation type, never the assumed canonical source form.

`pronunciation_object_details` remains the browser-compatible detail projection for currently supported verified IPA and delivery metadata. `pronunciation_representation_evidence` independently links every representation to one or more immutable source records.

The Lexique 3.83 importer stores `phonological_code` representations with `transcription_system = lexique383`, plus `syllabification` arrays. These are source-labelled data for future linguistic processing; the current browser deliberately does not show them as IPA or as a pronunciation substitute.

The retained `pronunciations` table is an importer compatibility boundary. `scripts/add_graph_native_pronunciation_schema.py` materializes each compatible record as a graph object and relationship.

## Surface-form rule

Lemmas and inflected forms are separate objects. A form displays and plays only a pronunciation object directly linked to that form. It never inherits the lemma’s IPA or audio. Absence is displayed honestly as unavailable.

## Playback contract

Pages request `playPronunciation(LanguageObject)`. Provider selection is hidden from UI and currently follows:

```text
local recording → cached local TTS → browser SpeechSynthesis
```

No cloud provider is registered. Future cached audio or premium providers must implement the provider interface without changing data ownership or page markup.

## AI rule

AI-generated IPA, notes, variants, or audio must create a draft representation with provenance, confidence, and review status. It cannot overwrite a curated representation or relabel a source phonological code as verified IPA.
