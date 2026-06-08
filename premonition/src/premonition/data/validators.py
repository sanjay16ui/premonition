"""Data quality validation for the PREMONITION ICU dataset."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from premonition.features.feature_registry import FeatureRegistry
from premonition.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationIssue:
    """Single data quality finding."""

    check: str
    severity: str  # "error" | "warning" | "info"
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataQualityReport:
    """Aggregated validation results."""

    passed: bool
    n_rows: int
    n_columns: int
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "n_rows": self.n_rows,
            "n_columns": self.n_columns,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [
                {
                    "check": i.check,
                    "severity": i.severity,
                    "message": i.message,
                    "details": i.details,
                }
                for i in self.issues
            ],
        }


class DatasetValidator:
    """Run schema, leakage, and distribution checks on raw data."""

    def __init__(self, registry: FeatureRegistry) -> None:
        self.registry = registry

    def validate(self, df: pd.DataFrame) -> DataQualityReport:
        issues: list[ValidationIssue] = []

        issues.extend(self._check_shape(df))
        issues.extend(self._check_schema(df))
        issues.extend(self._check_identifier_uniqueness(df))
        issues.extend(self._check_target(df))
        issues.extend(self._check_constant_columns(df))
        issues.extend(self._check_categorical_values(df))
        issues.extend(self._check_missingness(df))
        issues.extend(self._check_outliers(df))
        issues.extend(self._check_leakage_patterns(df))
        issues.extend(self._check_excluded_columns_documented(df))

        passed = len([i for i in issues if i.severity == "error"]) == 0
        report = DataQualityReport(
            passed=passed,
            n_rows=len(df),
            n_columns=len(df.columns),
            issues=issues,
        )

        if passed:
            logger.info("Data quality validation PASSED (%d warnings)", len(report.warnings))
        else:
            logger.error(
                "Data quality validation FAILED (%d errors, %d warnings)",
                len(report.errors),
                len(report.warnings),
            )
        return report

    def _check_shape(self, df: pd.DataFrame) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if len(df) == 0:
            issues.append(ValidationIssue("shape", "error", "Dataset is empty"))
        if len(df) < 100:
            issues.append(
                ValidationIssue(
                    "shape",
                    "warning",
                    f"Small dataset: only {len(df)} rows",
                    {"n_rows": len(df)},
                )
            )
        return issues

    def _check_schema(self, df: pd.DataFrame) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        expected = set(self.registry.all_raw_columns())
        actual = set(df.columns)

        missing = sorted(expected - actual)
        extra = sorted(actual - expected)

        if missing:
            issues.append(
                ValidationIssue(
                    "schema",
                    "error",
                    f"Missing required columns: {missing}",
                    {"missing": missing},
                )
            )
        if extra:
            issues.append(
                ValidationIssue(
                    "schema",
                    "warning",
                    f"Unexpected extra columns: {extra}",
                    {"extra": extra},
                )
            )
        return issues

    def _check_identifier_uniqueness(self, df: pd.DataFrame) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        id_col = "subject_id"
        if id_col not in df.columns:
            return issues

        dup_count = int(df[id_col].duplicated().sum())
        if dup_count > 0:
            issues.append(
                ValidationIssue(
                    "identifier",
                    "error",
                    f"Duplicate subject_id values: {dup_count}",
                    {"duplicate_count": dup_count},
                )
            )
        return issues

    def _check_target(self, df: pd.DataFrame) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        target = self.registry.target_column
        if target not in df.columns:
            issues.append(ValidationIssue("target", "error", f"Target column missing: {target}"))
            return issues

        nulls = int(df[target].isna().sum())
        if nulls > 0:
            issues.append(
                ValidationIssue(
                    "target",
                    "error",
                    f"Target has {nulls} null values",
                    {"null_count": nulls},
                )
            )

        values = df[target].dropna().unique()
        if not set(values).issubset({0, 1}):
            issues.append(
                ValidationIssue(
                    "target",
                    "error",
                    f"Target must be binary 0/1, found: {sorted(values)}",
                )
            )

        pos_rate = float(df[target].mean())
        issues.append(
            ValidationIssue(
                "target",
                "info",
                f"Target prevalence: {pos_rate:.2%}",
                {"positive_rate": pos_rate, "n_positive": int(df[target].sum())},
            )
        )

        if pos_rate < 0.05 or pos_rate > 0.40:
            issues.append(
                ValidationIssue(
                    "target",
                    "warning",
                    f"Unusual class balance: {pos_rate:.2%} positive",
                    {"positive_rate": pos_rate},
                )
            )
        return issues

    def _check_constant_columns(self, df: pd.DataFrame) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for col in df.columns:
            if df[col].nunique(dropna=False) <= 1:
                issues.append(
                    ValidationIssue(
                        "constant_column",
                        "warning",
                        f"Column '{col}' has only one unique value",
                        {"column": col, "value": df[col].iloc[0] if len(df) else None},
                    )
                )
        return issues

    def _check_categorical_values(self, df: pd.DataFrame) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if "gender" in df.columns:
            invalid_gender = df[~df["gender"].isin(["M", "F"])]["gender"].unique().tolist()
            if invalid_gender:
                issues.append(
                    ValidationIssue(
                        "categorical",
                        "warning",
                        f"Unexpected gender values: {invalid_gender}",
                        {"invalid_values": invalid_gender},
                    )
                )

        for col in self.registry.categorical_columns:
            if col not in df.columns:
                continue
            null_rate = float(df[col].isna().mean())
            if null_rate > 0:
                issues.append(
                    ValidationIssue(
                        "categorical",
                        "warning",
                        f"Categorical '{col}' has {null_rate:.1%} missing",
                        {"column": col, "null_rate": null_rate},
                    )
                )
        return issues

    def _check_missingness(self, df: pd.DataFrame) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        miss_pct = (df.isnull().mean() * 100).sort_values(ascending=False)
        high_miss = miss_pct[miss_pct > 15]

        for col, pct in high_miss.items():
            issues.append(
                ValidationIssue(
                    "missingness",
                    "warning",
                    f"Column '{col}' missing {pct:.1f}%",
                    {"column": col, "missing_pct": float(pct)},
                )
            )

        # MNAR pattern: labs missing more in sepsis cases
        target = self.registry.target_column
        if target in df.columns:
            for col in self.registry.lab_columns:
                if col not in df.columns:
                    continue
                miss_neg = float(df.loc[df[target] == 0, col].isna().mean())
                miss_pos = float(df.loc[df[target] == 1, col].isna().mean())
                if miss_pos > miss_neg + 0.05:
                    issues.append(
                        ValidationIssue(
                            "missingness_mnar",
                            "info",
                            f"MNAR pattern in '{col}': missing rate higher in positives "
                            f"({miss_pos:.1%} vs {miss_neg:.1%})",
                            {
                                "column": col,
                                "missing_rate_negative": miss_neg,
                                "missing_rate_positive": miss_pos,
                            },
                        )
                    )
        return issues

    def _check_outliers(self, df: pd.DataFrame) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        temp_cols = [
            c for c in df.columns
            if c in {"temp_celsius_mean", "temp_celsius_max", "temp_celsius_min"}
        ]
        for col in temp_cols:
            if col not in df.columns:
                continue
            below = int((df[col] < 30).sum())
            above = int((df[col] > 42).sum())
            if below or above:
                issues.append(
                    ValidationIssue(
                        "outliers",
                        "warning",
                        f"Temperature outliers in '{col}': {below} below 30°C, {above} above 42°C",
                        {"column": col, "below_30": below, "above_42": above},
                    )
                )

        if "hr_mean" in df.columns:
            extreme_hr = int((df["hr_mean"] > 200).sum())
            if extreme_hr:
                issues.append(
                    ValidationIssue(
                        "outliers",
                        "warning",
                        f"{extreme_hr} rows with hr_mean > 200 bpm",
                        {"count": extreme_hr},
                    )
                )
        return issues

    def _check_leakage_patterns(self, df: pd.DataFrame) -> list[ValidationIssue]:
        """Detect known synthetic leakage patterns in raw data."""
        issues: list[ValidationIssue] = []

        if "pao2_fio2_ratio" in df.columns and "spo2_mean" in df.columns:
            diff = (df["pao2_fio2_ratio"] - df["spo2_mean"]).abs()
            exact_match = int((diff < 0.1).sum())
            if exact_match > len(df) * 0.5:
                issues.append(
                    ValidationIssue(
                        "leakage_pattern",
                        "warning",
                        f"pao2_fio2_ratio ≈ spo2_mean in {exact_match}/{len(df)} rows "
                        "(confirmed leakage — excluded from features)",
                        {"match_count": exact_match},
                    )
                )

        if "mechanical_ventilation" in df.columns:
            nunique = df["mechanical_ventilation"].nunique()
            if nunique <= 1:
                issues.append(
                    ValidationIssue(
                        "leakage_pattern",
                        "warning",
                        "mechanical_ventilation is constant — excluded from features",
                        {"nunique": int(nunique)},
                    )
                )
        return issues

    def _check_excluded_columns_documented(self, df: pd.DataFrame) -> list[ValidationIssue]:
        """Confirm excluded columns exist in raw data but won't be used."""
        issues: list[ValidationIssue] = []
        for col in self.registry.excluded_columns:
            if col not in df.columns:
                issues.append(
                    ValidationIssue(
                        "excluded_columns",
                        "info",
                        f"Excluded column '{col}' not present in raw data",
                        {"column": col},
                    )
                )
        return issues


def validate_dataset(
    df: pd.DataFrame,
    registry: FeatureRegistry,
    raise_on_error: bool = True,
) -> DataQualityReport:
    """
    Validate dataset and optionally raise on critical failures.

    Parameters
    ----------
    df:
        Raw dataframe.
    registry:
        Feature registry with tier/leakage definitions.
    raise_on_error:
        If True, raise ValueError when errors are found.
    """
    report = DatasetValidator(registry).validate(df)
    if raise_on_error and not report.passed:
        messages = "\n".join(f"  [{i.severity}] {i.check}: {i.message}" for i in report.errors)
        raise ValueError(f"Data quality validation failed:\n{messages}")
    return report
