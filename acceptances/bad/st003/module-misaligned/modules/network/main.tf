variable "vpc_id" {
  type = string
}

variable "subnet_cidr" {
  type = string
}

variable "availability_zone" {
  type = string
}

output "id" {
  value = "subnet-stub-id"
}
