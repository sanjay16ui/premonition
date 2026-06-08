"""Model comparison dashboard backend."""

from __future__ import annotations

import json
from pathlib import Path

from premonition.analytics.benchmarking import ModelBenchmarkingFramework
from premonition.analytics.schemas import ModelBenchmark, ModelComparisonResult


class ModelComparisonService:
    """Compare Logistic Regression vs Random Forest vs XGBoost."""

    def __init__(self, models_dir: Path, tier: str) -> None:
        self.benchmarker = ModelBenchmarkingFramework(models_dir, tier)

    def compare(self) -> ModelComparisonResult:
        benchmarks = self.benchmarker.benchmark_all()
        if not benchmarks:
            return ModelComparisonResult(
                primary_metric="pr_auc",
                winner="unknown",
                models=[],
                recommendation="Train models first",
            )
        winner = benchmarks[0]
        rec = (
            f"Deploy '{winner.model_name}' (PR-AUC {winner.pr_auc:.4f}). "
            f"Consider ensemble for +{(benchmarks[0].pr_auc - benchmarks[-1].pr_auc) * 100:.1f}% coverage."
        )
        return ModelComparisonResult(
            primary_metric="pr_auc",
            winner=winner.model_name,
            models=benchmarks,
            recommendation=rec,
        )

    def load_selection_comparison(self) -> list[dict]:
        path = self.benchmarker.models_dir / self.benchmarker.tier / "best_model" / "metrics.json"
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("selection", {}).get("comparison", [])
