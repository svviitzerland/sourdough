"""Sourdough: a starter for a baby AI that is born knowing nothing and grows by living.

Quick start::

    from sourdough import Brain

    baby = Brain()
    baby.observe(text="look, a cat", image="cat.jpg")   # name a thing once
    print(baby.observe(image="another_cat.jpg"))        # cat
    baby.observe(text="yes, good")                       # praise
    baby.tick(seconds=60)                                # time passes, it may act

To keep a baby between runs, use a :class:`Nest`::

    from sourdough import Nest

    nest = Nest("kiki")
    baby = nest.load()
    ...
    nest.save(baby)
"""

from .brain import Brain, Response
from .storage import Nest

__all__ = ["Brain", "Nest", "Response"]
__version__ = "0.1.0"
