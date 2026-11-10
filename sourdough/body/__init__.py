"""Body: how the baby acts on the world.

* ``Voice`` babbling and imitating sounds
* ``actions`` names of things the host can do for it, learned from consequences
"""

from .actions import concept
from .voice import Voice

__all__ = ["Voice", "concept"]
