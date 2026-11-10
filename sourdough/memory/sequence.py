"""Sequence: which word tends to come next.

Transition counts between words let the baby continue a phrase it has heard
several times, such as "good morning".
"""

from __future__ import annotations

from collections import defaultdict


class Sequence:
    """Directed transition memory, P(next word | this word)."""

    def __init__(self):
        self.out: dict[str, float] = {}
        self.next: defaultdict[str, dict[str, float]] = defaultdict(dict)

    def observe(self, items: list[str]) -> None:
        for a, b in zip(items, items[1:]):
            if a != b:
                self.out[a] = self.out.get(a, 0.0) + 1.0
                self.next[a][b] = self.next[a].get(b, 0.0) + 1.0

    def likely_next(self, a: str) -> tuple[str, float] | None:
        """The most probable follower of ``a`` and how sure that is.

        The +1 in the denominator means a phrase heard once is only a guess.
        """
        links = self.next.get(a)
        if not links:
            return None
        b = max(links, key=links.get)
        return b, links[b] / (self.out[a] + 1.0)

    def decay(self, factor: float, floor: float) -> None:
        for a in list(self.next):
            self.out[a] *= factor
            links = self.next[a]
            for b in list(links):
                links[b] *= factor
                if links[b] < floor:
                    del links[b]
            if not links:
                del self.next[a]
                del self.out[a]

    def __len__(self) -> int:
        return sum(len(v) for v in self.next.values())

    def to_dict(self) -> dict:
        return {"out": self.out, "next": self.next}

    @classmethod
    def from_dict(cls, d: dict) -> "Sequence":
        m = cls()
        m.out = dict(d["out"])
        for a, links in d["next"].items():
            m.next[a] = dict(links)
        return m
