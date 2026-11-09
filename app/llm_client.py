"""LLM client. STUB: echoes the prompt. Real version (Ollama): issue #3."""


def generate(prompt: str, system: str | None = None) -> str:
    return f"[STUB LLM] {prompt[:100]}"
