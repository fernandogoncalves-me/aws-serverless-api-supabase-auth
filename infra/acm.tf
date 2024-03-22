resource "aws_acm_certificate" "backend_api" {
  domain_name       = local.api_domain
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_acm_certificate_validation" "backend_api" {
  certificate_arn         = aws_acm_certificate.backend_api.arn
  validation_record_fqdns = [for record in aws_route53_record.validate_certificate_backend_api : record.fqdn]
}
