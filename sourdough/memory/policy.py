"""Policy: habits shaped by praise and correction.

Each link goes from something perceived (a word, a color, a shape) to
something the baby did (a word it said, or an ability it used). Praise pushes
the link up and correction pushes it down. This is how it learns replies
("hello" then "bye") and when to use an ability.
"""

from __future__ import annotations

from collections import defaultdict


class Policy:
    """Directed weights from situations to actions, each from -1 to 1."""

    def __init__(self):
        self.w: defaultdict[str, dict[str, float]] = defaultdict(dict)

    def nudge(self, situation: str, action: str, delta: float) -> None:
        value = self.w[situation].get(action, 0.0) + delta
        self.w[situation][action] = max(-1.0, min(1.0, value))

    def neighbors(self, situation: str):
        return self.w.get(situation, {}).items()

    def decay(self, factor: float, floor: float) -> None:
        for a in list(self.w):
            links = self.w[a]
            for b in list(links):
                links[b] *= factor
                if abs(links[b]) < floor:
                    del links[b]
            if not links:
                del self.w[a]

    def __len__(self) -> int:
        return sum(len(v) for v in self.w.values())

    def to_dict(self) -> dict:
        return {"w": self.w}

    @classmethod
    def from_dict(cls, d: dict) -> "Policy":
        m = cls()
        for a, links in d["w"].items():
            m.w[a] = dict(links)
        return m
