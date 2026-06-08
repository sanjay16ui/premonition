variable "name_prefix" { type = string }
variable "namespace" { type = string }
variable "image" { type = string }
variable "replicas" { type = number; default = 3 }
variable "enable_hpa" { type = bool; default = true }
variable "min_replicas" { type = number; default = 2 }
variable "max_replicas" { type = number; default = 20 }
