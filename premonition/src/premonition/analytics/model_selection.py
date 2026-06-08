"""Dynamic model selection engine — route patients to optimal model."""

from __future__ import annotations

from typing import Any


class DynamicModelSelector:
    """
    Route predictions to the best model based on patient characteristics.

    Rules derived from clinical patterns and validation metrics:
    - High comorbidity + elderly → logistic_regression (better calibration)
    - Acute vital instability → xgboost (higher recall)
    - Moderate risk profile → random_forest (balanced)
    """

    def select(self, features: dict[str, Any]) -> tuple[str, str]:
        age = float(features.get("age", 65))
        comorbidity = float(features.get("comorbidity_count", 0))
        hr = float(features.get("hr_mean", 80))
        spo2 = float(features.get("spo2_mean", 97))
        map_val = float(features.get("map_mean", 85))

        instability = 0
        if hr > 100 or spo2 < 92 or map_val < 65:
            instability += 2
        if hr > 120 or spo2 < 88:
            instability += 2

        if instability >= 3:
            return "xgboost", "Acute vital instability — routing to highest-recall model"
        if age >= 70 and comorbidity >= 3:
            return "logistic_regression", "Elderly with comorbidities — routing to best-calibrated model"
        if comorbidity >= 2:
            return "random_forest", "Moderate comorbidity — routing to balanced ensemble tree model"
        return "logistic_regression", "Default routing to best validation performer"
