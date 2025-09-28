variable "project_name" {
  description = "project name, used to prefix resource names"
  type        = string
  default     = "steam-market-price-predictor"
}

variable "aws_region" {
  description = "AWS region."
  type        = string
  default     = "ap-southeast-2"
}

variable "cognito_app_client_secret" {
  description = "Secret for the Cognito App Client"
  type        = string
  sensitive   = true 
}

variable "domain_name" {
  description = "Registered domain name for the project"
  type        = string
  default     = "steam-market-price-predictor.cab432.com"
}
