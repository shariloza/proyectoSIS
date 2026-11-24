"""Rate limiting en memoria con ventana deslizante (suficiente para una sola instancia)."""

import time
from collections import defaultdict, deque
from threading import Lock

from app.shared.errors import RateLimitedError


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self._window:
                hits.popleft()
            if len(hits) >= self._max:
                raise RateLimitedError("Demasiadas solicitudes. Intenta de nuevo en un momento.")
            hits.append(now)
