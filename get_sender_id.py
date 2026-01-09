#!/usr/bin/env python3
"""
Быстрая проверка последнего Instagram сообщения через API.
"""

import httpx
import json
import sys
import os

# Пробуем получить admin token
admin_token = os.getenv("ADMIN_TOKEN")

# Пробуем из .env файлов
for env_file in ["backend/.env", ".env"]:
    if os.path.exists(env_file):
        try:
            with open(env_file, "r") as f:
                for line in f:
                    if line.startswith("ADMIN_TOKEN") or line.startswith("admin_token"):
                        admin_token = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except:
            pass

if not admin_token:
    print("⚠️  Admin token не найден")
    print("💡 Проверьте логи сервера вручную - там должен быть sender.id")
    print("   Ищите строку: 'НАЙДЕН RECIPIENT_ID' или 'Sender ID'")
    sys.exit(1)

print("🔍 Проверяю последние Instagram диалоги...")

try:
    response = httpx.get(
        "http://localhost:8000/api/v1/admin/conversations?limit=20",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=5.0
    )
    
    if response.status_code == 200:
        conversations = response.json()
        instagram_convos = [c for c in conversations if c.get("channel") == "instagram"]
        
        if instagram_convos:
            # Сортируем по updated_at
            instagram_convos.sort(
                key=lambda x: x.get("updated_at", x.get("created_at", "")),
                reverse=True
            )
            
            latest = instagram_convos[0]
            user_id = latest.get("external_user_id")
            
            print("\n" + "="*80)
            print("📨 ПОСЛЕДНИЙ INSTAGRAM ДИАЛОГ")
            print("="*80)
            print(f"Conversation ID: {latest.get('conversation_id')}")
            print(f"Agent ID: {latest.get('agent_id')}")
            print(f"Status: {latest.get('status')}")
            print(f"Updated: {latest.get('updated_at')}")
            
            if user_id:
                print("\n" + "="*80)
                print(f"✅ НАЙДЕН RECIPIENT_ID (sender.id): {user_id}")
                print("="*80)
                print(f"\n💡 Используйте этот ID для теста:")
                print(f"   python3 test_instagram_send.py {user_id}")
                print("="*80)
            else:
                print("\n⚠️  В диалоге нет external_user_id")
                print("Полная информация о диалоге:")
                print(json.dumps(latest, indent=2, default=str))
        else:
            print("⚠️  Instagram диалогов не найдено")
            print(f"Всего диалогов: {len(conversations)}")
    else:
        print(f"❌ Ошибка API: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

