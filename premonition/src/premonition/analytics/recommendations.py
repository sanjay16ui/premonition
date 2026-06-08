"""Clinical recommendation ranking engine."""

from __future__ import annotations

from premonition.analytics.schemas import ClinicalRecommendation, RecommendationRequest


class ClinicalRecommendationRanker:
    """Rank clinical actions by priority and evidence."""

    ACTION_CATALOG = [
        ("obtain_blood_cultures", "Obtain blood cultures before antibiotics", "high", "Sepsis-3 bundle"),
        ("broad_spectrum_abx", "Initiate broad-spectrum antibiotics within 1 hour", "critical", "Surviving Sepsis Campaign"),
        ("lactate_measurement", "Measure serum lactate level", "high", "Sepsis-3 criteria"),
        ("fluid_resuscitation", "Begin IV fluid resuscitation (30 mL/kg)", "high", "SSC guidelines"),
        ("repeat_vitals", "Increase vital sign monitoring frequency to q15min", "moderate", "ICU early warning"),
        ("icu_consult", "Request ICU consultation", "high", "Escalation protocol"),
        ("vasopressor_prep", "Prepare vasopressor infusion", "critical", "Hemodynamic instability"),
        ("source_control", "Evaluate for source control intervention", "moderate", "SSC bundle"),
    ]

    def rank(self, request: RecommendationRequest) -> list[ClinicalRecommendation]:
        risk = request.risk_score or 0.3
        factors = set(request.top_factors)
        recommendations: list[ClinicalRecommendation] = []

        for i, (action_id, action, base_priority, evidence) in enumerate(self.ACTION_CATALOG):
            priority = base_priority
            rationale = evidence

            if risk >= 0.55 and action_id in {"broad_spectrum_abx", "vasopressor_prep", "icu_consult"}:
                priority = "critical"
                rationale = f"High risk ({risk:.2f}) — urgent {action.lower()}"
            elif risk >= 0.35 and action_id in {"obtain_blood_cultures", "lactate_measurement", "fluid_resuscitation"}:
                priority = "high"
                rationale = f"Elevated risk ({risk:.2f}) — {evidence}"

            if "spo2" in str(factors).lower() or "hypoxemia" in factors:
                if action_id == "fluid_resuscitation":
                    priority = "critical"
                    rationale = "Hypoxemia detected — prioritize fluid resuscitation"

            score = self._priority_score(priority)
            recommendations.append((score, ClinicalRecommendation(
                rank=0,
                action=action,
                priority=priority,
                rationale=rationale,
                evidence_level="guideline",
            )))

        recommendations.sort(key=lambda x: x[0], reverse=True)
        return [
            ClinicalRecommendation(rank=i + 1, **rec.model_dump(exclude={"rank"}))
            for i, (_, rec) in enumerate(recommendations[:6])
        ]

    def _priority_score(self, priority: str) -> int:
        return {"critical": 4, "high": 3, "moderate": 2, "low": 1}.get(priority, 0)
