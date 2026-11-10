"""Feelings, initiative, actions and storage: the parts that make it alive."""

import numpy as np

from sourdough import Brain, Nest
from sourdough.foundation.lessons import draw
from sourdough.mind.feelings import BORED_AFTER

RED = (220, 40, 40)


def test_praise_makes_it_happy_and_correction_upset():
    baby = Brain(seed=0)
    baby.observe(text="good")
    assert baby.feelings.joy > 0
    for _ in range(3):
        baby.observe(text="no")
    assert baby.feelings.strongest() == "upset"


def test_boredom_makes_it_act_on_its_own():
    baby = Brain(seed=0)
    baby.observe(text="hello")
    quiet = baby.tick(seconds=1)
    assert quiet.mode == "silent"
    acted = baby.tick(seconds=BORED_AFTER)
    assert acted.initiative and acted.mode in ("babble", "practice", "do")


def test_it_practices_words_it_knows_when_bored():
    rng = np.random.default_rng(0)
    baby = Brain(seed=0)
    baby.observe(text="red", image=draw("circle", RED, rng))
    r = baby.tick(seconds=BORED_AFTER)
    assert r.mode == "practice" and r.words == ["red", "?"]


def test_learns_an_action_from_one_demonstration():
    baby = Brain(seed=0, actions=("wave",))
    baby.observe(text="wave")
    assert baby.demonstrate("wave").action == "wave"
    assert baby.observe(text="wave").action == "wave"
    assert baby.habits()[0] == {"action": "wave", "triggers": ["wave"]}


def test_a_bored_baby_tries_its_actions():
    baby = Brain(seed=0, actions=("explore",))
    baby.observe(text="hello")
    assert baby.tick(seconds=BORED_AFTER).action == "explore"


def test_surprising_consequences_make_an_action_a_habit():
    """Curiosity is the reward: what brought something new is worth doing again."""
    rng = np.random.default_rng(0)
    baby = Brain(seed=0, actions=("explore",))
    baby.observe(text="toys")
    for shape in ("star", "heart", "arrow"):
        baby.observe(text="toys")
        assert baby.tick(seconds=BORED_AFTER).action == "explore"
        baby.observe(image=draw(shape, RED, rng), outcome_of="explore")
    assert baby.policy.w["word:0"]["action:explore"] > 0
    assert baby.observe(text="toys").action == "explore"


def test_boring_consequences_fade_an_action():
    rng = np.random.default_rng(0)
    baby = Brain(seed=0, actions=("explore",))
    card = draw("star", RED, rng)
    baby.observe(text="toys", image=card)
    baby.demonstrate("explore")
    before = baby.policy.w["word:0"]["action:explore"]
    for _ in range(4):
        baby.observe(image=card, outcome_of="explore")
        baby._credit = [("word:0", "action:explore")]
    assert baby.policy.w["word:0"]["action:explore"] < before


def test_praise_after_exploring_teaches_when_to_act():
    """It tries an action on its own while hearing "dance", and praise makes it a habit."""
    baby = Brain(seed=0, actions=("spin",))
    for _ in range(2):
        baby.observe(text="dance")
        assert baby.tick(seconds=BORED_AFTER).action == "spin"
        baby.observe(text="yes, good")
    assert baby.observe(text="dance").action == "spin"


def test_tired_baby_falls_asleep():
    baby = Brain(seed=0)
    baby.feelings.tiredness = 1.0
    assert baby.tick(seconds=1).mode == "sleep"
    assert baby.feelings.tiredness == 0


def test_a_new_nest_is_born_at_a_level_with_a_world(tmp_path):
    nest = Nest("pip", tmp_path)
    baby = nest.create("toddler")
    assert len(baby.vocabulary()) > 20
    assert len(list(nest.world.glob("*.png"))) == 6
    assert Nest("pip", tmp_path).load().age == baby.age


def test_nest_keeps_brain_journal_and_snapshots(tmp_path):
    nest = Nest("kiki", tmp_path)
    assert not nest.exists
    baby = nest.load()
    baby.observe(text="hello")
    nest.save(baby)
    nest.journal.write("moment", heard="hello")
    nest.snapshot(baby)
    again = Nest("kiki", tmp_path)
    assert again.exists and again.load().age == 1
    assert again.journal.recent()[0]["heard"] == "hello"
    assert len(list((tmp_path / "kiki" / "snapshots").glob("*.json"))) == 1


def test_graph_shows_what_it_knows():
    rng = np.random.default_rng(0)
    baby = Brain(seed=0)
    baby.observe(text="red", image=draw("circle", RED, rng))
    graph = baby.graph()
    kinds = {n["kind"] for n in graph["nodes"]}
    assert kinds == {"word", "color", "shape"}
    assert graph["active"]


def test_a_spoken_request_outranks_naming_what_it_sees():
    rng = np.random.default_rng(0)
    baby = Brain(seed=0, actions=("jump",))
    card = draw("circle", RED, rng)
    baby.observe(text="red", image=card)
    baby.observe(text="jump", image=card)
    baby.demonstrate("jump")
    assert baby.observe(text="jump", image=card).action == "jump"
