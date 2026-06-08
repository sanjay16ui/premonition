# PREMONITION — Multi-cloud Terraform root module
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
    azurerm = { source = "hashicorp/azurerm", version = "~> 3.0" }
    google = { source = "hashicorp/google", version = "~> 5.0" }
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.25" }
  }
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# AWS deployment
module "aws" {
  count  = var.cloud_provider == "aws" ? 1 : 0
  source = "./modules/aws"

  name_prefix    = local.name_prefix
  region         = var.aws_region
  vpc_cidr       = var.vpc_cidr
  instance_type  = var.instance_type
  db_instance    = var.db_instance_class
  tags           = local.common_tags
  enable_multi_region = var.enable_multi_region
}

# Azure deployment
module "azure" {
  count  = var.cloud_provider == "azure" ? 1 : 0
  source = "./modules/azure"

  name_prefix   = local.name_prefix
  location      = var.azure_location
  instance_type = var.instance_type
  tags          = local.common_tags
}

# GCP deployment
module "gcp" {
  count  = var.cloud_provider == "gcp" ? 1 : 0
  source = "./modules/gcp"

  name_prefix = local.name_prefix
  region      = var.gcp_region
  zone        = var.gcp_zone
  tags        = local.common_tags
}

# Kubernetes application deployment (cloud-agnostic)
module "k8s_app" {
  count  = var.deploy_kubernetes ? 1 : 0
  source = "./modules/kubernetes"

  name_prefix  = local.name_prefix
  namespace    = var.k8s_namespace
  image        = var.container_image
  replicas     = var.k8s_replicas
  enable_hpa   = var.enable_autoscaling
  min_replicas = var.hpa_min_replicas
  max_replicas = var.hpa_max_replicas
}
