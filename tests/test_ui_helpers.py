from app.pipeline import PipelineResult
from app.types import Verdict
from ui.helpers import EXAMPLES, find_leaks, status_of, timing_summary


def test_find_leaks():
    assert find_leaks("Mã là ABC-SECRET-7731.") == ["ABC-SECRET-7731"]
    assert find_leaks("abc-secret-7731") == ["ABC-SECRET-7731"]  # case-insensitive
    assert find_leaks("không có gì") == []


def test_status_of():
    blocked = PipelineResult(answer="x", blocked=True, blocked_by="injection")
    assert status_of(blocked) == ("blocked", "Blocked by: injection")
    warn = PipelineResult(answer="x", verdict=Verdict("warn", 0.56, []))
    assert status_of(warn)[0] == "warn"
    ok = PipelineResult(answer="x", verdict=Verdict("allow", 0.0, []))
    assert status_of(ok)[0] == "ok"


def test_timing_summary_without_llm():
    assert "not called" in timing_summary({"protection_total": 2.0})


def test_timing_summary_share():
    assert "0.10%" in timing_summary({"protection_total": 10.0, "llm": 9990.0})


def test_examples_are_complete():
    for ex in EXAMPLES.values():
        assert ex["message"].strip()
        assert ex["role"] in {"employee", "manager", "admin"}
