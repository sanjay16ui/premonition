"""Human-readable clinical labels for model features."""

from __future__ import annotations

# Maps internal feature names -> clinician-friendly display names
FEATURE_LABELS: dict[str, str] = {
    # Demographics
    "age": "Age",
    "gender": "Gender",
    "weight_kg": "Weight",
    "height_cm": "Height",
    "bmi": "BMI",
    "ethnicity": "Ethnicity",
    "insurance": "Insurance Type",
    # Comorbidities
    "diabetes": "Diabetes",
    "hypertension": "Hypertension",
    "chf": "Congestive Heart Failure",
    "copd": "COPD",
    "chronic_kidney_disease": "Chronic Kidney Disease",
    "liver_disease": "Liver Disease",
    "immunosuppression": "Immunosuppression",
    "cad": "Coronary Artery Disease",
    "atrial_fibrillation": "Atrial Fibrillation",
    "cancer_active": "Active Cancer",
    "comorbidity_count": "Comorbidity Burden",
    # Vitals
    "hr_mean": "Mean Heart Rate",
    "hr_max": "Peak Heart Rate",
    "hr_min": "Minimum Heart Rate",
    "hr_std": "Heart Rate Variability",
    "hr_range": "Heart Rate Range",
    "sbp_mean": "Mean Systolic BP",
    "sbp_max": "Peak Systolic BP",
    "sbp_min": "Minimum Systolic BP",
    "sbp_std": "Blood Pressure Variability",
    "sbp_range": "Systolic BP Range",
    "dbp_mean": "Mean Diastolic BP",
    "map_mean": "Mean Arterial Pressure",
    "temp_celsius_mean": "Mean Temperature",
    "temp_celsius_max": "Peak Temperature",
    "temp_celsius_min": "Minimum Temperature",
    "temp_celsius_std": "Temperature Variability",
    "temp_range": "Temperature Range",
    "spo2_mean": "Mean Oxygen Saturation",
    "spo2_min": "Minimum Oxygen Saturation",
    "spo2_std": "Oxygen Saturation Variability",
    "spo2_range": "Oxygen Saturation Range",
    "respiratory_rate_mean": "Mean Respiratory Rate",
    "respiratory_rate_max": "Peak Respiratory Rate",
    "respiratory_rate_std": "Respiratory Instability",
    "respiratory_rate_range": "Respiratory Rate Range",
    # Engineered
    "shock_index": "Shock Index",
    "pulse_pressure": "Pulse Pressure",
    # Labs
    "wbc": "White Blood Cell Count",
    "lactate_mmol": "Lactate Level",
    "creatinine": "Creatinine",
    "platelet_count": "Platelet Count",
    "glucose": "Blood Glucose",
    "ph_arterial": "Arterial pH",
    "inr": "INR",
    "sodium": "Sodium",
    "potassium": "Potassium",
    "hemoglobin": "Hemoglobin",
    # Admin
    "hospital_admit_source": "Admission Source",
    "icu_admit_time_hour": "ICU Admit Hour",
    "day_of_week": "Day of Week",
}


def friendly_name(feature: str) -> str:
    """
    Return a clinician-friendly name for a feature.

    Handles one-hot encoded names like 'gender_M' -> 'Gender (M)'.
    """
    if feature in FEATURE_LABELS:
        return FEATURE_LABELS[feature]

    for prefix, label in FEATURE_LABELS.items():
        if feature.startswith(f"{prefix}_"):
            suffix = feature[len(prefix) + 1 :]
            return f"{label} ({suffix})"

    if feature.endswith("_missing"):
        base = feature.replace("_missing", "")
        return f"{friendly_name(base)} (Missing)"

    return feature.replace("_", " ").title()


def categorize_feature(feature: str) -> str:
    """Group a feature into a clinical category for narrative explanations."""
    base = feature.split("_")[0] if "_" in feature else feature

    vital_prefixes = {"hr", "sbp", "dbp", "map", "temp", "spo2", "respiratory"}
    lab_features = {
        "wbc", "lactate", "creatinine", "platelet", "glucose", "ph", "inr",
        "sodium", "potassium", "hemoglobin", "bilirubin", "bicarbonate",
        "chloride", "hematocrit",
    }

    if any(feature.startswith(p) for p in vital_prefixes) or feature in {
        "shock_index", "pulse_pressure", "hr_range", "sbp_range",
        "temp_range", "spo2_range", "respiratory_rate_range",
    }:
        return "Vital Signs"
    if base in lab_features or feature.endswith("_missing"):
        return "Laboratory"
    if feature in {
        "diabetes", "hypertension", "chf", "copd", "chronic_kidney_disease",
        "liver_disease", "immunosuppression", "cad", "atrial_fibrillation",
        "cancer_active", "comorbidity_count",
    }:
        return "Comorbidities"
    if feature in {"age", "gender", "weight_kg", "height_cm", "bmi", "ethnicity", "insurance"}:
        return "Demographics"
    return "Other"
