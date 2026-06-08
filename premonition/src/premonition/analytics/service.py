"""Analytics service facade — orchestrates all analytics engines."""

from __future__ import annotations

from typing import Any

import pandas as pd

from premonition.analytics.alert_prioritization import AlertPrioritizationAI
from premonition.analytics.benchmarking import ModelBenchmarkingFramework
from premonition.analytics.clinical_rules import ClinicalRuleEngine
from premonition.analytics.cohorts import CohortAnalysisEngine
from premonition.analytics.comparison import ModelComparisonService
from premonition.analytics.decision_audit import AIDecisionAuditFramework
from premonition.analytics.ensemble import EnsembleEngine
from premonition.analytics.escalation import SmartEscalationWorkflow
from premonition.analytics.executive import ExecutiveIntelligenceService
from premonition.analytics.explainability_compare import ExplainabilityComparisonEngine
from premonition.analytics.kpis import HospitalKPIEngine
from premonition.analytics.model_selection import DynamicModelSelector
from premonition.analytics.operational import OperationalAnalyticsService
from premonition.analytics.outcomes import OutcomePredictionFramework
from premonition.analytics.population import PopulationHealthAnalytics
from premonition.analytics.capacity import CapacityPlanningAnalytics
from premonition.analytics.recommendations import ClinicalRecommendationRanker
from premonition.analytics.resources import ResourceUtilizationAnalytics
from premonition.analytics.risk_stratification import RiskStratificationEngine
from premonition.analytics.schemas import (
    CohortAnalysisRequest,
    OutcomePredictionRequest,
    RecommendationRequest,
    RiskStratificationRequest,
    SimulateRequest,
)
from premonition.analytics.trajectory import PatientTrajectoryAnalyzer
from premonition.api.schemas.requests import PatientFeaturesRequest
from premonition.api.schemas.validation import features_to_dataframe, prepare_tier_features
from premonition.features.feature_registry import FeatureRegistry
from premonition.config.settings import Settings
from premonition.models.registry import ModelRegistry
from premonition.models.prediction_logger import PredictionLogger
from premonition.utils.logging import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Enterprise analytics and decision-support platform."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.registry = ModelRegistry(settings.models_dir)
        self.prediction_logger = PredictionLogger(settings.logs_dir)

        self.ensemble = EnsembleEngine(self.registry, settings.primary_tier)
        self.model_selector = DynamicModelSelector()
        self.benchmarker = ModelBenchmarkingFramework(settings.models_dir, settings.primary_tier)
        self.comparison = ModelComparisonService(settings.models_dir, settings.primary_tier)
        self.explain_compare = ExplainabilityComparisonEngine()
        self.decision_audit = AIDecisionAuditFramework()
        self.clinical_rules = ClinicalRuleEngine()
        self.risk_stratifier = RiskStratificationEngine()
        self.population = PopulationHealthAnalytics()
        self.cohorts = CohortAnalysisEngine()
        self.outcomes = OutcomePredictionFramework()
        self.trajectory = PatientTrajectoryAnalyzer()
        self.recommendations = ClinicalRecommendationRanker()
        self.alert_prioritizer = AlertPrioritizationAI()
        self.escalation = SmartEscalationWorkflow()
        self.executive = ExecutiveIntelligenceService()
        self.operational = OperationalAnalyticsService()
        self.capacity = CapacityPlanningAnalytics()
        self.resources = ResourceUtilizationAnalytics()
        self.kpis = HospitalKPIEngine()

    def _load_dataset(self, nrows: int | None = None) -> pd.DataFrame:
        path = self.settings.dataset_path
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(path, nrows=nrows)

    def _prediction_logs(self) -> list[dict[str, Any]]:
        return self.prediction_logger.read_log()

    def _model_metrics(self) -> dict[str, Any]:
        return self.executive.load_model_metrics(self.settings.models_dir, self.settings.primary_tier)

    def get_executive(self, realtime_summary: dict | None = None, metrics_collector: dict | None = None) -> dict:
        return self.executive.build(
            realtime_summary=realtime_summary,
            prediction_logs=self._prediction_logs(),
            model_metrics=self._model_metrics(),
            metrics_collector=metrics_collector or {},
        ).model_dump()

    def get_population(self) -> dict:
        df = self._load_dataset()
        return self.population.analyze(df).model_dump()

    def get_cohorts(self, request: CohortAnalysisRequest | None = None) -> list[dict]:
        df = self._load_dataset()
        req = request or CohortAnalysisRequest()
        return [s.model_dump() for s in self.cohorts.analyze(df, req, feature_config=self.settings.feature_config)]

    def get_outcomes(self, request: OutcomePredictionRequest) -> list[dict]:
        risk = 0.3
        features = request.patient_features or {}
        if features:
            rules = self.clinical_rules.clinical_score(features, risk)
            risk = rules
        return [p.model_dump() for p in self.outcomes.predict(request, risk, features)]

    def get_capacity(self, realtime_summary: dict | None = None) -> dict:
        if realtime_summary:
            return self.capacity.from_realtime(realtime_summary).model_dump()
        return self.capacity.forecast(current_patients=10).model_dump()

    def get_resources(self, realtime_summary: dict | None = None) -> dict:
        summary = realtime_summary or {}
        return self.resources.analyze(
            icu_patients=summary.get("current_icu_patients", 10),
            high_risk=summary.get("high_risk_count", 2),
            critical_alerts=summary.get("critical_alert_count", 0),
        ).model_dump()

    def get_kpis(self, metrics_collector: dict | None = None) -> dict:
        df = self._load_dataset(nrows=100)
        sepsis_rate = float(df["sepsis_label"].mean()) if "sepsis_label" in df.columns and len(df) > 0 else 0.15
        return self.kpis.compute(
            prediction_logs=self._prediction_logs(),
            model_metrics=self._model_metrics(),
            metrics_collector=metrics_collector or {},
            dataset_sepsis_rate=sepsis_rate,
        ).model_dump()

    def simulate(self, request: SimulateRequest) -> dict[str, Any]:
        params = request.parameters
        if request.scenario == "icu_surge":
            return self.capacity.forecast(
                current_patients=int(params.get("patients", 18)),
                total_beds=int(params.get("beds", 20)),
                admission_rate=float(params.get("admission_rate", 0.8)),
                high_risk_count=int(params.get("high_risk", 5)),
            ).model_dump()
        if request.scenario == "sepsis_outbreak":
            df = self._load_dataset(nrows=200)
            base_rate = float(df["sepsis_label"].mean()) if "sepsis_label" in df.columns else 0.15
            return {
                "scenario": request.scenario,
                "baseline_sepsis_rate": base_rate,
                "projected_rate": round(base_rate * float(params.get("multiplier", 1.5)), 4),
                "additional_alerts": int(params.get("patients", 20) * base_rate * 1.5),
            }
        return {"scenario": request.scenario, "status": "simulated", "parameters": params}

    def compare_models(self) -> dict:
        return self.comparison.compare().model_dump()

    def get_recommendations(self, request: RecommendationRequest) -> list[dict]:
        return [r.model_dump() for r in self.recommendations.rank(request)]

    def risk_stratification(self, request: RiskStratificationRequest | None = None) -> dict:
        logs = self._prediction_logs()
        if request and request.patient_ids:
            logs = [l for l in logs if l.get("patient_id") in request.patient_ids]
        scores = [float(l.get("risk_score", 0)) for l in logs]
        if not scores:
            df = self._load_dataset(nrows=500)
            if "sepsis_label" in df.columns:
                scores = [0.1 + float(r) * 0.6 for r in df["sepsis_label"].head(100)]
            else:
                scores = [0.2, 0.35, 0.5, 0.15, 0.75]
        return self.risk_stratifier.stratify(scores, request.thresholds if request else None).model_dump()

    def cohort_analysis(self, request: CohortAnalysisRequest) -> list[dict]:
        return self.get_cohorts(request)

    def outcome_prediction(self, request: OutcomePredictionRequest) -> list[dict]:
        return self.get_outcomes(request)

    def ensemble_predict(self, features: dict[str, Any], model: Any | None = None) -> dict:
        registry = FeatureRegistry(self.settings.feature_config)
        req = PatientFeaturesRequest(**{k: v for k, v in features.items() if k != "patient_id"})
        df = features_to_dataframe(req)
        X = prepare_tier_features(df, registry, self.settings.primary_tier)
        selected, reason = self.model_selector.select(features)
        primary_score = None
        if model and model.is_fitted:
            try:
                primary_score = float(model.predict_proba(X)[0])
            except Exception:
                pass
        result = self.ensemble.predict(X, primary_model=model, primary_score=primary_score)
        rules = self.clinical_rules.triggered_names(features, result.ensemble_score)
        self.decision_audit.record(
            patient_id=features.get("patient_id", "unknown"),
            model_name=result.method,
            risk_score=result.ensemble_score,
            prediction=result.ensemble_prediction,
            selected_model=selected,
            routing_reason=reason,
            clinical_rules=rules,
            ensemble_used=True,
        )
        return result.model_dump()

    def get_operational(self, metrics_collector: dict | None = None) -> dict:
        return self.operational.report(
            prediction_logs=self._prediction_logs(),
            alert_logs=[],
            metrics=metrics_collector or {},
        )

    def get_benchmarks(self) -> dict:
        return self.benchmarker.summary()

    def get_explainability_comparison(self, model: Any | None = None) -> dict:
        importances: dict[str, dict[str, float]] = {}
        if model and model.is_fitted:
            importances[model.name] = model.get_feature_importance()
        benchmarks = self.benchmarker.benchmark_all()
        for b in benchmarks:
            if b.model_name not in importances:
                importances[b.model_name] = {f"feature_{i}": 0.1 / (i + 1) for i in range(10)}
        comparisons = self.explain_compare.compare(importances)
        return {
            "comparisons": [c.model_dump() for c in comparisons],
            "agreement_score": self.explain_compare.agreement_score(comparisons),
        }

    def prioritize_alerts(self, alerts: list[dict]) -> list[dict]:
        return self.alert_prioritizer.prioritize(alerts)

    def evaluate_escalation(self, risk_score: float, velocity: float, alert_level: str) -> dict:
        return self.escalation.evaluate(risk_score, velocity, alert_level)

    def patient_trajectory(self, patient_id: str) -> dict:
        logs = [l for l in self._prediction_logs() if str(l.get("patient_id")) == str(patient_id)]
        return self.trajectory.analyze_history(logs)

    def decision_audit_summary(self) -> dict:
        return self.decision_audit.summary()
