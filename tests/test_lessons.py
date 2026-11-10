"""The built-in curriculum teaches quickly, in every language it ships with."""

import pytest

from sourdough import Brain
from sourdough.foundation import Foundation
from sourdough.foundation.lessons import LANGUAGES, catalog, curriculum, grow, levels, teach


def lessons():
    return {name: lesson for name, lesson in curriculum().items() if not name.startswith("_")}


def answers_of(lesson: dict, language: str) -> list[str]:
    """Every word a lesson expects the baby to say, in one language."""
    out = []
    for item in lesson["items"]:
        value = item[language]
        out += value["reply"].split() if isinstance(value, dict) else [value]
    return out


@pytest.mark.parametrize("language", LANGUAGES)
def test_each_lesson_is_learned_in_two_rounds(language):
    baby = Brain(seed=0)
    for lesson in catalog():
        result = teach(baby, lesson["name"], language, rounds=2, seed=1)
        assert result["score"] >= result["total"] - 1, result


@pytest.mark.parametrize("level", [lvl["name"] for lvl in levels()])
def test_every_level_passes_its_quizzes(level):
    for report in grow(Brain(seed=0), level):
        assert report["score"] >= report["total"] - 1, report


def test_levels_know_more_and_more():
    sizes = []
    for level in levels():
        baby = Brain(seed=0)
        grow(baby, level["name"])
        sizes.append(len(baby.vocabulary()))
    assert sizes[0] == 0
    assert sizes == sorted(sizes) and len(set(sizes)) == len(sizes)


def test_a_kid_answers_basic_questions_in_both_languages():
    baby = Brain(seed=0)
    grow(baby, "kid")
    asked = {
        "what is your name": ["sourdough"],
        "what does a cat say": ["meow"],
        "what color is the sky": ["blue"],
        "opposite of hot": ["cold"],
        "what comes after three": ["four"],
        "an apple is a": ["fruit"],
        "anjing bilang apa": ["guk"],
        "lawan kata besar": ["kecil"],
        "setelah tujuh": ["delapan"],
        "halo": ["hai"],
    }
    for question, answer in asked.items():
        assert baby.observe(text=question).words == answer, question


def test_every_lesson_has_every_language():
    for lesson in lessons().values():
        assert set(lesson["title"]) >= set(LANGUAGES)
        for language in LANGUAGES:
            assert answers_of(lesson, language)
            if "phrases" in lesson:
                assert lesson["phrases"][language]


def test_answers_are_content_words():
    """An answer must never be mistaken for praise, correction or filler."""
    foundation = Foundation()
    for lesson in lessons().values():
        for language in LANGUAGES:
            for word in answers_of(lesson, language):
                assert foundation.role(word) == "content", (lesson["title"], word)
