locals {
  index_page = try(var.website_configurations["index"], {
    file_name = "index.html"
    content   = ""
  })
  error_page = try(var.website_configurations["error"], {
    file_name = "error.html"
    content   = ""
  })
}
