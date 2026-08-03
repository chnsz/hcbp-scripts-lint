resource "huaweicloud_vpc" "old" {
  name = "old"
  cidr = "10.0.0.0/16"
}

resource "huaweicloud_vpc" "new" {
  name = "new"
  cidr = "10.0.0.0/16"
}
