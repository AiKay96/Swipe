from __future__ import annotations

import pickle
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

import redis

from src.runner.config import settings


def _loads(b: bytes) -> Any:
    return pickle.loads(b)


def _dumps(obj: Any) -> bytes:
    return pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)


@dataclass
class Cache:
    redis_url: str | None = None
    namespace: str = "swp"

    _r: redis.Redis = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        url: str = settings.redis_url

        self._r = redis.Redis.from_url(url)

        self._dumps: Callable[[Any], bytes] = _dumps
        self._loads: Callable[[bytes], Any] = _loads

    def get(self, key: str) -> Any | None:
        b = self._r.get(self._k(key))
        if b is None:
            return None
        try:
            return self._loads(b)  # type: ignore
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl_sec: int) -> None:
        payload = self._dumps(value)
        self._r.setex(self._k(key), ttl_sec, payload)

    def clear(self) -> None:
        pattern = f"{self.namespace}:*"
        batch: list[bytes] = []
        for k in self._scan_iter(pattern, count=1000):
            batch.append(k)
            if len(batch) >= 1000:
                self._r.delete(*batch)
                batch.clear()
        if batch:
            self._r.delete(*batch)

    def user(self, user_id: str) -> Cache:
        return _UserScopedCache(self, user_id)

    def _k(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    def _scan_iter(self, match: str, count: int = 1000) -> Iterable[bytes]:
        return self._r.scan_iter(match=match, count=count)


class _UserScopedCache(Cache):
    def __init__(self, parent: Cache, user_id: str) -> None:
        self._r = parent._r
        self._dumps = parent._dumps
        self._loads = parent._loads
        self.namespace = parent.namespace
        self._user_prefix = f"u:{user_id}:"

    def get(self, key: str) -> Any | None:
        return super().get(self._user_prefix + key)

    def set(self, key: str, value: Any, ttl_sec: int) -> None:
        super().set(self._user_prefix + key, value, ttl_sec)

    def clear(self) -> None:
        pattern = f"{self.namespace}:{self._user_prefix}*"
        batch: list[bytes] = []
        for k in self._scan_iter(pattern, count=1000):
            batch.append(k)
            if len(batch) >= 1000:
                self._r.delete(*batch)
                batch.clear()
        if batch:
            self._r.delete(*batch)
