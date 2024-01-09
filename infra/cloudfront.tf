locals {
  s3_redirect_to_www_origin_id = "redirect-to-www"
}

resource "aws_cloudfront_distribution" "redirect_to_www" {
  origin {
    domain_name = aws_s3_bucket_website_configuration.redirect_to_www.website_endpoint
    origin_id   = local.s3_redirect_to_www_origin_id
  }

  enabled = true
  aliases = [local.apex_domain]

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = local.s3local.s3_redirect_to_www_origin_id
    viewer_protocol_policy = "redirect-to-https"
  }

  price_class = "PriceClass_All"

  restrictions {
    geo_restriction {
      restriction_type = "none"
      locations        = []
    }
  }

  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate.this[local.apex_domain].arn
  }

  tags = local.tags
}