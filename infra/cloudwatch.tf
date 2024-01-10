
resource "aws_cloudwatch_log_group" "backend_api" {
  name              = "${local.title}-api"
  retention_in_days = 7
  tags              = local.tags
}
