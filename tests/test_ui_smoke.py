from pathlib import Path

from streamlit.testing.v1 import AppTest

from app import pipeline
from app.types import Verdict

APP = str(Path(__file__).resolve().parent.parent / "ui" / "app.py")


def test_app_renders_and_runs_a_request(monkeypatch):
    def fake_chat(message, role="employee", session_id=None, switches=None):
        return pipeline.PipelineResult(
            answer="ok",
            verdict=Verdict("allow", 0.0, []),
            masked_question=message,
            timings_ms={"protection_total": 1.0, "llm": 1000.0},
        )

    monkeypatch.setattr(pipeline, "chat", fake_chat)  # no Ollama needed
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception

    at.text_area(key="message").set_value("nghỉ phép bao nhiêu ngày")
    at.button(key="send").click().run()
    assert not at.exception
    result, error = at.session_state["results"]["on"]
    assert error is None and result.answer == "ok"
