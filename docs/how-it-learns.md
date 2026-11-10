# How Sourdough learns

Large language models learn the way a library is built: collect everything first, then index it. Children learn differently. They get little data, almost all of it from a few people, grounded in what they can see and touch, one moment at a time. Yet a two year old can learn a word from hearing it once.

Sourdough copies the child, not the library. This page explains each mechanism, why it is there, and the research behind it. Every mechanism is small enough to read in one sitting.

## Design rules

1. **Born empty.** No concepts, no word meanings, no links at birth.
2. **Born with capacities.** Senses, a feel for how people talk to babies, and the ability to learn. Babies have these too.
3. **Always learning.** Living and learning are the same loop.
4. **One example can be enough.** A child cannot wait for a thousand labeled pictures.
5. **Meaning is grounded.** A word means what it reliably comes with in the world.

## 1. Senses

`sourdough/senses/`

The senses are fixed encoders. They turn input into vectors and never change, the way eyes and ears work from day one without knowing anything.

| Sense | Encoding | Like |
|---|---|---|
| Words | character 1 to 3 grams hashed into 128 numbers | the sound shape of a word, so "cat" and "cap" are close |
| Color | hue split by brightness and vividness, plus four grays, from the figure only | color selective cells |
| Shape | the distance from the center to the edge all the way around, summarized by its spread and its Fourier spectrum | form selective cells |
| Sound | loudness in 32 frequency bands | the cochlea |

**The fovea.** The baby looks only at the center of the view and separates the figure from the background, estimated from the edges of the view. A webcam frame is mostly room. Looking at the center means the object you hold up is what it sees.

**Two visual streams.** Color and shape are reported separately, as in the primate visual system. This is what makes fast, combinable learning possible. "Red" attaches to the color stream and "triangle" to the shape stream, so a red triangle it has never seen is still "red triangle".

**Shape without the details.** The shape code ignores color, size, position and rotation. A circle has a flat radius profile, a square four bumps, a triangle three, a star five. The strength of each number of bumps does not change when the shape turns.

## 2. Foundation

`sourdough/foundation/`

A newborn knows no words, yet it is not a blank slate. Long before understanding any word, infants tell short function words apart from content words and use them to find the words that matter (Shi and Werker, 2001). They read approval and prohibition in a caregiver's voice (Fernald, 1989), and they know when they are being asked something.

Sourdough gets the same head start as a small word list per language, in English and Indonesian:

* **function** words ("this", "is", "ini", "adalah") get little attention
* **praise** ("yes", "good", "iya", "bagus") becomes reward for what it just did
* **correction** ("no", "wrong", "bukan", "salah") becomes the opposite
* **questions** ("what", "apa") mean someone wants an answer, not an echo

The list never says what any word means. It only says what role a word plays in how people talk to babies. You can teach in plain language: "no, blue" corrects the last answer *and* teaches "blue" for what is in view.

It also tells **languages** apart. Each language's little words are known, so "ini" and "lihat" mark Indonesian and "this" and "look" mark English. Babies separate languages by their sound long before they know any words in them. Sourdough remembers which language each content word was heard in, and when it knows a word for something in the language it is being spoken to, it uses that one. Synonyms across languages are allowed to coexist, as they do for bilingual children.

The foundation also includes **lessons**: prepared experiences, like picture books. A lesson is not pretraining. It feeds ordinary moments through the same loop you use by hand, then quizzes the baby and answers in plain language. There are four kinds:

| Lesson | Teaches | How |
|---|---|---|
| Colors | 10 color words | picture cards, each color on varied shapes |
| Shapes | 8 shape words | picture cards, each shape in varied colors |
| Routines | 6 call and response pairs, like "hello" and "hi" | the teacher says the prompt, then *models* the reply, the way parents say "say hi!" (`Brain.model`) |

Knowledge packs for older babies work the same way as routines: about itself, what animals say, the colors of things, opposites, counting and kinds of things. Only the thing being taught stays constant across cards, so the statistics can work out what each word refers to. Two rounds pass every quiz, in both languages.

**Levels** bundle these: a newborn has taken nothing, a toddler colors, shapes and routines, a preschooler also the packs about itself and animals, a kid all of them. A level is just more experience, with one night of sleep after each language. Nothing is copied into its memory directly.

**Answering a question.** Every content word in what was said votes for the replies it is linked to, and the votes add up. In "what does a cat say" only "cat" decides. In "how old are you" both "old" and "you" add their votes to "baby". Words shared by many questions ("after", "opposite") vote for all their answers equally, so they cancel out.

## 3. Cortex: concepts that grow from nothing

`sourdough/mind/cortex.py`

Each sense has a cortex that starts with zero concepts. For each new percept:

* if it is similar enough to a known concept (the *vigilance* level), it is recognized and that concept moves a little toward it
* otherwise a new concept is born, and this example is its first prototype

This is the heart of **Adaptive Resonance Theory** (Carpenter and Grossberg, 1987). Learning something new never overwrites something old, because new things get new concepts. There are no epochs and no batches.

**Surprise** is one minus the best similarity. It measures how new a moment is. It drives curiosity and decides which memories are replayed in sleep.

## 4. Memory: what words mean

`sourdough/memory/associations.py`

Picture a parent saying "look, this is red" while holding a red cup. Which word names what? Is "red" the cup, its color or its handle? One moment is ambiguous, but across many moments only "red" reliably comes with red things. Infants use exactly these statistics (Yu and Smith, 2007, Smith and Yu, 2008).

Sourdough counts what co-occurs in moments when something was said, then decides meaning in two steps.

**Each word picks one meaning**, the thing it most reliably comes with:

```
score(thing) = P(thing | word) x (0.5 + 0.5 x P(word | thing))
```

Ties go to the thing heard with fewer other words. Once "red" means the color red, it stops competing for the circle it was painted on. Children show this **mutual exclusivity** bias (Markman and Wachtel, 1988). When a word is equally likely to mean a shape or a color, the shape wins by a small margin. That is the **shape bias** (Landau, Smith and Jones, 1988), which is why a new word heard once with a blue star is first taken to mean "star".

**A thing is named by the words that picked it**, each scored by

```
sureness = P(thing | word) x share x evidence
share    = its evidence divided by the evidence of the strongest word for the thing
evidence = co / (co + 1)
```

Weak claims next to a strong one count little, so a filler word that slipped in once is ignored. Two strong claims both stay sure, which is how "red" and "merah" can both mean the same color.

The evidence term makes one example a hint (0.5) and five a fact (0.83). Because everything is a ratio, a single clear naming moment is already usable. Children **fast map** like this (Carey and Bartlett, 1978).

**Attention.** Within an utterance, function words get 0.1 attention and content word *i* of *n* gets *(i + 1) / n*, so the last one gets full weight. Infants find words more easily at the end of utterances (Seidl and Johnson, 2006), and caregivers tend to put new words there.

## 5. Feelings

`sourdough/mind/feelings.py`

Feelings are numbers that rise and fall with experience and push decisions.

| Feeling | Rises when | Changes |
|---|---|---|
| joy | it is praised | happy, it speaks up sooner. Upset, it hesitates |
| curiosity | things are surprising | adds exploration to decisions |
| boredom | nothing new happens | when full, it starts something by itself |
| confusion | it cannot name what it is asked about | shows as a frown, fades as it learns |
| tiredness | every experience | when full, it decides to sleep |

Infants spend attention the same way: little on the fully familiar, little on chaos, most on what is just new enough (Kidd, Piantadosi and Aslin, 2012).

## 6. Deciding

`sourdough/mind/decide.py`

Every moment, the baby lists what it could do and gives each option a value in tiers:

| Tier | Options |
|---|---|
| knows | answer what was said, name what it sees, use an action it has learned for this situation |
| needs | ask about something new, react to praise, practice a word, sleep |
| tries | imitate a word, try an action |
| idle | babble, stay quiet |

The best option wins. Curiosity adds a little randomness, so sometimes it tries something new instead of repeating what worked. It always decides with what it knew *before* the moment, then learns from it.

With the live camera on, it glances every few seconds, reacts only when the view settles, and only once per view. It **habituates**: something seen many times that nobody named stops being interesting.

## 7. Acting and learning from consequences

`sourdough/body/`

Its **voice** develops in stages. Newborn babbling uses universal syllables like "ma" and "ba". Later babbling is built from the letter statistics of everything it has heard, so it drifts toward your language, as real babbling does (Kuhl, 2004). Imitation starts mangled and improves with age.

**Actions** are a body the host gives it: names it can choose, whose effects it does not know. On the web it can explore a folder of its own or glance through the camera. A robot could give it motors. The baby learns what actions are for in three ways:

* **Consequences.** Whatever an action brings back is perceived as a new moment, marked as the outcome of that action. Its surprise becomes a reward: `0.5 x (surprise - 0.25)`. Finding something new makes the action more likely in that situation, finding the same old thing makes it less likely. This is curiosity driven learning, the way infants keep repeating actions that make interesting things happen (Oudeyer, Kaplan and Hafner, 2007).
* **Demonstration.** You perform the action for it, and it links what it was perceiving to that action. One demonstration is enough.
* **Praise.** "Yes" or "no" after it acts strengthens or weakens the habit.

## 8. Feedback

Praise and correction change only the links that produced the last words or action. This is a three factor learning rule: what it perceived, what it did, and a global reward signal, the way dopamine is thought to gate learning in the brain (Schultz, Dayan and Montague, 1997, Frémaux and Gerstner, 2016). If you say "no, blue star" after it said "red star", "star" is spared because you repeated it.

## 9. Sleep

`Brain.sleep()`, when you ask or when it is tired:

1. **Replay.** The 50 most surprising moments are relived at low weight, like hippocampal replay during sleep (Wilson and McNaughton, 1994).
2. **Fade.** Every count shrinks by 10%. Well supported meanings survive, weak ones fall below threshold. Sleep renormalizes the strengthening of the day (Tononi and Cirelli, 2014).
3. **Prune.** Concepts seen once or twice and never linked to anything are deleted. Most passing camera frames end here.

Together this is a small version of **complementary learning systems** (McClelland, McNaughton and O'Reilly, 1995): fast learning from single episodes while awake, slower consolidation offline. A word learned once and never used fades after a few nights. A word used every day becomes permanent.

## 10. Its face

`web/src/lib/Face.svelte`, `Brain.face()`

It shows what it feels with a face, never with words. Expressions are not drawn by hand. Each one is a mix of facial muscles, named after the action units of the Facial Action Coding System (Ekman and Friesen, 1978):

| Muscle | Action unit | Driven by |
|---|---|---|
| lip corner puller | AU12 | joy, scaled by its learned smile |
| cheek raiser | AU6 | a strong smile, which makes it look real |
| lip corner depressor | AU15 | upset, being corrected |
| brow lowerer | AU4 | upset and confusion |
| brow raisers | AU1, AU2 | curiosity, surprise, asking |
| upper lid raiser | AU5 | surprise, listening |
| eyes closed | AU43 | tiredness, sleep, blinking |
| jaw drop | AU26 | talking, surprise, yawning |

Every muscle moves on a critically damped spring, so one expression flows into the next and can change half way, as a real face does.

Two things about its face are learned, the way they are in infants.

* **Control.** A newborn's expressions are small, imprecise and twitchy, with big eyes and faint brows. `face()["maturity"]` grows with age and vocabulary, and with it the range and steadiness of every expression (Oster, 2005).
* **The social smile.** Its smile starts weak. Each time it is praised while happy, `smile` grows a little, so a baby that people answer warmly smiles more broadly. Infants' smiles likewise turn social and grow when caregivers respond to them (Messinger and Fogel, 2007).

## What it cannot do yet

* It names, asks, answers and repeats short phrases, but it has no grammar.
* Its eyes know color and outline. Two different mugs look the same to it.
* Speech recognition comes from the browser, so its ears for words are borrowed, not grown.
* Its feelings are simple dials, not a model of itself.

Each of these is a good first contribution. See [growing-it.md](growing-it.md).

## References

* Carey, S., and Bartlett, E. (1978). Acquiring a single new word. *Papers and Reports on Child Language Development*, 15, 17 to 29.
* Carpenter, G. A., and Grossberg, S. (1987). A massively parallel architecture for a self-organizing neural pattern recognition machine. *Computer Vision, Graphics, and Image Processing*, 37(1), 54 to 115.
* Ekman, P., and Friesen, W. V. (1978). *Facial Action Coding System: A technique for the measurement of facial movement.* Consulting Psychologists Press.
* Fernald, A. (1989). Intonation and communicative intent in mothers' speech to infants: Is the melody the message? *Child Development*, 60(6), 1497 to 1510.
* Frémaux, N., and Gerstner, W. (2016). Neuromodulated spike-timing-dependent plasticity, and theory of three-factor learning rules. *Frontiers in Neural Circuits*, 9, 85.
* Kidd, C., Piantadosi, S. T., and Aslin, R. N. (2012). The Goldilocks effect: Human infants allocate attention to visual sequences that are neither too simple nor too complex. *PLoS ONE*, 7(5), e36399.
* Kuhl, P. K. (2004). Early language acquisition: Cracking the speech code. *Nature Reviews Neuroscience*, 5(11), 831 to 843.
* Landau, B., Smith, L. B., and Jones, S. S. (1988). The importance of shape in early lexical learning. *Cognitive Development*, 3(3), 299 to 321.
* Markman, E. M., and Wachtel, G. F. (1988). Children's use of mutual exclusivity to constrain the meanings of words. *Cognitive Psychology*, 20(2), 121 to 157.
* Messinger, D., and Fogel, A. (2007). The interactive development of social smiling. *Advances in Child Development and Behavior*, 35, 327 to 366.
* McClelland, J. L., McNaughton, B. L., and O'Reilly, R. C. (1995). Why there are complementary learning systems in the hippocampus and neocortex. *Psychological Review*, 102(3), 419 to 457.
* Oster, H. (2005). The repertoire of infant facial expressions: An ontogenetic perspective. In J. Nadel and D. Muir (Eds.), *Emotional Development* (pp. 261 to 292). Oxford University Press.
* Schultz, W., Dayan, P., and Montague, P. R. (1997). A neural substrate of prediction and reward. *Science*, 275(5306), 1593 to 1599.
* Seidl, A., and Johnson, E. K. (2006). Infant word segmentation revisited: Edge alignment facilitates target extraction. *Developmental Science*, 9(6), 565 to 573.
* Shi, R., and Werker, J. F. (2001). Six-month-old infants' preference for lexical words. *Psychological Science*, 12(1), 70 to 75.
* Smith, L., and Yu, C. (2008). Infants rapidly learn word-referent mappings via cross-situational statistics. *Cognition*, 106(3), 1558 to 1568.
* Tononi, G., and Cirelli, C. (2014). Sleep and the price of plasticity. *Neuron*, 81(1), 12 to 34.
* Oudeyer, P.-Y., Kaplan, F., and Hafner, V. V. (2007). Intrinsic motivation systems for autonomous mental development. *IEEE Transactions on Evolutionary Computation*, 11(2), 265 to 286.
* Turing, A. M. (1950). Computing machinery and intelligence. *Mind*, 59(236), 433 to 460.
* Wilson, M. A., and McNaughton, B. L. (1994). Reactivation of hippocampal ensemble memories during sleep. *Science*, 265(5172), 676 to 679.
* Yu, C., and Smith, L. B. (2007). Rapid word learning under uncertainty via cross-situational statistics. *Psychological Science*, 18(5), 414 to 420.
