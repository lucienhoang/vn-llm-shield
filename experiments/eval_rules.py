"""Evaluate the rule layer on data/prompts_eval.csv.  Run: python experiments/eval_rules.py"""

import csv
import time
from pathlib import Path

from app.injection import detect

DATA = Path(__file__).resolve().parent.parent / "data" / "prompts_eval.csv"

with open(DATA, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

attacks = [r for r in rows if r["label"] == "attack"]
benign = [r for r in rows if r["label"] == "benign"]

start = time.perf_counter()
results = {r["id"]: detect(r["text"]) for r in rows}
elapsed_ms = (time.perf_counter() - start) * 1000

caught = [r for r in attacks if results[r["id"]].action == "block"]
missed = [r for r in attacks if results[r["id"]].action != "block"]
false_pos = [r for r in benign if results[r["id"]].action == "block"]
warned = [r for r in benign if results[r["id"]].action == "warn"]

print(f"Prompts: {len(rows)} ({len(attacks)} attack, {len(benign)} benign)")
print(
    f"Block rate (attacks blocked):   {len(caught)}/{len(attacks)} = {len(caught) / len(attacks):.1%}"
)
print(
    f"False-positive rate (benign blocked): {len(false_pos)}/{len(benign)} = {len(false_pos) / len(benign):.1%}"
)
print(f"Benign warned: {len(warned)}")
print(f"Avg latency: {elapsed_ms / len(rows):.3f} ms/prompt")
print("\nMISSED attacks:")
for r in missed:
    print(f"  {r['id']} [{r['category']}] {r['text'][:80]}")
print("\nFALSE POSITIVES:")
for r in false_pos:
    print(f"  {r['id']} [{r['category']}] {r['text'][:80]}")
