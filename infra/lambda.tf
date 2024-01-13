resource "aws_lambda_layer_version" "pip" {
  filename         = "files/artifacts/lambda_layer.zip"
  layer_name       = local.title
  source_code_hash = filebase64sha256("files/artifacts/lambda_layer.zip")

  compatible_runtimes = ["python3.9"]
}

module "lambda_authorizer" {
  source = "./modules/lambda_function"

  title       = "${local.title}-api-authorizer"
  handler     = "bubamara_backend.api.authorizer.lambda_function.lambda_handler"
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

module "lambda_members" {
  source = "./modules/lambda_function"

  title       = "${local.title}-api-members"
  handler     = "bubamara_backend.api.members.lambda_function.lambda_handler"
  environment = var.environment
  layer_arns  = [aws_lambda_layer_version.pip.arn]

  environment_variables = {
    MEMBERS_TABLE           = aws_dynamodb_table.members.name
    POWERTOOLS_SERVICE_NAME = "members"
  }

  iam_policy = templatefile("${path.module}/files/iam/permission_policy.json.tpl", {
    iam_policy_statements = jsonencode([
      {
        "Effect" : "Allow",
        "Action" : [
          "dynamodb:GetItem"
        ],
        "Resource" : [
          aws_dynamodb_table.members.arn
        ]
      }
    ])
  })

  tags = local.tags
}

module "lambda_payments" {
  source = "./modules/lambda_function"

  title       = "${local.title}-api-payments"
  handler     = "bubamara_backend.api.payments.lambda_function.lambda_handler"
  environment = var.environment
  layer_arns  = [aws_lambda_layer_version.pip.arn]

  environment_variables = {
    MEMBERS_TABLE           = aws_dynamodb_table.members.name
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
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ],
        "Resource" : [
          aws_dynamodb_table.members.arn
        ]
      }
    ])
  })

  tags = local.tags
}

module "lambda_sessions" {
  source = "./modules/lambda_function"

  title       = "${local.title}-api-sessions"
  handler     = "bubamara_backend.api.sessions.lambda_function.lambda_handler"
  environment = var.environment
  layer_arns  = [aws_lambda_layer_version.pip.arn]

  environment_variables = {
    MEMBERS_TABLE           = aws_dynamodb_table.members.name
    POWERTOOLS_SERVICE_NAME = "sessions"
    RESERVATIONS_TABLE      = aws_dynamodb_table.reservations.name
    SESSIONS_TABLE          = aws_dynamodb_table.sessions.name
  }

  iam_policy = templatefile("${path.module}/files/iam/permission_policy.json.tpl", {
    iam_policy_statements = jsonencode([
      {
        "Effect" : "Allow",
        "Action" : [
          "dynamodb:UpdateItem"
        ],
        "Resource" : [
          aws_dynamodb_table.members.arn
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "dynamodb:Query",
          "dynamodb:UpdateItem",
        ],
        "Resource" : [
          aws_dynamodb_table.sessions.arn,
          "${aws_dynamodb_table.sessions.arn}/*"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "dynamodb:DeleteItem",
          "dynamodb:Putitem",
        ],
        "Resource" : [
          aws_dynamodb_table.reservations.arn
        ]
      }
    ])
  })

  tags = local.tags
}
