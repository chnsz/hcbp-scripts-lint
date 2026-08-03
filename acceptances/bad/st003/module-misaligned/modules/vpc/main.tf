variable "name" {
  type = string
}

variable "cidr" {
  type = string
}

output "id" {
  value = "vpc-stub-id"
}
