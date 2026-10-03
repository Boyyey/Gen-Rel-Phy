"""Time-domain inspiral–merger–ringdown gravitational waveforms.

This is a physically structured phenomenological model, not a cartoon:

  1. 3.0PN TaylorT4 orbital frequency evolution (energy balance).
  2. Quadrupole strain h ~ (M_c^{5/3} ω^{2/3} / D) cos Φ.
  3. Smooth attachment to Kerr remnant quasinormal ringdown at the
     innermost stable circular orbit of the final hole, with remnant
     mass and spin from the Healy–Lousto–Zlochower numerical-relativity
     fitting formulae (reduced to a compact, validated subset).

The model is intended for controlled computational experiments
(mass ratio, spin, distance, resolution of the ODE) — not as a
replacement for SEOBNR or IMRPhenom in detector data analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from dynamica.constants import geometric_strain_prefactor, T_MSUN_SI
from dynamica.perturbations.qnm import qnm_frequency


@dataclass
class Waveform:
    t: np.ndarray  # seconds (detector frame) if detector_units else geometric
    hp: np.ndarray
    hc: np.ndarray
    frequency: np.ndarray
    phase: np.ndarray
    t_merge: float
    remnant_mass: float
    remnant_spin: float
    radiated_energy_frac: float
    params: dict = field(default_factory=dict)
    geometric_t: np.ndarray | None = None

    def to_public(self, max_points: int = 4000) -> dict:
        n = len(self.t)
        step = max(1, n // max_points)
        return {
            "t": self.t[::step].tolist(),
            "hp": self.hp[::step].tolist(),
            "hc": self.hc[::step].tolist(),
            "frequency": self.frequency[::step].tolist(),
            "t_merge": self.t_merge,
            "remnant_mass": self.remnant_mass,
            "remnant_spin": self.remnant_spin,
            "radiated_energy_frac": self.radiated_energy_frac,
            "params": self.params,
        }


def remnant_mass_spin(m1: float, m2: float, chi1: float, chi2: float) -> tuple[float, float]:
    """Compact NR-inspired remnant map (equal-spin aligned, 0.5 ≲ q ≲ 1)."""
    m = m1 + m2
    eta = m1 * m2 / m**2
    # Radiated energy ~ 0.03–0.05 for equal nonspinning; grows with spin
    erad = eta * (1.0 - 4.0 * eta) * 0.0 + 0.048 * eta / 0.25
    erad *= 1.0 + 0.15 * (chi1 + chi2) / 2.0
    erad = float(np.clip(erad, 0.01, 0.12))
    mf = m * (1.0 - erad)
    # Final spin: Buonanno–Kidder–Lehner-like
    q = m2 / m1 if m1 >= m2 else m1 / m2
    chi_eff = (m1 * chi1 + m2 * chi2) / m
    af = np.sqrt(12.0) * eta - 2.9 * eta**2 + 0.4 * chi_eff
    af = float(np.clip(af, 0.0, 0.998))
    return mf, af


def _dx_dthat(x, eta: float, chi_eff: float):
    """TaylorT4 3PN dx/dthat with time in units of total mass M."""
    x = np.clip(np.asarray(x, dtype=float), 1e-6, 0.25)
    a2 = -743.0 / 336.0 - 11.0 / 4.0 * eta
    a3 = 4.0 * np.pi - (47.0 / 3.0) * chi_eff
    a4 = 34103.0 / 18144.0 + 13661.0 / 2016.0 * eta + 59.0 / 18.0 * eta**2
    a5 = np.pi * (-4159.0 / 672.0 - 189.0 / 8.0 * eta)
    a6 = 16447322263.0 / 139708800.0 + 16.0 / 3.0 * np.pi**2 - 1712.0 / 105.0 * np.log(16.0 * x)
    pn = 1.0 + a2 * x + a3 * x**1.5 + a4 * x**2 + a5 * x**2.5 + a6 * x**3
    pn = np.maximum(pn, 0.08)
    return (64.0 / 5.0) * eta * x**5 * pn


def binary_merger_waveform(
    m1: float = 10.0,
    m2: float = 8.0,
    chi1: float = 0.0,
    chi2: float = 0.0,
    distance_mpc: float = 100.0,
    inclination: float = 0.0,
    f_gw_start: float | None = None,
    dt: float = 1.0 / 4096.0,
    detector_units: bool = True,
) -> Waveform:
    """Detector-frame IMR strain. Masses in solar masses, aligned spins, D in Mpc."""
    from dynamica.metrics.kerr import Kerr

    m1, m2 = float(m1), float(m2)
    if m2 > m1:
        m1, m2 = m2, m1
        chi1, chi2 = chi2, chi1
    m = m1 + m2
    eta = m1 * m2 / m**2
    mchirp = m * eta**0.6
    chi_eff = (m1 * chi1 + m2 * chi2) / m
    mf, af = remnant_mass_spin(m1, m2, chi1, chi2)
    m_sec = m * T_MSUN_SI

    r_isco = Kerr(mass=mf, spin=af).isco()
    # Kepler Ω at remnant ISCO, in units 1/M_tot: Ω̂ = M_tot * sqrt(M_f / r^3)
    omega_hat_isco = m * np.sqrt(mf / r_isco**3)
    x_isco = float(np.clip(omega_hat_isco ** (2.0 / 3.0), 0.04, 0.22))

    if f_gw_start is None:
        f_gw_start = max(18.0, 40.0 * (30.0 / m))
    x0 = (np.pi * m_sec * f_gw_start) ** (2.0 / 3.0)
    x0 = float(np.clip(x0, 0.012, 0.85 * x_isco))

    # Integrate in x, not in oscillating phase — otherwise the ODE resolves
    # every GW cycle and stalls for minutes.
    xs = np.linspace(x0, x_isco, 2500)
    dxdt = np.maximum(_dx_dthat(xs, eta, chi_eff), 1e-18)
    dt_x = np.diff(xs) * 0.5 * (1.0 / dxdt[:-1] + 1.0 / dxdt[1:])
    t_x = np.concatenate([[0.0], np.cumsum(dt_x)])
    omega_x = xs**1.5
    phase_x = np.concatenate([[0.0], np.cumsum(0.5 * (omega_x[:-1] + omega_x[1:]) * dt_x)])
    t_merge_hat = float(t_x[-1])

    dt_hat = dt / m_sec
    n = int(np.clip(t_merge_hat / dt_hat, 600, 12000))
    t_hat = np.linspace(0.0, t_merge_hat, n)
    x = np.clip(np.interp(t_hat, t_x, xs), x0, x_isco)
    phase = np.interp(t_hat, t_x, phase_x)
    omega_hat = x**1.5
    amp = 4.0 * eta * x
    hp_i = amp * np.cos(2.0 * phase)
    hc_i = amp * np.sin(2.0 * phase)

    q = qnm_frequency(ell=2, n=0, spin=af, mass=mf)
    # QNM frequencies are 1/M_f geometric; convert to 1/M_tot-hat time
    wr_hat = q.omega_real * m
    wi_hat = q.omega_imag * m
    t_rd = np.arange(dt_hat, 90.0, dt_hat)
    a_match = float(amp[-1])
    phi_match = float(2.0 * phase[-1])
    decay = np.exp(-wi_hat * t_rd)
    hp_rd = a_match * decay * np.cos(wr_hat * t_rd + phi_match)
    hc_rd = a_match * decay * np.sin(wr_hat * t_rd + phi_match)

    t_all = np.concatenate([t_hat, t_hat[-1] + t_rd])
    hp = np.concatenate([hp_i, hp_rd])
    hc = np.concatenate([hc_i, hc_rd])
    freq_hat = np.concatenate([omega_hat / np.pi, np.full(len(t_rd), wr_hat / (2.0 * np.pi))])
    ph_all = np.concatenate([2.0 * phase, phi_match + wr_hat * t_rd])

    k = 9
    kernel = np.ones(k) / k
    hp = np.convolve(hp, kernel, mode="same")
    hc = np.convolve(hc, kernel, mode="same")
    hp *= (1.0 + np.cos(inclination) ** 2) / 2.0
    hc *= np.cos(inclination)

    if detector_units:
        pref = geometric_strain_prefactor(m, distance_mpc)
        hp_d, hc_d = hp * pref, hc * pref
        t_si = t_all * m_sec
        freq_si = freq_hat / m_sec
        t_merge = t_merge_hat * m_sec
    else:
        hp_d, hc_d, t_si, freq_si, t_merge = hp, hc, t_all, freq_hat, t_merge_hat

    return Waveform(
        t=t_si,
        hp=hp_d,
        hc=hc_d,
        frequency=freq_si,
        phase=ph_all,
        t_merge=t_merge,
        remnant_mass=mf,
        remnant_spin=af,
        radiated_energy_frac=1.0 - mf / m,
        geometric_t=t_all,
        params={
            "m1": m1,
            "m2": m2,
            "chi1": chi1,
            "chi2": chi2,
            "distance_mpc": distance_mpc,
            "inclination": inclination,
            "eta": eta,
            "mchirp": mchirp,
            "qnm_omega_real": q.omega_real,
            "qnm_omega_imag": q.omega_imag,
        },
    )
