variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

# Port Configuration
variable "site_port" {
  description = "API site port"
  type        = number
}

variable "redis_port" {
  description = "Redis port"
  type        = number
}

variable "web_port" {
  description = "Web service port"
  type        = number
}

variable "ml_port" {
  description = "ML service port"
  type        = number
}

# Redis Configuration
variable "reset_database" {
  description = "Reset database flag"
  type        = bool
  default     = false
}

variable "redis_host" {
  description = "Redis host"
  type        = string
}

variable "redis_db" {
  description = "Redis database number"
  type        = number
}

variable "redis_password" {
  description = "Redis password"
  type        = string
}

# AWS S3 Configuration
variable "local_storage" {
  description = "Use local storage flag"
  type        = bool
  default     = false
}

variable "sklearn_service_url" {
  description = "Sklearn service URL"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "CAB432-assessment3"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = var.common_tags
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.project_name}-api"
  retention_in_days = 7
  tags              = var.common_tags
}

resource "aws_cloudwatch_log_group" "web" {
  name              = "/ecs/${var.project_name}-web"
  retention_in_days = 7
  tags              = var.common_tags
}

resource "aws_cloudwatch_log_group" "sklearn" {
  name              = "/ecs/${var.project_name}-sklearn"
  retention_in_days = 7
  tags              = var.common_tags
}

resource "aws_cloudwatch_log_group" "redis" {
  name              = "/ecs/${var.project_name}-redis"
  retention_in_days = 7
  tags              = var.common_tags
}

# Convert all variables to locals for use in task definitions
locals {
  shared_environment = [
    {
      name  = "NODE_ENV"
      value = var.environment
    },
    {
      name  = "AWS_REGION"
      value = var.aws_region
    },
    {
      name  = "PROJECT_NAME"
      value = var.project_name
    },
    {
      name  = "SITE_PORT"
      value = tostring(var.site_port)
    },
    {
      name  = "REDIS_PORT"
      value = tostring(var.redis_port)
    },
    {
      name  = "WEB_PORT"
      value = tostring(var.web_port)
    },
    {
      name  = "ML_PORT"
      value = tostring(var.ml_port)
    },
    {
      name  = "RESET_DATABASE"
      value = tostring(var.reset_database)
    },
    {
      name  = "REDIS_HOST"
      value = var.redis_host
    },
    {
      name  = "REDIS_DB"
      value = tostring(var.redis_db)
    },
    {
      name  = "REDIS_PASSWORD"
      value = var.redis_password
    },
    {
      name  = "LOCAL_STORAGE"
      value = tostring(var.local_storage)
    },
    {
      name  = "SKLEARN_SERVICE_URL"
      value = var.sklearn_service_url
    }
  ]
}