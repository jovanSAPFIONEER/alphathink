from __future__ import annotations

from collections import deque
from typing import Deque, Tuple

from .agent import Memory


class RingMemory(Memory):
    def __init__(self, maxlen: int = 64) -> None:
        self._q: Deque[Tuple[str, str, bool]] = deque(maxlen=maxlen)

    def remember(self, q: str, a: str, ok: bool) -> None:
        self._q.append((q, a, ok))

    def stats(self) -> Tuple[int, int]:
        ok = sum(1 for _, _, s in self._q if s)
        return ok, len(self._q)
