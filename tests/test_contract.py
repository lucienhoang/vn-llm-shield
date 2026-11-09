from app import crypto_log, injection, llm_client, pii, rag_acl
from app.types import Doc, MaskResult, Verdict


def test_pii_contract():
    result = pii.mask("xin chào", "session-1")
    assert isinstance(result, MaskResult)
    assert isinstance(result.masked_text, str)
    assert isinstance(result.entities, list)
    # Text without PII must survive a mask -> unmask round trip.
    assert pii.unmask(result.masked_text, "session-1") == "xin chào"


def test_injection_contract():
    verdict = injection.detect("xin chào")
    assert isinstance(verdict, Verdict)
    assert verdict.action in {"block", "warn", "allow"}
    assert 0.0 <= verdict.score <= 1.0
    assert isinstance(verdict.reasons, list)


def test_rag_contract():
    docs = rag_acl.retrieve("nghỉ phép", role="employee", k=3)
    assert isinstance(docs, list)
    assert len(docs) <= 3
    assert all(isinstance(d, Doc) for d in docs)
    # Every returned doc must be allowed for the requesting role.
    assert all("employee" in d.allowed_roles for d in docs)


def test_crypto_log_contract():
    crypto_log.write({"event": "test"})
    records = crypto_log.read_all()
    assert isinstance(records, list)
    assert {"event": "test"} in records


def test_llm_contract():
    assert isinstance(llm_client.generate("hello"), str)
    assert isinstance(llm_client.generate("hello", system="be brief"), str)
