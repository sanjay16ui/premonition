#!/usr/bin/env python
"""
PREMONITION training script.

Usage
-----
    python scripts/train.py                  # train with default tier (t1)
    python scripts/train.py --tier t2        # train with labs tier
    python scripts/train.py --tier t0        # baseline-only tier
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure src is on the path when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from premonition.config.settings import get_settings
from premonition.training.pipeline import TrainingPipeline
from premonition.utils.logging import setup_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Train PREMONITION sepsis models")
    parser.add_argument(
        "--tier",
        type=str,
        default=None,
        choices=["t0", "t1", "t2"],
        help="Feature tier (default: t1 from config)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Skip saving model artifacts (for quick testing)",
    )
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(settings.log_level)

    pipeline = TrainingPipeline(tier=args.tier, settings=settings)
    result = pipeline.run(save_artifacts=not args.no_save)

    print("\n" + "=" * 60)
    print("  PREMONITION TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Tier:          {result.tier}")
    print(f"  Best model:    {result.best_model_name}")
    print(f"  Reason:        {result.selection_reason}")
    if result.test_result:
        m = result.test_result.metrics
        print(f"  Test PR-AUC:   {m.pr_auc:.4f}")
        print(f"  Test ROC-AUC:  {m.roc_auc:.4f}")
        print(f"  Test F1:       {m.f1:.4f}")
        print(f"  Test Recall:   {m.recall:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
