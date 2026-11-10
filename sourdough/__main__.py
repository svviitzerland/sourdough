"""Raise Sourdough babies from the terminal or the browser.

    sourdough                         open the web app with the baby used last
    sourdough --name kiki             open the web app with kiki
    sourdough new kiki                create a baby, born knowing nothing
    sourdough new pip --level kid --about "a curious robot"
    sourdough list                    every baby and how far along it is
    sourdough feed kiki --pairs facts.json        learn answers from a JSON or CSV file
    sourdough feed kiki --folder ./pictures       learn words from pictures named after them
    sourdough feed kiki --ai openrouter --topic "animals" --count 20

Every baby starts as a newborn. ``--level`` (toddler, preschooler or kid) is
an optional starting pack that runs the built-in lessons once, at birth.
"""

from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

from .feeders import PROVIDERS, Teacher, feed, from_folder, from_pairs
from .foundation.lessons import levels
from .interface import serve
from .storage import Nest, babies, current, home


def main() -> None:
    packs = [level["name"] for level in levels()]
    parser = argparse.ArgumentParser(prog="sourdough", description="Raise a baby AI.")
    parser.add_argument("--home", type=Path, default=None,
                        help="folder that holds the babies (default ~/.sourdough/brains)")
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("serve", help="open the web app (the default)")
    new = sub.add_parser("new", help="create a baby")
    sub.add_parser("list", help="list every baby")
    fed = sub.add_parser("feed", help="teach a baby from files or another AI")

    for p in (parser, run):
        p.add_argument("--name", default=None, help="which baby to open")
        p.add_argument("--host", default="127.0.0.1")
        p.add_argument("--port", type=int, default=8008)
        p.add_argument("--no-browser", action="store_true", help="do not open a browser tab")

    new.add_argument("name")
    new.add_argument("--level", default="newborn", choices=packs, help="optional starting pack")
    new.add_argument("--about", default="", help="who it is, in a sentence")

    fed.add_argument("name")
    fed.add_argument("--pairs", type=Path, help="JSON or CSV file of prompts and answers")
    fed.add_argument("--folder", type=Path, help="folder of pictures named after what they show")
    fed.add_argument("--ai", choices=sorted(PROVIDERS) + ["custom"], help="an AI teacher")
    fed.add_argument("--model", default=None)
    fed.add_argument("--base-url", default=None, help="for a custom OpenAI compatible API")
    fed.add_argument("--topic", default="everyday things")
    fed.add_argument("--count", type=int, default=12)
    fed.add_argument("--language", default="en", choices=["en", "id"])

    args = parser.parse_args()
    folder = args.home or home()

    if args.command == "new":
        nest = Nest(args.name, folder)
        if nest.exists:
            parser.error(f"there is already a baby called {args.name}")
        baby = nest.create(args.level, about=args.about)
        print(f"{args.name} was born as a {args.level}, knowing {len(baby.vocabulary())} words.")
        print(f"It lives in {nest.folder}")
        return

    if args.command == "feed":
        nest = Nest(args.name, folder)
        if not nest.exists:
            parser.error(f"there is no baby called {args.name}")
        if args.pairs:
            moments = list(from_pairs(args.pairs))
        elif args.folder:
            moments = list(from_folder(args.folder))
        elif args.ai:
            teacher = Teacher(args.ai, model=args.model, base_url=args.base_url)
            print(f"Asking {args.ai} for {args.count} lessons about {args.topic}...")
            moments = list(teacher.lesson(args.topic, args.count, args.language))
        else:
            parser.error("choose --pairs, --folder or --ai")
        brain = nest.load()
        report = feed(brain, moments)
        nest.save(brain)
        nest.journal.write("fed", age=brain.age, taught=report["taught"], correct=report["correct"])
        for c in report["checked"]:
            mark = "right" if c["correct"] else "wrong"
            print(f"  {mark:5}  {c['prompt'] or '(picture)':32} {c['answer']:16} said: {c['said']}")
        print(f"{args.name} learned {report['correct']} of {report['taught']}.")
        return

    if args.command == "list":
        found = babies(folder)
        if not found:
            print("No babies yet. Create one with: sourdough new <name>")
        last = current(folder)
        for nest in found:
            p = nest.profile()
            mark = "*" if nest.name == last else " "
            about = f"  {p['about']}" if p.get("about") else ""
            print(f"{mark} {nest.name:16} {p.get('stage', '?'):12} {p.get('words', 0):4} words{about}")
        return

    server = serve(folder, name=args.name, host=args.host, port=args.port)
    nursery = server.nursery
    url = f"http://localhost:{server.server_address[1]}"
    who = nursery.nest.name if nursery.nest else "No baby yet, create one in the browser"
    print(f"Sourdough is running at {url}  ({who})")
    print(f"Babies live in {folder}. Press Ctrl+C to stop.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        nursery.save()
        print("\nGood night.")


if __name__ == "__main__":
    main()
