# Interface contract

Status: **FROZEN**. Do not change names, parameters or return types without
opening an Issue and getting both members to agree. If a change is approved,
update `app/types.py`, the stubs, `tests/test_contract.py` and this file in the same PR.

## Types (`app/types.py`)

| Type         | Fields                                                                       |
| ------------ | ---------------------------------------------------------------------------- |
| `PIIEntity`  | `type` (NAME, PHONE, CCCD, ACCOUNT), `text`, `start`, `end`                  |
| `MaskResult` | `masked_text`, `entities: list[PIIEntity]`                                   |
| `Verdict`    | `action` ("block", "warn", "allow"), `score` (0.0-1.0), `reasons: list[str]` |
| `Doc`        | `doc_id`, `text`, `allowed_roles: list[str]`                                 |

## Functions

| Module          | Function                        | Returns                                | Owner |
| --------------- | ------------------------------- | -------------------------------------- | ----- |
| `pii.py`        | `mask(text, session_id)`        | `MaskResult`                           | B     |
| `pii.py`        | `unmask(text, session_id)`      | `str`                                  | B     |
| `injection.py`  | `detect(text)`                  | `Verdict`                              | A     |
| `rag_acl.py`    | `retrieve(query, role, k=3)`    | `list[Doc]` (already filtered by role) | B     |
| `crypto_log.py` | `write(record: dict)`           | `None`                                 | B     |
| `crypto_log.py` | `read_all()`                    | `list[dict]` (decrypted, needs key)    | B     |
| `llm_client.py` | `generate(prompt, system=None)` | `str`                                  | A     |
| `pii.py`        | `clear_session(session_id)`     | `None` (drops the session's PII map)   | B     |

## Rules

- `injection.detect` runs on the **original** text, not the PII-masked text.
- `rag_acl.retrieve` filters by role **before** documents are put into the prompt.
- Token format for masked PII: `<NAME_1>`, `<PHONE_1>`, `<CCCD_1>`, `<ACCOUNT_1>`.
- The PII token map is stored per `session_id` and never written to logs in plaintext.
- `pii.mask` may be called several times with the same `session_id` (the question, then each
  retrieved document). The same original value must always get the same token within a session
  (`0912345678` is always `<PHONE_1>`), and new values get the next number. `pii.unmask` must
  restore every token created in that session. The pipeline relies on this.
- `pii.clear_session` is called by the pipeline when a one-shot request ends, so PII never
  accumulates in memory.
- `rag_acl.retrieve(query, role)` is also called with `role="admin"` to simulate "no access
  control" in experiments, so `admin` must be allowed on every document.

## Data formats

- `data/prompts_eval.csv`: `id, text, lang (vi|en), category, label (attack|benign), has_pii (0|1), source (manual|llm), note`
  - `category`: `benign`, `benign_pii`, `benign_lookalike`, `injection`, `jailbreak`
- `data/pii_labeled.csv`: `id, text, entities` (`entities` is a JSON list of `{type, text, start, end}`)
