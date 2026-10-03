from __future__ import annotations

from pathlib import Path

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from dynamica.constants import C_SI, G_SI, L_MSUN_SI, MPC_SI, MSUN_SI, T_MSUN_SI
from dynamica.geodesics.integrator import geodesic_orbit
from dynamica.lab.experiments import (
    experiment_amplitude_scan,
    experiment_binary_spins,
    experiment_convergence,
    experiment_known_solutions,
    experiment_mass_ratio,
    experiment_mode_coupling,
    experiment_spin_ringdown,
    experiment_wavelength_scan,
    run_full_campaign,
)
from dynamica.metrics.kerr import Kerr
from dynamica.perturbations.qnm import qnm_frequency
from dynamica.perturbations.rw_zerilli import evolve_perturbation
from dynamica.waveforms.extraction import extract_features
from dynamica.waveforms.imr import binary_merger_waveform
from dynamica.waveforms.newtonian import newtonian_collision
from dynamica.inverse.estimator import infer_from_strain
from dynamica.lab.timeline import orbital_timeline
from dynamica.analysis.science_plots import science_pack

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

app = FastAPI(title="Dynamical Spacetime Laboratory", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class BinaryRequest(BaseModel):
    m1: float = 10.0
    m2: float = 8.0
    chi1: float = 0.0
    chi2: float = 0.0
    distance_mpc: float = 100.0
    inclination: float = 0.0
    kind1: str = "black_hole"
    kind2: str = "black_hole"
    sim_mode: str = "blackhole"
    v1: float = 30.0
    v2: float = 25.0
    impact_parameter: float = 5.0
    orbit_speed_fraction: float = 0.35
    restitution: float = Field(0.25, ge=0.0, le=1.0)


class PerturbRequest(BaseModel):
    mass: float = 1.0
    amplitude: float = 2e-3
    ell: int = 2
    parity: str = "odd"
    packet_width: float = 3.0
    nonlinear_lambda: float = 0.0
    n_r: int = 401
    t_end: float = 100.0


class GeodesicRequest(BaseModel):
    mass: float = 1.0
    spin: float = 0.0
    r0: float = 10.0
    lam_span: float = 250.0


class InverseRequest(BaseModel):
    m1: float = 12.0
    m2: float = 9.0
    chi1: float = 0.2
    chi2: float = 0.4


class KerrRequest(BaseModel):
    mass: float = 1.0
    spin: float = Field(0.7, ge=0.0, le=0.99)


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "lab": "dynamical-spacetime"}


@app.post("/api/evolve")
def api_evolve(req: BinaryRequest):
    if req.sim_mode == "blackhole":
        # Original black hole merger simulation
        wf = binary_merger_waveform(
            req.m1, req.m2, req.chi1, req.chi2, req.distance_mpc, req.inclination
        )
        feat = extract_features(wf.t, wf.hp, wf.t_merge)
        timeline = orbital_timeline(req.m1, req.m2, req.chi1, req.chi2, req.kind1, req.kind2)
        kerr = Kerr(1.0, wf.remnant_spin)
        return {
            "waveform": wf.to_public(2800),
            "features": feat.to_public(),
            "timeline": timeline,
            "plots": science_pack(timeline, wf),
            "remnant": {
                "mass": wf.remnant_mass,
                "spin": wf.remnant_spin,
                "horizon": kerr.horizon,
                "isco": kerr.isco(),
                "photon": kerr.photon_sphere(),
            },
            "sim_mode": "blackhole",
        }
    else:
        # Newtonian collision/scattering simulation
        newton = newtonian_collision(
            m1=req.m1,
            m2=req.m2,
            v1_initial=req.v1,
            v2_initial=req.v2,
            impact_parameter=req.impact_parameter,
            kind1=req.kind1,
            kind2=req.kind2,
            mode=req.sim_mode,
            orbit_speed_fraction=req.orbit_speed_fraction,
            restitution=req.restitution,
        )

        # Create a timeline dict compatible with the visualization
        relative_phase = np.unwrap(np.arctan2(newton.y1 - newton.y2, newton.x1 - newton.x2))
        periapsis_index = int(np.argmin(newton.separation))
        contact_occurred = bool(newton.separation[periapsis_index] <= newton.contact_radius * 1.01)
        if newton.outcome in {"captured", "merged", "settled"}:
            first_index = int(np.argmin(np.abs(newton.t - (newton.first_contact_time or 0.0))))
            final_index = int(np.argmin(np.abs(newton.t - (newton.contact_time or 0.0))))
            final_stage = "capture" if newton.outcome == "captured" else "settled"
            stages = ["approach" if i < first_index else "rebound" for i in range(len(newton.t))]
            stages[final_index:] = [final_stage] * (len(stages) - final_index)
            fade = newton.capture_fade > 0.0
            stages = ["fading" if fade[i] > 0.0 else stage for i, stage in enumerate(stages)]
        elif req.sim_mode == "orbit" and newton.outcome == "no_contact":
            stages = ["orbit"] * len(newton.t)
        elif req.sim_mode in {"collision", "orbit"}:
            stages = ["approach" if i < periapsis_index else "rebound" for i in range(len(newton.t))]
            stages[periapsis_index] = "impact" if newton.outcome == "rebounded" else "contact"
        else:
            stages = ["approach" if i < periapsis_index else "recession" for i in range(len(newton.t))]
            stages[periapsis_index] = "periapsis"
        timeline = {
            "t": newton.t.tolist(),
            "r": newton.separation.tolist(),
            "phi": relative_phase.tolist(),
            "omega": np.gradient(relative_phase, newton.t).tolist(),
            "energy": newton.energy.tolist(),
            "angular_momentum": newton.angular_momentum.tolist(),
            "x1": newton.x1.tolist(),
            "y1": newton.y1.tolist(),
            "z1": newton.z1.tolist(),
            "x2": newton.x2.tolist(),
            "y2": newton.y2.tolist(),
            "z2": newton.z2.tolist(),
            "vx1": newton.vx1.tolist(),
            "vy1": newton.vy1.tolist(),
            "vz1": newton.vz1.tolist(),
            "vx2": newton.vx2.tolist(),
            "vy2": newton.vy2.tolist(),
            "vz2": newton.vz2.tolist(),
            "stages": stages,
            "m1": req.m1,
            "m2": req.m2,
            "kind1": req.kind1,
            "kind2": req.kind2,
            "label1": f"Object A ({req.kind1})",
            "label2": f"Object B ({req.kind2})",
            "r_isco": 0.0,
            "r_contact": 0.0,
            "contact_radius": newton.contact_radius,
            "contact_occurred": contact_occurred,
            "deflection_angle_deg": newton.deflection_angle,
            "energy_scale": newton.energy_scale,
            "outcome": newton.outcome,
            "contact_time": newton.contact_time,
            "first_contact_time": newton.first_contact_time,
            "impact_speed_m_s": newton.impact_speed,
            "impact_impulse_n_s": newton.impact_impulse,
            "impact_impulse_vector_n_s": newton.impact_impulse_vector.tolist(),
            "impact_energy_loss_j": newton.impact_energy_loss,
            "capture_fade": newton.capture_fade.tolist(),
            "restitution": 0.0 if newton.outcome == "captured" else req.restitution,
            "orbit_speed_fraction": req.orbit_speed_fraction,
            "remnant_mass": req.m1 + req.m2,
            "remnant_spin": 0.0,
            "both_horizons": False,
            "radius1": 0.0,
            "radius2": 0.0,
            "gpu1": 0.0,
            "gpu2": 0.0,
        }

        mass1_kg = req.m1 * MSUN_SI
        mass2_kg = req.m2 * MSUN_SI
        reduced_mass_kg = mass1_kg * mass2_kg / (mass1_kg + mass2_kg)
        length_scale_m = (req.m1 + req.m2) * L_MSUN_SI
        velocity_scale_m_s = C_SI
        closest_index = int(np.argmin(newton.separation))
        sample_indices = {
            "initial": 0,
            "closest": closest_index,
            "final": len(newton.t) - 1,
        }
        mechanics = {}
        for sample_name, index in sample_indices.items():
            relative_position = np.array([
                newton.x2[index] - newton.x1[index],
                newton.y2[index] - newton.y1[index],
                newton.z2[index] - newton.z1[index],
            ]) * length_scale_m
            velocity1 = np.array([newton.vx1[index], newton.vy1[index], newton.vz1[index]]) * velocity_scale_m_s
            velocity2 = np.array([newton.vx2[index], newton.vy2[index], newton.vz2[index]]) * velocity_scale_m_s
            relative_velocity = velocity2 - velocity1
            radius = max(float(np.linalg.norm(relative_position)), 1e-9)
            force_on_1 = G_SI * mass1_kg * mass2_kg * relative_position / radius**3
            kinetic_energy = 0.5 * mass1_kg * float(np.dot(velocity1, velocity1)) + 0.5 * mass2_kg * float(np.dot(velocity2, velocity2))
            potential_energy = -G_SI * mass1_kg * mass2_kg / radius
            radial_speed = float(np.dot(relative_velocity, relative_position) / radius)
            tangential_speed = float(np.sqrt(max(0.0, np.dot(relative_velocity, relative_velocity) - radial_speed**2)))
            orbital_angular_momentum = reduced_mass_kg * np.cross(relative_position, relative_velocity)
            system_momentum = mass1_kg * velocity1 + mass2_kg * velocity2
            mechanics[sample_name] = {
                "separation_m": relative_position.tolist(),
                "relative_velocity_m_s": relative_velocity.tolist(),
                "relative_speed_m_s": float(np.linalg.norm(relative_velocity)),
                "radial_speed_m_s": radial_speed,
                "tangential_speed_m_s": tangential_speed,
                "force_on_object_a_n": force_on_1.tolist(),
                "force_on_object_b_n": (-force_on_1).tolist(),
                "acceleration_a_m_s2": (force_on_1 / mass1_kg).tolist(),
                "acceleration_b_m_s2": (-force_on_1 / mass2_kg).tolist(),
                "system_momentum_kg_m_s": system_momentum.tolist(),
                "kinetic_energy_j": kinetic_energy,
                "potential_energy_j": potential_energy,
                "total_energy_j": kinetic_energy + potential_energy,
                "orbital_angular_momentum_kg_m2_s": orbital_angular_momentum.tolist(),
            }
        mechanics["impact"] = {
            "outcome": newton.outcome,
            "relative_impact_speed_m_s": newton.impact_speed,
            "normal_impulse_n_s": newton.impact_impulse,
            "impulse_vector_n_s": newton.impact_impulse_vector.tolist(),
            "kinetic_energy_lost_j": newton.impact_energy_loss,
            "coefficient_of_restitution": timeline["restitution"],
        }

        # Leading-order quadrupole radiation is diagnostic only; it does not
        # feed radiation-reaction forces back into the Newtonian orbit.
        from dynamica.waveforms.imr import Waveform
        total_mass_seconds = (req.m1 + req.m2) * T_MSUN_SI
        relative_position_m = C_SI * total_mass_seconds * np.column_stack((
            newton.x2 - newton.x1,
            newton.y2 - newton.y1,
            newton.z2 - newton.z1,
        ))
        time_seconds = newton.t * total_mass_seconds
        reduced_mass_kg = (req.m1 * req.m2 / (req.m1 + req.m2)) * MSUN_SI
        distance_m = req.distance_mpc * MPC_SI
        quadrupole_plus = reduced_mass_kg * (relative_position_m[:, 0] ** 2 - relative_position_m[:, 1] ** 2)
        quadrupole_cross = 2.0 * reduced_mass_kg * relative_position_m[:, 0] * relative_position_m[:, 1]
        quadrupole_scale = G_SI / (C_SI**4 * distance_m)
        hp = quadrupole_scale * np.gradient(np.gradient(quadrupole_plus, time_seconds), time_seconds)
        hc = quadrupole_scale * np.gradient(np.gradient(quadrupole_cross, time_seconds), time_seconds)
        phase = np.unwrap(np.arctan2(hc, hp))
        frequency = np.maximum(np.gradient(phase, time_seconds) / (2.0 * np.pi), 0.0)
        t_merge = float(time_seconds[int(np.argmin(newton.separation))])
        wf = Waveform(
            t=time_seconds,
            hp=hp,
            hc=hc,
            frequency=frequency,
            phase=phase,
            t_merge=t_merge,
            remnant_mass=req.m1 + req.m2,
            remnant_spin=0.0,
            radiated_energy_frac=0.0,
            params={"mode": "newtonian"},
        )

        features = extract_features(wf.t, wf.hp, wf.t_merge)
        return {
            "waveform": wf.to_public(2800),
            "features": features.to_public(),
            "timeline": timeline,
            "plots": science_pack(timeline, wf),
            "mechanics": mechanics,
            "remnant": {
                "mass": req.m1 + req.m2,
                "spin": 0.0,
                "horizon": 0.0,
                "isco": 0.0,
                "photon": 0.0,
            },
            "sim_mode": req.sim_mode,
        }


@app.post("/api/binary")
def api_binary(req: BinaryRequest):
    wf = binary_merger_waveform(
        req.m1, req.m2, req.chi1, req.chi2, req.distance_mpc, req.inclination
    )
    feat = extract_features(wf.t, wf.hp, wf.t_merge)
    kerr = Kerr(1.0, wf.remnant_spin)
    return {
        "waveform": wf.to_public(3200),
        "features": feat.to_public(),
        "remnant": {
            "mass": wf.remnant_mass,
            "spin": wf.remnant_spin,
            "horizon": kerr.horizon,
            "isco": kerr.isco(),
            "photon": kerr.photon_sphere(),
        },
    }


@app.post("/api/perturb")
def api_perturb(req: PerturbRequest):
    res = evolve_perturbation(
        mass=req.mass,
        ell=req.ell,
        parity=req.parity,
        amplitude=req.amplitude,
        packet_width=req.packet_width,
        nonlinear_lambda=req.nonlinear_lambda,
        n_r=req.n_r,
        t_end=req.t_end,
    )
    feat = extract_features(res.t, res.strain)
    return {"field": res.to_public(), "features": feat.to_public()}


@app.post("/api/geodesic")
def api_geodesic(req: GeodesicRequest):
    g = geodesic_orbit(
        mass=req.mass,
        spin=req.spin,
        r0=req.r0 * req.mass,
        lam_span=req.lam_span * req.mass,
        n_eval=1800,
    )
    step = max(1, len(g.t) // 800)
    return {
        "t": (g.t / req.mass)[::step].tolist(),
        "r": (g.r / req.mass)[::step].tolist(),
        "phi": g.phi[::step].tolist(),
        "x": (g.r * np.cos(g.phi) / req.mass)[::step].tolist(),
        "y": (g.r * np.sin(g.phi) / req.mass)[::step].tolist(),
        "conserved_error": g.conserved_error,
        "kind": g.kind,
    }


@app.post("/api/kerr")
def api_kerr(req: KerrRequest):
    k = Kerr(req.mass, req.spin)
    q = qnm_frequency(2, 0, req.spin, req.mass)
    return {
        "horizon": k.horizon,
        "inner_horizon": k.inner_horizon,
        "isco": k.isco(),
        "photon": k.photon_sphere(),
        "omega_h": k.omega_h(),
        "qnm": {"wr": q.omega_real, "wi": q.omega_imag, "f": q.frequency, "tau": q.damping_time},
    }


@app.post("/api/inverse")
def api_inverse(req: InverseRequest):
    wf = binary_merger_waveform(req.m1, req.m2, req.chi1, req.chi2, distance_mpc=90.0)
    inf = infer_from_strain(
        wf.t,
        wf.hp,
        distance_mpc=90.0,
        truth={"m1": req.m1, "m2": req.m2, "chi1": req.chi1, "chi2": req.chi2},
        maxiter=6,
    )
    return inf.to_public()


@app.get("/api/experiments/{name}")
def api_experiment(name: str, quick: bool = True):
    table = {
        "known": experiment_known_solutions,
        "convergence": experiment_convergence,
        "amplitude": experiment_amplitude_scan,
        "wavelength": experiment_wavelength_scan,
        "spin": experiment_spin_ringdown,
        "mass_ratio": experiment_mass_ratio,
        "binary_spins": experiment_binary_spins,
        "modes": experiment_mode_coupling,
    }
    if name == "campaign":
        return run_full_campaign(quick=quick)
    fn = table.get(name)
    if fn is None:
        return {"error": "unknown experiment", "known": list(table)}
    return fn()
