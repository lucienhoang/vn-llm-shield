"""PII masking. STUB: returns text unchanged. Real version: issues #6-#8."""

from app.types import MaskResult


def mask(text: str, session_id: str) -> MaskResult:
    return MaskResult(masked_text=text, entities=[])


def unmask(text: str, session_id: str) -> str:
    return text
