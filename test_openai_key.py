#!/usr/bin/env python3
"""Тестовый скрипт для проверки OpenAI API ключа."""

import json
import sys
import subprocess
from pathlib import Path

# Читаем ключ из временного файла
api_key_path = Path("/tmp/test_api_key.txt")
if not api_key_path.exists():
    print("❌ Файл с ключом не найден")
    sys.exit(1)

with open(api_key_path, "r") as f:
    api_key = f.read().strip()

print(f"📋 Получен ключ (первые 20 символов): {api_key[:20]}...")
print(f"📏 Длина ключа: {len(api_key)}")
print(f"🔍 Начинается с 'sk-': {api_key.startswith('sk-')}")

# Проверяем, не является ли ключ JSON строкой
if api_key.startswith('{'):
    print("⚠️  Ключ выглядит как JSON, пытаемся распарсить...")
    try:
        parsed = json.loads(api_key)
        if isinstance(parsed, dict):
            print(f"📦 Распарсенный JSON: {list(parsed.keys())}")
            if "OPENAI_API_KEY" in parsed:
                api_key = parsed["OPENAI_API_KEY"]
                print(f"✅ Извлечен ключ из JSON: {api_key[:20]}...")
    except json.JSONDecodeError:
        print("❌ Не удалось распарсить как JSON")

# Очистка ключа
api_key = api_key.strip().strip('"').strip("'")
print(f"🧹 После очистки (первые 20 символов): {api_key[:20]}...")

# Тест с OpenAI API через curl (не требует установки библиотек)
print("\n🧪 Тестируем подключение к OpenAI API через curl...")
import urllib.request
import urllib.parse

url = "https://api.openai.com/v1/chat/completions"
data = {
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Привет! Ответь одним словом: работает?"}],
    "max_tokens": 10
}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode('utf-8'),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        answer = result['choices'][0]['message']['content']
        print(f"✅ Успех! Ответ от OpenAI: {answer}")
        print("✅ Ключ работает корректно!")
except urllib.error.HTTPError as e:
    error_body = e.read().decode('utf-8')
    print(f"❌ Ошибка HTTP {e.code}: {error_body[:200]}")
    if "401" in str(e.code) or "Incorrect API key" in error_body:
        print(f"🔍 Проблема с ключом. Проверяем формат...")
        print(f"   Первые 50 символов: {repr(api_key[:50])}")
        print(f"   Последние 20 символов: {repr(api_key[-20:])}")
        print(f"   Длина: {len(api_key)}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Ошибка при тестировании: {type(e).__name__}: {e}")
    sys.exit(1)
