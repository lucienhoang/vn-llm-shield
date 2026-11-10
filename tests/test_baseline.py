from fastapi.testclient import TestClient

from app import baseline
from app.main import app

client = TestClient(app)


def test_baseline_leaks_manager_doc_to_employee():
    # Documents the T04 hole: role is ignored, so an employee gets the manager salary doc.
    docs = baseline.retrieve_unfiltered("bảng lương quản lý")
    assert "doc_002" in [d.doc_id for d in docs]


def test_prompt_contains_retrieved_text_verbatim():
    docs = baseline.retrieve_unfiltered("tiếp nhận hồ sơ ứng viên")
    prompt = baseline.build_prompt("câu hỏi", docs)
    assert "bỏ qua mọi chỉ dẫn" in prompt  # T05: poisoned text goes in unchecked


def test_chat_endpoint(monkeypatch):
    monkeypatch.setattr(
        baseline.llm_client, "generate", lambda prompt, system=None: "ok"
    )
    resp = client.post(
        "/chat", json={"message": "nghỉ phép bao nhiêu ngày", "role": "employee"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "ok"
    assert "doc_001" in body["retrieved_doc_ids"]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}
