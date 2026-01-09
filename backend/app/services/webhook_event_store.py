"""In-memory store for recent webhook events (for testing/debugging)."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Store recent webhook events (last 100)
_recent_events: List[Dict[str, Any]] = []
_max_events = 100


def add_webhook_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Add a webhook event to the store."""
    global _recent_events
    
    # Extract useful information from payload for easier access
    extracted_info = {}
    if event_type == "instagram_webhook":
        entries = payload.get("entry", [])
        for entry in entries:
            messaging = entry.get("messaging", [])
            for msg_event in messaging:
                sender = msg_event.get("sender", {})
                recipient = msg_event.get("recipient", {})
                message_data = msg_event.get("message", {})
                
                if sender.get("id"):
                    extracted_info["sender_id"] = sender.get("id")
                if recipient.get("id"):
                    extracted_info["recipient_id"] = recipient.get("id")
                if message_data.get("text"):
                    extracted_info["message_text"] = message_data.get("text")
                if message_data.get("mid"):
                    extracted_info["message_id"] = message_data.get("mid")
                if message_data.get("is_echo"):
                    extracted_info["is_echo"] = message_data.get("is_echo")
                if message_data.get("is_self"):
                    extracted_info["is_self"] = message_data.get("is_self")
                break  # Only process first messaging event
            break  # Only process first entry
    
    event = {
        "id": f"webhook_{datetime.utcnow().timestamp()}",
        "type": event_type,
        "payload": payload,
        "extracted": extracted_info,  # Add extracted info for easier access
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    _recent_events.append(event)
    
    # Keep only last N events
    if len(_recent_events) > _max_events:
        _recent_events = _recent_events[-_max_events:]
    
    logger.info(
        f"Webhook event stored: {event_type} (total events: {len(_recent_events)})"
        + (f", sender_id={extracted_info.get('sender_id')}" if extracted_info.get("sender_id") else "")
    )


def get_recent_events(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent webhook events."""
    return _recent_events[-limit:]


def get_event_by_id(event_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific event by ID."""
    for event in _recent_events:
        if event["id"] == event_id:
            return event
    return None


def clear_events() -> int:
    """Clear all stored events. Returns number of cleared events."""
    global _recent_events
    count = len(_recent_events)
    _recent_events = []
    logger.info(f"Cleared {count} webhook events")
    return count

