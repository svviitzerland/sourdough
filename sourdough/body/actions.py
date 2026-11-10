"""Actions: what the baby can do to the world besides talking.

The brain is not born knowing what any action does. An action is only a name,
like a muscle it can move. Whatever hosts the brain carries the action out
and reports back what happened, and the brain learns from that:

* **consequences**: the result comes back as an ordinary moment, through
  ``Brain.observe(..., outcome_of=name)``. If the result is new and
  surprising, the action becomes more likely in that situation. If it is
  the same old thing, less likely. Curiosity is the reward.
* **demonstration**: you perform the action for it, and it links what it was
  perceiving to that action.
* **praise**: "yes" or "no" after it acts strengthens or weakens the habit.

So the host decides what the body *can* do, and the baby discovers what each
action is *for*. The web server gives it two actions (see ``interface/body.py``):
exploring a folder of its own, and glancing through the camera. A robot could
give it motors, a smart home its lights.
"""

from __future__ import annotations


def concept(name: str) -> str:
    """The concept id the memory uses for an action."""
    return f"action:{name}"
