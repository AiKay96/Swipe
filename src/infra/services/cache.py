from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass
class Cache:
    _store: dict[str, tuple[float, object]] = field(
        default_factory=dict, init=False, repr=False
    )

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if time() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl_sec: int) -> None:
        self._store[key] = (time() + ttl_sec, value)

    def clear(self) -> None:
        self._store.clear()
