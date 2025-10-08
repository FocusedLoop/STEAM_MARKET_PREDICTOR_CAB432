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

common_tags = {
  Project     = "CAB432-assessment3"
  Environment = "dev"
  ManagedBy   = "terraform"
  Student     = "your-student-id"
}