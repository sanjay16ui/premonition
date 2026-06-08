#!/usr/bin/env python
"""
PREMONITION explainability script.

Usage
-----
    python scripts/explain.py                    # explain test set samples
    python scripts/explain.py --patient-id 37464 # explain one patient
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from premonition.config.settings import get_settings
from premonition.data.pipeline import DataPipeline
from premonition.explainability.pipeline import ExplainabilityPipeline
from premonition.intelligence.predictor import PredictionIntelligence
from premonition.utils.logging import setup_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SHAP explanations")
    parser.add_argument("--tier", type=str, default=None, choices=["t0", "t1", "t2"])
    parser.add_argument("--patient-id", type=int, default=None, help="Explain one patient")
    parser.add_argument("--n-samples", type=int, default=5, help="Number of sample patients")
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(settings.log_level)
    tier = args.tier or settings.primary_tier

    if args.patient_id:
        _explain_single_patient(tier, args.patient_id, settings)
    else:
        pipeline = ExplainabilityPipeline(tier=tier, settings=settings)
        result = pipeline.run(n_sample_patients=args.n_samples)

        print("\n" + "=" * 60)
        print("  EXPLAINABILITY COMPLETE")
        print("=" * 60)
        print(f"  Model:     {result.model_name}")
        print(f"  Tier:      {result.tier}")
        print(f"  Reports:   {len(result.patient_reports)} patient reports")
        print(f"  SHAP dirs: {list(result.shap_plot_paths.keys())}")
        print("=" * 60)

        if result.sample_predictions:
            print("\nSample Patient Report:")
            top = result.sample_predictions[0]
            print(f"  Patient ID: {top['patient_id']}")
            print(f"  Risk:       {top['risk_pct']}")
            print(f"  Confidence: {top['confidence']}")
            for f in top["top_factors"]:
                sign = "+" if f["direction"] == "increased" else "-"
                print(f"    {f['rank']}. {f['feature']} ({sign}{f['contribution_pct']}%)")


def _explain_single_patient(tier: str, patient_id: int, settings) -> None:
    data = DataPipeline(tier=tier, settings=settings).run(save_artifacts=False)
    intel = PredictionIntelligence(tier=tier, settings=settings)
    intel.load()
    intel.set_background(data.X_train_processed)

    test_df = data.splits.test
    row = test_df[test_df["subject_id"] == patient_id]
    if row.empty:
        row = data.splits.val[data.splits.val["subject_id"] == patient_id]
    if row.empty:
        print(f"Patient {patient_id} not found in val/test splits.")
        return

    feature_cols = [c for c in row.columns if c not in {"subject_id", "sepsis_label"}]
    result = intel.predict_patient(row[feature_cols], patient_id=patient_id)
    print(result.patient_report.to_text())


if __name__ == "__main__":
    main()
