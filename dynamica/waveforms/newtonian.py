"""Newtonian N-body collision simulation for non-black-hole scenarios."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from dynamica.constants import C_SI, G_SI, L_MSUN_SI


@dataclass
class NewtonianState:
    """State of a Newtonian N-body simulation."""
    t: np.ndarray
    x1: np.ndarray
    y1: np.ndarray
    z1: np.ndarray
    x2: np.ndarray
    y2: np.ndarray
    z2: np.ndarray
    vx1: np.ndarray
    vy1: np.ndarray
    vz1: np.ndarray
    vx2: np.ndarray
    vy2: np.ndarray
    vz2: np.ndarray
    energy: np.ndarray
    angular_momentum: np.ndarray
    separation: np.ndarray
    contact_radius: float
    deflection_angle: float
    energy_scale: float
    outcome: str
    contact_time: float | None
    first_contact_time: float | None
    impact_speed: float
    impact_impulse: float
    impact_impulse_vector: np.ndarray
    impact_energy_loss: float
    capture_fade: np.ndarray


def newtonian_collision(
    m1: float = 10.0,
    m2: float = 8.0,
    v1_initial: float = 30.0,
    v2_initial: float = 25.0,
    impact_parameter: float = 5.0,
    kind1: str = "star",
    kind2: str = "star",
    n_steps: int = 4000,
    dt: float | None = None,
    mode: str = "collision",
    orbit_speed_fraction: float = 0.35,
    restitution: float = 1.0,
) -> NewtonianState:
    """
    Integrate a Newtonian two-body encounter with adaptive DOP853 in geometric units.

    Contact can rebound, lose normal kinetic energy, merge, or trigger a
    Newtonian capture-radius proxy when either object is a black hole.
    """
    from dynamica.lab.objects import physical_radius

    # Convert masses to kg
    m1_kg = m1 * 1.98847e30
    m2_kg = m2 * 1.98847e30

    r1_m = physical_radius(kind1, m1) * L_MSUN_SI
    r2_m = physical_radius(kind2, m2) * L_MSUN_SI
    contact = r1_m + r2_m
    total_mass = m1_kg + m2_kg
    impact_m = max(0.0, impact_parameter) * 1e3
    speed1 = max(0.0, v1_initial) * 1e3
    speed2 = max(0.0, v2_initial) * 1e3
    relative_speed = speed1 + speed2

    if mode not in {"collision", "scattering", "orbit"}:
        raise ValueError("mode must be 'collision', 'scattering', or 'orbit'")
    if n_steps < 2:
        raise ValueError("n_steps must be at least 2")
    if m1 <= 0.0 or m2 <= 0.0:
        raise ValueError("object masses must be positive")
    if mode == "orbit" and not 0.0 < orbit_speed_fraction < 1.0:
        raise ValueError("orbit_speed_fraction must be between 0 and 1")
    if not 0.0 <= restitution <= 1.0:
        raise ValueError("restitution must be between 0 and 1")

    if mode == "collision":
        initial_sep = max(5.0 * contact, 1.0e6)
    elif mode == "scattering":
        positive_energy_radius = (
            4.0 * G_SI * total_mass / relative_speed**2
            if relative_speed > 0.0
            else 0.0
        )
        initial_sep = max(8.0 * max(impact_m, contact), 5.0e7, positive_energy_radius)
    else:
        initial_sep = 8.0 * contact
    dynamical_time = np.sqrt(initial_sep**3 / (G_SI * total_mass))
    crossing_time = initial_sep / max(relative_speed, 1e-12)
    if mode == "collision":
        duration = 1.5 * dynamical_time
    elif mode == "scattering":
        duration = 2.5 * crossing_time if relative_speed > 0.0 else 2.0 * dynamical_time
    else:
        orbital_period = 2.0 * np.pi * dynamical_time
        duration = 1.1 * orbital_period
    if dt is not None:
        duration = float(dt) * (n_steps - 1)
    t_seconds = np.linspace(0.0, duration, n_steps)
    mass_fraction1, mass_fraction2 = m1_kg / total_mass, m2_kg / total_mass
    length_unit = G_SI * total_mass / C_SI**2
    time_unit = G_SI * total_mass / C_SI**3
    contact_geo = contact / length_unit
    center_velocity = np.array([(m1_kg * speed1 - m2_kg * speed2) / total_mass / C_SI, 0.0, 0.0])
    if mode == "orbit":
        circular_speed = np.sqrt(G_SI * total_mass / initial_sep)
        relative_initial = np.array([0.0, orbit_speed_fraction * circular_speed / C_SI, 0.0])
        relative_position = np.array([initial_sep, 0.0, 0.0]) / length_unit
        center_velocity[:] = 0.0
    else:
        relative_initial = np.array([-relative_speed / C_SI, 0.0, 0.0])
        relative_position = np.array([initial_sep, impact_m, 0.0]) / length_unit
    initial_state = np.concatenate((relative_position, relative_initial))
    time_geo = t_seconds / time_unit

    def rhs(_time, state):
        relative_position = state[:3]
        radius = max(float(np.linalg.norm(relative_position)), contact_geo * 1e-8)
        return np.concatenate((state[3:], -relative_position / radius**3))

    def contact_event(_time, state):
        return float(np.linalg.norm(state[:3]) - contact_geo)

    contact_event.terminal = True
    contact_event.direction = -1
    segments = []
    start_time = 0.0
    state = initial_state
    outcome = "no_contact"
    contact_time_geo = None
    first_contact_time_geo = None
    impact_speed = 0.0
    impact_impulse = 0.0
    impact_impulse_vector = np.zeros(3, dtype=float)
    impact_energy_loss = 0.0
    frozen_state = None
    black_hole_capture = kind1 == "black_hole" or kind2 == "black_hole"
    contact_count = 0
    for _ in range(512):
        solution = solve_ivp(
            rhs,
            (start_time, time_geo[-1]),
            state,
            method="DOP853",
            rtol=2e-11,
            atol=2e-12,
            max_step=max((time_geo[-1] / max(n_steps - 1, 1)) * 8.0, 1e-9),
            dense_output=True,
            events=contact_event,
        )
        if not solution.success:
            raise RuntimeError(f"Newtonian integration failed: {solution.message}")
        segments.append(solution)
        if not len(solution.t_events[0]):
            break
        start_time = float(solution.t_events[0][0])
        state = solution.y_events[0][0].copy()
        contact_count += 1
        if first_contact_time_geo is None:
            first_contact_time_geo = start_time
        normal = state[:3] / max(float(np.linalg.norm(state[:3])), 1e-12)
        inward_speed = float(np.dot(state[3:], normal))
        if inward_speed >= 0.0:
            break
        reduced_mass_fraction = mass_fraction1 * mass_fraction2
        incoming_speed_geo = float(np.linalg.norm(state[3:]))
        impact_speed = max(impact_speed, incoming_speed_geo * C_SI)
        if black_hole_capture:
            impact_impulse += reduced_mass_fraction * incoming_speed_geo * C_SI * total_mass
            impact_impulse_vector -= reduced_mass_fraction * total_mass * C_SI * state[3:]
            impact_energy_loss += 0.5 * reduced_mass_fraction * incoming_speed_geo**2 * total_mass * C_SI**2
            state[3:] = 0.0
            outcome = "captured"
            contact_time_geo = start_time
            frozen_state = state.copy()
            break
        if restitution <= 1e-8 or (restitution < 0.5 and contact_count >= 4):
            impact_impulse += reduced_mass_fraction * incoming_speed_geo * C_SI * total_mass
            impact_impulse_vector -= reduced_mass_fraction * total_mass * C_SI * state[3:]
            impact_energy_loss += 0.5 * reduced_mass_fraction * incoming_speed_geo**2 * total_mass * C_SI**2
            state[3:] = 0.0
            outcome = "merged" if restitution <= 1e-8 else "settled"
            contact_time_geo = start_time
            frozen_state = state.copy()
            break
        impact_energy_loss += 0.5 * reduced_mass_fraction * (1.0 - restitution**2) * inward_speed**2 * total_mass * C_SI**2
        impact_impulse += reduced_mass_fraction * (1.0 + restitution) * abs(inward_speed) * C_SI * total_mass
        impact_impulse_vector -= reduced_mass_fraction * (1.0 + restitution) * inward_speed * normal * C_SI * total_mass
        state[3:] -= (1.0 + restitution) * inward_speed * normal
        outcome = "rebounded"
        contact_time_geo = start_time
        state[:3] = normal * contact_geo * (1.0 + 1e-10)

    relative_position_track = np.zeros((n_steps, 3), dtype=float)
    relative_velocity_track = np.zeros_like(relative_position_track)
    assigned = np.zeros(n_steps, dtype=bool)
    for solution in segments:
        mask = (~assigned) & (time_geo >= solution.t[0] - 1e-12) & (time_geo <= solution.t[-1] + 1e-12)
        if np.any(mask):
            values = solution.sol(time_geo[mask])
            relative_position_track[mask] = values[:3].T
            relative_velocity_track[mask] = values[3:].T
            assigned[mask] = True
    if frozen_state is not None and contact_time_geo is not None:
        after_capture = time_geo > contact_time_geo
        relative_position_track[after_capture] = frozen_state[:3]
        relative_velocity_track[after_capture] = 0.0
        assigned[after_capture] = True
    if not np.all(assigned):
        raise RuntimeError("Newtonian integration did not cover the requested output interval")

    center_position = time_geo[:, None] * center_velocity[None, :]
    position1 = center_position - mass_fraction2 * relative_position_track
    position2 = center_position + mass_fraction1 * relative_position_track
    velocity1 = center_velocity[None, :] - mass_fraction2 * relative_velocity_track
    velocity2 = center_velocity[None, :] + mass_fraction1 * relative_velocity_track
    separation = np.linalg.norm(relative_position_track, axis=1)
    kinetic = 0.5 * (
        mass_fraction1 * np.sum(velocity1**2, axis=1)
        + mass_fraction2 * np.sum(velocity2**2, axis=1)
    )
    potential = -mass_fraction1 * mass_fraction2 / np.maximum(separation, 1e-12)
    energy_norm = kinetic + potential
    angular_vector = (
        mass_fraction1 * np.cross(position1, velocity1)
        + mass_fraction2 * np.cross(position2, velocity2)
    )
    angular_norm = np.linalg.norm(angular_vector, axis=1)
    relative_initial = relative_velocity_track[0]
    relative_final = relative_velocity_track[-1]
    cosine = np.dot(relative_initial, relative_final) / max(
        float(np.linalg.norm(relative_initial) * np.linalg.norm(relative_final)), 1e-30
    )
    deflection_angle = float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))

    pos_geo = np.stack((position1, position2), axis=1)
    t_geo = time_geo
    sep_geo = separation
    energy_scale = float(kinetic[0] + abs(potential[0]))
    capture_fade = np.zeros(n_steps, dtype=float)
    if outcome in {"captured", "merged", "settled"} and contact_time_geo is not None:
        fade_duration = max(0.08 * (time_geo[-1] - contact_time_geo), 1e-12)
        capture_fade = np.clip((time_geo - contact_time_geo) / fade_duration, 0.0, 1.0)

    return NewtonianState(
        t=t_geo,
        x1=pos_geo[:, 0, 0],
        y1=pos_geo[:, 0, 1],
        z1=pos_geo[:, 0, 2],
        x2=pos_geo[:, 1, 0],
        y2=pos_geo[:, 1, 1],
        z2=pos_geo[:, 1, 2],
        vx1=velocity1[:, 0],
        vy1=velocity1[:, 1],
        vz1=velocity1[:, 2],
        vx2=velocity2[:, 0],
        vy2=velocity2[:, 1],
        vz2=velocity2[:, 2],
        energy=energy_norm,
        angular_momentum=angular_norm,
        separation=sep_geo,
        contact_radius=contact_geo,
        deflection_angle=deflection_angle,
        energy_scale=float(energy_scale),
        outcome=outcome,
        contact_time=contact_time_geo,
        first_contact_time=first_contact_time_geo,
        impact_speed=impact_speed,
        impact_impulse=impact_impulse,
        impact_impulse_vector=impact_impulse_vector,
        impact_energy_loss=impact_energy_loss,
        capture_fade=capture_fade,
    )
