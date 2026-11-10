"""Innate senses: fixed encoders that turn the world into numbers.

A newborn has eyes and ears on day one, but no concepts. These encoders play
that role. They never learn and know nothing about the world. Everything the
baby comes to know is learned above them, in the mind and the memory.

Every encoder returns unit length float32 vectors, so comparing two percepts
is a single dot product.
"""

from .sound import encode_audio
from .vision import Sight, load_image, see
from .words import encode_word, tokenize

__all__ = ["Sight", "encode_audio", "encode_word", "load_image", "see", "tokenize"]
