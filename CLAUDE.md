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
sourdough new demo --level kid     # a new baby with the kid starter pack
sourdough list                     # every baby
python examples/first_words.py      # terminal demo
```

Each baby is a character with its own folder in `~/.sourdough/brains/<name>/` (`profile.json`, `brain.json`, `journal.jsonl`, `snapshots/`, `world/`). Code picks one by name with `Nest("kiki")`, the web app opens the one used last. Every baby is born a newborn. Starter packs (`foundation/lessons.json` `_levels`) only run once, at creation. Set `SOURDOUGH_HOME` to use a scratch folder while developing, so you never touch a real baby.

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

The web app is a separate Svelte 5 + Vite project in `web/`, styled with Tailwind CSS v4 and icons from Lucide (`@lucide/svelte`). It only talks to the HTTP API (`web/src/lib/api.js`), and all state and API calls live in `web/src/lib/baby.svelte.js`. Components read that state and call its functions.

```bash
sourdough --no-browser          # the API on :8008
cd web && npm install
npm run dev                     # the app on :5173, proxying /api to :8008
npm run build                   # writes sourdough/interface/static, commit it
```

The build is committed so `pip install` users get the app without Node. Rebuild and commit `sourdough/interface/static` whenever `web/` changes.

The layout is for people who are not technical and follows a Mac app: a sidebar of babies (`Sidebar.svelte`), the conversation under the baby's animated face (`Talk.svelte`, `Face.svelte`), and an inspector with a segmented control (`Inspector.svelte`): Mind (the concept network canvas), Teach (forms and lessons), Feed (AI teacher, pictures, files) and Diary. On narrow screens the sidebar and inspector open as sheets. Keep new controls inside an inspector tab.

Look and feel follows Apple's human interface guidelines. Colors are CSS variables in `web/src/app.css` with a light and a dark set, exposed as Tailwind tokens (`bg-surface`, `bg-fill`, `text-mute`, `text-accent`, `bg-blue`, `text-green` and so on), so never hard code a color. The font is the system font. Translucent materials use the `material` utility, large titles the `title` utility. Motion is critically damped springs, with feedback on press, and it respects reduced motion and reduced transparency. The Mind canvas reads its colors from `THEMES` in `Mind.svelte`. Style with Tailwind classes in the markup, not `<style>` blocks. Icons come only from Lucide. No emoji anywhere.

**The face shows, it does not tell.** Never write an expression as text. `Face.svelte` drives facial action units (FACS) from `state.feelings`, `state.face` (maturity and the learned smile) and `baby.moment` (praised, corrected, spoke, explored, slept). Add a new reaction by setting a moment in `baby.svelte.js` and mapping it to muscles, not by drawing a new face.

**Feeders turn outside data into experience.** `sourdough/feeders/` only produces moments (`name`, `reply`, `action`). `feed()` teaches them through the same `observe` and `model` calls a person would use. API keys come from the environment or are passed in, and are never written to disk.

## Common tasks

* **Add a lesson:** add an entry to `foundation/lessons.json` with `teaches` set to `color`, `shape`, `reply` or `action`, add it to a level in `_levels`, then run `pytest`.
* **Add a language:** add a block to `foundation/language.json` and translations to every lesson. `test_lesson_words_are_content_words` catches collisions.
* **Add a sense:** write an encoder in `senses/`, give it a `Cortex` in `Brain.__init__`, add its kind to `Brain.senses` and to the Mind view columns.
* **Add a feeder:** write a function in `feeders/` that yields moments like `{"kind": "reply", "prompt": ..., "answer": ...}`, pass them to `feed(brain, moments)`, and add a test in `tests/test_feeders.py`. An OpenAI compatible provider only needs an entry in `feeders/ai.py` `PROVIDERS`.
* **Add an action:** pass it in `Brain(actions=...)` (the web host adds its own in `interface/body.py`), carry out `response.action`, and report the result with `observe(..., outcome_of=...)`.
