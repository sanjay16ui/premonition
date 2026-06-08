"""Prediction confidence scoring."""

from __future__ import annotations

from enum import Enum


class ConfidenceLevel(str, Enum):
    """How confident the model is in its prediction."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


def assess_confidence(risk_score: float) -> ConfidenceLevel:
    """
    Assess prediction confidence from the risk probability.

    Simple logic (beginner-friendly)
    --------------------------------
    - **High**   : Risk is very clear — near 0% or near 100%
                   (model is decisive: "definitely sepsis" or "definitely not")
    - **Medium** : Risk is in a moderate zone (35-65%)
                   (model sees mixed signals)
    - **Low**    : Risk is borderline around the 50% decision boundary
                   (model is uncertain — clinician review recommended)

    Parameters
    ----------
    risk_score:
        Probability of sepsis (0.0 to 1.0).
    """
    distance_from_boundary = abs(risk_score - 0.5)

    if distance_from_boundary >= 0.40:
        return ConfidenceLevel.HIGH
    if distance_from_boundary >= 0.15:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW
