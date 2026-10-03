"""Geometric units and astrophysical conversions.

Throughout the laboratory we work in geometrized units G = c = 1, so mass,
length, and time share a common dimension. Solar-mass conversions restore
SI / LIGO-style units for gravitational-wave strain analysis.
"""

from __future__ import annotations

import numpy as np

G_SI = 6.67430e-11
C_SI = 2.99792458e8
MSUN_SI = 1.98847e30
PC_SI = 3.0856775814913673e16
MPC_SI = 1.0e6 * PC_SI

# Geometric time corresponding to one solar mass: GM_sun / c^3
T_MSUN_SI = G_SI * MSUN_SI / C_SI**3  # ~ 4.925490947e-6 s
L_MSUN_SI = G_SI * MSUN_SI / C_SI**2  # ~ 1476.625 m


def mass_to_seconds(mass_msun: float) -> float:
    return float(mass_msun) * T_MSUN_SI


def seconds_to_mass(t_si: float, mass_msun: float) -> float:
    return float(t_si) / mass_to_seconds(mass_msun)


def geometric_strain_prefactor(total_mass_msun: float, distance_mpc: float) -> float:
    """Convert dimensionless geometric strain (units of M) to detector strain.

    h_detector ~ (G M / c^2 D) * h_geometric
    """
    m_len = float(total_mass_msun) * L_MSUN_SI
    d_len = float(distance_mpc) * MPC_SI
    return m_len / d_len


def schwarzschild_radius(mass_msun: float) -> float:
    """Coordinate radius 2M in meters."""
    return 2.0 * float(mass_msun) * L_MSUN_SI


def trapz(y, x):
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    if hasattr(np, "trapezoid"):
        return np.trapezoid(y, x)
    return np.trapz(y, x)

