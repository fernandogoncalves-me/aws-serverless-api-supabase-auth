locals {
  s3_redirect_to_www_origin_id = "redirect-to-www"
}

resource "aws_cloudfront_origin_request_policy" "redirect_to_www" {
  name = "${local.title}-redirect-to-www"

  cookies_config {
    cookie_behavior = "none"
  }
  headers_config {
    header_behavior = "none"
  }
  query_strings_config {
    query_string_behavior = "none"
  }
}

resource "aws_cloudfront_cache_policy" "redirect_to_www" {
  name    = "${local.title}-redirect-to-www"
  min_ttl = 1
  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }
    headers_config {
      header_behavior = "none"
    }
    query_strings_config {
      query_string_behavior = "none"
    }
  }
}

resource "aws_cloudfront_distribution" "redirect_to_www" {
  origin {
    domain_name = aws_s3_bucket.redirect_to_www.bucket_regional_domain_name
    origin_id   = local.s3_redirect_to_www_origin_id
  }

  enabled = true
  aliases = [local.apex_domain]

  default_cache_behavior {
    allowed_methods          = ["GET", "HEAD"]
    cached_methods           = ["GET", "HEAD"]
    origin_request_policy_id = aws_cloudfront_origin_request_policy.redirect_to_www.id
    cache_policy_id          = aws_cloudfront_cache_policy.redirect_to_www.id
    target_origin_id         = local.s3_redirect_to_www_origin_id
    viewer_protocol_policy   = "redirect-to-https"
  }

  price_class = "PriceClass_All"

  restrictions {
    geo_restriction {
      restriction_type = "none"
      locations        = []
    }
  }

  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate.redirect_to_www.arn
    ssl_support_method  = "sni-only"
  }

  tags = local.tags

  depends_on = [aws_acm_certificate_validation.redirect_to_www]
}