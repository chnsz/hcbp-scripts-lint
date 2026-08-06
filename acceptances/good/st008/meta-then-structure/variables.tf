variable "create_vpc" {
  type    = bool
  default = true
}

variable "vpc_cidr" {
  type    = string
  default = ""
}

variable "vpc_name" {
  type    = string
  default = ""
}

variable "subnet_id" {
  type    = string
  default = ""
}
