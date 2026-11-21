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


class _FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"message": {"role": "assistant", "content": "xin chào"}}


def test_llm_contract(monkeypatch):
    # Fake the HTTP call so the test does not need Ollama running.
    monkeypatch.setattr(llm_client.httpx, "post", lambda *a, **kw: _FakeResponse())
    assert isinstance(llm_client.generate("hello"), str)
    assert isinstance(llm_client.generate("hello", system="be brief"), str)


def test_pii_token_format_and_entities():
    from app.types import PIIEntity

    sid = "contract-test-pii"
    text = "Gọi 0912345678 nhé, số khác 0987654321, lặp lại 0912345678"
    r = pii.mask(text, sid)
    assert r.masked_text == "Gọi <PHONE_1> nhé, số khác <PHONE_2>, lặp lại <PHONE_1>"
    assert all(isinstance(e, PIIEntity) for e in r.entities)
    assert {e.type for e in r.entities} <= {"NAME", "PHONE", "CCCD", "ACCOUNT"}
    assert all(text[e.start : e.end] == e.text for e in r.entities)
    assert pii.unmask(r.masked_text, sid) == text
    pii.clear_session(sid)
