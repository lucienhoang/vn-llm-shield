r"""Protection pipeline: glues the modules together (issue #17). Owner: A only.

Flow (see project notes, section 4):
  question --> injection (on ORIGINAL text) --+
           \-> PII mask (independent) --------+--> block? --> RAG retrieve (ACL first)
  --> scan retrieved docs --> mask docs --> LLM --> scan output --> unmask PII --> answer
Every request is logged (masked text only) and timed per stage.
Only the interface contract is used (docs/interface_contract.md).
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from pydantic import BaseModel

from app import baseline, crypto_log, injection, llm_client, pii, rag_acl
from app.types import Doc, Verdict

# Placeholder output scan (issue #23 will improve it): strings that must never leave the system.
CANARIES = ["ABC-SECRET-7731"]

BLOCKED_MESSAGE = (
    "Yêu cầu bị chặn bởi lớp bảo vệ vì có dấu hiệu prompt injection hoặc jailbreak."
)
OUTPUT_BLOCKED_MESSAGE = (
    "Câu trả lời bị chặn vì chứa thông tin nội bộ không được phép tiết lộ."
)


class Switches(BaseModel):
    """One switch per protection layer (needed for the before/after experiments)."""

    injection: bool = True
    injection_ml: bool = True  # False = rule layer only
    pii: bool = True
    rag_acl: bool = True  # False = retrieve as 'admin' (simulates no access control)
    scan_docs: bool = True  # quarantine retrieved docs that contain injected commands
    output_scan: bool = True
    log: bool = True
    block_on_warn: bool = False  # False: 'warn' passes through (flagged + logged)

    @classmethod
    def all_off(cls) -> "Switches":
        return cls(
            injection=False,
            injection_ml=False,
            pii=False,
            rag_acl=False,
            scan_docs=False,
            output_scan=False,
            log=False,
        )


@dataclass
class PipelineResult:
    answer: str
    session_id: str = ""
    blocked: bool = False
    blocked_by: str | None = None  # "injection" | "output_scan"
    verdict: Verdict | None = None  # injection verdict on the question
    masked_question: str = ""
    retrieved_doc_ids: list[str] = field(default_factory=list)
    quarantined_doc_ids: list[str] = field(default_factory=list)
    timings_ms: dict[str, float] = field(default_factory=dict)


def _ms(t0: float) -> float:
    return (time.perf_counter() - t0) * 1000


def _detect(text: str, sw: Switches) -> Verdict:
    return injection.detect(text) if sw.injection_ml else injection.rule_verdict(text)


def scan_output(text: str) -> list[str]:
    """Return the canary strings found in the LLM output."""
    low = text.lower()
    return [c for c in CANARIES if c.lower() in low]


def _finish(
    res: PipelineResult,
    sw: Switches,
    role: str,
    t: dict[str, float],
    answer_for_log: str,
) -> PipelineResult:
    if sw.log:
        t0 = time.perf_counter()
        crypto_log.write(
            {
                "ts": datetime.now(UTC).isoformat(),
                "session_id": res.session_id,
                "role": role,
                "switches": sw.model_dump(),
                "question_masked": res.masked_question,  # never the raw question when pii is on
                "injection": {
                    "action": res.verdict.action,
                    "score": res.verdict.score,
                    "reasons": res.verdict.reasons,
                },
                "retrieved_doc_ids": res.retrieved_doc_ids,
                "quarantined_doc_ids": res.quarantined_doc_ids,
                "blocked": res.blocked,
                "blocked_by": res.blocked_by,
                "answer_masked": answer_for_log,  # before PII restore
                "timings_ms": {k: round(v, 3) for k, v in t.items()},
            }
        )
        t["log"] = _ms(t0)
    t["protection_total"] = sum(v for k, v in t.items() if k != "llm")
    res.timings_ms = {k: round(v, 3) for k, v in t.items()}
    return res


def _run(question: str, role: str, sid: str, sw: Switches) -> PipelineResult:
    t: dict[str, float] = {}
    res = PipelineResult(answer="", session_id=sid, masked_question=question)

    # 1. Injection detection on the ORIGINAL text (never on the PII-masked text).
    t0 = time.perf_counter()
    res.verdict = _detect(question, sw) if sw.injection else Verdict("allow", 0.0, [])
    t["injection"] = _ms(t0)

    # 2. PII masking, independent of step 1 (so the log never needs the raw text).
    t0 = time.perf_counter()
    if sw.pii:
        res.masked_question = pii.mask(question, sid).masked_text
    t["pii"] = _ms(t0)

    v = res.verdict
    if v.action == "block" or (v.action == "warn" and sw.block_on_warn):
        res.blocked, res.blocked_by, res.answer = True, "injection", BLOCKED_MESSAGE
        return _finish(res, sw, role, t, answer_for_log=BLOCKED_MESSAGE)

    # 3. RAG retrieval: the role filter happens INSIDE retrieve, before any prompt is built.
    #    The query is the original text: retrieval is local, and masking would hide names.
    t0 = time.perf_counter()
    docs = rag_acl.retrieve(question, role if sw.rag_acl else "admin")
    res.retrieved_doc_ids = [d.doc_id for d in docs]
    t["rag"] = _ms(t0)

    # 4. Indirect injection: quarantine poisoned docs (rules only; the classifier was
    #    trained on short user prompts, not on documents).
    t0 = time.perf_counter()
    kept: list[Doc] = []
    for d in docs:
        if sw.scan_docs and injection.rule_verdict(d.text).action == "block":
            res.quarantined_doc_ids.append(d.doc_id)
        else:
            kept.append(d)
    t["doc_scan"] = _ms(t0)

    # 5. Mask PII inside the documents too (same session, so tokens stay consistent).
    t0 = time.perf_counter()
    if sw.pii:
        kept = [
            Doc(d.doc_id, pii.mask(d.text, sid).masked_text, d.allowed_roles)
            for d in kept
        ]
    t["pii"] += _ms(t0)

    # 6. LLM (timed separately: it is NOT protection overhead).
    prompt = baseline.build_prompt(res.masked_question, kept)
    t0 = time.perf_counter()
    reply = llm_client.generate(prompt, system=baseline.SYSTEM_PROMPT)
    t["llm"] = _ms(t0)

    # 7. Scan the output BEFORE restoring PII.
    t0 = time.perf_counter()
    leaked = scan_output(reply) if sw.output_scan else []
    t["output_scan"] = _ms(t0)
    if leaked:
        res.blocked, res.blocked_by, res.answer = (
            True,
            "output_scan",
            OUTPUT_BLOCKED_MESSAGE,
        )
        return _finish(res, sw, role, t, answer_for_log="[blocked]")

    # 8. Restore PII for the user.
    t0 = time.perf_counter()
    res.answer = pii.unmask(reply, sid) if sw.pii else reply
    t["pii"] += _ms(t0)
    return _finish(res, sw, role, t, answer_for_log=reply)


def chat(
    question: str,
    role: str = "employee",
    session_id: str | None = None,
    switches: Switches | None = None,
) -> PipelineResult:
    """Public entry point. A request without a session_id is one-shot: its PII map is
    dropped when the request ends. A UI that passes a fixed session_id keeps the map
    for the whole conversation and must call pii.clear_session() when it ends."""
    sid = session_id or uuid.uuid4().hex
    try:
        return _run(question, role, sid, switches or Switches())
    finally:
        if session_id is None:
            pii.clear_session(sid)
