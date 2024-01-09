locals {
  ssm_params = {
    plaintext = {
      supabase_project = local.supabase_projects[var.environment]
    }
    sensitive = ["stripe_api_key", "supabase_api_key"]
  }
}

resource "aws_ssm_parameter" "plaintext" {
  for_each = toset(local.ssm_params.plaintext)
  name     = "/${local.title}/${each.key}"
  type     = "SecureString"
  value    = each.value
  tags     = local.tags
}

resource "aws_ssm_parameter" "sensitive" {
  for_each = toset(local.ssm_params.sensitive)
  name     = "/${local.title}/${each.value}"
  type     = "SecureString"
  value    = "SENSITIVE"
  tags     = local.tags

  lifecycle {
    ignore_changes = [value]
  }
}