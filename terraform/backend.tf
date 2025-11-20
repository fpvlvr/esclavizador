terraform {
  required_version = ">= 1.5.0"

  backend "remote" {
    organization = "fpvlvr-org"

    workspaces {
      name = "esclavizador-github-actions"
    }
  }
}