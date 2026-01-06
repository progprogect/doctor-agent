# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "doctor-agent-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.common_tags
}

# CloudWatch Log Group for ECS
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/doctor-agent"
  retention_in_days = 7

  tags = local.common_tags
}

# ECS Task Definition
resource "aws_ecs_task_definition" "backend" {
  family                   = "doctor-agent-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_cpu
  memory                   = var.ecs_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = "${aws_ecr_repository.backend.repository_url}:latest"

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = concat([
        {
          name  = "ENVIRONMENT"
          value = "production"
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "CORS_ORIGINS"
          value = var.enable_alb ? "http://${aws_lb.main[0].dns_name},https://${aws_lb.main[0].dns_name}" : "*"
        },
        {
          name  = "DYNAMODB_TABLE_AGENTS"
          value = aws_dynamodb_table.agents.name
        },
        {
          name  = "DYNAMODB_TABLE_CONVERSATIONS"
          value = aws_dynamodb_table.conversations.name
        },
        {
          name  = "DYNAMODB_TABLE_MESSAGES"
          value = aws_dynamodb_table.messages.name
        },
        {
          name  = "DYNAMODB_TABLE_CHANNEL_BINDINGS"
          value = aws_dynamodb_table.channel_bindings.name
        },
        {
          name  = "OPENSEARCH_ENDPOINT"
          value = var.enable_opensearch && length(aws_opensearch_domain.main) > 0 ? "https://${aws_opensearch_domain.main[0].endpoint}" : ""
        },
        {
          name  = "OPENSEARCH_USE_SSL"
          value = "true"
        },
        {
          name  = "OPENSEARCH_USERNAME"
          value = var.opensearch_master_user_name
        },
        {
          name  = "SECRETS_MANAGER_OPENAI_KEY_NAME"
          value = aws_secretsmanager_secret.openai.name
        }
      ], var.redis_num_cache_nodes > 0 && length(aws_elasticache_replication_group.redis) > 0 ? [
        {
          name  = "REDIS_HOST"
          value = aws_elasticache_replication_group.redis[0].configuration_endpoint_address
        },
        {
          name  = "REDIS_PORT"
          value = "6379"
        }
      ] : [])

      secrets = [
        {
          name      = "OPENSEARCH_PASSWORD"
          valueFrom = aws_secretsmanager_secret.opensearch.arn
        },
        {
          name      = "OPENAI_API_KEY"
          valueFrom = aws_secretsmanager_secret.openai.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix"  = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = local.common_tags
}

# ECS Service
resource "aws_ecs_service" "backend" {
  name            = "doctor-agent-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.ecs_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_service.id]
    # If ALB is disabled, we need public IP for internet access (OpenAI API)
    # If ALB is enabled, tasks can stay private
    assign_public_ip = !var.enable_alb
  }

  # Only add load balancer if ALB is enabled
  dynamic "load_balancer" {
    for_each = var.enable_alb ? [1] : []
    content {
      target_group_arn = aws_lb_target_group.backend[0].arn
      container_name   = "backend"
      container_port   = 8000
    }
  }

  depends_on = [
    aws_iam_role_policy.ecs_execution,
    aws_iam_role_policy.ecs_task
  ]

  tags = local.common_tags
}

# Secrets Manager secret for OpenSearch password
resource "aws_secretsmanager_secret" "opensearch" {
  name        = "doctor-agent/opensearch"
  description = "OpenSearch master password for Doctor Agent"

  tags = local.common_tags
}

