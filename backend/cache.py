"""Tiny in-process TTL cache. Deliberately simple — no Redis/Celery for a hobby deploy."""
from __future__ import annotations
import time
import threading

_store: dict[str, tuple[float, object]] = {}
_lock = threading.Lock()


def get(key: str):
    with _lock:
        item = _store.get(key)
        if not item:
            return None
        expires_at, value = item
        if time.time() > expires_at:
            _store.pop(key, None)
            return None
        return value


def set(key: str, value, ttl: int):
    with _lock:
        _store[key] = (time.time() + ttl, value)


def clear():
    with _lock:
        _store.clear()
