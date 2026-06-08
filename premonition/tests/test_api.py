"""Section 2 — FastAPI backend integration tests."""

from __future__ import annotations

import io
import json

import pandas as pd
import pytest

from premonition.api.schemas.requests import PatientFeaturesRequest
from premonition.api.services.model_loader import ModelLoaderService
from premonition.api.version import API_PREFIX
from premonition.config.settings import get_settings
from premonition.models.prediction_logger import PredictionLogger

HEALTH_URL = f"{API_PREFIX}/health"
STATUS_URL = f"{API_PREFIX}/system/status"
VERSION_URL = f"{API_PREFIX}/models/version"
PREDICT_URL = f"{API_PREFIX}/predict"
BATCH_URL = f"{API_PREFIX}/predict/batch"
EXPLAIN_URL = f"{API_PREFIX}/explain"
HISTORY_URL = f"{API_PREFIX}/predictions/history"
AUDIT_URL = f"{API_PREFIX}/audit/logs"
METRICS_URL = f"{API_PREFIX}/metrics"


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get(HEALTH_URL)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "premonition-api"

    def test_health_has_request_id_header(self, client):
        response = client.get(HEALTH_URL)
        assert "X-Request-ID" in response.headers
        assert "X-Response-Time-Ms" in response.headers


class TestSystemStatus:
    def test_system_status(self, client):
        response = client.get(STATUS_URL)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in {"ready", "degraded"}
        assert "model_loaded" in data
        assert "uptime_seconds" in data


class TestModelVersion:
    def test_model_version(self, client):
        response = client.get(VERSION_URL)
        assert response.status_code == 200
        data = response.json()
        assert "model_name" in data
        assert "model_version" in data
        assert data["tier"] == "t1"


class TestModelLoading:
    def test_model_loader_loads_best_model(self, settings):
        import asyncio

        loader = ModelLoaderService(settings)
        state = asyncio.run(loader.load())
        assert state.loaded is True
        assert state.model is not None
        assert state.preprocessor is not None
        assert state.intelligence is not None
        assert loader.is_ready()

    def test_model_loaded_at_startup(self, client):
        response = client.get(STATUS_URL)
        data = response.json()
        assert data["model_loaded"] is True
        assert data["model_name"] is not None


class TestValidation:
    def test_predict_rejects_invalid_age(self, client, sample_patient_features):
        bad = sample_patient_features.copy()
        bad["age"] = 5
        payload = {"patient_id": 999, "features": bad}
        response = client.post(PREDICT_URL, json=payload)
        assert response.status_code == 422
        body = response.json()
        assert body["error"] == "validation_error"
        assert any("age" in d["field"] for d in body["details"])

    def test_predict_rejects_extra_fields(self, client, sample_patient_features):
        bad = sample_patient_features.copy()
        bad["sepsis_label"] = 1
        payload = {"patient_id": 999, "features": bad}
        response = client.post(PREDICT_URL, json=payload)
        assert response.status_code == 422

    def test_batch_rejects_duplicate_ids(self, client, sample_patient_features):
        item = {"patient_id": 100, "features": sample_patient_features}
        payload = {"patients": [item, item]}
        response = client.post(BATCH_URL, json=payload)
        assert response.status_code == 422

    def test_patient_features_schema_valid(self, sample_patient_features):
        model = PatientFeaturesRequest(**sample_patient_features)
        assert model.age >= 18


class TestPredictEndpoint:
    def test_predict_single_patient(self, client, sample_patient_features):
        payload = {
            "patient_id": 37464,
            "features": sample_patient_features,
            "include_shap": True,
            "include_explanation": True,
        }
        response = client.post(PREDICT_URL, json=payload)
        assert response.status_code == 200, response.text
        data = response.json()

        assert data["patient_id"] == "37464"
        assert 0.0 <= data["risk_score"] <= 1.0
        assert data["prediction"] in {0, 1}
        assert data["prediction_label"] in {"sepsis_alert", "no_alert"}
        assert data["confidence"] in {"High", "Medium", "Low"}
        assert data["risk_category"] in {"green", "yellow", "orange", "red"}
        assert data["model_name"]
        assert data["model_version"]
        assert "request_id" in data
        assert data.get("top_factors") is not None

    def test_predict_batch(self, client, sample_patient_features):
        payload = {
            "patients": [
                {"patient_id": 101, "features": sample_patient_features},
                {"patient_id": 102, "features": sample_patient_features},
            ],
            "include_shap": False,
        }
        response = client.post(BATCH_URL, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["predictions"]) == 2


class TestExplainEndpoint:
    def test_explain_patient(self, client, sample_patient_features):
        payload = {
            "patient_id": 37464,
            "features": sample_patient_features,
            "top_n": 5,
        }
        response = client.post(EXPLAIN_URL, json=payload)
        assert response.status_code == 200, response.text
        data = response.json()

        assert data["patient_id"] == "37464"
        assert 0.0 <= data["risk_score"] <= 1.0
        assert data["explanation_summary"]
        assert len(data["top_factors"]) <= 5
        assert data["shap"]["base_value"] is not None
        assert "risk_increasers" in data["shap"]


class TestAuditLogging:
    def test_prediction_creates_audit_log(self, client, sample_patient_features, settings, tmp_path, monkeypatch, auth_headers):
        import os
        monkeypatch.setenv("PREMONITION_LOGS_DIR", str(tmp_path))
        get_settings.cache_clear()

        from premonition.api.main import create_app
        from fastapi.testclient import TestClient

        # Isolated client also needs auth headers when JWT is enabled
        with TestClient(create_app(), headers=auth_headers) as isolated_client:
            payload = {
                "patient_id": 55555,
                "features": sample_patient_features,
                "include_shap": False,
            }
            response = isolated_client.post(PREDICT_URL, json=payload)
            assert response.status_code == 200

            logger = PredictionLogger(tmp_path)
            records = logger.read_log()
            assert len(records) >= 1
            assert any(r["patient_id"] == "55555" for r in records)

    def test_prediction_history_endpoint(self, client, sample_patient_features):
        client.post(
            PREDICT_URL,
            json={"patient_id": 77777, "features": sample_patient_features, "include_shap": False},
        )
        response = client.get(HISTORY_URL, params={"limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "count" in data

    def test_audit_logs_endpoint(self, client):
        response = client.get(AUDIT_URL, params={"limit": 5})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestMetricsEndpoint:
    def test_metrics_json(self, client):
        response = client.get(METRICS_URL)
        assert response.status_code == 200
        data = response.json()
        assert "predictions_total" in data
        assert "model_loaded" in data

    def test_metrics_prometheus(self, client):
        response = client.get(METRICS_URL, params={"format": "prometheus"})
        assert response.status_code == 200
        assert "premonition_predictions_total" in response.text


class TestCsvUpload:
    def test_predict_upload_csv(self, client, settings, sample_patient_features):
        row = sample_patient_features.copy()
        row["subject_id"] = 88888
        df = pd.DataFrame([row])
        csv_bytes = df.to_csv(index=False).encode("utf-8")

        response = client.post(
            f"{API_PREFIX}/predict/upload-csv",
            files={"file": ("patients.csv", io.BytesIO(csv_bytes), "text/csv")},
            data={"id_column": "subject_id", "include_shap": "false"},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["count"] == 1
