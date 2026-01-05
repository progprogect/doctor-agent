# GitHub Actions CI/CD Setup

## Что делает этот CI/CD

При пуше в ветку `main` автоматически:
1. Собирает Docker образ для Linux (amd64)
2. Загружает образ в AWS ECR
3. Обновляет ECS сервис для автоматического деплоя

## Настройка (один раз)

### 1. Добавьте секреты в GitHub

1. Перейдите в ваш репозиторий на GitHub
2. Нажмите **Settings** → **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**
4. Добавьте следующие секреты:

   - **Имя:** `AWS_ACCESS_KEY_ID`
     **Значение:** (ваш AWS Access Key ID)

   - **Имя:** `AWS_SECRET_ACCESS_KEY`
     **Значение:** (ваш AWS Secret Access Key)

### 2. Проверка

После добавления секретов:
- При следующем пуше в `main` автоматически запустится деплой
- Можно также запустить вручную: **Actions** → выберите workflow → **Run workflow**

## Как это работает

### Backend workflow
- Триггер: изменения в `backend/` или сам workflow файл
- Собирает образ из `backend/Dockerfile`
- Деплоит в `doctor-agent-backend` сервис

### Frontend workflow
- Триггер: изменения в `frontend/` или сам workflow файл
- Собирает образ из `frontend/Dockerfile`
- Деплоит в `doctor-agent-frontend` сервис

## Мониторинг

Проверить статус деплоя:
- GitHub: **Actions** вкладка в репозитории
- AWS Console: ECS → Clusters → doctor-agent-cluster → Services

## Ручной запуск

Если нужно задеплоить вручную:
1. GitHub → **Actions**
2. Выберите нужный workflow (Deploy Backend или Deploy Frontend)
3. Нажмите **Run workflow** → **Run workflow**

