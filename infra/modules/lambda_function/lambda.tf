resource "aws_lambda_function" "this" {
  filename      = "example.zip"
  function_name = var.title
  role          = aws_iam_role.this.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  layers        = var.layer_arns
  publish       = true

  environment {
    variables = var.environment_variables
  }

  tags = var.tags
}

resource "aws_lambda_alias" "this" {
  name             = var.environment
  function_name    = aws_lambda_function.this.arn
  function_version = aws_lambda_function.this.version
}
