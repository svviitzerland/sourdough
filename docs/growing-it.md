# Growing it

Sourdough is a starter: deliberately small, with clear places to add more. This page lists what you can give it next, roughly in order of how much each helps, and where each change goes.

One rule for every addition: **give it capacities, not knowledge.** Better eyes are fine. A list of object names is not. If a change would let Sourdough know something nobody showed it, it breaks the idea.

## Where this can go, honestly

Sourdough will not out-talk a large language model any time soon. Those models read a large part of the written world. A baby that learns from one household cannot match that breadth, and pretending otherwise would be dishonest.

What Sourdough can do that they cannot is different, and worth building:

* **It learns continuously from you**, during use, without retraining.
* **Its knowledge is grounded** in what it actually saw and heard, not in text about the world.
* **It is fully inspectable.** Every concept, link and decision can be read in a JSON file.
* **It is personal and small.** It runs anywhere, offline, and belongs to whoever raised it.

The path to a much more capable mind runs through the steps below. Each one adds a capacity and keeps the principle.

## 1. Better eyes

**The biggest win for real-world use.** Today it sees color and outline, enough for picture cards and simple objects, not enough to tell two mugs apart.

Add a third stream to `sourdough/senses/vision.py` that runs a small pretrained, **frozen** image encoder, such as a MobileNet or a CLIP image tower, and give it its own cortex in `brain.py`. Evolution hands babies a powerful visual system before they learn a single word, so a frozen encoder plays the part of innate perception. Names still come only from you.

Tune the new cortex's vigilance so two photos of the same object score above it and two different objects below it.

## 2. Ears of its own

Words currently arrive as text, typed or transcribed by the browser. To let it learn words from sound itself, segment the microphone stream into word sized pieces and give each its own concept in the sound cortex. A sound concept that reliably comes with a sight would then *be* a word, with no text involved. That is how infants do it, and it is a real research project.

## 3. Its own voice

The page speaks its words with the browser's speech synthesis. A next step is babbling in sound rather than letters, so imitation means matching your voice instead of your spelling.

## 4. A body

Actions are the interface for a body. The brain only knows action names. Whatever hosts it carries them out and reports back what happened, and the baby learns from the consequence: a surprising result makes the action more likely, a boring one less likely. `interface/body.py` is the web body, with two actions: exploring its own folder and glancing through the camera.

To give it a different body:

```python
baby = Brain(actions=["arm_left", "arm_right", "lamp"])
response = baby.observe(text="hello")
if response.action:
    result = my_robot.do(response.action)          # whatever your hardware does
    baby.observe(image=result.camera_frame, outcome_of=response.action)
```

Ideas that keep the principle: a motorized camera it can point (so it chooses what to look at), a speaker it can play sounds through (so it hears its own voice), or tools that fetch a random picture from the web, each just a new action. Never tell it what an action is *for*. Let it find out.

## 5. Prediction as the teacher

Have it predict the next moment: which sight follows, which word comes next. Use the prediction error as a learning signal (predictive coding, Rao and Ballard, 1999). The `Sequence` memory is a start. Extending it to every kind of concept would give it expectations, and with expectations, meaningful surprise.

## 6. Curiosity that seeks

Boredom makes it act today, but it does not choose *what to look at*. Track how fast surprise falls for each concept and prefer situations where it falls fastest, the ones it is learning most from (Oudeyer, Kaplan and Hafner, 2007).

## 7. Sentences

Two natural steps beyond single words:

* Let `Sequence` remember two or three previous words.
* Learn **frames** like "more ___" or "where is ___", where a known word fills a slot. Children build early grammar this way.

## 8. Living all the time

Run it as a process that never stops: camera on during the day, sleeping at night, a short summary of what it learned each morning drawn from its journal.

## Where things live

| You want to change | Look in |
|---|---|
| What it can sense | `senses/` |
| When something counts as new | the `vigilance` values in `Brain.__init__` |
| How meaning forms | `memory/associations.py`, `Brain._salience` |
| What it knows at birth | `foundation/language.json`, `foundation/lessons.json` |
| How it feels | `mind/feelings.py` |
| How it chooses | `mind/decide.py`, `Brain._options` |
| What it can do | `body/actions.py`, `interface/body.py` and the host |
| What it forgets | `Brain.sleep` |
| Where it is stored | `storage.py` |
| The web app | `web/src`, Svelte 5, `npm run dev` |

Every change should come with a behavioral test in `tests/`, written the way you would describe a child.

## References

* Oudeyer, P.-Y., Kaplan, F., and Hafner, V. V. (2007). Intrinsic motivation systems for autonomous mental development. *IEEE Transactions on Evolutionary Computation*, 11(2), 265 to 286.
* Rao, R. P. N., and Ballard, D. H. (1999). Predictive coding in the visual cortex. *Nature Neuroscience*, 2(1), 79 to 87.
