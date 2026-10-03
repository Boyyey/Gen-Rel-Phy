# Numerical methods

## Units

Geometrized units \(G=c=1\). Solar-mass conversion \(GM_\odot/c^3 \approx 4.925490947\times 10^{-6}\,\mathrm{s}\) restores detector-frame time and strain.

## Background geometries

Schwarzschild and Kerr (Boyer–Lindquist) are implemented as exact closed-form metrics. Horizon, photon orbit, ISCO, Lense–Thirring \(\omega\), and Kretschmann \(48M^2/r^6\) are evaluated, not fitted.

## Master-function evolution

Odd parity (spin-weight \(s=2\)):

\[
\partial_t^2\Psi - \partial_{r_*}^2\Psi + V_\ell^{\mathrm{RW}}(r)\Psi = \lambda\Psi^2
\]

with tortoise \(r_* = r + 2M\ln|r/2M-1|\). Even parity uses the Zerilli potential. Spatial operator: second-order centered differences. Time: leapfrog with CFL \(<1/2\). Inner boundary: ingoing (horizon). Outer: Sommerfeld outgoing. Strain proxy at a large-\(r_*\) observer: \(\Psi/r\). Energy proxy: \(\int \dot\Psi^2\,dt\).

The \(\lambda\) term is a **deliberate model** for nonlinear mode coupling, not a claim of the quadratic Einstein operator in a specific gauge.

## Quasinormal modes

Schwarzschild \(\ell=2,3,4\) fundamental frequencies are published high-precision values. Kerr \(\ell=m=2,n=0\) uses a polynomial fit constrained to the Schwarzschild limit, of Berti–Cardoso–Will type. Ringdown:

\[
h(t) = \sum_n A_n e^{-\omega_I^{(n)} t}\cos(\omega_R^{(n)} t + \phi_n).
\]

## Binary IMR

TaylorT4 3PN \(\dot x\) with a leading spin-orbit term, quadrupole amplitude \(4\eta x\), attachment at remnant ISCO to the Kerr fundamental QNM. Remnant \((M_f,a_f)\) from a compact NR-inspired map (equal-spin aligned). This is a laboratory waveform family, not LIGO production.

## Inverse problem

Mismatch

\[
\mathcal{M}(h,g) = 1 - \frac{(h|g)}{\sqrt{(h|h)(g|g)}}
\]

with a flat inner product, minimized by differential evolution over \((m_1,m_2,\chi_1,\chi_2)\).

## Convergence

Three grids with refinement factor 2. Observed order

\[
p = \frac{\log(|Q_c-Q_m|/|Q_m-Q_f|)}{\log 2}.
\]

## Visualization

The WebGL disk is a GPU ray march with Schwarzschild-like deflection, a Kerr-dependent photon-ring radius, Doppler beaming, and spin-dependent ISCO. It is for the booth. All claims in the paper must come from `dynamica`, not from the shader.

## Newtonian encounter mechanics

The collision, scattering, and bound-orbit modes integrate the relative two-body equation

\[
\ddot{\mathbf r}=-\frac{G(m_1+m_2)}{r^3}\mathbf r
\]

with adaptive DOP853 in total-mass geometric units. User masses, radii, velocities, and times are converted from SI at the solver boundary. Scattering starts with positive relative orbital energy when the input speeds are nonzero. Bound-orbit mode starts at apocenter with tangential speed \(f v_{\rm circ}\), where \(v_{\rm circ}=\sqrt{GM/r}\); the Newtonian orbit remains conservative until a finite-radius impact.

Contact is located as a terminal ODE event. The restitution coefficient \(e\) changes the normal relative speed to \(-e v_n\); for a contact pair, the model reports impulse and the idealized loss \(\Delta K=\frac12\mu v_n^2(1-e^2)\). Repeated low-restitution impacts settle after a small number of impacts. The merge/stick option removes relative motion at contact. If either body is marked as a black hole, the Schwarzschild-radius sum is used as an absorbing capture boundary and the relative state is frozen.

The black-hole capture boundary is a Newtonian absorbing-radius proxy; the fade is a qualitative renderer effect. Neither is relativistic horizon evolution, time dilation, ringdown, or a two-hole Einstein-equation solution. The rocky-planet radius uses an approximate Earth-normalized mass-radius power law. Material strength, fragmentation, tides, and heat transport are not solved.

For AP Physics C analysis, the API samples initial, closest-approach, and final states and reconstructs SI vectors for force, acceleration, momentum, kinetic/potential/total energy, and orbital angular momentum. Impact summaries report peak relative speed, impulse, restitution, and translational energy lost. The rendered gravity mesh is not fed back into the force integrator.
