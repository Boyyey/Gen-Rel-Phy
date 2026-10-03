# DYNAMICAL SPACETIME — Feature Documentation

## Core Visualization Features

### Interactive 3D Black Hole Renderer
- **Real-time WebGL raymarching** with gravitational lensing
- **Geodesic light bending** using Schwarzschild geodesic equations
- **Accretion disk physics** with:
  - Doppler beaming (relativistic boosting)
  - Gravitational redshift
  - Frame dragging for Kerr (rotating) black holes
  - Volumetric disk with turbulent structure
  - Spiral arm patterns based on Keplerian rotation
- **Photon ring** visualization (critical impact parameter)
- **Smooth camera controls** with damping:
  - Drag to orbit azimuthally
  - Shift-drag to change elevation
  - Mouse wheel for zoom
  - AZ/EL/Distance sliders for precise control
  - RESET VIEW button for default Gargantua angle

### Object Types
Five visual object types are supported. Their scope depends on the selected simulation model:

1. **Black Hole** (Event Horizon)
   - Schwarzschild radius: 2.05 M
   - No light emission (captures all rays)
   - Full accretion disk visualization
   - Forms Kerr remnant after merger

2. **Neutron Star**
   - Radius: 3.35 M (compact but visible)
   - Thermal emission with blue-white color
   - No event horizon (light escapes)
   - Rim lighting for 3D appearance

3. **Star**
   - Radius: 5.5 M (largest visual size)
   - Yellow-white stellar emission
   - Standard stellar appearance
   - No event horizon

4. **Mass Sphere**
   - Radius: 4.15 M (intermediate compactness)
   - Gray metallic appearance
   - Generic compact object
   - No event horizon

5. **Rocky Planet**
   - Mass entered in Earth masses and converted to solar masses for integration
   - Approximate Earth-normalized mass-radius power law
   - Rocky teal surface shader
   - Newtonian finite-size collision/orbit experiments

## Diagnostic Plots (22 Total)

### Worldline Visualization
1. **3D Trajectory** — Spatial worldlines with depth-aware rendering
2. **3D Spectrogram Waterfall** — Windowed amplitude across time and frequency

### Gravitational Wave Diagnostics
3. **Strain h₊(t)** — Plus polarization with merger time marker
4. **Strain h×(t)** — Cross polarization
5. **Ψ₄ News Proxy** — Newman-Penrose scalar (−ḧ) showing wave acceleration
6. **Chirp Frequency** — GW frequency evolution through inspiral-merger-ringdown
7. **Spectrum |h̃(f)|** — Frequency-domain amplitude
8. **Spectrogram** — Time-frequency evolution (waterfall plot)
9. **Unwrapped Phase** — GW phase evolution without 2π jumps
10. **Strain Amplitude** — Envelope |h| = √(h₊² + h×²)
11. **Chirp Rate** — df/dt showing frequency acceleration

### Orbital Dynamics
12. **Separation r(t)** — Binary separation in geometric units
13. **Binding Energy** — E = -½ηM/r
14. **Angular Momentum** — L = η√(Mr)
15. **Orbital Frequency** — Ω from PN evolution
16. **Orbital Phase** — φ(t) evolution

### Newtonian Mechanics and AP Physics C
- **Bound orbit & impact** — Start at apocenter with a configurable fraction of circular speed; contact only occurs if the resulting periapsis reaches the object surfaces.
- **Planet masses** — Entered in Earth masses; approximate rocky mass-radius relation converts to finite contact radii.
- **Scattering** — Positive-energy incoming states with periapsis and standard relative-velocity deflection angle.
- **Impact response** — Elastic, damped restitution, merge/stick, or automatic absorbing-radius capture when a black-hole object is selected.
- **Component calculations** — SI position/velocity/force/acceleration vectors, system momentum, kinetic/potential/total energy, angular momentum, impact speed, impulse, and dissipated energy at initial/closest/final states.
- **Capture animation** — Freeze at the capture event, fade the bodies, and show a remnant-like visual. This is a qualitative effect, not horizon-time evolution.

### Curvature and Energy
17. **Radiated Energy** — Cumulative ∫h² dt proxy
18. **Kretschmann Scalar** — K = 48M²/r⁶ curvature invariant along path

### Spatial Slices (Heatmaps)
19. **Early Potential** — Two-body potential at initial separation (two distinct wells)
20. **Mid Potential** — During inspiral (wells merging)
21. **Late Potential** — Remnant configuration (single deep well)
22. **Constraint Proxy** — |H| approximation for Hamiltonian constraint

## Physics Engine Features

### Binary Waveform Generation
- **3.0PN TaylorT4** orbital frequency evolution
- **Energy balance** radiation reaction
- **Smooth inspiral-merger-ringdown** attachment
- **Kerr remnant QNM** ringdown with:
  - NR-inspired remnant mass/spin maps
  - Spin-dependent QNM frequencies
  - Exponential damping

### Perturbation Solver
- **Regge-Wheeler** (odd parity) and **Zerilli** (even parity) equations
- **Tortoise coordinate** r* evolution
- **Leapfrog integration** on non-uniform grid
- **Optional nonlinear coupling** λΨ² term for mode coupling studies
- **Initial Gaussian wave packets** with configurable width/amplitude

### Inverse Problem
- **Matched-template parameter recovery**
- **Mismatch minimization** without machine learning
- **Recover masses and spins** from h(t) alone
- **Physics-based optimization**

### Experiment Campaign
1. **Known Solutions** — Validate against analytic Schwarzschild/Kerr
2. **Convergence** — Multi-resolution convergence study
3. **Amplitude Scan** — Nonlinear threshold investigation
4. **Wavelength Scan** — Packet width effects
5. **Spin Ringdown** — Kerr QNM spin dependence
6. **Mass Ratio** — q effects on waveform
7. **Binary Spins** — Aligned spin effects
8. **Mode Coupling** — Nonlinear mode generation

## Technical Specifications

### Numerical Methods
- **Finite difference** leapfrog scheme
- **Catmull-Rom spline** interpolation for smooth curves
- **FFT-based spectral analysis** with Hann windowing
- **Hilbert transform** for instantaneous frequency
- **Curve fitting** for QNM extraction

### Performance
- **Real-time 60 FPS** WebGL rendering
- **200 geodesic steps** per ray
- **Dynamic resolution** scaling for performance
- **Downsampled data transmission** (max 4000 points)

### Data Format
- **JSON API** for all communication
- **Geometric units** (G = c = 1) internally
- **Detector units** (solar masses, Mpc, Hz) for user interface
- **16-bit floating point** color precision in WebGL

## Usage Workflow

1. **Configure Objects** — Select types, masses, spins for both bodies
2. **Set Detector** — Distance in Mpc, inclination angle
3. **Evolve Spacetime** — Run full inspiral-merger-ringdown simulation
4. **Analyze Results** — View 21 diagnostic plots simultaneously
5. **Explore Physics** — Change parameters and compare
6. **Run Campaigns** — Systematic parameter sweeps
7. **Inverse Analysis** — Recover parameters from waveforms

## Scientific Validity

### What Is Computed Exactly
- Schwarzschild horizon, ISCO, photon sphere
- Kerr ISCO, ergosphere, frame dragging
- Regge-Wheeler/Zerilli linearized perturbations
- 3PN orbital dynamics
- Kerr QNM frequencies (published fits)

### What Is Phenomenological
- Full nonlinear Einstein equations (not solved)
- BSSN numerical relativity merger (not implemented)
- IMR waveform attachment (smooth but approximate)
- NR-inspired remnant maps (fit formulas)
- Newtonian black-hole capture uses an absorbing Schwarzschild-radius proxy, not GR horizon dynamics
- Rocky-planet material impacts do not model fragmentation, deformation, tides, or thermal transport
- Rendered gravity-grid warping is visual-only and does not modify integrated forces

### Validation Strategy
- Analytic solution comparison
- Convergence testing
- Conservation monitoring
- Published QNM benchmarks
