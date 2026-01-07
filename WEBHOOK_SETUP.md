# Настройка Instagram Webhook

## Шаг 1: Генерация верификационного токена

**Верификационный токен:**
```
RBrGdpk3pGB2LNJvte1vS6W-UN6S41b-GKC6r0ARXaE
```

Этот токен нужно использовать в Facebook Developer Console и в переменных окружения сервера.

## Шаг 2: Настройка в Facebook Developer Console

1. Перейдите в [Facebook Developers](https://developers.facebook.com/)
2. Выберите ваше приложение
3. Перейдите в **Instagram** → **Настроить** → **Шаг 2. Настройте Webhooks**
4. Заполните форму:

   **URL обратного вызова:**
   ```
   https://doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com/api/v1/instagram/webhook
   ```

   **Подтверждение маркера (Verify Token):**
   ```
   RBrGdpk3pGB2LNJvte1vS6W-UN6S41b-GKC6r0ARXaE
   ```

5. Нажмите **Подтвердить и сохранить**

## Шаг 3: Настройка переменных окружения на сервере

Добавьте токен в переменные окружения ECS задачи:

### Через AWS Console:

1. Перейдите в ECS → Clusters → doctor-agent-cluster → Services → doctor-agent-backend
2. Нажмите **Update**
3. В разделе **Environment** добавьте:
   - **Key:** `INSTAGRAM_WEBHOOK_VERIFY_TOKEN`
   - **Value:** `RBrGdpk3pGB2LNJvte1vS6W-UN6S41b-GKC6r0ARXaE`
4. Сохраните и дождитесь обновления сервиса

### Через AWS CLI:

```bash
# Получить текущую task definition
aws ecs describe-task-definition \
  --task-definition doctor-agent-backend \
  --region me-central-1 \
  --query 'taskDefinition' > task-definition.json

# Добавить переменную окружения в task-definition.json
# (отредактируйте файл вручную, добавив в containerDefinitions[0].environment)

# Зарегистрировать новую версию task definition
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json \
  --region me-central-1

# Обновить сервис
aws ecs update-service \
  --cluster doctor-agent-cluster \
  --service doctor-agent-backend \
  --task-definition doctor-agent-backend \
  --force-new-deployment \
  --region me-central-1
```

### Через Terraform (рекомендуется):

Добавьте в `infra/ecs.tf` в секцию `environment`:

```hcl
{
  name  = "INSTAGRAM_WEBHOOK_VERIFY_TOKEN"
  value = "RBrGdpk3pGB2LNJvte1vS6W-UN6S41b-GKC6r0ARXaE"
}
```

Или используйте Secrets Manager (более безопасно):

```hcl
{
  name      = "INSTAGRAM_WEBHOOK_VERIFY_TOKEN"
  valueFrom = aws_secretsmanager_secret.instagram_webhook_token.arn
}
```

## Шаг 4: Проверка верификации

После настройки в Facebook Developer Console, Meta отправит GET запрос:

```
GET /api/v1/instagram/webhook?hub.mode=subscribe&hub.verify_token=RBrGdpk3pGB2LNJvte1vS6W-UN6S41b-GKC6r0ARXaE&hub.challenge=RANDOM_STRING
```

Сервер должен ответить:
- **HTTP 200**
- **Body:** `RANDOM_STRING` (challenge string как есть)

### Тест вручную:

```bash
# Замените YOUR_TOKEN на ваш токен
curl "https://doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com/api/v1/instagram/webhook?hub.mode=subscribe&hub.verify_token=RBrGdpk3pGB2LNJvte1vS6W-UN6S41b-GKC6r0ARXaE&hub.challenge=test_challenge_123"
```

Должен вернуться: `test_challenge_123`

## Шаг 5: Подписка на события

После успешной верификации, в Facebook Developer Console:

1. Перейдите в **Webhooks** → **Instagram**
2. Выберите события для подписки:
   - ✅ **messages** - входящие сообщения
   - ✅ **messaging_postbacks** - ответы на кнопки
3. Сохраните изменения

## Проверка работы

### 1. Проверка логов верификации:

```bash
aws logs tail /ecs/doctor-agent --region me-central-1 --since 5m | grep -i "webhook.*verif"
```

Должны увидеть:
```
Instagram webhook verified successfully
Webhook verification successful, returning challenge: ...
```

### 2. Тест отправки сообщения:

Попросите пользователя написать сообщение агенту в Instagram. После этого проверьте логи:

```bash
aws logs tail /ecs/doctor-agent --region me-central-1 --since 5m | grep -E "(WEBHOOK|sender|recipient)"
```

Должны увидеть:
```
📨 INSTAGRAM WEBHOOK EVENT RECEIVED
🔹 Sender ID: ...
🔹 Recipient ID: ...
🔹 Message Text: ...
```

## Troubleshooting

### Проблема: Webhook не верифицируется (403 Forbidden)

**Причины:**
1. Токен не совпадает с настроенным в Facebook Developer Console
2. Токен не настроен в переменных окружения сервера
3. Неверный URL webhook

**Решение:**
1. Проверьте токен в Facebook Developer Console
2. Проверьте переменную окружения `INSTAGRAM_WEBHOOK_VERIFY_TOKEN` в ECS
3. Проверьте URL webhook (должен быть HTTPS)

### Проблема: Webhook верифицируется, но события не приходят

**Причины:**
1. Не выбраны события для подписки (messages, messaging_postbacks)
2. Пользователь не отправлял сообщения
3. Проблемы с доступностью URL

**Решение:**
1. Проверьте подписки в Facebook Developer Console
2. Попросите пользователя отправить тестовое сообщение
3. Проверьте доступность URL через curl

### Проблема: Сервер возвращает не challenge string

**Решение:**
Убедитесь, что endpoint возвращает challenge как plain text (не JSON):
```python
return Response(content=challenge, media_type="text/plain", status_code=200)
```

## Безопасность

⚠️ **Важно:** 
- Храните токен в Secrets Manager или переменных окружения
- Не коммитьте токен в git
- Используйте HTTPS для webhook URL
- Настройте проверку подписи webhook через `INSTAGRAM_APP_SECRET`

