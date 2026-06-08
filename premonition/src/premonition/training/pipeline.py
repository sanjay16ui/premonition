"""End-to-end training pipeline — data → train → validate → select → test → save."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from premonition.config.settings import Settings, get_settings
from premonition.data.pipeline import DataPipeline, DataPipelineResult
from premonition.models.registry import ModelArtifact, ModelRegistry
from premonition.training.evaluator import EvaluationResult, ModelEvaluator
from premonition.training.metrics import compare_models, resolve_metric_name, select_best_model
from premonition.training.trainer import ModelTrainer, TrainedModel
from premonition.training.visualizations import plot_metrics_comparison
from premonition.utils.logging import get_logger, setup_logging
from premonition.utils.paths import ensure_dir, timestamp_slug
from premonition.utils.serialization import dumps_json

logger = get_logger(__name__)


@dataclass
class TrainingPipelineResult:
    """Complete output of the Phase 1 training run."""

    tier: str
    data: DataPipelineResult
    trained_models: list[TrainedModel]
    val_results: list[EvaluationResult]
    test_result: EvaluationResult | None
    best_model_name: str
    selection_reason: str
    artifacts: list[ModelArtifact] = field(default_factory=list)
    comparison: list[dict[str, Any]] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "best_model": self.best_model_name,
            "selection_reason": self.selection_reason,
            "n_train": len(self.data.y_train),
            "n_val": len(self.data.y_val),
            "n_test": len(self.data.y_test),
            "val_comparison": self.comparison,
            "test_metrics": (
                self.test_result.metrics.to_dict() if self.test_result else None
            ),
        }


class TrainingPipeline:
    """
    Orchestrate the full Phase 1 training workflow.

    How it works (simple)
    -----------------------
    Step 1  →  Run Section 3 data pipeline (load, validate, engineer, split, preprocess)
    Step 2  →  Train 3 models on TRAIN split only
    Step 3  →  Evaluate all 3 on VALIDATION split
    Step 4  →  Compare metrics, pick winner by PR-AUC
    Step 5  →  Evaluate winner on TEST split (used only once, no peeking)
    Step 6  →  Save all models + metrics + plots

    Why PR-AUC for selection?
    -------------------------
    Our dataset is imbalanced (15% sepsis). Accuracy can look good (85%)
    while missing most sepsis cases. PR-AUC focuses on the minority class.
    """

    def __init__(
        self,
        tier: str | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.tier = tier or self.settings.primary_tier
        self.primary_metric = (
            self.settings.model_config.get("evaluation", {}).get(
                "primary_metric", "pr_auc"
            )
        )

    def run(self, save_artifacts: bool = True) -> TrainingPipelineResult:
        """Execute the complete training pipeline."""
        setup_logging(self.settings.log_level)
        stamp = timestamp_slug()
        reports_dir = ensure_dir(self.settings.reports_dir / self.tier / stamp)
        registry = ModelRegistry(self.settings.models_dir)

        # ── Step 1: Data pipeline (Section 3) ──────────────────────────
        logger.info("=== STEP 1: Data Pipeline (tier=%s) ===", self.tier)
        data = DataPipeline(tier=self.tier, settings=self.settings).run(
            save_artifacts=save_artifacts
        )

        # ── Step 2: Train all models on TRAIN split ────────────────────
        logger.info("=== STEP 2: Training Models ===")
        trainer = ModelTrainer(self.settings.model_config)
        trained_models = trainer.train_all(data)

        # ── Step 3: Evaluate on VALIDATION split ───────────────────────
        logger.info("=== STEP 3: Validation Evaluation ===")
        evaluator = ModelEvaluator(reports_dir=reports_dir)
        val_results: list[EvaluationResult] = []

        for tm in trained_models:
            result = evaluator.evaluate(
                model=tm.model,
                X=data.X_val_processed,
                y=data.y_val.values,
                split="val",
            )
            val_results.append(result)

        evaluator.print_metrics_table(val_results)

        val_metrics = [r.metrics for r in val_results]
        comparison = compare_models(val_metrics, primary_metric=self.primary_metric)

        plot_metrics_comparison(
            comparison,
            reports_dir / "model_comparison_val.png",
            split="val",
        )

        # ── Step 4: Select best model by PR-AUC ────────────────────────
        logger.info("=== STEP 4: Model Selection (metric=%s) ===", self.primary_metric)
        best_name = select_best_model(val_metrics, primary_metric=self.primary_metric)
        metric_attr = resolve_metric_name(self.primary_metric)
        best_val_score = next(
            m for m in val_metrics if m.model_name == best_name
        )
        selection_reason = (
            f"Selected '{best_name}' with highest validation {self.primary_metric} "
            f"= {getattr(best_val_score, metric_attr):.4f}"
        )
        logger.info(selection_reason)

        # Explain XGBoost outcome
        xgb_metrics = next(
            (m for m in val_metrics if m.model_name == "xgboost"), None
        )
        if xgb_metrics and best_name == "xgboost":
            logger.info(
                "XGBoost SELECTED — best validation PR-AUC (%.4f). "
                "Handles imbalance and non-linear vital patterns well.",
                xgb_metrics.pr_auc,
            )
        elif xgb_metrics:
            logger.info(
                "XGBoost NOT selected — validation PR-AUC=%.4f vs winner '%s'=%.4f",
                xgb_metrics.pr_auc,
                best_name,
                getattr(best_val_score, metric_attr),
            )

        # ── Step 5: Final TEST evaluation (winner only) ────────────────
        logger.info("=== STEP 5: Test Evaluation (best model only) ===")
        best_trained = next(tm for tm in trained_models if tm.model.name == best_name)
        test_result = evaluator.evaluate(
            model=best_trained.model,
            X=data.X_test_processed,
            y=data.y_test.values,
            split="test",
        )
        evaluator.print_metrics_table([test_result])

        # ── Step 6: Save all models + metrics ──────────────────────────
        logger.info("=== STEP 6: Saving Models ===")
        artifacts: list[ModelArtifact] = []

        if save_artifacts:
            for tm in trained_models:
                val_m = next(
                    m for m in val_metrics if m.model_name == tm.model.name
                )
                is_best = tm.model.name == best_name
                artifact = registry.save_model(
                    model=tm.model,
                    tier=self.tier,
                    metrics={"validation": val_m.to_dict()},
                    metadata={
                        "selection_metric": self.primary_metric,
                        "is_best_model": is_best,
                    },
                    preprocessor=data.preprocessor if is_best else None,
                    is_best=is_best,
                    stamp=stamp,
                    dataset_path=self.settings.dataset_path,
                )
                artifacts.append(artifact)

            # Save test metrics for best model
            best_artifact = next(a for a in artifacts if a.is_best)
            combined_metrics = {
                "validation": best_val_score.to_dict(),
                "test": test_result.metrics.to_dict(),
                "selection": {
                    "metric": self.primary_metric,
                    "reason": selection_reason,
                    "comparison": comparison,
                },
            }
            best_artifact.metrics_path.write_text(
                dumps_json(combined_metrics), encoding="utf-8"
            )

            # Save full pipeline summary
            summary_path = reports_dir / "training_summary.json"
            result = TrainingPipelineResult(
                tier=self.tier,
                data=data,
                trained_models=trained_models,
                val_results=val_results,
                test_result=test_result,
                best_model_name=best_name,
                selection_reason=selection_reason,
                artifacts=artifacts,
                comparison=comparison,
            )
            summary_path.write_text(
                dumps_json(result.summary()), encoding="utf-8"
            )
            logger.info("Training summary -> %s", summary_path)

        return TrainingPipelineResult(
            tier=self.tier,
            data=data,
            trained_models=trained_models,
            val_results=val_results,
            test_result=test_result,
            best_model_name=best_name,
            selection_reason=selection_reason,
            artifacts=artifacts,
            comparison=comparison,
        )
