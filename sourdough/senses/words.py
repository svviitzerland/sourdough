"""Hearing words.

Words arrive as text, typed or transcribed by the browser's speech
recognition. Each word is encoded by its character n-grams, a stand-in for
its sound, so words that sound alike get similar codes.
"""

from __future__ import annotations

import hashlib
import re

import numpy as np

from .vectors import unit

WORD_DIM = 128


def tokenize(text: str) -> list[str]:
    """Split text into lowercase words."""
    return re.findall(r"[\w']+", text.lower())


def encode_word(word: str) -> np.ndarray:
    """Encode a word so that "cat" and "cap" end up close, like they sound."""
    v = np.zeros(WORD_DIM, np.float32)
    padded = f"<{word}>"
    for n in (1, 2, 3):
        for i in range(len(padded) - n + 1):
            h = _hash(padded[i : i + n])
            v[h % WORD_DIM] += 1.0 if (h >> 32) & 1 else -1.0
    return unit(v)


def _hash(s: str) -> int:
    return int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "little")
