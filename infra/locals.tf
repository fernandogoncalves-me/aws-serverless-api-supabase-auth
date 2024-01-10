locals {
  title       = "bubamarahub"
  apex_domain = "${local.title}.com"
  api_domain  = "api.${local.apex_domain}"

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