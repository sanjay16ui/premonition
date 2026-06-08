"""JSON serialization helpers for numpy types."""

from __future__ import annotations

import json
from typing import Any

import numpy as np


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.bool_):
        return bool(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def dumps_json(obj: Any, indent: int = 2) -> str:
    """Serialize object to JSON string, handling numpy types."""
    return json.dumps(obj, indent=indent, default=_json_default)
