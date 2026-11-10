"""Deciding: weigh every option, then do one thing.

Each moment the brain lists what it could do (name something, ask, use an
ability, imitate, babble, stay quiet) and gives each option a value. Options
come in tiers, so a confident answer always beats a guess, and within a tier
the stronger option wins. Curiosity adds a little randomness, which is how
the baby sometimes tries something new instead of repeating what worked.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# Tiers, from the most to the least deliberate.
KNOWS = 3.0     # it knows what to say or do here
NEEDS = 2.0     # it needs something: to ask, to sleep, to react to feedback
TRIES = 1.0     # it tries: imitating a word, or exploring an ability
IDLE = 0.0      # babbling or keeping quiet


@dataclass
class Option:
    """One thing the baby could do right now."""

    mode: str                  # speak, do, practice, ask, sleep, react, imitate, babble, silent
    value: float
    words: list[str] = field(default_factory=list)   # what it would say
    action: str | None = None                         # the ability it would use
    credit: list[tuple[str, str]] = field(default_factory=list)  # links praise would reach
    expression: str = ""


def choose(options: list[Option], curiosity: float, rng: np.random.Generator) -> Option:
    """Pick the most valuable option, with a little curiosity driven noise."""
    noise = 0.1 * curiosity
    return max(options, key=lambda o: o.value + rng.uniform(0.0, noise))
