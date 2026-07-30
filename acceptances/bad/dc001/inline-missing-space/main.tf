# Proper full-line comment
resource "huaweicloud_vpc" "test" {
  name = "example-vpc" #Missing space in inline comment
  cidr = "192.168.0.0/16"
}
