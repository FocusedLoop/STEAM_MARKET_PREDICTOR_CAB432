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
      image = "${aws_ecr_repository.steam_predictor_api.repository_url}:latest"
      
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
      image = "${aws_ecr_repository.steam_predictor_web.repository_url}:latest"
      
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
      image = "${aws_ecr_repository.steam_predictor_sklearn.repository_url}:latest"
      
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
      image = "${aws_ecr_repository.steam_predictor_redis.repository_url}:latest"
      
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