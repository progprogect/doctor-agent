#!/usr/bin/env python3
"""
Скрипт для проверки последнего Instagram сообщения и получения sender.id (recipient_id).
"""

import asyncio
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
    
    async def check_last_instagram_message():
        """Проверить последнее Instagram сообщение."""
        print("\n" + "="*80)
        print("🔍 ПОИСК ПОСЛЕДНЕГО INSTAGRAM СООБЩЕНИЯ")
        print("="*80)
        
        try:
            settings = get_settings()
            dynamodb = DynamoDBClient(settings)
            
            # Получаем все Instagram диалоги
            print("\n📋 Получаем список Instagram диалогов...")
            all_conversations = await dynamodb.list_conversations(limit=100)
            
            instagram_conversations = [
                conv for conv in all_conversations
                if (hasattr(conv.channel, 'value') and conv.channel.value == MessageChannel.INSTAGRAM.value)
                or (isinstance(conv.channel, str) and conv.channel == MessageChannel.INSTAGRAM.value)
            ]
            
            if not instagram_conversations:
                print("\n⚠️  Instagram диалогов не найдено в базе данных")
                return None
            
            print(f"\n✅ Найдено Instagram диалогов: {len(instagram_conversations)}")
            
            # Сортируем по дате обновления (последние первые)
            instagram_conversations.sort(
                key=lambda x: x.updated_at if x.updated_at else x.created_at,
                reverse=True
            )
            
            # Берем последний диалог
            last_conv = instagram_conversations[0]
            print(f"\n📨 Последний диалог:")
            print(f"   Conversation ID: {last_conv.conversation_id}")
            print(f"   Agent ID: {last_conv.agent_id}")
            print(f"   Status: {last_conv.status}")
            print(f"   External User ID (это recipient_id!): {last_conv.external_user_id}")
            print(f"   Created: {last_conv.created_at}")
            print(f"   Updated: {last_conv.updated_at}")
            
            if last_conv.external_user_id:
                print("\n" + "="*80)
                print(f"✅ НАЙДЕН RECIPIENT_ID: {last_conv.external_user_id}")
                print("="*80)
                print(f"\n💡 Используйте этот ID для отправки тестового сообщения:")
                print(f"   python3 test_instagram_send.py {last_conv.external_user_id}")
                print("="*80)
                
                # Получаем последние сообщения из этого диалога
                print(f"\n📝 Последние сообщения из диалога:")
                messages = await dynamodb.list_messages(
                    conversation_id=last_conv.conversation_id,
                    limit=5,
                    reverse=True
                )
                
                for msg in messages:
                    role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                    content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                    print(f"   [{role}] {content_preview} ({msg.timestamp})")
                
                return last_conv.external_user_id
            else:
                print("\n⚠️  В диалоге нет external_user_id")
                return None
                
        except Exception as e:
            print(f"\n❌ Ошибка при проверке базы данных: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    if __name__ == "__main__":
        result = asyncio.run(check_last_instagram_message())
        if not result:
            print("\n💡 Альтернативные способы получить recipient_id:")
            print("   1. Посмотрите логи сервера (где запущен uvicorn)")
            print("   2. Найдите строку с 'НАЙДЕН RECIPIENT_ID' в логах")
            print("   3. Или проверьте webhook события в Facebook Developer Console")

except ImportError as e:
    print(f"\n⚠️  Не удалось импортировать модули: {e}")
    print("   Убедитесь, что зависимости установлены:")
    print("   cd backend && pip install -r requirements.txt")
    print("\n💡 Альтернативно, проверьте логи сервера вручную:")
    print("   Найдите в логах строку: 'НАЙДЕН RECIPIENT_ID'")

