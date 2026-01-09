output "ecs_service_sg_id" {
  description = "Security Group ID for ECS service"
  value       = aws_security_group.ecs_service.id
}

output "redis_sg_id" {
  description = "Security Group ID for Redis"
  value       = aws_security_group.redis.id
}

output "opensearch_sg_id" {
  description = "Security Group ID for OpenSearch"
  value       = aws_security_group.opensearch.id
}

output "dynamodb_tables" {
  description = "Map of DynamoDB table names"
  value = {
    agents           = aws_dynamodb_table.agents.name
    conversations    = aws_dynamodb_table.conversations.name
    messages         = aws_dynamodb_table.messages.name
    channel_bindings = aws_dynamodb_table.channel_bindings.name
  }
}

output "openai_secret_arn" {
  description = "ARN of OpenAI API key secret"
  value       = aws_secretsmanager_secret.openai.arn
}

output "opensearch_domain_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = var.enable_opensearch && length(aws_opensearch_domain.main) > 0 ? aws_opensearch_domain.main[0].endpoint : null
}

output "opensearch_domain_arn" {
  description = "OpenSearch domain ARN"
  value       = var.enable_opensearch && length(aws_opensearch_domain.main) > 0 ? aws_opensearch_domain.main[0].arn : null
}

output "opensearch_secret_arn" {
  description = "ARN of OpenSearch password secret"
  value       = aws_secretsmanager_secret.opensearch.arn
}

output "instagram_webhook_verify_token_secret_arn" {
  description = "ARN of Instagram webhook verify token secret"
  value       = aws_secretsmanager_secret.instagram_webhook_verify_token.arn
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN"
  value       = aws_ecs_cluster.main.arn
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.backend.name
}

output "alb_dns_name" {
  description = "ALB DNS name (only if ALB is enabled)"
  value       = var.enable_alb ? aws_lb.main[0].dns_name : null
}

output "alb_arn" {
  description = "ALB ARN (only if ALB is enabled)"
  value       = var.enable_alb ? aws_lb.main[0].arn : null
}

output "alb_target_group_arn" {
  description = "ALB target group ARN (only if ALB is enabled)"
  value       = var.enable_alb ? aws_lb_target_group.backend[0].arn : null
}

output "redis_endpoint" {
  description = "Redis configuration endpoint address"
  value       = var.redis_num_cache_nodes > 0 && length(aws_elasticache_replication_group.redis) > 0 ? aws_elasticache_replication_group.redis[0].configuration_endpoint_address : null
}

output "redis_port" {
  description = "Redis port"
  value       = var.redis_num_cache_nodes > 0 && length(aws_elasticache_replication_group.redis) > 0 ? aws_elasticache_replication_group.redis[0].port : null
}

output "iam_ecs_execution_role_arn" {
  description = "IAM role ARN for ECS task execution"
  value       = aws_iam_role.ecs_execution.arn
}

output "iam_ecs_task_role_arn" {
  description = "IAM role ARN for ECS task"
  value       = aws_iam_role.ecs_task.arn
}

output "frontend_ecr_repository_url" {
  description = "ECR repository URL for frontend"
  value       = aws_ecr_repository.frontend.repository_url
}

output "frontend_ecs_service_name" {
  description = "ECS service name for frontend"
  value       = var.enable_alb ? aws_ecs_service.frontend[0].name : null
}

output "frontend_url" {
  description = "Frontend URL (same as ALB DNS when ALB is enabled)"
  value       = var.enable_alb ? "http://${aws_lb.main[0].dns_name}" : null
}

