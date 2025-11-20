resource "neon_project" "esclavizador_project" {
  name                      = "esclavizador"
  org_id                    = "org-mute-dream-04914225"
  region_id                 = "aws-us-east-1"
  pg_version                = 16
  history_retention_seconds = 21600

  branch {
    name          = var.branch_name
    database_name = var.database_name
    role_name     = var.role_name
  }
}