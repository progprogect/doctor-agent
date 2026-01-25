"""Telegram webhook API endpoints."""

import json
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies import CommonDependencies
from app.services.channel_binding_service import ChannelBindingService
from app.services.telegram_service import TelegramService
from app.storage.secrets import get_secrets_manager

logger = logging.getLogger(__name__)

router = APIRouter()


def get_telegram_service(
    deps: CommonDependencies = Depends(),
) -> TelegramService:
    """Get Telegram service instance."""
    from app.config import get_settings

    settings = get_settings()
    secrets_manager = get_secrets_manager()
    binding_service = ChannelBindingService(deps.dynamodb, secrets_manager)
    return TelegramService(binding_service, deps.dynamodb, settings)


@router.post("/telegram/webhook/{binding_id}")
async def handle_webhook(
    binding_id: str,
    request: Request,
    telegram_service: TelegramService = Depends(get_telegram_service),
):
    """Handle Telegram webhook events (POST request for incoming messages)."""
    # Validate UUID format
    try:
        UUID(binding_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid binding ID format",
        )

    # Get request body
    try:
        body = await request.body()
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Telegram webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Log webhook event for debugging
    logger.info("=" * 80)
    logger.info("📨 TELEGRAM WEBHOOK EVENT RECEIVED")
    logger.info("=" * 80)
    logger.info(f"Binding ID: {binding_id}")
    logger.info(f"Full payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    # Store event for testing/debugging (optional)
    try:
        from app.services.webhook_event_store import add_webhook_event

        add_webhook_event("telegram_webhook", payload)
    except Exception as e:
        logger.debug(f"Failed to store webhook event: {e}")

    # Handle webhook event
    try:
        await telegram_service.handle_webhook_event(payload, binding_id)
    except Exception as e:
        logger.error(f"Error handling Telegram webhook event: {e}", exc_info=True)
        # Return 200 to prevent Telegram from retrying
        # Log the error for investigation
        return {"status": "error", "message": "Event processing failed"}

    return {"status": "ok"}
