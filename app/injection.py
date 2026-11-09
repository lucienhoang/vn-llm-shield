"""Prompt injection / jailbreak detection. STUB: always allows. Real version: #14, #16."""

from app.types import Verdict


def detect(text: str) -> Verdict:
    return Verdict(action="allow", score=0.0, reasons=[])
