"""Effective potentials for linearized gravitational perturbations."""

from __future__ import annotations

import numpy as np


def regge_wheeler_potential(r: np.ndarray, mass: float, ell: int, spin_weight: int = 2) -> np.ndarray:
    """Odd-parity RW potential V_l^{(s)}(r)."""
    m = mass
    f = 1.0 - 2.0 * m / r
    return f * (ell * (ell + 1) / r**2 + (1 - spin_weight**2) * 2.0 * m / r**3)


def zerilli_potential(r: np.ndarray, mass: float, ell: int) -> np.ndarray:
    """Even-parity Zerilli potential for gravitational perturbations."""
    m = mass
    n = (ell - 1) * (ell + 2) / 2.0
    f = 1.0 - 2.0 * m / r
    num = 2.0 * n**2 * (n + 1.0) * r**3 + 6.0 * n**2 * m * r**2 + 18.0 * n * m**2 * r + 18.0 * m**3
    den = r**3 * (n * r + 3.0 * m) ** 2
    return f * num / den
