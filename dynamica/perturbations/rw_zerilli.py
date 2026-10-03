"""1+1D evolution of Regge–Wheeler / Zerilli master functions.

The linearized Einstein equations on Schwarzschild reduce, after gauge fixing,
to a wave equation on the tortoise line:

    ∂²Ψ/∂t² − ∂²Ψ/∂r*² + V_ℓ(r) Ψ = S(t, r*) + λ Ψ²   (optional nonlinear probe)

This is a genuine numerical-relativity calculation in spherical symmetry /
multipole reduction — not a cartoon. Outgoing radiation is read at large r*.

The optional quadratic source is *not* the full nonlinear Einstein equation.
It is a controlled probe of mode coupling and of the breakdown of linearity,
which is the research question of this laboratory.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from dynamica.constants import trapz
from dynamica.metrics.schwarzschild import Schwarzschild
from dynamica.perturbations.potentials import regge_wheeler_potential, zerilli_potential


@dataclass
class PerturbationResult:
    t: np.ndarray
    rstar: np.ndarray
    r: np.ndarray
    psi_snapshot: np.ndarray
    strain: np.ndarray
    observer_rstar: float
    ell: int
    parity: str
    amplitude: float
    mass: float
    dt: float
    dr: float
    nonlinear_lambda: float
    energy_flux: np.ndarray
    diagnostics: dict = field(default_factory=dict)

    def to_public(self, stride: int = 4) -> dict:
        k = max(1, stride)
        return {
            "t": self.t[::k].tolist(),
            "strain": self.strain[::k].tolist(),
            "energy_flux": self.energy_flux[::k].tolist(),
            "rstar": self.rstar[:: max(1, len(self.rstar) // 256)].tolist(),
            "psi": self.psi_snapshot[:: max(1, self.psi_snapshot.shape[0] // 80), :: max(1, self.psi_snapshot.shape[1] // 256)].tolist(),
            "ell": self.ell,
            "parity": self.parity,
            "amplitude": self.amplitude,
            "mass": self.mass,
            "dt": self.dt,
            "dr": self.dr,
            "nonlinear_lambda": self.nonlinear_lambda,
            "diagnostics": self.diagnostics,
        }


def _gaussian_packet(rstar: np.ndarray, amp: float, center: float, width: float) -> np.ndarray:
    return amp * np.exp(-((rstar - center) ** 2) / (2.0 * width**2))


def evolve_perturbation(
    mass: float = 1.0,
    ell: int = 2,
    parity: str = "odd",
    amplitude: float = 1e-3,
    packet_center: float = 20.0,
    packet_width: float = 3.0,
    rstar_min: float = -50.0,
    rstar_max: float = 90.0,
    n_r: int = 801,
    t_end: float = 160.0,
    cfl: float = 0.45,
    nonlinear_lambda: float = 0.0,
    snapshot_every: int = 8,
    observer_frac: float = 0.82,
) -> PerturbationResult:
    """Leapfrog evolution of the master gravitational perturbation."""
    bh = Schwarzschild(mass=mass)
    rstar = np.linspace(rstar_min, rstar_max, n_r)
    dr = float(rstar[1] - rstar[0])
    r = bh.tortoise_inverse(rstar)
    if parity == "even":
        v = zerilli_potential(r, mass, ell)
    else:
        v = regge_wheeler_potential(r, mass, ell, spin_weight=2)

    psi0 = _gaussian_packet(rstar, amplitude, packet_center, packet_width)
    # Initially outgoing: ∂t Ψ ≈ −∂r* Ψ
    dpsi_dr = np.gradient(psi0, dr)
    dt = cfl * dr
    n_t = int(np.ceil(t_end / dt))
    dt = t_end / n_t

    psi_prev = psi0 + dt * dpsi_dr  # first-order start for outgoing
    psi = psi0.copy()

    i_obs = int(observer_frac * (n_r - 1))
    strain = np.zeros(n_t + 1)
    flux = np.zeros(n_t + 1)
    times = np.linspace(0.0, t_end, n_t + 1)
    snaps = []
    snap_times = []

    # Sommerfeld outgoing at outer boundary, ingoing at inner (horizon)
    for n in range(n_t):
        lap = (np.roll(psi, -1) + np.roll(psi, 1) - 2.0 * psi) / dr**2
        source = -v * psi + nonlinear_lambda * psi**2
        psi_next = 2.0 * psi - psi_prev + dt**2 * (lap + source)
        # characteristic boundaries
        psi_next[0] = psi[1]  # ingoing / absorb near horizon
        psi_next[-1] = psi[-2]
        # outgoing radiation: psi_t + psi_r* = 0 at outer edge
        psi_next[-1] = psi[-1] - (dt / dr) * (psi[-1] - psi[-2])
        psi_next[0] = psi[0] + (dt / dr) * (psi[1] - psi[0])

        dpsi_dt = (psi_next - psi_prev) / (2.0 * dt)
        dpsi_rs = (psi[min(i_obs + 1, n_r - 1)] - psi[max(i_obs - 1, 0)]) / (2.0 * dr)
        strain[n] = float(psi[i_obs] / max(r[i_obs], 1.0))
        flux[n] = float(dpsi_dt[i_obs] ** 2)

        if n % snapshot_every == 0:
            snaps.append(psi.copy())
            snap_times.append(times[n])

        psi_prev, psi = psi, psi_next

    strain[-1] = float(psi[i_obs] / max(r[i_obs], 1.0))
    flux[-1] = flux[-2]
    snaps.append(psi.copy())
    psi_snapshot = np.vstack(snaps) if snaps else psi[None, :]

    # Rough radiated energy ∫ Ṅ² dt  (normalization up to ℓ-dependent factor)
    e_rad = float(trapz(flux, times))
    diagnostics = {
        "radiated_energy_proxy": e_rad,
        "max_abs_psi": float(np.max(np.abs(psi_snapshot))),
        "observer_r": float(r[i_obs]),
        "n_r": n_r,
        "n_t": n_t,
        "cfl": cfl,
        "grid_dr": dr,
        "outgoing_peak": float(np.max(np.abs(strain))),
    }
    return PerturbationResult(
        t=times,
        rstar=rstar,
        r=r,
        psi_snapshot=psi_snapshot,
        strain=strain,
        observer_rstar=float(rstar[i_obs]),
        ell=ell,
        parity=parity,
        amplitude=amplitude,
        mass=mass,
        dt=dt,
        dr=dr,
        nonlinear_lambda=nonlinear_lambda,
        energy_flux=flux,
        diagnostics=diagnostics,
    )
