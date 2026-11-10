"""A small local server: the JSON API, plus the built web app.

Standard library only. The browser handles the camera, microphone, speech
recognition and speech synthesis. This server holds the babies, carries out
their actions and writes their journals. Any program that speaks HTTP and
JSON can use the same API, so the babies are not tied to the web app.

The web app lives in ``web/`` at the repository root (Svelte). Its build is
written to ``static/`` next to this file, and served from here.

Babies (characters)

    GET  /api/babies          every baby, which one is open, and the starting packs
    POST /api/babies          {"name", "about", "color", "level"}  create one and open it
    POST /api/baby            {"name"}  open a baby
    POST /api/baby/edit       {"about", "color"}  change the open baby's profile
    POST /api/baby/delete     {"name"}  move a baby to the trash

The open baby

    GET  /api/state           how it is doing
    GET  /api/graph           its concept network
    GET  /api/journal         its most recent moments
    GET  /api/suggestions     things worth saying to it
    GET  /api/lessons         the built-in lessons
    POST /api/observe         {"text", "image", "audio", "passive", "outcome_of"}
    POST /api/teach           {"kind": "name" | "reply" | "action", "prompt", "answer", "image", "action"}
    POST /api/correct         {"answer", "prompt", "image"}  "no", then the right answer
    POST /api/tick            {"seconds"}  time passes, it may act on its own
    POST /api/show            {"action"}   demonstrate an action
    POST /api/lesson          {"name", "language"}
    GET  /api/feeders         the AI providers it can learn from, and which have a key
    POST /api/feed            {"source": "pairs" | "pictures" | "ai", ...}  learn from outside
    POST /api/reward          {"amount"}   from -1 to 1
    POST /api/sleep

Calls about the open baby answer 409 when no baby has been created yet.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import random
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

from ..brain import Response
from ..feeders import PROVIDERS, Teacher, feed, label_of
from ..foundation.lessons import LANGUAGES, catalog, curriculum, levels, teach
from ..storage import Nest, babies, current, remember_current
from .body import ACTIONS, Body

STATIC = Path(__file__).parent / "static"
MISSING = b"""<!doctype html><meta charset="utf-8"><title>Sourdough</title>
<body style="font-family:sans-serif;background:#0a0d16;color:#eef1f8;padding:40px">
<p>The web app has not been built yet. Run:</p>
<pre>cd web && npm install && npm run build</pre>
<p>The API is running at /api/state.</p></body>"""
MAX_BODY = 10 * 1024 * 1024
SAVE_EVERY = 20


class NoBaby(LookupError):
    """Raised when a call needs a baby and none has been created yet."""


class Nursery:
    """Looks after the babies: one is open at a time, the rest wait on disk."""

    def __init__(self, folder: Path, name: str | None = None, level: str = "newborn"):
        self.folder = folder
        self.lock = threading.Lock()
        self.nest: Nest | None = None
        self.brain = None
        self.keys: dict[str, str] = {}   # API keys typed in the web app, kept in memory only
        self._unsaved = 0
        name = name or current(folder)
        if name:
            nest = Nest(name, folder)
            if not nest.exists:
                nest.create(level)
            self._open(nest)

    # Babies

    def _open(self, nest: Nest) -> None:
        if self.nest and self.brain:
            self.nest.save(self.brain)
        self.nest = nest
        self.brain = nest.load()
        for action in ACTIONS:
            if action not in self.brain.actions:
                self.brain.actions.append(action)
        self.body = Body(nest.world)
        self._unsaved = 0
        remember_current(nest.name, self.folder)

    def list(self) -> dict:
        with self.lock:
            if self.nest and self.brain:
                self.nest.save(self.brain)
            return {
                "current": self.nest.name if self.nest else None,
                "babies": [nest.profile() | {"name": nest.name} for nest in babies(self.folder)],
                "levels": levels(),
            }

    def create(self, name: str, about: str, color: str, level: str) -> dict:
        with self.lock:
            nest = Nest(name.strip(), self.folder)
            if nest.exists:
                raise ValueError(f"there is already a baby called {nest.name}")
            if level not in {lvl["name"] for lvl in levels()}:
                raise ValueError(f"unknown starting pack: {level}")
            nest.create(level, about=about, color=color)
            self._open(nest)
            return self._status()

    def switch(self, name: str) -> dict:
        with self.lock:
            nest = Nest(name, self.folder)
            if not nest.exists:
                raise ValueError(f"there is no baby called {name}")
            self._open(nest)
            return self._status()

    def edit(self, about: str | None, color: str | None) -> dict:
        with self.lock:
            self._need()
            self.nest.describe(about, color)
            return self._status()

    def delete(self, name: str) -> dict:
        with self.lock:
            nest = Nest(name, self.folder)
            if not nest.exists:
                raise ValueError(f"there is no baby called {name}")
            if self.nest and self.nest.name == name:
                self.nest, self.brain = None, None
            nest.delete()
            remaining = babies(self.folder)
            if not self.nest and remaining:
                self._open(remaining[0])
            elif not self.nest:
                remember_current(None, self.folder)
        return self.list()

    # The open baby

    def state(self) -> dict:
        with self.lock:
            if not self.brain:
                return {"name": None, "profile": None, "state": None}
            return self._status()

    def observe(self, body: dict) -> dict:
        audio = body.get("audio")
        samples = None
        if audio:
            samples = np.frombuffer(base64.b64decode(audio["samples"]), np.float32)
        with self.lock:
            self._need()
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

    def teach(self, body: dict) -> dict:
        """Teach one thing in one step, the way the web app's forms do."""
        with self.lock:
            self._need()
            response = self._teach(body)
            self.nest.journal.write("taught", age=self.brain.age, what=body.get("kind"),
                                    prompt=body.get("prompt") or "", answer=body.get("answer") or "",
                                    action=body.get("action") or "")
            self._changed()
            return self._reply(response)

    def correct(self, body: dict) -> dict:
        """It got something wrong: say no, then teach the right answer."""
        with self.lock:
            self._need()
            self.brain.reward(-1.0)
            kind = "name" if body.get("image") else "reply" if body.get("prompt") else "word"
            response = self._teach(body | {"kind": kind})
            self.nest.journal.write("corrected", age=self.brain.age, answer=body.get("answer") or "")
            self._changed()
            return self._reply(response)

    def _teach(self, body: dict) -> Response:
        kind = body.get("kind")
        answer = (body.get("answer") or "").strip()
        prompt = (body.get("prompt") or "").strip()
        if kind == "name":
            if not body.get("image") or not answer:
                raise ValueError("naming needs a picture and a word")
            return self.brain.observe(text=answer, image=body["image"])
        if kind == "reply":
            if not prompt or not answer:
                raise ValueError("a reply needs what you say and what it should answer")
            self.brain.observe(text=prompt)
            return self.brain.model(answer)
        if kind == "action":
            action = body.get("action")
            if not prompt or action not in self.brain.actions:
                raise ValueError("an action needs a word and one of its actions")
            self.brain.observe(text=prompt)
            return self.brain.demonstrate(action)
        if kind == "word" and answer:
            return self.brain.observe(text=answer)
        raise ValueError("unknown kind of teaching")

    def tick(self, seconds: float) -> dict:
        with self.lock:
            self._need()
            response = self.brain.tick(max(0.0, min(seconds, 600.0)))
            if response.mode == "sleep":
                self._slept()
            elif response.initiative and response.mode != "silent":
                self._remember("initiative", response)
            return self._reply(response)

    def show(self, action: str) -> dict:
        with self.lock:
            self._need()
            response = self.brain.demonstrate(action)
            self._remember("demonstration", response)
            return self._reply(response)

    def lesson(self, name: str, language: str) -> dict:
        with self.lock:
            self._need()
            result = teach(self.brain, name, language, who=self.nest.name)
            self.nest.journal.write("lesson", lesson=result["lesson"], score=result["score"],
                                    total=result["total"], age=self.brain.age)
            self.nest.save(self.brain)
            return {"lesson": result, "state": self.brain.state()}

    def feeders(self) -> dict:
        return {"providers": [
            {"name": name, "model": info["model"], "url": info["url"],
             "ready": not info["key"] or bool(os.environ.get(info["key"]) or self.keys.get(name)),
             "key": info["key"]}
            for name, info in PROVIDERS.items()
        ]}

    def feed(self, body: dict) -> dict:
        """Learn from outside: pairs, named pictures, or an AI teacher."""
        source = body.get("source")
        if source == "pairs":
            moments = [{"kind": "reply", "prompt": str(p.get("prompt", "")), "answer": str(p.get("answer", ""))}
                       for p in body.get("pairs", [])]
        elif source == "pictures":
            moments = [{"kind": "name", "image": p["image"], "answer": p.get("label") or label_of(p.get("file", ""))}
                       for p in body.get("pictures", []) if p.get("image")]
        elif source == "ai":
            provider = str(body.get("provider") or "openai")
            if body.get("api_key"):
                self.keys[provider] = str(body["api_key"]).strip()
            teacher = Teacher(provider, model=body.get("model") or None, api_key=self.keys.get(provider),
                              base_url=body.get("base_url") or None)
            # Ask the teacher before taking the lock: it can take a while.
            moments = list(teacher.lesson(str(body.get("topic") or ""), int(body.get("count") or 12),
                                          str(body.get("language") or "en")))
        else:
            raise ValueError("unknown source, use pairs, pictures or ai")
        if not moments:
            raise ValueError("there was nothing to learn from")
        with self.lock:
            self._need()
            report = feed(self.brain, moments)
            self.nest.journal.write("fed", age=self.brain.age, source=source, taught=report["taught"],
                                    correct=report["correct"], topic=body.get("topic") or "")
            self.nest.save(self.brain)
            return {"report": report, "state": self.brain.state()}

    def reward(self, amount: float) -> dict:
        with self.lock:
            self._need()
            amount = max(-1.0, min(1.0, amount))
            self.brain.reward(amount)
            self.nest.journal.write("feedback", amount=amount, age=self.brain.age)
            self._changed()
            return {"state": self.brain.state()}

    def sleep(self) -> dict:
        with self.lock:
            self._need()
            report = self.brain.sleep()
            self._slept(report)
            return {"report": report, "state": self.brain.state()}

    def graph(self) -> dict:
        with self.lock:
            self._need()
            return self.brain.graph()

    def journal(self) -> dict:
        with self.lock:
            self._need()
            return {"moments": self.nest.journal.recent(100)}

    def suggestions(self) -> dict:
        """A few prompts from the lessons whose answers this baby already knows."""
        with self.lock:
            self._need()
            known = {v["word"] for v in self.brain.vocabulary()}
            language = self.brain.language if self.brain.language in LANGUAGES else "en"
            name = self.nest.name.lower()
        prompts = []
        for key, lesson in curriculum().items():
            if key.startswith("_") or lesson["teaches"] != "reply":
                continue
            for item in lesson["items"]:
                pair = item[language]
                if pair["reply"].replace("{name}", name).split()[0] in known:
                    prompts.append(pair["prompt"])
        random.shuffle(prompts)
        return {"prompts": prompts[:4], "language": language}

    def save(self) -> None:
        with self.lock:
            if self.nest and self.brain:
                self.nest.save(self.brain)
                self._unsaved = 0

    def _need(self) -> None:
        if not self.brain:
            raise NoBaby("no baby yet, create one first")

    def _status(self) -> dict:
        return {"name": self.nest.name, "profile": self.nest.profile(), "state": self.brain.state()}

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
    "/api/babies": lambda n, b: n.list(),
    "/api/graph": lambda n, b: n.graph(),
    "/api/lessons": lambda n, b: {"lessons": catalog()},
    "/api/journal": lambda n, b: n.journal(),
    "/api/suggestions": lambda n, b: n.suggestions(),
    "/api/feeders": lambda n, b: n.feeders(),
}
ROUTES_POST = {
    "/api/babies": lambda n, b: n.create(str(b.get("name") or ""), str(b.get("about") or ""),
                                         str(b.get("color") or ""), str(b.get("level") or "newborn")),
    "/api/baby": lambda n, b: n.switch(str(b["name"])),
    "/api/baby/edit": lambda n, b: n.edit(b.get("about"), b.get("color")),
    "/api/baby/delete": lambda n, b: n.delete(str(b["name"])),
    "/api/observe": lambda n, b: n.observe(b),
    "/api/teach": lambda n, b: n.teach(b),
    "/api/correct": lambda n, b: n.correct(b),
    "/api/tick": lambda n, b: n.tick(float(b.get("seconds", 0))),
    "/api/show": lambda n, b: n.show(str(b["action"])),
    "/api/lesson": lambda n, b: n.lesson(b["name"], b.get("language", "en")),
    "/api/feed": lambda n, b: n.feed(b),
    "/api/reward": lambda n, b: n.reward(float(b.get("amount", 0))),
    "/api/sleep": lambda n, b: n.sleep(),
}


def make_handler(nursery: Nursery):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path.startswith("/api/"):
                return self._route(ROUTES_GET, path, {})
            self._static(path)

        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self._json({"error": "too large"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                return self._json({"error": "invalid JSON"}, HTTPStatus.BAD_REQUEST)
            self._route(ROUTES_POST, self.path.split("?", 1)[0], body)

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

        def _route(self, routes: dict, path: str, body: dict) -> None:
            handler = routes.get(path)
            if handler is None:
                return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            try:
                self._json(handler(nursery, body))
            except NoBaby as e:
                self._json({"error": str(e)}, HTTPStatus.CONFLICT)
            except (ValueError, KeyError, OSError) as e:
                self._json({"error": str(e).strip("'\"")}, HTTPStatus.BAD_REQUEST)

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


def serve(folder: Path, name: str | None = None, host: str = "127.0.0.1", port: int = 8008,
          level: str = "newborn") -> ThreadingHTTPServer:
    """Create the server. Call ``serve_forever`` on the result to run it.

    ``folder`` holds the babies. ``name`` opens (or creates) one baby, and
    without it the server opens the baby used last, or none at all.
    """
    nursery = Nursery(folder, name, level)
    server = ThreadingHTTPServer((host, port), make_handler(nursery))
    server.nursery = nursery
    return server


__all__ = ["Nursery", "serve"]
