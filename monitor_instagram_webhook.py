#!/usr/bin/env python3
"""
Скрипт для мониторинга Instagram webhook событий в реальном времени.
Ждет входящих сообщений и выводит sender.id (recipient_id).
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

# Добавляем путь к backend
backend_path = os.path.join(os.path.dirname(__file__), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from app.storage.dynamodb import DynamoDBClient
    from app.models.conversation import MessageChannel
    from app.config import get_settings
    
    async def monitor_instagram_messages():
        """Мониторинг Instagram сообщений в реальном времени."""
        print("\n" + "="*80)
        print("🔍 МОНИТОРИНГ INSTAGRAM WEBHOOK СОБЫТИЙ")
        print("="*80)
        print("⏳ Ожидание входящих сообщений...")
        print("   (Отправьте сообщение в Instagram агенту)")
        print("="*80)
        
        try:
            settings = get_settings()
            dynamodb = DynamoDBClient(settings)
            
            # Получаем начальное состояние - последние сообщения
            print("\n📋 Проверяю текущее состояние диалогов...")
            all_conversations = await dynamodb.list_conversations(limit=100)
            
            instagram_conversations = [
                conv for conv in all_conversations
                if (hasattr(conv.channel, 'value') and conv.channel.value == MessageChannel.INSTAGRAM.value)
                or (isinstance(conv.channel, str) and conv.channel == MessageChannel.INSTAGRAM.value)
            ]
            
            # Запоминаем последнее время обновления
            last_update_time = None
            if instagram_conversations:
                instagram_conversations.sort(
                    key=lambda x: x.updated_at if x.updated_at else x.created_at,
                    reverse=True
                )
                last_conv = instagram_conversations[0]
                last_update_time = last_conv.updated_at or last_conv.created_at
                print(f"   Последнее обновление: {last_update_time}")
                if last_conv.external_user_id:
                    print(f"   Текущий external_user_id: {last_conv.external_user_id}")
            else:
                print("   Instagram диалогов пока нет")
            
            print("\n🔄 Начинаю мониторинг (проверка каждые 2 секунды)...")
            print("   Нажмите Ctrl+C для остановки\n")
            
            check_count = 0
            while True:
                check_count += 1
                await asyncio.sleep(2)  # Проверяем каждые 2 секунды
                
                # Получаем обновленный список диалогов
                all_conversations = await dynamodb.list_conversations(limit=100)
                instagram_conversations = [
                    conv for conv in all_conversations
                    if (hasattr(conv.channel, 'value') and conv.channel.value == MessageChannel.INSTAGRAM.value)
                    or (isinstance(conv.channel, str) and conv.channel == MessageChannel.INSTAGRAM.value)
                ]
                
                if instagram_conversations:
                    instagram_conversations.sort(
                        key=lambda x: x.updated_at if x.updated_at else x.created_at,
                        reverse=True
                    )
                    latest_conv = instagram_conversations[0]
                    latest_update_time = latest_conv.updated_at or latest_conv.created_at
                    
                    # Проверяем, появилось ли новое обновление
                    if last_update_time is None or latest_update_time > last_update_time:
                        print("\n" + "="*80)
                        print("🎉 ОБНАРУЖЕНО НОВОЕ СООБЩЕНИЕ!")
                        print("="*80)
                        print(f"📨 Conversation ID: {latest_conv.conversation_id}")
                        print(f"🔹 Agent ID: {latest_conv.agent_id}")
                        print(f"🔹 Status: {latest_conv.status}")
                        print(f"🔹 Updated: {latest_update_time}")
                        
                        if latest_conv.external_user_id:
                            print("\n" + "="*80)
                            print(f"✅ НАЙДЕН RECIPIENT_ID (sender.id): {latest_conv.external_user_id}")
                            print("="*80)
                            
                            # Получаем последние сообщения
                            messages = await dynamodb.list_messages(
                                conversation_id=latest_conv.conversation_id,
                                limit=3,
                                reverse=True
                            )
                            
                            if messages:
                                print(f"\n📝 Последние сообщения:")
                                for msg in messages:
                                    role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                                    content_preview = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
                                    timestamp = msg.timestamp.strftime("%H:%M:%S") if hasattr(msg.timestamp, 'strftime') else str(msg.timestamp)
                                    print(f"   [{role}] {content_preview} ({timestamp})")
                            
                            print("\n" + "="*80)
                            print(f"💡 Используйте этот ID для теста:")
                            print(f"   python3 test_instagram_send.py {latest_conv.external_user_id}")
                            print("="*80)
                            
                            return latest_conv.external_user_id
                        else:
                            print("⚠️  В диалоге нет external_user_id")
                    
                    last_update_time = latest_update_time
                
                # Показываем прогресс каждые 10 проверок (20 секунд)
                if check_count % 10 == 0:
                    print(f"   ⏳ Проверка #{check_count}... (ждем сообщение)")
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Мониторинг остановлен пользователем")
            return None
        except Exception as e:
            print(f"\n❌ Ошибка при мониторинге: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    if __name__ == "__main__":
        result = asyncio.run(monitor_instagram_messages())
        if result:
            print(f"\n✅ Мониторинг завершен. Recipient ID: {result}")
        else:
            print("\n⚠️  Мониторинг завершен без результата")

except ImportError as e:
    print(f"\n⚠️  Не удалось импортировать модули: {e}")
    print("   Убедитесь, что зависимости установлены:")
    print("   cd backend && pip install -r requirements.txt")
    print("\n💡 Альтернативно, проверьте логи сервера вручную в терминале")

