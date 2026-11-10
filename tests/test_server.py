"""The web API, end to end over real HTTP."""

import json
import threading
import urllib.request

import pytest

from sourdough.interface import serve
from sourdough.storage import Nest

RED_PIXEL = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)


@pytest.fixture
def url(tmp_path):
    server = serve(Nest("test", tmp_path), port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def call(url, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())


def test_page_is_served(url):
    with urllib.request.urlopen(url) as res:
        assert b"Sourdough" in res.read()


def test_teach_and_recall_over_http(url):
    call(url, "/api/observe", {"text": "red", "image": RED_PIXEL})
    data = call(url, "/api/observe", {"image": RED_PIXEL})
    assert data["response"]["words"] == ["red"]
    assert data["state"]["vocabulary"][0]["word"] == "red"


def test_reward_and_sleep(url):
    call(url, "/api/observe", {"text": "hi"})
    assert "state" in call(url, "/api/reward", {"amount": 1})
    assert "replayed" in call(url, "/api/sleep", {})["report"]


def test_lessons_over_http(url):
    names = [lesson["name"] for lesson in call(url, "/api/lessons")["lessons"]]
    assert names[:3] == ["colors", "shapes", "routines"] and len(names) == 9
    data = call(url, "/api/lesson", {"name": "colors", "language": "id"})
    assert data["lesson"]["total"] == 10
    assert data["state"]["vocabulary"]


def test_journal_and_graph(url):
    call(url, "/api/observe", {"text": "red", "image": RED_PIXEL})
    call(url, "/api/observe", {"image": RED_PIXEL})
    moments = call(url, "/api/journal")["moments"]
    assert [m["event"] for m in moments] == ["born", "moment", "moment"]
    graph = call(url, "/api/graph")
    assert {n["kind"] for n in graph["nodes"]} >= {"word", "color", "shape"}


def test_show_and_tick(url):
    call(url, "/api/observe", {"text": "jump"})
    assert call(url, "/api/show", {"action": "jump"})["response"]["action"] == "jump"
    assert call(url, "/api/observe", {"text": "jump"})["response"]["action"] == "jump"
    assert "response" in call(url, "/api/tick", {"seconds": 5})


def test_exploring_brings_back_something_from_its_world(url):
    call(url, "/api/observe", {"text": "explore"})
    data = call(url, "/api/show", {"action": "explore"})
    assert data["outcome"]["file"]
    assert data["outcome"]["response"]["mode"] != "silent"


def test_babies_can_be_created_at_a_level_and_switched(url):
    listing = call(url, "/api/babies")
    assert [lvl["name"] for lvl in listing["levels"]] == ["newborn", "toddler", "preschooler", "kid"]
    data = call(url, "/api/baby", {"name": "kidd", "level": "kid"})
    assert data["name"] == "kidd" and len(data["state"]["vocabulary"]) > 60
    assert call(url, "/api/observe", {"text": "what does a cat say"})["response"]["words"] == ["meow"]
    back = call(url, "/api/baby", {"name": "test"})
    assert back["name"] == "test"
    assert {b["name"] for b in call(url, "/api/babies")["babies"]} == {"test", "kidd"}


def test_suggestions_fit_what_it_knows(url):
    assert call(url, "/api/suggestions")["prompts"] == []
    call(url, "/api/baby", {"name": "kid", "level": "kid"})
    prompts = call(url, "/api/suggestions")["prompts"]
    assert 0 < len(prompts) <= 4
