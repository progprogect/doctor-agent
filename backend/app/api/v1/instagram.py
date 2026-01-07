"""Instagram webhook API endpoints."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from app.config import get_settings
from app.dependencies import CommonDependencies
from app.services.channel_binding_service import ChannelBindingService
from app.services.instagram_service import InstagramService
from app.storage.secrets import get_secrets_manager

logger = logging.getLogger(__name__)

router = APIRouter()


def get_instagram_service(
    deps: CommonDependencies = Depends(),
) -> InstagramService:
    """Get Instagram service instance."""
    settings = get_settings()
    secrets_manager = get_secrets_manager()
    binding_service = ChannelBindingService(deps.dynamodb, secrets_manager)
    return InstagramService(binding_service, deps.dynamodb, settings)


@router.get("/instagram/webhook")
async def verify_webhook(
    mode: str = Query(..., alias="hub.mode", description="Webhook verification mode"),
    token: str = Query(..., alias="hub.verify_token", description="Verification token"),
    challenge: str = Query(..., alias="hub.challenge", description="Challenge string"),
    instagram_service: InstagramService = Depends(get_instagram_service),
):
    """
    Verify Instagram webhook (GET request for webhook setup).
    
    Meta/Facebook sends GET request with:
    - hub.mode=subscribe
    - hub.verify_token=<your_token>
    - hub.challenge=<random_string>
    
    Server MUST return HTTP 200 with challenge string as response body.
    """
    logger.info(f"Webhook verification request: mode={mode}, token={'*' * len(token) if token else None}")
    
    result = instagram_service.verify_webhook(mode=mode, token=token, challenge=challenge)
    if result is None:
        logger.warning(f"Webhook verification failed: mode={mode}, token mismatch")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook verification failed",
        )
    
    logger.info(f"Webhook verification successful, returning challenge: {challenge}")
    # IMPORTANT: Return challenge as plain string (not JSON)
    # Meta requires HTTP 200 with challenge string as response body
    from fastapi.responses import Response
    return Response(content=result, media_type="text/plain", status_code=200)


@router.post("/instagram/webhook")
async def handle_webhook(
    request: Request,
    instagram_service: InstagramService = Depends(get_instagram_service),
    x_hub_signature_256: str | None = Header(
        None, alias="X-Hub-Signature-256", description="Webhook signature"
    ),
):
    """Handle Instagram webhook events (POST request for incoming messages)."""
    settings = get_settings()

    # Get request body
    body = await request.body()

    # Verify webhook signature if app secret is configured
    if settings.instagram_app_secret and x_hub_signature_256:
        if not instagram_service.verify_webhook_signature(body, x_hub_signature_256):
            logger.warning("Instagram webhook signature verification failed")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature",
            )

    # Parse JSON payload
    try:
        import json

        payload = json.loads(body.decode("utf-8"))
        
        # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ для отладки - выводим всю структуру события
        logger.info("="*80)
        logger.info("📨 INSTAGRAM WEBHOOK EVENT RECEIVED")
        logger.info("="*80)
        logger.info(f"Full payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        # Извлекаем и логируем sender.id если есть
        entries = payload.get("entry", [])
        for entry in entries:
            messaging = entry.get("messaging", [])
            for event in messaging:
                sender = event.get("sender", {})
                recipient = event.get("recipient", {})
                message_data = event.get("message", {})
                
                sender_id = sender.get("id")
                recipient_id = recipient.get("id")
                message_text = message_data.get("text", "")
                message_id = message_data.get("mid")
                is_self = message_data.get("is_self", False)
                is_echo = message_data.get("is_echo", False)
                
                logger.info("-"*80)
                logger.info(f"🔹 Sender ID (это recipient_id для отправки): {sender_id}")
                logger.info(f"🔹 Recipient ID (наш аккаунт): {recipient_id}")
                logger.info(f"🔹 Message ID: {message_id}")
                logger.info(f"🔹 Message Text: {message_text}")
                logger.info(f"🔹 Is Self: {is_self}")
                logger.info(f"🔹 Is Echo: {is_echo}")
                logger.info("-"*80)
                
                if is_self and is_echo:
                    logger.info("="*80)
                    logger.info("🎯 SELF MESSAGING WEBHOOK ОБНАРУЖЕН!")
                    logger.info("="*80)
                    logger.info(f"✅ Instagram-scoped ID для Self Messaging: {recipient_id}")
                    logger.info(f"   Используйте этот ID для отправки самому себе:")
                    logger.info(f"   POST /{recipient_id}/messages")
                    logger.info(f"   Body: {{'message': {{'text': '...'}}}}")
                    logger.info(f"   (БЕЗ поля recipient!)")
                    logger.info("="*80)
                
                if sender_id:
                    logger.info(f"✅ НАЙДЕН RECIPIENT_ID: {sender_id}")
                    logger.info(f"   Используйте этот ID для отправки сообщения:")
                    logger.info(f"   python3 test_instagram_send.py {sender_id}")
        
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Handle webhook event asynchronously
    # Note: In production, you might want to use a background task queue
    try:
        await instagram_service.handle_webhook_event(payload)
    except Exception as e:
        logger.error(f"Error handling webhook event: {e}", exc_info=True)
        # Return 200 to prevent Instagram from retrying
        # Log the error for investigation
        return {"status": "error", "message": "Event processing failed"}

    return {"status": "ok"}

