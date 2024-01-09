resource "aws_acm_certificate" "this" {
  for_each = toset(local.domains)

  domain_name       = each.value
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_acm_certificate_validation" "redirect_certificate" {
  certificate_arn         = aws_acm_certificate.certificate.arn
  validation_record_fqdns = [aws_route53_record.validation.fqdn]
}
