"""Caching utilities."""

import inspect
from functools import wraps
from typing import Any, Callable, Optional

from app.storage.redis import RedisClient, get_redis_client


class CacheService:
    """Service for caching data."""

    def __init__(self, redis: RedisClient):
        """Initialize cache service."""
        self.redis = redis

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        return await self.redis.get(key)

    async def set(
        self, key: str, value: str, ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        return await self.redis.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        result = await self.redis.delete(key)
        return result > 0

    async def get_or_set(
        self,
        key: str,
        fetch_func: Callable[[], Any],
        ttl: Optional[int] = 300,
    ) -> Any:
        """Get value from cache or fetch and cache it."""
        cached = await self.get(key)
        if cached:
            return cached

        # Call fetch function (handle both sync and async)
        if inspect.iscoroutinefunction(fetch_func):
            value = await fetch_func()
        elif callable(fetch_func):
            value = fetch_func()
        else:
            value = fetch_func

        if value:
            await self.set(key, str(value), ttl)
        return value


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator to cache function results."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = CacheService(get_redis_client())
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            cached_value = await cache.get(cache_key)
            if cached_value:
                return cached_value

            result = await func(*args, **kwargs)
            if result:
                await cache.set(cache_key, str(result), ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, caching would need to be handled differently
            return func(*args, **kwargs)

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator

