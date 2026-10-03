"""Validation against analytic GR and solver self-consistency."""

from __future__ import annotations

import numpy as np

from dynamica.metrics.kerr import Kerr
from dynamica.metrics.schwarzschild import Schwarzschild
from dynamica.perturbations.qnm import qnm_frequency
from dynamica.perturbations.rw_zerilli import evolve_perturbation
from dynamica.waveforms.imr import binary_merger_waveform, remnant_mass_spin


def test_schwarzschild_loci():
    s = Schwarzschild(1.0)
    assert abs(s.horizon - 2.0) < 1e-12
    assert abs(s.photon_sphere - 3.0) < 1e-12
    assert abs(s.isco - 6.0) < 1e-12
    assert abs(s.kretschmann(3.0) - 48.0 / 3.0**6) < 1e-12


def test_kerr_reduces_to_schwarzschild():
    k = Kerr(1.0, 0.0)
    assert abs(k.horizon - 2.0) < 1e-9
    assert abs(k.isco() - 6.0) < 1e-3


def test_kerr_spin_shrinks_isco():
    a0 = Kerr(1.0, 0.0).isco()
    a9 = Kerr(1.0, 0.9).isco()
    assert a9 < a0


def test_qnm_schwarzschild_l2():
    q = qnm_frequency(2, 0, 0.0, 1.0)
    assert abs(q.omega_real - 0.3736716844180417) < 1e-8
    assert abs(q.omega_imag - 0.0889623156889357) < 1e-8


def test_qnm_spin_increases_frequency():
    q0 = qnm_frequency(2, 0, 0.0, 1.0)
    q8 = qnm_frequency(2, 0, 0.8, 1.0)
    assert q8.omega_real > q0.omega_real


def test_tortoise_roundtrip():
    s = Schwarzschild(1.0)
    r = np.linspace(2.2, 40.0, 40)
    rs = s.tortoise(r)
    back = s.tortoise_inverse(rs)
    assert np.max(np.abs(back - r)) < 1e-6


def test_perturbation_radiates():
    res = evolve_perturbation(amplitude=1e-3, n_r=201, t_end=40.0, rstar_min=-25, rstar_max=50)
    assert np.max(np.abs(res.strain)) > 0
    assert np.isfinite(res.diagnostics["radiated_energy_proxy"])


def test_binary_waveform_chirps():
    wf = binary_merger_waveform(10.0, 10.0, 0.0, 0.0, distance_mpc=100.0)
    assert len(wf.hp) > 100
    assert wf.t_merge > 0
    assert 0.3 < wf.remnant_spin < 0.9
    assert wf.remnant_mass < 20.0
    # frequency should rise through inspiral
    n = max(10, len(wf.frequency) // 3)
    assert np.mean(wf.frequency[n : 2 * n]) >= np.mean(wf.frequency[:n]) * 0.5


def test_orbital_timeline_stages():
    from dynamica.lab.timeline import orbital_timeline

    tr = orbital_timeline(10, 8, 0.2, 0.1, "black_hole", "black_hole")
    assert "inspiral" in tr["stages"] or "orbit" in tr["stages"]
    assert len(tr["r"]) > 20
    assert tr["r"][0] > tr["r"][-1]


def test_mass_sphere_catalog():
    from dynamica.lab.objects import CATALOG, gpu_type
    assert "mass_sphere" in CATALOG
    assert gpu_type("mass_sphere") == 3.0
    from dynamica.lab.timeline import orbital_timeline
    tr = orbital_timeline(8, 6, 0, 0, "star", "mass_sphere")
    assert tr["kind1"] == "star"
    assert tr["r"][0] > tr["r"][-1]

    from dynamica.lab.timeline import orbital_timeline
    from dynamica.analysis.science_plots import science_pack
    from dynamica.waveforms.imr import binary_merger_waveform

    wf = binary_merger_waveform(10.0, 8.0, 0.0, 0.0, distance_mpc=100.0)
    tr = orbital_timeline(10, 8, 0.0, 0.0)
    pack = science_pack(tr, wf)
    needed = [
        "traj2d", "traj3d", "hp", "hc", "psi4", "freq", "spectrum",
        "sep", "energy", "angmom", "eradiated", "omega",
        "slice_early", "slice_late",
    ]
    for k in needed:
        assert k in pack
    assert len(pack["traj2d"]["x1"]) > 10
    assert pack["slice_early"]["n"] == 72


def test_remnant_energy_positive():
    mf, af = remnant_mass_spin(10, 10, 0, 0)
    assert mf < 20
    assert 0 <= af < 1


def test_newtonian_collision_reaches_surface_and_rebounds():
    from dynamica.waveforms.newtonian import newtonian_collision

    track = newtonian_collision(
        m1=21.2,
        m2=24.0,
        v1_initial=30.0,
        v2_initial=25.0,
        impact_parameter=0.0,
        kind1="mass_sphere",
        kind2="mass_sphere",
        n_steps=2000,
    )
    assert track.separation[0] > track.contact_radius
    assert np.min(track.separation) <= track.contact_radius * 1.01
    assert track.separation[-1] > track.contact_radius
    assert np.all(np.isfinite(track.energy))
    relative_energy_drift = np.max(np.abs(track.energy - track.energy[0])) / abs(track.energy[0])
    assert relative_energy_drift < 1e-3


def test_newtonian_scattering_has_a_noncontact_periapsis():
    from dynamica.waveforms.newtonian import newtonian_collision

    track = newtonian_collision(
        m1=21.2,
        m2=24.0,
        v1_initial=30.0,
        v2_initial=25.0,
        impact_parameter=100000.0,
        kind1="mass_sphere",
        kind2="mass_sphere",
        n_steps=2000,
        mode="scattering",
    )
    periapsis = int(np.argmin(track.separation))
    assert 0 < periapsis < len(track.separation) - 1
    assert track.separation[periapsis] > 5.0 * track.contact_radius
    assert track.separation[-1] > 5.0 * track.separation[periapsis]
    incoming = np.array([track.vx2[0] - track.vx1[0], track.vy2[0] - track.vy1[0]])
    outgoing = np.array([track.vx2[-1] - track.vx1[-1], track.vy2[-1] - track.vy1[-1]])
    expected_angle = np.degrees(
        np.arccos(np.clip(np.dot(incoming, outgoing) / (np.linalg.norm(incoming) * np.linalg.norm(outgoing)), -1.0, 1.0))
    )
    assert abs(track.deflection_angle - expected_angle) < 1e-8


def test_kerr_circular_geodesic_remains_on_shell():
    from dynamica.geodesics.integrator import geodesic_orbit

    orbit = geodesic_orbit(mass=10.0, spin=0.7, r0=100.0, lam_span=2500.0, n_eval=1800)
    radius_m = orbit.r / 10.0
    assert len(orbit.r) == 1800
    assert np.max(radius_m) - np.min(radius_m) < 1e-4
    assert orbit.conserved_error < 1e-10


def test_newtonian_mass_changes_gravitational_scattering():
    from dynamica.constants import L_MSUN_SI
    from dynamica.waveforms.newtonian import newtonian_collision

    def periapsis_km(primary_mass):
        track = newtonian_collision(
            m1=primary_mass,
            m2=0.8 * primary_mass,
            v1_initial=3000.0,
            v2_initial=2700.0,
            impact_parameter=50000.0,
            kind1="mass_sphere",
            kind2="mass_sphere",
            mode="scattering",
        )
        return np.min(track.separation) * (1.8 * primary_mass) * L_MSUN_SI / 1000.0

    assert periapsis_km(20.0) < periapsis_km(10.0)


def test_planetary_bound_orbit_impacts_and_reports_ap_components():
    from app.server import BinaryRequest, api_evolve

    earth_mass_solar = 3.0034896e-6
    result = api_evolve(BinaryRequest(
        m1=10.0 * earth_mass_solar,
        m2=8.0 * earth_mass_solar,
        kind1="planet",
        kind2="planet",
        sim_mode="orbit",
        orbit_speed_fraction=0.35,
        restitution=0.25,
    ))
    track = result["timeline"]
    assert track["outcome"] == "settled"
    assert track["contact_occurred"]
    assert min(track["r"]) <= track["contact_radius"] * 1.001
    assert track["impact_speed_m_s"] > 0
    assert track["impact_energy_loss_j"] > 0
    assert track["capture_fade"][-1] == 1.0
    assert set(("initial", "closest", "final", "impact")).issubset(result["mechanics"])
    assert len(result["mechanics"]["closest"]["force_on_object_a_n"]) == 3
    assert len(result["mechanics"]["impact"]["impulse_vector_n_s"]) == 3
    assert np.allclose(
        np.array(result["mechanics"]["closest"]["force_on_object_a_n"])
        + np.array(result["mechanics"]["closest"]["force_on_object_b_n"]),
        0.0,
    )


def test_newtonian_black_hole_contact_captures_and_fades():
    from dynamica.waveforms.newtonian import newtonian_collision

    track = newtonian_collision(
        m1=10.0,
        m2=8.0,
        v1_initial=3000.0,
        v2_initial=2700.0,
        kind1="black_hole",
        kind2="black_hole",
        n_steps=1200,
    )
    assert track.outcome == "captured"
    assert track.contact_time is not None
    assert np.all(track.capture_fade[1:] >= track.capture_fade[:-1])
    assert track.capture_fade[-1] == 1.0
    assert np.allclose(track.vx1[-20:], track.vx1[-1])
