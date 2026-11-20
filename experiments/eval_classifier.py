"""Cross-validated comparison: rules vs classifier vs rules + classifier.

Run from the repo root:  python -m experiments.eval_classifier
Classifier numbers are out-of-fold: every prompt is scored by a model that never saw it.
Stratified by category so every fold has some of each of the 5 groups.
"""

import time

import numpy as np
from sklearn.model_selection import StratifiedKFold

from app.injection import rule_verdict
from app.injection_ml import BLOCK_T, WARN_T, build_pipeline, load_rows

N_REPEATS = 5
N_FOLDS = 5
THRESHOLDS = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
CHOSEN = BLOCK_T  # per-category breakdown uses the real production threshold

rows = load_rows()
texts = [r["text"] for r in rows]
y = np.array([1 if r["label"] == "attack" else 0 for r in rows])
cats = np.array([r["category"] for r in rows])
rule_blocked = np.array([rule_verdict(t).action == "block" for t in texts])

# Out-of-fold P(attack), one row per repetition.
oof = np.zeros((N_REPEATS, len(rows)))
for rep in range(N_REPEATS):
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=rep)
    for train, test in skf.split(texts, cats):
        model = build_pipeline()
        model.fit([texts[i] for i in train], y[train])
        oof[rep, test] = model.predict_proba([texts[i] for i in test])[:, 1]


def rates(blocked):
    """blocked: bool array (N_REPEATS, n_prompts) -> (block rate, FPR) per repetition."""
    return blocked[:, y == 1].mean(axis=1), blocked[:, y == 0].mean(axis=1)


def fmt(a):
    return f"{a.mean():6.1%} +-{a.std():.1%}"


print(
    f"{len(rows)} prompts ({int(y.sum())} attack, {int((y == 0).sum())} benign); "
    f"{N_REPEATS} x {N_FOLDS}-fold CV\n"
)
print(f"{'method':30} {'block rate':>16} {'FPR':>16}")
br, fp = rates(np.tile(rule_blocked, (N_REPEATS, 1)))
print(f"{'rules only':30} {fmt(br):>16} {fmt(fp):>16}")
for t in THRESHOLDS:
    clf_blocked = oof >= t
    for name, blocked in [
        (f"classifier only, T={t}", clf_blocked),
        (f"rules + classifier, T={t}", clf_blocked | rule_blocked),
    ]:
        br, fp = rates(blocked)
        print(f"{name:30} {fmt(br):>16} {fmt(fp):>16}")

combined = (oof >= CHOSEN) | rule_blocked
print(f"\nShare blocked per category (rules + classifier, T={CHOSEN}):")
for c in sorted(set(cats)):
    print(
        f"  {c:18} {combined[:, cats == c].mean():6.1%}  (n={int((cats == c).sum())})"
    )

print("\nAttacks missed in at least half of the repetitions:")
for i, r in enumerate(rows):
    if y[i] == 1 and combined[:, i].mean() < 0.5:
        print(f"  {r['id']} [{r['category']}] {r['text'][:70]}")
print("\nBenign blocked in at least half of the repetitions:")
for i, r in enumerate(rows):
    if y[i] == 0 and combined[:, i].mean() >= 0.5:
        print(f"  {r['id']} [{r['category']}] {r['text'][:70]}")

warned = ((oof >= WARN_T) & ~combined)[:, y == 0].mean(axis=1)
print(f"\nBenign warned (classifier, {WARN_T} <= p < {BLOCK_T}): {fmt(warned)}")

final = build_pipeline().fit(texts, y)
start = time.perf_counter()
for t in texts:
    final.predict_proba([t])
print(
    f"\nClassifier latency: {(time.perf_counter() - start) * 1000 / len(texts):.2f} ms/prompt"
)
