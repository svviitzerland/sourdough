"""The brain: a life loop of perceive, feel, decide, act and learn.

There is no training phase and no dataset. Every moment is both living and
learning.

1. **Listen.** The foundation hears praise ("yes", "bagus") or correction
   ("no", "bukan") and applies it to what the baby just did.
2. **Perceive.** Each sense lands on a concept in its cortex, or grows one.
   Vision reports two things at once, a color and a shape.
3. **Feel.** Surprise feeds curiosity, routine feeds boredom, every moment
   adds a little tiredness.
4. **Decide.** It weighs every option (answer, name, ask, act, imitate,
   babble, stay quiet) using only what it knew before this moment.
5. **Learn.** What was perceived while something was said gets linked.

Time passing matters too. :meth:`Brain.tick` lets the baby act on its own
when it is bored and fall asleep when it is tired.

Actions are a body the host gives it. The brain does not know what an action
does. It finds out from the consequences: whatever the action brings back is
perceived with ``observe(..., outcome_of=action)``, and a surprising result
makes that action more likely next time. Curiosity is the reward.

See ``docs/how-it-learns.md`` for the research behind each step.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from .body import Voice, concept
from .foundation import CONTENT, Foundation
from .memory import Associations, Policy, Sequence, kind
from .mind import IDLE, KNOWS, NEEDS, TRIES, Cortex, Feelings, Option, Percept, choose
from .senses import encode_audio, encode_word, see, tokenize

CONFIDENCE = 0.4   # how sure it must be before it says or does something on purpose
CHAIN = 0.6        # how sure it must be of the next word to continue a phrase
QUIET = 0.1        # attention given to function words, praise and questions
NOVEL_USAGE = 3    # something seen this few times still feels new
SAVE_FORMAT = 4


@dataclass
class Response:
    """What the baby did in one moment."""

    words: list[str] = field(default_factory=list)
    mode: str = "silent"       # silent, speak, do, practice, ask, sleep, react, imitate, babble
    expression: str = ""
    confidence: float = 0.0
    action: str | None = None  # an action for the host to carry out
    feeling: str = "calm"
    initiative: bool = False   # True when it acted without being prompted

    def __str__(self) -> str:
        parts = [self.expression, " ".join(self.words)]
        if self.action:
            parts.append(f"[{self.action}]")
        return " ".join(p for p in parts if p)

    def to_dict(self) -> dict:
        return asdict(self) | {"text": str(self)}


class Brain:
    """A Sourdough brain. Create one, then let it live through ``observe`` and ``tick``."""

    def __init__(self, seed: int | None = None, actions=()):
        self.rng = np.random.default_rng(seed)
        self.foundation = Foundation()
        self.words = Cortex("word", vigilance=0.92)
        self.colors = Cortex("color", vigilance=0.85)
        self.shapes = Cortex("shape", vigilance=0.85)
        self.sounds = Cortex("sound", vigilance=0.80)
        self.assoc = Associations()
        self.sequence = Sequence()
        self.policy = Policy()
        self.voice = Voice()
        self.feelings = Feelings()
        self.actions: list[str] = list(actions)
        self.age = 0
        self.language: str | None = None             # the language it is being spoken to in
        self.languages: dict[str, dict[str, int]] = {}  # word concept: language it was heard in

        self.active: list[str] = []      # what it perceived in the latest moment
        self.episodes: deque[tuple[dict[str, float], float]] = deque(maxlen=500)
        self._credit: list[tuple[str, str]] = []
        self._glance: str | None = None
        self._attended: str | None = None

    @property
    def senses(self) -> tuple[Cortex, ...]:
        """Sense cortices, in the order their words are spoken: "red circle"."""
        return (self.colors, self.shapes, self.sounds)

    # Living

    def observe(self, text: str | None = None, image=None, audio=None,
                sample_rate: int = 16000, passive: bool = False,
                outcome_of: str | None = None) -> Response:
        """Experience one moment through any mix of senses.

        Args:
            text: what someone says, typed or transcribed.
            image: what the baby is looking at (path, PIL image, array or data URL).
            audio: raw mono samples of a sound.
            passive: ``True`` for a glance nobody asked for, such as a live
                camera frame. The baby then only reacts once the view has
                settled on something it has not reacted to yet.
            outcome_of: the action that produced this moment, if any. How
                surprising the moment is becomes a reward for that action.
        """
        words = tokenize(text) if text else []
        roles = [self.foundation.role(w) for w in words]
        heard = [self.words.perceive(encode_word(w), label=w) for w in words]
        seen: list[Percept] = []
        if image is not None:
            sight = see(image)
            seen = [self.colors.perceive(sight.color, picture=sight.swatch),
                    self.shapes.perceive(sight.shape, picture=sight.silhouette)]
        percepts = heard + seen
        if audio is not None:
            percepts.append(self.sounds.perceive(encode_audio(audio, sample_rate)))
        if not percepts:
            return Response(feeling=self.feelings.strongest())

        if seen:
            view = "|".join(p.concept for p in seen)
            if passive and not words and not self._worth_attention(view):
                return Response(feeling=self.feelings.strongest())
            self._glance = self._attended = view

        language = self.foundation.language(words)
        if language:
            self.language = language
        feedback = self.foundation.feedback(words)
        if feedback:
            said = {c for c in self._said() if self.words.label(c) in words}
            self.reward(feedback, spare=said if feedback < 0 else set())

        self.age += 1
        concepts = list(dict.fromkeys(p.concept for p in percepts))
        surprise = max(p.surprise for p in percepts)
        self.feelings.experienced(surprise)
        if outcome_of:
            # Something new is worth doing again, the same old thing is not.
            for source, target in self._credit:
                if target == concept(outcome_of):
                    self.policy.nudge(source, target, 0.5 * (surprise - 0.25))

        content = [p for p, r in zip(heard, roles) if r == CONTENT]
        if language:
            for p in content:
                seen_in = self.languages.setdefault(p.concept, {})
                seen_in[language] = seen_in.get(language, 0) + 1
        asked = self.foundation.is_question(words)
        options = self._options(concepts, content, seen, surprise, passive, asked, feedback)
        response = self._carry_out(choose(options, self.feelings.curiosity, self.rng))

        for w in words:
            self.voice.listen(w)
        salience = self._salience(percepts, heard, roles)
        if len(salience) > 1 and (heard or audio is not None):
            self.assoc.observe(salience)
            self.episodes.append((salience, surprise))
        self.sequence.observe([p.concept for p in heard])
        self.active = concepts

        if self.feelings.tiredness >= 1.0:
            self.sleep()
            response.expression = "*falls asleep*"
        return response

    def tick(self, seconds: float) -> Response:
        """Let time pass. A bored baby acts on its own, a tired one sleeps."""
        self.feelings.waited(seconds)
        if self.feelings.tiredness >= 1.0:
            self.sleep()
            return Response(mode="sleep", expression="*falls asleep*", feeling="sleepy",
                            initiative=True)
        if self.feelings.boredom < 1.0:
            return Response(feeling=self.feelings.strongest())

        self.feelings.boredom = 0.3
        options = [Option("babble", IDLE + 0.5, words=[self.voice.babble(self.rng)],
                          expression="*babbles for attention*")]
        known = self._known_words()
        known = [k for k in known if self._fits_language(k[0])] or known
        if known:
            # Practice a word, more often one it is unsure of.
            weights = np.array([1.1 - k[2] for k in known])
            word, meaning, sureness = known[self.rng.choice(len(known), p=weights / weights.sum())]
            options.append(Option("practice", NEEDS + 1.0 - sureness,
                                  words=[self.words.label(word), "?"],
                                  credit=[(meaning, word)], expression="*tries a word*"))
        if self.actions:
            # Prefer the action that turned out most interesting here before.
            value = {a: sum(self.policy.w.get(c, {}).get(concept(a), 0.0) for c in self.active)
                     for a in self.actions}
            action = max(self.actions, key=lambda a: value[a] + self.rng.uniform(0, 0.3))
            options.append(Option("do", TRIES + self.feelings.curiosity, action=action,
                                  credit=[(c, concept(action)) for c in self.active or ["self"]],
                                  expression="*tries something*"))
        response = self._carry_out(choose(options, self.feelings.curiosity, self.rng))
        response.initiative = True
        return response

    def demonstrate(self, action: str) -> Response:
        """Show the baby an action in the current situation.

        It copies you, and links what it was perceiving to that action.
        """
        if action not in self.actions:
            self.actions.append(action)
        target = concept(action)
        for c in self.active:
            self.policy.nudge(c, target, 0.4)
        self._credit = [(c, target) for c in self.active]
        return Response(mode="do", action=action, expression="*copies you*",
                        feeling=self.feelings.strongest())

    def model(self, reply: str) -> Response:
        """Say an answer for the baby, the way parents say "say hi!".

        It repeats the answer and links the words it just heard to it, so the
        next time it hears them it can answer by itself.
        """
        words = tokenize(reply)
        heard = [self.words.perceive(encode_word(w), label=w) for w in words]
        if not heard:
            return Response(feeling=self.feelings.strongest())
        for w in words:
            self.voice.listen(w)
        self.sequence.observe([p.concept for p in heard])
        if self.language:
            for p in heard:
                seen_in = self.languages.setdefault(p.concept, {})
                seen_in[self.language] = seen_in.get(self.language, 0) + 1
        first = heard[0].concept
        prompts = [c for c in self.active if kind(c) == "word"
                   and self.foundation.role(self.words.label(c)) == CONTENT] or self.active
        for c in prompts:
            self.policy.nudge(c, first, 0.4)
        self._credit = [(c, first) for c in prompts]
        return Response(words=words, mode="imitate", expression="*copies you*",
                        feeling=self.feelings.strongest())

    def reward(self, amount: float, spare: set[str] = frozenset()) -> None:
        """Praise (positive) or correct (negative) what the baby just did.

        Only the links that produced its last words or action are changed.
        Words in ``spare`` are left alone, because the caregiver repeated them.
        """
        self.feelings.praised(amount)
        for source, target in self._credit:
            if target not in spare:
                self.policy.nudge(source, target, 0.3 * amount)

    def sleep(self) -> dict:
        """Consolidate memory: replay the day, fade everything, prune the unused."""
        salient = sorted(self.episodes, key=lambda e: e[1], reverse=True)[:50]
        for attention, _ in salient:
            self.assoc.observe(attention, weight=0.2)
        self.episodes.clear()

        self.assoc.decay(0.9, floor=0.05)
        self.sequence.decay(0.9, floor=0.05)
        self.policy.decay(0.95, floor=0.02)

        forgotten = set()
        for cortex in (self.words, *self.senses):
            unused = {c for c, n in zip(cortex.ids, cortex.usage)
                      if n <= 2 and c not in self.assoc.co}
            cortex.forget(unused)
            forgotten |= unused
        self.assoc.forget(forgotten)

        self.feelings.rested()
        self._glance = self._attended = None
        return {"replayed": len(salient), "forgotten": len(forgotten)}

    # Deciding

    def _options(self, concepts: list[str], content: list[Percept], seen: list[Percept],
                 surprise: float, passive: bool, asked: bool, feedback: float) -> list[Option]:
        face = self.feelings.expression(surprise)
        options = [Option("silent", IDLE)]
        threshold = CONFIDENCE - 0.05 * self.feelings.joy  # happy babies speak up sooner

        answer = self._answer(content, concepts, threshold)
        if answer:
            target, score, sources = answer
            credit = [(src, target) for src in sources]
            if kind(target) == "action":
                options.append(Option("do", KNOWS + 0.5 + min(score, 0.49), action=target.split(":", 1)[1],
                                      credit=credit, expression=face))
            else:
                options.append(Option("speak", KNOWS + 0.5 + min(score, 0.49),
                                      words=[self.words.label(c) for c in self._phrase(target)],
                                      credit=credit, expression=face))

        names = self._name([c for c in concepts if kind(c) != "word"], threshold)
        if names:
            said = [word for _, word, _ in names]
            if len(said) == 1:
                said = self._phrase(said[0])
            options.append(Option("speak", KNOWS + min(s for _, _, s in names),
                                  words=[self.words.label(c) for c in said],
                                  credit=[(src, w) for src, w, _ in names], expression=face))

        habit = self._habit([c for c in concepts if kind(c) != "word"], threshold)
        if habit:
            action, source, value = habit
            options.append(Option("do", KNOWS + value, action=action,
                                  credit=[(source, concept(action))], expression=face))

        if seen and not content:
            novel = any(self._usage(p.concept) <= NOVEL_USAGE for p in seen)
            if not passive or novel:
                face = "*tilts head*" if asked else "*points at it*"
                options.append(Option("ask", NEEDS + 0.5, words=["?"], expression=face))
        if passive:
            return options

        if asked and not content and not seen:
            options.append(Option("ask", NEEDS + 0.5, words=["?"], expression="*tilts head*"))
        if feedback and not content:
            face = "*giggles*" if feedback > 0 else "*looks down*"
            options.append(Option("react", NEEDS + 0.2, expression=face))
        if content and self.rng.random() < min(0.9, 0.2 + self.age / 100):
            target = max(content, key=lambda p: p.surprise).concept
            skill = min(1.0, self.age / 150)
            copy = self.voice.imitate(self.words.label(target), skill, self.rng)
            options.append(Option("imitate", TRIES + 0.5, words=[copy],
                                  credit=[(c, target) for c in concepts], expression=face))
        options.append(Option("babble", IDLE + 0.5, words=[self.voice.babble(self.rng)],
                              expression=face))
        return options

    def _carry_out(self, choice: Option) -> Response:
        self._credit = choice.credit
        if choice.mode == "ask":
            self.feelings.puzzled()
        confidence = choice.value - KNOWS if choice.value >= KNOWS else 0.0
        return Response(words=choice.words, mode=choice.mode, expression=choice.expression,
                        confidence=round(confidence, 2), action=choice.action,
                        feeling=self.feelings.strongest())

    def _answer(self, content: list[Percept], concepts: list[str],
                threshold: float) -> tuple[str, float, list[str]] | None:
        """The best reply (a word or an action) to what was just said.

        Every content word in the sentence votes with its habits, so in "what
        does a cat say" the word "cat" decides, and in "how old are you" both
        "old" and "you" add up. Returns ``(target, score, voters)``.
        """
        known = set(self.words.ids)
        votes: dict[str, float] = {}
        voters: dict[str, list[str]] = {}
        for p in {p.concept: p for p in content}.values():
            for target, weight in self.policy.neighbors(p.concept):
                if kind(target) == "action" or target in known:
                    votes[target] = votes.get(target, 0.0) + weight
                    voters.setdefault(target, []).append(p.concept)
        if not votes:
            return None
        fitting = {t: v for t, v in votes.items() if v >= threshold
                   and (kind(t) == "action" or self._fits_language(t))}
        pool = fitting or votes
        best = max(pool, key=pool.get)
        if votes[best] < threshold:
            return None
        return best, votes[best], voters[best]

    def _phrase(self, word: str) -> list[str]:
        """A word, continued by the words that usually follow it."""
        said = [word]
        while len(said) < 3:
            follow = self.sequence.likely_next(said[-1])
            if not follow or follow[1] < CHAIN or follow[0] in said:
                break
            said.append(follow[0])
        return said

    def _name(self, concepts: list[str], threshold: float) -> list[tuple[str, str, float]]:
        """For each thing seen or heard, the word that best names it.

        Returns ``(source, word, score)`` triples in speaking order (color,
        shape, sound), at most two.
        """
        known = set(self.words.ids)
        order = {"color": 0, "shape": 1, "sound": 2}
        found: dict[str, tuple[str, float]] = {}
        for source in sorted(concepts, key=lambda c: order[kind(c)]):
            scores = {w: s for w, s in self.assoc.names(source).items()
                      if w in known and w not in concepts}
            for other, weight in self.policy.neighbors(source):
                if other in known:
                    scores[other] = scores.get(other, 0.0) + weight
            if not scores:
                continue
            # Answer in the language it is spoken to, if it knows the word in it.
            fitting = {w: sc for w, sc in scores.items()
                       if sc >= threshold and self._fits_language(w)}
            pool = fitting or scores
            word = max(pool, key=pool.get)
            if scores[word] >= threshold and word not in found:
                found[word] = (source, scores[word])
        return [(source, word, score) for word, (source, score) in found.items()][:2]

    def _fits_language(self, word: str) -> bool:
        """Whether a word belongs to the language being spoken right now."""
        heard_in = self.languages.get(word)
        if not self.language or not heard_in:
            return True
        return max(heard_in, key=heard_in.get) == self.language

    def _habit(self, concepts: list[str], threshold: float) -> tuple[str, str, float] | None:
        """The action this situation most calls for, if any is strong enough."""
        best = None
        for source in concepts:
            for target, weight in self.policy.neighbors(source):
                if kind(target) == "action" and weight >= threshold:
                    if best is None or weight > best[2]:
                        best = (target.split(":", 1)[1], source, weight)
        return best

    def _salience(self, percepts: list[Percept], heard: list[Percept],
                  roles: list[str]) -> dict[str, float]:
        """How much attention each concept gets in this moment.

        Sights and sounds get full attention. Function words, praise and
        questions get little. Among content words later ones get more, since
        babies attend most to the end of a phrase, where new words usually
        land ("look, this is a *zebra*").
        """
        salience = {p.concept: 1.0 for p in percepts if p not in heard}
        content = [p for p, r in zip(heard, roles) if r == CONTENT]
        for p, r in zip(heard, roles):
            if r != CONTENT:
                salience[p.concept] = max(salience.get(p.concept, 0.0), QUIET)
        for i, p in enumerate(content):
            salience[p.concept] = max(salience.get(p.concept, 0.0), (i + 1) / len(content))
        return salience

    def _said(self) -> list[str]:
        return [t for _, t in self._credit if kind(t) == "word"]

    def _usage(self, c: str) -> int:
        cortex = next(x for x in (self.words, *self.senses) if x.kind == kind(c))
        return cortex.usage_of(c)

    def _worth_attention(self, view: str) -> bool:
        """Debounce a live view: react once, after the view has settled."""
        if view != self._glance:
            self._glance = view
            return False
        return view != self._attended

    def _known_words(self) -> list[tuple[str, str, float]]:
        """``(word, meaning, sureness)`` for every word it understands."""
        known = []
        for word in self.words.ids:
            meaning = self.assoc.referent(word)
            if meaning:
                sureness = self.assoc.names(meaning).get(word, 0.0)
                if sureness >= CONFIDENCE:
                    known.append((word, meaning, sureness))
        return known

    # Looking inside

    def vocabulary(self) -> list[dict]:
        """Words it understands, and what each one means to it.

        Names point at something it sensed (a color, a shape). Sayings are
        words it has learned to answer with, like "hi" or "meow".
        """
        result = []
        named = set()
        for word, meaning, sureness in self._known_words():
            cortex = next(c for c in self.senses if c.kind == kind(meaning))
            named.add(word)
            result.append({"word": self.words.label(word), "kind": kind(meaning),
                           "strength": round(sureness, 2), "picture": cortex.picture(meaning)})
        said: dict[str, float] = {}
        for links in self.policy.w.values():
            for target, weight in links.items():
                if kind(target) == "word" and target not in named and target in self.words.ids:
                    said[target] = max(said.get(target, 0.0), weight)
        for word, weight in said.items():
            if weight >= CONFIDENCE:
                result.append({"word": self.words.label(word), "kind": "saying",
                               "strength": round(min(weight, 1.0), 2), "picture": ""})
        return sorted(result, key=lambda x: (x["kind"], -x["strength"]))

    def habits(self) -> list[dict]:
        """Abilities, and what makes the baby use each one."""
        result = []
        for action in self.actions:
            target = concept(action)
            triggers = [self._describe(source) for source, links in self.policy.w.items()
                        if links.get(target, 0.0) >= CONFIDENCE]
            result.append({"action": action, "triggers": triggers})
        return result

    def stage(self) -> str:
        known = len(self.vocabulary())
        if known == 0 and self.age < 10:
            return "newborn"
        if known < 3:
            return "babbling"
        if known < 20:
            return "first words"
        if known < 100:
            return "toddler"
        return "child"

    def state(self) -> dict:
        """A snapshot of the baby for display."""
        return {
            "age": self.age,
            "stage": self.stage(),
            "feeling": self.feelings.strongest(),
            "feelings": self.feelings.to_dict(),
            "language": self.language,
            "concepts": {"words": len(self.words), "colors": len(self.colors),
                         "shapes": len(self.shapes), "sounds": len(self.sounds)},
            "links": len(self.assoc) + len(self.sequence) + len(self.policy),
            "vocabulary": self.vocabulary(),
            "actions": self.habits(),
        }

    def graph(self, limit: int = 400) -> dict:
        """Its concept network: the strongest links, for drawing."""
        edges = []
        for a, links in self.assoc.co.items():
            for b, co in links.items():
                if a < b and co >= 0.5:
                    edges.append({"from": a, "to": b, "weight": round(min(1.0, co / 4), 3),
                                  "type": "association"})
        for a, links in self.policy.w.items():
            for b, w in links.items():
                if w > 0.1:
                    edges.append({"from": a, "to": b, "weight": round(w, 3), "type": "habit"})
        # Little words ("of", "is", "yes") carry no meaning of their own, so leave them out.
        edges = [e for e in edges if self._meaningful(e["from"]) and self._meaningful(e["to"])]
        edges = sorted(edges, key=lambda e: -e["weight"])[:limit]
        lit = [c for c in self.active + [t for _, t in self._credit] if self._meaningful(c)]
        ids = {e["from"] for e in edges} | {e["to"] for e in edges} | set(lit)
        nodes = [self._node(c) for c in sorted(ids)]
        return {"nodes": [n for n in nodes if n], "edges": edges, "active": lit}

    def _meaningful(self, c: str) -> bool:
        if kind(c) != "word" or c not in self.words.ids:
            return True
        return self.foundation.role(self.words.label(c)) == CONTENT

    def _node(self, c: str) -> dict | None:
        k = kind(c)
        if k == "action":
            return {"id": c, "kind": k, "label": c.split(":", 1)[1], "picture": ""}
        cortex = next((x for x in (self.words, *self.senses) if x.kind == k), None)
        if cortex is None or c not in cortex.ids:
            return None
        label = cortex.label(c) if k == "word" else ""
        return {"id": c, "kind": k, "label": label, "picture": cortex.picture(c)}

    def _describe(self, c: str) -> str:
        """A human readable name for a concept: its word, if it has one."""
        if kind(c) == "word" and c in self.words.ids:
            return self.words.label(c)
        names = self.assoc.names(c)
        if names:
            return self.words.label(max(names, key=names.get))
        return f"a {kind(c)}"

    # Saving and loading, as plain JSON that is safe to share

    def to_dict(self) -> dict:
        return {
            "format": SAVE_FORMAT,
            "age": self.age,
            "feelings": self.feelings.to_dict(),
            "actions": self.actions,
            "language": self.language,
            "languages": self.languages,
            "words": self.words.to_dict(),
            "colors": self.colors.to_dict(),
            "shapes": self.shapes.to_dict(),
            "sounds": self.sounds.to_dict(),
            "assoc": self.assoc.to_dict(),
            "sequence": self.sequence.to_dict(),
            "policy": self.policy.to_dict(),
            "voice": self.voice.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict, seed: int | None = None) -> "Brain":
        if d.get("format") != SAVE_FORMAT:
            raise ValueError(f"unsupported brain format: {d.get('format')}")
        b = cls(seed, actions=d["actions"])
        b.age = d["age"]
        b.feelings = Feelings.from_dict(d["feelings"])
        b.language = d.get("language")
        b.languages = d.get("languages", {})
        b.words = Cortex.from_dict(d["words"])
        b.colors = Cortex.from_dict(d["colors"])
        b.shapes = Cortex.from_dict(d["shapes"])
        b.sounds = Cortex.from_dict(d["sounds"])
        b.assoc = Associations.from_dict(d["assoc"])
        b.sequence = Sequence.from_dict(d["sequence"])
        b.policy = Policy.from_dict(d["policy"])
        b.voice = Voice.from_dict(d["voice"])
        return b

    def save(self, path: str | Path) -> None:
        """Write the brain to a JSON file, atomically."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.to_dict()))
        tmp.replace(path)

    @classmethod
    def load(cls, path: str | Path) -> "Brain":
        return cls.from_dict(json.loads(Path(path).read_text()))
