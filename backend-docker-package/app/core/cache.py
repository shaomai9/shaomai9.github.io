from __future__ import annotations

import json
import time
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings


class MemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at < time.time():
            self._store.pop(key, None)
            return None
        return json.loads(value)

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = (time.time() + ttl_seconds, json.dumps(value, ensure_ascii=False))


class CacheClient:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._memory = MemoryCache()
        self._redis: Redis | None = None
        if self._settings.redis_url:
            try:
                self._redis = Redis.from_url(self._settings.redis_url, decode_responses=True)
                self._redis.ping()
            except RedisError:
                self._redis = None

    def get(self, key: str) -> Any | None:
        if self._redis:
            try:
                value = self._redis.get(key)
                return json.loads(value) if value else None
            except RedisError:
                return self._memory.get(key)
        return self._memory.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or self._settings.cache_ttl_seconds
        if self._redis:
            try:
                self._redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
                return
            except RedisError:
                pass
        self._memory.set(key, value, ttl)


cache_client = CacheClient()
