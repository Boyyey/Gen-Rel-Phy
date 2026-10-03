"""Kerr geometry in Boyer–Lindquist coordinates (G = c = 1)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Kerr:
    mass: float = 1.0
    spin: float = 0.0  # dimensionless a/M in [0, 0.999]

    def __post_init__(self):
        a = float(self.spin)
        if a < 0.0 or a >= 1.0:
            object.__setattr__(self, "spin", float(np.clip(a, 0.0, 0.999)))

    @property
    def a(self) -> float:
        return self.spin * self.mass

    @property
    def horizon(self) -> float:
        m, a = self.mass, self.a
        return m + np.sqrt(max(m * m - a * a, 0.0))

    @property
    def inner_horizon(self) -> float:
        m, a = self.mass, self.a
        return m - np.sqrt(max(m * m - a * a, 0.0))

    @property
    def ergosphere_eq(self) -> float:
        return 2.0 * self.mass

    def delta(self, r):
        return r * r - 2.0 * self.mass * r + self.a * self.a

    def sigma(self, r, theta):
        return r * r + self.a * self.a * np.cos(theta) ** 2

    def isco(self, prograde: bool = True) -> float:
        """Bardeen–Press–Teukolsky equatorial ISCO (M = mass)."""
        m = self.mass
        chi = self.spin
        z1 = 1.0 + (1.0 - chi * chi) ** (1.0 / 3.0) * (
            (1.0 + chi) ** (1.0 / 3.0) + (1.0 - chi) ** (1.0 / 3.0)
        )
        z2 = np.sqrt(3.0 * chi * chi + z1 * z1)
        if prograde:
            return m * (3.0 + z2 - np.sqrt((3.0 - z1) * (3.0 + z1 + 2.0 * z2)))
        return m * (3.0 + z2 + np.sqrt((3.0 - z1) * (3.0 + z1 + 2.0 * z2)))

    def photon_sphere(self, prograde: bool = True) -> float:
        m = self.mass
        chi = self.spin
        if prograde:
            return 2.0 * m * (1.0 + np.cos(2.0 / 3.0 * np.arccos(-chi)))
        return 2.0 * m * (1.0 + np.cos(2.0 / 3.0 * np.arccos(chi)))

    def omega_h(self) -> float:
        """Horizon angular velocity."""
        return self.a / (2.0 * self.mass * self.horizon)

    def frame_dragging_omega(self, r, theta=np.pi / 2) -> float:
        """Lense–Thirring angular velocity ω = -g_tφ / g_φφ."""
        m, a = self.mass, self.a
        rho2 = self.sigma(r, theta)
        delta = self.delta(r)
        g_tphi = -2.0 * m * a * r * np.sin(theta) ** 2 / rho2
        g_phiphi = (
            (r * r + a * a + 2.0 * m * a * a * r * np.sin(theta) ** 2 / rho2)
            * np.sin(theta) ** 2
        )
        # Use the exact BL g_φφ
        g_phiphi = np.sin(theta) ** 2 * (
            (r * r + a * a) ** 2 - a * a * delta * np.sin(theta) ** 2
        ) / rho2
        return -g_tphi / g_phiphi
