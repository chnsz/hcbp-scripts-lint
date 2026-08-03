resource "huaweicloud_networking_secgroup" "dr" {
  provider = huaweicloud.dr

  name                 = var.dr_security_group_name
  delete_default_rules = true
}

resource "huaweicloud_vpc" "test" {
  count = var.create_vpc ? 1 : 0

  name = var.vpc_name
  cidr = var.vpc_cidr

  depends_on = [huaweicloud_networking_secgroup.dr]
}
