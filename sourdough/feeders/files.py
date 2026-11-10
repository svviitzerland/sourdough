"""Feeding from files: a list of answers, or a folder of named pictures."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

PICTURES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def from_pairs(path: str | Path):
    """Read prompts and answers from a JSON or CSV file.

    JSON: a list of objects with ``prompt`` and ``answer`` (``say`` and
    ``reply``, or ``question`` and ``answer``, work too). CSV: two columns,
    prompt then answer, with or without a header row.
    """
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as f:
            rows = [r for r in csv.reader(f) if len(r) >= 2]
        if rows and rows[0][0].strip().lower() in {"prompt", "question", "say", "when"}:
            rows = rows[1:]
        pairs = [{"prompt": r[0], "answer": r[1]} for r in rows]
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        pairs = data.get("pairs", []) if isinstance(data, dict) else data
    for p in pairs:
        prompt = p.get("prompt") or p.get("say") or p.get("question") or ""
        answer = p.get("answer") or p.get("reply") or ""
        if str(prompt).strip() and str(answer).strip():
            yield {"kind": "reply", "prompt": str(prompt).strip(), "answer": str(answer).strip()}


def label_of(filename: str) -> str:
    """The word a picture is named after: "red-apple_2.jpg" becomes "red apple"."""
    stem = Path(filename).stem
    words = re.sub(r"[\d_\-.]+", " ", stem).strip().lower()
    return re.sub(r"\s+", " ", words)


def from_folder(path: str | Path):
    """Every picture in a folder, named after what it shows.

    "cat.jpg", "cat-2.jpg" and "cat_sleeping.png" all teach "cat" (and
    "sleeping"). Subfolders count too: "fruit/apple.png" teaches "apple".
    """
    for picture in sorted(Path(path).rglob("*")):
        if picture.is_file() and picture.suffix.lower() in PICTURES and not picture.name.startswith("."):
            label = label_of(picture.name)
            if label:
                yield {"kind": "name", "image": str(picture), "answer": label}
