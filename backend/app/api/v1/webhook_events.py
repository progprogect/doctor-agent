"""API endpoints for webhook events (for testing page)."""

import logging
from typing import List

from fastapi import APIRouter, Query

from app.services.webhook_event_store import get_recent_events, clear_events

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/webhook-events/recent")
async def get_recent_webhook_events(
    limit: int = Query(default=50, ge=1, le=100, description="Number of events to return"),
) -> dict:
    """Get recent webhook events."""
    events = get_recent_events(limit=limit)
    return {
        "total": len(events),
        "events": events,
    }


@router.post("/webhook-events/clear")
async def clear_webhook_events() -> dict:
    """Clear all stored webhook events."""
    count = clear_events()
    return {
        "status": "ok",
        "cleared_count": count,
    }

