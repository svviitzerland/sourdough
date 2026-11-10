"""Hearing sounds that are not words: a clap, a whistle, a laugh.

Raw audio becomes a log spaced frequency spectrum, a crude cochlea.
"""

from __future__ import annotations

import numpy as np

from .vectors import unit

BANDS = 32


def encode_audio(samples, sample_rate: int = 16000) -> np.ndarray:
    """Encode raw mono audio as the loudness of 32 frequency bands."""
    x = np.asarray(samples, np.float32).ravel()
    if x.size < 64:
        return np.zeros(BANDS, np.float32)
    spectrum = np.abs(np.fft.rfft(x * np.hanning(x.size)))
    freqs = np.fft.rfftfreq(x.size, 1.0 / sample_rate)
    edges = np.geomspace(80, min(8000, sample_rate / 2), BANDS + 1)
    bands = np.zeros(BANDS, np.float32)
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        in_band = (freqs >= lo) & (freqs < hi)
        if in_band.any():
            bands[i] = spectrum[in_band].mean()
    bands = np.log1p(bands)
    return unit(bands - bands.mean())
