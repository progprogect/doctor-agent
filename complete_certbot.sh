#!/bin/bash
# Скрипт для завершения процесса получения сертификата после добавления DNS записи

set -e

DOMAIN="agents.elemental.ae"
CERT_DIR="/tmp/letsencrypt"
TXT_VALUE="Sjh4y0QnLzIXzswJvwwSH-Ueg95PaCdGI2YwlQPdNdY"

echo "=========================================="
echo "Завершение получения Let's Encrypt сертификата"
echo "=========================================="
echo ""
echo "Проверяю DNS запись..."

# Проверка DNS записи
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    DNS_VALUE=$(dig +short TXT "_acme-challenge.$DOMAIN" @8.8.8.8 | tr -d '"' | head -1)
    
    if [ "$DNS_VALUE" = "$TXT_VALUE" ]; then
        echo "✅ DNS запись найдена! Продолжаю..."
        break
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    echo "Попытка $ATTEMPT/$MAX_ATTEMPTS: DNS запись еще не распространилась..."
    echo "Ожидаемое значение: $TXT_VALUE"
    echo "Найденное значение: $DNS_VALUE"
    echo "Ожидание 10 секунд..."
    sleep 10
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "❌ DNS запись не найдена после $MAX_ATTEMPTS попыток"
    echo "Убедитесь, что вы добавили TXT запись:"
    echo "  Имя: _acme-challenge.agents"
    echo "  Значение: $TXT_VALUE"
    exit 1
fi

echo ""
echo "Продолжаю процесс certbot..."

# Продолжить certbot (нужно будет нажать Enter)
echo "" | certbot certonly \
  --manual \
  --preferred-challenges dns \
  --email mikitavalkunovich@gmail.com \
  --agree-tos \
  --no-eff-email \
  --config-dir "$CERT_DIR/config" \
  --work-dir "$CERT_DIR/work" \
  --logs-dir "$CERT_DIR/logs" \
  -d "$DOMAIN" \
  --manual-auth-hook /bin/true \
  --manual-cleanup-hook /bin/true 2>&1 || {
    echo ""
    echo "Попробую альтернативный метод..."
    # Если не сработало, попробуем еще раз с ожиданием
    sleep 5
    echo "" | certbot certonly \
      --manual \
      --preferred-challenges dns \
      --email mikitavalkunovich@gmail.com \
      --agree-tos \
      --no-eff-email \
      --config-dir "$CERT_DIR/config" \
      --work-dir "$CERT_DIR/work" \
      --logs-dir "$CERT_DIR/logs" \
      -d "$DOMAIN"
}

echo ""
echo "✅ Процесс завершен!"
echo ""
echo "Проверка файлов сертификата:"
ls -la "$CERT_DIR/config/live/$DOMAIN/" 2>/dev/null || echo "Файлы не найдены"

