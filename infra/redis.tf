# ElastiCache Redis Cluster (опционально - создается только если redis_num_cache_nodes > 0)
resource "aws_elasticache_subnet_group" "redis" {
  count      = var.redis_num_cache_nodes > 0 ? 1 : 0
  name       = "doctor-agent-redis-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = local.common_tags
}

resource "aws_elasticache_replication_group" "redis" {
  count                    = var.redis_num_cache_nodes > 0 ? 1 : 0
  replication_group_id     = "doctor-agent-redis"
  description              = "Redis cluster for Doctor Agent session management"
  
  node_type                = var.redis_node_type
  port                     = 6379
  parameter_group_name     = "default.redis7"
  num_cache_clusters       = var.redis_num_cache_nodes
  
  subnet_group_name        = aws_elasticache_subnet_group.redis[0].name
  security_group_ids       = [aws_security_group.redis[0].id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = false
  
  automatic_failover_enabled = var.redis_num_cache_nodes > 1 ? true : false
  multi_az_enabled           = var.redis_num_cache_nodes > 1 ? true : false

  tags = merge(
    local.common_tags,
    {
      Name = "doctor-agent-redis"
    }
  )
}


