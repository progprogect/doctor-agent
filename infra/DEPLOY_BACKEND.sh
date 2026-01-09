#!/bin/bash
# Скрипт для деплоя бэкенда в AWS ECS

set -e

echo "🚀 Деплой бэкенда в AWS ECS Fargate"
echo ""

# Переменные
REGION="me-central-1"
BACKEND_DIR="../backend"
INFRA_DIR="."

# Проверка зависимостей
command -v docker >/dev/null 2>&1 || { echo "❌ Docker не установлен"; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI не установлен"; exit 1; }

# 1. Получить ECR URL
echo "📦 Получение ECR repository URL..."
cd "$INFRA_DIR"
ECR_REPO=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "")
if [ -z "$ECR_REPO" ]; then
  echo "❌ Не удалось получить ECR repository URL"
  echo "   Убедитесь, что Terraform применен: terraform apply"
  exit 1
fi

echo "✅ ECR Repository: $ECR_REPO"
echo ""

# 2. Логин в ECR
echo "🔐 Авторизация в ECR..."
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_REPO"

# 3. Сборка Docker образа
echo "🔨 Сборка Docker образа..."
cd "$BACKEND_DIR"

if [ ! -f "Dockerfile" ]; then
  echo "❌ Dockerfile не найден в $BACKEND_DIR"
  exit 1
fi

docker build --platform linux/amd64 -t doctor-agent-backend:latest .

# 4. Тегирование и push в ECR
echo "📤 Загрузка образа в ECR..."
docker tag doctor-agent-backend:latest "$ECR_REPO:latest"
docker push "$ECR_REPO:latest"

echo "✅ Образ загружен в ECR"
echo ""

# 5. Обновление ECS сервиса
echo "🔄 Обновление ECS сервиса..."
cd "$INFRA_DIR"
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
SERVICE_NAME=$(terraform output -raw ecs_service_name)

if [ -z "$CLUSTER_NAME" ] || [ -z "$SERVICE_NAME" ]; then
  echo "❌ Не удалось получить имена кластера или сервиса"
  exit 1
fi

aws ecs update-service \
  --cluster "$CLUSTER_NAME" \
  --service "$SERVICE_NAME" \
  --force-new-deployment \
  --region "$REGION" > /dev/null

echo "✅ Сервис обновлен, запускается новый деплой..."
echo ""

# 6. Ожидание завершения деплоя
echo "⏳ Ожидание завершения деплоя (это может занять 2-3 минуты)..."
aws ecs wait services-stable \
  --cluster "$CLUSTER_NAME" \
  --services "$SERVICE_NAME" \
  --region "$REGION"

echo ""
echo "✅ Деплой завершен успешно!"
echo ""
echo "📊 Проверка статуса:"
aws ecs describe-services \
  --cluster "$CLUSTER_NAME" \
  --services "$SERVICE_NAME" \
  --region "$REGION" \
  --query 'services[0].[runningCount,desiredCount,status]' \
  --output table

echo ""
echo "📝 Логи доступны через:"
echo "   aws logs tail /ecs/doctor-agent --region $REGION --since 5m"

