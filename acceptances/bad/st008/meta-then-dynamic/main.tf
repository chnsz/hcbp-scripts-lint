resource "huaweicloud_vpc" "test" {
  count = var.create_vpc ? 1 : 0
  dynamic "tags" {
    for_each = var.tag_map

    content {
      key   = tags.key
      value = tags.value
    }
  }

  name = var.vpc_name
  cidr = var.vpc_cidr
}
