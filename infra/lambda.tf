resource "aws_lambda_layer_version" "pip" {
  filename   = "files/artifacts/lambda_layer.zip"
  layer_name = local.title

  compatible_runtimes = ["python3.9"]
}

module "lambda_authorizer" {
  source = "./modules/lambda_function"

  title       = "${local.title}-api-authorizer"
  handler     = "api.authorizer.lambda_function.lambda_handler"
  environment = var.environment
  layer_arns  = [aws_lambda_layer_version.pip.arn]

  environment_variables = {
    POWERTOOLS_SERVICE_NAME = "authorizer"
    SUPABASE_PROJECT_PARAM  = aws_ssm_parameter.plaintext["supabase_project"].name
    SUPABASE_API_KEY_PARAM  = aws_ssm_parameter.sensitive["supabase_api_key"].name
  }

  iam_policy = templatefile("${path.module}/files/iam/permission_policy.json.tpl", {
    iam_policy_statements = jsonencode([
      {
        "Effect" : "Allow",
        "Action" : [
          "ssm:GetParameter"
        ],
        "Resource" : [
          aws_ssm_parameter.plaintext["supabase_project"].arn,
          aws_ssm_parameter.sensitive["supabase_api_key"].arn
        ]
      }
    ])
  })

  tags = local.tags
}

module "lambda_payments" {
  source = "./modules/lambda_function"

  title       = "${local.title}-api-payments"
  handler     = "api.payments.lambda_function.lambda_handler"
  environment = var.environment
  layer_arns  = [aws_lambda_layer_version.pip.arn]

  environment_variables = {
    ALLOW_ORIGIN            = lookup(local.allow_origin, var.environment, local.allow_origin["nonprod"])
    POWERTOOLS_SERVICE_NAME = "payments"
    STRIPE_API_KEY_PARAM    = aws_ssm_parameter.sensitive["stripe_api_key"].name
  }

  iam_policy = templatefile("${path.module}/files/iam/permission_policy.json.tpl", {
    iam_policy_statements = jsonencode([
      {
        "Effect" : "Allow",
        "Action" : [
          "ssm:GetParameter"
        ],
        "Resource" : [
          aws_ssm_parameter.sensitive["stripe_api_key"].arn
        ]
      }
    ])
  })

  tags = local.tags
}
