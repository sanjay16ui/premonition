"""SHAP explainability and patient-level reports."""

from premonition.explainability.feature_labels import categorize_feature, friendly_name
from premonition.explainability.patient_report import (
    ContributingFactor,
    PatientExplanationReport,
    PatientReportGenerator,
)
from premonition.explainability.plots import generate_all_shap_plots
from premonition.explainability.shap_explainer import (
    ShapExplanation,
    ShapExplainer,
    ShapExplainerResult,
)

__all__ = [
    "ContributingFactor",
    "PatientExplanationReport",
    "PatientReportGenerator",
    "ShapExplanation",
    "ShapExplainer",
    "ShapExplainerResult",
    "categorize_feature",
    "friendly_name",
    "generate_all_shap_plots",
]
