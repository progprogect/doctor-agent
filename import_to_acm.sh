#!/bin/bash
# Скрипт для импорта Let's Encrypt сертификата в AWS ACM

set -e

DOMAIN="agents.elemental.ae"
CERT_DIR="/tmp/letsencrypt/config/live/$DOMAIN"
REGION="me-central-1"

echo "=========================================="
echo "Импорт Let's Encrypt сертификата в AWS ACM"
echo "=========================================="
echo ""

# Проверка наличия файлов
if [ ! -f "$CERT_DIR/fullchain.pem" ]; then
    echo "❌ Ошибка: Сертификат не найден в $CERT_DIR"
    echo "Сначала выполните: ./get_letsencrypt_cert.sh"
    exit 1
fi

# Проверка AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "⚠️  AWS credentials не установлены"
    echo "Установите:"
    echo "export AWS_ACCESS_KEY_ID=\"...\""
    echo "export AWS_SECRET_ACCESS_KEY=\"...\""
    exit 1
fi

export AWS_DEFAULT_REGION="$REGION"

echo "Подготовка файлов сертификата..."

# Создать временные файлы
TMP_DIR="/tmp/acm_import_$$"
mkdir -p "$TMP_DIR"

# Использовать fullchain.pem (уже содержит cert + chain)
cp "$CERT_DIR/fullchain.pem" "$TMP_DIR/certificate.pem"
cp "$CERT_DIR/privkey.pem" "$TMP_DIR/private-key.pem"
cp "$CERT_DIR/chain.pem" "$TMP_DIR/certificate-chain.pem"

echo "Импорт сертификата в AWS ACM (регион: $REGION)..."

# Импортировать в ACM
CERT_ARN=$(aws acm import-certificate \
  --certificate fileb://"$TMP_DIR/certificate.pem" \
  --private-key fileb://"$TMP_DIR/private-key.pem" \
  --certificate-chain fileb://"$TMP_DIR/certificate-chain.pem" \
  --region "$REGION" \
  --tags Key=Name,Value="$DOMAIN-letsencrypt" \
  --query 'CertificateArn' \
  --output text)

echo ""
echo "✅ Сертификат успешно импортирован в AWS ACM!"
echo ""
echo "Certificate ARN:"
echo "$CERT_ARN"
echo ""
echo "Сохраните этот ARN - он понадобится для обновления Terraform"
echo ""

# Сохранить ARN в файл
echo "$CERT_ARN" > /tmp/acm_cert_arn.txt
echo "ARN сохранен в /tmp/acm_cert_arn.txt"

# Очистить временные файлы (но оставить ключи на случай ошибки)
# rm -rf "$TMP_DIR"

echo ""
echo "Следующий шаг: Обновить Terraform конфигурацию с этим ARN"

