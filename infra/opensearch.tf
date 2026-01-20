# OpenSearch Domain for RAG vector search (опционально)

resource "aws_opensearch_domain" "main" {
  count        = var.enable_opensearch ? 1 : 0
  domain_name  = "doctor-agent-opensearch"
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type            = var.opensearch_instance_type
    instance_count           = var.opensearch_instance_count
    dedicated_master_enabled = false
    zone_awareness_enabled   = false
  }

  ebs_options {
    ebs_enabled = true
    volume_size = var.opensearch_ebs_volume_size
    volume_type = "gp3"
  }

  vpc_options {
    # OpenSearch single-node требует только одну подсеть
    subnet_ids         = [var.private_subnet_ids[0]]
    security_group_ids = [aws_security_group.opensearch[0].id]
  }

  # Пароль задается через Secrets Manager после создания домена
  # Не указываем master_user_password здесь, чтобы избежать проблем с подпиской

  node_to_node_encryption {
    enabled = true
  }

  encrypt_at_rest {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  advanced_security_options {
    enabled                        = true
    internal_user_database_enabled = true
    master_user_options {
      master_user_name     = var.opensearch_master_user_name
      # Пароль не указываем здесь, так как он уже установлен вручную
      # master_user_password задается только при создании, не обновляется через Terraform
    }
  }

  lifecycle {
    # Игнорируем изменения в master_user_options, так как пароль уже установлен
    ignore_changes = [advanced_security_options[0].master_user_options]
  }

  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch[0].arn
    log_type                 = "INDEX_SLOW_LOGS"
  }

  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch[0].arn
    log_type                 = "SEARCH_SLOW_LOGS"
  }

  tags = merge(
    local.common_tags,
    {
      Name = "doctor-agent-opensearch"
    }
  )
}

# CloudWatch Log Group for OpenSearch logs
resource "aws_cloudwatch_log_group" "opensearch" {
  count             = var.enable_opensearch ? 1 : 0
  name              = "/aws/opensearch/doctor-agent"
  retention_in_days = 7

  tags = local.common_tags
}

# CloudWatch Log Resource Policy for OpenSearch
resource "aws_cloudwatch_log_resource_policy" "opensearch" {
  count       = var.enable_opensearch ? 1 : 0
  policy_name = "doctor-agent-opensearch-logs"

  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "es.amazonaws.com"
        }
        Action = [
          "logs:PutLogEvents",
          "logs:CreateLogStream"
        ]
        Resource = "${aws_cloudwatch_log_group.opensearch[0].arn}:*"
      }
    ]
  })
}


