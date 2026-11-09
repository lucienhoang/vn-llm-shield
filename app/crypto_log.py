"""Encrypted conversation log. STUB: in-memory, NOT encrypted. Real version: issue #12."""

_records: list[dict] = []


def write(record: dict) -> None:
    _records.append(dict(record))


def read_all() -> list[dict]:
    return list(_records)
