"""Foundation: what Sourdough knows at birth.

A newborn knows no words, but it is not a blank slate either. Long before
understanding any word, infants

* tell short **function words** ("the", "is", "this") apart from content
  words, and use them to find the words that matter (Shi and Werker, 2001)
* read **approval and prohibition** in a caregiver's voice (Fernald, 1989)
* recognize when they are being **asked** something
* tell languages apart by their sound, even before knowing any word in them

Sourdough gets these as a small word list per language, in
``language.json`` next to this file. It ships with English and Indonesian.
The list says nothing about what any word *means*. It only says what role a
word plays in how people talk to babies. Meaning is always learned.

The built-in lessons in ``lessons.py`` are the other half of the foundation:
a small curriculum of prepared experiences, like picture books.
"""

from __future__ import annotations

import json
from importlib import resources

FUNCTION, PRAISE, CORRECTION, QUESTION, CONTENT = (
    "function", "praise", "correction", "question", "content",
)


class Foundation:
    """Word roles across every language in the data file."""

    def __init__(self, languages: dict | None = None):
        if languages is None:
            path = resources.files(__package__).joinpath("language.json")
            languages = json.loads(path.read_text())
        self.roles: dict[str, str] = {}
        self.home: dict[str, set[str]] = {}   # which languages a known word belongs to
        for name, lists in languages.items():
            if name.startswith("_"):
                continue
            for role in (FUNCTION, QUESTION, CORRECTION, PRAISE):
                for word in lists.get(role, []):
                    self.roles.setdefault(word, role)
                    self.home.setdefault(word, set()).add(name)

    def role(self, word: str) -> str:
        return self.roles.get(word, CONTENT)

    def language(self, words: list[str]) -> str | None:
        """Which language is being spoken, judged from its little words.

        Returns None when the words give no clue, or clues that disagree.
        """
        votes: dict[str, int] = {}
        for w in words:
            homes = self.home.get(w, set())
            if len(homes) == 1:
                lang = next(iter(homes))
                votes[lang] = votes.get(lang, 0) + 1
        if not votes:
            return None
        ranked = sorted(votes.items(), key=lambda kv: -kv[1])
        if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
            return None
        return ranked[0][0]

    def feedback(self, words: list[str]) -> float:
        """+1 for praise, -1 for correction, 0 for neither.

        Correction wins when both appear ("no, not good").
        """
        roles = {self.role(w) for w in words}
        if CORRECTION in roles:
            return -1.0
        if PRAISE in roles:
            return 1.0
        return 0.0

    def is_question(self, words: list[str]) -> bool:
        return any(self.role(w) == QUESTION for w in words)
