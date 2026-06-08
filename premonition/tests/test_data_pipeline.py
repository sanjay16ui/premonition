"""Tests for Section 3 data pipeline components."""

from __future__ import annotations

import pytest

from premonition.config.settings import get_settings
from premonition.data.loaders import load_dataset
from premonition.data.pipeline import DataPipeline
from premonition.data.splitters import SplitConfig, create_splits
from premonition.data.validators import validate_dataset
from premonition.features.engineering import engineer_features, select_tier_frame
from premonition.features.feature_registry import FeatureRegistry


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture
def registry(settings):
    return FeatureRegistry(settings.feature_config)


@pytest.fixture
def raw_df(settings):
    return load_dataset(settings=settings)


class TestFeatureRegistry:
    def test_no_leakage_in_t1(self, registry):
        cols = registry.get_tier_columns("t1")
        registry.validate_no_leakage(cols)
        assert "pao2_fio2_ratio" not in cols
        assert "sofa_score" not in cols
        assert "mechanical_ventilation" not in cols

    def test_t2_includes_labs(self, registry):
        t1 = set(registry.get_tier_columns("t1"))
        t2 = set(registry.get_tier_columns("t2"))
        assert "lactate_mmol" in t2
        assert t2 - t1 == {"lactate_mmol"} | set(registry.lab_columns) - t1

    def test_missing_indicators_only_t2(self, registry):
        assert registry.get_missing_indicator_columns("t1") == []
        assert len(registry.get_missing_indicator_columns("t2")) == len(registry.lab_columns)


class TestValidators:
    def test_validation_passes_on_real_data(self, raw_df, registry):
        report = validate_dataset(raw_df, registry, raise_on_error=False)
        assert report.passed
        assert report.n_rows == 5000

    def test_detects_duplicate_ids(self, raw_df, registry):
        bad = raw_df.copy()
        bad.loc[1, "subject_id"] = bad.loc[0, "subject_id"]
        report = validate_dataset(bad, registry, raise_on_error=False)
        assert not report.passed
        assert any(i.check == "identifier" for i in report.errors)


class TestEngineering:
    def test_engineered_columns_created(self, raw_df, registry):
        out = engineer_features(raw_df, registry)
        for col in registry.engineered_columns:
            assert col in out.columns

    def test_gender_typo_fixed(self, raw_df):
        out = engineer_features(raw_df)
        assert "Mael" not in out["gender"].values


class TestSplits:
    def test_stratified_proportions(self, raw_df, registry):
        eng = engineer_features(raw_df, registry)
        tier_df = select_tier_frame(eng, registry, "t1")
        splits = create_splits(
            tier_df,
            target_column="sepsis_label",
            config=SplitConfig(test_size=0.10, val_size=0.10, random_state=42),
        )
        total = len(splits.train) + len(splits.val) + len(splits.test)
        assert total == len(tier_df)
        assert len(splits.test) == 500
        assert 499 <= len(splits.val) <= 501
        assert len(splits.train) == total - len(splits.test) - len(splits.val)


class TestFullPipeline:
    def test_pipeline_runs_t1(self, settings):
        pipeline = DataPipeline(tier="t1", settings=settings, raise_on_validation_error=True)
        result = pipeline.run(save_artifacts=False)

        assert result.quality_report.passed
        assert result.X_train_processed.shape[0] == len(result.splits.train)
        assert result.X_val_processed.shape[0] == len(result.splits.val)
        assert result.X_test_processed.shape[0] == len(result.splits.test)
        assert len(result.processed_feature_names) > len(result.feature_columns)
        assert result.preprocessor.is_fitted

    def test_pipeline_runs_t2(self, settings):
        pipeline = DataPipeline(tier="t2", settings=settings, raise_on_validation_error=True)
        result = pipeline.run(save_artifacts=False)
        assert result.X_train_processed.shape[1] > result.X_train.shape[1]
