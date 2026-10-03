"""Convergence-order estimation for grid-based relativistic solvers."""

from __future__ import annotations

import numpy as np


def observed_order(q_coarse, q_mid, q_fine, r: float = 2.0) -> float:
    """Three-level observed convergence order p = log(|q_c-q_m|/|q_m-q_f|) / log(r)."""
    num = abs(q_coarse - q_mid)
    den = abs(q_mid - q_fine)
    if den < 1e-30 or num < 1e-30:
        return float("nan")
    return float(np.log(num / den) / np.log(r))


def relative_error(q, q_ref) -> float:
    return float(abs(q - q_ref) / (abs(q_ref) + 1e-30))
