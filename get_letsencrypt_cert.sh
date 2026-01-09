#!/bin/bash
# Скрипт для получения Let's Encrypt сертификата

set -e

DOMAIN="agents.elemental.ae"
EMAIL="mikitavalkunovich@gmail.com"
CERT_DIR="/tmp/letsencrypt"

echo "=========================================="
echo "Получение Let's Encrypt сертификата"
echo "Домен: $DOMAIN"
echo "=========================================="
echo ""

# Создать директории
mkdir -p "$CERT_DIR"/{config,work,logs}

echo "Запрашиваю сертификат..."
echo ""
echo "⚠️  ВАЖНО: Certbot попросит добавить TXT запись в DNS!"
echo "Когда увидите запрос с TXT значением:"
echo "1. Добавьте TXT запись в панели DNS регистратора"
echo "2. Имя записи: _acme-challenge.agents"
echo "3. Значение: [будет показано certbot]"
echo "4. После добавления нажмите Enter в этом терминале"
echo ""
echo "Нажмите Enter чтобы начать..."
read

certbot certonly \
  --manual \
  --preferred-challenges dns \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  --config-dir "$CERT_DIR/config" \
  --work-dir "$CERT_DIR/work" \
  --logs-dir "$CERT_DIR/logs" \
  -d "$DOMAIN"

echo ""
echo "✅ Сертификат получен!"
echo ""
echo "Файлы сертификата:"
echo "  Cert: $CERT_DIR/config/live/$DOMAIN/cert.pem"
echo "  Key:  $CERT_DIR/config/live/$DOMAIN/privkey.pem"
echo "  Chain: $CERT_DIR/config/live/$DOMAIN/chain.pem"
echo "  Fullchain: $CERT_DIR/config/live/$DOMAIN/fullchain.pem"

