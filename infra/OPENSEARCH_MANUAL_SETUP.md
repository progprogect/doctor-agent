# Инструкция: Создание OpenSearch вручную в AWS Console

## Шаги создания OpenSearch Domain

1. **Откройте AWS Console** → **OpenSearch Service** → **me-central-1**

2. **Нажмите "Create domain"**

3. **Настройки домена:**
   - **Domain name**: `doctor-agent-opensearch`
   - **Deployment type**: `Development and testing` (single node)
   - **Version**: `OpenSearch 2.11`

4. **Hardware configuration:**
   - **Instance type**: `t3.small.search`
   - **Number of nodes**: `1` (для single-node)

5. **Storage configuration:**
   - **EBS storage type**: `General Purpose (SSD) gp3`
   - **EBS storage size per node**: `20 GB`

6. **Network:**
   - **VPC**: выберите `vpc-03cb895f29b20a53e`
   - **Subnets**: выберите **только одну** подсеть: `subnet-090c04ef58faa7ee1` (Doctor-agent-subnet-private1-me-central-1a)
   - **Security groups**: выберите `opensearch-sg` (sg-0c9ac0a356a74639e)
   - **Enable fine-grained access control**: `Yes`
   - **Master user**: `Internal user database`
   - **Master username**: `admin`
   - **Master password**: создайте надежный пароль (минимум: заглавная, строчная, цифра, спецсимвол)
     - Пример: `DoctorAgent2024!OpenSearch`
   - **Confirm master password**: повторите пароль

7. **Access policy:**
   - Выберите **VPC access** (уже выбрано через VPC настройки)

8. **Encryption:**
   - **Encryption at rest**: `Enable`
   - **Node-to-node encryption**: `Enable`

9. **Fine-grained access control:**
   - **Enable fine-grained access control**: `Yes` (уже включено выше)

10. **Review и Create domain**

11. **Дождитесь создания** (займет ~10-15 минут)
    - Статус должен стать `Active`

## После создания

Когда домен будет готов, сообщите мне:
- **Domain endpoint** (например: `doctor-agent-opensearch-xxxxx.me-central-1.es.amazonaws.com`)
- **Domain ARN** (можно скопировать из консоли)

Я импортирую его в Terraform и продолжу с Docker образом.

## Сохранение пароля в Secrets Manager

После создания домена выполните команду (замените `YOUR_PASSWORD` на реальный пароль):

```bash
aws secretsmanager put-secret-value \
  --region me-central-1 \
  --secret-id doctor-agent/opensearch \
  --secret-string "YOUR_PASSWORD"
```







