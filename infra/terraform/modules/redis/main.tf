# ===========================================
# Redis Module - Cloud Memorystore
# ===========================================

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "vpc_network_id" {
  type = string
}

variable "redis_tier" {
  type    = string
  default = "BASIC"
}

# Memorystore Redis Instance
resource "google_redis_instance" "main" {
  name           = "call-quality-redis"
  tier           = var.redis_tier
  memory_size_gb = var.redis_tier == "BASIC" ? 1 : 2
  region         = var.region
  project        = var.project_id

  authorized_network = var.vpc_network_id

  redis_version = "REDIS_7_0"
  display_name  = "Call Quality Dashboard Redis"

  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 4
        minutes = 0
      }
    }
  }

  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }

  labels = {
    app         = "call-quality-dashboard"
    environment = "production"
  }
}

# Outputs
output "host" {
  value = google_redis_instance.main.host
}

output "port" {
  value = google_redis_instance.main.port
}

output "connection_url" {
  value = "redis://${google_redis_instance.main.host}:${google_redis_instance.main.port}/0"
}
