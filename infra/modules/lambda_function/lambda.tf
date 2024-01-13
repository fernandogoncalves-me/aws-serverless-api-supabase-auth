resource "aws_lambda_function" "this" {
  filename         = "${path.root}/files/artifacts/lambda_package.zip"
  function_name    = var.title
  role             = aws_iam_role.this.arn
  handler          = var.handler
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("${path.root}/files/artifacts/lambda_package.zip")
  layers           = var.layer_arns
  publish          = true
  timeout          = 60
  memory_size      = 256

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
