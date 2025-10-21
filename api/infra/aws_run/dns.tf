# ACM Certificate for HTTPS
# resource "aws_acm_certificate" "this" {
#   domain_name       = "steam-market-price-predictor.cab432.com"
#   validation_method = "DNS"

#   tags = var.common_tags
# }

# resource "aws_route53_record" "cert_validation" {
#   for_each = {
#     for dvo in aws_acm_certificate.this.domain_validation_options : dvo.domain_name => {
#       name   = dvo.resource_record_name
#       type   = dvo.resource_record_type
#       record = dvo.resource_record_value
#     }
#   }

#   zone_id = var.cab432_zone_id
#   name    = each.value.name
#   type    = each.value.type
#   records = [each.value.record]
#   ttl     = 60
# }

# resource "aws_acm_certificate_validation" "this" {
#   certificate_arn         = aws_acm_certificate.this.arn
#   validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
# }

# DNS Record for ALB
# resource "aws_route53_record" "website_alias" {
#   zone_id = var.cab432_zone_id
#   name    = "steam-market-price-predictor" 
#   type    = "CNAME"

#   alias {
#     name                   = aws_lb.main.dns_name
#     zone_id                = aws_lb.main.zone_id
#     evaluate_target_health = true
#   }
# }