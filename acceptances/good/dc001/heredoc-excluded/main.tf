# Comments inside heredoc blocks are excluded from DC.001
locals {
  script = <<EOT
#! /bin/bash
#This has no space but should be ignored
#  Multiple spaces should also be ignored
echo "hello world!"
EOT
}

resource "huaweicloud_compute_instance" "test" {
  name = "example"

  user_data = <<EOF
#!/bin/bash
#BadFormatInsideHeredoc
echo "Starting application..."
EOF
}
