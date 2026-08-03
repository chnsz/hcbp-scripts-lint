variable "source_availability_zone" {
  description = "The production site AZ of the protection group"
  type        = string
  default     = ""

  validation {
    condition     = (
      (var.source_availability_zone == "" && var.target_availability_zone == "") ||
      (var.source_availability_zone != "" && var.target_availability_zone != "")
    )
    error_message = "Both `source_availability_zone` and `target_availability_zone` must be set, or both must be empty"
  }
}

variable "target_availability_zone" {
  description = "The DR site AZ of the protection group"
  type        = string
  default     = ""
}
