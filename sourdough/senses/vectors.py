"""Small helpers shared by the senses."""

from __future__ import annotations

import numpy as np


def unit(v) -> np.ndarray:
    """Scale a vector to length 1. Zero vectors are returned unchanged."""
    v = np.asarray(v, np.float32)
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-9 else v
