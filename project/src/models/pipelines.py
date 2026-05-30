
from typing import Any

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.pipeline import Pipeline


def _tfidf_params(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        "max_features": int(cfg["model"]["tfidf_max_features"]),
        "ngram_range": tuple(cfg["model"]["tfidf_ngram_range"]),
        "min_df": 2,
        "stop_words": "english",
    }


def build_experiment_models(cfg: dict[str, Any]) -> dict[str, Pipeline]:
    """Модели для сравнения в notebooks/02_experiments.ipynb."""
    tfidf_params = _tfidf_params(cfg)
    rs = int(cfg["model"]["random_state"])

    return {
        "DummyClassifier": Pipeline(
            [
                ("tfidf", TfidfVectorizer(**tfidf_params)),
                ("clf", DummyClassifier(strategy="most_frequent")),
            ]
        ),
        "LogisticRegression": Pipeline(
            [
                ("tfidf", TfidfVectorizer(**tfidf_params)),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=rs,
                    ),
                ),
            ]
        ),
        "SGDClassifier": Pipeline(
            [
                ("tfidf", TfidfVectorizer(**tfidf_params)),
                (
                    "clf",
                    SGDClassifier(
                        loss="log_loss",
                        penalty="l2",
                        alpha=1e-4,
                        class_weight="balanced",
                        max_iter=1000,
                        random_state=rs,
                    ),
                ),
            ]
        ),
        "RandomForestClassifier": Pipeline(
            [
                ("tfidf", TfidfVectorizer(**tfidf_params)),
                (
                    "clf",
                    RandomForestClassifier(
                        n_estimators=200,
                        class_weight="balanced",
                        random_state=rs,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def get_production_pipeline(cfg: dict[str, Any]) -> tuple[str, Pipeline]:
    """Финальная модель для API (имя из config + sklearn Pipeline)."""
    name = str(cfg["model"]["production_model"])
    models = build_experiment_models(cfg)
    if name not in models:
        raise ValueError(
            f"Unknown production_model '{name}'. "
            f"Expected one of: {list(models.keys())}"
        )
    return name, models[name]
