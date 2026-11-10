"""Feeding from another AI: a teacher that writes lessons for the baby.

Any service with an OpenAI compatible chat API works: OpenAI, OpenRouter,
Ollama, LM Studio, Groq, Together and others. The teacher is asked for short,
simple prompts and answers about a topic, the way a parent would quiz a
toddler, and those become ordinary teaching moments.

The baby never sees the other AI's weights or text dumps. It only hears the
prompts and answers, one moment at a time, like any lesson.

API keys come from the environment (``OPENAI_API_KEY``, ``OPENROUTER_API_KEY``)
or are passed in. They are never written to disk by Sourdough.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

PROVIDERS = {
    "openai": {"url": "https://api.openai.com/v1", "key": "OPENAI_API_KEY", "model": "gpt-4o-mini"},
    "openrouter": {"url": "https://openrouter.ai/api/v1", "key": "OPENROUTER_API_KEY",
                   "model": "openai/gpt-4o-mini"},
    "ollama": {"url": "http://localhost:11434/v1", "key": "", "model": "llama3.2"},
}

LANGUAGES = {"en": "English", "id": "Indonesian"}

INSTRUCTIONS = """You are teaching a baby AI that only understands very short, concrete
language. Write {count} question and answer pairs about: {topic}.
Write them in {language}. Each question is a short, natural thing a parent
would ask, at most six words. Each answer is one or two simple words, never a
sentence, never a yes or no. Use everyday words a small child knows.
Reply with JSON only, in this exact shape:
{{"pairs": [{{"prompt": "...", "answer": "..."}}]}}"""


class Teacher:
    """Another AI, reached through an OpenAI compatible chat completions API."""

    def __init__(self, provider: str = "openai", model: str | None = None,
                 api_key: str | None = None, base_url: str | None = None, timeout: float = 90):
        known = PROVIDERS.get(provider, {})
        self.provider = provider
        self.url = (base_url or known.get("url") or "").rstrip("/")
        if not self.url:
            raise ValueError(f"unknown provider {provider}, pass base_url for a custom one")
        self.model = model or known.get("model")
        if not self.model:
            raise ValueError("choose a model")
        env = known.get("key")
        self.api_key = api_key or (os.environ.get(env) if env else None)
        if env and not self.api_key:
            raise ValueError(f"{provider} needs an API key, set {env} or pass one")
        self.timeout = timeout

    def lesson(self, topic: str, count: int = 12, language: str = "en"):
        """Ask the teacher for prompt and answer pairs about a topic."""
        count = max(1, min(int(count), 40))
        prompt = INSTRUCTIONS.format(count=count, topic=topic.strip() or "everyday things",
                                     language=LANGUAGES.get(language, "English"))
        text = self._chat(prompt)
        for pair in _parse(text)[:count]:
            yield {"kind": "reply", "prompt": pair["prompt"], "answer": pair["answer"]}

    def _chat(self, prompt: str) -> str:
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
        }
        headers = {"Content-Type": "application/json", "User-Agent": "sourdough"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.provider == "openrouter":
            headers["X-Title"] = "Sourdough"
        request = urllib.request.Request(f"{self.url}/chat/completions", data=json.dumps(body).encode(),
                                         headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="ignore")[:200]
            raise ValueError(f"{self.provider} answered {e.code}: {detail}") from None
        except urllib.error.URLError as e:
            raise ValueError(f"could not reach {self.provider}: {e.reason}") from None
        return data["choices"][0]["message"]["content"]


def _parse(text: str) -> list[dict]:
    """Pull the pairs out of the reply, tolerating code fences and chatter."""
    match = re.search(r"\{.*\}|\[.*\]", text, re.S)
    if not match:
        raise ValueError("the teacher did not answer with JSON")
    data = json.loads(match.group(0))
    pairs = data.get("pairs", []) if isinstance(data, dict) else data
    clean = []
    for p in pairs:
        prompt = str(p.get("prompt", "")).strip().strip("?").strip()
        answer = str(p.get("answer", "")).strip().strip(".!").lower()
        if prompt and answer and len(answer.split()) <= 3:
            clean.append({"prompt": prompt, "answer": answer})
    return clean
