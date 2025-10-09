# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  tags = var.common_tags
}

# # Cloudwatch
# resource "aws_cloudwatch_log_group" "api" {
#   name              = "aws/ecs/${var.project_name}-api"
#   retention_in_days = 7
#   tags              = var.common_tags
# }

# resource "aws_cloudwatch_log_group" "web" {
#   name              = "aws/ecs/${var.project_name}-web"
#   retention_in_days = 7
#   tags              = var.common_tags
# }

# resource "aws_cloudwatch_log_group" "sklearn" {
#   name              = "aws/ecs/${var.project_name}-sklearn"
#   retention_in_days = 7
#   tags              = var.common_tags
# }

# resource "aws_cloudwatch_log_group" "redis" {
#   name              = "aws/ecs/${var.project_name}-redis"
#   retention_in_days = 7
#   tags              = var.common_tags
# }