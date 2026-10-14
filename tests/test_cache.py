from __future__ import annotations

import time

from app.core.cache import TTLCache


def test_ttl_cache_hit_and_expire():
    cache = TTLCache[str](ttl_seconds=1)
    cache.set("q1", "answer")

    assert cache.get("q1") == "answer"

    time.sleep(1.1)
    assert cache.get("q1") is None
