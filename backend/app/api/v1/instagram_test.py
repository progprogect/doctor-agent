"""Instagram API testing endpoints."""

import json
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.dependencies import CommonDependencies

logger = logging.getLogger(__name__)

router = APIRouter()


class SendTestMessageRequest(BaseModel):
    """Request to send test message."""
    account_id: str
    recipient_id: str
    message_text: str
    use_self_messaging: bool = False


class TestMessageResponse(BaseModel):
    """Response from test message."""
    success: bool
    status_code: int
    response_data: dict[str, Any]
    error: str | None = None


@router.post("/instagram-test/send", response_model=TestMessageResponse)
async def send_test_message(
    request: SendTestMessageRequest,
    deps: CommonDependencies = Depends(),
):
    """Send test Instagram message with detailed logging."""
    INSTAGRAM_GRAPH_API_BASE = "https://graph.instagram.com/v21.0"
    FACEBOOK_GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
    ACCESS_TOKEN = "IGAAXjRiKjwKFBZAGFRU1RTcUdhU1UwYWhvTndCdWJNSEFGN1FEZA1M5N0Rhekp3MDE4NUpKanlwd1haSHpubmRFZAk8xbXF1UF9CRmRZATHRqWU44QURYVlcwZA2VhaVV1MngwYUdSeDRXVTdEcWhCNmhpLTR2S3NrRWxzQU5UcEQ5dwZDZD"
    
    logger.info("="*80)
    logger.info("🧪 ТЕСТ ОТПРАВКИ INSTAGRAM СООБЩЕНИЯ")
    logger.info("="*80)
    logger.info(f"Account ID: {request.account_id}")
    logger.info(f"Recipient ID: {request.recipient_id}")
    logger.info(f"Message: {request.message_text}")
    logger.info(f"Use Self Messaging: {request.use_self_messaging}")
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if request.use_self_messaging:
                # Self Messaging формат (без recipient)
                url = f"{INSTAGRAM_GRAPH_API_BASE}/{request.recipient_id}/messages"
                payload = {
                    "message": {"text": request.message_text}
                }
                logger.info(f"Self Messaging формат: POST {url}")
            else:
                # Стандартный формат (с recipient) - пробуем Instagram Graph API
                url = f"{INSTAGRAM_GRAPH_API_BASE}/{request.account_id}/messages"
                payload = {
                    "recipient": {"id": request.recipient_id},
                    "message": {"text": request.message_text},
                }
                logger.info(f"Стандартный формат (Instagram API): POST {url}")
            
            logger.info(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            response = await client.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            if response.status_code == 200:
                logger.info("✅ Сообщение успешно отправлено!")
                return TestMessageResponse(
                    success=True,
                    status_code=response.status_code,
                    response_data=response_data,
                )
            else:
                error_msg = response_data.get("error", {}).get("message", "Unknown error")
                error_code = response_data.get("error", {}).get("code")
                error_subcode = response_data.get("error", {}).get("error_subcode")
                
                logger.error(f"❌ Ошибка отправки: {error_code} (subcode: {error_subcode}) - {error_msg}")
                
                # Если ошибка "User not found" и это не Self Messaging, пробуем через Facebook Graph API
                # (согласно документации Messenger Platform может потребоваться Facebook Page ID)
                if error_code == 100 and not request.use_self_messaging:
                    logger.info("⚠️  Пробую через Facebook Graph API (Messenger Platform)...")
                    fb_url = f"{FACEBOOK_GRAPH_API_BASE}/{request.account_id}/messages"
                    fb_response = await client.post(fb_url, json=payload, headers=headers)
                    fb_response_data = fb_response.json()
                    
                    logger.info(f"Facebook API Status Code: {fb_response.status_code}")
                    logger.info(f"Facebook API Response: {json.dumps(fb_response_data, indent=2, ensure_ascii=False)}")
                    
                    if fb_response.status_code == 200:
                        logger.info("✅ Сообщение успешно отправлено через Facebook Graph API!")
                        return TestMessageResponse(
                            success=True,
                            status_code=fb_response.status_code,
                            response_data=fb_response_data,
                        )
                
                return TestMessageResponse(
                    success=False,
                    status_code=response.status_code,
                    response_data=response_data,
                    error=f"{error_code} (subcode: {error_subcode}): {error_msg}",
                )
    
    except Exception as e:
        logger.exception(f"Исключение при отправке сообщения: {e}")
        return TestMessageResponse(
            success=False,
            status_code=0,
            response_data={},
            error=str(e),
        )


@router.get("/instagram-test/account-info")
async def get_account_info(
    account_id: str,
    deps: CommonDependencies = Depends(),
):
    """Get Instagram account information."""
    INSTAGRAM_GRAPH_API_BASE = "https://graph.instagram.com/v21.0"
    ACCESS_TOKEN = "IGAAXjRiKjwKFBZAGFRU1RTcUdhU1UwYWhvTndCdWJNSEFGN1FEZA1M5N0Rhekp3MDE4NUpKanlwd1haSHpubmRFZAk8xbXF1UF9CRmRZATHRqWU44QURYVlcwZA2VhaVV1MngwYUdSeDRXVTdEcWhCNmhpLTR2S3NrRWxzQU5UcEQ5dwZDZD"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{INSTAGRAM_GRAPH_API_BASE}/{account_id}?fields=id,username,account_type"
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json()
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

