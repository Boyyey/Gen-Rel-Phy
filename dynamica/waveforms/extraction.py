"""Waveform feature extraction: peaks, chirp, spectrum, ringdown fit."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from dynamica.constants import trapz
from scipy.fft import rfft, rfftfreq
from scipy.optimize import curve_fit
from scipy.signal import get_window, hilbert


@dataclass
class WaveFeatures:
    peak_amp: float
    peak_time: float
    f_peak: float
    chirp_rate: float
    radiated_proxy: float
    qnm_freq: float
    qnm_tau: float
    bandwidth: float
    spectrum_freq: list
    spectrum_amp: list
    spectrogram: dict

    def to_public(self) -> dict:
        return {
            "peak_amp": self.peak_amp,
            "peak_time": self.peak_time,
            "f_peak": self.f_peak,
            "chirp_rate": self.chirp_rate,
            "radiated_proxy": self.radiated_proxy,
            "qnm_freq": self.qnm_freq,
            "qnm_tau": self.qnm_tau,
            "bandwidth": self.bandwidth,
            "spectrum_freq": self.spectrum_freq,
            "spectrum_amp": self.spectrum_amp,
            "spectrogram": self.spectrogram,
        }


def _inst_freq(t: np.ndarray, h: np.ndarray) -> np.ndarray:
    analytic = hilbert(h)
    phase = np.unwrap(np.angle(analytic))
    return np.gradient(phase, t) / (2.0 * np.pi)


def extract_features(t: np.ndarray, h: np.ndarray, t_merge: float | None = None) -> WaveFeatures:
    t = np.asarray(t, dtype=float)
    h = np.asarray(h, dtype=float)
    env = np.abs(hilbert(h))
    i_peak = int(np.argmax(env))
    peak_amp = float(env[i_peak])
    peak_time = float(t[i_peak])
    if t_merge is None:
        t_merge = peak_time

    f_inst = _inst_freq(t, h)
    f_peak = float(np.clip(f_inst[i_peak], 0, 1e6))
    # chirp rate before merger
    pre = t < t_merge
    if np.count_nonzero(pre) > 8:
        p = np.polyfit(t[pre][-200:], f_inst[pre][-200:], 1)
        chirp = float(p[0])
    else:
        chirp = 0.0

    radiated = float(trapz(h**2, t))

    # Ringdown fit after peak
    post = t > peak_time
    qnm_f, qnm_tau = f_peak, 0.0
    if np.count_nonzero(post) > 20:
        tp = t[post] - peak_time
        hp = h[post]

        def model(tt, a, wr, wi, ph):
            return a * np.exp(-wi * tt) * np.cos(wr * tt + ph)

        try:
            popt, _ = curve_fit(
                model,
                tp[: min(len(tp), 400)],
                hp[: min(len(hp), 400)],
                p0=(hp[0] if hp[0] != 0 else peak_amp, 2 * np.pi * max(f_peak, 1e-3), 1.0 / (tp[20] + 1e-6), 0.0),
                maxfev=4000,
            )
            qnm_f = float(abs(popt[1]) / (2 * np.pi))
            qnm_tau = float(1.0 / abs(popt[2])) if popt[2] != 0 else 0.0
        except Exception:
            pass

    dt = float(np.median(np.diff(t))) if len(t) > 1 else 1.0
    window = get_window("hann", len(h))
    spec = np.abs(rfft(h * window))
    freq = rfftfreq(len(h), d=dt)
    # downsample spectrum
    step = max(1, len(freq) // 512)
    bandwidth = float(np.sqrt(np.average((freq - np.average(freq, weights=spec + 1e-30)) ** 2, weights=spec + 1e-30)))

    # coarse spectrogram
    nseg = 48
    L = max(32, len(h) // nseg)
    hops = max(1, L // 2)
    rows = []
    ts = []
    for i0 in range(0, len(h) - L, hops):
        seg = h[i0 : i0 + L] * get_window("hann", L)
        rows.append(np.abs(rfft(seg))[: L // 4])
        ts.append(float(t[i0 + L // 2]))
    specgram = {
        "t": ts,
        "f": rfftfreq(L, d=dt)[: L // 4].tolist(),
        "amp": np.array(rows).tolist() if rows else [],
    }

    return WaveFeatures(
        peak_amp=peak_amp,
        peak_time=peak_time,
        f_peak=f_peak,
        chirp_rate=chirp,
        radiated_proxy=radiated,
        qnm_freq=qnm_f,
        qnm_tau=qnm_tau,
        bandwidth=bandwidth,
        spectrum_freq=freq[::step].tolist(),
        spectrum_amp=spec[::step].tolist(),
        spectrogram=specgram,
    )
