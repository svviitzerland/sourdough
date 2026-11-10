# Architecture

Sourdough is organized like a body. Each folder is one part, and each part only talks to the parts next to it. This page explains the parts, how a moment flows through them, where data lives, and how to reach the baby from outside.

## The parts

```
sourdough/
  brain.py           the life loop that connects everything
  senses/            fixed encoders, the eyes and ears
    words.py           text to a vector by character n-grams
    vision.py          image to a color vector and a shape vector
    sound.py           audio to a frequency spectrum
  mind/              what it knows, feels and decides
    cortex.py          concepts that grow from nothing, one cortex per sense
    feelings.py        joy, curiosity, boredom, confusion, tiredness
    decide.py          options, tiers and the choice
  memory/            links between concepts, and a record of its life
    associations.py    what goes together, and what words mean
    sequence.py        which word comes next
    policy.py          habits shaped by praise and correction
    journal.py         the append only life story on disk
  body/              how it acts
    voice.py           babbling and imitation
    actions.py         action names, learned from their consequences
  foundation/        what it knows at birth
    language.json      word roles and language markers, English and Indonesian
    lessons.json       the built-in curriculum: colors, shapes, routines, actions
    lessons.py         draws lesson cards, runs lessons, grows a baby to a level
  storage.py         where each baby lives on disk
  interface/         how people reach it
    server.py          a standard library HTTP server
    body.py            the actions the web host carries out (explore, glance)
    static/            the built web app (from web/ at the repository root)
web/                 the Svelte web app, talks only to the HTTP API
```

Rules that keep it understandable:

* **Senses never learn.** Knowledge lives in the mind and memory, so you can swap a sense for a better one without touching anything else.
* **The brain never touches the disk or the network.** It is a pure in memory object. `storage.py` saves it and `interface/` serves it.
* **The brain decides, the host acts.** An action is only a name to the brain. The host carries it out and reports back what happened, which the brain perceives with `observe(..., outcome_of=action)`.
* **Data is plain JSON.** No pickles, no binary formats, nothing that can run code when loaded.

## One moment, step by step

Here is what happens when you hold up a red ball and say "look, red".

1. **Foundation.** "look" is a function word, "red" is content. No praise or correction was heard.
2. **Senses.** The words become vectors. The camera frame is cropped to its center, the ball is separated from the background, and vision reports a color vector and a shape vector.
3. **Cortex.** Each vector is compared with known concepts. The color matches `color:4`, the shape is new, so `shape:9` is born. Surprise is high.
4. **Feelings.** Surprise raises curiosity and clears boredom. Tiredness ticks up.
5. **Decide.** Using what it knew *before* this moment, it lists options. It already links `color:4` to "red" strongly, so "speak red" is in the top tier and wins.
6. **Learn.** The moment is recorded in memory: "red" now also co-occurs with the round shape, with "look" getting little attention.
7. **Journal.** The server appends one line to `journal.jsonl`.

When you then say "yes", the foundation hears praise, and the link that produced "red" is strengthened in the policy.

## Ways to teach it

| Method | Use it for |
|---|---|
| `observe(text, image, audio)` | everyday life: showing, naming, talking, praising |
| `model(reply)` | saying an answer for it, so it learns to reply to what it just heard |
| `demonstrate(action)` | showing it an action, so it links what it just perceived to that action |
| `observe(..., outcome_of=action)` | reporting what an action brought back, so surprise can reward it |
| `reward(amount)` | explicit praise or correction, when plain "yes" and "no" are not enough |
| `teach(brain, lesson, language)` | a prepared lesson with a quiz |
| `grow(brain, level)` | every lesson of a level (toddler, preschooler, kid) in every language |

## Time passes

Between messages the page calls `tick` every few seconds. Boredom grows while nothing new happens. When it is full, the baby decides to do something on its own: practice a word it is unsure of, try an action, or babble for attention. Tiredness grows with every experience. When it is full, the baby goes to sleep, and the server saves a snapshot.

## Where data lives

Each baby has a folder, under `~/.sourdough/brains` by default. Set `SOURDOUGH_HOME` or pass `--home` to move it.

```
~/.sourdough/brains/<name>/
  brain.json        what it knows
  journal.jsonl     what happened
  snapshots/
    age-000120.json
    age-000340.json
  world/            pictures and texts it can explore
```

| File | Holds | Written |
|---|---|---|
| `brain.json` | concepts (prototype vectors), every link, feelings, actions, languages, letter statistics | every 20 changes, after lessons and sleep, and on exit |
| `journal.jsonl` | time, event, what was heard, what it did and said, how it felt | every meaningful moment |
| `snapshots/` | dated copies of `brain.json`, the newest 14 are kept | after each sleep |

The journal never stores images or audio, only what was understood. A brain file is usually a few hundred kilobytes.

How data grows: every new thing seen or heard adds one concept, and every naming moment adds or strengthens links. Sleep works the other way. It fades every link a little and deletes concepts that were seen once or twice and never connected to anything, so the brain grows with what matters, not with every camera frame.

## Reaching it from outside

The server binds to `127.0.0.1:8008`. Any program that speaks HTTP and JSON can raise the baby.

| Method | Path | Body | Does |
|---|---|---|---|
| GET | `/api/state` | | name, age, stage, feelings, vocabulary, actions |
| GET | `/api/babies` | | every baby in this home, and the levels a new one can start at |
| GET | `/api/graph` | | its concept network: nodes, weighted edges, active concepts |
| GET | `/api/lessons` | | the built-in curriculum |
| GET | `/api/journal` | | its last 100 moments |
| POST | `/api/observe` | `text`, `image` (data URL), `audio` (`samples` as base64 float32, `rate`), `passive`, `outcome_of` | one moment of experience |
| POST | `/api/tick` | `seconds` | time passes, it may act on its own |
| POST | `/api/baby` | `name`, `level` | switch to a baby, creating it at a level if it is new |
| POST | `/api/show` | `action` | demonstrate an action |
| POST | `/api/lesson` | `name`, `language` | run a lesson and its quiz |
| POST | `/api/reward` | `amount` from -1 to 1 | praise or correct |
| POST | `/api/sleep` | | sleep now |

Every response that involves the baby acting returns a `response` with `words`, `mode`, `expression`, `action`, `feeling` and `initiative`, plus the current `state`.

To let a phone or another computer on your network visit, start with `--host 0.0.0.0`. Browsers only allow camera and microphone on `localhost` or HTTPS, so for those features on another device put the server behind an HTTPS proxy.
