variable "bucket_acl" {
  type    = string
  default = ""
}

variable "bucket_encryption" {
  type    = bool
  default = false
}

variable "bucket_encryption_key_id" {
  type    = string
  default = ""
}

variable "bucket_name" {
  type    = string
  default = ""
}

variable "bucket_sse_algorithm" {
  type    = string
  default = ""
}

variable "bucket_storage_class" {
  type    = string
  default = ""
}

variable "bucket_tags" {
  type    = map(string)
  default = {}
}

variable "objects_force_destroy_limits" {
  type    = list(object({
    enabled            = bool
    object_name        = optional(string, "")
    object_name_prefix = optional(string, "")
  }))
  default = []
}

variable "website_configurations" {
  type    = map(object({
    file_name = string
    content   = optional(string, "")
  }))
  default = {}
}
