#!/usr/bin/env python3
"""
Простой скрипт для мониторинга Instagram webhook через API.
Использует только httpx, без зависимостей от базы данных.
"""

import asyncio
import json
import time
from datetime import datetime

import httpx

API_BASE = "http://localhost:8000"
ADMIN_TOKEN = None  # Будет получен из переменных окружения или .env

async def get_admin_token():
    """Попытаться получить admin token."""
    import os
    
    # Пробуем из переменных окружения
    token = os.getenv("ADMIN_TOKEN")
    if token:
        return token
    
    # Пробуем из .env файла
    try:
        env_path = "backend/.env"
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("ADMIN_TOKEN") or line.startswith("admin_token"):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    return token
    except:
        pass
    
    return None

async def monitor_via_api():
    """Мониторинг через API."""
    print("\n" + "="*80)
    print("🔍 МОНИТОРИНГ INSTAGRAM СООБЩЕНИЙ ЧЕРЕЗ API")
    print("="*80)
    
    admin_token = await get_admin_token()
    if not admin_token:
        print("⚠️  Admin token не найден")
        print("💡 Установите ADMIN_TOKEN в переменных окружения или в backend/.env")
        print("\n🔄 Пробую мониторинг без авторизации (может не работать)...")
    else:
        print("✅ Admin token найден")
    
    print("\n⏳ Ожидание входящих сообщений...")
    print("   (Отправьте сообщение в Instagram агенту)")
    print("="*80)
    
    headers = {}
    if admin_token:
        headers["Authorization"] = f"Bearer {admin_token}"
    
    last_conversations = []
    check_count = 0
    
    print("\n🔄 Начинаю мониторинг (проверка каждые 2 секунды)...")
    print("   Нажмите Ctrl+C для остановки\n")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            while True:
                check_count += 1
                await asyncio.sleep(2)
                
                try:
                    # Получаем список диалогов
                    response = await client.get(
                        f"{API_BASE}/api/v1/admin/conversations?limit=50",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        conversations = response.json()
                        
                        # Фильтруем Instagram диалоги
                        instagram_convos = [
                            conv for conv in conversations
                            if conv.get("channel") == "instagram"
                        ]
                        
                        # Проверяем, появились ли новые или обновленные диалоги
                        if instagram_convos:
                            # Сортируем по updated_at
                            instagram_convos.sort(
                                key=lambda x: x.get("updated_at", x.get("created_at", "")),
                                reverse=True
                            )
                            
                            latest = instagram_convos[0]
                            latest_id = latest.get("conversation_id")
                            latest_update = latest.get("updated_at", latest.get("created_at", ""))
                            external_user_id = latest.get("external_user_id")
                            
                            # Проверяем, это новый диалог или обновление
                            found_in_last = any(
                                c.get("conversation_id") == latest_id 
                                for c in last_conversations
                            )
                            
                            if not found_in_last or (
                                last_conversations and 
                                latest_update > last_conversations[0].get("updated_at", "")
                            ):
                                print("\n" + "="*80)
                                print("🎉 ОБНАРУЖЕНО НОВОЕ/ОБНОВЛЕННОЕ СООБЩЕНИЕ!")
                                print("="*80)
                                print(f"📨 Conversation ID: {latest_id}")
                                print(f"🔹 Agent ID: {latest.get('agent_id')}")
                                print(f"🔹 Status: {latest.get('status')}")
                                print(f"🔹 Updated: {latest_update}")
                                
                                if external_user_id:
                                    print("\n" + "="*80)
                                    print(f"✅ НАЙДЕН RECIPIENT_ID (sender.id): {external_user_id}")
                                    print("="*80)
                                    print(f"\n💡 Используйте этот ID для теста:")
                                    print(f"   python3 test_instagram_send.py {external_user_id}")
                                    print("="*80)
                                    return external_user_id
                                else:
                                    print("⚠️  В диалоге нет external_user_id")
                            
                            last_conversations = instagram_convos
                        else:
                            if check_count % 10 == 0:
                                print(f"   ⏳ Проверка #{check_count}... (Instagram диалогов пока нет)")
                    elif response.status_code == 401:
                        if check_count == 1:
                            print("⚠️  Не авторизован. Продолжаю без авторизации...")
                    else:
                        if check_count % 20 == 0:
                            print(f"   ⚠️  Ошибка API: {response.status_code}")
                
                except Exception as e:
                    if check_count % 20 == 0:
                        print(f"   ⚠️  Ошибка запроса: {e}")
                
                # Показываем прогресс
                if check_count % 10 == 0:
                    print(f"   ⏳ Проверка #{check_count}... (ждем сообщение)")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Мониторинг остановлен пользователем")
        return None

if __name__ == "__main__":
    result = asyncio.run(monitor_via_api())
    if result:
        print(f"\n✅ Мониторинг завершен. Recipient ID: {result}")
    else:
        print("\n⚠️  Мониторинг завершен без результата")

