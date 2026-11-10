"""Seeing.

Vision is split into two streams, as in the primate brain: one for **color**
and one for **shape**. Each stream has its own concepts, so a word can attach
to just one of them. That is what lets "red" and "triangle" be learned apart
and then combined to describe a red triangle never seen before.

The baby looks only at the center of the view (its fovea), where a held up
object usually is, and separates the figure from the background.
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass

import numpy as np
from PIL import Image

from .vectors import unit

FOVEA = 0.6   # fraction of the view's center the baby attends to
EYE = 48      # the fovea is seen at 48 by 48 pixels


@dataclass
class Sight:
    """What the eyes report about one view."""

    color: np.ndarray
    shape: np.ndarray
    swatch: str       # a tiny picture of the color, for display
    silhouette: str   # a tiny picture of the shape, for display


def load_image(image) -> Image.Image:
    """Accept a PIL image, a file path, a data URL, raw bytes or an RGB array."""
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, np.ndarray):
        return Image.fromarray(image.astype(np.uint8)).convert("RGB")
    if isinstance(image, str) and image.startswith("data:"):
        image = base64.b64decode(image.split(",", 1)[1])
    if isinstance(image, bytes):
        image = io.BytesIO(image)
    return Image.open(image).convert("RGB")


def fovea(image: Image.Image, size: int = EYE) -> Image.Image:
    """Crop the center of view."""
    w, h = image.size
    side = int(min(w, h) * FOVEA)
    left, top = (w - side) // 2, (h - side) // 2
    return image.crop((left, top, left + side, top + side)).resize((size, size))


def see(image) -> Sight:
    """Look at the center of an image and report its color and its shape.

    The figure is whatever differs from the background, which is estimated
    from the edges of the view. If nothing stands out, the whole view counts.
    """
    view = fovea(load_image(image))
    rgb = np.asarray(view, np.float32) / 255.0
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    background = np.median(border, axis=0)
    figure = np.linalg.norm(rgb - background, axis=-1) > 0.25
    if figure.sum() < 12:
        figure = np.ones_like(figure)
    return Sight(
        color=_color(view, figure),
        shape=_shape(figure),
        swatch=_png(Image.new("RGB", (8, 8), _mean_color(rgb, figure))),
        silhouette=_png(Image.fromarray(figure.astype(np.uint8) * 255).resize((32, 32))),
    )


def _color(view: Image.Image, figure: np.ndarray) -> np.ndarray:
    """Hue, split by brightness and vividness, plus four shades of gray.

    Brightness separates orange from brown. Vividness separates red from pink.
    """
    hsv = np.asarray(view.convert("HSV"), np.float32)[figure] / 255.0
    hue, sat, val = hsv[:, 0], hsv[:, 1], hsv[:, 2]
    colorful = (sat > 0.25) & (val > 0.2)
    hue_bin = (hue[colorful] * 12 + 0.5).astype(int) % 12
    bright = (val[colorful] > 0.65).astype(int)
    vivid = (sat[colorful] > 0.6).astype(int)
    hues = np.bincount(hue_bin * 4 + bright * 2 + vivid, minlength=48)
    grays = np.bincount(np.minimum((val[~colorful] * 4).astype(int), 3), minlength=4)
    return unit(np.concatenate([hues, 2 * grays]).astype(np.float32))


def _shape(figure: np.ndarray) -> np.ndarray:
    """Describe a silhouette whatever its color, size, position or tilt.

    Walk around the figure and measure how far its edge is from its center.
    A circle gives a flat line, a square four bumps, a triangle three, a star
    five. Two summaries of that profile make the code: how the distances are
    spread, and how strong each number of bumps is (a Fourier spectrum, which
    stays the same when the shape is rotated).
    """
    ys, xs = np.nonzero(figure)
    cy, cx = ys.mean(), xs.mean()
    angle = np.arctan2(ys - cy, xs - cx)
    radius = np.hypot(ys - cy, xs - cx)
    sector = ((angle + np.pi) / (2 * np.pi) * 64).astype(int) % 64
    profile = np.zeros(64, np.float32)
    np.maximum.at(profile, sector, radius)
    empty = profile == 0
    if empty.any() and not empty.all():
        known = np.flatnonzero(~empty)
        profile[empty] = np.interp(np.flatnonzero(empty), known, profile[known], period=64)
    profile /= max(float(profile.max()), 1e-6)

    spread = np.histogram(profile, bins=8, range=(0.2, 1.0001))[0].astype(np.float32)
    bumps = np.abs(np.fft.rfft(profile - profile.mean()))[1:9] / 64
    return unit(np.concatenate([unit(spread), 6.0 * bumps]))


def _mean_color(rgb: np.ndarray, figure: np.ndarray) -> tuple[int, int, int]:
    r, g, b = (rgb[figure].mean(axis=0) * 255).astype(int)
    return int(r), int(g), int(b)


def _png(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
