variable "availability_zone" {
  type    = string
  default = ""
}

variable "create_vpc" {
  type    = bool
  default = true
}

variable "subnet_cidr" {
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
