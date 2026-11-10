"""Storage: where each baby lives on disk.

Every baby is a character of its own, with its own folder. By default the
folders live in ``~/.sourdough/brains``, which you can move by setting
``SOURDOUGH_HOME``::

    ~/.sourdough/
        current             the name of the baby opened last
        brains/<name>/
            profile.json    who it is: name, description, color, how it started
            brain.json      what it knows (concepts, links, feelings)
            journal.jsonl   what happened, one line per moment
            snapshots/      a copy of brain.json after each sleep
            world/          its own folder of pictures and texts to explore
        trash/              deleted babies, kept so they can be restored

Everything is plain JSON. A brain can be read with any tool, versioned with
git, or copied to a friend, like sharing a sourdough starter.

Every baby is born as a newborn knowing nothing. A starting pack (toddler,
preschooler, kid) is optional and only applies at birth: it runs the
built-in lessons once. After that, the baby only grows from what you teach.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .brain import Brain
from .memory import Journal

KEEP_SNAPSHOTS = 14
COLORS = ("peach", "sky", "lilac", "mint", "rose")
SAMPLE_TEXT = """hello little one. look, a red star. the cat says meow.
halo sayang. lihat, bintang merah. kucing bilang meong.
"""


def root() -> Path:
    """The folder that holds everything: babies, trash and the current choice."""
    return Path(os.environ.get("SOURDOUGH_HOME", Path.home() / ".sourdough"))


def home() -> Path:
    """The folder that holds every baby."""
    return root() / "brains"


def babies(folder: Path | None = None) -> list["Nest"]:
    """Every baby in this home, most recently active first."""
    folder = folder or home()
    if not folder.exists():
        return []
    nests = [Nest(p.name, folder) for p in folder.iterdir() if (p / "brain.json").exists()]
    return sorted(nests, key=lambda n: n.brain_file.stat().st_mtime, reverse=True)


def remember_current(name: str | None, folder: Path | None = None) -> None:
    """Note which baby was opened last, so the next start opens it again."""
    path = (folder or home()).parent / "current"
    path.parent.mkdir(parents=True, exist_ok=True)
    if name:
        path.write_text(name)
    elif path.exists():
        path.unlink()


def current(folder: Path | None = None) -> str | None:
    """The baby opened last, if it still exists."""
    path = (folder or home()).parent / "current"
    if path.exists():
        name = path.read_text().strip()
        if Nest.valid(name) and Nest(name, folder).exists:
            return name
    found = babies(folder)
    return found[0].name if found else None


class Nest:
    """One baby's folder: its profile, brain, journal, snapshots and world."""

    def __init__(self, name: str = "sourdough", folder: Path | None = None):
        if not self.valid(name):
            raise ValueError("a name may only use letters, digits, dots, dashes and underscores")
        self.name = name
        self.folder = (folder or home()) / name
        self.brain_file = self.folder / "brain.json"
        self.profile_file = self.folder / "profile.json"
        self.world = self.folder / "world"
        self.journal = Journal(self.folder / "journal.jsonl")

    @staticmethod
    def valid(name: str) -> bool:
        return bool(re.fullmatch(r"[\w.-]{1,40}", name or ""))

    @property
    def exists(self) -> bool:
        return self.brain_file.exists()

    def load(self) -> Brain:
        """The saved brain, or a newborn if there is none yet."""
        return Brain.load(self.brain_file) if self.exists else Brain()

    def save(self, brain: Brain) -> None:
        """Save the brain, and keep a short summary in the profile."""
        brain.save(self.brain_file)
        profile = self.profile()
        profile.update(age=brain.age, stage=brain.stage(), words=len(brain.vocabulary()))
        self._write_profile(profile)

    def create(self, level: str = "newborn", about: str = "", color: str = "",
               seed: int = 0) -> Brain:
        """Give birth to this baby. Every baby starts as a newborn.

        ``level`` is an optional starting pack. Anything other than newborn
        runs that level's lessons once, right now, and never again.
        """
        from .foundation.lessons import grow

        if self.exists:
            raise ValueError(f"{self.name} already exists")
        self.folder.mkdir(parents=True, exist_ok=True)
        self._write_profile({
            "name": self.name,
            "about": about.strip()[:200],
            "color": color if color in COLORS else COLORS[sum(map(ord, self.name)) % len(COLORS)],
            "start": level,
            "born": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        brain = Brain(seed=seed)
        reports = grow(brain, level, seed=seed, who=self.name)
        self.save(brain)
        self.seed_world(seed)
        self.journal.write("born", level=level, age=brain.age, lessons=reports)
        return brain

    def profile(self) -> dict:
        """Who this baby is. Older folders without a profile get a plain one."""
        if self.profile_file.exists():
            return json.loads(self.profile_file.read_text())
        return {"name": self.name, "about": "", "color": COLORS[0], "start": "newborn"}

    def describe(self, about: str | None = None, color: str | None = None) -> dict:
        """Change the description or color."""
        profile = self.profile()
        if about is not None:
            profile["about"] = about.strip()[:200]
        if color in COLORS:
            profile["color"] = color
        self._write_profile(profile)
        return profile

    def delete(self) -> Path:
        """Move this baby to the trash, where it can still be restored by hand."""
        trash = self.folder.parent.parent / "trash"
        trash.mkdir(parents=True, exist_ok=True)
        target = trash / f"{self.name}-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.move(str(self.folder), target)
        return target

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

    def _write_profile(self, profile: dict) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        self.profile_file.write_text(json.dumps(profile, ensure_ascii=False, indent=2))
