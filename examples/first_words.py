"""Watch Sourdough learn its first words in the terminal.

It takes the two built-in lessons, then names a combination it was never
shown: colors and shapes were taught separately, so a purple heart is new.

    python examples/first_words.py
    python examples/first_words.py id     # in Indonesian
"""

import sys

import numpy as np

from sourdough import Brain
from sourdough.foundation.lessons import draw, teach

language = sys.argv[1] if len(sys.argv) > 1 else "en"
baby = Brain(seed=0)
rng = np.random.default_rng(7)

print("A newborn sees a purple heart:")
print("  baby:", baby.observe(image=draw("heart", (140, 60, 190), rng)))

for name in ("colors", "shapes"):
    result = teach(baby, name, language, rounds=2, seed=1)
    print(f"\nLesson: {result['lesson']}, quiz {result['score']}/{result['total']}")
    for r in result["results"]:
        mark = "right" if r["correct"] else "wrong"
        print(f"  shown {r['word']:10} said {r['said'] or '-':16} {mark}")

print("\nNever shown together before:")
for shape, rgb in (("heart", (140, 60, 190)), ("star", (240, 130, 30))):
    print(f"  a {shape} in a new color  ->  baby: {baby.observe(image=draw(shape, rgb, rng))}")

print(f"\nIt now understands {len(baby.vocabulary())} words, "
      f"after {baby.age} experiences.")
