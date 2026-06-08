"""Model benchmarking framework."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from premonition.analytics.schemas import ModelBenchmark


class ModelBenchmarkingFramework:
    """Load and rank model performance from artifact metrics."""

    def __init__(self, models_dir: Path, tier: str) -> None:
        self.models_dir = models_dir
        self.tier = tier

    def _load_bundle_metrics(self, bundle: Path) -> dict[str, Any] | None:
        mf = bundle / "metrics.json"
        if not mf.exists():
            return None
        data = json.loads(mf.read_text(encoding="utf-8"))
        return data.get("validation", data)

    def benchmark_all(self) -> list[ModelBenchmark]:
        tier_dir = self.models_dir / self.tier
        seen: set[str] = set()
        benchmarks: list[ModelBenchmark] = []

        if not tier_dir.exists():
            return benchmarks

        for bundle in sorted(tier_dir.iterdir()):
            metrics = self._load_bundle_metrics(bundle)
            if not metrics:
                continue
            name = metrics.get("model_name", bundle.name)
            if name in seen:
                continue
            seen.add(name)
            benchmarks.append(ModelBenchmark(
                model_name=name,
                pr_auc=float(metrics.get("pr_auc", 0)),
                roc_auc=float(metrics.get("roc_auc", 0)),
                f1=float(metrics.get("f1", 0)),
                precision=float(metrics.get("precision", 0)),
                recall=float(metrics.get("recall", 0)),
                brier_score=float(metrics.get("brier_score", 0)),
            ))

        benchmarks.sort(key=lambda b: b.pr_auc, reverse=True)
        for i, b in enumerate(benchmarks, 1):
            b.rank = i
        return benchmarks

    def summary(self) -> dict[str, Any]:
        benchmarks = self.benchmark_all()
        if not benchmarks:
            return {"models": [], "winner": None}
        return {
            "models": [b.model_dump() for b in benchmarks],
            "winner": benchmarks[0].model_name,
            "primary_metric": "pr_auc",
            "spread": round(benchmarks[0].pr_auc - benchmarks[-1].pr_auc, 4) if len(benchmarks) > 1 else 0,
        }
