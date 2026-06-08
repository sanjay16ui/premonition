"""Automated model evaluation and comparison reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from premonition.utils.serialization import dumps_json


def compare_models(model_a_metrics: dict[str, float], model_b_metrics: dict[str, float]) -> dict[str, Any]:
    """Generate comparison report between two model metric sets."""
    all_keys = set(model_a_metrics) | set(model_b_metrics)
    comparison = {}
    winner = "tie"
    primary = "pr_auc"
    for key in sorted(all_keys):
        a = model_a_metrics.get(key, 0.0)
        b = model_b_metrics.get(key, 0.0)
        delta = round(b - a, 4)
        comparison[key] = {"model_a": a, "model_b": b, "delta": delta, "better": "b" if delta > 0 else ("a" if delta < 0 else "tie")}
    if primary in comparison:
        winner = comparison[primary]["better"]
    return {
        "metrics": comparison,
        "recommended": f"model_{winner}" if winner != "tie" else "either",
        "primary_metric": primary,
    }


def save_evaluation_report(path: Path, report: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_json(report), encoding="utf-8")
    return path


def load_metrics_from_bundle(bundle_path: Path) -> dict[str, float]:
    mf = bundle_path / "metrics.json"
    if not mf.exists():
        return {}
    data = json.loads(mf.read_text(encoding="utf-8"))
    return {k: float(v) for k, v in data.items() if isinstance(v, (int, float))}
