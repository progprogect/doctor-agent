# IAM Role for ECS Task Execution (pulls images, writes logs)
resource "aws_iam_role" "ecs_execution" {
  name = "doctor-agent-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for ECS Task Execution
resource "aws_iam_role_policy" "ecs_execution" {
  name = "doctor-agent-ecs-execution-policy"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.ecs.arn}:*",
          "${aws_cloudwatch_log_group.frontend.arn}:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.openai.arn,
          aws_secretsmanager_secret.opensearch.arn,
          aws_secretsmanager_secret.instagram_webhook_verify_token.arn
        ]
      }
    ]
  })
}

# IAM Role for ECS Task (application runtime)
resource "aws_iam_role" "ecs_task" {
  name = "doctor-agent-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for ECS Task (DynamoDB, OpenSearch, Redis access)
resource "aws_iam_role_policy" "ecs_task" {
  name = "doctor-agent-ecs-task-policy"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.agents.arn,
          aws_dynamodb_table.conversations.arn,
          aws_dynamodb_table.messages.arn,
          aws_dynamodb_table.channel_bindings.arn,
          aws_dynamodb_table.audit_logs.arn,
          aws_dynamodb_table.sessions.arn,
          aws_dynamodb_table.rag_documents.arn,
          "${aws_dynamodb_table.agents.arn}/*",
          "${aws_dynamodb_table.conversations.arn}/*",
          "${aws_dynamodb_table.messages.arn}/*",
          "${aws_dynamodb_table.channel_bindings.arn}/*",
          "${aws_dynamodb_table.audit_logs.arn}/*",
          "${aws_dynamodb_table.sessions.arn}/*",
          "${aws_dynamodb_table.rag_documents.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.openai.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:CreateSecret",
          "secretsmanager:UpdateSecret",
          "secretsmanager:DeleteSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:doctor-agent/channels/*",
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:doctor-agent/channels/*-*"
        ]
      }
    ]
  })
}


