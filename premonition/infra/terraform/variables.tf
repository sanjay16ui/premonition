variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "premonition"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "cloud_provider" {
  description = "Target cloud: aws, azure, or gcp"
  type        = string
  default     = "aws"
  validation {
    condition     = contains(["aws", "azure", "gcp"], var.cloud_provider)
    error_message = "cloud_provider must be aws, azure, or gcp"
  }
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "azure_location" {
  type    = string
  default = "eastus"
}

variable "gcp_region" {
  type    = string
  default = "us-central1"
}

variable "gcp_zone" {
  type    = string
  default = "us-central1-a"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "instance_type" {
  type    = string
  default = "t3.large"
}

variable "db_instance_class" {
  type    = string
  default = "db.r6g.large"
}

variable "container_image" {
  type    = string
  default = "premonition/api:latest"
}

variable "deploy_kubernetes" {
  type    = bool
  default = true
}

variable "k8s_namespace" {
  type    = string
  default = "premonition"
}

variable "k8s_replicas" {
  type    = number
  default = 3
}

variable "enable_autoscaling" {
  type    = bool
  default = true
}

variable "hpa_min_replicas" {
  type    = number
  default = 2
}

variable "hpa_max_replicas" {
  type    = number
  default = 20
}

variable "enable_multi_region" {
  type    = bool
  default = false
}

variable "enable_cdn" {
  type    = bool
  default = true
}

variable "enable_waf" {
  type    = bool
  default = true
}
