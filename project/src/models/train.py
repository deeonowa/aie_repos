
import json
import logging
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    matthews_corrcoef,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from src.data.load_nvd import load_processed_dataset
from src.features.text import clean_description
from src.models.metrics import LABEL_NAMES
from src.models.pipelines import get_production_pipeline
from src.utils.config import load_config, resolve_path

logger = logging.getLogger(__name__)


def _metrics_for_json(y_true, y_pred, y_proba) -> dict[str, float]:
    """Формат метрик как в metrics_all.json / best_model.json."""
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(
            f1_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
        "roc_auc": float(
            roc_auc_score(
                y_true,
                y_proba,
                multi_class="ovr",
                average="weighted",
                labels=[0, 1, 2],
            )
        ),
    }


def train_and_save() -> dict[str, Any]:
    """Обучение финальной production-модели на полном датасете."""
    cfg = load_config()
    df = load_processed_dataset()
    max_len = int(cfg["data"]["max_text_len"])

    texts = df["description"].map(lambda t: clean_description(t, max_len))
    y = df["severity_id"].astype(int)

    rs = int(cfg["model"]["random_state"])
    test_size = float(cfg["model"]["test_size"])
    X_train, X_test, y_train, y_test = train_test_split(
        texts, y, test_size=test_size, random_state=rs, stratify=y
    )

    model_name, pipeline = get_production_pipeline(cfg)
    logger.info("Training production model: %s on %s samples", model_name, len(X_train))
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)
    test_metrics = _metrics_for_json(y_test, y_pred, y_proba)

    artifacts_dir = resolve_path(cfg["artifacts"]["dir"])
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    best_meta = {
        "model_name": model_name,
        "model_type": str(type(pipeline.named_steps["clf"])),
        "best_params": {},
        "cv_score": None,
        "test_metrics": test_metrics,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "n_total": int(len(df)),
    }
    best_meta_path = artifacts_dir / cfg["artifacts"]["best_model_meta_file"]
    with best_meta_path.open("w", encoding="utf-8") as f:
        json.dump(best_meta, f, ensure_ascii=False, indent=2)

    model_path = artifacts_dir / cfg["artifacts"]["model_file"]
    joblib.dump(
        {
            "pipeline": pipeline,
            "model_name": model_name,
            "severity_thresholds": cfg["data"]["severity_thresholds"],
            "label_names": {i: name for i, name in enumerate(LABEL_NAMES)},
            "task": "multiclass_severity",
        },
        model_path,
    )

    logger.info("Saved model: %s", model_path)
    logger.info("Saved metadata: %s", best_meta_path)
    return best_meta
