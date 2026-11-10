"""Mind: what the baby knows, how it feels, and how it decides.

* ``Cortex`` concepts that grow from nothing, one cortex per sense
* ``Feelings`` joy, curiosity, boredom, confusion and tiredness
* ``choose`` picks one option among everything it could do
"""

from .cortex import Cortex, Percept
from .decide import IDLE, KNOWS, NEEDS, TRIES, Option, choose
from .feelings import TIRED_AFTER, Feelings

__all__ = ["Cortex", "Feelings", "IDLE", "KNOWS", "NEEDS", "Option", "Percept",
           "TIRED_AFTER", "TRIES", "choose"]
