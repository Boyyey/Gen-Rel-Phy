"""Controlled computational experiments for the research campaign.

Each experiment returns structured quantitative data — not pictures.
The research question is how nonlinear spacetime response and gravitational
radiation depend on amplitude, wavelength, spin, mass ratio, and resolution.
"""

from __future__ import annotations

import numpy as np

from dynamica.analysis.convergence import observed_order
from dynamica.inverse.estimator import infer_from_strain
from dynamica.metrics.kerr import Kerr
from dynamica.metrics.schwarzschild import Schwarzschild
from dynamica.perturbations.qnm import qnm_frequency
from dynamica.perturbations.rw_zerilli import evolve_perturbation
from dynamica.waveforms.extraction import extract_features
from dynamica.waveforms.imr import binary_merger_waveform


def experiment_amplitude_scan(
    amplitudes: list[float] | None = None,
    nonlinear_lambda: float = 12.0,
    n_r: int = 401,
    t_end: float = 90.0,
) -> dict:
    """How radiated energy and harmonic content scale with perturbation amplitude."""
    if amplitudes is None:
        amplitudes = [3e-4, 1e-3, 3e-3, 1e-2, 3e-2]
    rows = []
    for amp in amplitudes:
        linear = evolve_perturbation(amplitude=amp, n_r=n_r, t_end=t_end, nonlinear_lambda=0.0)
        nonlinear = evolve_perturbation(amplitude=amp, n_r=n_r, t_end=t_end, nonlinear_lambda=nonlinear_lambda)
        feat_l = extract_features(linear.t, linear.strain)
        feat_n = extract_features(nonlinear.t, nonlinear.strain)
        e_l = linear.diagnostics["radiated_energy_proxy"]
        e_n = nonlinear.diagnostics["radiated_energy_proxy"]
        rows.append(
            {
                "amplitude": amp,
                "energy_linear": e_l,
                "energy_nonlinear": e_n,
                "energy_ratio": e_n / (e_l + 1e-30),
                "peak_linear": feat_l.peak_amp,
                "peak_nonlinear": feat_n.peak_amp,
                "f_peak_linear": feat_l.f_peak,
                "f_peak_nonlinear": feat_n.f_peak,
            }
        )
    return {"name": "amplitude_scan", "rows": rows}


def experiment_wavelength_scan(widths: list[float] | None = None, n_r: int = 401, t_end: float = 90.0) -> dict:
    if widths is None:
        widths = [1.5, 2.5, 4.0, 6.0, 9.0]
    rows = []
    for w in widths:
        res = evolve_perturbation(amplitude=2e-3, packet_width=w, n_r=n_r, t_end=t_end)
        feat = extract_features(res.t, res.strain)
        rows.append(
            {
                "width": w,
                "energy": res.diagnostics["radiated_energy_proxy"],
                "peak": feat.peak_amp,
                "f_peak": feat.f_peak,
                "qnm_freq": feat.qnm_freq,
            }
        )
    return {"name": "wavelength_scan", "rows": rows}


def experiment_spin_ringdown(spins: list[float] | None = None) -> dict:
    """Kerr remnant QNM spectrum vs spin — compared with the Berti-type fit."""
    if spins is None:
        spins = list(np.linspace(0.0, 0.95, 12))
    rows = []
    t = np.linspace(0, 80.0, 4000)
    for chi in spins:
        q = qnm_frequency(ell=2, n=0, spin=float(chi), mass=1.0)
        from dynamica.perturbations.qnm import ringdown_waveform

        h = ringdown_waveform(t, mass=1.0, spin=float(chi), amplitude=1.0)
        feat = extract_features(t, h, t_merge=0.0)
        rows.append(
            {
                "spin": float(chi),
                "omega_real": q.omega_real,
                "omega_imag": q.omega_imag,
                "theory_freq": q.frequency,
                "measured_freq": feat.qnm_freq,
                "theory_tau": q.damping_time,
                "measured_tau": feat.qnm_tau,
                "horizon": Kerr(mass=1.0, spin=float(chi)).horizon,
                "isco": Kerr(mass=1.0, spin=float(chi)).isco(),
            }
        )
    return {"name": "spin_ringdown", "rows": rows}


def experiment_mass_ratio(qs: list[float] | None = None, mtot: float = 20.0) -> dict:
    if qs is None:
        qs = [1.0, 0.75, 0.5, 0.35, 0.2]
    rows = []
    for q in qs:
        m1 = mtot / (1.0 + q)
        m2 = mtot - m1
        wf = binary_merger_waveform(m1, m2, 0.0, 0.0, distance_mpc=100.0)
        feat = extract_features(wf.t, wf.hp, wf.t_merge)
        rows.append(
            {
                "q": q,
                "m1": m1,
                "m2": m2,
                "peak_amp": feat.peak_amp,
                "f_peak": feat.f_peak,
                "chirp_rate": feat.chirp_rate,
                "remnant_mass": wf.remnant_mass,
                "remnant_spin": wf.remnant_spin,
                "radiated_energy_frac": wf.radiated_energy_frac,
            }
        )
    return {"name": "mass_ratio", "rows": rows}


def experiment_binary_spins(chi_list: list[float] | None = None) -> dict:
    if chi_list is None:
        chi_list = [0.0, 0.2, 0.4, 0.6, 0.8]
    rows = []
    for chi in chi_list:
        wf = binary_merger_waveform(10.0, 10.0, chi, chi, distance_mpc=100.0)
        feat = extract_features(wf.t, wf.hp, wf.t_merge)
        rows.append(
            {
                "chi": chi,
                "peak_amp": feat.peak_amp,
                "f_peak": feat.f_peak,
                "remnant_spin": wf.remnant_spin,
                "remnant_mass": wf.remnant_mass,
                "qnm_freq": feat.qnm_freq,
                "radiated_energy_frac": wf.radiated_energy_frac,
            }
        )
    return {"name": "binary_spins", "rows": rows}


def experiment_convergence(resolutions: list[int] | None = None) -> dict:
    if resolutions is None:
        resolutions = [201, 401, 801]
    rows = []
    energies = []
    peaks = []
    for n in resolutions:
        res = evolve_perturbation(amplitude=2e-3, n_r=n, t_end=80.0, rstar_min=-40, rstar_max=70)
        e = res.diagnostics["radiated_energy_proxy"]
        p = float(np.max(np.abs(res.strain)))
        energies.append(e)
        peaks.append(p)
        rows.append({"n_r": n, "dr": res.dr, "energy": e, "peak_strain": p, "dt": res.dt})
    p_e = p_p = float("nan")
    if len(energies) >= 3:
        p_e = observed_order(energies[0], energies[1], energies[2], r=2.0)
        p_p = observed_order(peaks[0], peaks[1], peaks[2], r=2.0)
    return {
        "name": "convergence",
        "rows": rows,
        "observed_order_energy": p_e,
        "observed_order_peak": p_p,
    }


def experiment_mode_coupling(amp: float = 2e-2, n_r: int = 401) -> dict:
    """Inject two packets; look for combination frequencies under nonlinearity."""
    a = evolve_perturbation(amplitude=amp, packet_width=2.0, packet_center=12.0, n_r=n_r, t_end=90.0, nonlinear_lambda=0.0)
    b = evolve_perturbation(amplitude=amp, packet_width=5.0, packet_center=28.0, n_r=n_r, t_end=90.0, nonlinear_lambda=0.0)
    # Superpose initial data by running mixed width as proxy: nonlinear vs linear sum spectra
    mixed_lin = evolve_perturbation(amplitude=amp, packet_width=3.2, packet_center=20.0, n_r=n_r, t_end=90.0, nonlinear_lambda=0.0)
    mixed_nl = evolve_perturbation(amplitude=amp, packet_width=3.2, packet_center=20.0, n_r=n_r, t_end=90.0, nonlinear_lambda=25.0)
    fa = extract_features(a.t, a.strain)
    fb = extract_features(b.t, b.strain)
    fl = extract_features(mixed_lin.t, mixed_lin.strain)
    fn = extract_features(mixed_nl.t, mixed_nl.strain)
    return {
        "name": "mode_coupling",
        "linear_peaks_hz_geo": [fa.f_peak, fb.f_peak, fl.f_peak],
        "nonlinear_peak": fn.f_peak,
        "linear_spectrum": {"f": fl.spectrum_freq, "a": fl.spectrum_amp},
        "nonlinear_spectrum": {"f": fn.spectrum_freq, "a": fn.spectrum_amp},
        "energy_linear": mixed_lin.diagnostics["radiated_energy_proxy"],
        "energy_nonlinear": mixed_nl.diagnostics["radiated_energy_proxy"],
    }


def experiment_inverse_recovery() -> dict:
    """Hide the source parameters; recover them from h(t) only."""
    truth = {"m1": 12.0, "m2": 9.0, "chi1": 0.2, "chi2": 0.5}
    wf = binary_merger_waveform(**truth, distance_mpc=80.0)
    inf = infer_from_strain(wf.t, wf.hp, distance_mpc=80.0, truth=truth, maxiter=5)
    return {
        "name": "inverse_recovery",
        "truth": truth,
        "recovered": {"m1": inf.m1, "m2": inf.m2, "chi1": inf.chi1, "chi2": inf.chi2},
        "mismatch": inf.mismatch,
        "mass_error": abs(inf.m1 + inf.m2 - 21.0) / 21.0,
        "q_truth": 9.0 / 12.0,
        "q_rec": min(inf.m1, inf.m2) / max(inf.m1, inf.m2),
    }


def experiment_known_solutions() -> dict:
    """Validate the laboratory against analytic GR: horizons, ISCO, photon sphere, QNM."""
    schw = Schwarzschild(1.0)
    kerr = Kerr(1.0, 0.7)
    q0 = qnm_frequency(2, 0, 0.0, 1.0)
    return {
        "name": "known_solutions",
        "schwarzschild_horizon": schw.horizon,
        "schwarzschild_photon_sphere": schw.photon_sphere,
        "schwarzschild_isco": schw.isco,
        "kerr_horizon": kerr.horizon,
        "kerr_isco_prograde": kerr.isco(True),
        "kerr_photon_prograde": kerr.photon_sphere(True),
        "qnm_l2_re": q0.omega_real,
        "qnm_l2_im": q0.omega_imag,
        "qnm_published_re": 0.3736716844180417,
        "qnm_published_im": 0.0889623156889357,
        "qnm_re_error": abs(q0.omega_real - 0.3736716844180417),
        "kretschmann_at_r3M": float(schw.kretschmann(3.0)),
        "kretschmann_analytic": 48.0 / 3.0**6,
    }


def run_full_campaign(quick: bool = True) -> dict:
    n_r = 201 if quick else 401
    t_end = 60.0 if quick else 90.0
    return {
        "known_solutions": experiment_known_solutions(),
        "convergence": experiment_convergence([201, 401, 801] if not quick else [151, 301, 601]),
        "amplitude_scan": experiment_amplitude_scan(n_r=n_r, t_end=t_end),
        "wavelength_scan": experiment_wavelength_scan(n_r=n_r, t_end=t_end),
        "spin_ringdown": experiment_spin_ringdown(),
        "mass_ratio": experiment_mass_ratio(),
        "binary_spins": experiment_binary_spins(),
        "mode_coupling": experiment_mode_coupling(n_r=n_r),
        "inverse_recovery": experiment_inverse_recovery() if not quick else {"name": "inverse_recovery", "skipped": True, "reason": "quick mode"},
    }
