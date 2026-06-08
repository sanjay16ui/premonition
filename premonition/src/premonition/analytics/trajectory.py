"""Patient trajectory analysis."""

from __future__ import annotations

from typing import Any


class PatientTrajectoryAnalyzer:
    """Analyze patient risk trajectory over time."""

    def analyze_history(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        if not history:
            return {"trend": "stable", "points": [], "velocity": 0.0, "acceleration": 0.0}

        sorted_h = sorted(history, key=lambda h: h.get("timestamp", ""))
        scores = [float(h.get("risk_score", 0)) for h in sorted_h]
        points = [
            {"timestamp": h.get("timestamp"), "risk_score": s, "prediction": h.get("prediction")}
            for h, s in zip(sorted_h, scores)
        ]

        velocity = scores[-1] - scores[0] if len(scores) > 1 else 0.0
        acceleration = 0.0
        if len(scores) >= 3:
            mid = len(scores) // 2
            first_half = scores[mid] - scores[0]
            second_half = scores[-1] - scores[mid]
            acceleration = second_half - first_half

        trend = "stable"
        if velocity > 0.1:
            trend = "deteriorating"
        elif velocity < -0.1:
            trend = "improving"
        if acceleration > 0.05:
            trend = "rapidly_deteriorating"

        return {
            "trend": trend,
            "points": points,
            "velocity": round(velocity, 4),
            "acceleration": round(acceleration, 4),
            "current_score": scores[-1],
            "peak_score": max(scores),
            "n_observations": len(scores),
        }

    def predict_trajectory(self, current_score: float, velocity: float, hours: int = 6) -> list[dict[str, Any]]:
        forecast = []
        score = current_score
        for h in range(1, hours + 1):
            score = min(max(score + velocity * 0.1, 0.0), 1.0)
            forecast.append({"hour": h, "predicted_risk_score": round(score, 4)})
        return forecast
