resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project_name}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  task_role_arn           = data.aws_iam_role.task_role.arn
  execution_role_arn      = data.aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name  = "api"
      image = var.api_docker_image
      
      portMappings = [
        {
          containerPort = var.site_port
          protocol      = "tcp"
        }
      ]
      
      environment = local.shared_environment

      # logConfiguration = {
      #   logDriver = "awslogs"
      #   options = {
      #     awslogs-group         = aws_cloudwatch_log_group.api.name
      #     awslogs-region        = var.aws_region
      #     awslogs-stream-prefix = "ecs"
      #   }
      # }

      # healthCheck = {
      #   command = ["CMD-SHELL", "curl -f http://localhost:${var.site_port} || exit 1"]
      #   interval = 30
      #   timeout = 5
      #   retries = 3
      #   startPeriod = 60
      # }
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
  task_role_arn           = data.aws_iam_role.task_role.arn
  execution_role_arn      = data.aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name  = "web"
      image = var.web_docker_image
      
      portMappings = [
        {
          containerPort = var.web_port
          protocol      = "tcp"
        }
      ]
      
      environment = local.shared_environment

      # logConfiguration = {
      #   logDriver = "awslogs"
      #   options = {
      #     awslogs-group         = aws_cloudwatch_log_group.web.name
      #     awslogs-region        = var.aws_region
      #     awslogs-stream-prefix = "ecs"
      #   }
      # }

      healthCheck = {
        command = ["CMD-SHELL", "curl -s http://localhost:${var.web_port} > /dev/null || exit 1"]
        interval = 30
        timeout = 5
        retries = 3
        startPeriod = 120
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
  task_role_arn           = data.aws_iam_role.task_role.arn
  execution_role_arn      = data.aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name  = "sklearn"
      image = var.sklearn_docker_image
      
      portMappings = [
        {
          containerPort = var.ml_port
          protocol      = "tcp"
        }
      ]
      
      environment = local.shared_environment

      # logConfiguration = {
      #   logDriver = "awslogs"
      #   options = {
      #     awslogs-group         = aws_cloudwatch_log_group.sklearn.name
      #     awslogs-region        = var.aws_region
      #     awslogs-stream-prefix = "ecs"
      #   }
      # }

      # healthCheck = {
      #   command = ["CMD-SHELL", "curl -f http://localhost:${var.ml_port} || exit 1"]
      #   interval = 30
      #   timeout = 10
      #   retries = 3
      #   startPeriod = 120
      # }
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
  task_role_arn           = data.aws_iam_role.task_role.arn
  execution_role_arn      = data.aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name  = "redis"
      image = var.redis_docker_image
      
      portMappings = [
        {
          containerPort = var.redis_port
          protocol      = "tcp"
        }
      ]

      command = [
        "redis-server",
        "--appendonly", "yes",
        "--maxmemory", "512mb",
        "--maxmemory-policy", "allkeys-lru"
      ]

      # logConfiguration = {
      #   logDriver = "awslogs"
      #   options = {
      #     awslogs-group         = aws_cloudwatch_log_group.redis.name
      #     awslogs-region        = var.aws_region
      #     awslogs-stream-prefix = "ecs"
      #   }
      # }

      healthCheck = {
        command = ["CMD", "redis-cli", "ping"]
        interval = 30
        timeout = 5
        retries = 3
        startPeriod = 30
      }
    }
  ])

  tags = var.common_tags
}