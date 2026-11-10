"""Feeders: bring in things to learn from outside, as a teacher would.

A feeder never writes into the baby's memory directly. It turns some source
(a file, a folder of pictures, another AI) into ordinary teaching moments, and
:func:`feed` plays them through the same loop you use by hand:

* a **name** is a picture shown while its word is said
* a **reply** is something said, followed by the answer modeled for it

So the baby still learns from experience. The source only decides what it
experiences. Every feeder yields plain dictionaries::

    {"kind": "name", "image": <path, data URL or PIL image>, "answer": "apple"}
    {"kind": "reply", "prompt": "what do bees make", "answer": "honey"}

Sources that ship with Sourdough:

* :func:`from_pairs` a JSON or CSV file of prompts and answers
* :func:`from_folder` a folder of pictures, each named after what it shows
* :class:`Teacher` another AI behind an OpenAI compatible API (OpenAI,
  OpenRouter, Ollama, LM Studio and many more), asked to write lessons

Writing your own feeder is writing a generator of those dictionaries.
"""

from __future__ import annotations

from collections.abc import Iterable

from .ai import PROVIDERS, Teacher
from .files import from_folder, from_pairs, label_of


def feed(brain, moments: Iterable[dict], rounds: int = 2) -> dict:
    """Teach every moment, a few rounds over, then check what stuck.

    Returns how many moments were taught and how many it now gets right.
    """
    moments = [m for m in moments if _valid(m)]
    for _ in range(rounds):
        for m in moments:
            if m["kind"] == "name":
                brain.observe(text=m["answer"], image=m["image"])
            else:
                brain.observe(text=m["prompt"])
                brain.model(m["answer"])

    checked = []
    for m in moments:
        if m["kind"] == "name":
            reply = brain.observe(image=m["image"])
            target = m["answer"].lower().split()
            right = bool(set(target) & set(reply.words))
        else:
            reply = brain.observe(text=m["prompt"])
            right = reply.words[:1] == m["answer"].lower().split()[:1]
        if right:
            brain.observe(text="yes")
        checked.append({"kind": m["kind"], "prompt": m.get("prompt", ""), "answer": m["answer"],
                        "said": " ".join(reply.words), "correct": right})
    return {"taught": len(moments), "correct": sum(c["correct"] for c in checked), "checked": checked}


def _valid(m: dict) -> bool:
    if not isinstance(m, dict) or not str(m.get("answer", "")).strip():
        return False
    if m.get("kind") == "name":
        return m.get("image") is not None
    return m.get("kind") == "reply" and bool(str(m.get("prompt", "")).strip())


__all__ = ["PROVIDERS", "Teacher", "feed", "from_folder", "from_pairs", "label_of"]
