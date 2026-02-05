# ===========================================
# Outputs
# ===========================================

output "backend_url" {
  description = "Backend Cloud Run URL"
  value       = module.cloud_run.backend_url
}

output "frontend_url" {
  description = "Frontend Cloud Run URL"
  value       = module.cloud_run.frontend_url
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = module.database.connection_name
}

output "redis_host" {
  description = "Memorystore Redis host"
  value       = module.redis.host
}

output "storage_bucket" {
  description = "Cloud Storage bucket name"
  value       = module.storage.bucket_name
}

output "artifact_registry_url" {
  description = "Artifact Registry URL"
  value       = module.cloud_run.artifact_registry_url
}
