# Project Configuration
project_name = "steam-predictor"
aws_region   = "ap-southeast-2"
environment  = "dev"
namespace_id = "arn:aws:servicediscovery:ap-southeast-2:901444280953:namespace/ns-xnzxrwi3zj6tlv75"

# Ports
site_port  = 3010
web_port   = 3009
ml_port    = 3008
redis_port = 6379

# DOCKER IMAGES
api_docker_image     = "901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-api:latest"
web_docker_image     = "901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-web:latest"
sklearn_docker_image = "901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-sklearn:latest"
redis_docker_image   = "901444280953.dkr.ecr.ap-southeast-2.amazonaws.com/steam-predictor-redis:latest"

# Tags
common_tags = {
  project       = "steam-market-predictor"
  purpose       = "assessment3"
  qut-username  = "n11275561@qut.edu.au"
  qut-username2 = "n11803444@qut.edu.au"
}