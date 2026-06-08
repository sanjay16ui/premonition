variable "name_prefix" { type = string }
variable "region" { type = string }
variable "zone" { type = string }
variable "tags" { type = map(string) }
variable "enable_cdn" { type = bool; default = true }
variable "enable_waf" { type = bool; default = true }
