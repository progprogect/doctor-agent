provider "aws" {
  region = var.aws_region
}

# Validation: public_subnet_ids required when ALB is enabled
locals {
  _validation_public_subnets = var.enable_alb && length(var.public_subnet_ids) == 0 ? tobool("ERROR: public_subnet_ids must be provided when enable_alb is true") : true
}

# Security Groups

resource "aws_security_group" "ecs_service" {
  name        = "ecs-service-sg"
  description = "ECS backend service"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    # Игнорируем изменения, так как SG уже существует и используется
    ignore_changes = [description, tags, name]
    prevent_destroy = true  # Защита от случайного удаления
  }
}

resource "aws_security_group" "redis" {
  name        = "redis-sg"
  description = "Allow Redis access only from ECS backend"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Allow Redis from ECS service"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_service.id]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "redis-sg"
    }
  )
}

resource "aws_security_group" "opensearch" {
  name        = "opensearch-sg"
  description = "Allow OpenSearch access only from ECS backend"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Allow HTTPS from ECS service"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_service.id]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "opensearch-sg"
    }
  )
}

# DynamoDB Tables

resource "aws_dynamodb_table" "agents" {
  name         = "Agents"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "agent_id"

  attribute {
    name = "agent_id"
    type = "S"
  }

  tags = merge(
    local.common_tags,
    {
      Name = "Agents"
    }
  )
}

resource "aws_dynamodb_table" "conversations" {
  name         = "Conversations"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "conversation_id"

  attribute {
    name = "conversation_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = merge(
    local.common_tags,
    {
      Name = "Conversations"
    }
  )
}

resource "aws_dynamodb_table" "messages" {
  name         = "Messages"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "conversation_id"
  range_key = "message_id"

  attribute {
    name = "conversation_id"
    type = "S"
  }

  attribute {
    name = "message_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = merge(
    local.common_tags,
    {
      Name = "Messages"
    }
  )
}

resource "aws_dynamodb_table" "channel_bindings" {
  name         = "doctor-agent-channel-bindings"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "binding_id"

  attribute {
    name = "binding_id"
    type = "S"
  }

  attribute {
    name = "agent_id"
    type = "S"
  }

  attribute {
    name = "channel_type"
    type = "S"
  }

  attribute {
    name = "channel_account_id"
    type = "S"
  }

  global_secondary_index {
    name            = "agent_id-index"
    hash_key        = "agent_id"
    range_key       = "channel_type"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "channel_account-index"
    hash_key        = "channel_type"
    range_key       = "channel_account_id"
    projection_type = "ALL"
  }

  tags = merge(
    local.common_tags,
    {
      Name = "ChannelBindings"
    }
  )
}

resource "aws_dynamodb_table" "audit_logs" {
  name         = "doctor-agent-audit-logs"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "log_id"

  attribute {
    name = "log_id"
    type = "S"
  }

  attribute {
    name = "admin_id"
    type = "S"
  }

  attribute {
    name = "resource_type"
    type = "S"
  }

  global_secondary_index {
    name            = "admin_id-index"
    hash_key        = "admin_id"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "resource_type-index"
    hash_key        = "resource_type"
    projection_type = "ALL"
  }

  tags = merge(
    local.common_tags,
    {
      Name = "AuditLogs"
    }
  )
}

# Secrets Manager

resource "aws_secretsmanager_secret" "openai" {
  name        = "doctor-agent/openai"
  description = "OpenAI API key for Doctor Agent"

  tags = local.common_tags
}

