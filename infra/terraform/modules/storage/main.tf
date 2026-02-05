# ===========================================
# Storage Module - Cloud Storage
# ===========================================

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

# Audio Files Bucket (一時保存用)
resource "google_storage_bucket" "audio" {
  name          = "${var.project_id}-call-quality-audio"
  location      = var.region
  project       = var.project_id
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  # 7日間で自動削除（Biztel録音保持期間に合わせて）
  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }

  versioning {
    enabled = false
  }

  labels = {
    app         = "call-quality-dashboard"
    environment = "production"
  }
}

# Outputs
output "bucket_name" {
  value = google_storage_bucket.audio.name
}

output "bucket_url" {
  value = google_storage_bucket.audio.url
}
