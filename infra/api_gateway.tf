locals {
  api_routes = {
    payments = {
      route_key       = "ANY /payments/v1/{proxy+}"
      lambda_function = module.lambda_payments.invoke_arn
    }
  }
}

resource "aws_apigatewayv2_api" "backend" {
  name          = "${local.title}-api"
  protocol_type = "HTTP"
  tags          = local.tags
}

resource "aws_apigatewayv2_authorizer" "backend" {
  api_id                            = aws_apigatewayv2_api.backend.id
  name                              = "${aws_apigatewayv2_api.backend.name}-authorizer"
  authorizer_payload_format_version = "2.0"
  authorizer_type                   = "REQUEST"
  authorizer_uri                    = module.lambda_authorizer.invoke_arn
  identity_sources                  = ["$request.header.Authorization"]
}

resource "aws_apigatewayv2_integration" "this" {
  for_each = local.api_routes

  api_id             = aws_apigatewayv2_api.backend.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = each.value.lambda_function
}

resource "aws_apigatewayv2_route" "this" {
  for_each = local.api_routes

  api_id             = aws_apigatewayv2_api.backend.id
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.backend.id
  route_key          = each.value.route_key

  target = "integrations/${aws_apigatewayv2_integration.this[each.key].id}"
}

resource "aws_apigatewayv2_domain_name" "this" {
  domain_name = local.api_domain

  domain_name_configuration {
    certificate_arn = aws_acm_certificate.this[local.api_domain].arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "aws_apigatewayv2_stage" "backend" {
  api_id = aws_apigatewayv2_api.backend.id
  name   = var.environment
}

resource "aws_apigatewayv2_api_mapping" "backend" {
  api_id      = aws_apigatewayv2_api.backend.id
  domain_name = aws_apigatewayv2_domain_name.backend.id
  stage       = aws_apigatewayv2_stage.backend.id
}

resource "aws_apigatewayv2_deployment" "backend" {
  api_id      = aws_apigatewayv2_api.backend.id
  description = "Terraform deployment"

  triggers = {
    redeployment = sha1(join(",", tolist([
      jsonencode(aws_apigatewayv2_integration.backend),
      jsonencode(aws_apigatewayv2_route.backend),
    ])))
  }

  lifecycle {
    create_before_destroy = true
  }
}