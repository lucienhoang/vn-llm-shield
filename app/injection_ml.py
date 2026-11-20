"""ML layer for injection detection: TF-IDF + Logistic Regression. Issue #16.

The model is trained from data/prompts_eval.csv the first time it is needed
(it takes well under a second), so there is no model file to commit or unpickle.
NEVER report this model's accuracy on the data it was trained on: use
experiments/eval_classifier.py (cross-validation).
"""

import csv
from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from app.textnorm import normalize
from app.types import Verdict

DATA = Path(__file__).resolve().parent.parent / "data" / "prompts_eval.csv"

# Thresholds on P(attack). Set from cross-validation (see experiments/eval_classifier.py).
BLOCK_T = 0.6
WARN_T = 0.4


def load_rows(path: Path = DATA) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_pipeline() -> Pipeline:
    features = FeatureUnion(
        [
            (
                "word",
                TfidfVectorizer(
                    preprocessor=normalize,
                    analyzer="word",
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                ),
            ),
            (
                "char",
                TfidfVectorizer(
                    preprocessor=normalize,
                    analyzer="char_wb",
                    ngram_range=(2, 5),
                    sublinear_tf=True,
                    min_df=2,
                ),
            ),
        ]
    )
    clf = LogisticRegression(C=10, class_weight="balanced", max_iter=1000)
    return Pipeline([("tfidf", features), ("lr", clf)])


@lru_cache(maxsize=1)
def get_model() -> Pipeline:
    rows = load_rows()
    texts = [r["text"] for r in rows]
    y = [1 if r["label"] == "attack" else 0 for r in rows]
    return build_pipeline().fit(texts, y)


def attack_probability(text: str) -> float:
    return float(get_model().predict_proba([text])[0][1])


def clf_verdict(text: str) -> Verdict:
    p = attack_probability(text)
    action = "block" if p >= BLOCK_T else "warn" if p >= WARN_T else "allow"
    reasons = [f"clf: attack probability {p:.2f}"] if action != "allow" else []
    return Verdict(action=action, score=round(p, 2), reasons=reasons)
