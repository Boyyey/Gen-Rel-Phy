"""Physics-driven binary worldline for the booth visualization."""

from __future__ import annotations

import numpy as np

from dynamica.lab.objects import physical_radius, spec
from dynamica.metrics.kerr import Kerr
from dynamica.waveforms.imr import _dx_dthat, remnant_mass_spin


def contact_radius(m1: float, m2: float, kind1: str, kind2: str) -> float:
    return physical_radius(kind1, m1) + physical_radius(kind2, m2)


def orbital_timeline(
    m1: float = 10.0,
    m2: float = 8.0,
    chi1: float = 0.0,
    chi2: float = 0.0,
    kind1: str = "black_hole",
    kind2: str = "black_hole",
    n: int = 1800,
) -> dict:
    m1, m2 = float(m1), float(m2)
    a1, a2 = spec(kind1), spec(kind2)
    m = m1 + m2
    eta = m1 * m2 / m**2
    chi_eff = (m1 * chi1 + m2 * chi2) / m
    mf, af = remnant_mass_spin(m1, m2, chi1, chi2)
    both_holes = bool(a1["has_horizon"] and a2["has_horizon"])

    r_contact = contact_radius(m1, m2, kind1, kind2)
    r_isco = Kerr(mass=mf, spin=af).isco() if both_holes else r_contact
    r_stop = max(r_isco, r_contact)

    r0 = 22.0 * m
    x0 = m / r0
    x_stop = min(0.20, m / max(r_stop, 2.4 * m))
    xs = np.linspace(max(x0, 0.018), max(x_stop, x0 * 1.05), n)
    dxdt = np.maximum(_dx_dthat(xs, eta, chi_eff), 1e-18)
    dt = np.diff(xs) * 0.5 * (1.0 / dxdt[:-1] + 1.0 / dxdt[1:])
    t = np.concatenate([[0.0], np.cumsum(dt)])
    omega = xs**1.5
    phi = np.concatenate([[0.0], np.cumsum(0.5 * (omega[:-1] + omega[1:]) * dt)])
    r = m / np.maximum(xs, 1e-6)
    e_bind = -0.5 * eta * m / r
    ell = eta * np.sqrt(m * r)

    q = m2 / m1
    r1 = r * q / (1.0 + q)
    r2 = r / (1.0 + q)
    x1, y1 = r1 * np.cos(phi), r1 * np.sin(phi)
    x2, y2 = -r2 * np.cos(phi), -r2 * np.sin(phi)
    z1 = np.zeros_like(x1)
    z2 = np.zeros_like(x2)

    stages = []
    for ri in r:
        if both_holes and ri < 1.12 * r_isco:
            stages.append("merger")
        elif ri < 9.0 * m:
            stages.append("inspiral")
        else:
            stages.append("orbit")
    if both_holes:
        k = max(12, n // 14)
        stages[-k:] = ["ringdown"] * k
    elif not both_holes:
        # compact bodies meet at contact; no Kerr remnant ringdown
        for i, ri in enumerate(r):
            if ri <= 1.05 * r_contact:
                stages[i] = "contact"

    return {
        "t": t.tolist(),
        "r": r.tolist(),
        "phi": phi.tolist(),
        "omega": omega.tolist(),
        "energy": e_bind.tolist(),
        "angular_momentum": ell.tolist(),
        "x1": x1.tolist(),
        "y1": y1.tolist(),
        "z1": z1.tolist(),
        "x2": x2.tolist(),
        "y2": y2.tolist(),
        "z2": z2.tolist(),
        "stages": stages,
        "m1": m1,
        "m2": m2,
        "kind1": kind1,
        "kind2": kind2,
        "label1": a1["label"],
        "label2": a2["label"],
        "r_isco": float(r_isco),
        "r_contact": float(r_contact),
        "remnant_mass": float(mf if both_holes else m1 + m2),
        "remnant_spin": float(af if both_holes else 0.0),
        "both_horizons": both_holes,
        "radius1": physical_radius(kind1, m1),
        "radius2": physical_radius(kind2, m2),
        "gpu1": a1["gpu"],
        "gpu2": a2["gpu"],
    }
