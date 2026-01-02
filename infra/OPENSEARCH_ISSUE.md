# Проблема с OpenSearch в регионе me-central-1

## Ошибка
```
SubscriptionRequiredException: The AWS Access Key Id needs a subscription for the service
```

## Причина
Регион `me-central-1` (Middle East - UAE) является новым регионом AWS, и OpenSearch может требовать активации подписки через AWS Console.

## Решения

### Вариант 1: Активировать OpenSearch в AWS Console
1. Откройте AWS Console → OpenSearch Service
2. Перейдите в регион `me-central-1`
3. Если появится запрос на активацию - подтвердите
4. После активации повторите `terraform apply`

### Вариант 2: Использовать другой регион для OpenSearch
Если OpenSearch недоступен в `me-central-1`, можно:
- Использовать `us-east-1` или `eu-west-1` для OpenSearch
- Остальные ресурсы останутся в `me-central-1`

### Вариант 3: Временно отключить OpenSearch
Для MVP можно временно отключить RAG функциональность:
- Установить `opensearch_instance_count = 0` (но это не сработает)
- Или закомментировать ресурс `aws_opensearch_domain.main` в `opensearch.tf`

## Рекомендация
Попробуйте сначала активировать OpenSearch через AWS Console, затем повторите `terraform apply`.





