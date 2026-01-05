#!/bin/bash
# Скрипт для деплоя фронтенда в AWS

set -e

echo "🚀 Деплой фронтенда в AWS ECS Fargate"
echo ""

# Проверка зависимостей
command -v docker >/dev/null 2>&1 || { echo "❌ Docker не установлен"; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI не установлен"; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo "❌ Terraform не установлен"; exit 1; }

# Переменные
REGION="me-central-1"
FRONTEND_DIR="../frontend"
INFRA_DIR="."

# 1. Применить Terraform для создания инфраструктуры
echo "📦 Создание инфраструктуры через Terraform..."
cd "$INFRA_DIR"
terraform apply -var-file="terraform.tfvars" -auto-approve

# Получить ECR URL
ECR_REPO=$(terraform output -raw frontend_ecr_repository_url 2>/dev/null || echo "")
if [ -z "$ECR_REPO" ]; then
  echo "❌ Не удалось получить ECR repository URL"
  exit 1
fi

echo "✅ ECR Repository: $ECR_REPO"
echo ""

# 2. Сборка Docker образа
echo "🔨 Сборка Docker образа..."
cd "$FRONTEND_DIR"

# Проверка, что Dockerfile существует
if [ ! -f "Dockerfile" ]; then
  echo "❌ Dockerfile не найден в $FRONTEND_DIR"
  exit 1
fi

docker build --platform linux/amd64 -t doctor-agent-frontend:latest .

# 3. Тегирование и push в ECR
echo "📤 Загрузка образа в ECR..."
docker tag doctor-agent-frontend:latest "$ECR_REPO:latest"

# Логин в ECR
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_REPO"

docker push "$ECR_REPO:latest"

echo "✅ Образ загружен в ECR"
echo ""

# 4. Обновление ECS сервиса
echo "🔄 Обновление ECS сервиса..."
cd "$INFRA_DIR"
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
SERVICE_NAME=$(terraform output -raw frontend_ecs_service_name 2>/dev/null || echo "doctor-agent-frontend")

if [ -z "$SERVICE_NAME" ] || [ "$SERVICE_NAME" = "null" ]; then
  echo "⚠️ ECS Service еще не создан, создание..."
  terraform apply -var-file="terraform.tfvars" -auto-approve
  SERVICE_NAME=$(terraform output -raw frontend_ecs_service_name)
fi

aws ecs update-service \
  --cluster "$CLUSTER_NAME" \
  --service "$SERVICE_NAME" \
  --force-new-deployment \
  --region "$REGION" \
  --query 'service.[serviceName,status]' \
  --output table

echo ""
echo "✅ Деплой запущен!"
echo ""
echo "⏳ Ожидание запуска сервиса (это может занять 2-3 минуты)..."
sleep 30

# 5. Получение URL
ALB_DNS=$(terraform output -raw alb_dns_name 2>/dev/null || echo "")
if [ -n "$ALB_DNS" ] && [ "$ALB_DNS" != "null" ]; then
  echo ""
  echo "🌐 Frontend будет доступен по адресу:"
  echo "   http://$ALB_DNS"
  echo ""
  echo "📋 Полезные ссылки:"
  echo "   - Frontend: http://$ALB_DNS"
  echo "   - API: http://$ALB_DNS/api/v1"
  echo "   - Health: http://$ALB_DNS/health"
  echo ""
fi

echo "✅ Готово! Проверьте статус через:"
echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION"






