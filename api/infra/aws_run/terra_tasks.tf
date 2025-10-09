# Task Definitions
resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project_name}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = data.aws_iam_role.ecs_execution.arn  # Uses data from vpc.tf
  task_role_arn           = data.aws_iam_role.ecs_task.arn        # Uses data from vpc.tf

  container_definitions = jsonencode([
    {
      name  = "api"
      image = "901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-api:latest"
      
      portMappings = [
        {
          containerPort = var.site_port
          protocol      = "tcp"
        }
      ]
      
      environment = local.shared_environment

      healthCheck = {
        command = ["CMD-SHELL", "curl -f http://localhost:${var.site_port}/health || exit 1"]
        interval = 30
        timeout = 5
        retries = 3
        startPeriod = 60
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = var.common_tags
}

resource "aws_ecs_task_definition" "web" {
  family                   = "${var.project_name}-web"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name  = "web"
      image = "901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-web:latest"
      
      portMappings = [
        {
          containerPort = 3009
          protocol      = "tcp"
        }
      ]
      
      environment = local.shared_environment

      healthCheck = {
        command = ["CMD-SHELL", "curl -f http://localhost:3009/health || exit 1"]
        interval = 30
        timeout = 5
        retries = 3
        startPeriod = 30
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.web.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = var.common_tags
}

resource "aws_ecs_task_definition" "sklearn" {
  family                   = "${var.project_name}-sklearn"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name  = "sklearn"
      image = "901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-sklearn:latest"
      
      portMappings = [
        {
          containerPort = 3008
          protocol      = "tcp"
        }
      ]
      
      environment = local.shared_environment

      healthCheck = {
        command = ["CMD-SHELL", "curl -f http://localhost:3008/health || exit 1"]
        interval = 30
        timeout = 10
        retries = 3
        startPeriod = 120
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.sklearn.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = var.common_tags
}

resource "aws_ecs_task_definition" "redis" {
  family                   = "${var.project_name}-redis"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name  = "redis"
      image = "redis:7-alpine"
      
      portMappings = [
        {
          containerPort = 6379
          protocol      = "tcp"
        }
      ]

      command = [
        "redis-server",
        "--appendonly", "yes",
        "--maxmemory", "256mb",
        "--maxmemory-policy", "allkeys-lru"
      ]

      healthCheck = {
        command = ["CMD", "redis-cli", "ping"]
        interval = 30
        timeout = 5
        retries = 3
        startPeriod = 10
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.redis.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = var.common_tags
}

# ECS Services
# Backend API
resource "aws_ecs_service" "api" {
  name            = "${var.project_name}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids      # Uses subnets from VPC
    security_groups  = [data.aws_security_group.default.id]  # Uses security group from VPC
    assign_public_ip = true
  }

  tags = var.common_tags
}

# Sklearn Service
resource "aws_ecs_service" "sklearn" {
  name            = "${var.project_name}-sklearn"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.sklearn.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids      # Same VPC
    security_groups  = [data.aws_security_group.default.id]  # Same security group
    assign_public_ip = false
  }

  tags = var.common_tags
}

# Redis Service
resource "aws_ecs_service" "redis" {
  name            = "${var.project_name}-redis"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.redis.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids      # Same VPC
    security_groups  = [data.aws_security_group.default.id]  # Same security group
    assign_public_ip = false
  }

  tags = var.common_tags
}

# Frontend Web
resource "aws_ecs_service" "web" {
  name            = "${var.project_name}-web"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.web.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids      # Same VPC
    security_groups  = [data.aws_security_group.default.id]  # Same security group
    assign_public_ip = true  # Public access for now
  }

  tags = var.common_tags
}