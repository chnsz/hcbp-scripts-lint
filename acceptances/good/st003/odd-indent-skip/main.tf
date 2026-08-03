resource "huaweicloud_vpc" "test" {
  name = var.vpc_name
   cidr = var.vpc_cidr
}
