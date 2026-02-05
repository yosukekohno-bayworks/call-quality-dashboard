# ===========================================
# Networking Module - VPC & VPC Connector
# ===========================================

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

# VPC Network
resource "google_compute_network" "main" {
  name                    = "call-quality-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id
}

# Subnet
resource "google_compute_subnetwork" "main" {
  name          = "call-quality-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.main.id
  project       = var.project_id

  private_ip_google_access = true
}

# VPC Connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  name          = "call-quality-connector"
  region        = var.region
  project       = var.project_id
  network       = google_compute_network.main.name
  ip_cidr_range = "10.8.0.0/28"

  min_instances = 2
  max_instances = 3
}

# Private IP range for Cloud SQL
resource "google_compute_global_address" "private_ip_range" {
  name          = "call-quality-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
  project       = var.project_id
}

# Private Service Connection
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
}

# Outputs
output "vpc_network_id" {
  value = google_compute_network.main.id
}

output "vpc_network_name" {
  value = google_compute_network.main.name
}

output "subnet_id" {
  value = google_compute_subnetwork.main.id
}

output "vpc_connector_id" {
  value = google_vpc_access_connector.connector.id
}
