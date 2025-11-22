# ===================================
# TERRAFORM CLOUD WORKSPACE VARIABLES
# ===================================
#
# This project uses Terraform Cloud for remote state management.
# Variables must be set in the Terraform Cloud workspace, NOT in a local .tfvars file.
#
# How to set variables:
# 1. Go to: https://app.terraform.io/app/fpvlvr-org/workspaces/esclavizador-github-actions
# 2. Click "Variables" tab
# 3. Add each required variable below
# 4. Mark sensitive variables as "Sensitive" (neon_api_key, secret_key, role_password)
#
# Required variables:
#   - neon_api_key       (from Neon Console → API Keys)
#   - gcp_project_id     (your GCP project ID - also used for Firebase Hosting URLs)
#   - secret_key         (generate: openssl rand -base64 32)
#
# Optional variables (have defaults):
#   - All other variables have sensible defaults
#   - Override in Terraform Cloud workspace if needed
#
# For Workload Identity Federation (recommended):
#   - github_repository  (format: "username/esclavizador")
#
# Note: Firebase Hosting will use the same project ID as GCP (gcp_project_id)
#
# ===================================

# Neon Database Variables
variable "neon_api_key" {
  description = "API key for Neon (Neon Console → API Keys)"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "Neon region (e.g., aws-us-east-1)"
  type        = string
  default     = "aws-us-east-1"
}

variable "branch_name" {
  description = "Branch name in Neon (production / development)"
  type        = string
  default     = "production"
}

variable "database_name" {
  description = "Name of the database in the Neon branch"
  type        = string
  default     = "esclavizador"
}

variable "role_name" {
  description = "Database role / user name"
  type        = string
  default     = "esclavizador"
}

variable "role_password" {
  description = "Password for the Neon DB user"
  type        = string
  sensitive   = true
  default     = "dev_password_change_in_production"
}

# GCP Project Variables
variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region for resources (e.g., us-central1)"
  type        = string
  default     = "us-central1"
}

variable "gcp_credentials" {
  description = "GCP service account credentials JSON (for Terraform Cloud authentication)"
  type        = string
  sensitive   = true
}

# Docker Image Tags
# Note: Backend image tag is managed by gcloud CLI (not Terraform)
# See lifecycle.ignore_changes in main.tf

# Application Configuration
variable "secret_key" {
  description = "Application secret key (min 32 characters)"
  type        = string
  sensitive   = true
}

variable "jwt_algorithm" {
  description = "JWT signing algorithm"
  type        = string
  default     = "HS256"
}

variable "access_token_expire_minutes" {
  description = "JWT access token expiry in minutes"
  type        = number
  default     = 30
}

variable "refresh_token_expire_days" {
  description = "JWT refresh token expiry in days"
  type        = number
  default     = 7
}

# Cloud Run Configuration (Backend only - frontend on Firebase Hosting)
variable "backend_max_instances" {
  description = "Maximum number of backend Cloud Run instances"
  type        = number
  default     = 3
}

variable "backend_memory" {
  description = "Memory allocation for backend (e.g., 512Mi, 1Gi)"
  type        = string
  default     = "512Mi"
}

variable "backend_cpu" {
  description = "CPU allocation for backend (e.g., 1, 2)"
  type        = string
  default     = "1"
}

# GitHub Repository (for Workload Identity Federation)
variable "github_repository" {
  description = "GitHub repository in format 'owner/repo' (e.g., 'username/esclavizador')"
  type        = string
  default     = ""
}
