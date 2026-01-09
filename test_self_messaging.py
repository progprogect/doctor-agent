#!/usr/bin/env python3
"""
Тест Self Messaging для Instagram согласно официальной документации.
https://developers.facebook.com/docs/instagram-platform/self-messaging

Self Messaging позволяет отправлять сообщения самому себе без recipient.
24-часовое окно НЕ применяется для self messaging.
"""

import asyncio
import json

import httpx

INSTAGRAM_GRAPH_API_BASE = "https://graph.instagram.com/v21.0"
FACEBOOK_GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
ACCESS_TOKEN = "IGAAXjRiKjwKFBZAGFRU1RTcUdhU1UwYWhvTndCdWJNSEFGN1FEZA1M5N0Rhekp3MDE4NUpKanlwd1haSHpubmRFZAk8xbXF1UF9CRmRZATHRqWU44QURYVlcwZA2VhaVV1MngwYUdSeDRXVTdEcWhCNmhpLTR2S3NrRWxzQU5UcEQ5dwZDZD"
ACCOUNT_ID = "25638311079121978"  # Реальный Account ID из API

async def test_self_messaging():
    """Тест Self Messaging согласно документации."""
    print("\n" + "="*80)
    print("🔍 ТЕСТ SELF MESSAGING (отправка самому себе)")
    print("="*80)
    print("Согласно документации:")
    print("https://developers.facebook.com/docs/instagram-platform/self-messaging")
    print("="*80)
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    test_message = "Тестовое сообщение через Self Messaging API. Это проверка отправки самому себе."
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Согласно документации, для Self Messaging формат запроса:
        # POST /{INSTAGRAM_SCOPED_ID}/messages
        # Body: {"message": {"text": "..."}}
        # БЕЗ поля "recipient"!
        
        print("\n📋 ЭТАП 1: Проверка Account ID")
        print("-"*80)
        url_check = f"{INSTAGRAM_GRAPH_API_BASE}/{ACCOUNT_ID}?fields=id,username,account_type"
        response_check = await client.get(url_check, headers=headers)
        
        if response_check.status_code == 200:
            account_data = response_check.json()
            print(f"✅ Account ID: {account_data.get('id')}")
            print(f"✅ Username: {account_data.get('username')}")
            print(f"✅ Account Type: {account_data.get('account_type')}")
            
            if account_data.get('account_type') != 'BUSINESS':
                print(f"\n⚠️  ВНИМАНИE: Account Type не BUSINESS!")
                print(f"   Self Messaging требует Instagram Professional account")
        else:
            print(f"❌ Ошибка проверки Account ID: {response_check.status_code}")
            return
        
        # Вариант 1: Через Instagram Graph API (Instagram Login flow)
        print("\n📋 ЭТАП 2: Тест через Instagram Graph API (graph.instagram.com)")
        print("-"*80)
        print("Формат согласно документации:")
        print(f"POST /{ACCOUNT_ID}/messages")
        print('Body: {"message": {"text": "..."}}')
        print("(БЕЗ поля recipient)")
        print("-"*80)
        
        url1 = f"{INSTAGRAM_GRAPH_API_BASE}/{ACCOUNT_ID}/messages"
        payload1 = {
            "message": {
                "text": test_message
            }
        }
        
        print(f"\n🔹 POST {url1}")
        print(f"Body: {json.dumps(payload1, indent=2, ensure_ascii=False)}")
        
        response1 = await client.post(url1, json=payload1, headers=headers)
        
        print(f"\n✅ Status Code: {response1.status_code}")
        if response1.status_code == 200:
            result = response1.json()
            print(f"✅ УСПЕХ! Сообщение отправлено самому себе!")
            print(f"   Message ID: {result.get('id') or result.get('message_id')}")
            print(f"\n💡 Self Messaging работает через Instagram Graph API!")
            return True
        else:
            error = response1.json().get("error", {})
            print(f"❌ Ошибка: {error.get('code')} - {error.get('message')}")
            print(f"   Subcode: {error.get('error_subcode')}")
            
            # Если не сработало, пробуем через Facebook Graph API
            if error.get('code') == 100 or error.get('code') == 10:
                print(f"\n💡 Пробуем альтернативный вариант через Facebook Graph API...")
        
        # Вариант 2: Через Facebook Graph API (Facebook Login flow)
        print("\n📋 ЭТАП 3: Тест через Facebook Graph API (graph.facebook.com)")
        print("-"*80)
        print("Согласно документации, для Facebook Login flow используется:")
        print("graph.facebook.com вместо graph.instagram.com")
        print("-"*80)
        
        url2 = f"{FACEBOOK_GRAPH_API_BASE}/{ACCOUNT_ID}/messages"
        payload2 = {
            "message": {
                "text": test_message
            }
        }
        
        print(f"\n🔹 POST {url2}")
        print(f"Body: {json.dumps(payload2, indent=2, ensure_ascii=False)}")
        
        response2 = await client.post(url2, json=payload2, headers=headers)
        
        print(f"\n✅ Status Code: {response2.status_code}")
        if response2.status_code == 200:
            result = response2.json()
            print(f"✅ УСПЕХ! Сообщение отправлено самому себе!")
            print(f"   Message ID: {result.get('id') or result.get('message_id')}")
            print(f"\n💡 Self Messaging работает через Facebook Graph API!")
            return True
        else:
            error = response2.json().get("error", {})
            print(f"❌ Ошибка: {error.get('code')} - {error.get('message')}")
            print(f"   Subcode: {error.get('error_subcode')}")
            
            # Анализ ошибки
            error_code = error.get('code')
            if error_code == 100:
                print(f"\n💡 Возможные причины:")
                print(f"   1. Self Messaging может требовать специальной настройки")
                print(f"   2. Нужен Instagram Professional account (не просто Business)")
                print(f"   3. Может потребоваться специальный токен или permissions")
            elif error_code == 10:
                print(f"\n💡 Возможные причины:")
                print(f"   1. Токен не имеет прав для Self Messaging")
                print(f"   2. Нужны дополнительные permissions")
        
        # Вариант 3: Попробуем с recipient = самому себе (на случай если все же нужен)
        print("\n📋 ЭТАП 4: Тест с recipient = самому себе")
        print("-"*80)
        print("Пробуем формат с recipient, где recipient.id = Account ID")
        print("-"*80)
        
        url3 = f"{INSTAGRAM_GRAPH_API_BASE}/{ACCOUNT_ID}/messages"
        payload3 = {
            "recipient": {"id": ACCOUNT_ID},
            "message": {"text": test_message}
        }
        
        print(f"\n🔹 POST {url3}")
        print(f"Body: {json.dumps(payload3, indent=2, ensure_ascii=False)}")
        
        response3 = await client.post(url3, json=payload3, headers=headers)
        
        print(f"\n✅ Status Code: {response3.status_code}")
        if response3.status_code == 200:
            result = response3.json()
            print(f"✅ УСПЕХ! Сообщение отправлено!")
            print(f"   Message ID: {result.get('id') or result.get('message_id')}")
            return True
        else:
            error = response3.json().get("error", {})
            print(f"❌ Ошибка: {error.get('code')} - {error.get('message')}")
    
    print("\n" + "="*80)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*80)
    print("❌ Self Messaging не сработал ни одним способом")
    print("\n💡 Возможные причины:")
    print("   1. Self Messaging требует специальной настройки в Facebook Developer Console")
    print("   2. Нужен Instagram Professional account (не просто Business)")
    print("   3. Может потребоваться специальный токен или permissions")
    print("   4. Возможно, функция доступна только для определенных типов аккаунтов")
    print("\n📖 Документация:")
    print("   https://developers.facebook.com/docs/instagram-platform/self-messaging")
    print("="*80)
    
    return False

if __name__ == "__main__":
    result = asyncio.run(test_self_messaging())
    if result:
        print(f"\n✅ Тест успешен! Self Messaging работает!")
    else:
        print(f"\n⚠️  Тест не прошел. Проверьте требования из документации.")

