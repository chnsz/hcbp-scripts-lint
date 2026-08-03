variable "create_vpc" {
  type    = bool
  default = true
}

variable "dr_security_group_name" {
  type    = string
  default = ""
}

variable "vpc_cidr" {
  type    = string
  default = ""
}

variable "vpc_name" {
  type    = string
  default = ""
}
