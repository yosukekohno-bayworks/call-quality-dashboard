# ===========================================
# Call Quality Dashboard - GCP Infrastructure
# ===========================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "call-quality-dashboard-tfstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ===========================================
# Enable Required APIs
# ===========================================
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "vpcaccess.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# ===========================================
# Networking Module
# ===========================================
module "networking" {
  source = "./modules/networking"

  project_id = var.project_id
  region     = var.region

  depends_on = [google_project_service.apis]
}

# ===========================================
# Database Module (Cloud SQL)
# ===========================================
module "database" {
  source = "./modules/database"

  project_id         = var.project_id
  region             = var.region
  vpc_network_id     = module.networking.vpc_network_id
  database_tier      = var.database_tier
  database_password  = var.database_password

  depends_on = [module.networking]
}

# ===========================================
# Redis Module (Memorystore)
# ===========================================
module "redis" {
  source = "./modules/redis"

  project_id     = var.project_id
  region         = var.region
  vpc_network_id = module.networking.vpc_network_id
  redis_tier     = var.redis_tier

  depends_on = [module.networking]
}

# ===========================================
# Storage Module (Cloud Storage)
# ===========================================
module "storage" {
  source = "./modules/storage"

  project_id = var.project_id
  region     = var.region
}

# ===========================================
# Cloud Run Module
# ===========================================
module "cloud_run" {
  source = "./modules/cloud-run"

  project_id           = var.project_id
  region               = var.region
  vpc_connector_id     = module.networking.vpc_connector_id
  database_url         = module.database.connection_url
  redis_url            = module.redis.connection_url
  storage_bucket       = module.storage.bucket_name
  backend_image        = var.backend_image
  frontend_image       = var.frontend_image
  secret_key           = var.secret_key
  google_client_id     = var.google_client_id
  google_client_secret = var.google_client_secret
  openai_api_key       = var.openai_api_key
  hume_api_key         = var.hume_api_key
  anthropic_api_key    = var.anthropic_api_key

  depends_on = [module.database, module.redis, module.storage]
}

# ===========================================
# Scheduler Module
# ===========================================
module "scheduler" {
  source = "./modules/scheduler"

  project_id         = var.project_id
  region             = var.region
  backend_service_url = module.cloud_run.backend_url
  service_account_email = module.cloud_run.service_account_email

  depends_on = [module.cloud_run]
}

# ===========================================
# Monitoring Module
# ===========================================
module "monitoring" {
  source = "./modules/monitoring"

  project_id              = var.project_id
  backend_service_name    = module.cloud_run.backend_service_name
  frontend_service_name   = module.cloud_run.frontend_service_name
  celery_service_name     = module.cloud_run.celery_service_name
  notification_email      = var.notification_email

  depends_on = [module.cloud_run]
}
