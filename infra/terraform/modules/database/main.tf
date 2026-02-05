# ===========================================
# Database Module - Cloud SQL PostgreSQL
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

variable "database_tier" {
  type    = string
  default = "db-f1-micro"
}

variable "database_password" {
  type      = string
  sensitive = true
}

# Cloud SQL Instance
resource "google_sql_database_instance" "main" {
  name             = "call-quality-db"
  database_version = "POSTGRES_16"
  region           = var.region
  project          = var.project_id

  settings {
    tier              = var.database_tier
    availability_type = var.database_tier == "db-f1-micro" ? "ZONAL" : "REGIONAL"
    disk_size         = 10
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 7
      }
    }

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = var.vpc_network_id
      enable_private_path_for_google_cloud_services = true
    }

    maintenance_window {
      day          = 7  # Sunday
      hour         = 4  # 4:00 AM
      update_track = "stable"
    }

    insights_config {
      query_insights_enabled  = true
      query_plans_per_minute  = 5
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"  # Log queries taking > 1 second
    }
  }

  deletion_protection = true
}

# Database
resource "google_sql_database" "main" {
  name     = "callquality"
  instance = google_sql_database_instance.main.name
  project  = var.project_id
}

# Database User
resource "google_sql_user" "main" {
  name     = "callquality"
  instance = google_sql_database_instance.main.name
  password = var.database_password
  project  = var.project_id
}

# Outputs
output "connection_name" {
  value = google_sql_database_instance.main.connection_name
}

output "connection_url" {
  value     = "postgresql+asyncpg://callquality:${var.database_password}@/${google_sql_database.main.name}?host=/cloudsql/${google_sql_database_instance.main.connection_name}"
  sensitive = true
}

output "private_ip_address" {
  value = google_sql_database_instance.main.private_ip_address
}
