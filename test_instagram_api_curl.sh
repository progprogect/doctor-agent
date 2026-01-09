#!/bin/bash
# Тестирование Instagram Graph API через curl

ACCESS_TOKEN="IGAAXjRiKjwKFBZAGFRU1RTcUdhU1UwYWhvTndCdWJNSEFGN1FEZA1M5N0Rhekp3MDE4NUpKanlwd1haSHpubmRFZAk8xbXF1UF9CRmRZATHRqWU44QURYVlcwZA2VhaVV1MngwYUdSeDRXVTdEcWhCNmhpLTR2S3NrRWxzQU5UcEQ5dwZDZD"
ACCOUNT_ID_WEBHOOK="17841458318357324"  # entry.id из webhook
ACCOUNT_ID_REAL="25638311079121978"  # Реальный Account ID из API ответа
ACCOUNT_ID="$ACCOUNT_ID_REAL"  # Используем реальный ID
MESSAGE_ID="aWdfZAG1faXRlbToxOklHTWVzc2FnZAUlEOjE3ODQxNDU4MzE4MzU3MzI0OjM0MDI4MjM2Njg0MTcxMDMwMTI0NDI3NjExODk0MjI3MzE3ODI0MTozMjYxMzE2NDUzNzQyMzA0ODA3ODk1NzgxNjE4Mzc4MzQyNAZDZD"

INSTAGRAM_API="https://graph.instagram.com/v21.0"
FACEBOOK_API="https://graph.facebook.com/v21.0"

echo "=================================================================================="
echo "🧪 ТЕСТИРОВАНИЕ INSTAGRAM GRAPH API ENDPOINTS"
echo "=================================================================================="
echo ""
echo "Account ID: $ACCOUNT_ID"
echo "Message ID: ${MESSAGE_ID:0:50}..."
echo ""

# Тест 1: Информация об аккаунте
echo "=================================================================================="
echo "ТЕСТ 1: Получение информации об аккаунте"
echo "=================================================================================="
echo ""
echo "🔍 GET $INSTAGRAM_API/$ACCOUNT_ID"
echo ""
curl -s -X GET "$INSTAGRAM_API/$ACCOUNT_ID?fields=id,username,account_type" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' || echo "Ошибка или jq не установлен"
echo ""

# Тест 2: Список conversations
echo "=================================================================================="
echo "ТЕСТ 2: Получение списка conversations"
echo "=================================================================================="
echo ""
echo "🔍 GET $INSTAGRAM_API/$ACCOUNT_ID/conversations"
echo ""
CONVERSATIONS_RESPONSE=$(curl -s -X GET "$INSTAGRAM_API/$ACCOUNT_ID/conversations?fields=id,participants,updated_time" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo "$CONVERSATIONS_RESPONSE" | jq '.' || echo "$CONVERSATIONS_RESPONSE"
echo ""

# Извлечь первый conversation ID если есть
FIRST_CONV_ID=$(echo "$CONVERSATIONS_RESPONSE" | jq -r '.data[0].id // empty' 2>/dev/null)

if [ -n "$FIRST_CONV_ID" ] && [ "$FIRST_CONV_ID" != "null" ]; then
  echo "✅ Найден conversation ID: $FIRST_CONV_ID"
  echo ""
  
  # Тест 3: Messages из conversation
  echo "=================================================================================="
  echo "ТЕСТ 3: Получение messages из conversation"
  echo "=================================================================================="
  echo ""
  echo "🔍 GET $INSTAGRAM_API/$FIRST_CONV_ID/messages"
  echo ""
  MESSAGES_RESPONSE=$(curl -s -X GET "$INSTAGRAM_API/$FIRST_CONV_ID/messages?fields=id,from,to,message,created_time" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  echo "$MESSAGES_RESPONSE" | jq '.' || echo "$MESSAGES_RESPONSE"
  echo ""
  
  # Поиск сообщения с нужным message_id
  FOUND_MESSAGE=$(echo "$MESSAGES_RESPONSE" | jq --arg mid "$MESSAGE_ID" '.data[] | select(.id == $mid)' 2>/dev/null)
  if [ -n "$FOUND_MESSAGE" ]; then
    echo "🎯 НАЙДЕНО СООБЩЕНИЕ!"
    echo "$FOUND_MESSAGE" | jq '.'
    SENDER_ID=$(echo "$FOUND_MESSAGE" | jq -r '.from.id // empty' 2>/dev/null)
    if [ -n "$SENDER_ID" ] && [ "$SENDER_ID" != "null" ]; then
      echo ""
      echo "✅ SENDER ID НАЙДЕН: $SENDER_ID"
    fi
  else
    echo "⚠️  Сообщение с message_id не найдено в этом conversation"
  fi
else
  echo "⚠️  Conversation ID не найден, пропускаем тест 3"
fi

# Тест 4: Прямое получение информации о сообщении
echo ""
echo "=================================================================================="
echo "ТЕСТ 4: Прямое получение информации о сообщении по message_id"
echo "=================================================================================="
echo ""
echo "🔍 GET $INSTAGRAM_API/$MESSAGE_ID"
echo ""
curl -s -X GET "$INSTAGRAM_API/$MESSAGE_ID?fields=id,from,to,message" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' || echo "Ошибка или jq не установлен"
echo ""

# Тест 5: Альтернативные endpoints через Facebook Graph API
echo "=================================================================================="
echo "ТЕСТ 5: Альтернативные endpoints через Facebook Graph API"
echo "=================================================================================="
echo ""
echo "🔍 GET $FACEBOOK_API/$ACCOUNT_ID/conversations"
echo ""
curl -s -X GET "$FACEBOOK_API/$ACCOUNT_ID/conversations?fields=id,participants" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.' || echo "Ошибка или jq не установлен"
echo ""

echo "=================================================================================="
echo "✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО"
echo "=================================================================================="

