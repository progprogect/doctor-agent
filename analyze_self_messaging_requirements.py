#!/usr/bin/env python3
"""
Анализ требований для Self Messaging согласно документации.
"""

print("\n" + "="*80)
print("📖 АНАЛИЗ ТРЕБОВАНИЙ ДЛЯ SELF MESSAGING")
print("="*80)
print("Документация: https://developers.facebook.com/docs/instagram-platform/self-messaging")
print("="*80)

print("""
СОГЛАСНО ДОКУМЕНТАЦИИ:

1. ТРЕБОВАНИЯ:
   ✅ Instagram Professional account (у нас есть - BUSINESS)
   ✅ Business Messaging API access
   ✅ Webhooks configured for message events

2. КЛЮЧЕВОЙ МОМЕНТ:
   Для Self Messaging нужно использовать recipient ID из webhook события,
   где is_self = true и is_echo = true.
   
   Когда Instagram Professional аккаунт отправляет сообщение самому себе
   через Instagram app, приходит echo webhook с:
   - sender.id = Instagram User ID
   - recipient.id = Instagram-scoped ID
   - message.is_self = true
   - message.is_echo = true

3. ФОРМАТ ЗАПРОСА:
   POST /{INSTAGRAM_SCOPED_ID}/messages
   Body: {"message": {"text": "..."}}
   
   БЕЗ поля recipient! Используется INSTAGRAM_SCOPED_ID из webhook.

4. ВАЖНО:
   - INSTAGRAM_SCOPED_ID может отличаться от Account ID
   - Нужно получить его из webhook события с is_self=true
   - 24-часовое окно НЕ применяется для self messaging

5. ПРОБЛЕМА:
   Мы пытаемся использовать Account ID напрямую, но для Self Messaging
   нужен именно Instagram-scoped ID из webhook события.

РЕШЕНИЕ:
1. Отправьте сообщение самому себе через Instagram app (не через API)
2. Получите webhook событие с is_self=true
3. Используйте recipient.id из этого webhook как INSTAGRAM_SCOPED_ID
4. Отправьте сообщение через API используя этот ID БЕЗ поля recipient
""")

print("\n" + "="*80)
print("💡 ИНСТРУКЦИЯ ДЛЯ ТЕСТА")
print("="*80)
print("""
1. Откройте Instagram app на телефоне
2. Найдите свой аккаунт @beautician_test
3. Отправьте сообщение самому себе (в Direct Messages)
4. Проверьте логи сервера - должно прийти webhook событие с:
   - "is_self": true
   - "is_echo": true
   - recipient.id = Instagram-scoped ID (это и есть нужный ID!)

5. Используйте этот recipient.id для отправки через API:
   POST /{recipient.id}/messages
   Body: {"message": {"text": "..."}}
""")

print("\n" + "="*80)

