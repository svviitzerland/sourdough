"""Feelings: a few internal states that change what the baby does.

Feelings are not decoration. Each one is a number that rises and falls with
experience and pushes decisions in a direction:

* **joy** rises with praise and falls with correction. A happy baby speaks
  up more readily, an upset one hesitates.
* **curiosity** follows surprise. It makes the baby explore, trying things
  it is not sure about.
* **boredom** grows while nothing new happens. Past a point the baby starts
  something by itself.
* **confusion** rises when it is asked about something it cannot name, and
  makes it ask for help.
* **tiredness** grows with every experience. When full, it decides to sleep.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

TIRED_AFTER = 200   # experiences between sleeps
BORED_AFTER = 45.0  # seconds of nothing new before it acts by itself


@dataclass
class Feelings:
    joy: float = 0.0          # -1 upset to +1 happy
    curiosity: float = 0.5    # 0 to 1
    boredom: float = 0.0      # 0 to 1
    confusion: float = 0.0    # 0 to 1
    tiredness: float = 0.0    # 0 to 1

    def experienced(self, surprise: float) -> None:
        """Something happened. New things wake it up, old things bore it a bit."""
        self.curiosity = 0.8 * self.curiosity + 0.2 * surprise
        self.boredom = 0.0 if surprise > 0.3 else max(0.0, self.boredom - 0.2)
        self.tiredness = min(1.0, self.tiredness + 1.0 / TIRED_AFTER)
        self.joy *= 0.95
        self.confusion *= 0.8

    def praised(self, amount: float) -> None:
        self.joy = max(-1.0, min(1.0, 0.7 * self.joy + 0.3 * amount))

    def puzzled(self) -> None:
        self.confusion = min(1.0, self.confusion + 0.3)

    def waited(self, seconds: float) -> None:
        self.boredom = min(1.0, self.boredom + seconds / BORED_AFTER)

    def rested(self) -> None:
        self.tiredness = 0.0
        self.boredom = 0.0
        self.confusion = 0.0

    def strongest(self) -> str:
        """The feeling that shows the most right now."""
        if self.tiredness > 0.8:
            return "sleepy"
        levels = {
            "happy": self.joy,
            "upset": -self.joy,
            "curious": self.curiosity - 0.3,
            "bored": self.boredom - 0.2,
            "confused": self.confusion,
        }
        name, level = max(levels.items(), key=lambda kv: kv[1])
        return name if level > 0.3 else "calm"

    def expression(self, surprise: float = 0.0) -> str:
        """How the feeling shows on its face."""
        if surprise > 0.5 and self.tiredness <= 0.8:
            return "*eyes widen*"
        return {
            "sleepy": "*yawns*",
            "happy": "*smiles*",
            "upset": "*pouts*",
            "curious": "*leans in*",
            "bored": "*fidgets*",
            "confused": "*frowns*",
            "calm": "",
        }[self.strongest()]

    def to_dict(self) -> dict:
        return {k: round(v, 3) for k, v in asdict(self).items()}

    @classmethod
    def from_dict(cls, d: dict) -> "Feelings":
        return cls(**d)
