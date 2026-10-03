/* Scientific diagnostics: axes, legends, heatmaps, isometric 3D. */

function _ctx(c) {
  const r = c.getBoundingClientRect();
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  c.width = Math.max(40, r.width * dpr);
  c.height = Math.max(40, r.height * dpr);
  const g = c.getContext("2d");
  g.setTransform(1, 0, 0, 1, 0, 0);
  return g;
}

function paper(g, c) {
  g.fillStyle = "#0b1020";
  g.fillRect(0, 0, c.width, c.height);
}

function margins(c) {
  return { l: 48, r: 12, t: 28, b: 36, w: c.width, h: c.height };
}

function mapX(x, x0, x1, m) {
  return m.l + ((x - x0) / (x1 - x0 || 1e-12)) * (m.w - m.l - m.r);
}
function mapY(y, y0, y1, m) {
  return m.h - m.b - ((y - y0) / (y1 - y0 || 1e-12)) * (m.h - m.t - m.b);
}

function axes(g, m, x0, x1, y0, y1, xlabel, ylabel, title) {
  g.strokeStyle = "rgba(180,200,230,0.35)";
  g.lineWidth = 1;
  g.beginPath();
  g.moveTo(m.l, m.t);
  g.lineTo(m.l, m.h - m.b);
  g.lineTo(m.w - m.r, m.h - m.b);
  g.stroke();
  g.fillStyle = "#c9d4ea";
  g.font = "11px IBM Plex Mono, monospace";
  g.fillText(title, m.l, 16);
  g.fillStyle = "#8b97b8";
  g.font = "10px IBM Plex Mono, monospace";
  g.fillText(xlabel, m.w * 0.45, m.h - 10);
  g.save();
  g.translate(12, m.h * 0.55);
  g.rotate(-Math.PI / 2);
  g.fillText(ylabel, 0, 0);
  g.restore();
  g.fillText(x0.toPrecision(3), m.l, m.h - m.b + 14);
  g.fillText(x1.toPrecision(3), m.w - m.r - 40, m.h - m.b + 14);
}

function catmull(xs, ys, segs) {
  xs = xs || []; ys = ys || [];
  segs = segs || 10;
  if (xs.length < 3) return { x: xs, y: ys };
  const ox = [], oy = [];
  const n = xs.length;
  for (let i = 0; i < n - 1; i++) {
    const p0x = xs[Math.max(0, i - 1)], p0y = ys[Math.max(0, i - 1)];
    const p1x = xs[i], p1y = ys[i];
    const p2x = xs[Math.min(n - 1, i + 1)], p2y = ys[Math.min(n - 1, i + 1)];
    const p3x = xs[Math.min(n - 1, i + 2)], p3y = ys[Math.min(n - 1, i + 2)];
    for (let s = 0; s < segs; s++) {
      const t = s / segs, t2 = t * t, t3 = t2 * t;
      ox.push(0.5 * ((2 * p1x) + (-p0x + p2x) * t + (2 * p0x - 5 * p1x + 4 * p2x - p3x) * t2 + (-p0x + 3 * p1x - 3 * p2x + p3x) * t3));
      oy.push(0.5 * ((2 * p1y) + (-p0y + p2y) * t + (2 * p0y - 5 * p1y + 4 * p2y - p3y) * t2 + (-p0y + 3 * p1y - 3 * p2y + p3y) * t3));
    }
  }
  ox.push(xs[n - 1]); oy.push(ys[n - 1]);
  return { x: ox, y: oy };
}

function line(g, xs, ys, x0, x1, y0, y1, m, color, width, smooth) {
  if (smooth && xs && xs.length > 3) {
    const c = catmull(xs, ys, 8);
    xs = c.x; ys = c.y;
  }
  g.beginPath();
  g.strokeStyle = color;
  g.lineWidth = width || 1.6;
  g.lineJoin = "round";
  g.lineCap = "round";
  for (let i = 0; i < xs.length; i++) {
    const x = mapX(xs[i], x0, x1, m), y = mapY(ys[i], y0, y1, m);
    if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
  }
  g.stroke();
}

function extent(a) {
  let mn = Infinity, mx = -Infinity;
  for (let i = 0; i < a.length; i++) { if (a[i] < mn) mn = a[i]; if (a[i] > mx) mx = a[i]; }
  if (!isFinite(mn)) return [-1, 1];
  const p = (mx - mn) * 0.08 + 1e-18;
  return [mn - p, mx + p];
}

function legend(g, m, items) {
  items.forEach((it, i) => {
    g.fillStyle = it.color;
    g.fillRect(m.w - 118, 10 + i * 14, 10, 3);
    g.fillStyle = "#c9d4ea";
    g.font = "10px IBM Plex Mono, monospace";
    g.fillText(it.label, m.w - 104, 14 + i * 14);
  });
}

function viridis(t) {
  t = Math.max(0, Math.min(1, t));
  const r = Math.floor(68 + 187 * t * t);
  const g = Math.floor(1 + 210 * Math.sqrt(t));
  const b = Math.floor(84 + 140 * (1 - t) * t * 4);
  return [r, Math.min(255, g), Math.min(255, b)];
}

window.SciencePlots = {
  series(canvas, series, xlabel, ylabel, title) {
    const g = _ctx(canvas); paper(g, canvas);
    const m = margins(canvas);
    let xs = [], ys = [];
    series.forEach((s) => { xs = xs.concat(s.x); ys = ys.concat(s.y); });
    const [x0, x1] = extent(xs), [y0, y1] = extent(ys);
    axes(g, m, x0, x1, y0, y1, xlabel, ylabel, title);
    series.forEach((s) => line(g, s.x, s.y, x0, x1, y0, y1, m, s.color, s.width, s.smooth));
    legend(g, m, series);
  },
  traj2d(canvas, p) {
    this.series(canvas, [
      { x: p.x1, y: p.y1, color: "#e74c3c", label: "object A", width: 1.8, smooth: true },
      { x: p.x2, y: p.y2, color: "#27ae60", label: "object B", width: 1.8, smooth: true },
    ], "X [M]", "Y [M]", "Trajectory (equatorial)");
  },
  traj3d(canvas, p) {
    const g = _ctx(canvas); paper(g, canvas);
    const m = margins(canvas);
    // Enhanced 3D isometric projection with better depth perception
    const scale = 0.4;
    const iso = (x, y, z) => ({ x: x + scale * z, y: y + scale * 0.5 * z });
    const pts = [];
    for (let i = 0; i < p.x1.length; i++) {
      pts.push(iso(p.x1[i], p.y1[i], p.z1[i]));
      pts.push(iso(p.x2[i], p.y2[i], p.z2[i]));
    }
    const xs = pts.map((q) => q.x), ys = pts.map((q) => q.y);
    const [x0, x1] = extent(xs), [y0, y1] = extent(ys);
    axes(g, m, x0, x1, y0, y1, "X + 0.4 Z", "Y + 0.2 Z", "Trajectory (3D isometric)");
    const xa = p.x1.map((_, i) => iso(p.x1[i], p.y1[i], p.z1[i]).x);
    const ya = p.x1.map((_, i) => iso(p.x1[i], p.y1[i], p.z1[i]).y);
    const xb = p.x2.map((_, i) => iso(p.x2[i], p.y2[i], p.z2[i]).x);
    const yb = p.x2.map((_, i) => iso(p.x2[i], p.y2[i], p.z2[i]).y);
    const za = p.z1;
    const zb = p.z2;
    // Draw depth-aware lines with varying opacity based on z-depth
    const drawDepthLine = (xs, ys, zs, color) => {
      const zRange = extent(zs);
      for (let i = 0; i < xs.length - 1; i++) {
        const z0 = zs[Math.min(i, zs.length - 1)] || 0;
        const z1 = zs[Math.min(i + 1, zs.length - 1)] || 0;
        const zDepth = (z0 + z1) / 2;
        const depthFactor = 0.4 + 0.6 * ((zDepth - zRange[0]) / (zRange[1] - zRange[0] + 1e-12));
        g.strokeStyle = color;
        g.globalAlpha = depthFactor;
        g.lineWidth = 1.8;
        g.beginPath();
        const px1 = mapX(xs[i], x0, x1, m), py1 = mapY(ys[i], y0, y1, m);
        const px2 = mapX(xs[i+1], x0, x1, m), py2 = mapY(ys[i+1], y0, y1, m);
        g.moveTo(px1, py1);
        g.lineTo(px2, py2);
        g.stroke();
      }
      g.globalAlpha = 1.0;
    };
    // Smooth the curves with Catmull-Rom
    const sa = catmull(xa, ya, 12);
    const sb = catmull(xb, yb, 12);
    drawDepthLine(sa.x, sa.y, catmull(p.x1, p.z1, 12).y, "#e74c3c");
    drawDepthLine(sb.x, sb.y, catmull(p.x2, p.z2, 12).y, "#27ae60");
    // Add start and end markers
    g.fillStyle = "#e74c3c";
    g.beginPath();
    g.arc(mapX(xa[0], x0, x1, m), mapY(ya[0], y0, y1, m), 4, 0, Math.PI * 2);
    g.fill();
    g.fillStyle = "#27ae60";
    g.beginPath();
    g.arc(mapX(xb[0], x0, x1, m), mapY(yb[0], y0, y1, m), 4, 0, Math.PI * 2);
    g.fill();
    legend(g, m, [{ color: "#e74c3c", label: "Object A" }, { color: "#27ae60", label: "Object B" }]);
  },
  orbit3d(canvas, orbit) {
    const g = _ctx(canvas); paper(g, canvas);
    const m = margins(canvas);
    const xs = orbit.x || [], ys = orbit.y || [];
    if (!xs.length || !ys.length) return;
    const [x0, x1] = extent(xs), [y0, y1] = extent(ys);
    axes(g, m, x0, x1, y0, y1, "X [M]", "Y [M]", "Kerr test-particle geodesic · equatorial 3D view");
    line(g, xs, ys, x0, x1, y0, y1, m, "#77e3ff", 2.0, false);
    g.fillStyle = "#f6c177";
    g.beginPath();
    g.arc(mapX(xs[0], x0, x1, m), mapY(ys[0], y0, y1, m), 3.5, 0, Math.PI * 2);
    g.fill();
    g.fillStyle = "#77e3ff";
    g.beginPath();
    g.arc(mapX(xs[xs.length - 1], x0, x1, m), mapY(ys[ys.length - 1], y0, y1, m), 3, 0, Math.PI * 2);
    g.fill();
    legend(g, m, [{ color: "#77e3ff", label: "orbit" }, { color: "#f6c177", label: "start" }]);
  },
  waterfall(canvas, spectrogram) {
    const g = _ctx(canvas); paper(g, canvas);
    const matrix = spectrogram && spectrogram.amp;
    if (!matrix || matrix.length < 2 || !matrix[0] || matrix[0].length < 2) return;
    const times = spectrogram.t || [];
    const freqs = spectrogram.f || [];
    const timeCount = Math.min(matrix.length, 48);
    const freqCount = Math.min(matrix[0].length, 64);
    const maxValue = Math.max(1e-30, ...matrix.flat().map(Number).filter(Number.isFinite));
    const w = canvas.width, h = canvas.height;
    const cx = w * 0.5, baseY = h * 0.68;
    const scale = Math.min(w * 0.31, h * 0.67);
    const heightScale = h * 0.42;
    const sample = (ti, fi) => {
      const row = Math.min(matrix.length - 1, Math.round(ti / (timeCount - 1) * (matrix.length - 1)));
      const col = Math.min(matrix[0].length - 1, Math.round(fi / (freqCount - 1) * (matrix[0].length - 1)));
      return Math.log1p(9 * Math.max(0, Number(matrix[row][col]) || 0) / maxValue) / Math.log(10);
    };
    const point = (ti, fi) => {
      const t = ti / (timeCount - 1), f = fi / (freqCount - 1), amp = sample(ti, fi);
      return { x: cx + (t - f) * scale * 0.78, y: baseY + (t + f) * scale * 0.28 - amp * heightScale };
    };
    for (let ti = timeCount - 2; ti >= 0; ti--) {
      for (let fi = 0; fi < freqCount - 1; fi++) {
        const amp = sample(ti, fi);
        const [r, gv, b] = viridis(amp);
        const corners = [point(ti, fi), point(ti + 1, fi), point(ti + 1, fi + 1), point(ti, fi + 1)];
        g.beginPath();
        g.moveTo(corners[0].x, corners[0].y);
        for (let i = 1; i < corners.length; i++) g.lineTo(corners[i].x, corners[i].y);
        g.closePath();
        g.fillStyle = `rgb(${r},${gv},${b})`;
        g.fill();
        if (ti % 4 === 0) {
          g.strokeStyle = "rgba(225,239,255,0.18)";
          g.lineWidth = 0.5;
          g.stroke();
        }
      }
    }
    g.fillStyle = "#e8eefc";
    g.font = "11px IBM Plex Mono, monospace";
    g.fillText("3D spectrogram waterfall · log-normalized amplitude", 10, 16);
    g.fillStyle = "#8b97b8";
    g.font = "10px IBM Plex Mono, monospace";
    g.fillText(`t: ${Number(times[0] || 0).toPrecision(3)}–${Number(times[times.length - 1] || 0).toPrecision(3)} s`, 10, h - 8);
    g.fillText(`f: 0–${Number(freqs[freqs.length - 1] || 0).toPrecision(3)} Hz`, w - 128, h - 8);
  },
  surface3d(canvas, grid, title, quantity) {
    const g = _ctx(canvas); paper(g, canvas);
    if (!grid) return;
    const z = grid[quantity] || grid.phi || grid.ham || grid.kretschmann;
    if (!z || !z.length || !z[0]) return;
    const n = Math.min(grid.n || z.length, z.length);
    const values = [];
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
      const v = Number(z[j] && z[j][i]);
      if (Number.isFinite(v)) values.push(quantity === "phi" ? Math.abs(v) : v);
    }
    if (!values.length) return;
    const mn = Math.min(...values), mx = Math.max(...values);
    const w = canvas.width, h = canvas.height;
    const cx = w * 0.5, baseY = h * 0.70;
    const scale = Math.min(w * 0.30, h * 0.62);
    const heightScale = scale * 0.78;
    const point = (i, j) => {
      const x = (i / (n - 1) - 0.5) * 2;
      const y = (j / (n - 1) - 0.5) * 2;
      const raw = Number(z[j] && z[j][i]);
      const value = quantity === "phi" ? Math.abs(raw) : raw;
      const height = (value - mn) / (mx - mn + 1e-15);
      return { x: cx + (x - y) * scale * 0.72, y: baseY + (x + y) * scale * 0.30 - height * heightScale };
    };
    for (let j = n - 2; j >= 0; j--) {
      for (let i = 0; i < n - 1; i++) {
        const raw = Number(z[j] && z[j][i]);
        const value = quantity === "phi" ? Math.abs(raw) : raw;
        const t = (value - mn) / (mx - mn + 1e-15);
        const [r, gv, b] = viridis(t);
        const quad = [point(i, j), point(i + 1, j), point(i + 1, j + 1), point(i, j + 1)];
        g.beginPath();
        g.moveTo(quad[0].x, quad[0].y);
        for (let k = 1; k < quad.length; k++) g.lineTo(quad[k].x, quad[k].y);
        g.closePath();
        g.fillStyle = `rgb(${r},${gv},${b})`;
        g.fill();
        if (i % 6 === 0) {
          g.strokeStyle = "rgba(225,239,255,0.14)";
          g.lineWidth = 0.55;
          g.stroke();
        }
      }
    }
    g.strokeStyle = "rgba(220,235,255,0.5)";
    g.lineWidth = 1;
    g.beginPath();
    g.moveTo(cx - scale * 0.72, baseY);
    g.lineTo(cx, baseY + scale * 0.30);
    g.lineTo(cx + scale * 0.72, baseY);
    g.stroke();
    g.fillStyle = "#e8eefc";
    g.font = "11px IBM Plex Mono, monospace";
    g.fillText(title, 10, 16);
    g.fillStyle = "#c9d4ea";
    g.font = "10px IBM Plex Mono, monospace";
    g.fillText("x [M]", cx + scale * 0.62, baseY + 12);
    g.fillText("y [M]", cx - scale * 0.76, baseY + 12);
    g.fillText(quantity === "ham" ? "|H| proxy" : "−Φ / c²", 10, h - 8);
    g.fillStyle = "#8b97b8";
    g.fillText(`${mn.toExponential(1)}  →  ${mx.toExponential(1)}`, w - 155, h - 8);
  },
  renderAll(pack) {
    const S = window.SciencePlots;
    const gp = (id) => document.getElementById(id);
    if (!pack) return;
    const go = (id, fn) => {
      const el = gp(id);
      if (el) {
        fn(el);
        const figure = el.closest(".plot");
        if (figure) figure.classList.add("has-data");
      }
    };
    go("p-traj2d", (el) => S.traj2d(el, pack.traj2d));
    go("p-traj3d", (el) => S.traj3d(el, pack.traj3d));
    go("p-wave-surface", (el) => S.waterfall(el, pack.spectrogram));
    go("p-hp", (el) => S.series(el, [{ x: pack.hp.t, y: pack.hp.y, color: "#f39c12", label: "h₊", width: 1.4 }], "t [s]", "h₊ [dimensionless]", "Gravitational-wave strain h₊"));
    go("p-hc", (el) => S.series(el, [{ x: pack.hc.t, y: pack.hc.y, color: "#3498db", label: "h×", width: 1.4 }], "t [s]", "h×", "Gravitational-wave strain h×"));
    go("p-psi4", (el) => S.series(el, [
      { x: pack.psi4.t, y: pack.psi4.re, color: "#1abc9c", label: "Ψ₄ re (News proxy)", width: 1.2 },
      { x: pack.psi4.t, y: pack.psi4.im, color: "#9b59b6", label: "Ψ₄ im", width: 1.0 },
    ], "t [s]", "Ψ₄ [s⁻²]", "Radiative curvature proxy (−d²h/dt²)"));
    go("p-freq", (el) => S.series(el, [{ x: pack.freq.t, y: pack.freq.y, color: "#e67e22", label: "f_GW", width: 1.5 }], "t [s]", "f [Hz]", "Chirp frequency"));
    go("p-spec", (el) => S.series(el, [{ x: pack.spectrum.f, y: pack.spectrum.a, color: "#8e44ad", label: "|h̃|", width: 1.3 }], "f [Hz]", "|h̃|", "Spectrum"));
    go("p-sep", (el) => S.series(el, [{ x: pack.sep.t, y: pack.sep.y, color: "#2ecc71", label: "r", width: 1.6 }], "t [M]", "r [M]", "Orbital separation"));
    go("p-energy", (el) => S.series(el, [{ x: pack.energy.t, y: pack.energy.y, color: "#e74c3c", label: "E", width: 1.5 }], "t [M]", "E [normalized]", "Orbital energy diagnostic"));
    go("p-ang", (el) => S.series(el, [{ x: pack.angmom.t, y: pack.angmom.y, color: "#f1c40f", label: "L", width: 1.5 }], "t [M]", "L [normalized]", "Orbital angular momentum"));
    go("p-erad", (el) => S.series(el, [{ x: pack.eradiated.t, y: pack.eradiated.y, color: "#ecf0f1", label: "∫h²dt", width: 1.5 }], "t [s]", "∫h²dt [s]", "Accumulated strain power (not E_rad)"));
    go("p-omega", (el) => S.series(el, [{ x: pack.omega.t, y: pack.omega.y, color: "#00cec9", label: "Ω", width: 1.5 }], "t [M]", "Ω", "Orbital frequency"));
    go("p-phase", (el) => S.series(el, [{ x: pack.phase.t, y: pack.phase.y, color: "#e84393", label: "Φ_unwrapped", width: 1.4 }], "t [s]", "Φ [rad]", "Unwrapped GW phase"));
    go("p-strain-amp", (el) => S.series(el, [{ x: pack.strain_amp.t, y: pack.strain_amp.y, color: "#fd79a8", label: "|h|", width: 1.5 }], "t [s]", "|h|", "Strain amplitude envelope"));
    go("p-chirp", (el) => S.series(el, [{ x: pack.chirp_rate.t, y: pack.chirp_rate.y, color: "#00b894", label: "df/dt", width: 1.4 }], "t [s]", "df/dt [Hz/s]", "Chirp rate"));
    go("p-orb-phase", (el) => S.series(el, [{ x: pack.orbital_phase.t, y: pack.orbital_phase.y, color: "#6c5ce7", label: "φ_orb", width: 1.5 }], "t [M]", "φ [rad]", "Orbital phase"));
    go("p-kretschmann", (el) => S.series(el, [{ x: pack.kretschmann.t, y: pack.kretschmann.y, color: "#d63031", label: "K", width: 1.5 }], "t [M]", "K [M⁻⁴]", "Two-center curvature estimate"));
    go("p-early", (el) => S.surface3d(el, pack.slice_early, "Initial field slice", "phi"));
    go("p-mid", (el) => S.surface3d(el, pack.slice_mid, "Intermediate field slice", "phi"));
    go("p-late", (el) => S.surface3d(el, pack.slice_late, "Final field slice", "phi"));
    go("p-ham", (el) => S.surface3d(el, pack.slice_early, "Constraint-shaped proxy", "ham"));
    go("p-curvature-surface", (el) => S.surface3d(el, pack.slice_early, "Two-center curvature landscape", "kretschmann"));
  },
};
