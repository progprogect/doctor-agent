#!/bin/bash
# Автоматический деплой и тестирование Instagram webhook исправлений

set -e

echo "🚀 Автоматический деплой и тестирование"
echo "========================================"
echo ""

REGION="me-central-1"
INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$INFRA_DIR/.." && pwd)"

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Функция проверки AWS credentials
check_aws_credentials() {
    echo "🔐 Проверка AWS credentials..."
    if aws sts get-caller-identity --region "$REGION" &>/dev/null; then
        AWS_ACCOUNT=$(aws sts get-caller-identity --region "$REGION" --query Account --output text)
        echo -e "${GREEN}✅ AWS credentials настроены (Account: $AWS_ACCOUNT)${NC}"
        return 0
    else
        echo -e "${RED}❌ AWS credentials не настроены${NC}"
        echo ""
        echo "Настройте AWS credentials одним из способов:"
        echo "1. aws configure"
        echo "2. Экспорт переменных: export AWS_ACCESS_KEY_ID=... export AWS_SECRET_ACCESS_KEY=..."
        echo "3. AWS SSO: aws sso login"
        return 1
    fi
}

# Функция деплоя backend
deploy_backend() {
    echo ""
    echo "📦 Деплой backend..."
    cd "$INFRA_DIR"
    bash DEPLOY_BACKEND.sh
}

# Функция деплоя frontend
deploy_frontend() {
    echo ""
    echo "📦 Деплой frontend..."
    cd "$INFRA_DIR"
    bash DEPLOY_FRONTEND.sh
}

# Функция получения URL сервера
get_server_url() {
    cd "$INFRA_DIR"
    ALB_DNS=$(terraform output -raw alb_dns_name 2>/dev/null || echo "")
    if [ -n "$ALB_DNS" ] && [ "$ALB_DNS" != "null" ]; then
        echo "https://$ALB_DNS"
    else
        echo ""
    fi
}

# Функция тестирования webhook endpoint
test_webhook_endpoint() {
    local SERVER_URL=$1
    echo ""
    echo "🧪 Тестирование webhook endpoint..."
    
    if [ -z "$SERVER_URL" ]; then
        echo -e "${YELLOW}⚠️  Не удалось получить URL сервера${NC}"
        return 1
    fi
    
    echo "Проверка health endpoint: $SERVER_URL/health"
    if curl -s -f "$SERVER_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Сервер доступен${NC}"
        return 0
    else
        echo -e "${RED}❌ Сервер недоступен${NC}"
        return 1
    fi
}

# Функция проверки последних webhook событий
check_webhook_events() {
    local SERVER_URL=$1
    echo ""
    echo "📨 Проверка последних webhook событий..."
    
    if [ -z "$SERVER_URL" ]; then
        echo -e "${YELLOW}⚠️  Не удалось получить URL сервера${NC}"
        return 1
    fi
    
    EVENTS_RESPONSE=$(curl -s "$SERVER_URL/api/v1/webhook-events/recent?limit=5" 2>/dev/null || echo "")
    if [ -n "$EVENTS_RESPONSE" ]; then
        EVENT_COUNT=$(echo "$EVENTS_RESPONSE" | grep -o '"total":[0-9]*' | grep -o '[0-9]*' || echo "0")
        echo "Найдено webhook событий: $EVENT_COUNT"
        
        # Проверяем наличие sender_id в событиях
        if echo "$EVENTS_RESPONSE" | grep -q "sender_id"; then
            echo -e "${GREEN}✅ Найдены события с sender_id${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  События без sender_id (возможно, это message_edit события)${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  Не удалось получить webhook события${NC}"
        return 1
    fi
}

# Основной процесс
main() {
    # Проверка credentials
    if ! check_aws_credentials; then
        echo ""
        echo -e "${RED}❌ Не удалось продолжить без AWS credentials${NC}"
        exit 1
    fi
    
    # Деплой backend
    if deploy_backend; then
        echo -e "${GREEN}✅ Backend задеплоен${NC}"
    else
        echo -e "${RED}❌ Ошибка деплоя backend${NC}"
        exit 1
    fi
    
    # Деплой frontend
    if deploy_frontend; then
        echo -e "${GREEN}✅ Frontend задеплоен${NC}"
    else
        echo -e "${YELLOW}⚠️  Ошибка деплоя frontend (может быть не критично)${NC}"
    fi
    
    # Получение URL сервера
    echo ""
    echo "⏳ Ожидание запуска сервисов (30 секунд)..."
    sleep 30
    
    SERVER_URL=$(get_server_url)
    if [ -n "$SERVER_URL" ]; then
        echo -e "${GREEN}✅ URL сервера: $SERVER_URL${NC}"
    else
        echo -e "${YELLOW}⚠️  Не удалось получить URL сервера${NC}"
    fi
    
    # Тестирование
    if [ -n "$SERVER_URL" ]; then
        test_webhook_endpoint "$SERVER_URL"
        check_webhook_events "$SERVER_URL"
    fi
    
    echo ""
    echo "=" * 80
    echo -e "${GREEN}✅ Деплой завершен!${NC}"
    echo ""
    if [ -n "$SERVER_URL" ]; then
        echo "🌐 Тестовая страница: $SERVER_URL/admin/instagram-test"
        echo "📊 Health check: $SERVER_URL/health"
    fi
    echo ""
    echo "💡 Следующие шаги:"
    echo "   1. Откройте тестовую страницу Instagram"
    echo "   2. Отправьте новое сообщение агенту в Instagram"
    echo "   3. Проверьте webhook событие на тестовой странице"
    echo "   4. Используйте Sender ID для отправки ответа"
}

# Запуск
main

