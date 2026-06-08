output "cloud_provider" {
  value = var.cloud_provider
}

output "environment" {
  value = var.environment
}

output "aws_vpc_id" {
  value = try(module.aws[0].vpc_id, null)
}

output "aws_eks_cluster" {
  value = try(module.aws[0].eks_cluster_name, null)
}

output "aws_rds_endpoint" {
  value     = try(module.aws[0].rds_endpoint, null)
  sensitive = true
}

output "aws_s3_bucket" {
  value = try(module.aws[0].s3_bucket_name, null)
}

output "azure_aks_cluster" {
  value = try(module.azure[0].aks_cluster_name, null)
}

output "gcp_gke_cluster" {
  value = try(module.gcp[0].gke_cluster_name, null)
}

output "k8s_namespace" {
  value = try(module.k8s_app[0].namespace, null)
}

output "deployment_url" {
  value = "https://${var.project_name}.${var.environment}.healthcare.ai"
}
