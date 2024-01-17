locals {
  ssm_params = {
    plaintext = {
      already_member_link = local.already_member_link
      supabase_project    = local.supabase_projects[var.environment]
      trial_payment_link  = local.trial_payment_link
    }
    sensitive = ["stripe_api_key", "supabase_api_key"]
  }
}

resource "aws_ssm_parameter" "plaintext" {
  for_each = local.ssm_params.plaintext
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