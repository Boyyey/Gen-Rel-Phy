/* Oscilloscope canvases for strain, spectra, and the master field. */

function resizeCanvas(c) {
  const r = c.getBoundingClientRect();
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  c.width = Math.max(32, r.width * dpr);
  c.height = Math.max(32, r.height * dpr);
  return c.getContext("2d");
}

function clear(ctx, c) {
  ctx.fillStyle = "#05060d";
  ctx.fillRect(0, 0, c.width, c.height);
}

function drawWave(canvas, t, h, tMerge, playFrac) {
  const ctx = resizeCanvas(canvas);
  clear(ctx, canvas);
  if (!t || t.length < 4) return;
  const w = canvas.width, ht = canvas.height;
  let mn = Infinity, mx = -Infinity;
  for (let i = 0; i < h.length; i++) {
    if (h[i] < mn) mn = h[i];
    if (h[i] > mx) mx = h[i];
  }
  const span = Math.max(1e-30, mx - mn);
  ctx.strokeStyle = "rgba(126,224,255,0.15)";
  ctx.beginPath();
  ctx.moveTo(0, ht / 2);
  ctx.lineTo(w, ht / 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.strokeStyle = "#ff8a4a";
  ctx.lineWidth = 1.8;
  const n = Math.min(t.length, h.length);
  for (let i = 0; i < n; i++) {
    const x = ((t[i] - t[0]) / (t[n - 1] - t[0] + 1e-12)) * w;
    const y = ht - ((h[i] - mn) / span) * (ht * 0.82) - ht * 0.09;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
  if (tMerge != null) {
    const x = ((tMerge - t[0]) / (t[n - 1] - t[0] + 1e-12)) * w;
    ctx.strokeStyle = "rgba(246,193,119,0.5)";
    ctx.setLineDash([6, 6]);
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, ht);
    ctx.stroke();
    ctx.setLineDash([]);
  }
  if (playFrac != null) {
    const x = playFrac * w;
    ctx.strokeStyle = "#7ee0ff";
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, ht);
    ctx.stroke();
  }
}

function drawSpectrum(canvas, freq, amp, spectrogram) {
  const ctx = resizeCanvas(canvas);
  clear(ctx, canvas);
  const w = canvas.width, ht = canvas.height;
  const hasSpec = freq && amp && freq.length > 4 && amp.length > 4 && Math.max.apply(null, amp) > 0;
  if (spectrogram && spectrogram.amp && spectrogram.amp.length > 2 && spectrogram.amp[0].length > 4) {
    const rows = spectrogram.amp;
    const cols = rows[0].length;
    const img = ctx.createImageData(w, ht);
    for (let y = 0; y < ht; y++) {
      const ry = Math.min(rows.length - 1, Math.floor((y / ht) * rows.length));
      const row = rows[ry];
      let peak = 1e-30;
      for (let k = 0; k < row.length; k++) peak = Math.max(peak, row[k]);
      for (let x = 0; x < w; x++) {
        const cx = Math.min(cols - 1, Math.floor((x / w) * cols));
        const v = Math.min(1, Math.log10(1 + 9 * row[cx] / peak) );
        const i = (y * w + x) * 4;
        img.data[i] = 20 + 220 * v;
        img.data[i + 1] = 30 + 120 * v;
        img.data[i + 2] = 40 + 210 * v;
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }
  if (!hasSpec) return;
  const n = Math.min(freq.length, amp.length);
  let amax = 1e-30;
  for (let i = 0; i < n; i++) amax = Math.max(amax, amp[i]);
  ctx.beginPath();
  ctx.strokeStyle = "#c084fc";
  ctx.lineWidth = 1.8;
  ctx.lineJoin = "round";
  for (let i = 0; i < n; i++) {
    const x = (i / (n - 1)) * w;
    const y = ht - (amp[i] / amax) * (ht * 0.88) - 6;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
}

function drawSpectrogram(canvas, t, freq, spec_data) {
  const ctx = resizeCanvas(canvas);
  clear(ctx, canvas);
  const w = canvas.width, ht = canvas.height;
  if (!spec_data || !spec_data.length || !spec_data[0]) return;

  const n_time = spec_data.length;
  const n_freq = spec_data[0].length;

  // Find global max for normalization
  let maxVal = 1e-30;
  for (let i = 0; i < n_time; i++) {
    for (let j = 0; j < n_freq; j++) {
      maxVal = Math.max(maxVal, spec_data[i][j]);
    }
  }

  const img = ctx.createImageData(w, ht);
  for (let y = 0; y < ht; y++) {
    const timeIdx = Math.min(n_time - 1, Math.floor((y / ht) * n_time));
    const row = spec_data[timeIdx];
    for (let x = 0; x < w; x++) {
      const freqIdx = Math.min(n_freq - 1, Math.floor((x / w) * n_freq));
      const v = Math.min(1, Math.log10(1 + 9 * row[freqIdx] / maxVal));
      const i = (y * w + x) * 4;
      // Viridis-like colormap
      const r = Math.floor(68 + 187 * v * v);
      const g = Math.floor(1 + 210 * Math.sqrt(v));
      const b = Math.floor(84 + 140 * (1 - v) * v * 4);
      img.data[i] = r;
      img.data[i + 1] = Math.min(255, g);
      img.data[i + 2] = Math.min(255, b);
      img.data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);

  // Add time and frequency labels
  ctx.fillStyle = "#c9d4ea";
  ctx.font = "10px IBM Plex Mono, monospace";
  ctx.fillText("Time →", 10, ht - 6);
  ctx.save();
  ctx.translate(12, ht * 0.5);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("Frequency [Hz]", 0, 0);
  ctx.restore();
}

function drawField(canvas, psi) {
  const ctx = resizeCanvas(canvas);
  clear(ctx, canvas);
  if (!psi || !psi.length) return;
  const ny = psi.length, nx = psi[0].length;
  const w = canvas.width, ht = canvas.height;
  let m = 1e-12;
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) m = Math.max(m, Math.abs(psi[j][i]));
  const img = ctx.createImageData(w, ht);
  for (let y = 0; y < ht; y++) {
    const j = Math.min(ny - 1, Math.floor((y / ht) * ny));
    for (let x = 0; x < w; x++) {
      const i = Math.min(nx - 1, Math.floor((x / w) * nx));
      const v = psi[j][i] / m;
      const i4 = (y * w + x) * 4;
      const pos = Math.max(0, v);
      const neg = Math.max(0, -v);
      img.data[i4] = 255 * pos + 20;
      img.data[i4 + 1] = 30 + 80 * Math.abs(v);
      img.data[i4 + 2] = 255 * neg + 40;
      img.data[i4 + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
}

window.LabCharts = { drawWave, drawSpectrum, drawField, drawSpectrogram };
