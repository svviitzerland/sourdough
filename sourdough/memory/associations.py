"""Associations: what goes together, and what words mean.

Counts are gathered in moments when something was said. Words get their
meaning in two steps.

1. **Each word picks one meaning**: the thing it most reliably comes with,
   P(thing | word), with ties going to the thing that comes with the fewest
   other words. Once "red" means the color red, it stops competing for the
   circle it happened to be painted on. This is the mutual exclusivity bias
   of young children (Markman and Wachtel, 1988).
2. **A thing is named by the words that picked it**, each weighted against
   the strongest of them. Two languages can each have a word for it.

Filler words heard with everything ("look", "this") end up meaning nothing in
particular. This is cross situational learning (Yu and Smith, 2007). Every
score is a ratio, so one clear example already gives a usable link. That is
how children "fast map" a word after hearing it once.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations

# When a word could equally mean two things, children assume it names the
# object's shape (Landau, Smith and Jones, 1988). A small tie breaker.
BIAS = {"shape": 1.05}


def kind(concept: str) -> str:
    """The part of a concept id before the colon: "word", "color", "shape"..."""
    return concept.split(":", 1)[0]


class Associations:
    """Symmetric co-occurrence memory that turns counts into word meanings."""

    def __init__(self):
        self.count: dict[str, float] = {}
        self.co: defaultdict[str, dict[str, float]] = defaultdict(dict)

    def observe(self, salience: dict[str, float], weight: float = 1.0) -> None:
        """Record that these concepts were experienced together.

        ``salience`` maps each concept to how much attention it got, from 0
        to 1. Links between salient things gain more evidence.
        """
        for c, s in salience.items():
            self.count[c] = self.count.get(c, 0.0) + weight * s
        for (a, sa), (b, sb) in combinations(salience.items(), 2):
            self.bind(a, b, weight * sa * sb)

    def bind(self, a: str, b: str, weight: float) -> None:
        """Add evidence that ``a`` and ``b`` belong together."""
        value = self.co[a].get(b, 0.0) + weight
        self.co[a][b] = value
        self.co[b][a] = value

    def referent(self, word: str) -> str | None:
        """The one thing this word means: what it most reliably comes with."""
        best, best_score = None, 0.0
        for thing, co in self.co.get(word, {}).items():
            if kind(thing) == "word":
                continue
            thing_given_word = min(1.0, co / self.count[word])
            word_given_thing = min(1.0, co / self.count[thing])
            score = thing_given_word * (0.5 + 0.5 * word_given_thing)
            score *= BIAS.get(kind(thing), 1.0)
            if score > best_score:
                best, best_score = thing, score
        return best

    def names(self, thing: str) -> dict[str, float]:
        """Words that mean ``thing``, with how sure the baby is of each, 0 to 1."""
        claims = {w: co for w, co in self.co.get(thing, {}).items()
                  if kind(w) == "word" and self.referent(w) == thing}
        strongest = max(claims.values(), default=0.0)
        return {
            w: min(1.0, co / self.count[w])   # how reliably the word comes with it
            * (co / strongest)                # weak claims next to a strong one count little
            * (co / (co + 1.0))               # one example is a hint, five are a fact
            for w, co in claims.items()
        }

    def decay(self, factor: float, floor: float) -> None:
        """Weaken everything and drop what falls below ``floor``."""
        for a in list(self.co):
            links = self.co[a]
            for b in list(links):
                links[b] *= factor
                if links[b] < floor:
                    del links[b]
            if not links:
                del self.co[a]
        for c in list(self.count):
            self.count[c] *= factor
            if self.count[c] < floor and c not in self.co:
                del self.count[c]

    def forget(self, concepts: set[str]) -> None:
        for c in concepts:
            self.count.pop(c, None)
            for other in self.co.pop(c, {}):
                self.co.get(other, {}).pop(c, None)

    def __len__(self) -> int:
        return sum(len(v) for v in self.co.values()) // 2

    def to_dict(self) -> dict:
        return {"count": self.count, "co": self.co}

    @classmethod
    def from_dict(cls, d: dict) -> "Associations":
        m = cls()
        m.count = dict(d["count"])
        for a, links in d["co"].items():
            m.co[a] = dict(links)
        return m
