# Terraform Infrastructure для Doctor Agent MVP

Terraform-конфигурация для базовой инфраструктуры AWS: Security Groups, DynamoDB tables и Secrets Manager.

## Предварительные требования

1. **AWS CLI** настроен с правильными credentials
2. **Terraform** версии >= 1.0 установлен
3. **S3 bucket** `doctor-agent-terraform-state-760221990195` существует
4. **DynamoDB table** `terraform-state-locks` существует для state locking

## ⚠️ КРИТИЧЕСКИЕ ПРОВЕРКИ ПЕРЕД `terraform apply`

**ВАЖНО**: Выполните эти проверки перед применением конфигурации, чтобы избежать дорогих ошибок:

### 1. Проверка Subnets

```bash
# Проверьте, что private subnets имеют NAT Gateway для доступа в интернет
aws ec2 describe-route-tables \
  --region me-central-1 \
  --filters "Name=vpc-id,Values=vpc-03cb895f29b20a53e" \
  --query 'RouteTables[*].[RouteTableId,Associations[0].SubnetId,Routes[?DestinationCidrBlock==`0.0.0.0/0`]]' \
  --output table
```

**Требования:**
- ✅ Private subnets должны иметь маршрут `0.0.0.0/0 → NAT Gateway` (для доступа ECS к OpenAI API)
- ✅ Если ALB отключен (`enable_alb = false`), ECS tasks будут использовать `assign_public_ip = true` для доступа в интернет

### 2. Проверка Security Groups

```bash
# Проверьте существующие Security Groups
aws ec2 describe-security-groups \
  --region me-central-1 \
  --filters "Name=group-name,Values=ecs-service-sg,redis-sg,opensearch-sg" \
  --query 'SecurityGroups[*].[GroupName,GroupId,VpcId]' \
  --output table
```

**Требования:**
- ✅ `ecs-service-sg` должен существовать и быть в правильном VPC
- ✅ `opensearch-sg` должен разрешать доступ только от `ecs-service-sg` (TCP 443)
- ✅ `redis-sg` должен разрешать доступ только от `ecs-service-sg` (TCP 6379)

### 3. Проверка Secrets Manager

```bash
# Проверьте существование секрета OpenAI
aws secretsmanager describe-secret \
  --region me-central-1 \
  --secret-id doctor-agent/openai

# Проверьте формат секрета (должен быть простой строкой или JSON с ключом)
aws secretsmanager get-secret-value \
  --region me-central-1 \
  --secret-id doctor-agent/openai \
  --query SecretString \
  --output text
```

**Требования:**
- ✅ Секрет `doctor-agent/openai` должен существовать
- ✅ Значение должно быть простой строкой (API key) или JSON с ключом `api_key`/`OPENAI_API_KEY`
- ✅ Если JSON, убедитесь, что ключ называется именно так, как ожидает приложение

### 4. Проверка Health Check Path

Убедитесь, что ваше приложение отдаёт ответ на `/health`:

```bash
# После деплоя проверьте:
curl http://<ECS_TASK_IP>:8000/health
```

**Требования:**
- ✅ Endpoint `/health` должен возвращать HTTP 200
- ✅ Если путь другой, обновите `health_check.path` в `alb.tf` или `ecs.tf`

### 5. Проверка стоимости ресурсов

**Минимальные настройки для MVP (снижают стоимость):**

```hcl
# terraform.tfvars
enable_alb = false              # Отключить ALB (~$16/месяц)
redis_num_cache_nodes = 0       # Отключить Redis (~$15/месяц)
opensearch_instance_type = "t3.small.search"  # Минимальный размер
opensearch_instance_count = 1
ecs_cpu = 512                   # 0.5 vCPU
ecs_memory = 1024               # 1 GB RAM
ecs_desired_count = 1           # Один task
```

**Ориентировочная стоимость MVP (без ALB и Redis):**
- OpenSearch: ~$30-40/месяц
- ECS Fargate: ~$15-20/месяц (зависит от использования)
- DynamoDB: Pay-per-request (минимально)
- **Итого: ~$45-60/месяц**

### 6. Проверка переменных

Создайте `terraform.tfvars` на основе примера:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Или создайте вручную с реальными subnet IDs из вашего VPC:

```hcl
vpc_id             = "vpc-03cb895f29b20a53e"
aws_region         = "me-central-1"
project_tag        = "doctor-agent"

# Private subnets для ECS, OpenSearch, Redis
private_subnet_ids = [
  "subnet-090c04ef58faa7ee1",  # Doctor-agent-subnet-private1-me-central-1a
  "subnet-0aa9317fe1b2228e1"  # Doctor-agent-subnet-private2-me-central-1b
]

# Public subnets для ALB (только если enable_alb = true)
public_subnet_ids = [
  "subnet-05596238170cc2248",  # Doctor-agent-subnet-public1-me-central-1a
  "subnet-0d177e6c6453fbc92"  # Doctor-agent-subnet-public2-me-central-1b
]

# MVP настройки (минимальная стоимость)
enable_alb = false
redis_num_cache_nodes = 0

# OpenSearch
opensearch_instance_type  = "t3.small.search"
opensearch_instance_count = 1
opensearch_ebs_volume_size = 20
opensearch_master_user_name = "admin"

# ECS
ecs_cpu          = 512
ecs_memory       = 1024
ecs_desired_count = 1
```

---

## Быстрый старт

### 0. Подготовка переменных

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Отредактируйте terraform.tfvars при необходимости
```

Файл `terraform.tfvars.example` уже содержит правильные subnet IDs для вашего VPC:
- **Private subnets**: `subnet-090c04ef58faa7ee1`, `subnet-0aa9317fe1b2228e1`
- **Public subnets**: `subnet-05596238170cc2248`, `subnet-0d177e6c6453fbc92`

### 1. Инициализация Terraform

```bash
terraform init
```

При первом запуске Terraform загрузит необходимые провайдеры и настроит remote state backend.

### 2. Получение ID существующих ресурсов

Перед выполнением import необходимо получить реальные ID ресурсов из AWS Console:

#### Security Groups

```bash
# Получить список Security Groups
aws ec2 describe-security-groups \
  --region me-central-1 \
  --filters "Name=group-name,Values=ecs-service-sg,redis-sg,opensearch-sg" \
  --query 'SecurityGroups[*].[GroupName,GroupId]' \
  --output table
```

Сохраните ID для каждой Security Group:
- `ecs-service-sg` → `sg-XXXXXXXX`
- `redis-sg` → `sg-YYYYYYYY`
- `opensearch-sg` → `sg-ZZZZZZZZ`

#### DynamoDB Tables

Таблицы должны существовать с именами:
- `Agents`
- `Conversations`
- `Messages`

#### Secrets Manager

Секрет должен существовать с именем:
- `doctor-agent/openai`

### 3. Import существующих ресурсов

**Реальные ID Security Groups:**
- `ecs-service-sg`: `sg-06108dc748e728fac`
- `redis-sg`: `sg-05eed390c5dcd51a5`
- `opensearch-sg`: `sg-0c9ac0a356a74639e`

```bash
# Security Groups
terraform import aws_security_group.ecs_service sg-06108dc748e728fac
terraform import aws_security_group.redis sg-05eed390c5dcd51a5
terraform import aws_security_group.opensearch sg-0c9ac0a356a74639e

# DynamoDB Tables
terraform import aws_dynamodb_table.agents Agents
terraform import aws_dynamodb_table.conversations Conversations
terraform import aws_dynamodb_table.messages Messages

# Secrets Manager
terraform import aws_secretsmanager_secret.openai doctor-agent/openai
```

### 4. Проверка конфигурации

После import выполните:

```bash
terraform validate
terraform plan
```

`terraform plan` должен показать минимальные изменения или их отсутствие (если конфигурация точно соответствует существующим ресурсам).

### 5. Применение изменений (если необходимо)

```bash
terraform apply
```

## Настройка переменных

По умолчанию используются следующие значения:

- `vpc_id`: `vpc-03cb895f29b20a53e`
- `aws_region`: `me-central-1`
- `project_tag`: `doctor-agent`

Для переопределения создайте файл `terraform.tfvars`:

```hcl
vpc_id     = "vpc-03cb895f29b20a53e"
aws_region = "me-central-1"
project_tag = "doctor-agent"
```

Или передайте переменные через командную строку:

```bash
terraform plan -var="vpc_id=vpc-XXXXX"
```

## Настройка OpenAI API Key

**Важно**: Значение секрета не хранится в Terraform state и должно быть задано вручную через AWS Console или CLI.

### Через AWS CLI

```bash
aws secretsmanager put-secret-value \
  --region me-central-1 \
  --secret-id doctor-agent/openai \
  --secret-string "your-openai-api-key-here"
```

### Через AWS Console

1. Откройте AWS Secrets Manager в консоли
2. Найдите секрет `doctor-agent/openai`
3. Нажмите "Retrieve secret value"
4. Нажмите "Edit" и введите значение API key
5. Сохраните изменения

## Структура ресурсов

### Security Groups

- **ecs-service-sg**: Security group для ECS Fargate backend
  - Inbound: пусто
  - Outbound: все трафик

- **redis-sg**: Security group для Redis
  - Inbound: TCP 6379 от ecs-service-sg
  - Outbound: весь трафик

- **opensearch-sg**: Security group для OpenSearch
  - Inbound: TCP 443 от ecs-service-sg
  - Outbound: весь трафик

### DynamoDB Tables

- **Agents**: Хранение конфигураций агентов
  - Partition key: `agent_id` (String)
  - Billing: PAY_PER_REQUEST

- **Conversations**: Хранение диалогов
  - Partition key: `conversation_id` (String)
  - TTL: `expires_at` (48 часов)
  - Billing: PAY_PER_REQUEST

- **Messages**: Хранение сообщений
  - Partition key: `conversation_id` (String)
  - Sort key: `message_id` (String)
  - TTL: `expires_at` (48 часов)
  - Billing: PAY_PER_REQUEST

### Secrets Manager

- **doctor-agent/openai**: OpenAI API key
  - Значение задается вручную (не через Terraform)

## Outputs

После применения конфигурации доступны следующие outputs:

```bash
terraform output
```

- `ecs_service_sg_id`: ID Security Group для ECS service
- `redis_sg_id`: ID Security Group для Redis
- `opensearch_sg_id`: ID Security Group для OpenSearch
- `dynamodb_tables`: Map с именами таблиц DynamoDB
- `openai_secret_arn`: ARN секрета OpenAI API key

## Troubleshooting

### Ошибка при terraform init

Если возникает ошибка доступа к S3 bucket:

1. Проверьте, что bucket `doctor-agent-terraform-state-760221990195` существует
2. Проверьте права доступа AWS credentials
3. Убедитесь, что DynamoDB table `terraform-state-locks` существует

### Ошибка при import

Если import не работает:

1. Проверьте, что ресурс существует в AWS
2. Убедитесь, что используете правильный регион (`me-central-1`)
3. Проверьте формат команды import (должен соответствовать типу ресурса)

### Terraform plan показывает изменения после import

Это нормально, если:
- Конфигурация не полностью соответствует существующему ресурсу
- Добавлены теги или другие атрибуты

Проверьте изменения через `terraform plan` и при необходимости скорректируйте конфигурацию.

## Расширенная инфраструктура (OpenSearch, ECS, ALB, Redis)

Конфигурация включает дополнительные ресурсы для полного развертывания приложения.

### Переменные для новых ресурсов

См. раздел "Проверка переменных" выше для примера `terraform.tfvars`.

**Важно для MVP:**
- `enable_alb = false` - отключает ALB (экономия ~$16/месяц)
- `redis_num_cache_nodes = 0` - отключает Redis (экономия ~$15/месяц)
- ECS tasks будут использовать `assign_public_ip = true` для доступа в интернет

### Новые ресурсы

Конфигурация создает следующие ресурсы:

1. **OpenSearch Domain** (`opensearch.tf`)
   - Векторное хранилище для RAG
   - Размещен в private subnets
   - Использует Security Group `opensearch-sg`

2. **ECR Repository** (`ecr.tf`)
   - Репозиторий для Docker образов backend
   - Lifecycle policy (хранит последние 10 образов)

3. **ECS Cluster & Service** (`ecs.tf`)
   - Fargate cluster для запуска контейнеров
   - Task definition с переменными окружения
   - Service с подключением к ALB

4. **Application Load Balancer** (`alb.tf`)
   - HTTP listener (для MVP)
   - Target group для ECS service
   - Health checks на `/health`

5. **IAM Roles** (`iam.tf`)
   - Execution role (ECR, CloudWatch Logs, Secrets Manager)
   - Task role (DynamoDB, OpenSearch, Secrets Manager)

6. **ElastiCache Redis** (`redis.tf`)
   - Redis cluster для кэширования и сессий
   - Опционально (можно отключить через `redis_num_cache_nodes = 0`)

### Настройка секретов

Перед деплоем необходимо задать значения секретов:

```bash
# OpenSearch password
aws secretsmanager put-secret-value \
  --region me-central-1 \
  --secret-id doctor-agent/opensearch \
  --secret-string "your-opensearch-password"

# OpenAI API key
aws secretsmanager put-secret-value \
  --region me-central-1 \
  --secret-id doctor-agent/openai \
  --secret-string "your-openai-api-key"
```

### Деплой Docker образа

1. **Авторизация в ECR:**
```bash
aws ecr get-login-password --region me-central-1 | \
  docker login --username AWS --password-stdin \
  760221990195.dkr.ecr.me-central-1.amazonaws.com
```

2. **Сборка и пуш образа:**
```bash
cd ../backend
docker build -t doctor-agent-backend .
docker tag doctor-agent-backend:latest \
  760221990195.dkr.ecr.me-central-1.amazonaws.com/doctor-agent-backend:latest
docker push 760221990195.dkr.ecr.me-central-1.amazonaws.com/doctor-agent-backend:latest
```

### Применение конфигурации

```bash
# Планирование
terraform plan -var-file="terraform.tfvars"

# Применение
terraform apply -var-file="terraform.tfvars"
```

### Outputs

После применения доступны следующие outputs:

```bash
terraform output
```

- `alb_dns_name`: DNS имя ALB (используйте для доступа к API)
- `opensearch_domain_endpoint`: Endpoint для OpenSearch
- `ecr_repository_url`: URL ECR репозитория
- `ecs_cluster_name`: Имя ECS кластера
- `redis_endpoint`: Endpoint Redis (если включен)

### Проверка деплоя

1. **Если ALB включен - проверка через ALB:**
```bash
ALB_DNS=$(terraform output -raw alb_dns_name)
curl http://$ALB_DNS/health
```

2. **Если ALB отключен - проверка через ECS Task IP:**
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

curl http://$TASK_IP:8000/health
```

3. **Проверка ECS Service:**
```bash
aws ecs describe-services \
  --cluster doctor-agent-cluster \
  --services doctor-agent-backend \
  --region me-central-1
```

3. **Просмотр логов:**
```bash
aws logs tail /ecs/doctor-agent --follow --region me-central-1
```

### Troubleshooting

**ECS tasks не запускаются:**
- Проверьте IAM роли и политики
- Убедитесь, что секреты заданы в Secrets Manager
- Проверьте логи в CloudWatch: `/ecs/doctor-agent`

**OpenSearch недоступен:**
- Проверьте Security Group rules
- Убедитесь, что domain находится в правильных subnets
- Проверьте пароль в Secrets Manager

**ALB не маршрутизирует трафик:**
- Проверьте Target Group health checks
- Убедитесь, что ECS tasks запущены и здоровы
- Проверьте Security Group rules между ALB и ECS

## Следующие шаги

После успешного деплоя:

1. Настройте HTTPS для ALB (добавьте ACM certificate)
2. Настройте CloudWatch Alarms для мониторинга
3. Настройте Auto Scaling для ECS service
4. Добавьте WAF для защиты ALB
5. Настройте Route53 для кастомного домена

