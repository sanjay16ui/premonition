"""Simulated real-time ICU vitals generator."""

from __future__ import annotations

import random
from copy import deepcopy
from typing import Any

import pandas as pd

from premonition.api.schemas.requests import PatientFeaturesRequest
from premonition.realtime.schemas import VitalsSnapshot


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def compute_shock_index(hr: float, sbp: float) -> float:
    return round(hr / max(sbp, 1.0), 3)


class VitalsSimulator:
    """
    Simulate live ICU vital sign updates.

    Each tick applies small random drift with occasional deterioration
    patterns to trigger alert engine testing.
    """

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)
        self._deterioration_patients: set[str] = set()

    def load_patients_from_dataset(
        self,
        dataset_path: str,
        max_patients: int,
    ) -> dict[str, PatientFeaturesRequest]:
        df = pd.read_csv(dataset_path, nrows=max_patients * 2)
        patients: dict[str, PatientFeaturesRequest] = {}

        feature_cols = set(PatientFeaturesRequest.model_fields.keys())
        for _, row in df.iterrows():
            pid = str(int(row["subject_id"]))
            if pid in patients:
                continue
            data: dict[str, Any] = {}
            for col in feature_cols:
                if col == "subject_id":
                    data[col] = pid
                    continue
                if col not in row.index:
                    continue
                val = row[col]
                if pd.isna(val):
                    data[col] = None
                elif col == "gender":
                    data[col] = str(val)
                elif col in {"age", "icu_admit_time_hour", "day_of_week"}:
                    data[col] = int(val)
                elif col in {
                    "diabetes", "hypertension", "chf", "copd",
                    "chronic_kidney_disease", "liver_disease", "immunosuppression",
                    "cad", "atrial_fibrillation", "cancer_active",
                }:
                    data[col] = int(val)
                else:
                    data[col] = float(val) if isinstance(val, float) else val
            try:
                patients[pid] = PatientFeaturesRequest(**data)
            except Exception:
                continue
            if len(patients) >= max_patients:
                break

        # Mark ~30% for simulated deterioration
        pids = list(patients.keys())
        n = max(1, len(pids) // 3)
        self._deterioration_patients = set(self._rng.sample(pids, min(n, len(pids))))
        return patients

    def tick(self, patient_id: str, features: PatientFeaturesRequest) -> PatientFeaturesRequest:
        """Apply one vitals update cycle."""
        updated = deepcopy(features)
        deteriorating = patient_id in self._deterioration_patients
        drift = 1.5 if deteriorating else 0.8

        updated.hr_mean = _clamp(
            updated.hr_mean + self._rng.uniform(-drift, drift + (2 if deteriorating else 0)),
            40, 180,
        )
        updated.hr_max = _clamp(updated.hr_mean + self._rng.uniform(5, 15), 50, 200)
        updated.hr_min = _clamp(updated.hr_mean - self._rng.uniform(5, 12), 35, 160)
        updated.hr_std = _clamp(updated.hr_std + self._rng.uniform(-0.3, 0.5), 0, 25)

        sbp_delta = self._rng.uniform(-3, 1) if deteriorating else self._rng.uniform(-2, 2)
        updated.sbp_mean = _clamp(updated.sbp_mean + sbp_delta, 70, 200)
        updated.sbp_max = _clamp(updated.sbp_mean + self._rng.uniform(5, 15), 80, 220)
        updated.sbp_min = _clamp(updated.sbp_mean - self._rng.uniform(5, 15), 60, 190)
        updated.sbp_std = _clamp(updated.sbp_std + self._rng.uniform(-0.2, 0.4), 0, 25)

        updated.dbp_mean = _clamp(updated.dbp_mean + self._rng.uniform(-2, 2), 40, 120)
        updated.dbp_max = _clamp(updated.dbp_max + self._rng.uniform(-2, 3), 45, 130)
        updated.dbp_min = _clamp(updated.dbp_min + self._rng.uniform(-2, 2), 35, 110)

        spo2_delta = self._rng.uniform(-1.5, 0.3) if deteriorating else self._rng.uniform(-0.8, 0.8)
        updated.spo2_mean = _clamp(updated.spo2_mean + spo2_delta, 85, 100)
        updated.spo2_min = _clamp(updated.spo2_min + spo2_delta * 0.8, 80, 100)
        updated.spo2_max = _clamp(updated.spo2_max + self._rng.uniform(-0.3, 0.5), 88, 100)

        temp_delta = self._rng.uniform(-0.05, 0.15) if deteriorating else self._rng.uniform(-0.1, 0.1)
        updated.temp_celsius_mean = _clamp(updated.temp_celsius_mean + temp_delta, 35.5, 40.5)
        updated.temp_celsius_max = _clamp(updated.temp_celsius_max + temp_delta, 36, 41)
        updated.temp_celsius_min = _clamp(updated.temp_celsius_min + temp_delta * 0.5, 35, 40)

        rr_delta = self._rng.uniform(-0.5, 1.5) if deteriorating else self._rng.uniform(-1, 1)
        updated.respiratory_rate_mean = _clamp(updated.respiratory_rate_mean + rr_delta, 8, 40)
        updated.respiratory_rate_max = _clamp(updated.respiratory_rate_max + rr_delta, 10, 45)
        updated.respiratory_rate_min = _clamp(updated.respiratory_rate_min + rr_delta * 0.5, 6, 35)

        return updated

    def to_vitals_snapshot(self, features: PatientFeaturesRequest) -> VitalsSnapshot:
        return VitalsSnapshot(
            hr_mean=features.hr_mean,
            sbp_mean=features.sbp_mean,
            dbp_mean=features.dbp_mean,
            spo2_mean=features.spo2_mean,
            temp_celsius_mean=features.temp_celsius_mean,
            respiratory_rate_mean=features.respiratory_rate_mean,
            shock_index=compute_shock_index(features.hr_mean, features.sbp_mean),
        )
