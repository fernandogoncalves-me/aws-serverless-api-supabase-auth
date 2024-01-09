resource "aws_lambda_layer_version" "pip" {
  filename   = "lambda_layer_payload.zip"
  layer_name = "lambda_layer_name"

  compatible_runtimes = ["python3.9"]
}

module "lambda_authorizer" {
  source = "./modules/lambda_function"

  title       = "${local.title}-api-authorizer"
  environment = var.environment
  layer_arns  = [aws_lambda_layer_version.pip.arn]

  environment_variables = {
    POWERTOOLS_SERVICE_NAME = "authorizer"
    SUPABASE_PROJECT_PARAM  = aws_ssm_parameter.plaintext["supabase_project"].arn
    SUPABASE_API_KEY_PARAM  = aws_ssm_parameter.sensitive["supabase_api_key"].arn
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
  environment = var.environment
  layer_arns  = [aws_lambda_layer_version.pip.arn]

  environment_variables = {
    ALLOW_ORIGIN            = lookup(local.allow_origin, var.environment, local.allow_origin["nonprod"])
    POWERTOOLS_SERVICE_NAME = "payments"
    STRIPE_API_KEY_PARAM    = aws_ssm_parameter.plaintext["stripe_api_key"].arn
  }

  iam_policy = templatefile("${path.module}/files/iam/permission_policy.json.tpl", {
    iam_policy_statements = jsonencode([
      {
        "Effect" : "Allow",
        "Action" : [
          "ssm:GetParameter"
        ],
        "Resource" : [
          aws_ssm_parameter.plaintext["stripe_api_key"].arn
        ]
      }
    ])
  })

  tags = local.tags
}
