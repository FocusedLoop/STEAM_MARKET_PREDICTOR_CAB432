# Project
variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

# Ports
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

# Redis
variable "reset_database" {
  description = "Reset database flag"
  type        = bool
  default     = false
}

variable "redis_host" {
  description = "Redis host"
  type        = string
  default     = "redis"
}

variable "redis_db" {
  description = "Redis database number"
  type        = number
  default     = 0
}

variable "redis_password" {
  description = "Redis password"
  type        = string
  default     = ""
  sensitive   = true
}

# Misc
variable "local_storage" {
  description = "Use local storage flag"
  type        = bool
  default     = false
}

variable "sklearn_service_url" {
  description = "Sklearn service URL"
  type        = string
  default     = "http://sklearn-service.local:3008"
}

# Docker Images
variable "api_docker_image" {
  description = "Docker image for the API service"
  type        = string
}

variable "web_docker_image" {
  description = "Docker image for the Web service"
  type        = string
}

variable "sklearn_docker_image" {
  description = "Docker image for the Sklearn service"
  type        = string
}

variable "redis_docker_image" {
  description = "Docker image for the Redis service"
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

data "aws_vpc" "main" {
  id = "vpc-007bab53289655834"
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
}

data "aws_security_group" "default" {
  name = "CAB432SG"
}

data "aws_iam_role" "task_role" {
  name = "Task-Role-CAB432-ECS"
}

data "aws_iam_role" "ecs_execution" {
  name = "Execution-Role-CAB432-ECS"
}

data "aws_iam_role" "ecs_task" {
  name = "CAB432-Instance-Role"
}

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
    },
    {
      name  = "API_DOCKER_IMAGE"
      value = var.api_docker_image
    },
    {
      name  = "WEB_DOCKER_IMAGE"
      value = var.web_docker_image
    },
    {
      name  = "SKLEARN_DOCKER_IMAGE"
      value = var.sklearn_docker_image
    },
    {
      name  = "REDIS_DOCKER_IMAGE"
      value = var.redis_docker_image
    }
  ]
}