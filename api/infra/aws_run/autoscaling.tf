resource "aws_appautoscaling_target" "sklearn_target" {
  max_capacity       = 5
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.sklearn.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "sklearn_cpu_scale_up" {
  name               = "${var.project_name}-sklearn-cpu-scale-up"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.sklearn_target.resource_id
  scalable_dimension = aws_appautoscaling_target.sklearn_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.sklearn_target.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown               = 60
    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_lower_bound = 0
      metric_interval_upper_bound = 10
      scaling_adjustment          = 1
    }

    step_adjustment {
      metric_interval_lower_bound = 10
      scaling_adjustment           = 2
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "sklearn_cpu_high" {
  alarm_name          = "${var.project_name}-sklearn-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "70"
  alarm_description   = "Scale up when CPU utilization exceeds 70%"
  alarm_actions       = [aws_appautoscaling_policy.sklearn_cpu_scale_up.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.sklearn.name
  }

  tags = var.common_tags
}

resource "aws_appautoscaling_policy" "sklearn_cpu_scale_down" {
  name               = "${var.project_name}-sklearn-cpu-scale-down"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.sklearn_target.resource_id
  scalable_dimension = aws_appautoscaling_target.sklearn_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.sklearn_target.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown               = 300
    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_upper_bound = 0
      scaling_adjustment          = -1
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "sklearn_cpu_low" {
  alarm_name          = "${var.project_name}-sklearn-cpu-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "5"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "30"
  alarm_description   = "Scale down when CPU utilization is below 30%"
  alarm_actions       = [aws_appautoscaling_policy.sklearn_cpu_scale_down.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.sklearn.name
  }

  tags = var.common_tags
}

resource "aws_appautoscaling_policy" "sklearn_memory_scale_up" {
  name               = "${var.project_name}-sklearn-memory-scale-up"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.sklearn_target.resource_id
  scalable_dimension = aws_appautoscaling_target.sklearn_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.sklearn_target.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown               = 60
    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_lower_bound = 0
      metric_interval_upper_bound = 20
      scaling_adjustment          = 1
    }
    step_adjustment {
      metric_interval_lower_bound = 20
      scaling_adjustment          = 2
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "sklearn_memory_high" {
  alarm_name          = "${var.project_name}-sklearn-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Scale up when memory utilization exceeds 80%"
  alarm_actions       = [aws_appautoscaling_policy.sklearn_memory_scale_up.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.sklearn.name
  }

  tags = var.common_tags
}

resource "aws_appautoscaling_policy" "sklearn_queue_depth_scale_up" {
  name               = "${var.project_name}-sklearn-queue-depth-scale-up"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.sklearn_target.resource_id
  scalable_dimension = aws_appautoscaling_target.sklearn_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.sklearn_target.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown               = 60
    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_lower_bound = 0
      metric_interval_upper_bound = 5
      scaling_adjustment          = 1
    }

    step_adjustment {
      metric_interval_lower_bound = 5
      metric_interval_upper_bound = 10
      scaling_adjustment          = 2
    }

    step_adjustment {
      metric_interval_lower_bound = 10
      scaling_adjustment           = 3
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "sklearn_queue_depth_high" {
  alarm_name          = "${var.project_name}-sklearn-queue-depth-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "60"
  statistic           = "Average"
  threshold           = "5"
  alarm_description   = "Scale up when SQS queue has more than 5 messages"
  alarm_actions       = [aws_appautoscaling_policy.sklearn_queue_depth_scale_up.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.ml_jobs.name
  }

  tags = var.common_tags
}

