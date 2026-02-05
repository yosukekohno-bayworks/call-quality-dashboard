# ===========================================
# Scheduler Module - Cloud Scheduler
# ===========================================

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "backend_service_url" {
  type = string
}

variable "service_account_email" {
  type = string
}

# Service Account for Cloud Scheduler
resource "google_service_account" "scheduler" {
  account_id   = "call-quality-scheduler"
  display_name = "Call Quality Dashboard Scheduler"
  project      = var.project_id
}

# Allow Scheduler to invoke Cloud Run
resource "google_cloud_run_v2_service_iam_member" "scheduler_invoker" {
  project  = var.project_id
  location = var.region
  name     = "call-quality-backend"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

# ===========================================
# Daily Batch Job - AM 3:00 JST
# ===========================================
resource "google_cloud_scheduler_job" "daily_batch" {
  name        = "call-quality-daily-batch"
  description = "Daily batch job to fetch and analyze calls from Biztel"
  schedule    = "0 3 * * *"  # Every day at 3:00 AM
  time_zone   = "Asia/Tokyo"
  project     = var.project_id
  region      = var.region

  retry_config {
    retry_count          = 3
    min_backoff_duration = "60s"
    max_backoff_duration = "300s"
    max_doublings        = 2
  }

  http_target {
    http_method = "POST"
    uri         = "${var.backend_service_url}/api/batch/daily"

    headers = {
      "Content-Type" = "application/json"
    }

    body = base64encode(jsonencode({
      trigger = "scheduled"
      date    = "$${date}"
    }))

    oidc_token {
      service_account_email = google_service_account.scheduler.email
      audience              = var.backend_service_url
    }
  }

  attempt_deadline = "1800s"  # 30 minutes timeout
}

# ===========================================
# Recovery Job - Check for missed data
# ===========================================
resource "google_cloud_scheduler_job" "recovery_check" {
  name        = "call-quality-recovery-check"
  description = "Check for and recover any missed call data (within 7-day Biztel limit)"
  schedule    = "0 6 * * *"  # Every day at 6:00 AM
  time_zone   = "Asia/Tokyo"
  project     = var.project_id
  region      = var.region

  retry_config {
    retry_count          = 2
    min_backoff_duration = "120s"
    max_backoff_duration = "600s"
    max_doublings        = 1
  }

  http_target {
    http_method = "POST"
    uri         = "${var.backend_service_url}/api/batch/recovery"

    headers = {
      "Content-Type" = "application/json"
    }

    body = base64encode(jsonencode({
      trigger    = "scheduled"
      days_back  = 7
    }))

    oidc_token {
      service_account_email = google_service_account.scheduler.email
      audience              = var.backend_service_url
    }
  }

  attempt_deadline = "3600s"  # 1 hour timeout
}

# ===========================================
# Outputs
# ===========================================
output "daily_batch_job_name" {
  value = google_cloud_scheduler_job.daily_batch.name
}

output "recovery_check_job_name" {
  value = google_cloud_scheduler_job.recovery_check.name
}

output "scheduler_service_account" {
  value = google_service_account.scheduler.email
}
