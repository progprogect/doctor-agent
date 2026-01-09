#!/usr/bin/env python3
"""
Тестовый скрипт для отправки сообщения через Instagram API
используя данные из последнего webhook события.
"""

import asyncio
import json
import sys
from datetime import datetime

import httpx

# Конфигурация
API_BASE_URL = "http://localhost:8000"  # Локальный сервер
INSTAGRAM_GRAPH_API_BASE = "https://graph.instagram.com/v21.0"


async def get_last_webhook_event():
    """Получить последнее webhook событие через API."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE_URL}/api/v1/webhook-events/recent?limit=1")
            if response.status_code == 200:
                data = response.json()
                events = data.get("events", [])
                if events:
                    return events[-1]  # Последнее событие
                return None
            else:
                print(f"❌ Ошибка получения webhook событий: {response.status_code}")
                return None
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        print(f"   Убедитесь, что сервер запущен на {API_BASE_URL}")
        return None


async def get_channel_bindings():
    """Получить список channel bindings для получения access token."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Нужен admin token для этого endpoint
            # Для теста используем прямой запрос к DynamoDB или получаем через API
            response = await client.get(f"{API_BASE_URL}/api/v1/admin/channel-bindings")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️  Не удалось получить bindings через API: {response.status_code}")
                return None
    except Exception as e:
        print(f"⚠️  Ошибка получения bindings: {e}")
        return None


async def send_message_via_api(
    account_id: str, recipient_id: str, message_text: str, access_token: str
):
    """Отправить сообщение через Instagram Graph API."""
    url = f"{INSTAGRAM_GRAPH_API_BASE}/{account_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
    }

    print("\n" + "=" * 80)
    print("📤 ОТПРАВКА СООБЩЕНИЯ")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Account ID: {account_id}")
    print(f"Recipient ID: {recipient_id}")
    print(f"Message: {message_text}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print("=" * 80)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response_data = response.json()

            print(f"\nStatus Code: {response.status_code}")
            print(f"Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

            if response.status_code == 200:
                print("\n✅ Сообщение успешно отправлено!")
                return True
            else:
                error = response_data.get("error", {})
                error_code = error.get("code")
                error_subcode = error.get("error_subcode")
                error_message = error.get("message", "Unknown error")

                print(f"\n❌ Ошибка отправки:")
                print(f"   Code: {error_code}")
                print(f"   Subcode: {error_subcode}")
                print(f"   Message: {error_message}")

                # Попробуем Self Messaging формат
                if error_code == 100:
                    print("\n🔄 Пробую Self Messaging формат (без recipient)...")
                    return await send_self_messaging(
                        recipient_id, message_text, access_token
                    )

                return False
    except Exception as e:
        print(f"\n❌ Исключение при отправке: {e}")
        import traceback

        traceback.print_exc()
        return False


async def send_self_messaging(recipient_id: str, message_text: str, access_token: str):
    """Отправить сообщение в Self Messaging формате."""
    url = f"{INSTAGRAM_GRAPH_API_BASE}/{recipient_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {"message": {"text": message_text}}

    print(f"\nSelf Messaging URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response_data = response.json()

            print(f"\nStatus Code: {response.status_code}")
            print(f"Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

            if response.status_code == 200:
                print("\n✅ Сообщение успешно отправлено через Self Messaging!")
                return True
            else:
                error = response_data.get("error", {})
                print(f"\n❌ Self Messaging тоже не сработал:")
                print(f"   {error.get('code')} (subcode: {error.get('error_subcode')}): {error.get('message')}")
                return False
    except Exception as e:
        print(f"\n❌ Исключение при Self Messaging: {e}")
        return False


async def main():
    """Основная функция."""
    print("=" * 80)
    print("🧪 ТЕСТ ОТПРАВКИ СООБЩЕНИЯ ИЗ WEBHOOK")
    print("=" * 80)

    # 1. Получить последнее webhook событие
    print("\n📨 Получение последнего webhook события...")
    event = await get_last_webhook_event()

    if not event:
        print("❌ Webhook события не найдены")
        print("\n💡 Отправьте сообщение агенту в Instagram, чтобы получить webhook событие")
        return

    print(f"✅ Найдено webhook событие: {event.get('id')}")
    print(f"   Время: {event.get('timestamp')}")

    payload = event.get("payload", {})
    extracted = event.get("extracted", {})

    # 2. Извлечь ID из события
    sender_id = extracted.get("sender_id")
    recipient_id = extracted.get("recipient_id")  # Это наш Account ID
    event_type = extracted.get("event_type", "unknown")

    print(f"\n📋 Извлеченная информация:")
    print(f"   Event Type: {event_type}")
    print(f"   Sender ID: {sender_id or 'N/A'}")
    print(f"   Recipient ID (Account ID): {recipient_id or 'N/A'}")

    if event_type != "message":
        print(f"\n⚠️  Это событие типа '{event_type}', а не обычное сообщение")
        print("   Для отправки ответа нужно обычное сообщение с sender.id")
        print("\n💡 Отправьте новое сообщение агенту в Instagram")

        # Показываем структуру события для отладки
        print("\n📄 Структура события:")
        print(json.dumps(payload, indent=2, ensure_ascii=False)[:500] + "...")
        return

    if not sender_id:
        print("\n❌ Sender ID не найден в webhook событии")
        print("\n📄 Полный payload события:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    if not recipient_id:
        print("\n❌ Recipient ID (Account ID) не найден")
        print("   Нужен для отправки сообщения")
        return

    # 3. Получить access token
    # Для теста используем хардкод или получаем через API
    # В реальном сценарии нужно получить через channel binding service
    print("\n🔐 Получение access token...")
    print("   ⚠️  Для теста нужен access token из channel binding")
    print("   Используйте токен из настроек Instagram аккаунта")

    if len(sys.argv) > 1:
        access_token = sys.argv[1]
    else:
        print("\n❌ Access token не предоставлен")
        print("   Использование: python3 test_send_from_webhook.py <access_token>")
        print("\n💡 Получите access token из:")
        print("   - Channel binding в админ панели")
        print("   - AWS Secrets Manager")
        return

    # 4. Отправить тестовое сообщение
    message_text = "Тестовое сообщение от Doctor Agent (отправлено через API)"
    success = await send_message_via_api(
        account_id=recipient_id,
        recipient_id=sender_id,
        message_text=message_text,
        access_token=access_token,
    )

    if success:
        print("\n" + "=" * 80)
        print("✅ ТЕСТ УСПЕШЕН!")
        print("=" * 80)
        print(f"Сообщение отправлено пользователю {sender_id}")
    else:
        print("\n" + "=" * 80)
        print("❌ ТЕСТ НЕ УДАЛСЯ")
        print("=" * 80)
        print("\n💡 Возможные причины:")
        print("   1. 24-часовое окно ответов истекло")
        print("   2. Неправильный recipient_id (должен быть sender.id из webhook)")
        print("   3. Неправильный account_id (должен быть recipient.id из webhook)")
        print("   4. Access token недействителен или не имеет нужных разрешений")


if __name__ == "__main__":
    asyncio.run(main())

