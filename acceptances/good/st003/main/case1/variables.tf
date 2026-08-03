variable "availability_zone" {
  type    = string
  default = ""
}

variable "bandwidth_charge_mode" {
  type    = string
  default = ""
}

variable "bandwidth_name" {
  type    = string
  default = ""
}

variable "bandwidth_share_type" {
  type    = string
  default = ""
}

variable "bandwidth_size" {
  type    = number
  default = 1
}

variable "cluster_flavor_id" {
  type    = string
  default = ""
}

variable "cluster_name" {
  type    = string
  default = ""
}

variable "cluster_type" {
  type    = string
  default = ""
}

variable "cluster_version" {
  type    = string
  default = ""
}

variable "container_network_type" {
  type    = string
  default = ""
}

variable "data_volumes_configuration" {
  type    = list(object({
    volumetype     = string
    size           = number
    count          = number
    kms_key_id     = optional(string, null)
    extend_params  = optional(map(string), null)
    virtual_spaces = optional(list(object({
      name            = string
      size            = string
      lvm_lv_type     = optional(string, null)
      lvm_path        = optional(string, null)
      runtime_lv_type = optional(string, null)
    })), [])
  }))
  default = []
}

variable "eip_address" {
  type    = string
  default = ""
}

variable "eip_type" {
  type    = string
  default = ""
}

variable "keypair_name" {
  type    = string
  default = ""
}

variable "node_cpu_core_count" {
  type    = number
  default = 1
}

variable "node_memory_size" {
  type    = number
  default = 1
}

variable "node_performance_type" {
  type    = string
  default = ""
}

variable "node_pool_initial_node_count" {
  type    = number
  default = 1
}

variable "node_pool_max_node_count" {
  type    = number
  default = 1
}

variable "node_pool_min_node_count" {
  type    = number
  default = 1
}

variable "node_pool_name" {
  type    = string
  default = ""
}

variable "node_pool_os_type" {
  type    = string
  default = ""
}

variable "node_pool_priority" {
  type    = number
  default = 1
}

variable "node_pool_scale_down_cooldown_time" {
  type    = number
  default = 1
}

variable "node_pool_tags" {
  type    = map(string)
  default = {}
}

variable "node_pool_type" {
  type    = string
  default = ""
}

variable "root_volume_size" {
  type    = number
  default = 1
}

variable "root_volume_type" {
  type    = string
  default = ""
}

variable "subnet_cidr" {
  type    = string
  default = ""
}

variable "subnet_gateway_ip" {
  type    = string
  default = ""
}

variable "subnet_id" {
  type    = string
  default = ""
}

variable "subnet_name" {
  type    = string
  default = ""
}

variable "vpc_cidr" {
  type    = string
  default = ""
}

variable "vpc_id" {
  type    = string
  default = ""
}

variable "vpc_name" {
  type    = string
  default = ""
}
