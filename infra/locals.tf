locals {
  title              = "bubamarahub"
  apex_domain        = "${local.title}.com"
  api_domain         = "api.${local.apex_domain}"
  trial_active_link  = "https://www.bubamarahub.com/already-member"
  trial_payment_link = "https://buy.stripe.com/test_7sIdQVcdPey93UQ000"

  allow_origin = {
    production = "https://www.${local.apex_domain}",
    nonprod    = "https://editor.weweb.io"
  }

  domains = [
    local.apex_domain,
    local.api_domain,
  ]

  supabase_projects = {
    production = "unjrzpazrihxnrtqzcgw"
  }

  tags = {
    Project     = local.title
    Environment = var.environment
  }
}