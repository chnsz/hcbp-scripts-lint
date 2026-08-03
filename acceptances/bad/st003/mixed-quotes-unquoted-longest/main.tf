# Unquoted name is longest; global +2 quote bump must not apply.
# Compact unquoted + quoted with only one space before '=' is under-aligned.
locals {
  very_long_parameter_name = "x"
  "ab" = "y"
}
