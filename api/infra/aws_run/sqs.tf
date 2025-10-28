resource "aws_sqs_queue" "ml_jobs" {
  name                      = "${var.project_name}-ml-jobs-queue"
  visibility_timeout_seconds = 900  # 15 minutes
  message_retention_seconds  = 86400 # 24 hours
  receive_wait_time_seconds = 20    # Long polling
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ml_jobs_dlq.arn
    maxReceiveCount     = 3  # After 3 failed attempts, send to DLQ
  })
  
  tags = var.common_tags
}

resource "aws_sqs_queue" "ml_jobs_dlq" {
  name                      = "${var.project_name}-ml-jobs-dlq"
  message_retention_seconds = 1209600  # 14 days
  
  tags = var.common_tags
}

# resource "aws_iam_role_policy" "api_sqs_send" {
#   name = "${var.project_name}-api-sqs-send-policy"
#   role = data.aws_iam_role.task_role.id

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "sqs:SendMessage",
#           "sqs:GetQueueAttributes"
#         ]
#         Resource = aws_sqs_queue.ml_jobs.arn
#       }
#     ]
#   })
# }

# resource "aws_iam_role_policy" "sklearn_sqs_receive" {
#   name = "${var.project_name}-sklearn-sqs-receive-policy"
#   role = data.aws_iam_role.task_role.id

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "sqs:ReceiveMessage",
#           "sqs:DeleteMessage",
#           "sqs:GetQueueAttributes",
#           "sqs:ChangeMessageVisibility"
#         ]
#         Resource = aws_sqs_queue.ml_jobs.arn
#       },
#       {
#         Effect = "Allow"
#         Action = [
#           "sqs:SendMessage"
#         ]
#         Resource = aws_sqs_queue.ml_jobs_dlq.arn
#       }
#     ]
#   })
# }

resource "aws_cloudwatch_metric_alarm" "ml_queue_depth_high" {
  alarm_name          = "${var.project_name}-ml-queue-depth-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "60"
  statistic           = "Average"
  threshold           = "10"
  alarm_description   = "Alert when ML jobs queue has more than 10 messages"
  alarm_actions       = []

  dimensions = {
    QueueName = aws_sqs_queue.ml_jobs.name
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "ml_dlq_messages" {
  alarm_name          = "${var.project_name}-ml-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "Alert when messages are sent to DLQ"
  alarm_actions       = []

  dimensions = {
    QueueName = aws_sqs_queue.ml_jobs_dlq.name
  }

  tags = var.common_tags
}

# Output the queue URLs for use in application
output "ml_jobs_queue_url" {
  value = aws_sqs_queue.ml_jobs.url
}

output "ml_jobs_queue_arn" {
  value = aws_sqs_queue.ml_jobs.arn
}

output "ml_jobs_dlq_url" {
  value = aws_sqs_queue.ml_jobs_dlq.url
}

output "ml_jobs_dlq_arn" {
  value = aws_sqs_queue.ml_jobs_dlq.arn
}

