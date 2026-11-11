"""Validate data/prompts_eval.csv against the agreed format.

Run from the repo root:  python experiments/validate_prompts.py
"""

import csv
from collections import Counter
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "prompts_eval.csv"
COLUMNS = ["id", "text", "lang", "category", "label", "has_pii", "source", "note"]
LABEL_OF_CATEGORY = {
    "benign": "benign",
    "benign_pii": "benign",
    "benign_lookalike": "benign",
    "injection": "attack",
    "jailbreak": "attack",
}
TARGET = {
    "benign": 40,
    "benign_pii": 40,
    "benign_lookalike": 40,
    "injection": 50,
    "jailbreak": 40,
}


def validate(path: Path = DEFAULT_PATH) -> tuple[list[str], list[dict]]:
    # utf-8-sig reads both plain UTF-8 and UTF-8 with BOM (Excel).
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            return [f"Header must be {COLUMNS}, got {reader.fieldnames}"], []
        rows = list(reader)

    errors: list[str] = []
    ids: set[str] = set()
    texts: set[str] = set()
    for line, row in enumerate(rows, start=2):  # line 1 is the header
        where = f"line {line} ({row['id']})"
        if not row["id"] or row["id"] in ids:
            errors.append(f"{where}: id is empty or duplicated")
        ids.add(row["id"])
        if not row["text"].strip():
            errors.append(f"{where}: text is empty")
        key = row["text"].strip().lower()
        if key in texts:
            errors.append(f"{where}: duplicated text")
        texts.add(key)
        if row["lang"] not in {"vi", "en"}:
            errors.append(f"{where}: lang must be vi or en")
        if row["category"] not in LABEL_OF_CATEGORY:
            errors.append(f"{where}: unknown category {row['category']!r}")
        elif row["label"] != LABEL_OF_CATEGORY[row["category"]]:
            errors.append(f"{where}: label {row['label']!r} does not match category")
        if row["has_pii"] not in {"0", "1"}:
            errors.append(f"{where}: has_pii must be 0 or 1")
        if row["category"] == "benign_pii" and row["has_pii"] != "1":
            errors.append(f"{where}: benign_pii must have has_pii=1")
        if row["source"] not in {"manual", "llm"}:
            errors.append(f"{where}: source must be manual or llm")
    return errors, rows


if __name__ == "__main__":
    errors, rows = validate()
    for e in errors:
        print("ERROR:", e)
    counts = Counter(r["category"] for r in rows)
    print(f"\n{len(rows)} rows (goal: 200+)")
    for cat, goal in TARGET.items():
        print(f"  {cat:18} {counts.get(cat, 0):3} / {goal}")
    print("  lang:", dict(Counter(r["lang"] for r in rows)))
    print("  source:", dict(Counter(r["source"] for r in rows)))
    print("OK" if not errors else f"{len(errors)} error(s)")
