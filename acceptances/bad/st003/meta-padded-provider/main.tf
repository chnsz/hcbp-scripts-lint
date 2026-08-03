resource "huaweicloud_networking_secgroup" "dr" {
  provider             = huaweicloud.dr

  name                 = var.dr_security_group_name
  delete_default_rules = true
}
