from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class CacheItem(Generic[T]):
    value: T
    expires_at: float


class TTLCache(Generic[T]):
    """Simple thread-safe in-memory TTL cache."""

    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._data: dict[str, CacheItem[T]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> T | None:
        now = time.time()
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            if item.expires_at < now:
                self._data.pop(key, None)
                return None
            return item.value

    def set(self, key: str, value: T) -> None:
        with self._lock:
            self._data[key] = CacheItem(
                value=value,
                expires_at=time.time() + self.ttl_seconds,
            )

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def purge(self) -> None:
        now = time.time()
        with self._lock:
            expired = [key for key, item in self._data.items() if item.expires_at < now]
            for key in expired:
                self._data.pop(key, None)
