#!/usr/bin/env python3
"""
Скрипт для проверки прав (permissions) Instagram токена.
"""

import asyncio
import json

import httpx

# Конфигурация
INSTAGRAM_GRAPH_API_BASE = "https://graph.instagram.com/v21.0"
FACEBOOK_GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
ACCESS_TOKEN = "IGAAXjRiKjwKFBZAGFRU1RTcUdhU1UwYWhvTndCdWJNSEFGN1FEZA1M5N0Rhekp3MDE4NUpKanlwd1haSHpubmRFZAk8xbXF1UF9CRmRZATHRqWU44QURYVlcwZA2VhaVV1MngwYUdSeDRXVTdEcWhCNmhpLTR2S3NrRWxzQU5UcEQ5dwZDZD"
CHANNEL_ACCOUNT_ID = "17841458318357324"


async def check_token_info():
    """Проверить информацию о токене и его правах."""
    print("\n" + "="*80)
    print("🔍 ПРОВЕРКА ПРАВ INSTAGRAM ТОКЕНА")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Проверка через Instagram Graph API - получение информации об аккаунте
        print("\n📋 ЭТАП 1: Проверка информации об аккаунте через Instagram API")
        print("-"*80)
        
        url1 = f"{INSTAGRAM_GRAPH_API_BASE}/{CHANNEL_ACCOUNT_ID}?fields=id,username"
        response1 = await client.get(url1, headers=headers)
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"✅ Аккаунт найден:")
            print(f"   ID: {data1.get('id')}")
            print(f"   Username: {data1.get('username')}")
        else:
            print(f"❌ Ошибка: {response1.status_code}")
            print(response1.text)
        
        # 2. Проверка через Facebook Graph API - debug_token
        print("\n📋 ЭТАП 2: Проверка токена через Facebook Debug Token API")
        print("-"*80)
        
        url2 = f"{FACEBOOK_GRAPH_API_BASE}/debug_token"
        params2 = {
            "input_token": ACCESS_TOKEN,
            "access_token": ACCESS_TOKEN  # Для проверки нужен сам токен или app access token
        }
        
        response2 = await client.get(url2, params=params2, headers=headers)
        
        if response2.status_code == 200:
            data2 = response2.json()
            debug_data = data2.get("data", {})
            print(f"✅ Информация о токене:")
            print(f"   App ID: {debug_data.get('app_id')}")
            print(f"   User ID: {debug_data.get('user_id')}")
            print(f"   Type: {debug_data.get('type')}")
            print(f"   Valid: {debug_data.get('is_valid')}")
            print(f"   Expires At: {debug_data.get('expires_at')}")
            print(f"   Scopes (права): {debug_data.get('scopes', [])}")
            
            scopes = debug_data.get("scopes", [])
            if scopes:
                print(f"\n📝 Список прав (scopes):")
                for scope in scopes:
                    print(f"   - {scope}")
                
                # Проверяем необходимые права для отправки сообщений
                required_scopes = [
                    "instagram_basic",
                    "instagram_manage_messages",
                    "pages_show_list",
                    "pages_messaging",
                    "pages_manage_metadata"
                ]
                
                print(f"\n🔍 Проверка необходимых прав для отправки сообщений:")
                missing_scopes = []
                for required in required_scopes:
                    if required in scopes:
                        print(f"   ✅ {required}")
                    else:
                        print(f"   ❌ {required} - ОТСУТСТВУЕТ")
                        missing_scopes.append(required)
                
                if missing_scopes:
                    print(f"\n⚠️  Отсутствуют необходимые права:")
                    for scope in missing_scopes:
                        print(f"   - {scope}")
                    print(f"\n💡 Нужно добавить эти права в Facebook Developer Console")
                else:
                    print(f"\n✅ Все необходимые права присутствуют!")
            else:
                print(f"\n⚠️  Не удалось получить список прав")
        else:
            print(f"❌ Ошибка: {response2.status_code}")
            print(response2.text)
            print(f"\n💡 Попробуем альтернативный способ...")
        
        # 3. Альтернативная проверка - через /me/permissions (если доступно)
        print("\n📋 ЭТАП 3: Проверка через /me/permissions")
        print("-"*80)
        
        try:
            # Пробуем через Instagram Business Account ID
            account_id_from_step1 = data1.get("id") if response1.status_code == 200 else CHANNEL_ACCOUNT_ID
            
            url3 = f"{INSTAGRAM_GRAPH_API_BASE}/{account_id_from_step1}?fields=id,username"
            response3 = await client.get(url3, headers=headers)
            
            if response3.status_code == 200:
                print(f"✅ Доступ к аккаунту подтвержден")
            else:
                print(f"⚠️  Ошибка доступа: {response3.status_code}")
        except Exception as e:
            print(f"⚠️  Ошибка: {e}")
        
        # 4. Проверка доступных endpoints через Instagram API
        print("\n📋 ЭТАП 4: Проверка доступных endpoints")
        print("-"*80)
        
        account_id = data1.get("id") if response1.status_code == 200 else CHANNEL_ACCOUNT_ID
        
        # Пробуем различные endpoints для проверки прав
        endpoints_to_check = [
            (f"{INSTAGRAM_GRAPH_API_BASE}/{account_id}/conversations", "Получение списка диалогов"),
            (f"{INSTAGRAM_GRAPH_API_BASE}/{account_id}/messages", "Отправка сообщений (POST)"),
            (f"{INSTAGRAM_GRAPH_API_BASE}/{account_id}?fields=id,username,website", "Базовая информация"),
        ]
        
        for endpoint, description in endpoints_to_check:
            try:
                # Для messages делаем OPTIONS или пробуем GET (может не работать, но покажет права)
                if "messages" in endpoint:
                    # Пробуем сделать тестовый запрос с неверным recipient для проверки прав
                    test_payload = {"recipient": {"id": "test"}, "message": {"text": "test"}}
                    test_response = await client.post(endpoint, json=test_payload, headers=headers)
                    if test_response.status_code == 400:
                        error_data = test_response.json().get("error", {})
                        error_code = error_data.get("code")
                        # Если ошибка 100 (user not found) или 200 (invalid param) - значит endpoint доступен
                        # Если 403 - нет прав
                        if error_code in [100, 200]:
                            print(f"   ✅ {description}: Endpoint доступен (ошибка валидации, но права есть)")
                        elif error_code == 10 or test_response.status_code == 403:
                            print(f"   ❌ {description}: Нет прав (403 или Permission Denied)")
                        else:
                            print(f"   ⚠️  {description}: Неизвестная ошибка ({error_code})")
                    elif test_response.status_code == 200:
                        print(f"   ✅ {description}: Полный доступ")
                    else:
                        print(f"   ⚠️  {description}: Статус {test_response.status_code}")
                else:
                    test_response = await client.get(endpoint, headers=headers)
                    if test_response.status_code == 200:
                        print(f"   ✅ {description}: Доступен")
                    elif test_response.status_code == 403:
                        print(f"   ❌ {description}: Нет прав (403)")
                    elif test_response.status_code == 400:
                        error_data = test_response.json().get("error", {})
                        error_code = error_data.get("code")
                        if error_code == 10:
                            print(f"   ❌ {description}: Permission Denied")
                        else:
                            print(f"   ⚠️  {description}: Ошибка {error_code}")
                    else:
                        print(f"   ⚠️  {description}: Статус {test_response.status_code}")
            except Exception as e:
                print(f"   ⚠️  {description}: Ошибка - {e}")
        
        # 5. Проверка через Instagram Business Account (если доступно)
        print("\n📋 ЭТАП 5: Проверка типа аккаунта и связанных данных")
        print("-"*80)
        
        try:
            # Пробуем получить больше информации об аккаунте
            url5 = f"{INSTAGRAM_GRAPH_API_BASE}/{account_id}?fields=id,username,account_type"
            response5 = await client.get(url5, headers=headers)
            
            if response5.status_code == 200:
                account_data = response5.json()
                print(f"✅ Информация об аккаунте:")
                print(f"   ID: {account_data.get('id')}")
                print(f"   Username: {account_data.get('username')}")
                account_type = account_data.get('account_type', 'N/A')
                print(f"   Account Type: {account_type}")
                
                if account_type != "BUSINESS":
                    print(f"\n⚠️  ВНИМАНИЕ: Аккаунт не является Business аккаунтом!")
                    print(f"   Для отправки сообщений через API нужен Instagram Business Account")
            else:
                print(f"⚠️  Не удалось получить информацию: {response5.status_code}")
        except Exception as e:
            print(f"⚠️  Ошибка: {e}")
    
    print("\n" + "="*80)
    print("📊 ИТОГИ ПРОВЕРКИ")
    print("="*80)
    print("💡 Если отсутствуют необходимые права:")
    print("   1. Откройте Facebook Developer Console")
    print("   2. Перейдите в настройки приложения")
    print("   3. Добавьте необходимые permissions:")
    print("      - instagram_basic")
    print("      - instagram_manage_messages")
    print("      - pages_show_list")
    print("      - pages_messaging")
    print("      - pages_manage_metadata")
    print("   4. Пересоздайте токен с новыми правами")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(check_token_info())

