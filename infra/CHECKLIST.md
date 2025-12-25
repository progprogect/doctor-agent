# Чеклист готовности к `terraform apply`

## 🚀 Быстрый старт (автоматический скрипт)

Если у вас установлены Terraform и AWS CLI, можно использовать автоматический скрипт:

```bash
cd infra
./DEPLOY.sh
```

Скрипт выполнит все проверки и применит конфигурацию.

---

## Ручное выполнение

## ✅ Что уже готово:

1. ✅ **Subnet IDs** - заполнены в `terraform.tfvars.example`
2. ✅ **Security Groups** - существуют в AWS (ID известны)
3. ✅ **Health Check** - endpoint `/health` существует в приложении
4. ✅ **Конфигурация Terraform** - все файлы созданы
5. ✅ **Переменные** - MVP настройки (ALB и Redis отключены)

## ⚠️ Что нужно проверить ПЕРЕД `terraform apply`:

### 1. NAT Gateway для private subnets (КРИТИЧНО!)

ECS tasks нужен доступ в интернет для OpenAI API. Проверьте:

```bash
# Проверьте маршруты для private subnets
aws ec2 describe-route-tables \
  --region me-central-1 \
  --filters "Name=vpc-id,Values=vpc-03cb895f29b20a53e" \
  --query 'RouteTables[?Associations[0].SubnetId==`subnet-090c04ef58faa7ee1` || Associations[0].SubnetId==`subnet-0aa9317fe1b2228e1`].[RouteTableId,Associations[0].SubnetId,Routes[?DestinationCidrBlock==`0.0.0.0/0`]]' \
  --output table
```

**Если NAT Gateway отсутствует:**
- Вариант 1: Создать NAT Gateway (дорого, ~$32/месяц)
- Вариант 2: Использовать `assign_public_ip = true` для ECS (уже настроено в конфигурации)

**Текущая конфигурация:** ECS tasks используют `assign_public_ip = true` когда ALB отключен, поэтому NAT Gateway не обязателен.

### 2. Secrets Manager секреты

Проверьте существование секретов:

```bash
# Проверьте секрет OpenAI
aws secretsmanager describe-secret \
  --region me-central-1 \
  --secret-id doctor-agent/openai 2>&1

# Если секрет не существует, создайте его:
aws secretsmanager create-secret \
  --region me-central-1 \
  --name doctor-agent/openai \
  --description "OpenAI API key for Doctor Agent" \
  --secret-string "your-openai-api-key-here"
```

**Требования:**
- ✅ Секрет `doctor-agent/openai` должен существовать
- ✅ Значение должно быть простой строкой (API key)

### 3. Подготовка terraform.tfvars

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Проверьте значения в terraform.tfvars
```

### 4. Terraform init и plan

```bash
# Инициализация
terraform init

# Планирование (проверка без применения)
terraform plan -var-file="terraform.tfvars"

# Проверьте вывод plan:
# - Не должно быть ошибок
# - Должны создаваться только новые ресурсы (не пересоздавать существующие)
# - Проверьте количество создаваемых ресурсов
```

## 🚀 Порядок выполнения:

### Шаг 1: Подготовка (5 минут)

```bash
cd infra

# 1. Создайте terraform.tfvars
cp terraform.tfvars.example terraform.tfvars

# 2. Проверьте секреты
aws secretsmanager describe-secret \
  --region me-central-1 \
  --secret-id doctor-agent/openai
```

### Шаг 2: Инициализация и планирование (5 минут)

```bash
# 3. Инициализация Terraform
terraform init

# 4. Планирование (ВАЖНО: проверьте вывод!)
terraform plan -var-file="terraform.tfvars" > plan.txt

# 5. Просмотрите plan.txt
cat plan.txt
```

**Что проверить в plan:**
- ✅ Нет ошибок
- ✅ Количество создаваемых ресурсов разумное (~15-20)
- ✅ Нет попыток пересоздать существующие ресурсы (Security Groups, DynamoDB tables)

### Шаг 3: Применение (10-15 минут)

```bash
# 6. Применение конфигурации
terraform apply -var-file="terraform.tfvars"

# Подтвердите вводом "yes"
```

**Время выполнения:**
- OpenSearch domain: ~10-15 минут (самый долгий)
- ECS Cluster: ~1-2 минуты
- ECR Repository: ~30 секунд
- IAM Roles: ~30 секунд
- Остальное: быстро

### Шаг 4: Настройка секретов (после создания ресурсов)

После создания OpenSearch domain, задайте пароль:

```bash
# Получите пароль OpenSearch (если задавали при создании)
# Или создайте новый секрет:
aws secretsmanager put-secret-value \
  --region me-central-1 \
  --secret-id doctor-agent/opensearch \
  --secret-string "your-secure-opensearch-password"
```

### Шаг 5: Деплой Docker образа

```bash
# 1. Авторизация в ECR
aws ecr get-login-password --region me-central-1 | \
  docker login --username AWS --password-stdin \
  760221990195.dkr.ecr.me-central-1.amazonaws.com

# 2. Сборка образа
cd ../backend
docker build -t doctor-agent-backend .

# 3. Тегирование и пуш
docker tag doctor-agent-backend:latest \
  760221990195.dkr.ecr.me-central-1.amazonaws.com/doctor-agent-backend:latest

docker push 760221990195.dkr.ecr.me-central-1.amazonaws.com/doctor-agent-backend:latest

# 4. ECS автоматически обновит service (или сделайте force deployment)
aws ecs update-service \
  --cluster doctor-agent-cluster \
  --service doctor-agent-backend \
  --force-new-deployment \
  --region me-central-1
```

## ⚠️ Важные замечания:

1. **Стоимость:** ~$45-60/месяц для MVP (без ALB и Redis)
2. **OpenSearch:** Создание домена занимает 10-15 минут
3. **ECS Tasks:** После деплоя образа, tasks запустятся автоматически
4. **Доступ:** Без ALB доступ к приложению будет через public IP ECS task

## 🔍 Проверка после деплоя:

```bash
# Получите IP адрес ECS task
TASK_ARN=$(aws ecs list-tasks \
  --cluster doctor-agent-cluster \
  --service-name doctor-agent-backend \
  --region me-central-1 \
  --query 'taskArns[0]' --output text)

TASK_IP=$(aws ecs describe-tasks \
  --cluster doctor-agent-cluster \
  --tasks $TASK_ARN \
  --region me-central-1 \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
  --output text | xargs -I {} aws ec2 describe-network-interfaces \
    --network-interface-ids {} \
    --region me-central-1 \
    --query 'NetworkInterfaces[0].Association.PublicIp' \
    --output text)

# Проверка health endpoint
curl http://$TASK_IP:8000/health
```

## ✅ Готовы к применению?

Если все проверки пройдены:
1. ✅ Секреты существуют или будут созданы
2. ✅ terraform.tfvars подготовлен
3. ✅ terraform plan выполнен без ошибок
4. ✅ Понимаете стоимость (~$45-60/месяц)

**Тогда можно выполнять `terraform apply`!**

