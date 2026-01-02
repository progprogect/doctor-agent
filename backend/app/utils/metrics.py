"""Metrics collection for monitoring."""

import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable

from app.storage.dynamodb import DynamoDBClient


class MetricsCollector:
    """Collects application metrics."""

    def __init__(self, dynamodb: DynamoDBClient):
        """Initialize metrics collector."""
        self.dynamodb = dynamodb
        self._metrics: dict[str, Any] = {}

    def increment_counter(self, name: str, value: int = 1, tags: dict[str, str] = None):
        """Increment a counter metric."""
        key = f"counter:{name}"
        if tags:
            key += ":" + ":".join(f"{k}={v}" for k, v in sorted(tags.items()))
        self._metrics[key] = self._metrics.get(key, 0) + value

    def record_timing(self, name: str, duration: float, tags: dict[str, str] = None):
        """Record a timing metric."""
        key = f"timing:{name}"
        if tags:
            key += ":" + ":".join(f"{k}={v}" for k, v in sorted(tags.items()))
        if key not in self._metrics:
            self._metrics[key] = []
        self._metrics[key].append(duration)

    def set_gauge(self, name: str, value: float, tags: dict[str, str] = None):
        """Set a gauge metric."""
        key = f"gauge:{name}"
        if tags:
            key += ":" + ":".join(f"{k}={v}" for k, v in sorted(tags.items()))
        self._metrics[key] = value

    def get_metrics(self) -> dict[str, Any]:
        """Get all collected metrics."""
        return self._metrics.copy()

    def reset(self):
        """Reset all metrics."""
        self._metrics.clear()


def track_metrics(func: Callable) -> Callable:
    """Decorator to track function execution metrics."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            # Metrics would be collected here in production
            return result
        except Exception as e:
            duration = time.time() - start_time
            # Track error metrics
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            return result
        except Exception as e:
            duration = time.time() - start_time
            raise

    if hasattr(func, "__call__") and hasattr(func, "__code__"):
        # Check if function is async
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
    return sync_wrapper






