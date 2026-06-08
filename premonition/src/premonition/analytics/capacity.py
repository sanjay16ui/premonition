"""Capacity planning analytics."""

from __future__ import annotations

from typing import Any

from premonition.analytics.schemas import CapacityAnalytics


class CapacityPlanningAnalytics:
    """ICU occupancy and bed demand forecasting."""

    def forecast(
        self,
        current_patients: int,
        total_beds: int = 20,
        admission_rate: float = 0.5,
        discharge_rate: float = 0.3,
        high_risk_count: int = 0,
    ) -> CapacityAnalytics:
        occupancy = current_patients / max(total_beds, 1)
        surge_factor = 1 + (high_risk_count / max(current_patients, 1)) * 0.3

        forecast_24 = min((current_patients + admission_rate * 24 - discharge_rate * 24) / total_beds * surge_factor, 1.0)
        forecast_72 = min((current_patients + admission_rate * 72 - discharge_rate * 72) / total_beds * surge_factor, 1.0)

        bed_demand = []
        patients = float(current_patients)
        for hour in range(0, 73, 12):
            patients = patients + (admission_rate - discharge_rate) * 12
            patients = max(patients, 0)
            bed_demand.append({
                "hour": hour,
                "predicted_patients": round(patients, 1),
                "occupancy_pct": round(min(patients / total_beds, 1.0) * 100, 1),
            })

        surge_prob = min(forecast_72 * 0.8 + high_risk_count * 0.05, 0.95)

        return CapacityAnalytics(
            current_occupancy=round(occupancy * 100, 1),
            predicted_occupancy_24h=round(forecast_24 * 100, 1),
            predicted_occupancy_72h=round(forecast_72 * 100, 1),
            bed_demand_forecast=bed_demand,
            surge_probability=round(surge_prob, 4),
        )

    def from_realtime(self, summary: dict[str, Any], total_beds: int = 20) -> CapacityAnalytics:
        return self.forecast(
            current_patients=summary.get("current_icu_patients", 0),
            total_beds=total_beds,
            high_risk_count=summary.get("high_risk_count", 0),
        )
