locals {
  title       = "bubamarahub"
  apex_domain = "${local.title}.com"
  api_domain  = "api.${local.apex_domain}"

  allow_origin = {
    production = "https://www.${local.apex_domain}",
    non_prod   = "https://editor.weweb.io"
  }

  domains = [
    local.apex_domain,
    api_domain,
  ]

  supabase_projects = {
    production = "unjrzpazrihxnrtqzcgw"
  }

  tags = {
    Project     = local.title
    Environment = var.environment
  }
}