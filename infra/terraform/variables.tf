# ===========================================
# Variables
# ===========================================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

# Database
variable "database_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}

variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# Redis
variable "redis_tier" {
  description = "Memorystore Redis tier (BASIC or STANDARD_HA)"
  type        = string
  default     = "BASIC"
}

# Container Images
variable "backend_image" {
  description = "Backend container image URL"
  type        = string
}

variable "frontend_image" {
  description = "Frontend container image URL"
  type        = string
}

# Secrets
variable "secret_key" {
  description = "JWT Secret Key"
  type        = string
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth Client ID"
  type        = string
}

variable "google_client_secret" {
  description = "Google OAuth Client Secret"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "hume_api_key" {
  description = "Hume AI API Key"
  type        = string
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API Key"
  type        = string
  sensitive   = true
}

# Monitoring
variable "notification_email" {
  description = "Email for alert notifications"
  type        = string
}
