# Contributing

Thank you for helping Sourdough grow.

## Setup

```bash
pyenv install 3.13      # optional, any Python 3.11 or newer works
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

For the web app:

```bash
cd web && npm install && npm run dev    # needs `sourdough` running for the API
npm run build                            # before committing changes to web/
```

## Principles

1. **Capacities, not knowledge.** Give the baby better senses or new actions, never facts it was not taught. A pretrained image encoder is fine. A list of object names is not.
2. **Every moment teaches.** No training phase and no hidden state that cannot be inspected.
3. **Readable over clever.** Someone new should understand any module in one sitting.
4. **Cite the science.** If a mechanism comes from infant research, name the paper in the docstring and in `docs/how-it-learns.md`.

## Tests

Tests describe behavior the way you would describe a child: "learns a word from one example", "asks about something new", "stops asking about things it has seen many times". Add one for every behavior you change.

## Style

* Short lines, plain words, docstrings that explain *why*.
* No divider comments.
* In prose (docs, docstrings, comments, interface text) avoid semicolons and em dashes. Use two sentences instead.

## Commits

Follow [Conventional Commits](https://www.conventionalcommits.org):

```
feat(mind): add a hunger feeling
fix(vision): ignore the background when the figure is tiny
docs: explain the journal format
```

Common types are `feat`, `fix`, `docs`, `test`, `refactor` and `chore`. Use the folder name as the scope.

## Adding a language

Add a block to `sourdough/foundation/language.json` with its function, praise, correction and question words, and its phrases to `lessons.json`. Run `pytest` to check that no lesson word collides with a role word.
