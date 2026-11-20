"""Shared text normalization (used by the rule layer and the ML layer)."""

import re
import unicodedata


def normalize(text: str) -> str:
    """Lowercase, remove diacritics, map đ -> d, collapse whitespace."""
    text = text.lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip()
