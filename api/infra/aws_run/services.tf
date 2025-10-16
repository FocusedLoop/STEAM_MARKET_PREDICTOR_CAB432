# Basic services without auto-scaling
resource "aws_ecs_service" "api" {
  name            = "${var.project_name}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  enable_execute_command = true
  force_new_deployment   = true

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [data.aws_security_group.default.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = var.site_port
  }

  service_connect_configuration {
    enabled = true
    namespace = var.namespace_id

    service {
      port_name      = "api"
      discovery_name = "api"
      client_alias {
        port     = var.site_port
        dns_name = "api"
      }
    }
  }

  tags = var.common_tags
}

resource "aws_ecs_service" "web" {
  name            = "${var.project_name}-web"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.web.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  enable_execute_command = true
  force_new_deployment   = true

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [data.aws_security_group.default.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.web.arn
    container_name   = "web"
    container_port   = var.web_port
  }

  service_connect_configuration {
    enabled = true
    namespace = var.namespace_id

    service {
      port_name      = "web"
      discovery_name = "web"
      client_alias {
        port     = var.web_port
        dns_name = "web"
      }
    }
  }

  tags = var.common_tags
}

resource "aws_ecs_service" "redis" {
  name            = "${var.project_name}-redis"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.redis.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  enable_execute_command = true
  force_new_deployment   = true

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [data.aws_security_group.default.id]
    assign_public_ip = false
  }

  service_connect_configuration {
    enabled = true
    namespace = var.namespace_id

    service {
      port_name      = "redis"
      discovery_name = "redis"
      client_alias {
        port     = var.redis_port
        dns_name = "redis"
      }
    }
  }

  tags = var.common_tags
}

# Basic sklearn service - Scaling Service
resource "aws_ecs_service" "sklearn" {
  name            = "${var.project_name}-sklearn"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.sklearn.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  enable_execute_command = true
  force_new_deployment   = true

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [data.aws_security_group.default.id]
    assign_public_ip = true
  }

  service_connect_configuration {
    enabled = true
    namespace = var.namespace_id

    service {
      port_name      = "sklearn"
      discovery_name = "sklearn"
      client_alias {
        port     = var.ml_port
        dns_name = "sklearn"
      }
    }
  }

  tags = var.common_tags
}