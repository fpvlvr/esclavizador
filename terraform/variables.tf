variable "neon_api_key" {
  description = "API key for Neon (Neon Console → API Keys)"
  type        = string
  sensitive   = true
}

variable "org_id" {
  description = "Neon Organization ID (from Neon Dashboard → Organization Settings)"
  type        = string
  default     = "org-mute-dream-04914225"
}

variable "project_name" {
  description = "Name for the Neon project"
  type        = string
  default     = "misty‑forest‑02024483"
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
