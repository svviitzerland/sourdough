"""Raise Sourdough babies from the terminal or the browser.

    sourdough                         open the web app with the baby used last
    sourdough --name kiki             open the web app with kiki
    sourdough new kiki                create a baby, born knowing nothing
    sourdough new pip --level kid --about "a curious robot"
    sourdough list                    every baby and how far along it is

Every baby starts as a newborn. ``--level`` (toddler, preschooler or kid) is
an optional starting pack that runs the built-in lessons once, at birth.
"""

from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

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

    for p in (parser, run):
        p.add_argument("--name", default=None, help="which baby to open")
        p.add_argument("--host", default="127.0.0.1")
        p.add_argument("--port", type=int, default=8008)
        p.add_argument("--no-browser", action="store_true", help="do not open a browser tab")

    new.add_argument("name")
    new.add_argument("--level", default="newborn", choices=packs, help="optional starting pack")
    new.add_argument("--about", default="", help="who it is, in a sentence")

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
