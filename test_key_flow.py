#!/usr/bin/env python3
"""Тестовый скрипт для проверки получения и обработки OpenAI API ключа."""

import json
import sys
import os
import asyncio
from pathlib import Path

# Добавляем путь к backend для импорта
sys.path.insert(0, str(Path(__file__).parent / "backend"))

async def main():
    print("=" * 80)
    print("ТЕСТ 1: Получение ключа из Secrets Manager (как в приложении)")
    print("=" * 80)

    try:
        from app.storage.secrets import SecretsManager
        from app.config import get_settings
        
        settings = get_settings()
        secrets_manager = SecretsManager(settings)
        
        # Получаем ключ так же, как в приложении
        print(f"\n1. Получаем ключ через get_openai_api_key()...")
        api_key_1 = await secrets_manager.get_openai_api_key()
        print(f"   Тип: {type(api_key_1)}")
        print(f"   Длина: {len(api_key_1)}")
        print(f"   Первые 30 символов: {repr(api_key_1[:30])}")
        print(f"   Последние 20 символов: {repr(api_key_1[-20:])}")
        print(f"   Начинается с 'sk-': {api_key_1.startswith('sk-')}")
        
        # Проверяем, не является ли это JSON строкой
        if api_key_1.startswith('{'):
            print(f"   ⚠️  Ключ выглядит как JSON!")
            try:
                parsed = json.loads(api_key_1)
                print(f"   Распарсенный JSON: {type(parsed)}")
                if isinstance(parsed, dict):
                    print(f"   Ключи в JSON: {list(parsed.keys())}")
            except:
                pass
        
        print("\n" + "=" * 80)
        print("ТЕСТ 2: Получение через get_secret() напрямую")
        print("=" * 80)
        
        print(f"\n2. Получаем ключ через get_secret()...")
        secret_name = settings.secrets_manager_openai_key_name
        print(f"   Имя секрета: {secret_name}")
        
        # Очищаем кеш
        secrets_manager.clear_cache(secret_name)
        
        api_key_2 = await secrets_manager.get_secret(secret_name)
        print(f"   Тип: {type(api_key_2)}")
        print(f"   Длина: {len(api_key_2)}")
        print(f"   Первые 30 символов: {repr(api_key_2[:30])}")
        print(f"   Последние 20 символов: {repr(api_key_2[-20:])}")
        print(f"   Начинается с 'sk-': {api_key_2.startswith('sk-')}")
        
        # Проверяем кеш
        print(f"\n3. Проверяем кеш...")
        if secret_name in secrets_manager._cache:
            cached = secrets_manager._cache[secret_name]
            print(f"   Кеш существует")
            print(f"   Тип в кеше: {type(cached)}")
            print(f"   Длина в кеше: {len(cached)}")
            print(f"   Первые 30 символов в кеше: {repr(cached[:30])}")
            print(f"   Начинается с 'sk-': {cached.startswith('sk-')}")
        else:
            print(f"   Кеш пуст")
        
        print("\n" + "=" * 80)
        print("ТЕСТ 3: Создание LLMFactory и получение клиента")
        print("=" * 80)
        
        from app.utils.openai_client import LLMFactory
        
        llm_factory = LLMFactory(settings, secrets_manager)
        
        print(f"\n4. Получаем клиент через LLMFactory.get_client()...")
        client = await llm_factory.get_client()
        
        print(f"   Тип клиента: {type(client)}")
        print(f"   API ключ в клиенте:")
        print(f"     Тип: {type(client.api_key)}")
        print(f"     Длина: {len(client.api_key)}")
        print(f"     Первые 30 символов: {repr(client.api_key[:30])}")
        print(f"     Последние 20 символов: {repr(client.api_key[-20:])}")
        print(f"     Начинается с 'sk-': {client.api_key.startswith('sk-')}")
        
        # Проверяем кеш клиентов
        print(f"\n5. Проверяем кеш клиентов...")
        if "default" in llm_factory._clients:
            cached_client = llm_factory._clients["default"]
            cached_key = cached_client.api_key
            print(f"   Кеш клиентов существует")
            print(f"   API ключ в кешированном клиенте:")
            print(f"     Тип: {type(cached_key)}")
            print(f"     Длина: {len(cached_key)}")
            print(f"     Первые 30 символов: {repr(cached_key[:30])}")
            print(f"     Начинается с 'sk-': {cached_key.startswith('sk-')}")
        else:
            print(f"   Кеш клиентов пуст")
        
        print("\n" + "=" * 80)
        print("ТЕСТ 4: Проверка async_client (создание OpenAI клиента)")
        print("=" * 80)
        
        print(f"\n6. Проверяем async_client...")
        async_client = client.async_client
        print(f"   Тип async_client: {type(async_client)}")
        
        # Проверяем, какой ключ используется в async_client
        # OpenAI клиент хранит ключ в _client._api_key или подобном атрибуте
        if hasattr(async_client, '_client'):
            if hasattr(async_client._client, '_api_key'):
                actual_key = async_client._client._api_key
                print(f"   API ключ в OpenAI клиенте:")
                print(f"     Тип: {type(actual_key)}")
                print(f"     Длина: {len(actual_key)}")
                print(f"     Первые 30 символов: {repr(actual_key[:30])}")
                print(f"     Последние 20 символов: {repr(actual_key[-20:])}")
                print(f"     Начинается с 'sk-': {actual_key.startswith('sk-') if isinstance(actual_key, str) else False}")
        
        print("\n" + "=" * 80)
        print("ТЕСТ 5: Прямой запрос к OpenAI API")
        print("=" * 80)
        
        print(f"\n7. Тестируем запрос к OpenAI API...")
        try:
            response = await client.async_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Ответь одним словом: работает?"}],
                max_tokens=10
            )
            answer = response.choices[0].message.content
            print(f"   ✅ Успех! Ответ: {answer}")
        except Exception as e:
            print(f"   ❌ Ошибка: {type(e).__name__}: {e}")
            error_str = str(e)
            if "api_key" in error_str.lower() or "401" in error_str:
                print(f"   🔍 Детали ошибки:")
                print(f"      {error_str[:500]}")
        
        print("\n" + "=" * 80)
        print("ТЕСТ 6: Проверка ChatOpenAI (как в agent_chain)")
        print("=" * 80)
        
        print(f"\n8. Тестируем ChatOpenAI с ключом...")
        try:
            from langchain_openai import ChatOpenAI
            
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.2,
                max_tokens=10,
                openai_api_key=client.api_key,
                timeout=30,
            )
            print(f"   ChatOpenAI создан успешно")
            print(f"   Проверяем ключ в ChatOpenAI...")
            
            # Попробуем получить ключ из ChatOpenAI
            if hasattr(llm, 'openai_api_key'):
                llm_key = llm.openai_api_key
                print(f"     openai_api_key: {type(llm_key)}, длина: {len(llm_key) if isinstance(llm_key, str) else 'N/A'}")
                print(f"     Первые 30 символов: {repr(str(llm_key)[:30])}")
            
            if hasattr(llm, 'client'):
                if hasattr(llm.client, 'api_key'):
                    llm_client_key = llm.client.api_key
                    print(f"     llm.client.api_key: {type(llm_client_key)}, длина: {len(llm_client_key) if isinstance(llm_client_key, str) else 'N/A'}")
                    print(f"     Первые 30 символов: {repr(str(llm_client_key)[:30])}")
            
            # Тестируем вызов
            print(f"\n9. Тестируем вызов ChatOpenAI...")
            response = await llm.ainvoke("Ответь одним словом: работает?")
            print(f"   ✅ Успех! Ответ: {response.content}")
        except Exception as e:
            print(f"   ❌ Ошибка: {type(e).__name__}: {e}")
            error_str = str(e)
            if "api_key" in error_str.lower() or "401" in error_str:
                print(f"   🔍 Детали ошибки:")
                print(f"      {error_str[:500]}")
        
        print("\n" + "=" * 80)
        print("РЕЗЮМЕ")
        print("=" * 80)
        
        print(f"\nСравнение ключей на разных этапах:")
        print(f"1. get_openai_api_key(): {api_key_1[:20]}... (длина: {len(api_key_1)})")
        print(f"2. get_secret(): {api_key_2[:20]}... (длина: {len(api_key_2)})")
        print(f"3. client.api_key: {client.api_key[:20]}... (длина: {len(client.api_key)})")
        
        if api_key_1 == api_key_2 == client.api_key:
            print(f"\n✅ Все ключи идентичны")
        else:
            print(f"\n⚠️  Ключи различаются!")
            if api_key_1 != api_key_2:
                print(f"   Разница между 1 и 2")
            if api_key_2 != client.api_key:
                print(f"   Разница между 2 и 3")
            if api_key_1 != client.api_key:
                print(f"   Разница между 1 и 3")
    
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
