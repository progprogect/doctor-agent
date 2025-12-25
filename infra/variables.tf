variable "vpc_id" {
  description = "VPC ID where resources are located"
  type        = string
  default     = "vpc-03cb895f29b20a53e"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "me-central-1"
}

variable "project_tag" {
  description = "Project tag for all resources"
  type        = string
  default     = "doctor-agent"
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks and OpenSearch"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for ALB (required only if enable_alb = true)"
  type        = list(string)
  default     = []
  
  # Note: Validation cannot reference other variables, so we check this in main.tf instead
}

variable "opensearch_instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch instances"
  type        = number
  default     = 1
}

variable "opensearch_ebs_volume_size" {
  description = "EBS volume size for OpenSearch (GB)"
  type        = number
  default     = 20
}

variable "opensearch_master_user_name" {
  description = "OpenSearch master username"
  type        = string
  default     = "admin"
}

variable "opensearch_master_user_password" {
  description = "OpenSearch master password (should be stored in Secrets Manager)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "ecs_cpu" {
  description = "CPU units for ECS task (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "ecs_memory" {
  description = "Memory for ECS task (MB)"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1
}

variable "ecr_repository_name" {
  description = "ECR repository name for Docker image"
  type        = string
  default     = "doctor-agent-backend"
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 1
}

variable "enable_alb" {
  description = "Enable Application Load Balancer (set to false for MVP to reduce costs)"
  type        = bool
  default     = false
}

variable "enable_opensearch" {
  description = "Enable OpenSearch domain (may require subscription activation in me-central-1)"
  type        = bool
  default     = true
}

locals {
  common_tags = {
    Project = var.project_tag
  }
}

