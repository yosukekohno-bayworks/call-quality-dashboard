# ===========================================
# Cloud Run Module
# ===========================================

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "vpc_connector_id" {
  type = string
}

variable "database_url" {
  type      = string
  sensitive = true
}

variable "redis_url" {
  type = string
}

variable "storage_bucket" {
  type = string
}

variable "backend_image" {
  type = string
}

variable "frontend_image" {
  type = string
}

variable "secret_key" {
  type      = string
  sensitive = true
}

variable "google_client_id" {
  type = string
}

variable "google_client_secret" {
  type      = string
  sensitive = true
}

variable "openai_api_key" {
  type      = string
  sensitive = true
}

variable "hume_api_key" {
  type      = string
  sensitive = true
}

variable "anthropic_api_key" {
  type      = string
  sensitive = true
}

# Artifact Registry
resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = "call-quality-dashboard"
  description   = "Call Quality Dashboard Docker images"
  format        = "DOCKER"
  project       = var.project_id
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run" {
  account_id   = "call-quality-run"
  display_name = "Call Quality Dashboard Cloud Run"
  project      = var.project_id
}

# IAM Roles for Service Account
resource "google_project_iam_member" "cloud_run_roles" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# ===========================================
# Secret Manager
# ===========================================
resource "google_secret_manager_secret" "secrets" {
  for_each = {
    "database-url"         = var.database_url
    "secret-key"           = var.secret_key
    "google-client-secret" = var.google_client_secret
    "openai-api-key"       = var.openai_api_key
    "hume-api-key"         = var.hume_api_key
    "anthropic-api-key"    = var.anthropic_api_key
  }

  secret_id = "call-quality-${each.key}"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "secrets" {
  for_each = google_secret_manager_secret.secrets

  secret      = each.value.id
  secret_data = lookup({
    "database-url"         = var.database_url
    "secret-key"           = var.secret_key
    "google-client-secret" = var.google_client_secret
    "openai-api-key"       = var.openai_api_key
    "hume-api-key"         = var.hume_api_key
    "anthropic-api-key"    = var.anthropic_api_key
  }, replace(each.value.secret_id, "call-quality-", ""))
}

# ===========================================
# Backend Service (FastAPI)
# ===========================================
resource "google_cloud_run_v2_service" "backend" {
  name     = "call-quality-backend"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.cloud_run.email

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    vpc_access {
      connector = var.vpc_connector_id
      egress    = "ALL_TRAFFIC"
    }

    containers {
      image = var.backend_image

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }

      env {
        name  = "REDIS_URL"
        value = var.redis_url
      }

      env {
        name  = "GCS_BUCKET_NAME"
        value = var.storage_bucket
      }

      env {
        name  = "GOOGLE_CLIENT_ID"
        value = var.google_client_id
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["database-url"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["secret-key"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GOOGLE_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["google-client-secret"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["openai-api-key"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "HUME_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["hume-api-key"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["anthropic-api-key"].secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        period_seconds    = 30
        failure_threshold = 3
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Backend - Allow unauthenticated access
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ===========================================
# Frontend Service (Next.js)
# ===========================================
resource "google_cloud_run_v2_service" "frontend" {
  name     = "call-quality-frontend"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.cloud_run.email

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = var.frontend_image

      ports {
        container_port = 3000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "256Mi"
        }
      }

      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }

      env {
        name  = "NEXT_PUBLIC_GOOGLE_CLIENT_ID"
        value = var.google_client_id
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Frontend - Allow unauthenticated access
resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ===========================================
# Celery Worker Service
# ===========================================
resource "google_cloud_run_v2_service" "celery" {
  name     = "call-quality-celery"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.cloud_run.email

    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }

    vpc_access {
      connector = var.vpc_connector_id
      egress    = "ALL_TRAFFIC"
    }

    timeout = "3600s"  # 1 hour for long-running tasks

    containers {
      image = var.backend_image

      command = ["celery"]
      args    = ["-A", "app.tasks.celery_app", "worker", "--loglevel=info", "--concurrency=2"]

      resources {
        limits = {
          cpu    = "2"
          memory = "1Gi"
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }

      env {
        name  = "REDIS_URL"
        value = var.redis_url
      }

      env {
        name  = "GCS_BUCKET_NAME"
        value = var.storage_bucket
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["database-url"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["secret-key"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["openai-api-key"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "HUME_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["hume-api-key"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "ANTHROPIC_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["anthropic-api-key"].secret_id
            version = "latest"
          }
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# ===========================================
# Outputs
# ===========================================
output "backend_url" {
  value = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  value = google_cloud_run_v2_service.frontend.uri
}

output "backend_service_name" {
  value = google_cloud_run_v2_service.backend.name
}

output "frontend_service_name" {
  value = google_cloud_run_v2_service.frontend.name
}

output "celery_service_name" {
  value = google_cloud_run_v2_service.celery.name
}

output "service_account_email" {
  value = google_service_account.cloud_run.email
}

output "artifact_registry_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}"
}
