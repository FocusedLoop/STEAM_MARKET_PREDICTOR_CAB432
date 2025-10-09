project_name = "steam-predictor"
aws_region   = "ap-southeast-2"
environment  = "dev"

# Port Configuration
site_port  = 3010
redis_port = 6379
web_port   = 3009
ml_port    = 3008

# Redis Configuration
reset_database = false
redis_host     = "redis"
redis_db       = 0
redis_password = ""

# AWS S3 Configuration
local_storage = false

# Sklearn Service Configuration
sklearn_service_url = "http://sklearn-service.local:3008"

# Docker Images
api_docker_image     = "901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-api:latest"
web_docker_image     = "901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-web:latest"
sklearn_docker_image = "901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-sklearn:latest"
redis_docker_image   = "901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-redis:latest"

common_tags = {
  project       = "CAB432-assessment3"
  qut-username  = "n11275561@qut.edu.au"
  qut-username2 = "n11803444@qut.edu.au"
}