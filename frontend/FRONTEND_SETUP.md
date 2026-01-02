# Настройка фронтенда для подключения к бэкенду

## Вариант 1: Локальный запуск с подключением к AWS (Рекомендуется)

### Шаг 1: Получите публичный IP или настройте port forwarding

Поскольку ALB отключен, а ECS задача в private subnet, есть несколько вариантов:

#### Вариант 1A: Port Forwarding через AWS Systems Manager (если установлен SSM Agent)

```bash
# Установите Session Manager plugin для AWS CLI
# https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html

# Получите task ID
TASK_ARN=$(aws ecs list-tasks --cluster doctor-agent-cluster --service-name doctor-agent-backend --region me-central-1 --query 'taskArns[0]' --output text)
TASK_ID=$(echo $TASK_ARN | cut -d'/' -f3)

# Port forwarding (если SSM настроен)
aws ecs execute-command \
  --cluster doctor-agent-cluster \
  --task $TASK_ID \
  --container backend \
  --command "/bin/sh" \
  --interactive \
  --region me-central-1
```

#### Вариант 1B: Использовать публичный IP (если assign_public_ip = true)

Проверьте, есть ли у задачи публичный IP:
```bash
TASK_ARN=$(aws ecs list-tasks --cluster doctor-agent-cluster --service-name doctor-agent-backend --region me-central-1 --query 'taskArns[0]' --output text)
ENI_ID=$(aws ecs describe-tasks --cluster doctor-agent-cluster --tasks $TASK_ARN --region me-central-1 --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)
aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --region me-central-1 --query 'NetworkInterfaces[0].Association.PublicIp' --output text
```

Если есть публичный IP, используйте его в `.env.local`

### Шаг 2: Создайте файл `.env.local` в папке `frontend/`

```bash
cd frontend
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://ВАШ_ПУБЛИЧНЫЙ_IP:8000
NEXT_PUBLIC_WS_URL=ws://ВАШ_ПУБЛИЧНЫЙ_IP:8000
EOF
```

**ВАЖНО:** Если публичного IP нет, вам нужно:
1. Либо включить ALB (измените `enable_alb = true` в `terraform.tfvars` и выполните `terraform apply`)
2. Либо использовать VPN/SSH туннель для доступа к private subnet

### Шаг 3: Запустите фронтенд локально

```bash
cd frontend
npm install
npm run dev
```

Фронтенд будет доступен по адресу: `http://localhost:3000`

## Вариант 2: Включить ALB для публичного доступа

Если хотите публичный доступ без локального запуска:

1. Откройте `infra/terraform.tfvars`
2. Измените `enable_alb = true`
3. Выполните:
```bash
cd infra
terraform apply -var-file="terraform.tfvars"
```

После этого получите ALB DNS:
```bash
terraform output alb_dns_name
```

И используйте его в `.env.local`:
```
NEXT_PUBLIC_API_URL=https://ВАШ_ALB_DNS
NEXT_PUBLIC_WS_URL=wss://ВАШ_ALB_DNS
```

## Вариант 3: Развернуть фронтенд в AWS (Amplify/S3+CloudFront)

Для production окружения рекомендуется развернуть фронтенд через:
- AWS Amplify
- S3 + CloudFront
- ECS Fargate (как бэкенд)

## Текущий статус

- ✅ Бэкенд работает в ECS Fargate
- ✅ Health check доступен
- ⚠️ ALB отключен (нет публичного DNS)
- ⚠️ Задача в private subnet (нужен NAT для доступа)





