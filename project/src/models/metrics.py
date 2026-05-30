
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

LABEL_IDS = (0, 1, 2)
LABEL_NAMES = ("low", "medium", "high")


def compute_multiclass_metrics(
    y_true,
    y_pred,
    y_proba,
) -> dict[str, float]:
    recalls = recall_score(
        y_true, y_pred, labels=LABEL_IDS, average=None, zero_division=0
    )
    precisions = precision_score(
        y_true, y_pred, labels=LABEL_IDS, average=None, zero_division=0
    )
    f1s = f1_score(y_true, y_pred, labels=LABEL_IDS, average=None, zero_division=0)

    metrics: dict[str, float] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(
            f1_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "recall_low": float(recalls[0]),
        "recall_medium": float(recalls[1]),
        "recall_high": float(recalls[2]),
        "precision_low": float(precisions[0]),
        "precision_medium": float(precisions[1]),
        "precision_high": float(precisions[2]),
        "f1_low": float(f1s[0]),
        "f1_medium": float(f1s[1]),
        "f1_high": float(f1s[2]),
    }
    try:
        metrics["roc_auc_ovr"] = float(
            roc_auc_score(
                y_true,
                y_proba,
                multi_class="ovr",
                average="weighted",
                labels=LABEL_IDS,
            )
        )
    except ValueError:
        metrics["roc_auc_ovr"] = float("nan")
    return metrics


def confusion_matrix_labels(y_true, y_pred) -> tuple[np.ndarray, tuple[str, ...]]:
    cm = confusion_matrix(y_true, y_pred, labels=LABEL_IDS)
    return cm, LABEL_NAMES
