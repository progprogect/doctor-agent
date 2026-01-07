# Решение проблемы SSL сертификата для Instagram Webhook

## Проблема

Браузер показывает предупреждение "Это подключение не защищено" потому что используется **самоподписанный SSL сертификат**. 

Instagram **НЕ ПРИНИМАЕТ** самоподписанные сертификаты для webhook верификации. Нужен валидный сертификат от доверенного CA.

## Решения

### Вариант 1: Использовать домен с AWS Certificate Manager (Рекомендуется)

1. **Купить домен** (например, через Route53, Namecheap, GoDaddy)
   - Пример: `doctor-agent.com` или `elemental-clinic.com`

2. **Создать сертификат в ACM:**
   ```bash
   aws acm request-certificate \
     --domain-name your-domain.com \
     --validation-method DNS \
     --region me-central-1
   ```

3. **Провести DNS валидацию** (добавить CNAME записи в DNS)

4. **Обновить Terraform** для использования этого сертификата

5. **Настроить DNS** для домена на ALB:
   ```bash
   # Создать A record в Route53 или у регистратора домена
   # Указать ALB DNS: doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com
   ```

### Вариант 2: Использовать Cloudflare (Бесплатно)

1. Зарегистрировать домен или использовать существующий
2. Добавить домен в Cloudflare
3. Использовать Cloudflare SSL/TLS (автоматический сертификат)
4. Настроить проксирование на ALB

### Вариант 3: Использовать ngrok для тестирования (Временное решение)

Для тестирования можно использовать ngrok, который предоставляет HTTPS с валидным сертификатом:

```bash
ngrok http 80
# Получите HTTPS URL типа: https://xxxx-xx-xx-xx-xx.ngrok.io
```

Но это только для тестирования, не для production.

## Текущая ситуация

- ✅ HTTPS listener настроен на ALB
- ✅ Самоподписанный сертификат установлен
- ❌ Браузеры не доверяют сертификату (показывают предупреждение)
- ❌ Instagram не примет такой сертификат для webhook

## Что нужно сделать

**Для production использования Instagram webhook:**

1. **Получить домен** (можно купить за ~$10-15/год)
2. **Создать валидный SSL сертификат** через AWS ACM или Let's Encrypt
3. **Настроить DNS** для домена
4. **Обновить webhook URL** в Facebook Developer Console на новый домен

## Временное решение для тестирования

Можно использовать ngrok для тестирования webhook:

```bash
# Установить ngrok
brew install ngrok  # на macOS

# Запустить туннель
ngrok http doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com

# Использовать HTTPS URL от ngrok в Facebook Developer Console
```

Но это только для разработки/тестирования.

## Рекомендация

Для production лучше всего использовать **домен + AWS Certificate Manager**. Это бесплатно и надежно.

