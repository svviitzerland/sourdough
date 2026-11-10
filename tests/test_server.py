"""The web API, end to end over real HTTP."""

import json
import threading
import urllib.error
import urllib.request

import pytest

from sourdough.interface import serve

RED_PIXEL = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)


def start(folder, name=None):
    server = serve(folder, name=name, port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


@pytest.fixture
def url(tmp_path):
    server, address = start(tmp_path, "test")
    yield address
    server.shutdown()


def call(url, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())


def test_page_is_served(url):
    with urllib.request.urlopen(url) as res:
        assert b"Sourdough" in res.read()


def test_without_babies_it_asks_for_one_first(tmp_path):
    server, address = start(tmp_path)
    try:
        assert call(address, "/api/state")["name"] is None
        with pytest.raises(urllib.error.HTTPError) as err:
            call(address, "/api/observe", {"text": "hello"})
        assert err.value.code == 409
        made = call(address, "/api/babies", {"name": "kiki", "about": "a curious robot", "color": "mint"})
        assert made["name"] == "kiki" and made["profile"]["about"] == "a curious robot"
        assert made["state"]["vocabulary"] == []
    finally:
        server.shutdown()


def test_the_last_baby_opens_again_next_time(tmp_path):
    server, address = start(tmp_path)
    call(address, "/api/babies", {"name": "pip"})
    server.shutdown()
    server, address = start(tmp_path)
    try:
        assert call(address, "/api/state")["name"] == "pip"
    finally:
        server.shutdown()


def test_teach_and_recall_over_http(url):
    call(url, "/api/observe", {"text": "red", "image": RED_PIXEL})
    data = call(url, "/api/observe", {"image": RED_PIXEL})
    assert data["response"]["words"] == ["red"]
    assert data["state"]["vocabulary"][0]["word"] == "red"


def test_teaching_forms(url):
    call(url, "/api/teach", {"kind": "name", "image": RED_PIXEL, "answer": "merah"})
    assert call(url, "/api/observe", {"image": RED_PIXEL})["response"]["words"] == ["merah"]
    call(url, "/api/teach", {"kind": "reply", "prompt": "ping", "answer": "pong"})
    assert call(url, "/api/observe", {"text": "ping"})["response"]["words"] == ["pong"]
    call(url, "/api/teach", {"kind": "action", "prompt": "look around", "action": "explore"})
    assert call(url, "/api/observe", {"text": "look around"})["response"]["action"] == "explore"


def test_correcting_a_wrong_answer(url):
    call(url, "/api/teach", {"kind": "reply", "prompt": "hello", "answer": "bye"})
    assert call(url, "/api/observe", {"text": "hello"})["response"]["words"] == ["bye"]
    call(url, "/api/correct", {"prompt": "hello", "answer": "hi"})
    call(url, "/api/correct", {"prompt": "hello", "answer": "hi"})
    assert call(url, "/api/observe", {"text": "hello"})["response"]["words"] == ["hi"]


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
    assert call(url, "/api/show", {"action": "explore"})["response"]["action"] == "explore"
    assert "response" in call(url, "/api/tick", {"seconds": 5})


def test_exploring_brings_back_something_from_its_world(url):
    call(url, "/api/observe", {"text": "explore"})
    data = call(url, "/api/show", {"action": "explore"})
    assert data["outcome"]["file"]
    assert data["outcome"]["response"]["mode"] != "silent"


def test_characters_can_be_created_switched_edited_and_deleted(url):
    listing = call(url, "/api/babies")
    assert [lvl["name"] for lvl in listing["levels"]] == ["newborn", "toddler", "preschooler", "kid"]
    data = call(url, "/api/babies", {"name": "Kiki", "level": "kid", "about": "a robot"})
    assert data["name"] == "Kiki" and len(data["state"]["vocabulary"]) > 60
    assert call(url, "/api/observe", {"text": "what is your name"})["response"]["words"] == ["kiki"]
    assert call(url, "/api/baby/edit", {"about": "a kind robot", "color": "sky"})["profile"]["color"] == "sky"
    assert call(url, "/api/baby", {"name": "test"})["name"] == "test"
    names = {b["name"] for b in call(url, "/api/babies")["babies"]}
    assert names == {"test", "Kiki"}
    left = call(url, "/api/baby/delete", {"name": "Kiki"})
    assert [b["name"] for b in left["babies"]] == ["test"]


def test_names_must_be_new_and_simple(url):
    for name in ("test", "bad name!"):
        with pytest.raises(urllib.error.HTTPError) as err:
            call(url, "/api/babies", {"name": name})
        assert err.value.code == 400


def test_suggestions_fit_what_it_knows(url):
    assert call(url, "/api/suggestions")["prompts"] == []
    call(url, "/api/babies", {"name": "smart", "level": "kid"})
    prompts = call(url, "/api/suggestions")["prompts"]
    assert 0 < len(prompts) <= 4


def test_feeding_over_http(url):
    providers = {p["name"]: p for p in call(url, "/api/feeders")["providers"]}
    assert set(providers) >= {"openai", "openrouter", "ollama"} and providers["ollama"]["ready"]
    data = call(url, "/api/feed", {"source": "pairs", "pairs": [{"prompt": "what do bees make", "answer": "honey"}]})
    assert data["report"]["correct"] == 1
    data = call(url, "/api/feed", {"source": "pictures", "pictures": [{"image": RED_PIXEL, "file": "red.png"}]})
    assert data["report"]["taught"] == 1
