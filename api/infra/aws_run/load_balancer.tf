# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = var.alb_subnets
  security_groups    = [data.aws_security_group.default.id]
  tags = var.common_tags
}

# Target Groups
resource "aws_lb_target_group" "web" {
  name        = "${var.project_name}-web-loadb"
  port        = var.web_port
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"
  health_check {
    path     = "/"
    protocol = "HTTP"
  }
  tags = var.common_tags
}

resource "aws_lb_target_group" "api" {
  name        = "${var.project_name}-api-loadb"
  port        = var.site_port
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"
  health_check {
    path     = "/health"
    protocol = "HTTP"
  }
  tags = var.common_tags
}

# Listeners
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.certificate_arn

  # Default to web target group
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
  tags = var.common_tags
}

resource "aws_lb_listener_rule" "api_domain" {
  listener_arn = aws_lb_listener.https.arn
  priority = 10

  action {
    type = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    host_header {
      values = ["steam-market-price-predictor-api.cab432.com"]
    }
  }
}

resource "aws_lb_listener_rule" "web_domain" {
  listener_arn = aws_lb_listener.https.arn
  priority = 20

  action {
    type = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }

  condition {
    host_header {
      values = ["steam-market-price-predictor.cab432.com"]
    }
  }
}