"""Exact Schwarzschild geometry in geometrized units (G = c = 1)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Schwarzschild:
    mass: float = 1.0

    @property
    def horizon(self) -> float:
        return 2.0 * self.mass

    @property
    def photon_sphere(self) -> float:
        return 3.0 * self.mass

    @property
    def isco(self) -> float:
        return 6.0 * self.mass

    def lapse_factor(self, r: np.ndarray | float) -> np.ndarray | float:
        """sqrt(-g_tt) = sqrt(1 - 2M/r)."""
        return np.sqrt(np.clip(1.0 - 2.0 * self.mass / np.asarray(r), 0.0, None))

    def metric_tt(self, r):
        return -(1.0 - 2.0 * self.mass / r)

    def metric_rr(self, r):
        return 1.0 / (1.0 - 2.0 * self.mass / r)

    def tortoise(self, r: np.ndarray | float) -> np.ndarray | float:
        """r* = r + 2M ln|r/2M - 1|."""
        m = self.mass
        r = np.asarray(r, dtype=float)
        return r + 2.0 * m * np.log(np.abs(r / (2.0 * m) - 1.0))

    def tortoise_inverse(self, rstar: np.ndarray | float, r_guess: float | None = None) -> np.ndarray:
        """Newton inversion of the tortoise map, used to place radial grids."""
        m = self.mass
        rs = np.asarray(rstar, dtype=float)
        r = np.full_like(rs, 6.0 * m if r_guess is None else r_guess, dtype=float)
        for _ in range(40):
            f = r + 2.0 * m * np.log(np.abs(r / (2.0 * m) - 1.0)) - rs
            df = r / (r - 2.0 * m)
            r = r - f / df
            r = np.maximum(r, 2.0 * m * 1.0000001)
        return r

    def kretschmann(self, r: np.ndarray | float) -> np.ndarray | float:
        """K = R_{abcd} R^{abcd} = 48 M^2 / r^6."""
        return 48.0 * self.mass**2 / np.asarray(r) ** 6
