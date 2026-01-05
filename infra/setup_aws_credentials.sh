#!/bin/bash
# Скрипт для настройки AWS credentials

echo "🔐 Настройка AWS Credentials для Doctor Agent"
echo "=============================================="
echo ""

# Проверка AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI не установлен"
    exit 1
fi

echo "Выберите способ настройки:"
echo "1) AWS Access Key ID и Secret Access Key (рекомендуется)"
echo "2) AWS SSO"
echo "3) Переменные окружения (для текущей сессии)"
echo ""
read -p "Ваш выбор [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "Настройка через Access Keys..."
        echo "Вам понадобятся:"
        echo "- AWS Access Key ID"
        echo "- AWS Secret Access Key"
        echo ""
        echo "Если у вас нет ключей, создайте их в AWS Console:"
        echo "https://console.aws.amazon.com/iam/home#/security_credentials"
        echo ""
        read -p "Нажмите Enter для продолжения..."
        
        # Запускаем интерактивную настройку
        aws configure
        
        # Устанавливаем регион по умолчанию если не был установлен
        if ! aws configure get region &> /dev/null; then
            aws configure set region me-central-1
        fi
        
        echo ""
        echo "✅ Настройка завершена!"
        ;;
    2)
        echo ""
        echo "Настройка через AWS SSO..."
        read -p "Введите имя SSO профиля: " profile_name
        read -p "Введите SSO start URL: " sso_start_url
        read -p "Введите SSO region: " sso_region
        read -p "Введите account ID (760221990195): " account_id
        account_id=${account_id:-760221990195}
        
        aws configure sso --profile $profile_name
        export AWS_PROFILE=$profile_name
        
        echo ""
        echo "Выполните вход:"
        echo "aws sso login --profile $profile_name"
        echo ""
        echo "И установите профиль:"
        echo "export AWS_PROFILE=$profile_name"
        ;;
    3)
        echo ""
        echo "Настройка через переменные окружения..."
        read -p "AWS Access Key ID: " access_key
        read -p "AWS Secret Access Key: " secret_key
        
        export AWS_ACCESS_KEY_ID=$access_key
        export AWS_SECRET_ACCESS_KEY=$secret_key
        export AWS_DEFAULT_REGION=me-central-1
        
        echo ""
        echo "✅ Переменные окружения установлены для текущей сессии"
        echo ""
        echo "Для постоянной настройки добавьте в ~/.zshrc или ~/.bashrc:"
        echo "export AWS_ACCESS_KEY_ID=\"$access_key\""
        echo "export AWS_SECRET_ACCESS_KEY=\"$secret_key\""
        echo "export AWS_DEFAULT_REGION=me-central-1"
        ;;
    *)
        echo "Неверный выбор"
        exit 1
        ;;
esac

# Проверка credentials
echo ""
echo "🔍 Проверка настроек..."
if aws sts get-caller-identity --region me-central-1 &> /dev/null; then
    ACCOUNT=$(aws sts get-caller-identity --region me-central-1 --query Account --output text)
    USER=$(aws sts get-caller-identity --region me-central-1 --query Arn --output text)
    echo "✅ AWS credentials настроены успешно!"
    echo "   Account ID: $ACCOUNT"
    echo "   User/Role: $USER"
    echo ""
    echo "Теперь можно запустить деплой:"
    echo "  cd infra"
    echo "  ./DEPLOY.sh"
else
    echo "❌ Не удалось проверить credentials"
    echo "Проверьте правильность введенных данных"
fi







