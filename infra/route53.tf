data "aws_route53_zone" "hosted_zone" {
  name = local.apex_domain
}

resource "aws_route53_record" "acm_certificate_validation" {
  for_each = aws_acm_certificate.certificate.domain_validation_options

  zone_id = data.aws_route53_zone.hosted_zone.zone_id
  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  ttl     = 300
  records = [each.value.resource_record_value]
}

resource "aws_route53_record" "redirect_to_www" {
  name    = local.apex_domain
  type    = "A"
  zone_id = data.aws_route53_zone.hosted_zone.zone_id

  alias {
    name                   = aws_cloudfront_distribution.redirect_to_www.domain_name
    zone_id                = aws_cloudfront_distribution.redirect_to_www.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "api" {
  name    = aws_apigatewayv2_domain_name.this.domain_name
  type    = "A"
  zone_id = data.aws_route53_zone.hosted_zone.zone_id

  alias {
    name                   = aws_apigatewayv2_domain_name.this.domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.this.domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }
}