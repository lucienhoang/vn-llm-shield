# VN-LLM-Shield

A security gateway that sits between users and an enterprise LLM chatbot. It masks Vietnamese PII, detects prompt injection / jailbreak attempts, enforces role-based access control on RAG documents, and keeps conversation logs encrypted.

> Course project: Information Security (CMP174), HUTECH. Topic C5: protecting data when using LLMs.

## Features

- [ ] Vietnamese PII detection and masking (names, phone numbers, national ID, bank accounts) with restoration in the response.
- [ ] Prompt injection / jailbreak detection (rules + ML classifier).
- [ ] Role-based access control applied **before** documents enter the prompt (RAG).
- [ ] AES-GCM encrypted conversation logs.
- [ ] Local LLM via Ollama (no data leaves the machine).
- [ ] Web demo with protection ON/OFF comparison.

## Architecture

_TODO: add diagram._

## Getting started

### Requirements

- Python 3.11
- [Ollama](https://ollama.com) (for local LLM)

### Installation

```bash
git clone https://github.com/lucienhoang/vn-llm-shield.git
cd vn-llm-shield
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then fill in the values
```

### Run

_TODO: commands for the API and the demo UI._

### Demo accounts

_TODO._

## Project structure

```text
vn-llm-shield/
├── app/            # Gateway modules (PII, injection, RAG ACL, crypto log, LLM client)
├── ui/             # Demo web UI
├── data/           # Fake RAG documents and labeled evaluation sets
├── experiments/    # Evaluation scripts and results
├── redteam/        # promptfoo / garak configs
├── docs/           # Threat model and evidence
└── tests/          # Unit tests
```

## Evaluation

_TODO: blocking rate, false-positive rate, PII precision/recall, latency overhead (before vs. after)._

## Limitations

_TODO._

## License

[MIT](LICENSE)
