"""FastAPI gateway. /chat goes through the protection pipeline (issue #17);
/baseline/chat is the original UNPROTECTED chatbot (issue #13), kept for reference."""

from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app import baseline, injection_ml, pipeline
from app.llm_client import LLMError


@asynccontextmanager
async def lifespan(app: FastAPI):
    injection_ml.get_model()  # train the classifier once at startup (< 1 s)
    yield


app = FastAPI(title="VN-LLM-Shield", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    role: str = "employee"  # employee | manager | admin
    session_id: str | None = None
    switches: pipeline.Switches = pipeline.Switches()


class BaselineRequest(BaseModel):
    message: str
    role: str = "employee"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest) -> dict:
    try:
        result = pipeline.chat(req.message, req.role, req.session_id, req.switches)
    except LLMError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return asdict(result)


@app.post("/baseline/chat")
def baseline_chat(req: BaselineRequest) -> dict:
    try:
        return baseline.answer(req.message, req.role)
    except LLMError as e:
        raise HTTPException(status_code=503, detail=str(e))
