locals {
  service_routes = {
    members = {
      base_path       = "/members/v1/"
      lambda_function = module.lambda_members
      routes = {
        me = {
          method = "GET"
        }
      }
    }
    payments = {
      base_path       = "/payments/v1/"
      lambda_function = module.lambda_payments
      routes = {
        membership = {
          method = "POST"
        }
        trial = {
          method = "POST"
        }
      }
    }
    sessions = {
      base_path       = "/sessions/v1/"
      lambda_function = module.lambda_sessions
      routes = {
        list = {
          method = "GET"
        }
        reserve = {
          method = "POST"
        }
        unreserve = {
          method = "POST"
        }
      }
    }
  }

  api_routes = flatten([
    for service, service_config in local.service_routes : [
      for route, route_config in service_config.routes : {
        service         = service
        route           = route
        route_key       = "${route_config.method} ${service_config.base_path}${route}"
        lambda_function = service_config.lambda_function
      }
    ]
  ])

  api_lambda_permissions = flatten([
    for service, service_config in local.service_routes : [
      for route, route_config in service_config.routes : {
        service         = service
        route           = route
        route_key       = "${route_config.method} ${service_config.base_path}${route}"
        lambda_function = service_config.lambda_function
      }
    ]
  ])
}

resource "aws_apigatewayv2_api" "backend" {
  name          = "${local.title}-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = [for env, origin in local.allow_origin : origin]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
  }
  tags = local.tags
}

resource "aws_apigatewayv2_authorizer" "backend" {
  api_id                            = aws_apigatewayv2_api.backend.id
  name                              = "${aws_apigatewayv2_api.backend.name}-authorizer"
  authorizer_payload_format_version = "2.0"
  authorizer_type                   = "REQUEST"
  authorizer_uri                    = module.lambda_authorizer.alias.invoke_arn
  identity_sources                  = ["$request.header.Authorization"]
}

resource "aws_lambda_permission" "api_gateway_authorizer" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_authorizer.alias.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.backend.execution_arn}/*"
  qualifier     = module.lambda_authorizer.alias.name
}

resource "aws_apigatewayv2_integration" "this" {
  for_each = { for route in local.api_routes : "${route.service}_${route.route}" => route }

  api_id                 = aws_apigatewayv2_api.backend.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = each.value.lambda_function.alias.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "this" {
  for_each = { for route in local.api_routes : "${route.service}_${route.route}" => route }

  api_id             = aws_apigatewayv2_api.backend.id
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.backend.id
  route_key          = each.value.route_key

  target = "integrations/${aws_apigatewayv2_integration.this[each.key].id}"
}

resource "aws_lambda_permission" "allow_api_gateway" {
  for_each = { for service, service_config in local.service_routes : service => service_config }

  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = each.value.lambda_function.alias.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.backend.execution_arn}/*"
  qualifier     = each.value.lambda_function.alias.name
}

resource "aws_apigatewayv2_domain_name" "backend" {
  domain_name = local.api_domain

  domain_name_configuration {
    certificate_arn = aws_acm_certificate.backend_api.arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }

  depends_on = [aws_acm_certificate_validation.backend_api]
}

resource "aws_apigatewayv2_stage" "backend" {
  api_id = aws_apigatewayv2_api.backend.id
  name   = var.environment

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.backend_api.arn
    format = jsonencode({
      requestId               = "$context.requestId"
      ip                      = "$context.identity.sourceIp"
      requestTime             = "$context.requestTime"
      httpMethod              = "$context.httpMethod"
      routeKey                = "$context.routeKey"
      status                  = "$context.status"
      protocol                = "$context.protocol"
      responseLength          = "$context.responseLength"
      integrationStatus       = "$context.integrationStatus"
      integrationErrorMessage = "$context.integrationErrorMessage"
    })
  }
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
      jsonencode(aws_apigatewayv2_integration.this),
      jsonencode(aws_apigatewayv2_route.this),
    ])))
  }

  lifecycle {
    create_before_destroy = true
  }
}