from __future__ import annotations

import hashlib

from .tokenizer import normalise, tokenize
from .types import AnalysisEdge, AnalysisNode, SentenceAnalysis, Token

ENGINE_VERSION = "sil-0.1.0"
# Narrow, transparent morphology support for the v1 milestone. These complement
# graph forms until the full morphology import is available.
FORM_HINTS = {"a": "avoir", "ai": "avoir", "as": "avoir", "avons": "avoir", "avez": "avoir", "ont": "avoir", "allé": "aller", "allée": "aller", "aimé": "aimer", "aimée": "aimer"}


class SentenceIntelligenceEngine:
    def __init__(self, repository):
        self.repository = repository

    def analyze(self, sentence: str, saved_object_ids: set[str] | None = None) -> SentenceAnalysis:
        saved_object_ids = saved_object_ids or set()
        tokens = tokenize(sentence)
        nodes: list[AnalysisNode] = []
        edges: list[AnalysisEdge] = []
        for index, token in enumerate(tokens):
            self._resolve(token)
            node = AnalysisNode(f"token:{index}", "token", token.surface, token.object_id, (token.start, token.end), {"underlying": token.underlying, "lemma_id": token.lemma_id}, token.source, token.confidence)
            nodes.append(node)
            if token.lemma_id:
                edges.append(AnalysisEdge(node.id, token.lemma_id, "references", token.confidence))
        self._multiword(tokens, nodes, edges)
        self._grammar(tokens, nodes, edges)
        learning = self._learning(tokens, nodes, saved_object_ids)
        unresolved = [token.surface for token in tokens if token.surface.isalpha() and not token.object_id and not token.lemma_id]
        digest = hashlib.sha256(normalise(sentence).encode()).hexdigest()[:16]
        return SentenceAnalysis(f"analysis:{digest}", sentence, normalise(sentence), ENGINE_VERSION, tokens, nodes, edges, learning, unresolved, confidence=0.95 if not unresolved else 0.7)

    def _resolve(self, token: Token) -> None:
        forms = self.repository.forms(token.normalized)
        if forms:
            match = forms[0]; token.object_id, token.lemma_id, token.confidence = match['id'], match['lemma_id'], 1.0; return
        objects = self.repository.objects(token.normalized)
        word = next((item for item in objects if item['type_code'] == 'word'), objects[0] if objects else None)
        if word:
            token.object_id = token.lemma_id = word['id']; token.confidence = 1.0; return
        hint = FORM_HINTS.get(token.normalized)
        if hint:
            candidates = [item for item in self.repository.objects(hint) if item['type_code'] == 'word']
            if candidates:
                token.lemma_id, token.confidence = candidates[0]['id'], 0.85

    def _multiword(self, tokens: list[Token], nodes: list[AnalysisNode], edges: list[AnalysisEdge]) -> None:
        # v1 recognizes graph-backed `avoir besoin de` through lemma/surface matching.
        for start in range(len(tokens) - 2):
            sequence = [tokens[start].lemma_id, tokens[start + 1].lemma_id, tokens[start + 2].lemma_id]
            lemmas = []
            for token, object_id in zip(tokens[start:start + 3], sequence):
                if object_id:
                    rows = self.repository.objects(token.normalized)
                    lemmas.append(next((r['canonical_form'] for r in rows if r['id'] == object_id), FORM_HINTS.get(token.normalized, token.normalized)))
                else: lemmas.append(token.normalized)
            phrase = " ".join(lemmas)
            candidates = [item for item in self.repository.objects(phrase) if item['type_code'] in ('expression', 'idiom', 'collocation')]
            if candidates:
                item = candidates[0]; node = AnalysisNode(f"expression:{start}:{start+3}", item['type_code'], item['display_form'], item['id'], (tokens[start].start, tokens[start+2].end))
                nodes.append(node)
                for index in range(start, start + 3): edges.append(AnalysisEdge(node.id, f"token:{index}", "contains"))

    def _grammar(self, tokens: list[Token], nodes: list[AnalysisNode], edges: list[AnalysisEdge]) -> None:
        values = [token.normalized for token in tokens]
        lemmas = [token.lemma_id for token in tokens]
        def grammar(name: str, evidence: list[int]) -> None:
            item = self.repository.grammar(name)
            node = AnalysisNode(f"grammar:{name}", "grammar_construction", name, item['id'] if item else None, payload={"evidence": evidence}, confidence=1.0 if item else 0.8)
            nodes.append(node)
            for index in evidence: edges.append(AnalysisEdge(node.id, f"token:{index}", "contains"))
        for i in range(len(tokens) - 1):
            if values[i] in {'suis','es','est','sommes','êtes','sont','a','as','avons','avez','ont'} and values[i+1].endswith(('é','ée','és','ées','i','is','it','u')):
                grammar('passé composé with être', [i, i + 1])
            if values[i] in {'vais', 'vas', 'va', 'allons', 'allez', 'vont'} and i + 1 < len(tokens): grammar('futur proche', [i, i + 1])
        if any(value in {'ne', "n'"} or token.underlying[:1] == ['ne'] for value, token in zip(values, tokens)) and 'pas' in values: grammar('negation', [i for i, value in enumerate(values) if value == 'pas' or value.startswith("n'")])
        # `nous` and `vous` are also ordinary subject pronouns. v1 emits a
        # reflexive signal only for unambiguous clitic forms; richer agreement
        # analysis will expand this without producing false positives.
        if any(value in {'me','te','se'} for value in values): grammar('reflexive construction', [i for i, value in enumerate(values) if value in {'me','te','se'}])
        if any('que' in token.underlying or value in {'que','qu'} for value, token in zip(values, tokens)): grammar('simple subordinate clause', [i for i, value in enumerate(values) if value in {'que','qu'} or 'que' in tokens[i].underlying])

    def _learning(self, tokens: list[Token], nodes: list[AnalysisNode], saved: set[str]) -> dict:
        referenced = [token.lemma_id or token.object_id for token in tokens if token.lemma_id or token.object_id]
        grammar = [node.object_id or node.label for node in nodes if node.type == 'grammar_construction']
        return {"new_object_ids": [item for item in referenced if item not in saved], "saved_object_ids": [item for item in referenced if item in saved], "grammar_object_ids": grammar, "review_candidate_ids": list(dict.fromkeys(referenced)), "interesting_expression_ids": [node.object_id for node in nodes if node.type in {'expression','idiom','collocation'}]}
