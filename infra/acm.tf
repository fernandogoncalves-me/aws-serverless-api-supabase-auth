resource "aws_acm_certificate" "redirect_to_www" {
  provider          = aws.us-east-1
  domain_name       = local.apex_domain
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_acm_certificate_validation" "redirect_to_www" {
  provider                = aws.us-east-1
  certificate_arn         = aws_acm_certificate.redirect_to_www.arn
  validation_record_fqdns = [for record in aws_route53_record.validate_certificate_redirect_to_www : record.fqdn]
}

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
