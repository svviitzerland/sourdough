"""Lessons: a small built-in curriculum, like picture books for a baby.

A lesson is not pretraining. It is a prepared sequence of ordinary
experiences fed through the same :class:`Brain` methods you use by hand,
followed by a short quiz where the teacher reacts in plain language ("yes,
red" or "no, blue"). There are four kinds:

* **color** and **shape**: picture cards drawn on the fly, so nothing is
  downloaded and no two cards are the same. Color cards use varied shapes and
  shape cards use varied colors. Only the thing being taught stays constant,
  so cross situational learning can work out what each word refers to.
* **reply**: everyday routines ("hello", then "hi"). The teacher says the
  prompt, then models the answer, the way parents say "say hi!".
* **action**: words for actions ("wave"). The teacher says the word, then
  demonstrates the action.

The curriculum lives in ``lessons.json`` next to this file and is easy to
extend. :func:`grow` takes a baby through every lesson of a level (toddler,
preschooler, kid) in every language, so people can start from a baby that
already knows something.
"""

from __future__ import annotations

import base64
import io
import json
import math
from importlib import resources

import numpy as np
from PIL import Image, ImageDraw

CARD = 160
LANGUAGES = ("en", "id")
PALETTE = [(220, 40, 40), (40, 90, 220), (40, 170, 70), (240, 200, 40), (140, 60, 190)]
SHAPES = ["circle", "square", "triangle", "star", "heart", "hexagon", "oval", "arrow"]


def curriculum() -> dict:
    """All lessons, loaded from the bundled data file."""
    return json.loads(resources.files(__package__).joinpath("lessons.json").read_text())


def catalog() -> list[dict]:
    """Lesson names and titles, for showing a menu."""
    return [{"name": name, "title": lesson["title"], "size": len(lesson["items"])}
            for name, lesson in curriculum().items() if not name.startswith("_")]


# Kept for the first release, where a starter meant every lesson.
def raise_starter(brain, seed: int = 0) -> list[dict]:
    return grow(brain, "kid", seed)


def draw(shape: str, rgb: tuple[int, int, int], rng: np.random.Generator) -> Image.Image:
    """Draw one picture card: a shape in a color, slightly different every time."""
    paper = int(rng.integers(232, 256))
    card = Image.new("RGB", (CARD, CARD), (paper, paper, int(paper * 0.97)))
    size = CARD * rng.uniform(0.2, 0.27)
    cx = CARD / 2 + rng.uniform(-6, 6)
    cy = CARD / 2 + rng.uniform(-6, 6)
    tilt = rng.uniform(-0.15, 0.15)
    pen = ImageDraw.Draw(card)
    if shape == "circle":
        pen.ellipse((cx - size, cy - size, cx + size, cy + size), fill=rgb)
    else:
        pen.polygon(_outline(shape, cx, cy, size, tilt), fill=rgb)
    return card


def _outline(shape: str, cx: float, cy: float, r: float, tilt: float) -> list[tuple[float, float]]:
    if shape == "square":
        corners = [math.pi / 4 + k * math.pi / 2 for k in range(4)]
        points = [(r * 1.3 * math.cos(a), r * 1.3 * math.sin(a)) for a in corners]
    elif shape == "triangle":
        corners = [-math.pi / 2 + k * 2 * math.pi / 3 for k in range(3)]
        points = [(r * 1.2 * math.cos(a), r * 1.2 * math.sin(a) + r * 0.2) for a in corners]
    elif shape == "star":
        points = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            radius = r * 1.2 if k % 2 == 0 else r * 0.5
            points.append((radius * math.cos(a), radius * math.sin(a)))
    elif shape == "heart":
        points = []
        for k in range(40):
            t = k / 40 * 2 * math.pi
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            points.append((x * r / 15, y * r / 15))
    elif shape == "hexagon":
        points = [(r * 1.2 * math.cos(k * math.pi / 3), r * 1.2 * math.sin(k * math.pi / 3))
                  for k in range(6)]
    elif shape == "oval":
        points = [(r * 1.35 * math.cos(a), r * 0.7 * math.sin(a))
                  for a in np.linspace(0, 2 * math.pi, 40, endpoint=False)]
    elif shape == "arrow":
        points = [(-r * 1.2, -r * 0.3), (r * 0.2, -r * 0.3), (r * 0.2, -r * 0.8),
                  (r * 1.2, 0), (r * 0.2, r * 0.8), (r * 0.2, r * 0.3), (-r * 1.2, r * 0.3)]
    else:
        raise ValueError(f"unknown shape: {shape}")
    c, s = math.cos(tilt), math.sin(tilt)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in points]


def teach(brain, name: str, language: str = "en", rounds: int = 2,
          seed: int | None = None) -> dict:
    """Run a lesson: a few rounds of teaching, then a quiz with feedback.

    Returns the quiz results so an interface can show how it went.
    """
    book = curriculum()
    lesson = book[name]
    rng = np.random.default_rng(seed)
    feedback = book["_feedback"][language]

    for _ in range(rounds):
        for item in _shuffled(lesson["items"], rng):
            _show(brain, lesson, item, language, rng)

    results = []
    for item in _shuffled(lesson["items"], rng):
        results.append(_quiz(brain, lesson, item, language, feedback, rng))

    score = sum(r["correct"] for r in results)
    return {"lesson": lesson["title"][language], "score": score, "total": len(results),
            "results": results}


def levels() -> list[dict]:
    """The starting points a new baby can be born at, from newborn up."""
    return [{"name": name, **level} for name, level in curriculum()["_levels"].items()]


def grow(brain, level: str, seed: int = 0) -> list[dict]:
    """Take a baby through every lesson of a level, in every language.

    The result is still a baby that learned only from experience, the same
    loop you use by hand, just with more of it behind it. It sleeps once
    after each language, like a long day of school.
    """
    lessons = curriculum()["_levels"][level]["lessons"]
    reports = []
    for language in LANGUAGES:
        for name in lessons:
            report = teach(brain, name, language, rounds=2, seed=seed)
            reports.append({"language": language, "lesson": report["lesson"],
                            "score": report["score"], "total": report["total"]})
        if lessons:
            brain.sleep()
    return reports


def _show(brain, lesson: dict, item: dict, language: str, rng: np.random.Generator) -> None:
    """One teaching moment for one item."""
    kind = lesson["teaches"]
    if kind in ("color", "shape"):
        phrases = lesson["phrases"][language]
        phrase = phrases[rng.integers(len(phrases))]
        brain.observe(text=phrase.format(item[language]), image=_card(kind, item, rng))
    elif kind == "reply":
        brain.observe(text=item[language]["prompt"])
        brain.model(item[language]["reply"])
    elif kind == "action":
        brain.observe(text=item[language])
        brain.demonstrate(item["action"])


def _quiz(brain, lesson: dict, item: dict, language: str, feedback: dict,
          rng: np.random.Generator) -> dict:
    """Ask about one item, check the answer, and react like a parent would."""
    kind = lesson["teaches"]
    if kind in ("color", "shape"):
        word = item[language]
        image = _card(kind, item, rng)
        reply = brain.observe(image=image)
        correct = word in reply.words
        # The teacher answers the way a parent would. The brain's language
        # foundation turns "yes" and "no" into praise and correction.
        brain.observe(text=feedback["yes" if correct else "no"].format(word), image=image)
        return _result(word, "", reply, correct, _data_url(image))

    if kind == "reply":
        prompt, answer = item[language]["prompt"], item[language]["reply"]
        reply = brain.observe(text=prompt)
        correct = reply.words[:1] == answer.split()[:1]
        if correct:
            brain.observe(text=feedback["yes"].format(answer))
        else:
            brain.observe(text=feedback["no"].format(""))
            brain.observe(text=prompt)
            brain.model(answer)
        return _result(answer, prompt, reply, correct, "")

    word, action = item[language], item["action"]
    reply = brain.observe(text=word)
    correct = reply.action == action
    if correct:
        brain.observe(text=feedback["yes"].format(""))
    else:
        brain.observe(text=word)
        brain.demonstrate(action)
    return _result(action, word, reply, correct, "")


def _result(expected: str, prompt: str, reply, correct: bool, picture: str) -> dict:
    said = " ".join(reply.words) + (f" [{reply.action}]" if reply.action else "")
    return {"word": expected, "prompt": prompt, "said": said.strip(), "correct": correct,
            "picture": picture}


def _card(kind: str, item: dict, rng: np.random.Generator) -> Image.Image:
    if kind == "color":
        return draw(SHAPES[rng.integers(len(SHAPES))], tuple(item["rgb"]), rng)
    return draw(item["shape"], PALETTE[rng.integers(len(PALETTE))], rng)


def _shuffled(items: list, rng: np.random.Generator) -> list:
    items = list(items)
    rng.shuffle(items)
    return items


def _data_url(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.resize((64, 64)).save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
