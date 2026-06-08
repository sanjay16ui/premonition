variable "name_prefix" { type = string }
variable "location" { type = string }
variable "instance_type" { type = string; default = "Standard_D4s_v3" }
variable "tags" { type = map(string) }
variable "enable_waf" { type = bool; default = true }
