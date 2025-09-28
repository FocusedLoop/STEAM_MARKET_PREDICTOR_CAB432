resource "aws_secretsmanager_secret" "cognito_config" {
  name = "/${var.project_name}/cognito/config"
  description = "Stores Cognito configuration for the application."
  tags = {
    Project = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "cognito_config_values" {
  secret_id = aws_secretsmanager_secret.cognito_config.id

  secret_string = jsonencode({
    COGNITO_REGION            = var.aws_region
    COGNITO_USER_POOL_ID      = aws_cognito_user_pool.main_pool.id
    COGNITO_APP_CLIENT_ID     = aws_cognito_user_pool_client.app_client.id
    COGNITO_APP_CLIENT_SECRET = var.cognito_app_client_secret 
    COGNITO_DOMAIN            = aws_cognito_user_pool.main_pool.endpoint
  })
}
