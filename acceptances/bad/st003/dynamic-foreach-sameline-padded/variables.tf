variable "tag_map" {
  type    = map(string)
  default = {}
}

variable "vpc_cidr" {
  type    = string
  default = ""
}

variable "vpc_name" {
  type    = string
  default = ""
}
