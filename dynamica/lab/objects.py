"""Compact-object catalogue used by the laboratory.

Radii are geometric (G=c=1). Visual radii are deliberately scaled so
every species is readable in the same camera frustum; physical radii
control contact / merger in the worldline.
"""

from __future__ import annotations

CATALOG = {
    "planet": {
        "label": "Rocky planet",
        "gpu": 4.0,
        "R_visual": 4.6,
        "has_horizon": False,
        "has_disk": False,
    },
    "black_hole": {
        "label": "Black hole",
        "gpu": 0.0,
        "R_over_M": 2.0,
        "R_visual": 2.05,
        "has_horizon": True,
        "has_disk": True,
    },
    "neutron_star": {
        "label": "Neutron star",
        "gpu": 1.0,
        "R_over_M": 4.8,
        "R_visual": 3.4,
        "has_horizon": False,
        "has_disk": False,
    },
    "star": {
        "label": "Star",
        "gpu": 2.0,
        "R_over_M": 40.0,
        "R_visual": 5.6,
        "has_horizon": False,
        "has_disk": False,
    },
    "mass_sphere": {
        "label": "Mass sphere",
        "gpu": 3.0,
        "R_over_M": 16.0,
        "R_visual": 4.2,
        "has_horizon": False,
        "has_disk": False,
    },
}


def spec(kind: str) -> dict:
    return CATALOG.get(kind, CATALOG["mass_sphere"])


def physical_radius(kind: str, mass: float) -> float:
    if kind == "planet":
        earth_mass_solar = 3.0034896e-6
        earth_radius_solar_geometric = 6_371_000.0 / 1476.6250385
        return earth_radius_solar_geometric * (float(mass) / earth_mass_solar) ** 0.27
    return spec(kind)["R_over_M"] * float(mass)


def gpu_type(kind: str) -> float:
    return float(spec(kind)["gpu"])
