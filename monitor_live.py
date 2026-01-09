#!/usr/bin/env python3
"""
Мониторинг Instagram сообщений в реальном времени через API.
Ждет, пока пользователь отправит сообщение, и сразу показывает sender.id.
"""

import asyncio
import json
import time
from datetime import datetime

import httpx

API_BASE = "http://localhost:8000"

async def monitor_live():
    """Мониторинг в реальном времени."""
    print("\n" + "="*80)
    print("🔍 МОНИТОРИНГ INSTAGRAM СООБЩЕНИЙ В РЕАЛЬНОМ ВРЕМЕНИ")
    print("="*80)
    print("⏳ Ожидание входящих сообщений...")
    print("   👉 ОТПРАВЬТЕ СООБЩЕНИЕ В INSTAGRAM АГЕНТУ СЕЙЧАС!")
    print("="*80)
    
    # Пробуем получить admin token
    admin_token = None
    try:
        import os
        # Пробуем из переменных окружения
        admin_token = os.getenv("ADMIN_TOKEN")
        
        # Пробуем из .env файлов
        for env_file in ["backend/.env", ".env"]:
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        if line.startswith("ADMIN_TOKEN") or line.startswith("admin_token"):
                            admin_token = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
            except:
                pass
    except:
        pass
    
    if not admin_token:
        print("\n⚠️  Admin token не найден, но продолжаю мониторинг...")
        print("   (Может не работать без авторизации)")
    
    headers = {}
    if admin_token:
        headers["Authorization"] = f"Bearer {admin_token}"
    
    last_conversations = []
    check_count = 0
    start_time = time.time()
    
    print("\n🔄 Начинаю мониторинг (проверка каждую секунду)...")
    print("   Нажмите Ctrl+C для остановки\n")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            while True:
                check_count += 1
                await asyncio.sleep(1)  # Проверяем каждую секунду
                
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
                            
                            last_update_time = None
                            if last_conversations:
                                last_update_time = last_conversations[0].get("updated_at", "")
                            
                            if not found_in_last or (last_update_time and latest_update > last_update_time):
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
                                    
                                    # Получаем последние сообщения
                                    try:
                                        msg_response = await client.get(
                                            f"{API_BASE}/api/v1/chat/conversations/{latest_id}/messages",
                                            headers=headers
                                        )
                                        if msg_response.status_code == 200:
                                            messages = msg_response.json()
                                            if messages:
                                                print(f"\n📝 Последние сообщения:")
                                                for msg in messages[-3:]:  # Последние 3
                                                    role = msg.get("role", "unknown")
                                                    content = msg.get("content", "")[:60]
                                                    timestamp = msg.get("timestamp", "")
                                                    print(f"   [{role}] {content}... ({timestamp})")
                                    except:
                                        pass
                                    
                                    print(f"\n💡 Используйте этот ID для теста:")
                                    print(f"   python3 test_instagram_send.py {external_user_id}")
                                    print("="*80)
                                    
                                    return external_user_id
                                else:
                                    print("⚠️  В диалоге нет external_user_id")
                                    print(f"Полная информация о диалоге:")
                                    print(json.dumps(latest, indent=2, default=str))
                            
                            last_conversations = instagram_convos
                        else:
                            if check_count % 10 == 0:
                                elapsed = int(time.time() - start_time)
                                print(f"   ⏳ Проверка #{check_count}... ({elapsed}с) - Instagram диалогов пока нет")
                    elif response.status_code == 401:
                        if check_count == 1:
                            print("⚠️  Не авторизован. Продолжаю без авторизации...")
                        if check_count % 30 == 0:
                            print(f"   ⏳ Проверка #{check_count}... (без авторизации)")
                    else:
                        if check_count % 30 == 0:
                            print(f"   ⚠️  Ошибка API: {response.status_code}")
                
                except Exception as e:
                    if check_count % 30 == 0:
                        print(f"   ⚠️  Ошибка запроса: {e}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Мониторинг остановлен")
        return None

if __name__ == "__main__":
    print("🚀 Запуск мониторинга...")
    print("   Отправьте сообщение в Instagram агенту, и я сразу найду sender.id!")
    result = asyncio.run(monitor_live())
    if result:
        print(f"\n✅ Мониторинг завершен. Recipient ID: {result}")
    else:
        print("\n⚠️  Мониторинг завершен без результата")

