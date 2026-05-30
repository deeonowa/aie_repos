
import logging
import os
from time import perf_counter
from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.models.predict import load_model_bundle, predict_text
from src.utils.config import load_config

load_dotenv()
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

cfg = load_config()
SERVICE_VERSION = str(cfg["service"]["model_version"])
MAX_TEXT = int(cfg["service"]["max_text_length"])
THRESHOLDS = cfg["data"].get("severity_thresholds", {})


class PredictRequest(BaseModel):
    """Текст описания уязвимости (как в NVD)."""

    description: str = Field(
        ...,
        min_length=10,
        max_length=MAX_TEXT,
        description="English CVE description text",
        examples=[
            "Heap-based buffer overflow in the HTTP parser allows remote code execution."
        ],
    )


class PredictResponse(BaseModel):
    risk: str
    probabilities: Dict[str, float]
    probability: float
    model_name: str
    latency_ms: float
    model_version: str


app = FastAPI(
    title="CVE Severity Triage API",
    version=SERVICE_VERSION,
    description=(
        "Сервис первичной приоритизации уязвимостей по тексту описания CVE. "
        "Классы: low (CVSS < 4), medium (4 ≤ CVSS < 7), high (CVSS ≥ 7) "
        "по меткам обучающей выборки NVD."
    ),
)


@app.on_event("startup")
def startup_load_model() -> None:
    try:
        bundle = load_model_bundle()
        logger.info("Model ready: %s", bundle.get("model_name"))
    except FileNotFoundError as exc:
        logger.error("Model not loaded: %s", exc)


@app.get("/health", tags=["system"])
def health() -> dict:
    try:
        bundle = load_model_bundle()
        return {
            "status": "ok",
            "service": "cve-severity-triage",
            "version": SERVICE_VERSION,
            "model_loaded": True,
            "model_name": bundle.get("model_name"),
            "task": bundle.get("task", "multiclass_severity"),
            "severity_thresholds": bundle.get("severity_thresholds", THRESHOLDS),
        }
    except FileNotFoundError:
        return {
            "status": "degraded",
            "service": "cve-severity-triage",
            "version": SERVICE_VERSION,
            "model_loaded": False,
        }


@app.post("/predict", response_model=PredictResponse, tags=["inference"])
def predict(req: PredictRequest) -> PredictResponse:
    started = perf_counter()
    try:
        result = predict_text(req.description)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        logger.error("Prediction unavailable: model file is missing (%s)", exc)
        raise HTTPException(
            status_code=503,
            detail="Model is not available. Run training first: python -m src.train",
        ) from exc

    latency_ms = (perf_counter() - started) * 1000
    logger.info(
        "predict risk=%s proba=%.4f text_len=%s latency_ms=%.1f",
        result["risk"],
        result["probability"],
        len(req.description),
        latency_ms,
    )
    return PredictResponse(
        risk=result["risk"],
        probabilities=result["probabilities"],
        probability=result["probability"],
        model_name=result["model_name"],
        latency_ms=round(latency_ms, 2),
        model_version=SERVICE_VERSION,
    )
