output "gke_cluster_name" { value = google_container_cluster.main.name }
output "postgres_connection" { value = google_sql_database_instance.main.connection_name }
output "storage_bucket" { value = google_storage_bucket.data.name }
output "secret_id" { value = google_secret_manager_secret.db.secret_id }
output "waf_policy" { value = try(google_compute_security_policy.waf[0].name, null) }
