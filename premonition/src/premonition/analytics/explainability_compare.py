"""Explainability comparison across models."""

from __future__ import annotations

from typing import Any

from premonition.analytics.schemas import ExplainabilityComparison
from premonition.explainability.feature_labels import categorize_feature, friendly_name


class ExplainabilityComparisonEngine:
    """Compare feature importance and SHAP categories across models."""

    def compare(
        self,
        model_importances: dict[str, dict[str, float]],
        shap_categories: dict[str, dict[str, float]] | None = None,
    ) -> list[ExplainabilityComparison]:
        results = []
        for model_name, importances in model_importances.items():
            sorted_feats = sorted(importances.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
            top_features = [
                {
                    "feature": f,
                    "label": friendly_name(f),
                    "importance": round(v, 4),
                    "category": categorize_feature(f),
                }
                for f, v in sorted_feats
            ]
            category_impact: dict[str, float] = {}
            for f, v in importances.items():
                cat = categorize_feature(f)
                category_impact[cat] = category_impact.get(cat, 0.0) + abs(v)
            if shap_categories and model_name in shap_categories:
                category_impact = shap_categories[model_name]
            results.append(ExplainabilityComparison(
                model_name=model_name,
                top_features=top_features,
                category_impact={k: round(v, 4) for k, v in category_impact.items()},
            ))
        return results

    def agreement_score(self, comparisons: list[ExplainabilityComparison]) -> float:
        if len(comparisons) < 2:
            return 1.0
        top_sets = [set(c.top_features[i]["feature"] for i in range(min(5, len(c.top_features)))) for c in comparisons]
        overlap = len(top_sets[0] & top_sets[1])
        for i in range(2, len(top_sets)):
            overlap = min(overlap, len(top_sets[0] & top_sets[i]))
        return round(overlap / 5, 2)
