import logging
import os
import sqlite3
import threading
from pathlib import Path

log = logging.getLogger(__name__)

# longest compound worth trying; real lyrics rarely chain more
MAX_SPAN = 12


def is_han(ch: str) -> bool:
    return "一" <= ch <= "鿿" or "㐀" <= ch <= "䶿" or "豈" <= ch <= "﫿" or ch == "々"


class Dictionary:
    def __init__(self, path: str | None):
        self._db: sqlite3.Connection | None = None
        self._max: dict[str, int] = {}
        self._lock = threading.Lock()
        if not path or not os.path.exists(path):
            return
        db = None
        try:
            # read-only and queried per line: the file is never loaded whole
            db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True, check_same_thread=False)
            self._max = {key: int(value) for key, value in db.execute("SELECT key, value FROM meta")}
            # schema check once: an outdated file must not fail on every lookup
            db.execute("SELECT word, reading, common FROM words LIMIT 1").fetchall()
            db.execute("SELECT word, reading, kind, priority FROM stems LIMIT 1").fetchall()
            self._db = db
        except sqlite3.Error:
            log.warning("Romanization dictionary unreadable: %s", path, exc_info=True)
            if db is not None:
                db.close()

    @property
    def available(self) -> bool:
        return self._db is not None

    # (size, reading, common) of the longest word starting here
    def longest(self, lang: str, text: str, start: int) -> tuple[int, str, bool] | None:
        rows = self._lookup("SELECT word, reading, common FROM words", lang, self._max.get(f"max_len_{lang}", 0),
                            text, start)
        if not rows:
            return None
        word, reading, common = rows[0]
        return len(word), reading, bool(common)

    # every stem starting here, longest then most frequent first: (size, reading, kind)
    def stems(self, lang: str, text: str, start: int) -> list[tuple[int, str, str]]:
        rows = self._lookup("SELECT word, reading, kind, priority FROM stems", lang,
                            self._max.get(f"max_stem_{lang}", 0), text, start)
        rows.sort(key=lambda row: (len(row[0]), row[3]), reverse=True)
        return [(len(word), reading, kind) for word, reading, kind, _priority in rows]

    def _lookup(self, select: str, lang: str, longest: int, text: str, start: int) -> list[tuple]:
        if self._db is None:
            return []
        limit = min(longest, MAX_SPAN, len(text) - start)
        candidates = [text[start:start + size] for size in range(1, limit + 1)]
        if not candidates:
            return []
        marks = ",".join("?" * len(candidates))
        try:
            with self._lock:
                rows = self._db.execute(f"{select} WHERE lang = ? AND word IN ({marks})", (lang, *candidates)).fetchall()
        except sqlite3.Error:
            log.warning("Romanization lookup failed", exc_info=True)
            return []
        return sorted(rows, key=lambda row: len(row[0]), reverse=True)
