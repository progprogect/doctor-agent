# Настройка субдомена для Instagram Webhook

## Домен: elemental.ae

## Шаги настройки

### Шаг 1: Создать субдомен в DNS

**Рекомендуемые варианты субдомена:**
- `api.elemental.ae` - для API и webhook
- `webhook.elemental.ae` - специально для webhook
- `app.elemental.ae` - для приложения

**Что нужно сделать у регистратора домена:**

1. Зайти в панель управления DNS
2. Добавить новую A-запись (или CNAME):
   - **Тип:** A (или CNAME для Alias)
   - **Имя:** `api` (для api.elemental.ae)
   - **Значение:** `doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com`
   - **TTL:** 300 (или по умолчанию)

**Важно:** Если регистратор поддерживает Alias/ANAME записи для AWS, используйте их вместо обычной A-записи.

### Шаг 2: Создать SSL сертификат в AWS Certificate Manager

После создания DNS записи, создайте сертификат:

```bash
# Убедитесь, что AWS credentials настроены
# export AWS_ACCESS_KEY_ID="your_key"
# export AWS_SECRET_ACCESS_KEY="your_secret"
export AWS_DEFAULT_REGION="me-central-1"

# Создать сертификат для субдомена
aws acm request-certificate \
  --domain-name api.elemental.ae \
  --validation-method DNS \
  --region me-central-1
```

**Ответ будет содержать CertificateArn** - сохраните его!

### Шаг 3: Получить DNS валидационные записи

```bash
# Заменить CERTIFICATE_ARN на ARN из предыдущего шага
CERT_ARN="arn:aws:acm:me-central-1:760221990195:certificate/XXXXX"

# Получить валидационные записи
aws acm describe-certificate \
  --certificate-arn "$CERT_ARN" \
  --region me-central-1 \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord' \
  --output json
```

**Ответ будет содержать:**
```json
{
  "Name": "_xxxxx.api.elemental.ae",
  "Type": "CNAME",
  "Value": "_xxxxx.acm-validations.aws."
}
```

### Шаг 4: Добавить валидационные записи в DNS

В панели управления DNS у регистратора добавьте:

- **Тип:** CNAME
- **Имя:** `_xxxxx.api` (или полное имя из ответа)
- **Значение:** `_xxxxx.acm-validations.aws.` (из ответа)
- **TTL:** 300

### Шаг 5: Дождаться валидации

ACM проверит DNS записи (обычно 5-30 минут). Проверить статус:

```bash
aws acm describe-certificate \
  --certificate-arn "$CERT_ARN" \
  --region me-central-1 \
  --query 'Certificate.Status' \
  --output text
```

Должно быть: `ISSUED`

### Шаг 6: Обновить Terraform для использования нового сертификата

После валидации обновить `infra/alb_https.tf`:

```hcl
certificate_arn = "arn:aws:acm:me-central-1:760221990195:certificate/НОВЫЙ_ARN"
```

И применить изменения.

### Шаг 7: Обновить webhook URL в Facebook Developer Console

Использовать новый URL:
```
https://api.elemental.ae/api/v1/instagram/webhook
```

## Проверка после настройки

1. **Проверить DNS:**
   ```bash
   dig api.elemental.ae
   # Должен вернуть IP ALB
   ```

2. **Проверить HTTPS:**
   ```bash
   curl -I https://api.elemental.ae/api/v1/instagram/webhook
   # Должен вернуть HTTP 200 без предупреждений
   ```

3. **Проверить верификацию webhook:**
   ```bash
   curl "https://api.elemental.ae/api/v1/instagram/webhook?hub.mode=subscribe&hub.verify_token=RBrGdpk3pGB2LNJvte1vS6W-UN6S41b-GKC6r0ARXaE&hub.challenge=test123"
   # Должен вернуть: test123
   ```

## Важные моменты

1. **DNS распространение:** После добавления записей может занять 5-60 минут
2. **ACM валидация:** Обычно занимает 5-30 минут после добавления CNAME
3. **SSL сертификат:** Действителен 1 год, можно настроить автообновление
4. **Wildcard сертификат:** Можно создать `*.elemental.ae` для всех субдоменов

## Альтернатива: Wildcard сертификат

Если планируете использовать несколько субдоменов, создайте wildcard сертификат:

```bash
aws acm request-certificate \
  --domain-name "*.elemental.ae" \
  --subject-alternative-names "elemental.ae" \
  --validation-method DNS \
  --region me-central-1
```

Этот сертификат будет работать для всех субдоменов: `api.elemental.ae`, `webhook.elemental.ae`, `app.elemental.ae` и т.д.

