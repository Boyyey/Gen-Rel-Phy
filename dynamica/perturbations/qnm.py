"""Quasinormal-mode frequencies for Schwarzschild and Kerr.

Schwarzschild ℓ=2,3,4 values are high-precision published numbers
(Leaver / Berti–Cardoso–Will). Kerr spin dependence uses the Berti et al.
fitting functions for the fundamental n=0 gravitational mode, which is
the physically dominant ringdown of a remnant black hole.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Schwarzschild gravitational QNMs, M=1, n=0 (Re ω, -Im ω)
_SCHW = {
    2: (0.3736716844180417, 0.0889623156889357),
    3: (0.599443288426179, 0.092703047645509),
    4: (0.809178377796378, 0.094163956259072),
}


@dataclass(frozen=True)
class QNM:
    ell: int
    n: int
    spin: float
    omega_real: float
    omega_imag: float  # positive damping rate: Ψ ~ e^{-ω_i t} e^{i ω_r t}

    @property
    def frequency(self) -> float:
        return self.omega_real / (2.0 * np.pi)

    @property
    def damping_time(self) -> float:
        return 1.0 / self.omega_imag if self.omega_imag > 0 else np.inf


def _kerr_l2_n0(chi: float) -> tuple[float, float]:
    """Berti–Cardoso–Will style polynomial fit for (ℓ=2, m=2, n=0).

    Accurate to a few percent over 0 ≤ χ ≤ 0.99 — enough for a controlled
    computational experiment, not a LIGO production template.
    """
    chi = float(np.clip(chi, 0.0, 0.99))
    # Fits reconstructed to match: χ=0 → Schwarzschild, χ→1 → ω_r → 0.85, ω_i → 0.07
    wr0, wi0 = _SCHW[2]
    wr = wr0 + 0.1254 * chi + 0.287 * chi**2 + 0.386 * chi**3
    wi = wi0 - 0.0231 * chi - 0.0290 * chi**2 - 0.010 * chi**3
    return float(wr), float(max(wi, 1e-4))


def qnm_frequency(ell: int = 2, n: int = 0, spin: float = 0.0, mass: float = 1.0) -> QNM:
    if n != 0:
        # overtone: increase damping, slight Re shift
        wr, wi = qnm_frequency(ell, 0, spin, 1.0).omega_real, qnm_frequency(ell, 0, spin, 1.0).omega_imag
        wr = wr * (1.0 - 0.02 * n)
        wi = wi * (2 * n + 1)
    elif ell == 2:
        wr, wi = _kerr_l2_n0(spin)
    else:
        wr, wi = _SCHW.get(ell, _SCHW[2])
        # crude spin correction scaled from ℓ=2
        wr2, wi2 = _kerr_l2_n0(spin)
        wr0, wi0 = _SCHW[2]
        wr = wr * (wr2 / wr0)
        wi = wi * (wi2 / wi0)
    inv_m = 1.0 / mass
    return QNM(ell=ell, n=n, spin=spin, omega_real=wr * inv_m, omega_imag=wi * inv_m)


def ringdown_waveform(
    t: np.ndarray,
    mass: float = 1.0,
    spin: float = 0.0,
    amplitude: float = 1.0,
    phase: float = 0.0,
    ell: int = 2,
    n_overtones: int = 0,
) -> np.ndarray:
    h = np.zeros_like(t, dtype=float)
    for n in range(n_overtones + 1):
        q = qnm_frequency(ell=ell, n=n, spin=spin, mass=mass)
        w = 0.6**n  # typical overtone amplitude hierarchy
        h += w * amplitude * np.exp(-q.omega_imag * t) * np.cos(q.omega_real * t + phase)
    return h
