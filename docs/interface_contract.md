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

## Rules

- `injection.detect` runs on the **original** text, not the PII-masked text.
- `rag_acl.retrieve` filters by role **before** documents are put into the prompt.
- Token format for masked PII: `<NAME_1>`, `<PHONE_1>`, `<CCCD_1>`, `<ACCOUNT_1>`.
- The PII token map is stored per `session_id` and never written to logs in plaintext.

## Data formats

- `data/prompts_eval.csv`: `id, text, lang (vi|en), category, label (attack|benign), has_pii (0|1), source (manual|llm), note`
  - `category`: `benign`, `benign_pii`, `benign_lookalike`, `injection`, `jailbreak`
- `data/pii_labeled.csv`: `id, text, entities` (`entities` is a JSON list of `{type, text, start, end}`)
