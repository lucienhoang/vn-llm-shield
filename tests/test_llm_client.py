import httpx
import pytest

from app import llm_client


class _FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"message": {"role": "assistant", "content": "ok"}}


def test_system_prompt_is_sent(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["json"] = json
        return _FakeResponse()

    monkeypatch.setattr(llm_client.httpx, "post", fake_post)
    llm_client.generate("câu hỏi", system="bạn là trợ lý HR")

    messages = captured["json"]["messages"]
    assert messages[0] == {"role": "system", "content": "bạn là trợ lý HR"}
    assert messages[-1] == {"role": "user", "content": "câu hỏi"}


def test_no_system_prompt(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["json"] = json
        return _FakeResponse()

    monkeypatch.setattr(llm_client.httpx, "post", fake_post)
    llm_client.generate("câu hỏi")
    assert [m["role"] for m in captured["json"]["messages"]] == ["user"]


def test_connection_error_becomes_llm_error(monkeypatch):
    def fake_post(*args, **kwargs):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(llm_client.httpx, "post", fake_post)
    with pytest.raises(llm_client.LLMError):
        llm_client.generate("hello")


def _ollama_running() -> bool:
    try:
        httpx.get("http://localhost:11434", timeout=2)
        return True
    except httpx.HTTPError:
        return False


@pytest.mark.skipif(not _ollama_running(), reason="Ollama is not running")
def test_live_ollama():
    answer = llm_client.generate("Trả lời đúng một từ: 1+1 bằng mấy?")
    assert isinstance(answer, str) and answer.strip()
