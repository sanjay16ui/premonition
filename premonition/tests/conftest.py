"""Shared pytest fixtures for API and ML tests."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# ── Test-suite environment setup ─────────────────────────────────────────────
# Must be set BEFORE any premonition modules are imported so that
# is_jwt_enabled() and CsrfProtectionMiddleware see a consistent value.
#
# We use the same secret that test_otp.py uses (setdefault means whichever
# runs first wins — both use the same string to ensure consistency).
os.environ.setdefault("PREMONITION_JWT_SECRET", "test-secret-for-otp-tests-32chars!")

# Disable background realtime loop for most tests (enabled in test_realtime.py)
os.environ.setdefault("PREMONITION_REALTIME_ENABLED", "false")
# Disable rate limiting during test suite to prevent 429 cross-test pollution
os.environ.setdefault("PREMONITION_RATE_LIMIT", "0")

# Legacy API-key used as default auth header for the session-scoped client.
# The CSRF middleware accepts "X-API-Key" and the auth dependency falls through
# to the legacy-key check, granting ADMIN access.
_TEST_API_KEY = "premonition-test-api-key-for-suite"
os.environ.setdefault("PREMONITION_API_KEY", _TEST_API_KEY)

from premonition.api.main import create_app  # noqa: E402
from premonition.config.settings import get_settings  # noqa: E402

# Columns required by PatientFeaturesRequest (T1 safe raw features)
PATIENT_FEATURE_COLUMNS = [
    "age", "gender", "weight_kg", "height_cm", "bmi", "ethnicity", "insurance",
    "diabetes", "hypertension", "chf", "copd", "chronic_kidney_disease",
    "liver_disease", "immunosuppression", "cad", "atrial_fibrillation", "cancer_active",
    "hospital_admit_source", "icu_admit_time_hour", "day_of_week",
    "hr_mean", "hr_max", "hr_min", "hr_std",
    "sbp_mean", "sbp_max", "sbp_min", "sbp_std",
    "dbp_mean", "dbp_max", "dbp_min", "dbp_std", "map_mean",
    "temp_celsius_mean", "temp_celsius_max", "temp_celsius_min", "temp_celsius_std",
    "spo2_mean", "spo2_min", "spo2_max", "spo2_std",
    "respiratory_rate_mean", "respiratory_rate_max", "respiratory_rate_min", "respiratory_rate_std",
]


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture(scope="session")
def sample_patient_features(settings):
    """One real patient row from the dataset, mapped to API schema fields."""
    import pandas as pd

    df = pd.read_csv(settings.dataset_path, nrows=5)
    row = df.iloc[0]
    features = {}
    for col in PATIENT_FEATURE_COLUMNS:
        val = row[col]
        if col == "gender":
            features[col] = str(val)
        elif col in {"age", "icu_admit_time_hour", "day_of_week"}:
            features[col] = int(val)
        elif col in {
            "diabetes", "hypertension", "chf", "copd", "chronic_kidney_disease",
            "liver_disease", "immunosuppression", "cad", "atrial_fibrillation", "cancer_active",
        }:
            features[col] = int(val)
        elif pd.isna(val):
            features[col] = None
        else:
            features[col] = float(val) if isinstance(val, float) else val
    return features


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture(scope="session")
def auth_headers() -> dict:
    """
    Returns default auth headers for the test suite.
    Use this when creating isolated TestClient instances inside tests.
    """
    return {"X-API-Key": _TEST_API_KEY}


@pytest.fixture(scope="session")
def client(app, auth_headers):
    """
    Session-scoped authenticated TestClient.

    Injects the legacy API key as a default header so every request
    is authenticated as ADMIN without needing per-test setup.
    The same key is accepted by both:
      - CsrfProtectionMiddleware  (has_api_key → passes CSRF)
      - get_auth_context          (legacy key → AuthContext(ADMIN))
    """
    with TestClient(app, headers=auth_headers) as test_client:
        yield test_client
