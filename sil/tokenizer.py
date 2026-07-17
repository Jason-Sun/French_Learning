from __future__ import annotations

import re

from .types import Token

TOKEN_PATTERN = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:['’][A-Za-zÀ-ÖØ-öø-ÿ]+)?|\d+|[.,;:!?]", re.UNICODE)
CONTRACTIONS = {"au": ["à", "le"], "aux": ["à", "les"], "du": ["de", "le"], "des": ["de", "les"]}
ELISIONS = {"j'": "je", "n'": "ne", "l'": "le", "d'": "de", "qu'": "que", "c'": "ce", "s'": "se", "m'": "me", "t'": "te"}


def normalise(text: str) -> str:
    return " ".join(text.casefold().replace("’", "'").split())


def tokenize(sentence: str) -> list[Token]:
    tokens: list[Token] = []
    for match in TOKEN_PATTERN.finditer(sentence):
        surface = match.group(0)
        value = normalise(surface)
        if value in CONTRACTIONS:
            tokens.append(Token(surface, value, match.start(), match.end(), CONTRACTIONS[value]))
        elif "'" in value and value.split("'", 1)[0] + "'" in ELISIONS:
            prefix, suffix = value.split("'", 1)
            tokens.append(Token(surface, value, match.start(), match.end(), [ELISIONS[prefix + "'"], suffix]))
        else:
            tokens.append(Token(surface, value, match.start(), match.end()))
    return tokens
