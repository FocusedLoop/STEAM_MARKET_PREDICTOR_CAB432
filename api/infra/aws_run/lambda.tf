data "archive_file" "graph_deleation_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../../aws_lambda/graph_deleation.py"
  output_path = "${path.module}/graph_deleation_lambda.zip"
}

resource "aws_lambda_function" "graph_deleation" {
  filename         = data.archive_file.graph_deleation_lambda_zip.output_path
  function_name    = "graph_deleation_lambda"
  role             = "arn:aws:iam::901444280953:role/CAB432-Lambda-Role"
  handler          = "graph_deleation.lambda_handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.graph_deleation_lambda_zip.output_base64sha256
  tags             = var.common_tags
  environment {
    variables = {
      ENVIRONMENT = var.environment
      S3_BUCKET_NAME = var.s3_bucket
      KEEP_COUNT = "5"
    }
  }
}

resource "aws_cloudwatch_event_rule" "daily_cleanup" {
  name                = "daily-graph-deletion"
  schedule_expression = "rate(1 minute)"
  tags                = var.common_tags
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_cleanup.name
  target_id = "graph_deleation_lambda"
  arn       = aws_lambda_function.graph_deleation.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.graph_deleation.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_cleanup.arn
}