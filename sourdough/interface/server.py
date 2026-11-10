"""A small local server: the JSON API, plus the built web app.

Standard library only. The browser handles the camera, microphone, speech
recognition and speech synthesis. This server holds the brains, carries out
actions and writes each baby's journal. Any program that speaks HTTP and JSON
can use the same API, so the baby is not tied to the web app.

The web app lives in ``web/`` at the repository root (Svelte). Its build is
written to ``static/`` next to this file, and served from here.

    GET  /                the web app
    GET  /api/suggestions things worth saying to this baby
    GET  /api/state       how the current baby is doing
    GET  /api/babies      every baby in this home, and the levels to start at
    GET  /api/graph       its concept network
    GET  /api/lessons     the built-in curriculum
    GET  /api/journal     its most recent moments
    POST /api/baby        {"name", "level"}  switch to a baby, or create it
    POST /api/observe     {"text", "image", "audio", "passive", "outcome_of"}
    POST /api/tick        {"seconds"}  time passes, it may act on its own
    POST /api/show        {"action"}   demonstrate an action
    POST /api/lesson      {"name", "language"}
    POST /api/reward      {"amount"}   from -1 to 1
    POST /api/sleep
"""

from __future__ import annotations

import base64
import json
import mimetypes
import random
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

from ..brain import Response
from ..foundation.lessons import LANGUAGES, catalog, curriculum, levels, teach
from ..storage import Nest, babies
from .body import ACTIONS, Body

STATIC = Path(__file__).parent / "static"
MISSING = b"""<!doctype html><meta charset="utf-8"><title>Sourdough</title>
<body style="font-family:monospace;background:#0d0d0f;color:#f2f1ed;padding:40px">
<p>The web app has not been built yet. Run:</p>
<pre>cd web && npm install && npm run build</pre>
<p>The API is running at /api/state.</p></body>"""
MAX_BODY = 10 * 1024 * 1024
SAVE_EVERY = 20


class Nursery:
    """Looks after the babies: serializes access, saves, keeps journals."""

    def __init__(self, nest: Nest, level: str = "newborn"):
        self.root = nest.folder.parent
        self.lock = threading.Lock()
        self._unsaved = 0
        self._open(nest, level)

    def _open(self, nest: Nest, level: str = "newborn") -> None:
        self.nest = nest
        self.brain = nest.load() if nest.exists else nest.create(level)
        for action in ACTIONS:
            if action not in self.brain.actions:
                self.brain.actions.append(action)
        self.body = Body(nest.world)
        self._unsaved = 0

    def baby(self, name: str, level: str) -> dict:
        with self.lock:
            self.nest.save(self.brain)
            self._open(Nest(name, self.root), level)
            return self._status()

    def babies(self) -> dict:
        with self.lock:
            listing = []
            for nest in babies(self.root):
                brain = self.brain if nest.name == self.nest.name else nest.load()
                listing.append({"name": nest.name, "age": brain.age, "stage": brain.stage(),
                                "words": len(brain.vocabulary())})
            return {"current": self.nest.name, "babies": listing, "levels": levels()}

    def observe(self, body: dict) -> dict:
        audio = body.get("audio")
        samples = None
        if audio:
            samples = np.frombuffer(base64.b64decode(audio["samples"]), np.float32)
        with self.lock:
            response = self.brain.observe(
                text=body.get("text") or None,
                image=body.get("image") or None,
                audio=samples,
                sample_rate=int(audio["rate"]) if audio else 16000,
                passive=bool(body.get("passive")),
                outcome_of=body.get("outcome_of") or None,
            )
            if response.mode != "silent" or body.get("text"):
                self._remember("moment", response, heard=body.get("text") or "",
                               saw=bool(body.get("image")), sound=bool(audio))
            return self._reply(response)

    def tick(self, seconds: float) -> dict:
        with self.lock:
            response = self.brain.tick(max(0.0, min(seconds, 600.0)))
            if response.mode == "sleep":
                self._slept()
            elif response.initiative and response.mode != "silent":
                self._remember("initiative", response)
            return self._reply(response)

    def show(self, action: str) -> dict:
        with self.lock:
            response = self.brain.demonstrate(action)
            self._remember("demonstration", response)
            return self._reply(response)

    def lesson(self, name: str, language: str) -> dict:
        with self.lock:
            result = teach(self.brain, name, language)
            self.nest.journal.write("lesson", lesson=result["lesson"], score=result["score"],
                                    total=result["total"], age=self.brain.age)
            self.nest.save(self.brain)
            return {"lesson": result, "state": self.brain.state()}

    def reward(self, amount: float) -> dict:
        with self.lock:
            amount = max(-1.0, min(1.0, amount))
            self.brain.reward(amount)
            self.nest.journal.write("feedback", amount=amount, age=self.brain.age)
            self._changed()
            return {"state": self.brain.state()}

    def sleep(self) -> dict:
        with self.lock:
            report = self.brain.sleep()
            self._slept(report)
            return {"report": report, "state": self.brain.state()}

    def state(self) -> dict:
        with self.lock:
            return self._status()

    def graph(self) -> dict:
        with self.lock:
            return self.brain.graph()

    def journal(self) -> dict:
        return {"moments": self.nest.journal.recent(100)}

    def suggestions(self) -> dict:
        """A few prompts from the lessons whose answers this baby already knows."""
        with self.lock:
            known = {v["word"] for v in self.brain.vocabulary()}
            language = self.brain.language or "en"
        prompts = []
        for name, lesson in curriculum().items():
            if name.startswith("_") or lesson["teaches"] != "reply":
                continue
            for item in lesson["items"]:
                pair = item[language if language in LANGUAGES else "en"]
                if pair["reply"].split()[0] in known:
                    prompts.append(pair["prompt"])
        random.shuffle(prompts)
        return {"prompts": prompts[:4], "language": language}

    def save(self) -> None:
        with self.lock:
            self.nest.save(self.brain)
            self._unsaved = 0

    def _status(self) -> dict:
        return {"name": self.nest.name, "state": self.brain.state()}

    def _reply(self, response: Response) -> dict:
        """The response, plus the consequence if it chose an action the server can do."""
        reply = {"response": response.to_dict()}
        if response.action == "explore":
            found = self.body.explore()
            if found:
                followup = self.brain.observe(text=found.get("text"), image=found.get("image"),
                                              outcome_of="explore")
                self._remember("explored", followup, file=found["file"])
                reply["outcome"] = {"file": found["file"], "image": found.get("image"),
                                    "text": found.get("text"), "response": followup.to_dict()}
        reply["state"] = self.brain.state()
        return reply

    def _remember(self, event: str, response: Response, **details) -> None:
        self.nest.journal.write(event, age=self.brain.age, did=response.mode,
                                said=" ".join(response.words), action=response.action,
                                feeling=response.feeling, **details)
        self._changed()

    def _slept(self, report: dict | None = None) -> None:
        self.nest.journal.write("sleep", age=self.brain.age, **(report or {}))
        self.nest.save(self.brain)
        self.nest.snapshot(self.brain)
        self._unsaved = 0

    def _changed(self) -> None:
        self._unsaved += 1
        if self._unsaved >= SAVE_EVERY:
            self.nest.save(self.brain)
            self._unsaved = 0


ROUTES_GET = {
    "/api/state": lambda n, b: n.state(),
    "/api/babies": lambda n, b: n.babies(),
    "/api/graph": lambda n, b: n.graph(),
    "/api/lessons": lambda n, b: {"lessons": catalog()},
    "/api/journal": lambda n, b: n.journal(),
    "/api/suggestions": lambda n, b: n.suggestions(),
}
ROUTES_POST = {
    "/api/baby": lambda n, b: n.baby(str(b.get("name") or b.get("level") or "sourdough"),
                                     str(b.get("level") or "newborn")),
    "/api/observe": lambda n, b: n.observe(b),
    "/api/tick": lambda n, b: n.tick(float(b.get("seconds", 0))),
    "/api/show": lambda n, b: n.show(str(b["action"])),
    "/api/lesson": lambda n, b: n.lesson(b["name"], b.get("language", "en")),
    "/api/reward": lambda n, b: n.reward(float(b.get("amount", 0))),
    "/api/sleep": lambda n, b: n.sleep(),
}


def make_handler(nursery: Nursery):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path.startswith("/api/"):
                return self._route(ROUTES_GET, {})
            self._static(path)

        def _static(self, path: str) -> None:
            """Serve a built file, or the app itself for any other page."""
            root = STATIC.resolve()
            target = (root / path.lstrip("/")).resolve()
            if root not in target.parents or not target.is_file():
                target = root / "index.html"
            if not target.is_file():
                return self._send(HTTPStatus.OK, MISSING, "text/html; charset=utf-8")
            kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if kind.startswith("text/") or kind.endswith("javascript"):
                kind += "; charset=utf-8"
            self._send(HTTPStatus.OK, target.read_bytes(), kind, cache="/assets/" in path)

        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self._json({"error": "too large"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                return self._json({"error": "invalid JSON"}, HTTPStatus.BAD_REQUEST)
            self._route(ROUTES_POST, body)

        def _route(self, routes: dict, body: dict) -> None:
            handler = routes.get(self.path)
            if handler is None:
                return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            try:
                self._json(handler(nursery, body))
            except (ValueError, KeyError, OSError) as e:
                self._json({"error": str(e)}, HTTPStatus.BAD_REQUEST)

        def _json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            self._send(status, json.dumps(data).encode(), "application/json")

        def _send(self, status: HTTPStatus, payload: bytes, content_type: str,
                  cache: bool = False) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "max-age=86400" if cache else "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args) -> None:
            pass  # keep the terminal quiet

    return Handler


def serve(nest: Nest, host: str = "127.0.0.1", port: int = 8008,
          level: str = "newborn") -> ThreadingHTTPServer:
    """Create the server. Call ``serve_forever`` on the result to run it."""
    nursery = Nursery(nest, level)
    server = ThreadingHTTPServer((host, port), make_handler(nursery))
    server.nursery = nursery
    return server


__all__ = ["Nursery", "serve"]
