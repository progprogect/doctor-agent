#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отправки сообщений через Instagram Graph API.

Проверяет:
1. Валидность токена
2. Получение информации об аккаунте
3. Получение списка диалогов (если доступно)
4. Отправку тестового сообщения

Использование:
    python3 test_instagram_send.py [recipient_id]
    
    recipient_id - опциональный ID пользователя, которому отправить сообщение
"""

import asyncio
import json
import sys
from typing import Any, Optional

import httpx


# Конфигурация
INSTAGRAM_GRAPH_API_BASE = "https://graph.instagram.com/v21.0"
CHANNEL_ACCOUNT_ID = "17841458318357324"
ACCESS_TOKEN = "IGAAXjRiKjwKFBZAGFRU1RTcUdhU1UwYWhvTndCdWJNSEFGN1FEZA1M5N0Rhekp3MDE4NUpKanlwd1haSHpubmRFZAk8xbXF1UF9CRmRZATHRqWU44QURYVlcwZA2VhaVV1MngwYUdSeDRXVTdEcWhCNmhpLTR2S3NrRWxzQU5UcEQ5dwZDZD"

TEST_MESSAGE = "Тестовое сообщение от Doctor Agent. Это проверка отправки через API."


async def make_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: Optional[dict] = None,
    json_data: Optional[dict] = None,
) -> tuple[int, dict[str, Any]]:
    """Выполнить HTTP запрос и вернуть статус и JSON ответ."""
    print(f"\n{'='*80}")
    print(f"🔹 {method} {url}")
    if headers:
        print(f"Headers: {json.dumps({k: '***' if 'token' in k.lower() or 'authorization' in k.lower() else v for k, v in headers.items()}, indent=2)}")
    if json_data:
        print(f"Body: {json.dumps(json_data, indent=2, ensure_ascii=False)}")
    print(f"{'='*80}")
    
    try:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=json_data,
            timeout=30.0,
        )
        
        status_code = response.status_code
        try:
            response_data = response.json()
        except Exception:
            response_data = {"raw_text": response.text}
        
        print(f"\n✅ Status Code: {status_code}")
        print(f"Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        
        return status_code, response_data
    except httpx.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        return 0, {"error": str(e)}
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 0, {"error": str(e)}


async def test_token_validation(client: httpx.AsyncClient) -> tuple[bool, Optional[str]]:
    """Проверить валидность токена и получить информацию об аккаунте."""
    print("\n" + "="*80)
    print("📋 ЭТАП 1: Проверка токена и получение информации об аккаунте")
    print("="*80)
    
    url = f"{INSTAGRAM_GRAPH_API_BASE}/{CHANNEL_ACCOUNT_ID}"
    params = {"fields": "id,username"}
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    
    full_url = f"{url}?fields={params['fields']}"
    status, response = await make_request(client, "GET", full_url, headers=headers)
    
    if status == 200:
        account_id = response.get("id")
        username = response.get("username", "N/A")
        print(f"\n✅ Токен валиден!")
        print(f"   Account ID (из ответа): {account_id}")
        print(f"   Account ID (из запроса): {CHANNEL_ACCOUNT_ID}")
        print(f"   Username: {username}")
        if account_id != CHANNEL_ACCOUNT_ID:
            print(f"\n⚠️  ВНИМАНИЕ: Account ID в ответе отличается от используемого в запросе!")
            print(f"   Будем использовать Account ID из ответа API: {account_id}")
        return True, account_id
    else:
        error_message = response.get("error", {}).get("message", "Unknown error")
        error_code = response.get("error", {}).get("code", "Unknown")
        print(f"\n❌ Токен невалиден или ошибка доступа!")
        print(f"   Error Code: {error_code}")
        print(f"   Error Message: {error_message}")
        return False, None


async def find_user_id_by_username(
    client: httpx.AsyncClient, username: str
) -> Optional[str]:
    """Попытаться найти Instagram User ID по username через публичный API."""
    print("\n" + "="*80)
    print(f"📋 Поиск ID пользователя по username: {username}")
    print("="*80)
    
    # Пробуем получить ID через публичный Instagram API
    # (это неофициальный метод, может не работать из-за изменений в Instagram)
    print(f"\n🔍 Пробуем найти ID через публичный Instagram API...")
    
    try:
        # Убираем @ если есть
        clean_username = username.replace("@", "").strip()
        public_url = f"https://www.instagram.com/{clean_username}/?__a=1&__d=dis"
        
        print(f"   URL: {public_url}")
        
        # Используем обычный HTTP клиент без авторизации для публичного запроса
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as public_client:
            response = await public_client.get(public_url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Пытаемся извлечь ID из разных возможных структур ответа
                    user_id = None
                    
                    # Структура может быть разной в зависимости от версии API
                    if "graphql" in data and "user" in data["graphql"]:
                        user_id = data["graphql"]["user"].get("id")
                    elif "user" in data:
                        user_id = data["user"].get("id")
                    elif "id" in data:
                        user_id = data["id"]
                    
                    if user_id:
                        print(f"\n✅ Найден ID пользователя: {user_id}")
                        return str(user_id)
                    else:
                        print(f"\n⚠️  Не удалось извлечь ID из ответа")
                        print(f"   Попробуем альтернативный метод...")
                except json.JSONDecodeError:
                    print(f"\n⚠️  Instagram вернул HTML вместо JSON")
            elif response.status_code == 404:
                print(f"\n⚠️  Пользователь {clean_username} не найден (404)")
            else:
                print(f"\n⚠️  Ошибка при запросе: {response.status_code}")
                
    except Exception as e:
        print(f"\n⚠️  Ошибка при поиске ID: {e}")
    
    print(f"\n💡 Альтернативные способы получить ID:")
    print(f"   1. Использовать онлайн-сервис: https://www.otzberg.net/iguserid/")
    print(f"   2. Из webhook событий (когда пользователь пишет агенту)")
    print(f"   3. Из базы данных (если уже есть диалог с этим пользователем)")
    
    return None


async def get_conversations(client: httpx.AsyncClient, account_id: str) -> Optional[list[dict]]:
    """Попытаться получить список диалогов."""
    print("\n" + "="*80)
    print("📋 ЭТАП 2: Попытка получить список диалогов")
    print("="*80)
    
    # Используем правильный Account ID из ответа API
    # Попробуем несколько вариантов endpoints
    endpoints_to_try = [
        f"{INSTAGRAM_GRAPH_API_BASE}/{account_id}/conversations",
        f"{INSTAGRAM_GRAPH_API_BASE}/{account_id}/conversations?fields=participants,updated_time",
        f"https://graph.facebook.com/v21.0/{account_id}/conversations",
    ]
    
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    
    for endpoint in endpoints_to_try:
        print(f"\n🔍 Пробуем endpoint: {endpoint}")
        status, response = await make_request(client, "GET", endpoint, headers=headers)
        
        if status == 200:
            conversations = response.get("data", [])
            print(f"\n✅ Получено диалогов: {len(conversations)}")
            if conversations:
                print(f"   Первый диалог: {json.dumps(conversations[0], indent=2, ensure_ascii=False)}")
            return conversations
        elif status == 400 or status == 403:
            error_message = response.get("error", {}).get("message", "Unknown error")
            print(f"⚠️  Endpoint недоступен: {error_message}")
            continue
        else:
            print(f"⚠️  Неожиданный статус: {status}")
            continue
    
    print("\n⚠️  Не удалось получить список диалогов через стандартные endpoints")
    print("   Возможно, нужно использовать webhook события или другой метод")
    return None


async def extract_recipient_from_conversations(conversations: list[dict]) -> Optional[str]:
    """Извлечь recipient_id из списка диалогов."""
    if not conversations:
        return None
    
    print("\n" + "="*80)
    print("📋 ЭТАП 3: Извлечение получателя из диалогов")
    print("="*80)
    
    # Берем первый активный диалог
    conversation = conversations[0]
    print(f"\n📨 Анализируем диалог: {json.dumps(conversation, indent=2, ensure_ascii=False)}")
    
    # Пытаемся найти recipient_id в разных форматах
    recipient_id = None
    
    # Вариант 1: participants
    if "participants" in conversation:
        participants = conversation["participants"]
        if isinstance(participants, list) and len(participants) > 0:
            # Ищем участника, который не является нашим аккаунтом
            for participant in participants:
                participant_id = participant.get("id") if isinstance(participant, dict) else str(participant)
                if participant_id and participant_id != CHANNEL_ACCOUNT_ID:
                    recipient_id = participant_id
                    break
    
    # Вариант 2: participants.data
    if not recipient_id and "participants" in conversation:
        participants_data = conversation.get("participants", {}).get("data", [])
        if participants_data:
            for participant in participants_data:
                participant_id = participant.get("id")
                if participant_id and participant_id != CHANNEL_ACCOUNT_ID:
                    recipient_id = participant_id
                    break
    
    # Вариант 3: can_reply
    if not recipient_id and "can_reply" in conversation:
        # Если есть can_reply, значит это информация о диалоге
        # Нужно искать в других полях
        pass
    
    if recipient_id:
        print(f"\n✅ Найден получатель: {recipient_id}")
        return recipient_id
    else:
        print(f"\n⚠️  Не удалось извлечь recipient_id из диалога")
        print(f"   Структура диалога может отличаться от ожидаемой")
        return None


async def send_test_message(
    client: httpx.AsyncClient, recipient_id: str, account_id: str
) -> bool:
    """Отправить тестовое сообщение."""
    print("\n" + "="*80)
    print("📋 ЭТАП 4: Отправка тестового сообщения")
    print("="*80)
    
    # Пробуем оба варианта Account ID
    account_ids_to_try = [
        account_id,  # Из ответа API
        CHANNEL_ACCOUNT_ID,  # Исходный ID из конфигурации
    ]
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": TEST_MESSAGE},
    }
    
    for acc_id in account_ids_to_try:
        url = f"{INSTAGRAM_GRAPH_API_BASE}/{acc_id}/messages"
        print(f"\n🔍 Пробуем Account ID: {acc_id}")
        
        status, response = await make_request(client, "POST", url, headers=headers, json_data=payload)
        
        if status == 200:
            message_id = response.get("message_id") or response.get("id")
            print(f"\n✅ Сообщение успешно отправлено!")
            print(f"   Message ID: {message_id}")
            print(f"   Recipient ID: {recipient_id}")
            print(f"   Account ID (рабочий): {acc_id}")
            return True
        elif status == 400:
            error = response.get("error", {})
            error_code = error.get("code", "Unknown")
            error_subcode = error.get("error_subcode")
            
            # Если это ошибка "пользователь не найден", пробуем следующий Account ID
            if error_code == 100 and error_subcode == 2534014:
                print(f"   ⚠️  Пользователь не найден с Account ID {acc_id}, пробуем следующий...")
                continue
            else:
                # Другая ошибка - выводим и останавливаемся
                error_message = error.get("message", "Unknown error")
                error_type = error.get("type", "Unknown")
                
                print(f"\n❌ Ошибка при отправке сообщения!")
                print(f"   Error Code: {error_code}")
                print(f"   Error Subcode: {error_subcode}")
                print(f"   Error Type: {error_type}")
                print(f"   Error Message: {error_message}")
                
                if error_code == 10:  # Permission denied
                    print(f"\n💡 Возможные причины:")
                    print(f"   - Токен не имеет прав на отправку сообщений")
                    print(f"   - Нужны дополнительные permissions")
                elif error_code == 200:  # Invalid parameter
                    print(f"\n💡 Возможные причины:")
                    print(f"   - Неверный формат recipient_id")
                    print(f"   - Неверный формат сообщения")
                elif "24 hour" in error_message.lower() or "window" in error_message.lower():
                    print(f"\n💡 Возможные причины:")
                    print(f"   - Истекло 24-часовое окно для отправки сообщений")
                    print(f"   - Пользователь должен написать первым или написать недавно")
                
                return False
        else:
            # Другие статусы - выводим ошибку
            error = response.get("error", {})
            error_code = error.get("code", "Unknown")
            error_message = error.get("message", "Unknown error")
            print(f"\n❌ Ошибка: {status}")
            print(f"   Error Code: {error_code}")
            print(f"   Error Message: {error_message}")
            return False
    
    # Если все Account ID не сработали
    print(f"\n❌ Не удалось отправить сообщение ни с одним Account ID")
    print(f"💡 Возможные причины:")
    print(f"   1. 24-часовое окно истекло (пользователь должен написать недавно)")
    print(f"   2. Recipient ID неверный")
    print(f"   3. Токен не имеет необходимых прав")
    return False
    
    status, response = await make_request(client, "POST", url, headers=headers, json_data=payload)
    
    if status == 200:
        message_id = response.get("message_id") or response.get("id")
        print(f"\n✅ Сообщение успешно отправлено!")
        print(f"   Message ID: {message_id}")
        print(f"   Recipient ID: {recipient_id}")
        return True
    else:
        error = response.get("error", {})
        error_code = error.get("code", "Unknown")
        error_message = error.get("message", "Unknown error")
        error_type = error.get("type", "Unknown")
        
        print(f"\n❌ Ошибка при отправке сообщения!")
        print(f"   Error Code: {error_code}")
        print(f"   Error Type: {error_type}")
        print(f"   Error Message: {error_message}")
        
        # Дополнительная информация об ошибке
        if error_code == 10:  # Permission denied
            print(f"\n💡 Возможные причины:")
            print(f"   - Токен не имеет прав на отправку сообщений")
            print(f"   - Нужны дополнительные permissions")
        elif error_code == 200:  # Invalid parameter
            print(f"\n💡 Возможные причины:")
            print(f"   - Неверный формат recipient_id")
            print(f"   - Неверный формат сообщения")
        elif "24 hour" in error_message.lower() or "window" in error_message.lower():
            print(f"\n💡 Возможные причины:")
            print(f"   - Истекло 24-часовое окно для отправки сообщений")
            print(f"   - Пользователь должен написать первым или написать недавно")
        
        return False


async def main():
    """Основная функция тестирования."""
    # Проверяем аргументы командной строки
    recipient_id_from_args = None
    if len(sys.argv) > 1:
        recipient_id_from_args = sys.argv[1]
        print(f"\n📝 Получен recipient_id из аргументов: {recipient_id_from_args}")
    
    print("\n" + "="*80)
    print("🚀 ТЕСТИРОВАНИЕ INSTAGRAM GRAPH API")
    print("="*80)
    print(f"Channel Account ID: {CHANNEL_ACCOUNT_ID}")
    print(f"Access Token: {ACCESS_TOKEN[:20]}...")
    if recipient_id_from_args:
        print(f"Recipient ID (из аргументов): {recipient_id_from_args}")
    print("="*80)
    
    async with httpx.AsyncClient() as client:
        # Этап 1: Проверка токена
        token_valid, account_id = await test_token_validation(client)
        if not token_valid:
            print("\n❌ Тест остановлен: токен невалиден")
            return
        
        # Используем Account ID из ответа API
        actual_account_id = account_id or CHANNEL_ACCOUNT_ID
        
        # Этап 2: Получение диалогов
        conversations = await get_conversations(client, actual_account_id)
        
        # Этап 3: Извлечение получателя
        recipient_id = None
        if conversations:
            recipient_id = await extract_recipient_from_conversations(conversations)
        
        # Если не удалось получить из диалогов, попробуем получить из базы данных
        if not recipient_id:
            print("\n" + "="*80)
            print("📋 ЭТАП 2.5: Попытка получить recipient_id из базы данных")
            print("="*80)
            
            try:
                # Попробуем подключиться к базе данных и найти Instagram диалоги
                import os
                
                # Добавляем путь к backend для импорта
                backend_path = os.path.join(os.path.dirname(__file__), "backend")
                if backend_path not in sys.path:
                    sys.path.insert(0, backend_path)
                
                from app.storage.dynamodb import DynamoDBClient
                from app.models.conversation import ConversationStatus, MessageChannel
                from app.config import get_settings
                
                settings = get_settings()
                dynamodb = DynamoDBClient(settings)
                
                # Получаем все Instagram диалоги
                all_conversations = await dynamodb.list_conversations(limit=100)
                instagram_conversations = [
                    conv for conv in all_conversations
                    if (hasattr(conv.channel, 'value') and conv.channel.value == MessageChannel.INSTAGRAM.value)
                    or (isinstance(conv.channel, str) and conv.channel == MessageChannel.INSTAGRAM.value)
                ]
                
                if instagram_conversations:
                    # Берем первый активный диалог
                    active_conv = next(
                        (conv for conv in instagram_conversations 
                         if conv.external_user_id and 
                         (conv.status == ConversationStatus.AI_ACTIVE or 
                          conv.status == ConversationStatus.NEEDS_HUMAN)),
                        instagram_conversations[0]
                    )
                    
                    if active_conv.external_user_id:
                        recipient_id = active_conv.external_user_id
                        print(f"\n✅ Найден recipient_id из базы данных: {recipient_id}")
                        print(f"   Conversation ID: {active_conv.conversation_id}")
                        print(f"   Agent ID: {active_conv.agent_id}")
                        print(f"   Status: {active_conv.status}")
                    else:
                        print(f"\n⚠️  В диалоге нет external_user_id")
                else:
                    print(f"\n⚠️  В базе данных нет Instagram диалогов")
                    
            except Exception as e:
                print(f"\n⚠️  Не удалось подключиться к базе данных: {e}")
                print(f"   Продолжаем без использования базы данных")
        
        # Если все еще не удалось получить recipient_id, используем из аргументов
        if not recipient_id and recipient_id_from_args:
            # Проверяем, это username или уже ID
            if recipient_id_from_args.isdigit():
                recipient_id = recipient_id_from_args
                print(f"\n✅ Используем recipient_id из аргументов командной строки: {recipient_id}")
            else:
                # Это username, попробуем найти ID
                print(f"\n📝 Обнаружен username вместо ID: {recipient_id_from_args}")
                found_id = await find_user_id_by_username(client, recipient_id_from_args)
                if found_id:
                    recipient_id = found_id
                else:
                    print(f"\n⚠️  Не удалось автоматически найти ID для username: {recipient_id_from_args}")
                    print(f"   Попробуйте использовать числовой ID пользователя")
                    print(f"   (ID можно получить из webhook событий или базы данных)")
                    return
        
        # Если все еще не удалось получить recipient_id
        if not recipient_id:
            print("\n" + "="*80)
            print("⚠️  Не удалось автоматически определить recipient_id")
            print("="*80)
            print("\n💡 Альтернативные варианты:")
            print("   1. Использовать recipient_id из webhook событий (если они приходят)")
            print("   2. Использовать recipient_id из базы данных (если есть сохраненные диалоги)")
            print("   3. Попробовать отправить сообщение известному пользователю")
            print("\n   Для продолжения теста введите recipient_id вручную или")
            print("   используйте ID пользователя, который недавно писал агенту.")
            
            # Можно добавить интерактивный ввод, но для автоматизации пропустим
            print("\n⏭️  Пропускаем отправку сообщения (требуется recipient_id)")
            return
        
        # Этап 4: Отправка тестового сообщения
        success = await send_test_message(client, recipient_id, actual_account_id)
        
        # Итоги
        print("\n" + "="*80)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
        print("="*80)
        print(f"✅ Токен валиден: {token_valid}")
        print(f"✅ Диалоги получены: {conversations is not None}")
        print(f"✅ Recipient ID найден: {recipient_id is not None}")
        if recipient_id:
            print(f"✅ Сообщение отправлено: {success}")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

