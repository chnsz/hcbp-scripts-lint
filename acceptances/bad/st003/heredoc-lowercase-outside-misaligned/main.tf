resource "huaweicloud_compute_instance" "test" {
  user_data = <<eot
key = value
longer_name = 1
eot
  name = "a"
  flavor_id = "b"
}
