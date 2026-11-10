"""Storage: where each baby lives on disk.

Every baby gets its own folder. By default the folders live in
``~/.sourdough/brains``, which you can move by setting ``SOURDOUGH_HOME``::

    ~/.sourdough/brains/<name>/
        brain.json          what it knows (concepts, links, feelings)
        journal.jsonl       what happened, one line per moment
        snapshots/          a copy of brain.json after each sleep
        world/              its own folder of pictures and texts to explore

Everything is plain JSON. A brain can be read with any tool, versioned with
git, or copied to a friend, like sharing a sourdough starter.

The ``world`` folder is the baby's playground. Put pictures (png, jpg) or
short texts (txt, md) in it, and the baby may explore them on its own. It can
read nothing outside this folder.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np

from .brain import Brain
from .memory import Journal

KEEP_SNAPSHOTS = 14
SAMPLE_TEXT = """hello little one. look, a red star. the cat says meow.
halo sayang. lihat, bintang merah. kucing bilang meong.
"""


def home() -> Path:
    """The folder that holds every baby."""
    return Path(os.environ.get("SOURDOUGH_HOME", Path.home() / ".sourdough")) / "brains"


def babies(root: Path | None = None) -> list["Nest"]:
    """Every baby that has been born in this home, most recently active first."""
    root = root or home()
    if not root.exists():
        return []
    nests = [Nest(p.name, root) for p in root.iterdir() if (p / "brain.json").exists()]
    return sorted(nests, key=lambda n: n.brain_file.stat().st_mtime, reverse=True)


class Nest:
    """One baby's folder: its brain, journal, snapshots and world."""

    def __init__(self, name: str = "sourdough", root: Path | None = None):
        if not re.fullmatch(r"[\w.-]+", name):
            raise ValueError("a name may only use letters, digits, dots, dashes and underscores")
        self.name = name
        self.folder = (root or home()) / name
        self.brain_file = self.folder / "brain.json"
        self.world = self.folder / "world"
        self.journal = Journal(self.folder / "journal.jsonl")

    @property
    def exists(self) -> bool:
        return self.brain_file.exists()

    def load(self) -> Brain:
        """The saved brain, or a newborn if there is none yet."""
        return Brain.load(self.brain_file) if self.exists else Brain()

    def save(self, brain: Brain) -> None:
        brain.save(self.brain_file)

    def create(self, level: str = "newborn", seed: int = 0) -> Brain:
        """Give birth to this baby, grown to a level, with a world to explore."""
        from .foundation.lessons import grow

        brain = Brain(seed=seed)
        reports = grow(brain, level, seed=seed)
        self.save(brain)
        self.seed_world(seed)
        self.journal.write("born", level=level, age=brain.age, lessons=reports)
        return brain

    def seed_world(self, seed: int = 0) -> None:
        """Put a few pictures and a short text in its world folder."""
        from .foundation.lessons import PALETTE, SHAPES, draw

        self.world.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(seed)
        for i in range(6):
            shape = SHAPES[rng.integers(len(SHAPES))]
            color = PALETTE[rng.integers(len(PALETTE))]
            draw(shape, color, rng).save(self.world / f"picture-{i + 1}.png")
        (self.world / "words.txt").write_text(SAMPLE_TEXT, encoding="utf-8")

    def snapshot(self, brain: Brain) -> Path:
        """Keep a dated copy, so you can see how it grew or roll it back."""
        folder = self.folder / "snapshots"
        path = folder / f"age-{brain.age:06d}.json"
        brain.save(path)
        for old in sorted(folder.glob("age-*.json"))[:-KEEP_SNAPSHOTS]:
            old.unlink()
        return path
