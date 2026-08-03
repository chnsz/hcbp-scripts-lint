resource "huaweicloud_vpc" "test" {
  name = var.vpc_name
  cidr = var.vpc_cidr

  dynamic "tags" {
    for_each = var.tag_map

    content {
      key   = tags.key
      value = tags.value
    }
  }
}
