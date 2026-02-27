# Развёртывание AI Agents CRM на Railway

Документ описывает адаптацию проекта для развёртывания на [Railway](https://railway.app), список переменных окружения и шаги настройки.

---

## 1. Анализ текущей архитектуры

### Зависимости проекта

| Компонент | Использование | Railway-совместимость |
|-----------|----------------|------------------------|
| **DynamoDB** | Основное хранилище (conversations, messages, agents, audit_logs, channel_bindings, instagram_profiles, notification_configs, RAG documents) | ✅ Подключается через AWS credentials |
| **OpenSearch** | Не используется (заменён на DynamoDB RAG) | ⏭️ Пропустить |
| **Redis** | Не используется (заменён на DynamoDB Cache) | ⏭️ Пропустить |
| **AWS Secrets Manager** | Опционально для OpenAI API key | ⚠️ Можно заменить на `OPENAI_API_KEY` в env |
| **OpenAI API** | LLM, embeddings, moderation | ✅ Через env `OPENAI_API_KEY` |

### Вывод

Проект уже оптимизирован: **Redis и OpenSearch не требуются**. Используются DynamoDB (данные + кэш + RAG). Для Railway достаточно:

1. Подключить DynamoDB (через AWS credentials или managed DynamoDB)
2. Задать переменные окружения
3. Адаптировать PORT (уже сделано в Dockerfile)

---

## 2. Адаптации для Railway

### 2.1 Выполненные изменения

- **Backend Dockerfile**: использует `PORT` из окружения (Railway передаёт его автоматически), fallback 8000 для локальной разработки.
- **Healthcheck**: проверяет порт из `PORT`.

### 2.2 Структура деплоя на Railway

Рекомендуемая схема — **два сервиса**:

1. **Backend** (FastAPI) — корневая папка `backend/`, Dockerfile
2. **Frontend** (Next.js) — корневая папка `frontend/`, Dockerfile

Либо один сервис, если frontend раздаётся через backend (потребует доработки).

### 2.3 База данных

База создаётся отдельно. Варианты:

- **AWS DynamoDB** — создать таблицы в AWS и подключить через credentials.
- **DynamoDB Local / альтернативы** — если планируется миграция на другую БД, это отдельный этап.

Подключение в Railway — через переменные окружения (см. раздел 4).

---

## 3. Создание таблиц DynamoDB

Если используется AWS DynamoDB, таблицы создаются через Terraform (`infra/`) или вручную. Список таблиц:

| Таблица | Назначение |
|---------|------------|
| `doctor-agent-conversations` | Диалоги |
| `doctor-agent-messages` | Сообщения |
| `doctor-agent-agents` | Конфигурация агентов |
| `doctor-agent-audit-logs` | Аудит |
| `doctor-agent-channel-bindings` | Привязки каналов (Instagram, Telegram) |
| `doctor-agent-instagram-profiles` | Профили Instagram |
| `doctor-agent-notification-configs` | Конфигурация уведомлений |
| `doctor-agent-rag-documents` | RAG-документы (векторный поиск) |

Схемы таблиц — в `infra/main.tf`.

---

## 4. Переменные окружения для Railway

### 4.1 Backend (обязательные)

| Переменная | Описание | Пример |
|------------|----------|--------|
| `OPENAI_API_KEY` | Ключ OpenAI API | `sk-...` |
| `ADMIN_TOKEN` | Токен для админ-API | Случайная строка (например, `openssl rand -hex 32`) |
| `AWS_ACCESS_KEY_ID` | AWS Access Key (для DynamoDB) | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key | `...` |
| `AWS_REGION` | Регион AWS | `us-east-1` |

### 4.2 Backend (DynamoDB — подключение)

| Переменная | Описание |
|------------|----------|
| `DYNAMODB_ENDPOINT_URL` | **Не задавать** для AWS DynamoDB. Задавать только для DynamoDB Local или совместимых сервисов. |

### 4.3 Backend (DynamoDB — имена таблиц)

Если имена таблиц отличаются от дефолтных:

| Переменная | По умолчанию |
|------------|--------------|
| `DYNAMODB_TABLE_CONVERSATIONS` | `doctor-agent-conversations` |
| `DYNAMODB_TABLE_MESSAGES` | `doctor-agent-messages` |
| `DYNAMODB_TABLE_AGENTS` | `doctor-agent-agents` |
| `DYNAMODB_TABLE_AUDIT_LOGS` | `doctor-agent-audit-logs` |
| `DYNAMODB_TABLE_CHANNEL_BINDINGS` | `doctor-agent-channel-bindings` |
| `DYNAMODB_TABLE_INSTAGRAM_PROFILES` | `doctor-agent-instagram-profiles` |
| `DYNAMODB_TABLE_NOTIFICATION_CONFIGS` | `doctor-agent-notification-configs` |

Таблица RAG (`doctor-agent-rag-documents`) задаётся в коде; при необходимости её можно вынести в конфиг.

### 4.4 Backend (опциональные)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `ENVIRONMENT` | Окружение | `production` |
| `DEBUG` | Режим отладки | `false` |
| `CORS_ORIGINS` | CORS (JSON-массив или через запятую) | `["https://your-frontend.railway.app"]` |
| `RATE_LIMIT_PER_MINUTE` | Лимит запросов в минуту | `60` |
| `OPENAI_MODEL` | Модель OpenAI | `gpt-4o-mini` |
| `MESSAGE_TTL_HOURS` | TTL сообщений (часы) | `48` |

### 4.5 Backend (каналы — при использовании)

| Переменная | Описание |
|------------|----------|
| `INSTAGRAM_WEBHOOK_VERIFY_TOKEN` | Токен верификации webhook Instagram |
| `INSTAGRAM_APP_SECRET` | App Secret для проверки подписи webhook |

### 4.6 Backend (Secrets Manager — опционально)

Если OpenAI API key хранится в AWS Secrets Manager вместо env:

| Переменная | Описание |
|------------|----------|
| `SECRETS_MANAGER_OPENAI_KEY_NAME` | Имя секрета в Secrets Manager |
| `SECRETS_MANAGER_REGION` | Регион Secrets Manager (если отличается от AWS_REGION) |

При наличии `OPENAI_API_KEY` в env Secrets Manager не используется.

### 4.7 Frontend (обязательные при отдельном деплое)

| Переменная | Описание | Пример |
|------------|----------|--------|
| `NEXT_PUBLIC_API_URL` | URL backend API | `https://your-backend.railway.app` |
| `NEXT_PUBLIC_WS_URL` | URL WebSocket | `wss://your-backend.railway.app` |

Если frontend и backend на одном домене (через proxy), можно использовать относительные URL — тогда эти переменные не нужны.

### 4.8 Railway-специфичные

| Переменная | Описание |
|------------|----------|
| `PORT` | Задаётся Railway автоматически. Backend уже использует его. |

---

## 5. Минимальный набор для стабильной работы

### Backend

```
OPENAI_API_KEY=sk-...
ADMIN_TOKEN=<сгенерировать>
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=["https://your-frontend.railway.app"]
```

### Frontend (если деплоится отдельно)

```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_WS_URL=wss://your-backend.railway.app
```

---

## 6. Шаги развёртывания

1. Создать проект в Railway.
2. Создать сервис Backend:
   - Root Directory: `backend`
   - Dockerfile: `backend/Dockerfile`
   - Добавить переменные окружения из раздела 5.
3. Создать сервис Frontend (если нужен):
   - Root Directory: `frontend`
   - Dockerfile: `frontend/Dockerfile`
   - Добавить `NEXT_PUBLIC_API_URL` и `NEXT_PUBLIC_WS_URL` с URL backend.
4. Создать и подключить DynamoDB (AWS или другой провайдер).
5. Сгенерировать домены в Railway для backend и frontend.
6. Обновить `CORS_ORIGINS` на фактический URL frontend.

---

## 7. Проверка после деплоя

- Backend: `https://your-backend.railway.app/health` → `{"status":"healthy",...}`
- API docs: `https://your-backend.railway.app/docs`
- Frontend: открыть в браузере и проверить чат и админку.

---

## 8. Риски и ограничения

| Риск | Рекомендация |
|------|--------------|
| AWS credentials в env | Использовать Railway Variables (зашифрованы). Для production — рассмотреть IAM roles / OIDC. |
| Cold start | Railway может останавливать неактивные сервисы. Настроить Always-on при необходимости. |
| WebSocket | Railway поддерживает WebSocket. Убедиться, что URL frontend использует `wss://` для production. |

---

## 9. Ссылки

- [Railway Docs — Variables](https://docs.railway.app/reference/variables)
- [Railway Docs — Healthchecks](https://docs.railway.app/diagnose/healthchecks)
- Репозиторий: [AI-Agents-CRM](https://github.com/progprogect/AI-Agents-CRM)
