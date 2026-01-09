#!/usr/bin/env python3
"""
Альтернативные способы отправки сообщений через Instagram API.
Пробуем разные форматы запросов.
"""

import asyncio
import json

import httpx

INSTAGRAM_GRAPH_API_BASE = "https://graph.instagram.com/v21.0"
FACEBOOK_GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
ACCESS_TOKEN = "IGAAXjRiKjwKFBZAGFRU1RTcUdhU1UwYWhvTndCdWJNSEFGN1FEZA1M5N0Rhekp3MDE4NUpKanlwd1haSHpubmRFZAk8xbXF1UF9CRmRZATHRqWU44QURYVlcwZA2VhaVV1MngwYUdSeDRXVTdEcWhCNmhpLTR2S3NrRWxzQU5UcEQ5dwZDZD"
ACCOUNT_ID = "25638311079121978"
RECIPIENT_ID = "62670099264"

async def test_alternative_formats():
    """Пробуем альтернативные форматы отправки сообщений."""
    print("\n" + "="*80)
    print("🔍 ТЕСТИРОВАНИЕ АЛЬТЕРНАТИВНЫХ ФОРМАТОВ ОТПРАВКИ")
    print("="*80)
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    test_message = "Тестовое сообщение от Doctor Agent"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Вариант 1: Стандартный формат (уже пробовали)
        print("\n📋 ВАРИАНТ 1: Стандартный формат (recipient.id)")
        print("-"*80)
        url1 = f"{INSTAGRAM_GRAPH_API_BASE}/{ACCOUNT_ID}/messages"
        payload1 = {
            "recipient": {"id": RECIPIENT_ID},
            "message": {"text": test_message},
        }
        
        response1 = await client.post(url1, json=payload1, headers=headers)
        print(f"Status: {response1.status_code}")
        if response1.status_code != 200:
            error = response1.json().get("error", {})
            print(f"Error: {error.get('code')} - {error.get('message')}")
            print(f"Subcode: {error.get('error_subcode')}")
        
        # Вариант 2: Через Facebook Graph API (если связан с Page)
        print("\n📋 ВАРИАНТ 2: Через Facebook Graph API (Page)")
        print("-"*80)
        # Сначала попробуем найти связанную Page
        try:
            url_page = f"{FACEBOOK_GRAPH_API_BASE}/me/accounts"
            response_page = await client.get(url_page, headers=headers)
            if response_page.status_code == 200:
                pages = response_page.json().get("data", [])
                if pages:
                    page_id = pages[0].get("id")
                    print(f"Найдена Page: {page_id}")
                    
                    # Пробуем отправить через Page
                    url2 = f"{FACEBOOK_GRAPH_API_BASE}/{page_id}/messages"
                    payload2 = {
                        "recipient": {"id": RECIPIENT_ID},
                        "message": {"text": test_message},
                    }
                    response2 = await client.post(url2, json=payload2, headers=headers)
                    print(f"Status: {response2.status_code}")
                    if response2.status_code == 200:
                        print("✅ Успешно через Facebook Page!")
                        return True
                    else:
                        error = response2.json().get("error", {})
                        print(f"Error: {error.get('code')} - {error.get('message')}")
                else:
                    print("Связанных страниц не найдено")
            else:
                print(f"Не удалось получить страницы: {response_page.status_code}")
        except Exception as e:
            print(f"Ошибка: {e}")
        
        # Вариант 3: Проверяем, может быть нужен thread_id
        print("\n📋 ВАРИАНТ 3: Попытка получить thread_id из диалогов")
        print("-"*80)
        # Пробуем получить диалоги и найти thread_id
        url_convos = f"{INSTAGRAM_GRAPH_API_BASE}/{ACCOUNT_ID}/conversations"
        response_convos = await client.get(url_convos, headers=headers)
        if response_convos.status_code == 200:
            conversations = response_convos.json().get("data", [])
            print(f"Найдено диалогов: {len(conversations)}")
            if conversations:
                # Пробуем использовать thread_id если есть
                for conv in conversations:
                    thread_id = conv.get("thread_key", {}).get("thread_fbid") or conv.get("id")
                    participants = conv.get("participants", {}).get("data", [])
                    print(f"Thread ID: {thread_id}")
                    print(f"Participants: {participants}")
                    
                    # Пробуем отправить с thread_id
                    if thread_id:
                        url3 = f"{INSTAGRAM_GRAPH_API_BASE}/{ACCOUNT_ID}/messages"
                        payload3 = {
                            "recipient": {"thread_key": {"thread_fbid": thread_id}},
                            "message": {"text": test_message},
                        }
                        response3 = await client.post(url3, json=payload3, headers=headers)
                        print(f"Status с thread_id: {response3.status_code}")
                        if response3.status_code == 200:
                            print("✅ Успешно с thread_id!")
                            return True
        else:
            print(f"Не удалось получить диалоги: {response_convos.status_code}")
        
        # Вариант 4: Проверяем формат recipient с user_id
        print("\n📋 ВАРИАНТ 4: Альтернативный формат recipient")
        print("-"*80)
        url4 = f"{INSTAGRAM_GRAPH_API_BASE}/{ACCOUNT_ID}/messages"
        # Пробуем разные форматы
        formats_to_try = [
            {"user_id": RECIPIENT_ID},  # user_id вместо id
            {"id": str(RECIPIENT_ID)},  # строка вместо числа
            {"id": int(RECIPIENT_ID) if RECIPIENT_ID.isdigit() else RECIPIENT_ID},  # число
        ]
        
        for fmt in formats_to_try:
            payload4 = {
                "recipient": fmt,
                "message": {"text": test_message},
            }
            response4 = await client.post(url4, json=payload4, headers=headers)
            print(f"Format {fmt}: Status {response4.status_code}")
            if response4.status_code == 200:
                print(f"✅ Успешно с форматом {fmt}!")
                return True
            elif response4.status_code == 400:
                error = response4.json().get("error", {})
                if error.get("error_subcode") != 2534014:  # Если не "user not found"
                    print(f"  Другая ошибка: {error.get('message')}")
    
    return False

if __name__ == "__main__":
    result = asyncio.run(test_alternative_formats())
    if result:
        print("\n✅ Найден рабочий формат!")
    else:
        print("\n❌ Ни один альтернативный формат не сработал")
        print("\n💡 Возможные причины:")
        print("   1. Recipient ID неверный (проверьте sender.id из webhook)")
        print("   2. Пользователь не писал в течение 24 часов")
        print("   3. Нужны дополнительные настройки в Facebook Developer Console")

