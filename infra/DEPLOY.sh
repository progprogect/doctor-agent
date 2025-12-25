#!/bin/bash
# Скрипт для деплоя инфраструктуры Doctor Agent MVP

set -e  # Остановка при ошибке

echo "🚀 Деплой инфраструктуры Doctor Agent MVP"
echo "=========================================="
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка зависимостей
echo "📋 Проверка зависимостей..."
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform не установлен${NC}"
    echo "Установите Terraform: https://www.terraform.io/downloads"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI не установлен${NC}"
    echo "Установите AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

echo -e "${GREEN}✅ Все зависимости установлены${NC}"

# Проверка AWS credentials
echo "🔐 Проверка AWS credentials..."
if ! aws sts get-caller-identity --region me-central-1 &> /dev/null; then
    echo -e "${RED}❌ AWS credentials не настроены${NC}"
    echo ""
    echo "Настройте AWS credentials одним из способов:"
    echo "1. aws configure"
    echo "2. Экспорт переменных окружения AWS_ACCESS_KEY_ID и AWS_SECRET_ACCESS_KEY"
    echo "3. AWS SSO: aws sso login"
    echo ""
    echo "Подробнее см. SETUP_AWS.md"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --region me-central-1 --query Account --output text)
echo -e "${GREEN}✅ AWS credentials настроены (Account: $AWS_ACCOUNT)${NC}"
echo ""

# Проверка terraform.tfvars
if [ ! -f "terraform.tfvars" ]; then
    echo -e "${YELLOW}⚠️  terraform.tfvars не найден, создаю из примера...${NC}"
    cp terraform.tfvars.example terraform.tfvars
    echo -e "${GREEN}✅ terraform.tfvars создан${NC}"
    echo -e "${YELLOW}⚠️  Пожалуйста, проверьте значения в terraform.tfvars перед продолжением${NC}"
    echo ""
fi

# Проверка секрета OpenAI
echo "🔐 Проверка секрета OpenAI..."
if aws secretsmanager describe-secret --region me-central-1 --secret-id doctor-agent/openai &> /dev/null; then
    echo -e "${GREEN}✅ Секрет doctor-agent/openai существует${NC}"
else
    echo -e "${YELLOW}⚠️  Секрет doctor-agent/openai не найден${NC}"
    echo "Создайте секрет командой:"
    echo "aws secretsmanager create-secret \\"
    echo "  --region me-central-1 \\"
    echo "  --name doctor-agent/openai \\"
    echo "  --description 'OpenAI API key' \\"
    echo "  --secret-string 'your-api-key-here'"
    echo ""
    read -p "Продолжить без секрета? (секрет можно создать позже) [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Инициализация Terraform
echo "🔧 Инициализация Terraform..."
terraform init
echo ""

# Планирование
echo "📊 Планирование изменений..."
terraform plan -var-file="terraform.tfvars" -out=tfplan
echo ""

# Подтверждение
echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Будет создана инфраструктура стоимостью ~$45-60/месяц${NC}"
echo ""
read -p "Применить изменения? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Отменено пользователем"
    exit 0
fi

# Применение
echo ""
echo "🚀 Применение конфигурации..."
echo "Это займет ~15-20 минут (большую часть времени займет создание OpenSearch domain)"
echo ""
terraform apply tfplan

echo ""
echo -e "${GREEN}✅ Инфраструктура успешно создана!${NC}"
echo ""
echo "📝 Следующие шаги:"
echo "1. Задайте пароль OpenSearch в Secrets Manager:"
echo "   aws secretsmanager put-secret-value \\"
echo "     --region me-central-1 \\"
echo "     --secret-id doctor-agent/opensearch \\"
echo "     --secret-string 'your-password'"
echo ""
echo "2. Соберите и загрузите Docker образ (см. README.md)"
echo "3. Проверьте статус ECS service:"
echo "   aws ecs describe-services \\"
echo "     --cluster doctor-agent-cluster \\"
echo "     --services doctor-agent-backend \\"
echo "     --region me-central-1"

