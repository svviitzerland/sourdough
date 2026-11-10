"""Start Sourdough and open it in your browser.

    sourdough                       raise the baby called "sourdough", born knowing nothing
    sourdough --level kid           a new baby that already went through every lesson
    sourdough --name kiki           raise (or wake up) another baby
    sourdough --host 0.0.0.0        let other devices on your network visit

Levels: newborn, toddler, preschooler, kid. A level only applies when the
baby is new. You can also pick or create babies from the web page.
"""

from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

from .foundation.lessons import levels
from .interface import serve
from .storage import Nest


def main() -> None:
    names = [level["name"] for level in levels()]
    parser = argparse.ArgumentParser(prog="sourdough", description="Raise a baby AI.")
    parser.add_argument("--name", default="sourdough", help="which baby to raise")
    parser.add_argument("--level", default="newborn", choices=names,
                        help="how much a new baby already knows")
    parser.add_argument("--starter", action="store_true", help="same as --level kid")
    parser.add_argument("--home", type=Path, default=None,
                        help="folder that holds the babies (default ~/.sourdough/brains)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8008)
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser tab")
    args = parser.parse_args()

    level = "kid" if args.starter else args.level
    nest = Nest(args.name, args.home)
    born = "woke up" if nest.exists else f"was born as a {level}"
    server = serve(nest, host=args.host, port=args.port, level=level)
    url = f"http://localhost:{server.server_address[1]}"
    print(f"{args.name} {born}. Visit {url}")
    print(f"Babies live in {nest.folder.parent}. Press Ctrl+C to put them to bed.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.nursery.save()
        print("\nGood night.")


if __name__ == "__main__":
    main()
