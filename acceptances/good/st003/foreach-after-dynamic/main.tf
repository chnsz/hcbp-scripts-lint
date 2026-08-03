resource "huaweicloud_vpc" "test" {
  dynamic "tags" {
    for_each = var.tags

    content {
      key   = tags.key
      value = tags.value
    }
  }

  for_each = var.items

  name = var.name
}
