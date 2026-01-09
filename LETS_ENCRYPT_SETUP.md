# Настройка Let's Encrypt SSL сертификата для agents.elemental.ae

## Обзор процесса

Let's Encrypt предоставляет бесплатные SSL сертификаты, которые можно использовать с AWS ALB через импорт в AWS Certificate Manager (ACM).

**Важно:** ALB требует сертификат из ACM, поэтому процесс:
1. Получить сертификат Let's Encrypt через certbot
2. Импортировать в AWS ACM
3. Применить к ALB
4. Настроить автоматическое обновление

---

## Шаг 1: Установка certbot

### На macOS:
```bash
brew install certbot
```

### На Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install certbot
```

### На Linux (CentOS/RHEL):
```bash
sudo yum install certbot
```

### Проверка установки:
```bash
certbot --version
```

---

## Шаг 2: Получение сертификата через DNS validation

Let's Encrypt требует подтверждения владения доменом. Для ALB лучше использовать **DNS validation** (не HTTP validation).

### Вариант A: Ручная DNS validation (проще для начала)

```bash
# Запросить сертификат с ручной DNS validation
certbot certonly \
  --manual \
  --preferred-challenges dns \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d agents.elemental.ae
```

**Что произойдет:**
1. Certbot попросит добавить TXT запись в DNS
2. Вы добавите запись в DNS вашего регистратора
3. Certbot проверит запись и выдаст сертификат

**Пример TXT записи:**
```
Имя: _acme-challenge.agents
Тип: TXT
Значение: [будет показано certbot]
TTL: 300
```

### Вариант B: Автоматическая DNS validation (требует API доступа к DNS)

Если у вас есть API доступ к DNS провайдеру, можно использовать плагины:
- `certbot-dns-route53` (для AWS Route53)
- `certbot-dns-cloudflare` (для Cloudflare)
- И другие плагины для разных провайдеров

---

## Шаг 3: Получение файлов сертификата

После успешной валидации certbot сохранит файлы:

```
/etc/letsencrypt/live/agents.elemental.ae/
├── cert.pem          # Сертификат
├── chain.pem          # Цепочка сертификатов
├── fullchain.pem     # Полная цепочка (cert + chain)
└── privkey.pem       # Приватный ключ
```

**Важно:** Сохраните эти файлы в безопасном месте!

---

## Шаг 4: Импорт сертификата в AWS ACM

ACM требует объединенный формат сертификата и цепочки.

### Создать объединенный файл:

```bash
# Объединить сертификат и цепочку
cat /etc/letsencrypt/live/agents.elemental.ae/cert.pem \
    /etc/letsencrypt/live/agents.elemental.ae/chain.pem > certificate.pem

# Или использовать fullchain.pem напрямую
cp /etc/letsencrypt/live/agents.elemental.ae/fullchain.pem certificate.pem

# Копировать приватный ключ
cp /etc/letsencrypt/live/agents.elemental.ae/privkey.pem private-key.pem
```

### Импортировать в ACM:

```bash
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
export AWS_DEFAULT_REGION="me-central-1"

aws acm import-certificate \
  --certificate fileb://certificate.pem \
  --private-key fileb://private-key.pem \
  --certificate-chain fileb:///etc/letsencrypt/live/agents.elemental.ae/chain.pem \
  --region me-central-1 \
  --tags Key=Name,Value=agents.elemental.ae-letsencrypt
```

**Сохраните CertificateArn из ответа!**

---

## Шаг 5: Применить сертификат к ALB

### Через AWS Console:
1. EC2 → Load Balancers → выберите ваш ALB
2. Listeners → Edit HTTPS listener (port 443)
3. Select certificate → выберите импортированный сертификат
4. Save

### Через Terraform:

Обновить `infra/alb_https.tf`:

```hcl
resource "aws_lb_listener" "frontend_https" {
  count             = var.enable_alb ? 1 : 0
  load_balancer_arn = aws_lb.main[0].arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = "arn:aws:acm:me-central-1:760221990195:certificate/НОВЫЙ_ARN"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend[0].arn
  }
}
```

Применить изменения:
```bash
cd infra
terraform plan
terraform apply
```

---

## Шаг 6: Настройка автоматического обновления

Let's Encrypt сертификаты действительны **90 дней**. Нужно обновлять каждые **60 дней**.

### Вариант A: Cron job на локальной машине

Создать скрипт обновления:

```bash
#!/bin/bash
# renew-letsencrypt.sh

# Обновить сертификат
certbot renew --quiet

# Если сертификат обновлен, импортировать в ACM
if [ -f /etc/letsencrypt/live/agents.elemental.ae/cert.pem ]; then
  # Создать временные файлы
  cat /etc/letsencrypt/live/agents.elemental.ae/fullchain.pem > /tmp/cert.pem
  cat /etc/letsencrypt/live/agents.elemental.ae/privkey.pem > /tmp/key.pem
  cat /etc/letsencrypt/live/agents.elemental.ae/chain.pem > /tmp/chain.pem
  
  # Импортировать в ACM (замените ARN на ваш)
  CERT_ARN="arn:aws:acm:me-central-1:760221990195:certificate/ВАШ_ARN"
  
  aws acm import-certificate \
    --certificate fileb:///tmp/cert.pem \
    --private-key fileb:///tmp/key.pem \
    --certificate-chain fileb:///tmp/chain.pem \
    --certificate-arn "$CERT_ARN" \
    --region me-central-1
  
  # Очистить временные файлы
  rm /tmp/cert.pem /tmp/key.pem /tmp/chain.pem
  
  echo "Certificate renewed and imported to ACM"
fi
```

Добавить в crontab:
```bash
# Обновлять каждые 60 дней в 3:00 AM
0 3 */60 * * /path/to/renew-letsencrypt.sh
```

### Вариант B: AWS Lambda функция (более надежно)

Создать Lambda функцию, которая:
1. Использует certbot в контейнере Lambda
2. Получает новый сертификат через DNS API
3. Импортирует в ACM
4. Запускается по расписанию (EventBridge)

**Преимущества:**
- Не зависит от локальной машины
- Автоматическое обновление
- Интеграция с AWS

---

## Проверка после настройки

### 1. Проверить SSL сертификат:
```bash
openssl s_client -connect agents.elemental.ae:443 -servername agents.elemental.ae
```

Должен показать:
- `Verify return code: 0 (ok)` - сертификат валиден
- Issuer: Let's Encrypt

### 2. Проверить через браузер:
Открыть `https://agents.elemental.ae` - не должно быть предупреждений

### 3. Проверить webhook:
```bash
curl -I https://agents.elemental.ae/api/v1/instagram/webhook
```

### 4. Обновить webhook URL в Facebook:
```
https://agents.elemental.ae/api/v1/instagram/webhook
```

---

## Важные замечания

1. **Безопасность файлов:**
   - Приватный ключ (`privkey.pem`) должен быть защищен
   - Не коммитьте ключи в git
   - Используйте безопасное хранилище для ключей

2. **Обновление сертификатов:**
   - Let's Encrypt сертификаты действительны 90 дней
   - Обновляйте каждые 60 дней
   - Настройте мониторинг истечения срока действия

3. **DNS validation:**
   - При обновлении нужно будет снова добавить TXT запись
   - Можно автоматизировать через DNS API

4. **Резервное копирование:**
   - Сохраняйте копии сертификатов и ключей
   - Храните в безопасном месте (например, AWS Secrets Manager)

---

## Альтернатива: Использовать AWS ACM напрямую

Если автоматизация обновления Let's Encrypt кажется сложной, можно использовать **AWS ACM напрямую**:
- Бесплатно
- Автоматическое обновление
- Проще в настройке
- Требует только DNS validation один раз

Но если вы предпочитаете Let's Encrypt - этот гайд поможет настроить его правильно!

