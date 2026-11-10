"""Behavioral tests: does the baby learn the way a baby should?"""

import numpy as np
import pytest

from sourdough import Brain
from sourdough.foundation.lessons import draw

RED, BLUE, GREEN = (220, 40, 40), (40, 90, 220), (40, 170, 70)


@pytest.fixture
def rng():
    return np.random.default_rng(1)


def card(rgb, rng, shape="circle"):
    """A picture card, never exactly the same twice."""
    return draw(shape, rgb, rng)


def test_newborn_knows_no_words():
    baby = Brain(seed=0)
    r = baby.observe(text="hello")
    assert r.mode in ("babble", "imitate")
    assert baby.vocabulary() == []


def test_asks_about_something_new(rng):
    baby = Brain(seed=0)
    assert baby.observe(image=card(RED, rng)).mode == "ask"


def test_learns_a_name_from_one_example(rng):
    baby = Brain(seed=0)
    baby.observe(text="red", image=card(RED, rng))
    r = baby.observe(image=card(RED, rng))
    assert r.mode == "speak" and r.words == ["red"]


def test_one_sentence_is_enough(rng):
    """Function words get little attention, so "look this is" is not a name."""
    baby = Brain(seed=0)
    baby.observe(text="look, this is red", image=card(RED, rng))
    assert baby.observe(image=card(RED, rng)).words == ["red"]


def test_works_in_indonesian(rng):
    baby = Brain(seed=0)
    baby.observe(text="lihat, ini merah", image=card(RED, rng))
    assert baby.observe(image=card(RED, rng)).words == ["merah"]


def test_words_attach_to_color_or_shape(rng):
    """Color words vary with color, shape words with shape: each finds its own stream."""
    baby = Brain(seed=0)
    for _ in range(2):
        for shape in ("square", "star"):
            baby.observe(text="red", image=card(RED, rng, shape))
            baby.observe(text="blue", image=card(BLUE, rng, shape))
        for color in (RED, BLUE):
            baby.observe(text="circle", image=card(color, rng, "circle"))
            baby.observe(text="triangle", image=card(color, rng, "triangle"))
    kinds = {v["word"]: v["kind"] for v in baby.vocabulary()}
    assert kinds == {"red": "color", "blue": "color", "circle": "shape", "triangle": "shape"}


def test_names_a_combination_it_never_saw(rng):
    baby = Brain(seed=0)
    for _ in range(2):
        baby.observe(text="this is red", image=card(RED, rng, "square"))
        baby.observe(text="this is green", image=card(GREEN, rng, "square"))
        baby.observe(text="a triangle", image=card(BLUE, rng, "triangle"))
        baby.observe(text="a circle", image=card(BLUE, rng, "circle"))
    r = baby.observe(image=card(RED, rng, "triangle"))
    assert r.words == ["red", "triangle"]


def test_hears_praise_and_correction_in_words(rng):
    baby = Brain(seed=0)
    baby.observe(text="red", image=card(RED, rng))
    baby.observe(text="blue", image=card(RED, rng))  # a confusing teacher
    first = baby.observe(image=card(RED, rng)).words[0]
    other = "blue" if first == "red" else "red"
    baby.observe(text=f"no, {other}", image=card(RED, rng))
    baby.observe(text=f"no, {other}", image=card(RED, rng))
    assert baby.observe(image=card(RED, rng)).words == [other]


def test_new_words_are_assumed_to_name_shapes(rng):
    """Shape bias: one ambiguous example ("dax" with a blue star) means the star."""
    baby = Brain(seed=0)
    baby.observe(text="dax", image=card(BLUE, rng, "star"))
    assert baby.vocabulary()[0]["kind"] == "shape"


def test_correction_spares_the_right_word(rng):
    baby = Brain(seed=0)
    for shape in ("square", "circle"):
        baby.observe(text="red", image=card(RED, rng, shape))
    for color in (BLUE, GREEN):
        baby.observe(text="star", image=card(color, rng, "star"))
    assert baby.observe(image=card(RED, rng, "star")).words == ["red", "star"]
    baby.observe(text="no, blue star")
    assert all(w >= 0 for links in baby.policy.w.values()
               for c, w in links.items() if baby.words.label(c) == "star")


def test_praise_teaches_a_reply():
    baby = Brain(seed=0)
    baby.observe(text="bye")
    baby.observe(text="hello")
    baby._credit = [("word:1", "word:0")]  # pretend: heard "hello", said "bye"
    baby.observe(text="good")
    baby._credit = [("word:1", "word:0")]
    baby.observe(text="yes")
    assert baby.observe(text="hello").words == ["bye"]


def test_a_question_gets_an_answer_not_an_echo(rng):
    baby = Brain(seed=0)
    baby.observe(text="red", image=card(RED, rng))
    assert baby.observe(text="what is this?", image=card(RED, rng)).words == ["red"]


def test_live_camera_reacts_once_per_view(rng):
    baby = Brain(seed=0)
    view = card(RED, rng)
    frames = [baby.observe(image=view, passive=True) for _ in range(4)]
    assert [f.mode for f in frames] == ["silent", "ask", "silent", "silent"]


def test_sleep_prunes_and_brain_round_trips(tmp_path, rng):
    baby = Brain(seed=0)
    baby.observe(text="red", image=card(RED, rng))
    baby.observe(text="lonely")
    assert baby.sleep()["forgotten"] >= 1
    baby.save(tmp_path / "brain.json")
    again = Brain.load(tmp_path / "brain.json")
    assert again.age == baby.age
    assert again.observe(image=card(RED, rng)).words == ["red"]
