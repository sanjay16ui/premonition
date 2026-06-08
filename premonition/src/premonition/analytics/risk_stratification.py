"""Risk stratification engine."""

from __future__ import annotations

from typing import Any

from premonition.analytics.schemas import RiskStratificationResult, RiskTier


class RiskStratificationEngine:
    """Stratify patients into clinical risk tiers."""

    DEFAULT_THRESHOLDS = {
        "low": 0.15,
        "moderate": 0.35,
        "high": 0.55,
        "critical": 0.75,
    }

    def stratify(
        self,
        risk_scores: list[float],
        thresholds: dict[str, float] | None = None,
    ) -> RiskStratificationResult:
        t = thresholds or self.DEFAULT_THRESHOLDS
        tiers_def = [
            ("low", 0.0, t["low"]),
            ("moderate", t["low"], t["moderate"]),
            ("high", t["moderate"], t["high"]),
            ("critical", t["high"], 1.0),
        ]
        counts = {name: 0 for name, _, _ in tiers_def}
        for score in risk_scores:
            for name, lo, hi in tiers_def:
                if lo <= score < hi or (name == "critical" and score >= t["high"]):
                    counts[name] += 1
                    break

        total = len(risk_scores) or 1
        tiers = [
            RiskTier(
                tier=name,
                count=counts[name],
                percentage=round(counts[name] / total * 100, 2),
                score_range=f"{lo:.2f}-{hi:.2f}",
            )
            for name, lo, hi in tiers_def
        ]
        return RiskStratificationResult(
            tiers=tiers,
            total_patients=len(risk_scores),
            distribution={t.tier: t.percentage for t in tiers},
        )

    def stratify_from_predictions(self, predictions: list[dict[str, Any]]) -> RiskStratificationResult:
        scores = [float(p.get("risk_score", 0)) for p in predictions]
        return self.stratify(scores)
