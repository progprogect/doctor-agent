#!/usr/bin/env python3
"""
Тест отправки Instagram сообщения через серверный API.
Использует данные с сервера для реального теста.
"""

import asyncio
import json
import sys

import httpx

# Данные для теста
ALB_DNS = "doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com"
ACCESS_TOKEN = "IGAAXjRiKjwKFBZAGFRU1RTcUdhU1UwYWhvTndCdWJNSEFGN1FEZA1M5N0Rhekp3MDE4NUpKanlwd1haSHpubmRFZAk8xbXF1UF9CRmRZATHRqWU44QURYVlcwZA2VhaVV1MngwYUdSeDRXVTdEcWhCNmhpLTR2S3NrRWxzQU5UcEQ5dwZDZD"
ACCOUNT_ID = "25638311079121978"  # Instagram Business Account ID
INSTAGRAM_GRAPH_API_BASE = "https://graph.instagram.com/v21.0"


async def test_send_via_server_api(recipient_id: str, message_text: str = "Тестовое сообщение от Doctor Agent через серверный API"):
    """Тест отправки через серверный API endpoint."""
    print("\n" + "="*80)
    print("🧪 ТЕСТ ОТПРАВКИ ЧЕРЕЗ СЕРВЕРНЫЙ API")
    print("="*80)
    print(f"Recipient ID: {recipient_id}")
    print(f"Account ID: {ACCOUNT_ID}")
    print(f"Message: {message_text}")
    print("="*80)
    
    url = f"http://{ALB_DNS}/api/v1/instagram-test/send"
    payload = {
        "account_id": ACCOUNT_ID,
        "recipient_id": recipient_id,
        "message_text": message_text,
        "use_self_messaging": False,
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"\n📤 Отправка запроса на: {url}")
        print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        try:
            response = await client.post(url, json=payload)
            result = response.json()
            
            print(f"\n📥 Ответ сервера:")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get("success"):
                print("\n✅ Сообщение успешно отправлено через серверный API!")
                return True
            else:
                print(f"\n❌ Ошибка: {result.get('error', 'Unknown error')}")
                
                # Если стандартный формат не сработал, пробуем Self Messaging
                if result.get("status_code") == 400 and result.get("response_data", {}).get("error", {}).get("code") == 100:
                    print("\n🔄 Пробую Self Messaging формат...")
                    payload["use_self_messaging"] = True
                    response2 = await client.post(url, json=payload)
                    result2 = response2.json()
                    
                    print(f"Status Code: {response2.status_code}")
                    print(f"Response: {json.dumps(result2, indent=2, ensure_ascii=False)}")
                    
                    if result2.get("success"):
                        print("\n✅ Сообщение успешно отправлено через Self Messaging!")
                        return True
                
                return False
        
        except Exception as e:
            print(f"\n❌ Исключение: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_direct_api(recipient_id: str, message_text: str = "Тестовое сообщение напрямую через Instagram Graph API"):
    """Тест отправки напрямую через Instagram Graph API."""
    print("\n" + "="*80)
    print("🧪 ТЕСТ ОТПРАВКИ НАПРЯМУЮ ЧЕРЕЗ INSTAGRAM GRAPH API")
    print("="*80)
    print(f"Recipient ID: {recipient_id}")
    print(f"Account ID: {ACCOUNT_ID}")
    print(f"Message: {message_text}")
    print("="*80)
    
    url = f"{INSTAGRAM_GRAPH_API_BASE}/{ACCOUNT_ID}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
    }
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"\n📤 Отправка запроса на: {url}")
        print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        try:
            response = await client.post(url, json=payload, headers=headers)
            result = response.json()
            
            print(f"\n📥 Ответ Instagram API:")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if response.status_code == 200:
                print("\n✅ Сообщение успешно отправлено напрямую через Instagram API!")
                return True
            else:
                error = result.get("error", {})
                print(f"\n❌ Ошибка: {error.get('code')} - {error.get('message', 'Unknown error')}")
                print(f"   Error Subcode: {error.get('error_subcode')}")
                return False
        
        except Exception as e:
            print(f"\n❌ Исключение: {e}")
            import traceback
            traceback.print_exc()
            return False


async def check_webhook_config():
    """Проверка конфигурации webhook."""
    print("\n" + "="*80)
    print("🔍 ПРОВЕРКА КОНФИГУРАЦИИ WEBHOOK")
    print("="*80)
    
    url = f"http://{ALB_DNS}/api/v1/webhook-test/check-config"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            result = response.json()
            
            print(f"\n📋 Конфигурация webhook:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get("webhook_verify_token_configured"):
                print("\n✅ Webhook verify token настроен")
            else:
                print("\n⚠️  Webhook verify token НЕ настроен")
            
            if result.get("app_secret_configured"):
                print("✅ App secret настроен")
            else:
                print("⚠️  App secret НЕ настроен")
            
            print(f"\n📡 Webhook URL: {result.get('webhook_url')}")
            
        except Exception as e:
            print(f"\n❌ Ошибка проверки конфигурации: {e}")


async def main():
    """Главная функция."""
    recipient_id = sys.argv[1] if len(sys.argv) > 1 else "62670099264"
    
    print("\n" + "="*80)
    print("🚀 ТЕСТИРОВАНИЕ INSTAGRAM API НА СЕРВЕРЕ")
    print("="*80)
    
    # Проверка конфигурации webhook
    await check_webhook_config()
    
    # Тест отправки через серверный API
    success1 = await test_send_via_server_api(recipient_id)
    
    # Тест отправки напрямую через Instagram API
    success2 = await test_direct_api(recipient_id)
    
    # Итоги
    print("\n" + "="*80)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*80)
    print(f"Серверный API: {'✅ Успешно' if success1 else '❌ Ошибка'}")
    print(f"Прямой Instagram API: {'✅ Успешно' if success2 else '❌ Ошибка'}")
    print("="*80)
    
    if not success1 and not success2:
        print("\n⚠️  ОБА СПОСОБА НЕ СРАБОТАЛИ")
        print("\nВозможные причины:")
        print("1. 24-часовое окно ответов истекло (пользователь не писал в последние 24 часа)")
        print("2. Неверный recipient_id")
        print("3. Проблемы с правами токена")
        print("4. Instagram API временно недоступен")
        print("\n💡 Рекомендации:")
        print("- Попросите пользователя написать сообщение агенту в Instagram")
        print("- Проверьте логи сервера для webhook событий")
        print("- Используйте Self Messaging для тестирования (отправьте сообщение самому себе через Instagram app)")


if __name__ == "__main__":
    asyncio.run(main())

