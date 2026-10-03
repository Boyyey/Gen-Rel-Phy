const $ = (id) => document.getElementById(id);
const TYPE = { black_hole: 0, neutron_star: 1, star: 2, mass_sphere: 3, planet: 4 };
const EARTH_MASS_SOLAR = 3.0034896e-6;
const solarMass = (value, kind) => Number(value) * (kind === "planet" ? EARTH_MASS_SOLAR : 1);
const fieldMass = (value, kind) => kind === "planet" ? Number(value) / EARTH_MASS_SOLAR / 10 : Number(value) / 10;

const bh = window.createBlackHoleRenderer($("bh"));
bh.spin = 0.7;
bh.grid = 0.7;
bh.playing = false;
bh.speed = 1;
bh.simMode = "blackhole";

function bindCam(id, key) {
  const el = $(id);
  if (!el) return;
  el.addEventListener("input", () => { bh[key] = Number(el.value); });
}
bindCam("cam-dist", "targetCamDist");
bindCam("cam-az", "targetCamAz");
bindCam("cam-el", "targetCamEl");
$("cam-reset") && $("cam-reset").addEventListener("click", () => {
  bh.targetCamAz = 0.35; bh.targetCamEl = 1.38; bh.targetCamDist = 28;
  bh.camAz = 0.35; bh.camEl = 1.38; bh.camDist = 28;
  $("cam-az").value = 0.35; $("cam-el").value = 1.38; $("cam-dist").value = 28;
});
setInterval(() => {
  if (document.activeElement && String(document.activeElement.id || "").startsWith("cam-")) return;
  $("cam-az").value = bh.targetCamAz;
  $("cam-el").value = bh.targetCamEl;
  $("cam-dist").value = bh.targetCamDist;
}, 200);

function bindRange(id, vid, digits, on) {
  const el = $(id), v = $(vid);
  const upd = () => {
    v.textContent = Number(el.value).toFixed(digits);
    if (on) on(Number(el.value));
  };
  el.addEventListener("input", upd);
  upd();
}

bindRange("m1", "m1v", 1, syncMasses);
bindRange("m2", "m2v", 1, syncMasses);
bindRange("c1", "c1v", 2, (x) => { bh.spin = Math.max(0.05, 0.5 * (x + Number($("c2").value))); });
bindRange("c2", "c2v", 2, (x) => { bh.spin = Math.max(0.05, 0.5 * (x + Number($("c1").value))); });
bindRange("dist", "distv", 0);
bindRange("amp", "ampv", 4);
bindRange("wid", "widv", 1);
bindRange("lam", "lamv", 1);
bindRange("nr", "nrv", 0);
bindRange("geo-mass", "geo-mass-v", 1);
bindRange("geo-spin", "geo-spin-v", 2);
bindRange("geo-r0", "geo-r0-v", 1);
bindRange("kerr-mass", "kerr-mass-v", 1);
bindRange("kerr-spin", "kerr-spin-v", 2);
bindRange("orbit-speed", "orbit-speed-v", 2);

function syncMasses() {
  const kind1 = $("k1").value, kind2 = $("k2").value;
  const m1 = solarMass($("m1").value, kind1), m2 = solarMass($("m2").value, kind2);
  bh.m1 = Math.max(0.25, kind1 === "planet" ? 0.74 : m1 / 10);
  bh.m2 = Math.max(0.25, kind2 === "planet" ? 0.74 : m2 / 10);
  bh.fieldM1 = Math.max(0.02, fieldMass(m1, kind1));
  bh.fieldM2 = Math.max(0.02, fieldMass(m2, kind2));
  bh.type1 = TYPE[kind1] ?? 3;
  bh.type2 = TYPE[kind2] ?? 3;
  $("m1-unit").textContent = kind1 === "planet" ? "M⊕" : "M☉";
  $("m2-unit").textContent = kind2 === "planet" ? "M⊕" : "M☉";
}
["k1", "k2"].forEach((id) => $(id).addEventListener("change", syncMasses));
syncMasses();

$("grid").addEventListener("input", () => { bh.grid = Number($("grid").value); });
$("disk") && $("disk").addEventListener("input", () => { bh.disk = Number($("disk").value); });
$("lens-bh") && $("lens-bh").addEventListener("change", () => {
  bh.centralBH = $("lens-bh").checked ? 1.0 : 0.0;
});

// Simulation mode selector
$("sim-mode") && $("sim-mode").addEventListener("change", (e) => {
  const mode = e.target.value;
  bh.simMode = mode;
  // Set renderer mode uniform (0=BH lensing, 1=collision, 2=scattering, 3=orbit).
  if (mode === "blackhole") {
    bh.simModeVal = 0.0;
    bh.centralBH = 1.0;
    $("lens-bh").checked = true;
    $("tab-binary").classList.remove("collision-mode");
  } else if (mode === "collision") {
    bh.simModeVal = 1.0;
    bh.centralBH = 0.0;
    $("lens-bh").checked = false;
    $("tab-binary").classList.add("collision-mode");
    if (Number($("impact").value) > 1000) {
      $("impact").value = 0;
      $("impact").dispatchEvent(new Event("input"));
    }
  } else if (mode === "scattering") {
    bh.simModeVal = 2.0;
    bh.centralBH = 0.0;
    $("lens-bh").checked = false;
    $("tab-binary").classList.add("collision-mode");
    if (Number($("impact").value) < 1000) {
      $("impact").value = 50000;
      $("impact").dispatchEvent(new Event("input"));
    }
  } else {
    bh.simModeVal = 3.0;
    bh.centralBH = 0.0;
    $("lens-bh").checked = false;
    $("tab-binary").classList.add("collision-mode");
    $("impact").value = 0;
    $("impact").dispatchEvent(new Event("input"));
    if ($("k1").value === "black_hole") $("k1").value = "planet";
    if ($("k2").value === "black_hole") $("k2").value = "planet";
    $("k1").dispatchEvent(new Event("change"));
    $("k2").dispatchEvent(new Event("change"));
  }
  if (mode !== "blackhole") {
    $("hud-rh").textContent = "N/A";
    $("hud-ph").textContent = "N/A";
    $("hud-isco").textContent = "N/A";
    $("hud-chi").textContent = "0.000";
  }
  $("tab-binary").classList.toggle("orbit-mode", mode === "orbit");
});

// Velocity sliders for collision mode
bindRange("v1", "v1v", 0);
bindRange("v2", "v2v", 0);
bindRange("impact", "impactv", 1);

$("btn-pause").addEventListener("click", () => {
  if (playback.completed && playback.track) {
    playback.i = 0;
    playback.acc = 0;
    playback.lastNow = null;
    playback.completed = false;
    applyFrame(0);
  }
  bh.playing = !bh.playing;
  $("btn-pause").textContent = bh.playing ? "PAUSE" : "PLAY";
});
document.querySelectorAll("[data-spd]").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("[data-spd]").forEach((b) => b.classList.remove("on"));
    btn.classList.add("on");
    bh.speed = Number(btn.dataset.spd);
    if (playback.completed && playback.track) {
      playback.i = 0;
      playback.acc = 0;
      playback.lastNow = null;
      playback.completed = false;
      applyFrame(0);
    }
    bh.playing = true;
    $("btn-pause").textContent = "PAUSE";
  });
});

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("on"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("on"));
    btn.classList.add("on");
    $("tab-" + btn.dataset.tab).classList.add("on");
  });
});

function setStatus(s) { $("status").textContent = s; }

async function post(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function metricBlock(obj) {
  return Object.entries(obj)
    .map(([k, v]) => `${k}: <b>${typeof v === "number" ? v.toPrecision(4) : v}</b>`)
    .join("<br/>");
}

let currentMechanics = null;
function renderMechanics(data = currentMechanics) {
  currentMechanics = data;
  const panel = document.querySelector(".mechanics-readout");
  if (!panel) return;
  panel.hidden = !data;
  if (!data) return;
  const sample = data[$("mechanics-phase").value] || data.closest;
  const vector = (values) => "(" + values.map((value) => Number(value).toExponential(3)).join(", ") + ")";
  const impact = data.impact;
  $("mechanics-metrics").innerHTML = metricBlock({
    "r⃗₂₁ [m]": vector(sample.separation_m),
    "v⃗₂₁ [m/s]": vector(sample.relative_velocity_m_s),
    "|v₂₁| [m/s]": sample.relative_speed_m_s,
    "v radial [m/s]": sample.radial_speed_m_s,
    "v tangential [m/s]": sample.tangential_speed_m_s,
    "F⃗ on A [N]": vector(sample.force_on_object_a_n),
    "a⃗ A [m/s²]": vector(sample.acceleration_a_m_s2),
    "a⃗ B [m/s²]": vector(sample.acceleration_b_m_s2),
    "p⃗ system [kg m/s]": vector(sample.system_momentum_kg_m_s),
    "K [J]": sample.kinetic_energy_j,
    "Ugrav [J]": sample.potential_energy_j,
    "Etotal [J]": sample.total_energy_j,
    "|L⃗| [kg m²/s]": Math.hypot(...sample.orbital_angular_momentum_kg_m2_s),
    "impact outcome": impact.outcome,
    "impact speed [km/s]": impact.relative_impact_speed_m_s / 1000,
    "J⃗ on B [N s]": vector(impact.impulse_vector_n_s),
    "|J| [N s]": impact.normal_impulse_n_s,
    "energy dissipated [J]": impact.kinetic_energy_lost_j,
  });
}
$("mechanics-phase").addEventListener("change", () => renderMechanics());

const playback = { track: null, wave: null, i: 0, acc: 0, lastNow: null, completed: false };

function applyFrame(i) {
  const tr = playback.track;
  if (!tr) return;
  const n = tr.t.length;
  i = Math.max(0, Math.min(n - 1, i));
  playback.i = i;
  const m = tr.m1 + tr.m2;
  bh._driven = true;

  if (bh.simMode === "blackhole") {
    bh.sep = tr.r[i] / m;
    bh.phase = tr.phi[i];
    bh.m1 = Math.max(0.25, tr.m1 / 10);
    bh.m2 = Math.max(0.25, tr.m2 / 10);
    bh.fieldM1 = tr.m1 / 10;
    bh.fieldM2 = tr.m2 / 10;
    bh.type1 = tr.gpu1 != null ? tr.gpu1 : (TYPE[tr.kind1] ?? 0);
    bh.type2 = tr.gpu2 != null ? tr.gpu2 : (TYPE[tr.kind2] ?? 0);
    const st = tr.stages[i];
    bh.merger = st === "ringdown" || st === "merger" ? (st === "ringdown" ? 1.0 : 0.7) : 0.0;
    bh.wave = st === "inspiral" || st === "merger" || st === "ringdown" ? 1.0 : 0.25;
    bh.simModeVal = 0.0;
    $("hud-stage").textContent = st.toUpperCase();
  } else {
    // Newtonian collision/scattering mode
    bh.phase = tr.phi[i];
    bh.m1 = Math.max(0.25, tr.kind1 === "planet" ? 0.74 : tr.m1 / 10);
    bh.m2 = Math.max(0.25, tr.kind2 === "planet" ? 0.74 : tr.m2 / 10);
    bh.fieldM1 = Math.max(0.02, fieldMass(tr.m1, tr.kind1));
    bh.fieldM2 = Math.max(0.02, fieldMass(tr.m2, tr.kind2));
    bh.type1 = TYPE[tr.kind1] ?? 0;
    bh.type2 = TYPE[tr.kind2] ?? 0;
    const displayRadius = (type, mass) => type === 4 ? 3.4 : [2.05, 3.35, 5.5, 4.15][type] * mass;
    const visualContact = displayRadius(bh.type1, bh.m1) + displayRadius(bh.type2, bh.m2);
    const physicalContact = Math.max(Number(tr.contact_radius) || 1, 1e-9);
    const currentRatio = Math.max(1, tr.r[i] / physicalContact);
    const initialRatio = Math.max(1, tr.r[0] / physicalContact);
    const compression = Math.log1p(currentRatio - 1) / Math.max(Math.log1p(initialRatio - 1), 1e-9);
    bh.sep = visualContact + (30 - visualContact) * Math.min(1, compression);
    bh.merger = tr.capture_fade ? tr.capture_fade[i] : 0.0;
    bh.wave = 0.25;
    bh.simModeVal = bh.simMode === "collision" ? 1.0 : (bh.simMode === "orbit" ? 3.0 : 2.0);
    $("hud-stage").textContent = (tr.stages[i] || bh.simMode).toUpperCase();
  }

  $("hud-sep").textContent = (bh.simMode === "blackhole" ? tr.r[i] / m : tr.r[i]).toFixed(2) + " M";
  $("hud-e").textContent = Number(tr.energy[i]).toPrecision(3);
  $("hud-l").textContent = Number(tr.angular_momentum[i]).toPrecision(3);
  setStatus(bh.simMode === "blackhole" ? (tr.stages[i] || "ORBIT").toUpperCase() : bh.simMode.toUpperCase());
  if (playback.wave) {
    window.LabCharts.drawWave($("wave"), playback.wave.t, playback.wave.hp, playback.wave.t_merge, i / (n - 1));
  }
}

function tickPlayback(now) {
  requestAnimationFrame(tickPlayback);
  if (!playback.track || !bh.playing || playback.completed) {
    playback.lastNow = now;
    return;
  }
  const n = playback.track.t.length;
  if (playback.lastNow == null) playback.lastNow = now;
  const elapsed = Math.min(0.1, Math.max(0, (now - playback.lastNow) / 1000));
  playback.lastNow = now;
  playback.acc += elapsed * bh.speed * 180;
  const advance = Math.floor(playback.acc);
  if (advance < 1) return;
  playback.acc -= advance;
  playback.i = Math.min(n - 1, playback.i + advance);
  applyFrame(playback.i);
  if (playback.i === n - 1) {
    playback.completed = true;
    bh._driven = false;
    setStatus("SIMULATION COMPLETE");
  }
}
requestAnimationFrame(tickPlayback);

$("run-binary").addEventListener("click", () => runEvolve(false));
$("fast-track") && $("fast-track").addEventListener("click", () => runEvolve(true));

async function runEvolve(fast = false) {
  setStatus("EVOLVING GEOMETRY");
  $("run-binary").disabled = true;
  if ($("fast-track")) $("fast-track").disabled = true;
  try {
    const body = {
      m1: solarMass($("m1").value, $("k1").value),
      m2: solarMass($("m2").value, $("k2").value),
      chi1: Number($("c1").value),
      chi2: Number($("c2").value),
      distance_mpc: Number($("dist").value),
      kind1: $("k1").value,
      kind2: $("k2").value,
      sim_mode: $("sim-mode") ? $("sim-mode").value : "blackhole",
      v1: Number($("v1") ? $("v1").value : 30),
      v2: Number($("v2") ? $("v2").value : 25),
      impact_parameter: Number($("impact") ? $("impact").value : 5),
      orbit_speed_fraction: Number($("orbit-speed").value),
      restitution: Number($("impact-response").value),
    };
    const data = await post("/api/evolve", body);
    playback.track = data.timeline;
    playback.wave = data.waveform;
    playback.i = 0;
    playback.acc = 0;
    playback.lastNow = null;
    playback.completed = false;

    if (fast) {
      // Fast track: jump to end immediately
      bh.playing = false;
      playback.i = playback.track.t.length - 1;
      applyFrame(playback.i);
      playback.completed = true;
      setStatus("SIMULATION COMPLETE");
    } else {
      bh.playing = true;
      $("btn-pause").textContent = "PAUSE";
      applyFrame(0);
    }

    const f = data.features;
    window.LabCharts.drawWave($("wave"), data.waveform.t, data.waveform.hp, data.waveform.t_merge, 0);
    window.LabCharts.drawSpectrum($("spec"), f.spectrum_freq, f.spectrum_amp, f.spectrogram);
    if (f.spectrogram && f.spectrogram.amp && f.spectrogram.amp.length > 0) {
      window.LabCharts.drawSpectrogram($("spectrogram"), f.spectrogram.t, f.spectrum_freq, f.spectrogram.amp);
    }
    if (data.plots && window.SciencePlots) {
      window.SciencePlots.renderAll(data.plots);
      if (data.plots.spectrum) {
        window.LabCharts.drawSpectrum($("spec"), data.plots.spectrum.f, data.plots.spectrum.a, f.spectrogram);
      }
      if (data.plots.slice_early && data.plots.slice_early.phi) {
        window.LabCharts.drawField($("field"), data.plots.slice_early.phi);
      }
    }

    const metrics = {
      "simulation mode": body.sim_mode,
      "object A": body.kind1,
      "object B": body.kind2,
    };

    if (body.sim_mode === "blackhole") {
      metrics["remnant mass / M☉"] = data.remnant.mass;
      metrics["remnant spin χ"] = data.remnant.spin;
      metrics["horizon / M"] = data.remnant.horizon;
      metrics["ISCO / M"] = data.remnant.isco;
      metrics["E_rad / M"] = data.waveform.radiated_energy_frac;
      metrics["peak strain"] = f.peak_amp;
      metrics["f_peak"] = f.f_peak;
      metrics["chirp rate"] = f.chirp_rate;
      metrics["QNM f"] = f.qnm_freq;
    } else {
      const closestApproach = Math.min(...data.timeline.r);
      const contact = data.timeline.contact_radius;
      const durationSeconds = data.timeline.t[data.timeline.t.length - 1] * (body.m1 + body.m2) * 4.925490947e-6;
      const energy = data.timeline.energy;
      const firstContact = data.timeline.first_contact_time;
      const firstContactIndex = firstContact == null ? -1 : data.timeline.t.findIndex((time) => time >= firstContact);
      const conservativeCount = firstContactIndex < 0 ? energy.length : Math.max(2, firstContactIndex);
      const conservativeEnergy = energy.slice(0, conservativeCount);
      const energyDrift = Math.max(...conservativeEnergy.map((value) => Math.abs(value - conservativeEnergy[0]))) / Math.max(data.timeline.energy_scale, 1e-15);
      const peakSpeed = Math.max(
        ...data.timeline.vx1.map((vx, i) => Math.hypot(vx, data.timeline.vy1[i], data.timeline.vz1[i])),
        ...data.timeline.vx2.map((vx, i) => Math.hypot(vx, data.timeline.vy2[i], data.timeline.vz2[i])),
      );
      if (body.sim_mode === "orbit") {
        metrics["orbit speed / circular"] = body.orbit_speed_fraction;
      } else {
        metrics["initial speeds"] = `${body.v1} / ${body.v2} km/s`;
        metrics["impact parameter"] = body.impact_parameter + " km";
      }
      metrics["closest approach"] = closestApproach.toPrecision(4) + " M";
      metrics["surface contact radius"] = contact.toPrecision(4) + " M";
      metrics["run duration"] = durationSeconds.toPrecision(4) + " s";
      metrics["encounter outcome"] = data.timeline.outcome === "no_contact" ? "gravitational flyby" : data.timeline.outcome;
      if (body.sim_mode === "scattering") metrics["deflection angle"] = data.timeline.deflection_angle_deg.toPrecision(4) + " deg";
      if (data.timeline.outcome !== "no_contact") {
        metrics["impact speed"] = (data.timeline.impact_speed_m_s / 1000).toPrecision(4) + " km/s";
        metrics["impact impulse"] = data.timeline.impact_impulse_n_s.toExponential(3) + " N s";
        metrics["impact energy loss"] = data.timeline.impact_energy_loss_j.toExponential(3) + " J";
      }
      metrics["peak component speed"] = peakSpeed.toPrecision(4) + " c";
      metrics["pre-impact numerical energy drift"] = (100 * energyDrift).toPrecision(3) + "%";
      if (peakSpeed > 0.1) metrics["model warning"] = "Newtonian dynamics exceed 0.1c; use only as a qualitative comparison";
      metrics["wave strain model"] = "leading-order quadrupole; no backreaction";
    }

    $("bin-metrics").innerHTML = metricBlock(metrics);
    renderMechanics(data.mechanics || null);

    if (body.sim_mode === "blackhole") {
      bh.spin = Math.max(0.05, data.remnant.spin);
      $("hud-rh").textContent = data.remnant.horizon.toFixed(3) + " M";
      $("hud-ph").textContent = data.remnant.photon.toFixed(3) + " M";
      $("hud-isco").textContent = data.remnant.isco.toFixed(3) + " M";
      $("hud-chi").textContent = data.remnant.spin.toFixed(3);
    } else {
      // Hide BH-specific HUD elements in collision mode
      $("hud-rh").textContent = "N/A";
      $("hud-ph").textContent = "N/A";
      $("hud-isco").textContent = "N/A";
      $("hud-chi").textContent = "0.000";
    }
  } catch (e) {
    setStatus("FAULT");
    $("bin-metrics").textContent = String(e);
  } finally {
    $("run-binary").disabled = false;
    if ($("fast-track")) $("fast-track").disabled = false;
  }
}

$("run-perturb").addEventListener("click", async () => {
  setStatus("INTEGRATING Ψ");
  $("run-perturb").disabled = true;
  bh.wave = 1.0;
  try {
    const data = await post("/api/perturb", {
      amplitude: Number($("amp").value),
      packet_width: Number($("wid").value),
      nonlinear_lambda: Number($("lam").value),
      n_r: Number($("nr").value),
      t_end: 90,
    });
    const field = data.field;
    const f = data.features;
    window.LabCharts.drawWave($("wave"), field.t, field.strain, null);
    window.LabCharts.drawSpectrum($("spec"), f.spectrum_freq, f.spectrum_amp, f.spectrogram);
    window.LabCharts.drawField($("field"), field.psi);
    $("pert-metrics").innerHTML = metricBlock({
      parity: field.parity,
      "ℓ": field.ell,
      ε: field.amplitude,
      "λ_nl": field.nonlinear_lambda,
      "Δr*": field.dr,
      E_proxy: field.diagnostics.radiated_energy_proxy,
      "peak h": f.peak_amp,
      f_peak: f.f_peak,
    });
    setStatus("WAVE EXTRACTED");
  } catch (e) {
    setStatus("FAULT");
    $("pert-metrics").textContent = String(e);
  } finally {
    $("run-perturb").disabled = false;
  }
});

$("run-inverse").addEventListener("click", async () => {
  setStatus("MATCHED FILTERING");
  $("run-inverse").disabled = true;
  try {
    const data = await post("/api/inverse", {
      m1: solarMass($("m1").value, $("k1").value),
      m2: solarMass($("m2").value, $("k2").value),
      chi1: Number($("c1").value),
      chi2: Number($("c2").value),
    });
    window.LabCharts.drawWave($("wave"), data.t, data.recovered_hp, null);
    $("inv-metrics").innerHTML = metricBlock({
      "recovered m1": data.m1,
      "recovered m2": data.m2,
      "recovered χ1": data.chi1,
      "recovered χ2": data.chi2,
      mismatch: data.mismatch,
      "hidden m1": data.truth.m1,
      "hidden m2": data.truth.m2,
    });
    setStatus("INFERENCE COMPLETE");
  } catch (e) {
    setStatus("FAULT");
    $("inv-metrics").textContent = String(e);
  } finally {
    $("run-inverse").disabled = false;
  }
});

document.querySelectorAll("[data-exp]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const name = btn.dataset.exp;
    const output = $(btn.dataset.output || "campaign-log");
    setStatus("CAMPAIGN / " + name.toUpperCase());
    output.textContent = "running " + name + " …";
    try {
      const r = await fetch("/api/experiments/" + name);
      output.textContent = JSON.stringify(await r.json(), null, 2);
      setStatus("CAMPAIGN READY");
    } catch (e) {
      output.textContent = String(e);
      setStatus("FAULT");
    }
  });
});

$("run-geodesic").addEventListener("click", async () => {
  const button = $("run-geodesic");
  button.disabled = true;
  setStatus("INTEGRATING GEODESIC");
  try {
    const data = await post("/api/geodesic", {
      mass: Number($("geo-mass").value),
      spin: Number($("geo-spin").value),
      r0: Number($("geo-r0").value),
      lam_span: 250,
    });
    window.SciencePlots.orbit3d($("geo-chart"), data);
    $("geo-metrics").innerHTML = metricBlock({
      "orbit type": data.kind,
      "samples": data.r.length,
      "pericenter / M": Math.min(...data.r),
      "start radius / M": data.r[0],
      "conserved quantity drift": data.conserved_error,
    });
    setStatus("GEODESIC COMPLETE");
  } catch (e) {
    $("geo-metrics").textContent = String(e);
    setStatus("FAULT");
  } finally {
    button.disabled = false;
  }
});

$("run-kerr").addEventListener("click", async () => {
  const button = $("run-kerr");
  button.disabled = true;
  setStatus("MAPPING KERR SPIN");
  try {
    const mass = Number($("kerr-mass").value);
    const spins = Array.from({ length: 11 }, (_, i) => i * 0.099);
    const sweep = await Promise.all(spins.map((spin) => post("/api/kerr", { mass, spin })));
    const selected = await post("/api/kerr", { mass, spin: Number($("kerr-spin").value) });
    window.SciencePlots.series($("kerr-chart"), [
      { x: spins, y: sweep.map((v) => v.horizon / mass), color: "#f39c12", label: "r+ horizon", width: 1.7 },
      { x: spins, y: sweep.map((v) => v.photon / mass), color: "#67d7ff", label: "photon orbit", width: 1.7 },
      { x: spins, y: sweep.map((v) => v.isco / mass), color: "#50d890", label: "ISCO", width: 1.7 },
    ], "dimensionless spin χ", "radius [M]", "Kerr characteristic radii vs spin");
    $("kerr-chart").closest(".panel").classList.add("has-chart");
    $("kerr-metrics").innerHTML = metricBlock({
      "selected χ": Number($("kerr-spin").value),
      "outer horizon / M": selected.horizon / mass,
      "inner horizon / M": selected.inner_horizon / mass,
      "photon orbit / M": selected.photon / mass,
      "ISCO / M": selected.isco / mass,
      "horizon angular frequency × M": selected.omega_h * mass,
      "ℓ=2, n=0 QNM / Hz": selected.qnm.f / 4.925490947e-6,
      "QNM damping time / s": selected.qnm.tau * 4.925490947e-6,
    });
    setStatus("KERR MAP COMPLETE");
  } catch (e) {
    $("kerr-metrics").textContent = String(e);
    setStatus("FAULT");
  } finally {
    button.disabled = false;
  }
});

async function refreshKerr() {
  const chi = 0.5 * (Number($("c1").value) + Number($("c2").value));
  try {
    const data = await post("/api/kerr", { mass: 1, spin: chi });
    $("hud-rh").textContent = data.horizon.toFixed(3) + " M";
    $("hud-ph").textContent = data.photon.toFixed(3) + " M";
    $("hud-isco").textContent = data.isco.toFixed(3) + " M";
    $("hud-chi").textContent = chi.toFixed(3);
    bh.spin = Math.max(0.12, chi);
  } catch (_) { /* */ }
}
["c1", "c2"].forEach((id) => $(id).addEventListener("change", refreshKerr));
refreshKerr();

// Export functionality
$("export-data") && $("export-data").addEventListener("click", () => {
  if (!playback.track) {
    alert("No simulation data to export. Run a simulation first.");
    return;
  }

  const exportData = {
    timestamp: new Date().toISOString(),
    simulation: {
      mode: bh.simMode,
      m1_msun: solarMass($("m1").value, $("k1").value),
      m2_msun: solarMass($("m2").value, $("k2").value),
      chi1: Number($("c1").value),
      chi2: Number($("c2").value),
      kind1: $("k1").value,
      kind2: $("k2").value,
      distance_mpc: Number($("dist").value),
      orbit_speed_fraction: Number($("orbit-speed").value),
      restitution: Number($("impact-response").value),
    },
    timeline: playback.track,
    waveform: playback.wave,
  };

  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `dynamical_spacetime_${Date.now()}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  setStatus("DATA EXPORTED");
});

$("launch-enter").addEventListener("click", () => {
  const selected = document.querySelector('input[name="launch-mode"]:checked');
  const mode = selected ? selected.value : "blackhole";
  $("launch-gate").classList.add("dismissed");

  if (mode === "perturb") {
    document.querySelector('[data-tab="perturb"]').click();
    setStatus("PERTURBATION READY");
    return;
  }

  $("sim-mode").value = mode;
  if (mode === "collision" || mode === "scattering") {
    $("k1").value = "mass_sphere";
    $("k2").value = "mass_sphere";
    $("impact").value = mode === "scattering" ? 50000 : 0;
    $("impact").dispatchEvent(new Event("input"));
  } else if (mode === "orbit") {
    $("k1").value = "planet";
    $("k2").value = "planet";
    $("m1").value = 10;
    $("m2").value = 8;
    $("impact-response").value = 0.25;
  } else {
    $("k1").value = "black_hole";
    $("k2").value = "black_hole";
  }
  $("k1").dispatchEvent(new Event("change"));
  $("k2").dispatchEvent(new Event("change"));
  $("sim-mode").dispatchEvent(new Event("change"));
  document.querySelector('[data-tab="binary"]').click();
  setStatus(mode === "blackhole" ? "BINARY MODEL READY" : mode.toUpperCase() + " READY");
});
