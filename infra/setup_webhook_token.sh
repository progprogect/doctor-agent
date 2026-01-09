#!/bin/bash
# Скрипт для добавления INSTAGRAM_WEBHOOK_VERIFY_TOKEN в ECS task definition

set -e

REGION="me-central-1"
TASK_DEFINITION="doctor-agent-backend"
WEBHOOK_TOKEN="RBrGdpk3pGB2LNJvte1vS6W-UN6S41b-GKC6r0ARXaE"

echo "🔧 Настройка INSTAGRAM_WEBHOOK_VERIFY_TOKEN в ECS"
echo ""

# Экспорт AWS credentials если нужно
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "⚠️  AWS credentials не установлены"
    echo "Установите:"
    echo "export AWS_ACCESS_KEY_ID=\"...\""
    echo "export AWS_SECRET_ACCESS_KEY=\"...\""
    exit 1
fi

# Получить текущую task definition
echo "📥 Получение текущей task definition..."
aws ecs describe-task-definition \
    --task-definition "$TASK_DEFINITION" \
    --region "$REGION" \
    --query 'taskDefinition' > /tmp/task-definition.json

echo "✅ Task definition получена"

# Проверить, есть ли уже токен
if grep -q "INSTAGRAM_WEBHOOK_VERIFY_TOKEN" /tmp/task-definition.json; then
    echo "⚠️  INSTAGRAM_WEBHOOK_VERIFY_TOKEN уже существует в task definition"
    echo "Обновляю значение..."
    
    # Обновить значение через jq
    cat /tmp/task-definition.json | jq --arg token "$WEBHOOK_TOKEN" '
        .containerDefinitions[0].environment = (
            .containerDefinitions[0].environment | 
            map(if .name == "INSTAGRAM_WEBHOOK_VERIFY_TOKEN" then .value = $token else . end)
        )
    ' > /tmp/task-definition-updated.json
else
    echo "➕ Добавление INSTAGRAM_WEBHOOK_VERIFY_TOKEN..."
    
    # Добавить новую переменную окружения
    cat /tmp/task-definition.json | jq --arg token "$WEBHOOK_TOKEN" '
        .containerDefinitions[0].environment += [{
            "name": "INSTAGRAM_WEBHOOK_VERIFY_TOKEN",
            "value": $token
        }]
    ' > /tmp/task-definition-updated.json
fi

# Удалить поля, которые нельзя передавать при регистрации
cat /tmp/task-definition-updated.json | jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' > /tmp/task-definition-final.json

# Зарегистрировать новую версию
echo "📤 Регистрация новой версии task definition..."
NEW_REVISION=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/task-definition-final.json \
    --region "$REGION" \
    --query 'taskDefinition.revision' \
    --output text)

echo "✅ Новая версия task definition зарегистрирована: revision $NEW_REVISION"

# Обновить сервис
echo "🔄 Обновление ECS сервиса..."
aws ecs update-service \
    --cluster doctor-agent-cluster \
    --service doctor-agent-backend \
    --task-definition "$TASK_DEFINITION:$NEW_REVISION" \
    --force-new-deployment \
    --region "$REGION" > /dev/null

echo "✅ Сервис обновлен, запускается новый деплой..."
echo ""
echo "⏳ Ожидание завершения деплоя (это может занять 2-3 минуты)..."

aws ecs wait services-stable \
    --cluster doctor-agent-cluster \
    --services doctor-agent-backend \
    --region "$REGION" || echo "⚠️  Wait timeout, но деплой запущен"

echo ""
echo "✅ Готово!"
echo ""
echo "📋 Проверка:"
aws ecs describe-services \
    --cluster doctor-agent-cluster \
    --services doctor-agent-backend \
    --region "$REGION" \
    --query 'services[0].[runningCount,desiredCount,status]' \
    --output table

echo ""
echo "🧪 Тест верификации webhook:"
echo "curl \"https://doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com/api/v1/instagram/webhook?hub.mode=subscribe&hub.verify_token=$WEBHOOK_TOKEN&hub.challenge=test123\""

