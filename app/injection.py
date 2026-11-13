"""Prompt injection / jailbreak detection, RULE layer. Issue #14.

Runs on the ORIGINAL user text (never on PII-masked text).
Text is lowercased and stripped of Vietnamese diacritics before matching, so one
rule covers "Bỏ qua mọi chỉ dẫn" and "bo qua moi chi dan".
The ML classifier (issue #16) will be combined with this later.
"""

import re
import unicodedata
from dataclasses import dataclass

from app.types import Verdict

BLOCK_THRESHOLD = 0.7
WARN_THRESHOLD = 0.4


def normalize(text: str) -> str:
    """Lowercase, remove diacritics, map đ -> d, collapse whitespace."""
    text = text.lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class Rule:
    rule_id: str
    pattern: re.Pattern
    weight: float
    reason: str


def _r(rule_id: str, pattern: str, weight: float, reason: str) -> Rule:
    return Rule(rule_id, re.compile(pattern), weight, reason)


# Patterns are written for NORMALIZED text (lowercase, no diacritics).
RULES = [
    # --- T01: override instructions ---
    _r(
        "ignore_vi",
        r"\b(bo qua|lo di|quen|huy bo)\b.{0,20}\b(moi|tat ca|toan bo)\b.{0,15}"
        r"\b(chi dan|huong dan|quy tac|lenh|chi thi|gioi han)\b",
        0.9,
        "Vietnamese: asks to ignore/forget instructions",
    ),
    _r(
        "ignore_vi_prior",
        r"\b(bo qua|lo di|quen|huy bo)\b.{0,15}\bcac\b.{0,10}"
        r"\b(chi dan|huong dan|quy tac|lenh|chi thi)\b.{0,10}"
        r"\b(truoc do|truoc day|ban dau|o tren|cua he thong)\b",
        0.9,
        "Vietnamese: asks to ignore the earlier/original instructions",
    ),
    _r(
        "ignore_en",
        r"\b(ignore|disregard|forget|override)\b.{0,20}"
        r"\b(all|any|every|previous|prior|above|earlier|your|my|these|those|preceding)\b.{0,20}"
        r"\b(instructions?|rules|guidelines|directions|prompts?|system prompt)\b"
        r"|\b(ignore|disregard|forget)\b.{0,10}\b(instructions?|rules|guidelines)\b.{0,10}"
        r"\b(above|before|given|earlier)\b",
        0.9,
        "English: asks to ignore/forget instructions",
    ),
    # --- T03: reveal the system prompt / internal secrets ---
    _r(
        "reveal_vi",
        r"\b(lap lai|in ra|tiet lo|cho xem|hien thi|noi lai|doc lai|liet ke)\b.{0,30}"
        r"\b(system prompt|chi dan ban dau|chi dan cua ban|ma noi bo|"
        r"(chi dan|huong dan|prompt) he thong (cua (ban|may|bot|chatbot)|ban dau))\b",
        0.85,
        "Vietnamese: asks to reveal system prompt / internal code",
    ),
    _r(
        "reveal_vi_weak",
        r"\b(lap lai|in ra|tiet lo|cho xem|hien thi|noi lai|doc lai|liet ke)\b.{0,30}"
        r"\b(chi dan he thong|huong dan he thong|prompt he thong)\b",
        0.5,
        "Vietnamese: mentions system instructions (ambiguous, warn only)",
    ),
    _r(
        "reveal_en",
        r"\b(repeat|reveal|print|show|display|output|tell me|translate|what (is|are|were))\b.{0,40}"
        r"\b(system prompt|initial instructions|your instructions|hidden instructions|"
        r"your prompt|internal code(?! of conduct))\b",
        0.85,
        "English: asks to reveal system prompt / internal code",
    ),
    # --- fake system / admin messages ---
    _r(
        "fake_system",
        r"(^|\n)\s*\[?(system|assistant)\]?\s*:|\b(che do quan tri|admin mode|developer mode)\b.{0,15}\b(da bat|enabled|on)\b",
        0.7,
        "Fake system message or privileged mode",
    ),
    # --- T02: jailbreak / roleplay without limits ---
    _r(
        "jailbreak_vi",
        r"\b(dong vai|gia vo|gia su|tuong tuong)\b.{0,40}"
        r"(\bdan\b|khong (bi |co )?(gioi han|kiem duyet|han che|dao duc|quy tac|rang buoc))",
        0.8,
        "Vietnamese: roleplay as an unrestricted AI",
    ),
    _r(
        "jailbreak_en_mode",
        r"\b(developer mode|dan mode|jailbreak mode|do anything now)\b",
        0.8,
        "English: known jailbreak mode",
    ),
    _r(
        "jailbreak_en_roleplay",
        r"\b(pretend|act as|you are now|roleplay as)\b.{0,60}"
        r"\b(no (safety )?(rules|restrictions|limits|filters)|unrestricted|without (any )?(rules|restrictions))\b",
        0.8,
        "English: roleplay as an unrestricted AI",
    ),
    # --- weak signal: warn only ---
    _r(
        "no_restrictions",
        r"\b(no|without)\s+(restrictions?|safety rules|limitations|filters)\b",
        0.4,
        "Mentions removing restrictions (weak signal)",
    ),
]


def rule_verdict(text: str) -> Verdict:
    norm = normalize(text)
    hits = [r for r in RULES if r.pattern.search(norm)]
    if not hits:
        return Verdict(action="allow", score=0.0, reasons=[])
    # Strongest rule + a small bonus for each extra rule that fires.
    score = min(1.0, max(r.weight for r in hits) + 0.05 * (len(hits) - 1))
    action = (
        "block"
        if score >= BLOCK_THRESHOLD
        else "warn"
        if score >= WARN_THRESHOLD
        else "allow"
    )
    return Verdict(
        action=action,
        score=round(score, 2),
        reasons=[f"{r.rule_id}: {r.reason}" for r in hits],
    )


def detect(text: str) -> Verdict:
    """Public contract (do not change the signature). For now = rules only."""
    return rule_verdict(text)
