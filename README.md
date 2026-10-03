# Dynamical Spacetime
A computational general-relativity laboratory

<img width="1877" height="742" alt="Screenshot 2026-10-03 164909" src="https://github.com/user-attachments/assets/5741f22e-27f6-402d-9e26-44ebd9a2f73e" />
<img width="1860" height="687" alt="Screenshot 2026-10-03 165134" src="https://github.com/user-attachments/assets/6e92bb7b-fba8-4909-844a-2ff699a63798" />
## Project Title
**Dynamical Spacetime: A Computational Investigation of Nonlinear Gravitational Dynamics and Gravitational-Wave Information**

## Hypothesis
We hypothesize that by evolving linearized gravitational perturbations on a fixed Schwarzschild background using the Regge–Wheeler and Zerilli master equations, and by constructing phenomenological binary-black-hole waveforms from post-Newtonian inspiral through quasinormal ringdown, we can extract meaningful physical information about the source parameters (masses, spins) from the gravitational-wave strain signal alone. Furthermore, we hypothesize that controlled nonlinear perturbations will reveal when linearized gravity breaks down, providing insight into mode coupling and energy transfer in strongly curved spacetimes.

## Why This Project Is Useful
1. **Educational Tool**: Provides a hands-on computational laboratory for students to explore general relativity, gravitational waves, and spacetime dynamics without requiring access to supercomputers.
2. **Research Instrument**: Enables systematic investigation of how gravitational radiation encodes source information, supporting the development of matched-filter templates used in LIGO/Virgo observations.
3. **Method Development**: Demonstrates rigorous numerical methods (convergence testing, validation against analytic solutions) that are foundational to computational physics.
4. **Accessible Science**: Makes advanced gravitational-wave physics accessible to undergraduate researchers and high school students interested in computational astrophysics.
5. **Bridge to Research**: Serves as a stepping stone toward full numerical relativity by building intuition for linearized gravity, perturbation theory, and waveform extraction.

## Why This Project Is Advanced
1. **Rigorous Physics**: Implements genuine reductions of the linearized Einstein equation (Regge–Wheeler and Zerilli equations) on curved spacetime, not toy models.
2. **Multiple Physics Layers**: Combines exact Kerr/Schwarzschild metrics, linearized perturbation evolution, nonlinear coupling terms, post-Newtonian inspiral, and Newtonian mechanics in a unified framework.
3. **Numerical Sophistication**: Uses adaptive DOP853 integration, leapfrog schemes on tortoise coordinates, convergence testing across spatial resolutions, and regression testing.
4. **Inverse Problem Solving**: Performs physics-based matched-template parameter recovery from gravitational-wave data without machine learning, demonstrating genuine inference.
5. **Original Visualization**: Features a custom WebGL raymarching renderer with gravitational lensing, Doppler beaming, redshift, photon rings, and real-time geodesic integration.
6. **Comprehensive Diagnostics**: Provides 22 diagnostic graphs analyzing worldlines, strain polarizations, spectra, energy flux, orbital quantities, and curvature invariants.
7. **Validation Standards**: Cross-checks against published quasinormal mode frequencies, analytic loci, and geometric invariants.

---

**Core question.** How does a perturbed curved spacetime dynamically evolve, and what physical information is encoded in the gravitational radiation it produces?

This is more than a black-hole animation: it is a student-built computational-physics laboratory. It evolves linearized gravitational perturbations on a fixed Schwarzschild background, integrates Newtonian two-body encounters, generates a phenomenological compact-binary waveform, extracts spectra and ringdown diagnostics, tests convergence, and inverts \(h(t)\) for source parameters.

> We didn't program a picture of a black hole. We programmed the physics that makes the picture exist.

---

## What this actually computes

Einstein's equation

\[
G_{\mu\nu} = 8\pi T_{\mu\nu}
\]

says that energy–momentum and spacetime geometry determine each other. This laboratory studies several controlled levels of that problem; it does not evolve the full geometry of a binary black-hole spacetime.

The project does **not** claim a full 3+1 BSSN evolution of two black holes in vacuum (that is a multi-year research-code problem). It claims something more defensible, and scientifically sharper:

1. **Exact geometries.** Schwarzschild and Kerr, including horizons, photon spheres, ISCO, frame dragging, and the Kretschmann scalar.
2. **Linearized dynamical gravity.** The Regge–Wheeler and Zerilli master equations — the genuine reduction of the linearized Einstein equation on Schwarzschild — evolved with a leapfrog scheme on the tortoise line.
3. **Nonlinear probe.** A controlled quadratic source \(\lambda\Psi^2\) used to ask when linearity fails (mode coupling, excess radiated energy).
4. **Binary gravitational waves.** A 3PN energy-balance inspiral attached to a Kerr remnant quasinormal ringdown, with remnant mass and spin from numerical-relativity-inspired maps.
5. **Newtonian mechanics lab.** Earth-mass rocky planets, bound orbit-to-contact initial conditions, positive-energy gravitational scattering, adaptive DOP853 relative-orbit integration, finite-size impacts with restitution/merge outcomes, and SI vector/energy/momentum component analysis.
6. **Gravitational radiation diagnostic.** Newtonian tracks produce leading-order quadrupole strain at a chosen distance. It is diagnostic only; radiation reaction is not fed back into the orbit.
7. **Inverse problem.** Physics-based matched-template inference: given only \(h(t)\), recover masses and spins by mismatch minimization. No machine learning.
8. **Validation.** Analytic loci, published \(\ell=2\) Schwarzschild QNMs, convergence checks, and regression tests for contact and non-contact scattering.

The cinematic renderer is labeled as visualization. The science lives in the Python package `dynamica`.

The browser opens on an experiment chooser and never starts a simulation by itself. The laboratory provides **Evolve**, **Perturb**, **Inverse**, **Campaign**, **Geodesics**, **Kerr Lab**, and **Validate** workspaces. Evolve includes Newtonian collision, scattering, and bound-orbit modes; the mechanics inspector resolves AP Physics C vector components in SI units. The formula reference is separate from diagnostics. Graph captions identify units and approximations; spatial fields are shaded 3D surfaces and spectra are a 3D time-frequency waterfall.

---

## Install and run

Python 3.10+ recommended.

```bash
cd Gen-Rel-Phy
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -e .
```

Launch the interactive laboratory (browser). The first screen asks which experiment to configure. Choosing a path does not start a run; adjust parameters and explicitly press its run button:

```bash
python -m dynamica.cli serve
```


### Newtonian Controls and Units

- Planet masses are entered in Earth masses and use an approximate rocky mass-radius law; other object masses use solar masses. Radial speeds and impact parameter use km/s and km. Bound-orbit mode initializes at apocenter with a selected fraction of circular speed. Since Newtonian gravity is conservative, collision occurs only when that orbit's periapsis intersects the surfaces.
- Collision response is selectable: elastic rebound, damped rebound, or merge/stick. If either object is a black hole, contact is treated as capture and the renderer freezes/fades the pair into a remnant-like visual. This is an absorbing-radius proxy, not event-horizon evolution.
- Scattering starts far enough away to have positive relative orbital energy when nonzero speeds are supplied. Masses, radii, positions, and velocities are converted from SI inputs to total-mass geometric units before integration; returned time and positions use those same units. The scene compresses large separations logarithmically; plotted tracks do not.
- Newtonian energy is normalized by \(Mc^2\), and angular momentum by \(GM^2/c\). The interface reports energy drift as a numerical diagnostic, not as evidence of a fully relativistic encounter.
- The orange accretion-disk slider controls the black-hole lensing preview. Newtonian modes show the two-object gravity grid and suppress the disk.
Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Run the research campaign:

```bash
python -m dynamica.cli campaign --quick -o results/campaign.json
python -m dynamica.cli validate
pytest -q
```

---

## Laboratory map

```
Einstein field equations
        │
        ▼
exact Kerr / Schwarzschild          linearized 1+1D solver (RW / Zerilli)
        │                                      │
        └──────────────┬───────────────────────┘
                       ▼
              dynamical evolution
                       │
                       ▼
              gravitational waves h(t)
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
   spectral analysis            energy / flux
         │                           │
         └─────────────┬─────────────┘
                       ▼
              physical inference
```

| Path | Role |
|---|---|
| `dynamica/metrics/` | Exact Schwarzschild & Kerr |
| `dynamica/geodesics/` | Timelike / null integrators |
| `dynamica/perturbations/` | Potentials, RW/Zerilli evolution, QNMs |
| `dynamica/waveforms/` | 3PN–IMR strain, Newtonian encounter integration, and feature extraction |
| `dynamica/inverse/` | Matched-template parameter recovery |
| `dynamica/lab/` | Controlled experiment campaign |
| `dynamica/analysis/` | Science plots and convergence testing |
| `app/` | FastAPI + Interstellar-grade WebGL booth UI |
| `docs/` | Methods, scope, features, and ISEF-facing science writeup |
| `tests/` | Analytic and solver checks |

---

## Experiments (the actual research)

| Experiment | Question |
|---|---|
| Known solutions | Do horizons, ISCO, photon sphere, Kretschmann, and \(\omega_{\rm QNM}\) match analytic GR? |
| Amplitude scan | How do radiated energy and spectrum scale with \(\varepsilon\), with and without \(\lambda\Psi^2\)? |
| Wavelength scan | How does packet width change the outgoing wave? |
| Spin ringdown | How does Kerr rotation shift \(f_{\rm QNM}\) and \(\tau\)? |
| Mass ratio | How does \(q = m_2/m_1\) change chirp, peak strain, remnant? |
| Binary spins | How does aligned spin change radiated energy and ringdown? |
| Convergence | Does \(N_r = 201,401,801\) produce a measurable order of accuracy? |
| Mode coupling | Does nonlinearity generate extra spectral structure? |
| Inverse recovery | How much of \((m_1,m_2,\chi_1,\chi_2)\) is encoded in \(h(t)\)? |

These are the plots and tables that belong on an ISEF poster — not screenshots of a glowing disk.


