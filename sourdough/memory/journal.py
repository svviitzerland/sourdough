"""Journal: the baby's life story, one line per moment.

The brain file holds what the baby *knows*. The journal holds what *happened*:
what it heard, what it did, how it felt, and how people reacted. It is an
append only JSON Lines file, so it is cheap to write, easy to read with any
tool, and never rewritten. Pictures are not stored, only what was understood.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class Journal:
    def __init__(self, path: Path):
        self.path = path

    def write(self, event: str, **details) -> None:
        """Append one moment, stamped with the current time."""
        entry = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "event": event, **details}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def recent(self, limit: int = 50) -> list[dict]:
        """The last ``limit`` moments, oldest first."""
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-limit:]
        return [json.loads(line) for line in lines if line.strip()]
