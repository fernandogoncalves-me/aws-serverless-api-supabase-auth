output "arn" {
  value       = aws_lambda_alias.this.arn
  description = "ARN of the Lambda Function Alias"
}

output "invoke_arn" {
  value       = aws_lambda_alias.this.invoke_arn
  description = "Invoke ARN of the Lambda Function Alias"
}
