# Анализ проблемы с message_edit событиями в Instagram webhook

## Проблема

При отправке нового сообщения пользователем в Instagram, мы получаем webhook событие типа `message_edit` с `num_edit: 0`, в котором **отсутствуют поля `sender` и `recipient`**. Без этих ID мы не можем отправить ответ пользователю.

### Пример получаемого события:

```json
{
  "object": "instagram",
  "entry": [
    {
      "time": 1767963330978,
      "id": "17841458318357324",  // ← Это Instagram Business Account ID
      "messaging": [
        {
          "timestamp": 1767963330889,
          "message_edit": {
            "mid": "aWdfZAG1faXRlbToxOklHTWVzc2FnZAUlEOjE3ODQxNDU4MzE4MzU3MzI0OjM0MDI4MjM2Njg0MTcxMDMwMTI0NDI3NjExODk0MjI3MzE3ODI0MTozMjYxMzE2NDUzNzQyMzA0ODA3ODk1NzgxNjE4Mzc4MzQyNAZDZD",
            "num_edit": 0  // ← 0 означает новое сообщение
          }
          // ❌ НЕТ sender и recipient!
        }
      ]
    }
  ]
}
```

## Что мы знаем

1. **Это известное поведение Instagram API**: Instagram отправляет `message_edit` с `num_edit: 0` для новых сообщений
2. **В событии нет sender/recipient ID**: Это основная проблема
3. **Instagram может отправить отдельное событие `message` позже**: Но это не гарантировано

## Возможные решения

### Решение 1: Использовать Instagram Graph API для получения информации о сообщении

**Гипотеза**: Можно получить информацию о сообщении через Graph API используя `message_id` (mid) из события.

**Endpoints для проверки:**

1. **GET /{ig-user-id}/conversations**
   - Получить список всех conversations
   - В каждом conversation есть `participants` с ID пользователей
   - Можно найти conversation по `message_id`

2. **GET /{conversation-id}/messages**
   - Получить сообщения из conversation
   - В каждом сообщении должен быть `sender` и `recipient`

3. **GET /{message-id}** (если такой endpoint существует)
   - Прямое получение информации о сообщении

**Проблемы:**
- Нужен `conversation_id` для получения messages
- Нужно знать, в каком conversation находится сообщение
- Может потребоваться дополнительный запрос для получения conversation_id

### Решение 2: Использовать entry.id как Account ID и искать в существующих conversations

**Гипотеза**: `entry.id` в webhook = Instagram Business Account ID. Можно использовать его для поиска активных conversations и получения sender_id из последних сообщений.

**Подход:**
1. Получить `entry.id` из webhook (это Account ID)
2. Найти все активные conversations для этого Account ID
3. Получить последние сообщения из этих conversations
4. Найти сообщение с соответствующим `message_id` (mid)
5. Извлечь `sender_id` из найденного сообщения

**Проблемы:**
- Если conversation еще не создана, не найдем sender_id
- Если сообщение первое в conversation, может не быть в истории

### Решение 3: Подписка на правильные webhook события

**Гипотеза**: Возможно, нужно настроить подписку на другие события в Facebook Developer Console.

**События для проверки:**
- `messages` - обычные сообщения (должны содержать sender/recipient)
- `message_edits` - редактирование сообщений (может не содержать sender/recipient)
- `message_reactions` - реакции на сообщения
- `message_unsends` - удаление сообщений

**Действия:**
1. Проверить текущие подписки в Facebook Developer Console
2. Убедиться, что подписаны на событие `messages`
3. Проверить, не отключено ли событие `messages` случайно

### Решение 4: Использовать Conversations API для получения участников

**Гипотеза**: Можно использовать Instagram Conversations API для получения списка участников conversation по message_id.

**Endpoints:**
- `GET /{ig-user-id}/conversations?fields=participants,messages`
- `GET /{conversation-id}?fields=participants`

**Проблемы:**
- Нужен `conversation_id`, который мы не знаем
- Может потребоваться перебор всех conversations

### Решение 5: Комбинированный подход

1. **При получении `message_edit` события:**
   - Сохранить событие в очередь/таблицу ожидания
   - Запустить фоновую задачу для поиска sender_id

2. **Фоновая задача:**
   - Использовать `entry.id` (Account ID) для поиска conversations
   - Получить последние сообщения через Graph API
   - Найти сообщение с соответствующим `message_id`
   - Извлечь `sender_id` и обработать сообщение

3. **Fallback:**
   - Если не удалось найти sender_id через API
   - Подождать дополнительное событие `message` от Instagram
   - Если через N секунд не пришло - пропустить или эскалировать

## Рекомендуемый план действий

### Этап 1: Проверка настроек webhook

1. Проверить Facebook Developer Console:
   - Какие события подписаны для Instagram webhook
   - Убедиться, что `messages` событие активно
   - Проверить, не отключено ли оно

2. Проверить логи:
   - Приходят ли события типа `message` вообще?
   - Или только `message_edit`?
   - Есть ли паттерн (например, сначала `message_edit`, потом `message`)?

### Этап 2: Исследование Graph API endpoints

Проверить следующие endpoints:

```bash
# 1. Получить список conversations
GET /{ig-user-id}/conversations?fields=id,participants,updated_time

# 2. Получить messages из conversation
GET /{conversation-id}/messages?fields=id,from,to,message,created_time

# 3. Получить информацию о конкретном сообщении (если endpoint существует)
GET /{message-id}?fields=from,to,message
```

### Этап 3: Реализация решения

**Вариант A: Если `messages` событие доступно**
- Настроить подписку на `messages` событие
- Обрабатывать только `messages` события для новых сообщений
- Игнорировать `message_edit` с `num_edit: 0` для новых сообщений

**Вариант B: Если только `message_edit` доступно**
- Реализовать фоновую задачу для получения sender_id через Graph API
- Использовать `entry.id` для поиска conversations
- Получать messages из conversations и искать по `message_id`

**Вариант C: Гибридный подход**
- Обрабатывать `message_edit` события
- Пытаться получить sender_id через Graph API
- Если не удалось - ждать события `message`
- Если через таймаут не пришло - логировать и пропускать

## Вопросы для исследования

1. **Есть ли endpoint для получения информации о сообщении по message_id?**
   - `GET /{message-id}` или подобный

2. **Можно ли получить conversation_id из message_id?**
   - Есть ли связь между ними в API

3. **Приходят ли события `message` вообще?**
   - Нужно проверить логи за длительный период

4. **Можно ли использовать entry.id для получения conversations?**
   - `GET /{entry.id}/conversations` - работает ли?

5. **Есть ли способ получить участников conversation без conversation_id?**
   - По message_id или другим параметрам

## Следующие шаги

1. ✅ Проверить настройки webhook в Facebook Developer Console
2. ✅ Проверить логи на наличие событий типа `message`
3. ⏳ Протестировать Graph API endpoints для получения информации о сообщениях
4. ⏳ Реализовать решение на основе найденной информации

