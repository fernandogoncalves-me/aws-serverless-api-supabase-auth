terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.31"
    }
  }

  cloud {
    organization = "YOUR_ORG"

    workspaces {
      name = "YOUR_WORKSPACE"
    }
  }
}
