variable "file_format" {
  type    = string
  default = ""
}

variable "image_name_regex" {
  type    = string
  default = ""
}

variable "image_os" {
  type    = string
  default = ""
}

variable "image_type" {
  type    = string
  default = ""
}

variable "obs_bucket_name" {
  type    = string
  default = ""
}

variable "obs_bucket_tags" {
  type    = map(string)
  default = {}
}

variable "region_name" {
  type    = string
  default = ""
}
