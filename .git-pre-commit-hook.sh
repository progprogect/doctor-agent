#!/bin/bash
# Pre-commit hook для удаления AWS credentials перед коммитом
# Установка: cp .git-pre-commit-hook.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Паттерны для поиска credentials
ACCESS_KEY_PATTERN="AKIA[0-9A-Z]{16}"
SECRET_KEY_PATTERN="[A-Za-z0-9+/]{40}"

# Файлы для проверки
FILES_TO_CHECK=$(git diff --cached --name-only | grep -E '\.(md|sh|tf|py|js|ts|tsx)$')

if [ -z "$FILES_TO_CHECK" ]; then
    exit 0
fi

FOUND_SECRETS=false

for file in $FILES_TO_CHECK; do
    if [ -f "$file" ]; then
        # Проверка на Access Key ID
        if grep -qE "$ACCESS_KEY_PATTERN" "$file"; then
            echo -e "${RED}❌ Обнаружен AWS Access Key ID в файле: $file${NC}"
            FOUND_SECRETS=true
        fi
        
        # Проверка на Secret Access Key (общий паттерн для длинных base64 строк)
        if grep -qE "[A-Za-z0-9+/]{38,}" "$file" && ! grep -qE "YOUR_AWS|PLACEHOLDER|EXAMPLE" "$file"; then
            # Дополнительная проверка: если это похоже на секретный ключ
            if grep -qE "SECRET.*KEY|AWS_SECRET" "$file"; then
                echo -e "${RED}❌ Обнаружен возможный AWS Secret Access Key в файле: $file${NC}"
                FOUND_SECRETS=true
            fi
        fi
    fi
done

if [ "$FOUND_SECRETS" = true ]; then
    echo ""
    echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Обнаружены AWS credentials в файлах!${NC}"
    echo -e "${YELLOW}Удалите их перед коммитом или используйте:${NC}"
    echo -e "${GREEN}  git commit --no-verify${NC} (не рекомендуется)"
    echo ""
    exit 1
fi

exit 0

