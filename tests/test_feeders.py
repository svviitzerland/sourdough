"""Feeding from outside: files, folders of pictures, and another AI."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np
import pytest

from sourdough import Brain
from sourdough.feeders import Teacher, feed, from_folder, from_pairs, label_of
from sourdough.foundation.lessons import draw


def test_labels_come_from_file_names():
    assert label_of("red-apple_2.jpg") == "red apple"
    assert label_of("Cat.PNG") == "cat"


def test_pairs_from_json_and_csv(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps([{"prompt": "what do bees make", "answer": "honey"}]))
    (tmp_path / "b.csv").write_text("prompt,answer\nwhere do fish live,water\n")
    assert list(from_pairs(tmp_path / "a.json"))[0]["answer"] == "honey"
    assert list(from_pairs(tmp_path / "b.csv")) == [
        {"kind": "reply", "prompt": "where do fish live", "answer": "water"}]


def test_feeding_pairs_teaches_answers(tmp_path):
    (tmp_path / "facts.json").write_text(json.dumps([
        {"prompt": "what do bees make", "answer": "honey"},
        {"prompt": "where do fish live", "answer": "water"},
    ]))
    baby = Brain(seed=0)
    report = feed(baby, from_pairs(tmp_path / "facts.json"))
    assert report == report | {"taught": 2, "correct": 2}
    assert baby.observe(text="what do bees make").words == ["honey"]


def test_feeding_a_folder_of_pictures(tmp_path):
    rng = np.random.default_rng(0)
    draw("star", (40, 90, 220), rng).save(tmp_path / "star.png")
    draw("heart", (220, 40, 40), rng).save(tmp_path / "heart-1.png")
    baby = Brain(seed=0)
    report = feed(baby, from_folder(tmp_path))
    assert report["taught"] == 2 and report["correct"] == 2


class FakeAI(BaseHTTPRequestHandler):
    """Answers like an OpenAI compatible API, with a lesson in a code fence."""

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeAI.seen = body | {"auth": self.headers.get("Authorization")}
        lesson = {"pairs": [{"prompt": "what color is a banana?", "answer": "Yellow."},
                            {"prompt": "too long", "answer": "this is a whole sentence"}]}
        reply = {"choices": [{"message": {"content": "```json\n" + json.dumps(lesson) + "\n```"}}]}
        data = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def fake_ai():
    server = HTTPServer(("127.0.0.1", 0), FakeAI)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_an_ai_teacher_writes_a_lesson(fake_ai):
    teacher = Teacher("custom", model="tiny", api_key="secret", base_url=fake_ai)
    moments = list(teacher.lesson("fruit", count=5))
    assert moments == [{"kind": "reply", "prompt": "what color is a banana", "answer": "yellow"}]
    assert FakeAI.seen["model"] == "tiny" and FakeAI.seen["auth"] == "Bearer secret"
    baby = Brain(seed=0)
    feed(baby, moments)
    assert baby.observe(text="what color is a banana").words == ["yellow"]


def test_a_known_provider_needs_its_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        Teacher("openrouter")
