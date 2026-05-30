
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ARTIFACT = Path(__file__).resolve().parents[1] / "artifacts" / "cve_model.joblib"


@pytest.fixture
def client():
    if not ARTIFACT.exists():
        pytest.skip("Model artifact missing — run python -m src.train first")
    from src.service.api import app

    return TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("ok", "degraded")
    assert body["service"] == "cve-severity-triage"
    if body["status"] == "ok":
        assert body["task"] == "multiclass_severity"


def test_predict_high_risk_text(client):
    payload = {
        "description": (
            "Remote code execution vulnerability in the network stack "
            "allows unauthenticated attacker to execute arbitrary code."
        )
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk"] in ("low", "medium", "high")
    assert set(data["probabilities"].keys()) == {"low", "medium", "high"}
    assert abs(sum(data["probabilities"].values()) - 1.0) < 0.02
    assert 0.0 <= data["probability"] <= 1.0
    assert data["latency_ms"] >= 0


def test_predict_low_risk_text(client):
    payload = {
        "description": (
            "Information disclosure in local configuration file may reveal "
            "non-sensitive paths when an authenticated local user reads logs."
        )
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk"] in ("low", "medium", "high")


def test_predict_too_short(client):
    response = client.post("/predict", json={"description": "short"})
    assert response.status_code == 422
