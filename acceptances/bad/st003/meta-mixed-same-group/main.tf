# Meta-parameter shares a section with attributes (also an ST.008 blank-line issue).
# ST.003 should report compact '=' spacing for provider, not column alignment.
resource "huaweicloud_networking_secgroup" "dr" {
  provider             = huaweicloud.dr
  name                 = var.dr_security_group_name
  delete_default_rules = true
}
