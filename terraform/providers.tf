terraform {
  required_providers {
    neon = {
      source  = "kislerdm/neon"
      version = ">= 0.1.0"
    }
  }

  required_version = ">= 1.5.0"
}

provider "neon" {
  api_key = var.neon_api_key
}

