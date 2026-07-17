# Pronunciation System

## Responsibility

Model pronunciation as reusable linguistic knowledge, independent from page rendering and audio delivery.

## Data contract

An owner Language Object connects to one or more `pronunciation` objects via `has_pronunciation`. `pronunciation_object_details` supports IPA, syllables, stress, liaison, silent letters, elision, notes, regional variant, source, confidence, review status, audio URI, and local audio path.

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

AI-generated IPA, notes, variants, or audio must create a draft Pronunciation Object with provenance, confidence, and review status. It cannot overwrite a curated pronunciation object.
