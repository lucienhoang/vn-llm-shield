"""LLM client (Ollama). Real version for issue #3.

Reads settings from environment variables (see .env.example):
  LLM_BACKEND   ollama (only backend implemented for now)
  OLLAMA_HOST   default http://localhost:11434
  OLLAMA_MODEL  default qwen2.5:3b
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()  # read .env if present


class LLMError(RuntimeError):
    """Raised when the LLM backend is unreachable or returns an error."""


def generate(prompt: str, system: str | None = None) -> str:
    backend = os.getenv("LLM_BACKEND", "ollama")
    if backend != "ollama":
        raise NotImplementedError(f"LLM_BACKEND={backend!r} is not implemented yet")

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,  # wait for the full answer
        "options": {
            "temperature": 0,  # reproducible results for experiments
            "num_predict": 512,  # cap answer length (CPU is slow)
        },
    }

    try:
        # connect=5s: fail fast if Ollama is not running.
        # 300s total: a 3B model on CPU can be slow, especially on cold start.
        response = httpx.post(
            f"{host}/api/chat",
            json=payload,
            timeout=httpx.Timeout(300.0, connect=5.0),
        )
        response.raise_for_status()
    except httpx.ConnectError as e:
        raise LLMError(
            f"Cannot connect to Ollama at {host}. Is Ollama running? (try: ollama list)"
        ) from e
    except httpx.HTTPError as e:
        raise LLMError(f"Ollama request failed: {e}") from e

    return response.json()["message"]["content"]
