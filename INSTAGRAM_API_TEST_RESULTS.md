# Результаты тестирования Instagram Graph API

## Дата тестирования
2025-01-27

## Access Token
Использован предоставленный access token для аккаунта `dr.adamovich.ae`

## Результаты тестирования

### ✅ Тест 1: Получение информации об аккаунте
**Endpoint:** `GET /{account_id}?fields=id,username,account_type`

**Результат:** ✅ Успешно
```json
{
  "id": "25638311079121978",
  "username": "dr.adamovich.ae",
  "account_type": "BUSINESS"
}
```

**Вывод:** 
- Реальный Account ID: `25638311079121978`
- Account ID из webhook (`entry.id`): `17841458318357324` - это **другой идентификатор** (возможно Page ID или Instagram-scoped ID)

### ❌ Тест 2: Получение списка conversations
**Endpoint:** `GET /{account_id}/conversations?fields=id,participants,updated_time`

**Результат:** ❌ Пустой массив
```json
{
  "data": []
}
```

**Возможные причины:**
1. Conversations endpoint может быть недоступен для Instagram Graph API (deprecated)
2. Требуются дополнительные permissions
3. Нужно использовать другой endpoint или формат запроса
4. Conversations могут быть доступны только через webhook события

**Вывод:** Не удалось получить список conversations через Graph API.

### ❌ Тест 3: Получение messages из conversation
**Результат:** Пропущен (нет conversation ID)

**Причина:** Не удалось получить conversations в тесте 2.

### ❌ Тест 4: Прямое получение информации о сообщении
**Endpoint:** `GET /{message_id}?fields=id,from,to,message`

**Результат:** ❌ Пустой объект
```json
{}
```

**Вывод:** 
- Endpoint существует (не возвращает ошибку)
- Но не возвращает данные о сообщении
- Возможно, требуется другой формат запроса или permissions

### ❌ Тест 5: Facebook Graph API
**Endpoint:** `GET /{account_id}/conversations` через Facebook Graph API

**Результат:** ❌ Ошибка аутентификации
```json
{
  "error": {
    "message": "Invalid OAuth access token - Cannot parse access token",
    "type": "OAuthException",
    "code": 190
  }
}
```

**Вывод:** Instagram access token не работает с Facebook Graph API (ожидаемо).

## Ключевые выводы

### 1. Conversations API недоступен
- Endpoint `/conversations` возвращает пустой массив
- Не удалось получить список conversations для поиска sender_id

### 2. Message ID endpoint не работает
- Endpoint для получения информации о сообщении по `message_id` существует, но возвращает пустой объект
- Не удалось получить `sender_id` напрямую через Graph API

### 3. Разница в идентификаторах
- **Account ID из API:** `25638311079121978` (реальный Instagram Business Account ID)
- **entry.id из webhook:** `17841458318357324` (возможно Page ID или Instagram-scoped ID)
- Это может быть причиной проблем с поиском binding

## Рекомендации

### Решение 1: Проверить настройки webhook (ПРИОРИТЕТ)
**Действие:** Проверить в Facebook Developer Console:
1. Подписаны ли события типа `messages` (не только `message_edits`)
2. Активна ли подписка на `messages`
3. Проверить логи - приходят ли события типа `message` вообще

**Почему это важно:**
- Instagram может отправлять оба события: сначала `message_edit`, потом `message`
- Если событие `message` приходит, в нем будут `sender` и `recipient` ID

### Решение 2: Комбинированный подход
**Стратегия:**
1. При получении `message_edit` события:
   - Сохранить событие в очередь/таблицу ожидания с `message_id` и `entry.id`
   - Запустить таймер ожидания (например, 5-10 секунд)

2. Если приходит событие `message`:
   - Извлечь `sender_id` и `recipient_id`
   - Обработать сообщение нормально
   - Удалить из очереди ожидания

3. Если через таймаут не пришло событие `message`:
   - Логировать предупреждение
   - Пропустить обработку (или эскалировать)

**Преимущества:**
- Не требует дополнительных API запросов
- Использует данные, которые Instagram уже отправляет
- Минимальные изменения в коде

### Решение 3: Использовать entry.id для поиска binding
**Проблема:** В коде используется `entry.id` из webhook для поиска binding, но реальный Account ID отличается.

**Действие:** 
- Проверить, как сохраняется `channel_account_id` в binding
- Возможно, нужно сохранять оба ID (Account ID и Page ID)
- Или использовать `entry.id` для поиска binding вместо реального Account ID

### Решение 4: Альтернативные endpoints (для исследования)
**Возможные варианты:**
1. Использовать Page ID вместо Account ID для conversations endpoint
2. Проверить, есть ли endpoint для получения информации о conversation по message_id
3. Использовать Instagram Conversations API (если доступен)

## Следующие шаги

1. ✅ **Проверить логи webhook событий** - приходят ли события типа `message`?
2. ⏳ **Проверить настройки webhook** в Facebook Developer Console
3. ⏳ **Реализовать комбинированный подход** (Решение 2) - сохранять `message_edit` события и ждать `message`
4. ⏳ **Исправить поиск binding** - использовать правильный ID для поиска

## Вывод

**Основная проблема:** Instagram Graph API не предоставляет способ получить `sender_id` из `message_edit` события напрямую.

**Рекомендуемое решение:** Использовать комбинированный подход - сохранять `message_edit` события и ждать события `message`, которое должно содержать `sender` и `recipient` ID.

**Альтернатива:** Если события `message` не приходят вообще, нужно проверить настройки webhook в Facebook Developer Console и убедиться, что подписаны на правильные события.

