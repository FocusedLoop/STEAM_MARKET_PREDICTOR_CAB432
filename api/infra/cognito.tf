resource "aws_cognito_user_pool" "main_pool" {
  name = "${var.project_name}-user-pool"

  mfa_configuration = "ON"

  user_pool_add_ons {
    advanced_security_mode = "OFF"
  }

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true
  }

  schema {
    name                = "steam_id"
    attribute_data_type = "String"
    required            = false 
    mutable             = true  

    string_attribute_constraints {
      min_length = "1"
      max_length = "256"
    }

  alias_attributes         = ["email"]
  auto_verified_attributes = ["email"]

  tags = {
    Project = var.project_name
  }
}

resource "aws_cognito_user_pool_client" "app_client" {
  name         = "${var.project_name}-app-client"
  user_pool_id = aws_cognito_user_pool.main_pool.id

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]
  
  supported_identity_providers = ["Google", "COGNITO"]

  allowed_oauth_flows          = ["code"]
  allowed_oauth_scopes         = ["email", "openid", "profile"]
  allowed_oauth_flows_user_pool_client = true

  callback_urls = ["http://localhost:8501"]
  logout_urls   = ["http://localhost:8501"]
}
