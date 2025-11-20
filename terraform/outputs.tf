output "connection_uri" {
  value       = neon_project.esclavizador_project.connection_uri
  description = "Public Postgres connection string"
  sensitive   = true
}

output "database_host" {
  value       = neon_project.esclavizador_project.host
  description = "Database hostname"
  sensitive   = true
}