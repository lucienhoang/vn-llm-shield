"""Shared data types: the interface contract between modules.

Do NOT change names, fields or types without opening an Issue
and getting both members to agree (see CONTRIBUTING.md).
"""

from dataclasses import dataclass


@dataclass
class PIIEntity:
    type: str  # NAME | PHONE | CCCD | ACCOUNT
    text: str  # the original text found, e.g. "0912345678"
    start: int  # start index in the original text
    end: int  # end index (exclusive)


@dataclass
class MaskResult:
    masked_text: str  # text with PII replaced by tokens
    entities: list[PIIEntity]  # what was found


@dataclass
class Verdict:
    action: str  # "block" | "warn" | "allow"
    score: float  # 0.0 - 1.0
    reasons: list[str]  # why this verdict


@dataclass
class Doc:
    doc_id: str
    text: str
    allowed_roles: list[str]  # e.g. ["manager", "admin"]
