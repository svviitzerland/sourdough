"""The body the web host gives the baby.

The brain only decides to use an action. This module carries actions out and
reports what happened, so the brain can learn from the consequence.

* ``explore`` opens a random file from the baby's own ``world`` folder. A
  picture is seen, a text is heard. It can read nothing outside that folder.
* ``glance`` looks through the camera. The browser carries this one out,
  because only the browser has the camera.

To give the baby a different body (motors, lights, an API), write a class like
this one and pass its action names to the brain.
"""

from __future__ import annotations

import base64
from pathlib import Path

import numpy as np

ACTIONS = ("explore", "glance")
PICTURES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
TEXTS = {".txt", ".md"}
MAX_BYTES = 5 * 1024 * 1024


class Body:
    def __init__(self, world: Path, seed: int | None = None):
        self.world = world
        self.rng = np.random.default_rng(seed)

    def explore(self) -> dict | None:
        """Pick something from its world. Returns what it found, or None."""
        if not self.world.is_dir():
            return None
        files = [p for p in self.world.iterdir()
                 if p.is_file() and not p.is_symlink() and not p.name.startswith(".")
                 and p.suffix.lower() in PICTURES | TEXTS and p.stat().st_size <= MAX_BYTES]
        if not files:
            return None
        found = files[self.rng.integers(len(files))]
        if found.suffix.lower() in PICTURES:
            data = found.read_bytes()
            mime = "image/jpeg" if found.suffix.lower() in {".jpg", ".jpeg"} else f"image/{found.suffix[1:].lower()}"
            url = f"data:{mime};base64," + base64.b64encode(data).decode()
            return {"file": found.name, "image": url}
        lines = [ln.strip() for ln in found.read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip()]
        if not lines:
            return None
        return {"file": found.name, "text": lines[self.rng.integers(len(lines))][:200]}
