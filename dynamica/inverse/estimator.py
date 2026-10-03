"""Physics-based gravitational-wave parameter estimation.

Given only h(t), recover (m1, m2, χ1, χ2) by minimizing a mismatch against
the laboratory IMR waveform family. No machine learning: this is a
template inner-product search, the same logical architecture used in
matched filtering.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import differential_evolution

from dynamica.waveforms.imr import binary_merger_waveform


@dataclass
class InferenceResult:
    m1: float
    m2: float
    chi1: float
    chi2: float
    mismatch: float
    recovered_hp: list
    t: list
    truth: dict | None

    def to_public(self) -> dict:
        return {
            "m1": self.m1,
            "m2": self.m2,
            "chi1": self.chi1,
            "chi2": self.chi2,
            "mismatch": self.mismatch,
            "recovered_hp": self.recovered_hp,
            "t": self.t,
            "truth": self.truth,
        }


def _resample(t_src, h_src, t_tgt):
    return np.interp(t_tgt, t_src, h_src, left=0.0, right=0.0)


def mismatch(h, g) -> float:
    h = np.asarray(h, float)
    g = np.asarray(g, float)
    nh = np.dot(h, h) + 1e-30
    ng = np.dot(g, g) + 1e-30
    return float(1.0 - np.dot(h, g) / np.sqrt(nh * ng))


def infer_from_strain(
    t: np.ndarray,
    h: np.ndarray,
    distance_mpc: float = 100.0,
    bounds: tuple | None = None,
    truth: dict | None = None,
    maxiter: int = 8,
) -> InferenceResult:
    t = np.asarray(t, float)
    h = np.asarray(h, float)
    if len(t) > 1600:
        step = max(1, len(t) // 1600)
        t, h = t[::step], h[::step]
    h = h / (np.max(np.abs(h)) + 1e-30)

    if bounds is None:
        bounds = [(5.0, 40.0), (5.0, 40.0), (0.0, 0.9), (0.0, 0.9)]

    def objective(x):
        m1, m2, c1, c2 = x
        wf = binary_merger_waveform(m1, m2, c1, c2, distance_mpc=distance_mpc, dt=float(np.median(np.diff(t))))
        g = _resample(wf.t, wf.hp, t)
        g = g / (np.max(np.abs(g)) + 1e-30)
        return mismatch(h, g)

    res = differential_evolution(
        objective, bounds, seed=7, maxiter=maxiter, popsize=4, polish=True, workers=1, updating="immediate"
    )
    m1, m2, c1, c2 = res.x
    wf = binary_merger_waveform(m1, m2, c1, c2, distance_mpc=distance_mpc, dt=float(np.median(np.diff(t))))
    g = _resample(wf.t, wf.hp, t)
    g = g / (np.max(np.abs(g)) + 1e-30)
    return InferenceResult(
        m1=float(m1),
        m2=float(m2),
        chi1=float(c1),
        chi2=float(c2),
        mismatch=float(res.fun),
        recovered_hp=g.tolist(),
        t=t.tolist(),
        truth=truth,
    )
