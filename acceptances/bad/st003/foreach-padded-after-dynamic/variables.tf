variable "items" {
  type    = map(any)
  default = {}
}

variable "name" {
  type    = string
  default = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
