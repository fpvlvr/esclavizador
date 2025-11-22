# ===================================
# Neon Database Outputs
# ===================================

output "connection_uri" {
  value       = neon_project.esclavizador_project.connection_uri
  description = "Public Postgres connection string"
  sensitive   = true
}

output "database_host" {
  value       = neon_project.esclavizador_project.database_host
  description = "Neon database host"
}

# ===================================
# Cloud Run Service URLs
# ===================================

output "backend_url" {
  value       = google_cloud_run_v2_service.backend.uri
  description = "Backend Cloud Run service URL (use in GitHub Secrets as BACKEND_URL)"
}

output "frontend_urls" {
  value = {
    primary   = "https://${var.gcp_project_id}.web.app"
    secondary = "https://${var.gcp_project_id}.firebaseapp.com"
  }
  description = "Frontend Firebase Hosting URLs"
}

# ===================================
# Artifact Registry
# ===================================

output "artifact_registry_url" {
  value       = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/esclavizador"
  description = "Artifact Registry repository URL for pushing images"
}

# ===================================
# Service Accounts
# ===================================

output "cloudrun_service_account_email" {
  value       = google_service_account.cloudrun.email
  description = "Cloud Run service account email"
}

output "github_actions_service_account_email" {
  value       = google_service_account.github_actions.email
  description = "GitHub Actions service account email"
}

# ===================================
# Workload Identity Federation
# ===================================
# Only output if WIF is configured (github_repository is set)

output "workload_identity_provider" {
  value = var.github_repository != "" ? (
    "projects/${data.google_project.project[0].number}/locations/global/workloadIdentityPools/github-actions-pool/providers/github-oidc-provider"
  ) : null
  description = "Workload Identity Provider for GitHub Actions (use in GitHub Secrets)"
}

# Get project number for WIF output (only if WIF is enabled)
data "google_project" "project" {
  count      = var.github_repository != "" ? 1 : 0
  project_id = var.gcp_project_id

  # Ensure Cloud Resource Manager API is enabled before reading project data
  depends_on = [google_project_service.cloudresourcemanager]
}
