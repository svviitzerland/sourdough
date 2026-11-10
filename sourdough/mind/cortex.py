"""Cortex: a map of concepts that grows from nothing.

A cortex starts with zero concepts. Each percept is compared with every
concept it knows.

* similar enough (at or above the *vigilance* level) means it is recognized,
  and that concept drifts slightly toward the new example
* not similar enough means it is something new, and a new concept is born

This is the core idea of Adaptive Resonance Theory (Carpenter and Grossberg,
1987). It learns online from single examples and never needs a dataset or
training epochs, and new concepts never overwrite old ones.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np

from ..senses.vectors import unit


@dataclass
class Percept:
    """The result of perceiving one thing."""

    concept: str     # concept id, e.g. "word:3" or "sight:0"
    surprise: float  # 0 means completely familiar, 1 means never seen anything like it
    is_new: bool     # whether a new concept was just born


class Cortex:
    """A growing set of concept prototypes for one sense."""

    def __init__(self, kind: str, vigilance: float, learning_rate: float = 0.2):
        self.kind = kind
        self.vigilance = vigilance
        self.learning_rate = learning_rate
        self.ids: list[str] = []
        self.protos = np.zeros((0, 0), np.float32)
        self.usage: list[int] = []
        self.labels: list[Counter] = []   # how a word concept was spelled when heard
        self.pictures: list[str] = []     # a thumbnail of the last example seen
        self._next_id = 0

    def __len__(self) -> int:
        return len(self.ids)

    def __contains__(self, concept: str) -> bool:
        return concept.startswith(self.kind + ":")

    def perceive(self, x: np.ndarray, label: str = "", picture: str = "") -> Percept:
        """Recognize ``x`` as a known concept, or grow a new one."""
        x = unit(x)
        if self.ids:
            sims = self.protos @ x
            i = int(np.argmax(sims))
            surprise = float(np.clip(1.0 - sims[i], 0.0, 1.0))
            if sims[i] >= self.vigilance:
                self._adapt(i, x, label, picture)
                return Percept(self.ids[i], surprise, is_new=False)
        else:
            surprise = 1.0
        return Percept(self._grow(x, label, picture), surprise, is_new=True)

    def label(self, concept: str) -> str:
        """The most common spelling of a word concept."""
        labels = self.labels[self.ids.index(concept)]
        return labels.most_common(1)[0][0] if labels else concept

    def picture(self, concept: str) -> str:
        return self.pictures[self.ids.index(concept)]

    def usage_of(self, concept: str) -> int:
        return self.usage[self.ids.index(concept)]

    def forget(self, concepts: set[str]) -> None:
        """Remove concepts entirely (synaptic pruning during sleep)."""
        keep = [i for i, c in enumerate(self.ids) if c not in concepts]
        self.ids = [self.ids[i] for i in keep]
        self.protos = self.protos[keep]
        self.usage = [self.usage[i] for i in keep]
        self.labels = [self.labels[i] for i in keep]
        self.pictures = [self.pictures[i] for i in keep]

    def _adapt(self, i: int, x: np.ndarray, label: str, picture: str) -> None:
        # Well known concepts change slowly. Young ones stay plastic.
        rate = self.learning_rate / (1.0 + 0.1 * self.usage[i])
        self.protos[i] = unit(self.protos[i] + rate * (x - self.protos[i]))
        self.usage[i] += 1
        if label:
            self.labels[i][label] += 1
        if picture:
            self.pictures[i] = picture

    def _grow(self, x: np.ndarray, label: str, picture: str) -> str:
        concept = f"{self.kind}:{self._next_id}"
        self._next_id += 1
        self.ids.append(concept)
        self.protos = x[None, :] if not len(self.protos) else np.vstack([self.protos, x])
        self.usage.append(1)
        self.labels.append(Counter({label: 1}) if label else Counter())
        self.pictures.append(picture)
        return concept

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "vigilance": self.vigilance,
            "learning_rate": self.learning_rate,
            "next_id": self._next_id,
            "ids": self.ids,
            "protos": np.round(self.protos, 5).tolist(),
            "usage": self.usage,
            "labels": [dict(c) for c in self.labels],
            "pictures": self.pictures,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Cortex":
        c = cls(d["kind"], d["vigilance"], d["learning_rate"])
        c._next_id = d["next_id"]
        c.ids = list(d["ids"])
        if c.ids:
            c.protos = np.asarray(d["protos"], np.float32)
        c.usage = list(d["usage"])
        c.labels = [Counter(x) for x in d["labels"]]
        c.pictures = list(d["pictures"])
        return c
