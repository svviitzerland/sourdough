# CLAUDE.md

Guidance for AI coding assistants (and humans) working in this repository.

## What this is

Sourdough is an open source starter for a baby AI. It is born knowing no words and learns only from experience: it sees, hears, talks, feels, decides and learns what its actions do. No pretraining, no dataset, no training phase. Read `README.md` first, then `docs/how-it-learns.md` for the mechanisms and `docs/architecture.md` for the parts.

## Commands

```bash
pyenv local 3.13.15                 # pinned in .python-version
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'

pytest                              # behavioral tests, about 4 seconds
sourdough                           # web app on http://localhost:8008
sourdough --name demo --level kid  # a new baby grown through every lesson
python examples/first_words.py      # terminal demo
```

Brains live in `~/.sourdough/brains/<name>/`. Set `SOURDOUGH_HOME` to use a scratch folder while developing, so you never touch a real baby.

## Layout

```
sourdough/
  brain.py          the life loop: observe, tick, model, demonstrate, reward, sleep
  senses/           fixed encoders: words.py, vision.py (color and shape), sound.py
  mind/             cortex.py (concepts), feelings.py, decide.py (options and tiers)
  memory/           associations.py (word meaning), sequence.py, policy.py, journal.py
  body/             voice.py (babble, imitate), actions.py
  foundation/       innate knowledge: language.json, lessons.json, lessons.py
  storage.py        Nest: brain.json, journal.jsonl, snapshots per baby
  interface/        server.py (stdlib HTTP API), body.py (web actions), static/ (built web app)
web/                the Svelte 5 + Vite web app, built into sourdough/interface/static
tests/              behavioral tests
docs/               how-it-learns.md, architecture.md, growing-it.md
```

## Rules that must not break

* **Capacities, not knowledge.** Never give the baby facts it was not taught. Better senses and new actions are fine. Word lists that carry meaning are not. `foundation/language.json` may only say what *role* a word plays (function, praise, correction, question).
* **Senses never learn.** Learning lives in `mind/` and `memory/`.
* **The brain is pure.** `Brain` never touches the disk or the network. `storage.py` saves it, `interface/` serves it.
* **The brain decides, the host acts.** Actions are names. The host carries them out and reports the result with `observe(..., outcome_of=action)`. Never hard code what an action is for, let the baby learn it from consequences.
* **Plain JSON only.** No pickle. Bump `SAVE_FORMAT` in `brain.py` when the saved shape changes.
* **Act before learning.** In `observe`, the baby responds with what it knew before the moment, then learns from it. Keep that order.
* **Dependencies stay tiny.** numpy and Pillow for the core, the standard library for the server, no frontend build step.

## Style

* Prose in docs, docstrings, comments and interface text: no semicolons and no em dashes. Write two sentences instead.
* No divider comments (lines of `=`, `-` or `#`). Short lines, plain words.
* Docstrings explain *why*, and cite the research when a mechanism comes from infant studies.
* In the page's JavaScript, compare with `==` and `!=`. Avoid `===`. No semicolons at line ends.
* No emoji anywhere in the interface.
* Commits follow Conventional Commits with the folder as scope, for example `feat(mind): add a hunger feeling`.

## Tests

Tests read like a baby's milestones: `test_learns_a_name_from_one_example`, `test_ignores_filler_words`. Add one for every behavior you change. Lessons must keep passing their quiz in two rounds, in every language (`tests/test_lessons.py`).

## The web app

The web app is a separate Svelte 5 + Vite project in `web/`. It only talks to the HTTP API (`web/src/lib/api.js`), and all state and API calls live in `web/src/lib/baby.svelte.js`. Components read that state and call its functions.

```bash
sourdough --no-browser          # the API on :8008
cd web && npm install
npm run dev                     # the app on :5173, proxying /api to :8008
npm run build                   # writes sourdough/interface/static, commit it
```

The build is committed so `pip install` users get the app without Node. Rebuild and commit `sourdough/interface/static` whenever `web/` changes.

The layout is for people who are not technical: the baby's mind fills the left (a canvas of its concept network in layers, colors, shapes, names, hears, says, actions), a panel on the right has three tabs, Talk (conversation, suggestions, say bar), Teach (lessons, actions) and Diary (its life). A picker chooses a baby level on the first visit. Keep new controls inside a tab, not in the header.

Look and feel: a midnight blue ground, soft white text and one warm peach accent (`web/src/app.css` holds every color). The mind's strands glow in the color of the layer they lead into (names blue, hears lilac, says peach, actions mint) or of the color concept they touch. One friendly font, Plus Jakarta Sans, self hosted in `web/public/fonts`. Rounded, quiet surfaces. No emoji.

## Common tasks

* **Add a lesson:** add an entry to `foundation/lessons.json` with `teaches` set to `color`, `shape`, `reply` or `action`, add it to a level in `_levels`, then run `pytest`.
* **Add a language:** add a block to `foundation/language.json` and translations to every lesson. `test_lesson_words_are_content_words` catches collisions.
* **Add a sense:** write an encoder in `senses/`, give it a `Cortex` in `Brain.__init__`, add its kind to `Brain.senses` and to the Mind view columns.
* **Add an action:** pass it in `Brain(actions=...)` (the web host adds its own in `interface/body.py`), carry out `response.action`, and report the result with `observe(..., outcome_of=...)`.
