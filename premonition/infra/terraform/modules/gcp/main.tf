terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}

provider "google" {
  region = var.region
  zone   = var.zone
}

resource "google_compute_network" "main" {
  name                    = "${var.name_prefix}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "main" {
  name          = "${var.name_prefix}-subnet"
  ip_cidr_range = "10.2.0.0/24"
  region        = var.region
  network       = google_compute_network.main.id
}

resource "google_container_cluster" "main" {
  name     = "${var.name_prefix}-gke"
  location = var.zone

  remove_default_node_pool = true
  initial_node_count       = 1
  network                  = google_compute_network.main.name
  subnetwork               = google_compute_subnetwork.main.name

  workload_identity_config {
    workload_pool = "${data.google_project.current.project_id}.svc.id.goog"
  }
}

resource "google_container_node_pool" "main" {
  name       = "${var.name_prefix}-nodes"
  location   = var.zone
  cluster    = google_container_cluster.main.name
  node_count = 3

  node_config {
    machine_type = "e2-standard-4"
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    labels       = var.tags
  }

  autoscaling {
    min_node_count = 2
    max_node_count = 20
  }
}

resource "google_sql_database_instance" "main" {
  name             = "${var.name_prefix}-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = "db-custom-4-16384"
    availability_type = "REGIONAL"
    disk_size         = 100
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "03:00"
    }

    ip_configuration {
      ipv4_enabled = false
      private_network = google_compute_network.main.id
    }
  }

  deletion_protection = true
}

resource "google_sql_database" "main" {
  name     = "premonition"
  instance = google_sql_database_instance.main.name
}

resource "google_storage_bucket" "data" {
  name          = "${var.name_prefix}-data-${data.google_project.current.project_id}"
  location      = var.region
  force_destroy = false

  versioning { enabled = true }

  lifecycle_rule {
    condition { age = 365 }
    action { type = "Delete" }
  }

  labels = var.tags
}

resource "google_secret_manager_secret" "db" {
  secret_id = "${var.name_prefix}-db-credentials"
  replication { auto {} }
}

data "google_project" "current" {}

resource "google_compute_backend_bucket" "cdn" {
  count       = var.enable_cdn ? 1 : 0
  name        = "${var.name_prefix}-cdn-backend"
  bucket_name = google_storage_bucket.data.name
  enable_cdn  = true
}

resource "google_compute_security_policy" "waf" {
  count = var.enable_waf ? 1 : 0
  name  = "${var.name_prefix}-waf"

  rule {
    action   = "rate_based_ban"
    priority = 1000
    match {
      versioned_expr = "SRC_IPS_V1"
      config { src_ip_ranges = ["*"] }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 2000
        interval_sec = 60
      }
      ban_duration_sec = 300
    }
  }

  rule {
    action   = "allow"
    priority = 2147483647
    match {
      versioned_expr = "SRC_IPS_V1"
      config { src_ip_ranges = ["*"] }
    }
  }
}
