# Инструкция по деплою фронтенда

## Предварительные требования

1. **Docker Desktop должен быть запущен**
   ```bash
   # Проверьте, что Docker работает:
   docker ps
   ```

2. **AWS credentials настроены**
   ```bash
   # Если не настроены, установите переменные окружения:
   # export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY_ID"
   # export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_ACCESS_KEY"
   export AWS_DEFAULT_REGION="me-central-1"
   ```

## Шаги деплоя

### 1. Перейдите в директорию фронтенда
```bash
cd frontend
```

### 2. Соберите Docker образ
```bash
docker build --platform linux/amd64 -t doctor-agent-frontend:latest .
```

### 3. Тегируйте и загрузите образ в ECR
```bash
ECR_REPO="760221990195.dkr.ecr.me-central-1.amazonaws.com/doctor-agent-frontend"

# Тегируйте образ
docker tag doctor-agent-frontend:latest "$ECR_REPO:latest"

# Войдите в ECR
aws ecr get-login-password --region me-central-1 | docker login --username AWS --password-stdin "$ECR_REPO"

# Загрузите образ
docker push "$ECR_REPO:latest"
```

### 4. Обновите ECS сервис
```bash
aws ecs update-service \
  --cluster doctor-agent-cluster \
  --service doctor-agent-frontend \
  --force-new-deployment \
  --region me-central-1
```

### 5. Проверьте статус
```bash
# Проверьте статус сервиса
aws ecs describe-services \
  --cluster doctor-agent-cluster \
  --services doctor-agent-frontend \
  --region me-central-1 \
  --query 'services[0].[runningCount,desiredCount,status]' \
  --output table

# Проверьте логи
aws logs tail /ecs/doctor-agent-frontend \
  --region me-central-1 \
  --since 5m \
  --format short
```

## Доступ к фронтенду

После успешного деплоя фронтенд будет доступен по адресу:

**http://doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com**

### Маршрутизация через ALB:
- **Frontend (главная страница)**: `http://doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com/`
- **API**: `http://doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com/api/v1`
- **Health check**: `http://doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com/health`

## Альтернатива: Использование скрипта

Можно использовать готовый скрипт (после запуска Docker и настройки AWS credentials):

```bash
cd infra
./DEPLOY_FRONTEND.sh
```

## Устранение проблем

### Если задача не запускается:
1. Проверьте логи ECS:
   ```bash
   aws logs tail /ecs/doctor-agent-frontend --region me-central-1 --since 10m
   ```

2. Проверьте события сервиса:
   ```bash
   aws ecs describe-services \
     --cluster doctor-agent-cluster \
     --services doctor-agent-frontend \
     --region me-central-1 \
     --query 'services[0].events[:5]' \
     --output table
   ```

### Если образ не собирается:
- Убедитесь, что все зависимости установлены: `npm install`
- Проверьте, что сборка проходит локально: `npm run build`

### Если не удается загрузить в ECR:
- Проверьте AWS credentials
- Убедитесь, что ECR репозиторий создан (должен быть создан через Terraform)

