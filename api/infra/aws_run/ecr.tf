# ECR Repositories
resource "aws_ecr_repository" "steam_predictor_api" {
  name                 = "steam-predictor-api"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = var.common_tags
}

resource "aws_ecr_repository" "steam_predictor_web" {
  name                 = "steam-predictor-web"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = var.common_tags
}

resource "aws_ecr_repository" "steam_predictor_sklearn" {
  name                 = "steam-predictor-sklearn"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = var.common_tags
}

resource "aws_ecr_repository" "steam_predictor_redis" {
  name                 = "steam-predictor-redis"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = var.common_tags
}

# # Lifecycle policies to manage image retention
# resource "aws_ecr_lifecycle_policy" "api_policy" {
#   repository = aws_ecr_repository.steam_predictor_api.name

#   policy = jsonencode({
#     rules = [
#       {
#         rulePriority = 1
#         description  = "Keep last 10 images"
#         selection = {
#           tagStatus     = "tagged"
#           tagPrefixList = ["latest"]
#           countType     = "imageCountMoreThan"
#           countNumber   = 10
#         }
#         action = {
#           type = "expire"
#         }
#       }
#     ]
#   })
# }

# Output the repository URLs for use in task definitions
output "ecr_repositories" {
  description = "ECR repository URLs"
  value = {
    api     = aws_ecr_repository.steam_predictor_api.repository_url
    web     = aws_ecr_repository.steam_predictor_web.repository_url
    sklearn = aws_ecr_repository.steam_predictor_sklearn.repository_url
    redis   = aws_ecr_repository.steam_predictor_redis.repository_url
  }
}