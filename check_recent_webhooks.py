#!/usr/bin/env python3
"""
Проверка последних webhook событий через API или базу данных.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta

# Добавляем путь к backend
backend_path = os.path.join(os.path.dirname(__file__), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from app.storage.dynamodb import DynamoDBClient
    from app.models.conversation import MessageChannel
    from app.config import get_settings
    
    async def check_recent_webhooks():
        """Проверить последние webhook события через базу данных."""
        print("\n" + "="*80)
        print("🔍 ПРОВЕРКА ПОСЛЕДНИХ INSTAGRAM СООБЩЕНИЙ")
        print("="*80)
        
        try:
            settings = get_settings()
            dynamodb = DynamoDBClient(settings)
            
            # Получаем все Instagram диалоги
            print("\n📋 Получаем список Instagram диалогов...")
            all_conversations = await dynamodb.list_conversations(limit=50)
            
            instagram_conversations = [
                conv for conv in all_conversations
                if (hasattr(conv.channel, 'value') and conv.channel.value == MessageChannel.INSTAGRAM.value)
                or (isinstance(conv.channel, str) and conv.channel == MessageChannel.INSTAGRAM.value)
            ]
            
            if not instagram_conversations:
                print("\n⚠️  Instagram диалогов не найдено")
                print("   Это может означать, что webhook не приходит или не обрабатывается")
                return None
            
            print(f"\n✅ Найдено Instagram диалогов: {len(instagram_conversations)}")
            
            # Сортируем по дате обновления
            instagram_conversations.sort(
                key=lambda x: x.updated_at if x.updated_at else x.created_at,
                reverse=True
            )
            
            # Берем последние 3 диалога
            for i, conv in enumerate(instagram_conversations[:3], 1):
                print(f"\n{'='*80}")
                print(f"📨 ДИАЛОГ #{i}")
                print(f"{'='*80}")
                print(f"Conversation ID: {conv.conversation_id}")
                print(f"Agent ID: {conv.agent_id}")
                print(f"Status: {conv.status}")
                print(f"External User ID: {conv.external_user_id}")
                print(f"Created: {conv.created_at}")
                print(f"Updated: {conv.updated_at}")
                
                # Получаем последние сообщения
                messages = await dynamodb.list_messages(
                    conversation_id=conv.conversation_id,
                    limit=5,
                    reverse=True
                )
                
                if messages:
                    print(f"\n📝 Последние сообщения ({len(messages)}):")
                    for msg in messages:
                        role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                        content_preview = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
                        timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S") if hasattr(msg.timestamp, 'strftime') else str(msg.timestamp)
                        print(f"   [{role}] {content_preview} ({timestamp})")
                        
                        # Проверяем, может быть это self message
                        if conv.external_user_id == "25638311079121978":  # Account ID
                            print(f"\n   ⚠️  ВНИМАНИЕ: external_user_id совпадает с Account ID!")
                            print(f"   Это может быть self message!")
                            print(f"   Instagram-scoped ID для Self Messaging может быть: {conv.external_user_id}")
                else:
                    print(f"   Сообщений пока нет")
            
            # Проверяем самый последний диалог
            latest = instagram_conversations[0]
            if latest.external_user_id:
                print(f"\n{'='*80}")
                print(f"✅ ПОСЛЕДНИЙ EXTERNAL_USER_ID: {latest.external_user_id}")
                print(f"{'='*80}")
                print(f"\n💡 Попробуйте использовать этот ID для Self Messaging:")
                print(f"   python3 test_self_messaging_with_id.py {latest.external_user_id}")
                print(f"{'='*80}")
                return latest.external_user_id
            
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    if __name__ == "__main__":
        result = asyncio.run(check_recent_webhooks())
        if not result:
            print("\n💡 Альтернативно, проверьте логи сервера вручную:")
            print("   Найдите строку: '🎯 SELF MESSAGING WEBHOOK ОБНАРУЖЕН!'")

except ImportError as e:
    print(f"\n⚠️  Не удалось импортировать модули: {e}")
    print("   Проверяю через API...")
    
    import httpx
    
    async def check_via_api():
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Пробуем health endpoint
            try:
                resp = await client.get("http://localhost:8000/health")
                print(f"Server status: {resp.status_code}")
            except:
                print("Server недоступен через API")
    
    asyncio.run(check_via_api())

