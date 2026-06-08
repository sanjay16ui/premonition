"""API request models with Pydantic validation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class PatientFeaturesRequest(BaseModel):
    """Raw patient features for a single prediction (tier T1 safe features)."""

    subject_id: int | str | None = Field(None, description="Patient identifier")
    age: int = Field(..., ge=18, le=120)
    gender: str = Field(..., pattern=r"^(M|F)$")
    weight_kg: float = Field(..., gt=0, le=300)
    height_cm: float = Field(..., gt=100, le=250)
    bmi: float | None = Field(None, ge=10, le=60)
    ethnicity: str
    insurance: str
    # Comorbidities (0/1)
    diabetes: int = Field(0, ge=0, le=1)
    hypertension: int = Field(0, ge=0, le=1)
    chf: int = Field(0, ge=0, le=1)
    copd: int = Field(0, ge=0, le=1)
    chronic_kidney_disease: int = Field(0, ge=0, le=1)
    liver_disease: int = Field(0, ge=0, le=1)
    immunosuppression: int = Field(0, ge=0, le=1)
    cad: int = Field(0, ge=0, le=1)
    atrial_fibrillation: int = Field(0, ge=0, le=1)
    cancer_active: int = Field(0, ge=0, le=1)
    # Admin
    hospital_admit_source: str
    icu_admit_time_hour: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=1, le=7)
    # Vitals (T1 core)
    hr_mean: float = Field(..., ge=30, le=250)
    hr_max: float = Field(..., ge=30, le=280)
    hr_min: float = Field(..., ge=20, le=220)
    hr_std: float = Field(..., ge=0, le=30)
    sbp_mean: float = Field(..., ge=50, le=250)
    sbp_max: float = Field(..., ge=50, le=280)
    sbp_min: float = Field(..., ge=40, le=250)
    sbp_std: float = Field(..., ge=0, le=30)
    dbp_mean: float = Field(..., ge=30, le=180)
    dbp_max: float = Field(..., ge=30, le=200)
    dbp_min: float = Field(..., ge=20, le=180)
    dbp_std: float = Field(..., ge=0, le=25)
    map_mean: float | None = Field(None, ge=40, le=200)
    temp_celsius_mean: float = Field(..., ge=30, le=45)
    temp_celsius_max: float = Field(..., ge=30, le=45)
    temp_celsius_min: float = Field(..., ge=30, le=45)
    temp_celsius_std: float = Field(..., ge=0, le=2)
    spo2_mean: float = Field(..., ge=70, le=100)
    spo2_min: float = Field(..., ge=70, le=100)
    spo2_max: float = Field(..., ge=70, le=102)
    spo2_std: float = Field(..., ge=0, le=5)
    respiratory_rate_mean: float = Field(..., ge=4, le=60)
    respiratory_rate_max: float = Field(..., ge=4, le=70)
    respiratory_rate_min: float = Field(..., ge=4, le=60)
    respiratory_rate_std: float = Field(..., ge=0, le=10)

    model_config = {"extra": "forbid"}


class PredictRequest(BaseModel):
    """Single patient prediction request."""

    patient_id: int | str = Field(..., description="Unique patient identifier")
    features: PatientFeaturesRequest
    include_shap: bool = Field(True, description="Include SHAP explanation")
    include_explanation: bool = Field(True, description="Include narrative explanation")


class BatchPatientItem(BaseModel):
    """One patient in a batch request."""

    patient_id: int | str
    features: PatientFeaturesRequest


class BatchPredictRequest(BaseModel):
    """Batch prediction request (max 100 patients)."""

    patients: list[BatchPatientItem] = Field(..., min_length=1, max_length=100)
    include_shap: bool = False
    include_explanation: bool = True

    @field_validator("patients")
    @classmethod
    def unique_ids(cls, patients: list[BatchPatientItem]) -> list[BatchPatientItem]:
        ids = [str(p.patient_id) for p in patients]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate patient_id values in batch")
        return patients


class ExplainRequest(BaseModel):
    """SHAP explanation request for one patient."""

    patient_id: int | str
    features: PatientFeaturesRequest
    top_n: int = Field(5, ge=1, le=20)


class HistoryQueryParams(BaseModel):
    """Query parameters for prediction history."""

    date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    limit: int = Field(50, ge=1, le=500)
    patient_id: str | None = None


class AuditLogQueryParams(BaseModel):
    """Query parameters for audit log retrieval."""

    date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    limit: int = Field(100, ge=1, le=1000)
    prediction_label: str | None = Field(None, pattern=r"^(sepsis_alert|no_alert)$")
