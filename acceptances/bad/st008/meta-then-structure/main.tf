resource "huaweicloud_vpc" "test" {
  count = var.create_vpc ? 1 : 0
  network {
    uuid = var.subnet_id
  }

  name = var.vpc_name
  cidr = var.vpc_cidr
}
