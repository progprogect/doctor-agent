# Исправления для обработки Instagram message_edit событий

## Проблема

Instagram отправляет события типа `message_edit` с `num_edit: 0` для новых сообщений, но без полей `sender` и `recipient`, что не позволяет отправить ответ пользователю.

## Внесенные изменения

### 1. Исправлена логика определения типа события (`backend/app/api/v1/instagram.py`)

**Было:**
- Неправильная проверка наличия поля `"message"` в событии
- Использование неопределенных переменных `is_self` и `is_echo` вне блока `if event_type == "message"`

**Стало:**
- Использование метода `_get_event_type()` из `InstagramService`, который правильно проверяет наличие `sender` и `recipient` первыми
- Правильная обработка переменных только внутри соответствующих блоков

### 2. Добавлена попытка получения sender_id через Graph API (`backend/app/services/instagram_service.py`)

**Новый метод:** `get_message_sender_from_api(account_id, message_id)`

**Логика:**
1. Получает binding по `account_id` (Page ID из webhook)
2. Получает access token из binding
3. Пробует несколько вариантов endpoints для получения conversations:
   - `/{instagram_account_id}/conversations`
   - `/{page_id}/conversations`
4. Для каждой conversation получает messages
5. Ищет сообщение с нужным `message_id`
6. Извлекает `sender_id` из поля `from.id`

**Вызывается из:** `backend/app/api/v1/instagram.py` при получении `message_edit` события с `num_edit: 0`

### 3. Улучшено логирование

- Добавлено логирование попыток получения sender_id через Graph API
- Улучшена читаемость логов с правильным форматированием

## Как это работает

1. При получении webhook события:
   - Используется правильный метод `_get_event_type()` для определения типа
   - Если событие типа `message` - обрабатывается нормально
   - Если событие типа `message_edit` с `num_edit: 0`:
     - Логируется предупреждение
     - Вызывается `get_message_sender_from_api()` для попытки получить sender_id
     - Если sender_id получен - можно обработать сообщение
     - Если нет - ждем события `message` от Instagram

## Следующие шаги

1. Протестировать на реальных webhook событиях
2. Если Graph API не возвращает conversations, рассмотреть альтернативные подходы:
   - Сохранение message_edit событий в очередь ожидания
   - Ожидание события `message` от Instagram
   - Использование других endpoints Graph API

## Файлы изменены

- `backend/app/api/v1/instagram.py` - исправлена логика обработки webhook событий
- `backend/app/services/instagram_service.py` - добавлен метод `get_message_sender_from_api()`

