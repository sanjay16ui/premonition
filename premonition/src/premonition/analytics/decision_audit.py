"""AI decision audit framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AIDecisionRecord:
    decision_id: str
    patient_id: str
    model_name: str
    ensemble_used: bool
    risk_score: float
    prediction: int
    selected_model: str
    routing_reason: str
    top_factors: list[str]
    clinical_rules_triggered: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "patient_id": self.patient_id,
            "model_name": self.model_name,
            "ensemble_used": self.ensemble_used,
            "risk_score": self.risk_score,
            "prediction": self.prediction,
            "selected_model": self.selected_model,
            "routing_reason": self.routing_reason,
            "top_factors": self.top_factors,
            "clinical_rules_triggered": self.clinical_rules_triggered,
            "timestamp": self.timestamp,
        }


class AIDecisionAuditFramework:
    """Track and query AI decision provenance for compliance."""

    def __init__(self) -> None:
        self._records: list[AIDecisionRecord] = []
        self._counter = 0

    def record(
        self,
        patient_id: str,
        model_name: str,
        risk_score: float,
        prediction: int,
        selected_model: str,
        routing_reason: str,
        top_factors: list[str] | None = None,
        clinical_rules: list[str] | None = None,
        ensemble_used: bool = False,
    ) -> AIDecisionRecord:
        self._counter += 1
        rec = AIDecisionRecord(
            decision_id=f"dec-{self._counter:06d}",
            patient_id=str(patient_id),
            model_name=model_name,
            ensemble_used=ensemble_used,
            risk_score=risk_score,
            prediction=prediction,
            selected_model=selected_model,
            routing_reason=routing_reason,
            top_factors=top_factors or [],
            clinical_rules_triggered=clinical_rules or [],
        )
        self._records.append(rec)
        return rec

    def query(self, patient_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        records = self._records
        if patient_id:
            records = [r for r in records if r.patient_id == str(patient_id)]
        return [r.to_dict() for r in records[-limit:]]

    def summary(self) -> dict[str, Any]:
        if not self._records:
            return {"total_decisions": 0}
        models = {}
        rules = {}
        for r in self._records:
            models[r.selected_model] = models.get(r.selected_model, 0) + 1
            for rule in r.clinical_rules_triggered:
                rules[rule] = rules.get(rule, 0) + 1
        return {
            "total_decisions": len(self._records),
            "model_routing": models,
            "rules_triggered": rules,
            "ensemble_rate": sum(1 for r in self._records if r.ensemble_used) / len(self._records),
        }
