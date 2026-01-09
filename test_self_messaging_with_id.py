#!/usr/bin/env python3
"""
Тест Self Messaging с Instagram-scoped ID из webhook.
Использует формат БЕЗ поля recipient согласно документации.
"""

import asyncio
import json
import sys

import httpx

INSTAGRAM_GRAPH_API_BASE = "https://graph.instagram.com/v21.0"
ACCESS_TOKEN = "IGAAXjRiKjwKFBZAGFRU1RTcUdhU1UwYWhvTndCdWJNSEFGN1FEZA1M5N0Rhekp3MDE4NUpKanlwd1haSHpubmRFZAk8xbXF1UF9CRmRZATHRqWU44QURYVlcwZA2VhaVV1MngwYUdSeDRXVTdEcWhCNmhpLTR2S3NrRWxzQU5UcEQ5dwZDZD"

async def test_self_messaging_with_id(instagram_scoped_id: str):
    """Тест Self Messaging с Instagram-scoped ID."""
    print("\n" + "="*80)
    print("🔍 ТЕСТ SELF MESSAGING С INSTAGRAM-SCOPED ID")
    print("="*80)
    print(f"Instagram-scoped ID: {instagram_scoped_id}")
    print("="*80)
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    test_message = "Тестовое сообщение через Self Messaging API. Это проверка отправки самому себе."
    
    # Согласно документации, для Self Messaging формат:
    # POST /{INSTAGRAM_SCOPED_ID}/messages
    # Body: {"message": {"text": "..."}}
    # БЕЗ поля recipient!
    
    url = f"{INSTAGRAM_GRAPH_API_BASE}/{instagram_scoped_id}/messages"
    payload = {
        "message": {
            "text": test_message
        }
    }
    
    print(f"\n📋 Формат запроса согласно документации:")
    print(f"POST /{instagram_scoped_id}/messages")
    print(f"Body: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print("(БЕЗ поля recipient!)")
    print("-"*80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        
        print(f"\n✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            message_id = result.get("id") or result.get("message_id")
            print(f"\n✅ УСПЕХ! Self Messaging работает!")
            print(f"   Message ID: {message_id}")
            print(f"   Instagram-scoped ID: {instagram_scoped_id}")
            print("\n💡 Формат правильный: БЕЗ поля recipient!")
            return True
        else:
            error = response.json().get("error", {})
            error_code = error.get("code")
            error_subcode = error.get("error_subcode")
            error_message = error.get("message")
            
            print(f"\n❌ Ошибка: {error_code} (subcode: {error_subcode})")
            print(f"   Message: {error_message}")
            
            if error_code == 100:
                print(f"\n💡 Возможные причины:")
                print(f"   1. Instagram-scoped ID неверный")
                print(f"   2. Нужно получить его из webhook события с is_self=true")
                print(f"   3. Отправьте сообщение самому себе через Instagram app")
                print(f"   4. Проверьте логи сервера для получения recipient.id из webhook")
            
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python3 test_self_messaging_with_id.py <instagram_scoped_id>")
        print("\n💡 Чтобы получить instagram_scoped_id:")
        print("   1. Отправьте сообщение самому себе через Instagram app")
        print("   2. Проверьте логи сервера")
        print("   3. Найдите recipient.id из webhook события с is_self=true")
        sys.exit(1)
    
    instagram_scoped_id = sys.argv[1]
    result = asyncio.run(test_self_messaging_with_id(instagram_scoped_id))
    
    if result:
        print("\n✅ Тест успешен!")
    else:
        print("\n⚠️  Тест не прошел")

