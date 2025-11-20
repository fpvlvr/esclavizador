resource "neon_project" "esclavizador_project" {
  name   = var.project_name
  org_id = var.org_id
  region_id = "aws-us-east-1"
  pg_version = 16

  branch {
    name          = var.branch_name
    database_name = var.database_name
    role_name     = var.role_name
    role_password = var.role_password
    superuser     = true
  }
}