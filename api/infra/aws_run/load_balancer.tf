# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = var.alb_subnets
  security_groups    = [data.aws_security_group.default.id]
}

# Target Groups
resource "aws_lb_target_group" "web" {
  name        = "${var.project_name}-web-lb"
  port        = var.web_port
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"
  health_check {
    path     = "/"
    protocol = "HTTP"
  }
}

resource "aws_lb_target_group" "api" {
  name        = "${var.project_name}-api-lb"
  port        = var.site_port
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"
  health_check {
    path     = "/health"
    protocol = "HTTP"
  }
}

# Listeners
resource "aws_lb_listener" "web" {
  load_balancer_arn = aws_lb.main.arn
  port              = var.web_port
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

resource "aws_lb_listener" "api" {
  load_balancer_arn = aws_lb.main.arn
  port              = var.site_port
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}