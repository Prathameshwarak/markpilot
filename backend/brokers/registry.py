"""Shared singletons so system routes and the data-provider factory reflect the same
Kotak session state.
"""
from __future__ import annotations
from brokers.kotak_neo import KotakNeoAdapter

_adapter: KotakNeoAdapter | None = None


def get_kotak_adapter() -> KotakNeoAdapter:
    global _adapter
    if _adapter is None:
        _adapter = KotakNeoAdapter()
    return _adapter
