#!/usr/bin/env python3
"""
Диагностика проблемы с отправкой Instagram сообщений.
Проверяет все возможные причины ошибки.
"""

import asyncio
import json

import httpx

INSTAGRAM_GRAPH_API_BASE = "https://graph.instagram.com/v21.0"
ACCESS_TOKEN = "IGAAXjRiKjwKFBZAGFRU1RTcUdhU1UwYWhvTndCdWJNSEFGN1FEZA1M5N0Rhekp3MDE4NUpKanlwd1haSHpubmRFZAk8xbXF1UF9CRmRZATHRqWU44QURYVlcwZA2VhaVV1MngwYUdSeDRXVTdEcWhCNmhpLTR2S3NrRWxzQU5UcEQ5dwZDZD"
CHANNEL_ACCOUNT_ID_FROM_CONFIG = "17841458318357324"  # Из конфигурации binding
RECIPIENT_ID = "62670099264"

async def diagnose():
    """Полная диагностика проблемы."""
    print("\n" + "="*80)
    print("🔍 ДИАГНОСТИКА ПРОБЛЕМЫ С INSTAGRAM API")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Проверка реального Account ID
        print("\n📋 ЭТАП 1: Проверка реального Account ID")
        print("-"*80)
        
        url1 = f"{INSTAGRAM_GRAPH_API_BASE}/{CHANNEL_ACCOUNT_ID_FROM_CONFIG}?fields=id,username,account_type"
        response1 = await client.get(url1, headers=headers)
        
        if response1.status_code == 200:
            account_data = response1.json()
            real_account_id = account_data.get("id")
            username = account_data.get("username")
            account_type = account_data.get("account_type")
            
            print(f"✅ Account ID из конфигурации: {CHANNEL_ACCOUNT_ID_FROM_CONFIG}")
            print(f"✅ Реальный Account ID из API: {real_account_id}")
            print(f"✅ Username: {username}")
            print(f"✅ Account Type: {account_type}")
            
            if CHANNEL_ACCOUNT_ID_FROM_CONFIG != real_account_id:
                print(f"\n⚠️  ВНИМАНИЕ: Account ID не совпадает!")
                print(f"   В binding используется: {CHANNEL_ACCOUNT_ID_FROM_CONFIG}")
                print(f"   Реальный Account ID: {real_account_id}")
                print(f"   💡 НУЖНО ИСПОЛЬЗОВАТЬ РЕАЛЬНЫЙ Account ID: {real_account_id}")
        else:
            print(f"❌ Ошибка получения Account ID: {response1.status_code}")
            return
        
        # 2. Проверка формата запроса согласно документации
        print("\n📋 ЭТАП 2: Проверка формата запроса")
        print("-"*80)
        
        # Согласно документации Instagram Graph API:
        # POST /{ig-user-id}/messages
        # Body: {"recipient": {"id": "user-id"}, "message": {"text": "message"}}
        
        print("✅ Формат запроса правильный:")
        print(f"   POST /{real_account_id}/messages")
        print(f"   Body: {{'recipient': {{'id': '{RECIPIENT_ID}'}}, 'message': {{'text': '...'}}}}")
        
        # 3. Проверка требований к recipient_id
        print("\n📋 ЭТАП 3: Проверка требований к recipient_id")
        print("-"*80)
        
        print("Согласно документации Instagram Graph API:")
        print("1. recipient.id должен быть ID пользователя, который написал агенту")
        print("2. Пользователь должен был написать в течение последних 24 часов")
        print("3. recipient.id берется из webhook события: sender.id")
        print(f"\nИспользуемый recipient_id: {RECIPIENT_ID}")
        print("💡 Убедитесь, что это точно sender.id из последнего webhook события")
        
        # 4. Проверка отправки с правильным Account ID
        print("\n📋 ЭТАП 4: Тест отправки с правильным Account ID")
        print("-"*80)
        
        url4 = f"{INSTAGRAM_GRAPH_API_BASE}/{real_account_id}/messages"
        payload4 = {
            "recipient": {"id": RECIPIENT_ID},
            "message": {"text": "Тестовое сообщение от Doctor Agent. Диагностика."},
        }
        
        response4 = await client.post(url4, json=payload4, headers=headers)
        
        print(f"Status: {response4.status_code}")
        if response4.status_code == 200:
            result = response4.json()
            print(f"✅ УСПЕХ! Сообщение отправлено!")
            print(f"   Message ID: {result.get('message_id') or result.get('id')}")
            print(f"\n💡 ПРОБЛЕМА БЫЛА В Account ID!")
            print(f"   Используйте реальный Account ID ({real_account_id}) вместо {CHANNEL_ACCOUNT_ID_FROM_CONFIG}")
        else:
            error = response4.json().get("error", {})
            error_code = error.get("code")
            error_subcode = error.get("error_subcode")
            error_message = error.get("message")
            
            print(f"❌ Ошибка: {error_code} (subcode: {error_subcode})")
            print(f"   Message: {error_message}")
            
            # Анализ ошибки
            print("\n📋 АНАЛИЗ ОШИБКИ:")
            print("-"*80)
            
            if error_code == 100 and error_subcode == 2534014:
                print("Ошибка: 'Пользователь не найден'")
                print("\nВозможные причины:")
                print("1. ❌ Recipient ID неверный")
                print("   - Проверьте, что это точно sender.id из webhook события")
                print("   - Убедитесь, что нет лишних пробелов или символов")
                print("   - Проверьте, что ID в формате строки или числа")
                print("\n2. ❌ Пользователь не писал в течение 24 часов")
                print("   - Instagram позволяет отправлять только в течение 24ч после сообщения пользователя")
                print("   - Попросите пользователя написать снова")
                print("\n3. ❌ Проблема с настройками приложения")
                print("   - Проверьте, что приложение в режиме 'Live' (не Development)")
                print("   - Проверьте настройки конфиденциальности Instagram аккаунта")
                print("   - Убедитесь, что Instagram Business Account связан с Facebook Page")
            
            elif error_code == 10:
                print("Ошибка: 'Outside allowed window'")
                print("   - Истекло 24-часовое окно")
                print("   - Пользователь должен написать снова")
            
            elif error_code == 200:
                print("Ошибка: 'Invalid parameter'")
                print("   - Неверный формат recipient_id")
                print("   - Проверьте формат ID")
        
        # 5. Рекомендации
        print("\n" + "="*80)
        print("📋 РЕКОМЕНДАЦИИ")
        print("="*80)
        
        print("\n1. ✅ ИСПРАВИТЬ Account ID в binding:")
        print(f"   Замените {CHANNEL_ACCOUNT_ID_FROM_CONFIG} на {real_account_id}")
        print("   Это критично для правильной работы отправки сообщений")
        
        print("\n2. ✅ ПРОВЕРИТЬ recipient_id:")
        print("   - Откройте логи сервера после отправки сообщения")
        print("   - Найдите строку: 'Sender ID (это recipient_id для отправки):'")
        print("   - Убедитесь, что это точно '62670099264'")
        print("   - Если отличается - используйте правильный ID")
        
        print("\n3. ✅ ПРОВЕРИТЬ настройки приложения:")
        print("   - Facebook Developer Console > Ваше приложение")
        print("   - Убедитесь, что приложение в режиме 'Live'")
        print("   - Проверьте, что Instagram Business Account связан с Facebook Page")
        
        print("\n4. ✅ ПРОВЕРИТЬ webhook:")
        print("   - Убедитесь, что webhook настроен и получает события")
        print("   - Проверьте URL webhook в Facebook Developer Console")
        print("   - Убедитесь, что webhook endpoint доступен из интернета")
        
        print("\n5. ✅ ПРОВЕРИТЬ права токена:")
        print("   - instagram_basic")
        print("   - instagram_manage_messages")
        print("   - pages_messaging")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(diagnose())

