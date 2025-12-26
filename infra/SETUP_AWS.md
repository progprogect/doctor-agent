# Настройка AWS Credentials

Для работы Terraform нужны AWS credentials. Выполните следующие шаги:

## Вариант 1: AWS CLI configure (рекомендуется)

```bash
aws configure
```

Введите следующие данные:
- **AWS Access Key ID**: ваш Access Key ID
- **AWS Secret Access Key**: ваш Secret Access Key  
- **Default region name**: `me-central-1`
- **Default output format**: `json` (или просто нажмите Enter)

## Вариант 2: Переменные окружения

```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="me-central-1"
```

## Вариант 3: AWS SSO (если используете)

```bash
aws sso login --profile your-profile-name
export AWS_PROFILE=your-profile-name
```

## Проверка настроек

После настройки проверьте:

```bash
aws sts get-caller-identity --region me-central-1
```

Должен вернуться ваш AWS Account ID: `760221990195`

## После настройки credentials

Выполните:

```bash
cd infra
terraform init
terraform plan -var-file="terraform.tfvars"
```




