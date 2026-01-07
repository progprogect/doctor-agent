# Решение проблемы HTTPS для Instagram Webhook

## Проблема

Браузер показывает предупреждение "Это подключение не защищено" потому что используется **самоподписанный SSL сертификат**.

**Instagram НЕ ПРИНИМАЕТ** самоподписанные сертификаты для webhook верификации.

## Решения

### ✅ Вариант 1: Использовать домен + AWS Certificate Manager (Бесплатно)

**Шаги:**

1. **Купить домен** (если нет):
   - Route53: ~$12/год
   - Namecheap/GoDaddy: ~$10-15/год
   - Пример: `elemental-clinic.com` или `doctor-agent.app`

2. **Создать сертификат в ACM:**
   ```bash
   aws acm request-certificate \
     --domain-name your-domain.com \
     --validation-method DNS \
     --region me-central-1
   ```

3. **Провести DNS валидацию:**
   - ACM предоставит CNAME записи
   - Добавить их в DNS настройки домена

4. **Настроить DNS для домена:**
   - Создать A record (Alias) в Route53 или у регистратора
   - Указать ALB: `doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com`

5. **Обновить Terraform** для использования нового сертификата

### ✅ Вариант 2: Cloudflare (Бесплатно, если есть домен)

1. Зарегистрировать домен или использовать существующий
2. Добавить домен в Cloudflare (бесплатный план)
3. Cloudflare автоматически предоставляет SSL сертификат
4. Настроить проксирование на ALB

### ⚠️ Вариант 3: ngrok для тестирования (Временное)

Для тестирования webhook можно использовать ngrok:

```bash
# Установить ngrok
brew install ngrok  # macOS
# или скачать с https://ngrok.com/

# Запустить туннель
ngrok http doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com

# Использовать HTTPS URL от ngrok в Facebook Developer Console
# Пример: https://xxxx-xx-xx-xx-xx.ngrok-free.app
```

**⚠️ Внимание:** Это только для тестирования! Instagram может блокировать ngrok домены.

## Текущий статус

- ✅ HTTPS listener настроен на ALB (порт 443)
- ✅ Самоподписанный сертификат установлен
- ❌ Браузеры не доверяют (показывают предупреждение)
- ❌ Instagram не примет для webhook верификации

## Что делать сейчас

### Для тестирования (быстро):

Используйте **ngrok** для получения валидного HTTPS URL:

1. Установите ngrok: https://ngrok.com/download
2. Запустите: `ngrok http doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com`
3. Используйте HTTPS URL от ngrok в Facebook Developer Console
4. Webhook будет работать для тестирования

### Для production:

**Нужен домен** + валидный SSL сертификат. Рекомендую использовать AWS Certificate Manager (бесплатно) с доменом.

## Проверка текущего сертификата

Текущий сертификат: `IMPORTED` (самоподписанный)
- Статус: ISSUED
- Тип: IMPORTED
- **Не подходит для Instagram webhook**

Нужен сертификат типа `AMAZON_ISSUED` с валидным доменом.

