
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import os

from src.features.text import clean_description
from src.utils.config import load_config, resolve_path

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_model_bundle(model_path: str | Path | None = None) -> dict[str, Any]:
    cfg = load_config()
    path = Path(
        model_path
        or os.getenv("MODEL_PATH")
        or resolve_path(cfg["artifacts"]["dir"]) / cfg["artifacts"]["model_file"]
    )
    if not path.is_absolute():
        path = resolve_path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Model not found: {path}. Run: python -m src.train"
        )
    bundle = joblib.load(path)
    logger.info("Loaded model '%s' from %s", bundle.get("model_name"), path)
    return bundle


def predict_text(text: str) -> dict[str, Any]:
    cfg = load_config()
    max_len = int(cfg["data"]["max_text_len"])
    bundle = load_model_bundle()
    pipeline = bundle["pipeline"]
    cleaned = clean_description(text, max_len)
    if len(cleaned) < 5:
        raise ValueError("Description is too short after cleaning")

    proba_vec = pipeline.predict_proba([cleaned])[0]
    classes = pipeline.classes_
    label_map = bundle.get(
        "label_names", {0: "low", 1: "medium", 2: "high"}
    )
    probabilities = {
        str(label_map[int(cls)]): round(float(p), 4)
        for cls, p in zip(classes, proba_vec)
    }
    best_idx = int(proba_vec.argmax())
    risk = str(label_map[int(classes[best_idx])])

    thresholds = bundle.get("severity_thresholds") or cfg["data"].get(
        "severity_thresholds", {}
    )

    return {
        "risk": risk,
        "probabilities": probabilities,
        "probability": probabilities[risk],
        "model_name": bundle.get("model_name", "unknown"),
        "severity_thresholds": thresholds,
    }
