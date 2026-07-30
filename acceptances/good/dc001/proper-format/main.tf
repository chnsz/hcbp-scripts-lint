# Proper full-line comment
# TODO: keep exactly one space after hash

resource "huaweicloud_vpc" "test" {
  name = "example-vpc"
  cidr = "192.168.0.0/16" # Proper inline comment
}

#
# Empty comment above is allowed
variable "example" {
  description = "An example variable"
  type        = string
  default     = "test" # Default value for test environment
}
