# '#' inside quoted string values must not be treated as comments
resource "random_password" "test" {
  length           = 16
  min_upper        = 1
  min_lower        = 1
  min_numeric      = 1
  special          = true
  override_special = "~!@#%^*-_=+?"
}

locals {
  url_fragment      = "https://example.com/path#section"
  compact_hash      = "a#b#c"
  spaced_hash       = "hello # world"
  single_quoted     = '~!@#%^*-_=+?'
  single_spaced     = 'hello # world'
  after_hash_string = "hello # world" # Proper trailing comment
}
