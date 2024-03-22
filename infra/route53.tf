data "aws_route53_zone" "hosted_zone" {
  name = local.apex_domain
}

resource "aws_route53_record" "validate_certificate_backend_api" {
  for_each = {
    for dvo in aws_acm_certificate.backend_api.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.hosted_zone.zone_id
}

resource "aws_route53_record" "api" {
  name    = aws_apigatewayv2_domain_name.backend.domain_name
  type    = "A"
  zone_id = data.aws_route53_zone.hosted_zone.zone_id

  alias {
    name                   = aws_apigatewayv2_domain_name.backend.domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.backend.domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }
}