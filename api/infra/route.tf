# # --- Lookups ---
# data "aws_vpc" "default" { default = true }

# data "aws_subnets" "public" {
#   filter { name = "vpc-id" values = [data.aws_vpc.default.id] }
# }

# data "aws_route53_zone" "cab432" {
#   name         = "cab432.com."
#   private_zone = false
# }

# # --- Security groups ---
# resource "aws_security_group" "alb" {
#   name        = "${var.project_name}-alb-sg"
#   description = "ALB ingress 80"
#   vpc_id      = data.aws_vpc.default.id

#   ingress { from_port = 80  to_port = 80  protocol = "tcp" cidr_blocks = ["0.0.0.0/0"] }
#   egress  { from_port = 0   to_port = 0   protocol = "-1"  cidr_blocks = ["0.0.0.0/0"] }

#   tags = var.common_tags
# }

# resource "aws_security_group" "ecs_tasks" {
#   name        = "${var.project_name}-ecs-sg"
#   description = "Allow traffic from ALB to ECS tasks"
#   vpc_id      = data.aws_vpc.default.id

#   ingress {
#     from_port       = 0
#     to_port         = 65535
#     protocol        = "tcp"
#     security_groups = [aws_security_group.alb.id]
#   }
#   egress  { from_port = 0 to_port = 0 protocol = "-1" cidr_blocks = ["0.0.0.0/0"] }

#   tags = var.common_tags
# }

# # --- ALB ---
# resource "aws_lb" "app" {
#   name               = "${var.project_name}-alb"
#   internal           = false
#   load_balancer_type = "application"
#   security_groups    = [aws_security_group.alb.id]
#   subnets            = data.aws_subnets.public.ids
#   tags               = var.common_tags
# }

# # --- Target groups (Fargate => target_type=ip) ---
# # Web (3009)
# resource "aws_lb_target_group" "web" {
#   name        = "${var.project_name}-tg-web"
#   port        = var.web_port            # expect 3009
#   protocol    = "HTTP"
#   vpc_id      = data.aws_vpc.default.id
#   target_type = "ip"

#   health_check {
#     path                = "/"
#     protocol            = "HTTP"
#     interval            = 30
#     timeout             = 5
#     healthy_threshold   = 2
#     unhealthy_threshold = 3
#   }

#   tags = var.common_tags
# }

# # API (3010)
# resource "aws_lb_target_group" "api" {
#   name        = "${var.project_name}-tg-api"
#   port        = var.site_port           # expect 3010
#   protocol    = "HTTP"
#   vpc_id      = data.aws_vpc.default.id
#   target_type = "ip"

#   health_check {
#     path                = "/health"
#     protocol            = "HTTP"
#     interval            = 30
#     timeout             = 5
#     healthy_threshold   = 2
#     unhealthy_threshold = 3
#   }

#   tags = var.common_tags
# }

# # --- Listener: HTTP 80 (default -> web) ---
# resource "aws_lb_listener" "http" {
#   load_balancer_arn = aws_lb.app.arn
#   port              = 80
#   protocol          = "HTTP"

#   default_action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.web.arn
#   }
# }

# # Route /api/* to API TG
# resource "aws_lb_listener_rule" "api_path" {
#   listener_arn = aws_lb_listener.http.arn
#   priority     = 10

#   action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.api.arn
#   }

#   condition {
#     path_pattern { values = ["/api/*"] }
#   }
# }

# # --- Route 53: single alias A for the hostname ---
# resource "aws_route53_record" "app_a" {
#   zone_id = data.aws_route53_zone.cab432.zone_id
#   name    = "steam-market-price-predictor.cab432.com"
#   type    = "A"

#   alias {
#     name                   = aws_lb.app.dns_name
#     zone_id                = aws_lb.app.zone_id
#     evaluate_target_health = true
#   }
# }
