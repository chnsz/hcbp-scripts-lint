variable "kafka_access_user" {
  type      = string
  sensitive = true
  default   = ""
}

variable "kafka_max_retry_count" {
  type    = number
  default = 1
}

variable "kafka_message_key" {
  type    = string
  default = ""
}

variable "kafka_password" {
  type      = string
  sensitive = true
  default   = ""
}

variable "kafka_retry_backoff" {
  type    = number
  default = 1
}

variable "kafka_sasl_mechanisms" {
  type    = string
  default = ""
}

variable "kafka_sasl_password" {
  type      = string
  sensitive = true
  default   = ""
}

variable "kafka_sasl_username" {
  type      = string
  sensitive = true
  default   = ""
}

variable "kafka_security_protocol" {
  type    = string
  default = ""
}

variable "kafka_ssl_ca_content" {
  type      = string
  sensitive = true
  default   = ""
}

variable "kafka_topic_name" {
  type    = string
  default = ""
}

variable "plugin_description" {
  type    = string
  default = ""
}

variable "plugin_name" {
  type    = string
  default = ""
}
