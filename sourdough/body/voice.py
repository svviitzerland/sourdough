"""Voice: how Sourdough makes sounds before it knows any words.

Speech develops in stages, and each stage needs less help than the last:

1. **Babbling.** Syllables at first, then strings shaped by the letter
   statistics it has heard. Babbling drifts toward the language it is
   spoken to in.
2. **Imitation.** Copying a word it just heard, imperfectly at first, more
   accurately with age.
3. **Speaking.** Saying a word because it means something here. That part
   is decided by the brain, not the voice.
"""

from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np

FIRST_SOUNDS = ["a", "u", "e", "ma", "ba", "da", "pa", "ta", "na", "mm", "goo", "aah"]


class Voice:
    """Character statistics of everything heard, used to babble and imitate."""

    def __init__(self):
        self.starts: Counter = Counter()
        self.bigrams: defaultdict[str, Counter] = defaultdict(Counter)
        self.letters_heard = 0

    def listen(self, word: str) -> None:
        """Learn which letters start words and which letters follow which."""
        self.starts[word[0]] += 1
        for a, b in zip(word, word[1:] + "$"):
            self.bigrams[a][b] += 1
        self.letters_heard += len(word)

    def babble(self, rng: np.random.Generator) -> str:
        """Make a word-like sound. It sounds more like real words the more it has heard."""
        if not self.starts or rng.random() > min(1.0, self.letters_heard / 300):
            return "".join(rng.choice(FIRST_SOUNDS) for _ in range(rng.integers(1, 3)))
        out = _sample(self.starts, rng)
        while len(out) < 8:
            follow = self.bigrams.get(out[-1])
            nxt = _sample(follow, rng) if follow else "$"
            if nxt == "$":
                break
            out += nxt
        return out

    def imitate(self, word: str, skill: float, rng: np.random.Generator) -> str:
        """Repeat a word. With low skill, letters get dropped or swapped."""
        out = []
        for ch in word:
            roll = rng.random()
            if roll < (1 - skill) * 0.2:
                continue
            if roll < (1 - skill) * 0.4 and self.starts:
                ch = _sample(self.starts, rng)
            out.append(ch)
        return "".join(out) or word[:1]

    def to_dict(self) -> dict:
        return {"starts": self.starts, "bigrams": self.bigrams, "letters_heard": self.letters_heard}

    @classmethod
    def from_dict(cls, d: dict) -> "Voice":
        v = cls()
        v.starts = Counter(d["starts"])
        for a, follow in d["bigrams"].items():
            v.bigrams[a] = Counter(follow)
        v.letters_heard = d["letters_heard"]
        return v


def _sample(counter: Counter, rng: np.random.Generator) -> str:
    keys = list(counter)
    p = np.array([counter[k] for k in keys], np.float64)
    return keys[int(rng.choice(len(keys), p=p / p.sum()))]
