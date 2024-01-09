variable "environment" {
  type        = string
  description = "Environment to deploy to"
}

variable "environment_variables" {
  type        = map(string)
  description = "Environment variables for the Lambda Function"
}

variable "iam_policy" {
  type        = string
  default     = null
  description = "IAM Policy to attach to the Lambda Function"
}

variable "layer_arns" {
  type        = list(string)
  default     = null
  description = "List of Lambda Layer ARNs to attach to the Lambda Function"
}

variable "title" {
  type        = string
  description = "Title that will be used as a prefix for all resources"
}

variable "tags" {
  type        = map(string)
  description = "Tags that will be applied to all resources"
}