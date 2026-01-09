#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Instagram Graph API endpoints
для получения информации о сообщениях и conversations.
"""

import asyncio
import json
import sys
from typing import Optional

import httpx

# Конфигурация
INSTAGRAM_GRAPH_API_BASE = "https://graph.instagram.com/v21.0"
FACEBOOK_GRAPH_API_BASE = "https://graph.facebook.com/v21.0"

# Access token (нужно получить из channel binding или передать как аргумент)
ACCESS_TOKEN = None

# Данные из webhook события
WEBHOOK_ENTRY_ID = "17841458318357324"  # entry.id из webhook (Account ID)
MESSAGE_ID = "aWdfZAG1faXRlbToxOklHTWVzc2FnZAUlEOjE3ODQxNDU4MzE4MzU3MzI0OjM0MDI4MjM2Njg0MTcxMDMwMTI0NDI3NjExODk0MjI3MzE3ODI0MTozMjYxMzE2NDUzNzQyMzA0ODA3ODk1NzgxNjE4Mzc4MzQyNAZDZD"


async def test_endpoint(
    client: httpx.AsyncClient, method: str, url: str, headers: dict, data: Optional[dict] = None
) -> tuple[int, dict]:
    """Тестировать API endpoint."""
    try:
        if method == "GET":
            response = await client.get(url, headers=headers, timeout=30.0)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=data, timeout=30.0)
        else:
            return 0, {"error": "Unsupported method"}

        try:
            response_data = response.json()
        except:
            response_data = {"raw": response.text[:500]}

        return response.status_code, response_data
    except Exception as e:
        return 0, {"error": str(e)}


async def test_conversations_endpoint(client: httpx.AsyncClient, account_id: str, token: str):
    """Тест 1: Получить список conversations."""
    print("\n" + "=" * 80)
    print("ТЕСТ 1: Получение списка conversations")
    print("=" * 80)

    endpoints_to_try = [
        f"{INSTAGRAM_GRAPH_API_BASE}/{account_id}/conversations",
        f"{INSTAGRAM_GRAPH_API_BASE}/{account_id}/conversations?fields=id,participants,updated_time",
        f"{INSTAGRAM_GRAPH_API_BASE}/{account_id}/conversations?fields=id,participants,messages",
        f"{FACEBOOK_GRAPH_API_BASE}/{account_id}/conversations",
        f"{FACEBOOK_GRAPH_API_BASE}/{account_id}/conversations?fields=id,participants",
    ]

    headers = {"Authorization": f"Bearer {token}"}

    for endpoint in endpoints_to_try:
        print(f"\n🔍 Тестируем: {endpoint}")
        status, response = await test_endpoint(client, "GET", endpoint, headers)

        if status == 200:
            print(f"✅ Успешно! Статус: {status}")
            data = response.get("data", [])
            print(f"   Получено conversations: {len(data)}")
            if data:
                print(f"   Первый conversation:")
                print(json.dumps(data[0], indent=2, ensure_ascii=False)[:500])
            return response
        else:
            error = response.get("error", {})
            print(f"❌ Ошибка {status}: {error.get('message', 'Unknown')}")
            if error.get("code"):
                print(f"   Code: {error.get('code')}, Subcode: {error.get('error_subcode')}")

    return None


async def test_messages_endpoint(
    client: httpx.AsyncClient, conversation_id: str, token: str
):
    """Тест 2: Получить messages из conversation."""
    print("\n" + "=" * 80)
    print("ТЕСТ 2: Получение messages из conversation")
    print("=" * 80)

    endpoints_to_try = [
        f"{INSTAGRAM_GRAPH_API_BASE}/{conversation_id}/messages",
        f"{INSTAGRAM_GRAPH_API_BASE}/{conversation_id}/messages?fields=id,from,to,message,created_time",
        f"{FACEBOOK_GRAPH_API_BASE}/{conversation_id}/messages",
        f"{FACEBOOK_GRAPH_API_BASE}/{conversation_id}/messages?fields=id,from,to,message",
    ]

    headers = {"Authorization": f"Bearer {token}"}

    for endpoint in endpoints_to_try:
        print(f"\n🔍 Тестируем: {endpoint}")
        status, response = await test_endpoint(client, "GET", endpoint, headers)

        if status == 200:
            print(f"✅ Успешно! Статус: {status}")
            data = response.get("data", [])
            print(f"   Получено messages: {len(data)}")
            if data:
                print(f"   Последнее сообщение:")
                print(json.dumps(data[-1], indent=2, ensure_ascii=False)[:500])
            return response
        else:
            error = response.get("error", {})
            print(f"❌ Ошибка {status}: {error.get('message', 'Unknown')}")

    return None


async def test_message_by_id(client: httpx.AsyncClient, message_id: str, token: str):
    """Тест 3: Получить информацию о сообщении по message_id."""
    print("\n" + "=" * 80)
    print("ТЕСТ 3: Получение информации о сообщении по message_id")
    print("=" * 80)

    # Пробуем разные варианты endpoints
    endpoints_to_try = [
        f"{INSTAGRAM_GRAPH_API_BASE}/{message_id}",
        f"{INSTAGRAM_GRAPH_API_BASE}/{message_id}?fields=id,from,to,message",
        f"{FACEBOOK_GRAPH_API_BASE}/{message_id}",
        f"{FACEBOOK_GRAPH_API_BASE}/{message_id}?fields=id,from,to,message",
    ]

    headers = {"Authorization": f"Bearer {token}"}

    for endpoint in endpoints_to_try:
        print(f"\n🔍 Тестируем: {endpoint}")
        status, response = await test_endpoint(client, "GET", endpoint, headers)

        if status == 200:
            print(f"✅ Успешно! Статус: {status}")
            print(f"   Данные:")
            print(json.dumps(response, indent=2, ensure_ascii=False)[:500])
            return response
        else:
            error = response.get("error", {})
            print(f"❌ Ошибка {status}: {error.get('message', 'Unknown')}")

    return None


async def test_account_info(client: httpx.AsyncClient, account_id: str, token: str):
    """Тест 4: Получить информацию об аккаунте."""
    print("\n" + "=" * 80)
    print("ТЕСТ 4: Получение информации об аккаунте")
    print("=" * 80)

    endpoints_to_try = [
        f"{INSTAGRAM_GRAPH_API_BASE}/{account_id}",
        f"{INSTAGRAM_GRAPH_API_BASE}/{account_id}?fields=id,username,account_type",
        f"{FACEBOOK_GRAPH_API_BASE}/{account_id}",
    ]

    headers = {"Authorization": f"Bearer {token}"}

    for endpoint in endpoints_to_try:
        print(f"\n🔍 Тестируем: {endpoint}")
        status, response = await test_endpoint(client, "GET", endpoint, headers)

        if status == 200:
            print(f"✅ Успешно! Статус: {status}")
            print(f"   Данные:")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return response
        else:
            error = response.get("error", {})
            print(f"❌ Ошибка {status}: {error.get('message', 'Unknown')}")

    return None


async def main():
    """Основная функция."""
    print("=" * 80)
    print("🧪 ТЕСТИРОВАНИЕ INSTAGRAM GRAPH API ENDPOINTS")
    print("=" * 80)
    print("\nЦель: Найти способ получить sender_id из message_edit события")
    print(f"Account ID (entry.id): {WEBHOOK_ENTRY_ID}")
    print(f"Message ID (mid): {MESSAGE_ID[:50]}...")

    # Получить access token
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        print("\n❌ Access token не предоставлен")
        print("   Использование: python3 test_instagram_graph_api.py <access_token>")
        print("\n💡 Получите access token из:")
        print("   - Channel binding в админ панели")
        print("   - AWS Secrets Manager")
        return

    async with httpx.AsyncClient() as client:
        # Тест 1: Информация об аккаунте
        account_info = await test_account_info(client, WEBHOOK_ENTRY_ID, token)
        if not account_info:
            print("\n⚠️  Не удалось получить информацию об аккаунте")
            print("   Проверьте access token и Account ID")
            return

        # Тест 2: Список conversations
        conversations_response = await test_conversations_endpoint(
            client, WEBHOOK_ENTRY_ID, token
        )

        if conversations_response and "data" in conversations_response:
            conversations = conversations_response["data"]
            print(f"\n✅ Найдено conversations: {len(conversations)}")

            # Тест 3: Messages из первого conversation
            if conversations:
                first_conv_id = conversations[0].get("id")
                if first_conv_id:
                    print(f"\n📨 Тестируем получение messages из conversation: {first_conv_id}")
                    messages_response = await test_messages_endpoint(
                        client, first_conv_id, token
                    )

                    if messages_response and "data" in messages_response:
                        messages = messages_response["data"]
                        print(f"\n✅ Найдено messages: {len(messages)}")

                        # Ищем сообщение с нужным message_id
                        for msg in messages:
                            if msg.get("id") == MESSAGE_ID:
                                print("\n🎯 НАЙДЕНО СООБЩЕНИЕ!")
                                print(json.dumps(msg, indent=2, ensure_ascii=False))
                                if "from" in msg:
                                    print(f"\n✅ Sender ID найден: {msg.get('from', {}).get('id')}")
                                break

        # Тест 4: Прямое получение информации о сообщении
        await test_message_by_id(client, MESSAGE_ID, token)

    print("\n" + "=" * 80)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

