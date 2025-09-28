data "aws_route53_zone" "primary" {
  name = var.domain_name
}

resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.primary.zone_id
  name    = "api.${var.domain_name}"
  type    = "A"
  ttl     = 300
  records = ["13.239.237.66"]
}

resource "aws_route53_record" "auth" {
  zone_id = data.aws_route53_zone.primary.zone_id
  name    = "auth"
  type    = "A"

  alias {
    name                   = aws_cognito_user_pool.main_pool.custom_domain_configuration[0].cloudfront_distribution
    zone_id                = "Z2FDTNDATAQYW2"
    evaluate_target_health = false
  }
}
