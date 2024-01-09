
resource "aws_s3_bucket" "redirect_to_www" {
  bucket = local.apex_domain
  tags   = local.tags
}

resource "aws_s3_bucket_website_configuration" "redirect_to_www" {
  bucket = aws_s3_bucket.redirect_to_www.id

  redirect_all_requests_to {
    host_name = "www.${local.apex_domain}"
    protocol  = "http"
  }
}
