output "cognito_user_pool_id_ssm_path" {
  description = "The SSM Parameter Store path for the Cognito User Pool ID."
  value       = aws_ssm_parameter.user_pool_id.name
}

output "cognito_app_client_id_ssm_path" {
  description = "The SSM Parameter Store path for the Cognito App Client ID."
  value       = aws_ssm_parameter.app_client_id.name
}

output "s3_bucket_name" {
  description = "The name of the created S3 bucket for assets."
  value       = aws_s3_bucket.assets.id
}
