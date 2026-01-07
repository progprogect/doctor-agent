# Диагностика Instagram Webhook

## Проблема: Webhook не получается

### Текущая ситуация

1. **Ошибка отправки сообщений**: `100 (subcode: 2534014) - User not found`
   - Это означает, что либо:
     - 24-часовое окно ответов истекло
     - Неверный `recipient_id`
     - Пользователь не имеет активного диалога с агентом

2. **Webhook не приходит**: 
   - Возможные причины:
     - Webhook не настроен в Facebook Developer Console
     - Webhook URL недоступен для Instagram
     - Неверный verify token

## Проверка конфигурации Webhook

### 1. Проверка на сервере

После деплоя нового кода (через 3-5 минут):

```bash
# Проверка конфигурации
curl http://doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com/api/v1/webhook-test/check-config

# Проверка доступности webhook endpoint
curl http://doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com/api/v1/instagram/webhook
```

### 2. Проверка в Facebook Developer Console

1. Перейдите в [Facebook Developers](https://developers.facebook.com/)
2. Выберите ваше приложение
3. Перейдите в **Webhooks** → **Instagram**
4. Проверьте:
   - **Callback URL**: `https://doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com/api/v1/instagram/webhook`
   - **Verify Token**: должен совпадать с `INSTAGRAM_WEBHOOK_VERIFY_TOKEN` в настройках
   - **Subscription Fields**: должны быть выбраны `messages` и `messaging_postbacks`

### 3. Тест верификации Webhook

Instagram отправляет GET запрос для верификации:

```
GET /api/v1/instagram/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=CHALLENGE_STRING
```

Проверить можно вручную:

```bash
# Замените YOUR_TOKEN на ваш verify token
curl "http://doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com/api/v1/instagram/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test123"
```

Должен вернуться `test123` (challenge string).

## Тестирование Webhook

### Вариант 1: Симуляция через API

После деплоя:

```bash
# Симуляция webhook события
curl -X POST http://doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com/api/v1/webhook-test/simulate-instagram \
  -H "Content-Type: application/json" \
  -d '{
    "object": "instagram",
    "entry": [{
      "messaging": [{
        "sender": {"id": "62670099264"},
        "recipient": {"id": "25638311079121978"},
        "message": {
          "text": "Тестовое сообщение",
          "mid": "test_message_id"
        }
      }]
    }]
  }'
```

### Вариант 2: Реальный тест через Instagram

1. Откройте Instagram app
2. Найдите аккаунт агента (`beautician_test`)
3. Отправьте сообщение агенту
4. Проверьте логи сервера:

```bash
aws logs tail /ecs/doctor-agent --region me-central-1 --since 5m | grep -E "(WEBHOOK|instagram|sender)"
```

### Вариант 3: Использование Facebook Graph API Explorer

1. Перейдите в [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Выберите ваше приложение
3. Используйте endpoint для отправки тестового сообщения (требует активного диалога)

## Проверка логов

### Логи сервера

```bash
# Все логи за последние 10 минут
aws logs tail /ecs/doctor-agent --region me-central-1 --since 10m

# Только webhook события
aws logs tail /ecs/doctor-agent --region me-central-1 --since 10m | grep -i "webhook"

# Ошибки
aws logs tail /ecs/doctor-agent --region me-central-1 --since 10m | grep -i "error"
```

### Что искать в логах

1. **Успешная верификация webhook**:
   ```
   Instagram webhook verified successfully
   ```

2. **Входящее webhook событие**:
   ```
   📨 INSTAGRAM WEBHOOK EVENT RECEIVED
   🔹 Sender ID: ...
   🔹 Recipient ID: ...
   🔹 Message Text: ...
   ```

3. **Ошибки**:
   ```
   Instagram webhook signature verification failed
   Error handling Instagram webhook event
   ```

## Решение проблемы с отправкой сообщений

### Проблема: "User not found" (код 100)

**Причины:**
1. **24-часовое окно**: Пользователь не писал агенту в последние 24 часа
2. **Неверный recipient_id**: ID пользователя неверный или не соответствует Instagram-scoped ID
3. **Нет активного диалога**: Пользователь никогда не писал агенту

**Решения:**

1. **Попросите пользователя написать сообщение агенту**:
   - Это откроет 24-часовое окно для ответов
   - Webhook событие придет на сервер
   - Из webhook можно получить правильный `sender.id` (это и есть `recipient_id` для ответа)

2. **Используйте Self Messaging для тестирования**:
   - Отправьте сообщение самому себе через Instagram app
   - Webhook событие будет содержать `is_self: true` и `is_echo: true`
   - Используйте `recipient.id` из этого webhook как Instagram-scoped ID
   - Отправляйте сообщения БЕЗ поля `recipient` (формат Self Messaging)

3. **Проверьте правильность recipient_id**:
   - `recipient_id` должен быть Instagram User ID (не Instagram Business Account ID)
   - Получить его можно только из webhook события (`sender.id`)
   - Или через Conversations API (если есть активные диалоги)

## Настройка переменных окружения

Убедитесь, что в AWS Secrets Manager или переменных окружения ECS настроены:

- `INSTAGRAM_WEBHOOK_VERIFY_TOKEN` - токен для верификации webhook
- `INSTAGRAM_APP_SECRET` - секрет приложения для проверки подписи (опционально)

Проверить можно через:

```bash
aws ecs describe-task-definition \
  --task-definition doctor-agent-backend \
  --region me-central-1 \
  --query 'taskDefinition.containerDefinitions[0].environment' \
  --output json
```

## Следующие шаги

1. ✅ Дождаться завершения деплоя (3-5 минут)
2. ✅ Проверить конфигурацию webhook через `/api/v1/webhook-test/check-config`
3. ✅ Настроить webhook в Facebook Developer Console
4. ✅ Попросить пользователя написать сообщение агенту
5. ✅ Проверить логи для webhook событий
6. ✅ Использовать `sender.id` из webhook для отправки ответа

