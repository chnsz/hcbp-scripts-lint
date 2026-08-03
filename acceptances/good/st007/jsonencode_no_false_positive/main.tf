resource "huaweicloud_compute_instance" "test" {
  name = var.instance_name

  user_data = jsonencode({
    cache_key            = {
      system_params = []
      parameters    = ["custom_param"]
    }
    client_cache_control = {
      mode  = "off"
      datas = []
    }
  })

  network {
    uuid = var.subnet_id
  }
}
