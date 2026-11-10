"""FastAPI gateway. For now it only exposes the unprotected baseline (issue #13).
Later (issue #17) /chat will go through pipeline.py with protection switches."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app import baseline
from app.llm_client import LLMError

app = FastAPI(title="VN-LLM-Shield (baseline, unprotected)")


class ChatRequest(BaseModel):
    message: str
    role: str = "employee"  # employee | manager | admin


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest) -> dict:
    try:
        return baseline.answer(req.message, req.role)
    except LLMError as e:
        raise HTTPException(status_code=503, detail=str(e))
