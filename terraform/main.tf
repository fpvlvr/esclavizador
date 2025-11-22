# ===================================
# Neon PostgreSQL Database
# ===================================

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

# ===================================
# GCP: Enable Required APIs
# ===================================

resource "google_project_service" "cloud_run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iam" {
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudresourcemanager" {
  service            = "cloudresourcemanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iamcredentials" {
  service            = "iamcredentials.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "firebase" {
  service            = "firebase.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "firebasehosting" {
  service            = "firebasehosting.googleapis.com"
  disable_on_destroy = false
}

# ===================================
# GCP: Artifact Registry
# ===================================
# Docker repository for backend and frontend images
# Cleanup policy: Keep 2 versions (current + previous for rollback)
# Storage: ~600MB = ~$0.10/month

resource "google_artifact_registry_repository" "esclavizador" {
  location      = var.gcp_region
  repository_id = "esclavizador"
  description   = "Docker repository for esclavizador backend"
  format        = "DOCKER"

  cleanup_policies {
    id     = "keep-recent-versions"
    action = "KEEP"

    most_recent_versions {
      keep_count = 2 # Current + 1 previous for rollback
    }
  }

  cleanup_policies {
    id     = "delete-untagged"
    action = "DELETE"

    condition {
      tag_state  = "UNTAGGED"
      older_than = "86400s" # 1 day
    }
  }

  depends_on = [google_project_service.artifact_registry]
}

# ===================================
# GCP: IAM Service Accounts
# ===================================

# Service account for Cloud Run services (both backend and frontend)
resource "google_service_account" "cloudrun" {
  account_id   = "cloudrun"
  display_name = "Cloud Run Service Account"
  description  = "Service account for backend and frontend Cloud Run services"

  depends_on = [google_project_service.iam]
}

# Service account for GitHub Actions deployments
resource "google_service_account" "github_actions" {
  account_id   = "github-actions"
  display_name = "GitHub Actions Deployment"
  description  = "Service account for GitHub Actions to deploy Cloud Run services"

  depends_on = [google_project_service.iam]
}

# Grant GitHub Actions SA permissions to push to Artifact Registry
resource "google_project_iam_member" "github_actions_artifact_registry" {
  project = var.gcp_project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Grant GitHub Actions SA permissions to manage Cloud Run
resource "google_project_iam_member" "github_actions_cloud_run" {
  project = var.gcp_project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Grant GitHub Actions SA permissions to act as service accounts
resource "google_project_iam_member" "github_actions_service_account_user" {
  project = var.gcp_project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# ===================================
# GCP: Workload Identity Federation
# ===================================
# Allows GitHub Actions to authenticate to GCP without service account keys
# Only created if github_repository variable is set

resource "google_iam_workload_identity_pool" "github_pool" {
  count = var.github_repository != "" ? 1 : 0

  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Workload Identity Pool for GitHub Actions"
  disabled                  = false

  depends_on = [google_project_service.iam, google_project_service.iamcredentials]
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  count = var.github_repository != "" ? 1 : 0

  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool[0].workload_identity_pool_id
  workload_identity_pool_provider_id = "github-oidc-provider"
  display_name                       = "GitHub OIDC Provider"
  description                        = "OIDC provider for GitHub Actions"
  disabled                           = false

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "attribute.repository == '${var.github_repository}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Allow GitHub repository to impersonate the GitHub Actions service account
resource "google_service_account_iam_member" "github_actions_workload_identity" {
  count = var.github_repository != "" ? 1 : 0

  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool[0].name}/attribute.repository/${var.github_repository}"
}

# ===================================
# GCP: Cloud Run - Backend
# ===================================

resource "google_cloud_run_v2_service" "backend" {
  name     = "esclavizador-backend"
  location = var.gcp_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloudrun.email

    scaling {
      min_instance_count = 0
      max_instance_count = var.backend_max_instances
    }

    containers {
      # Image is managed by gcloud CLI for fast code deployments
      # Initial image: Public hello-world (first deploy only)
      # Subsequent updates: gcloud CLI updates with real backend image
      # lifecycle.ignore_changes ensures Terraform doesn't revert to this placeholder
      image = "us-docker.pkg.dev/cloudrun/container/hello:latest"

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = var.backend_cpu
          memory = var.backend_memory
        }
        cpu_idle = true
      }

      env {
        name  = "DATABASE_URL"
        value = neon_project.esclavizador_project.connection_uri
      }

      env {
        name  = "SECRET_KEY"
        value = var.secret_key
      }

      env {
        name  = "ALGORITHM"
        value = var.jwt_algorithm
      }

      env {
        name  = "ACCESS_TOKEN_EXPIRE_MINUTES"
        value = tostring(var.access_token_expire_minutes)
      }

      env {
        name  = "REFRESH_TOKEN_EXPIRE_DAYS"
        value = tostring(var.refresh_token_expire_days)
      }

      env {
        name = "CORS_ORIGINS"
        value = jsonencode([
          "https://${var.gcp_project_id}.web.app",
          "https://${var.gcp_project_id}.firebaseapp.com",
          "http://localhost:3000" # For local development
        ])
      }

      startup_probe {
        initial_delay_seconds = 0
        timeout_seconds       = 1
        period_seconds        = 3
        failure_threshold     = 3

        http_get {
          path = "/health"
          port = 8000
        }
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  # Ignore image changes - managed by gcloud CLI for fast deployments
  # Terraform sets initial image, gcloud handles updates
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }

  depends_on = [
    google_project_service.cloud_run,
    google_artifact_registry_repository.esclavizador
  ]
}

# Allow unauthenticated access to backend (JWT handles auth at app level)
resource "google_cloud_run_v2_service_iam_member" "backend_noauth" {
  location = google_cloud_run_v2_service.backend.location
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ===================================
# Firebase Project and Hosting
# ===================================

# Enable Firebase on the existing GCP project
resource "google_firebase_project" "default" {
  provider = google-beta
  project  = var.gcp_project_id

  depends_on = [google_project_service.firebase]
}

# Create Firebase Hosting site for frontend
resource "google_firebase_hosting_site" "default" {
  provider = google-beta
  project  = var.gcp_project_id
  site_id  = var.gcp_project_id

  depends_on = [
    google_firebase_project.default,
    google_project_service.firebasehosting
  ]
}