# Terraform Lint Rules - Detailed Documentation

This document contains detailed descriptions, examples, and implementation principles for all Terraform script checking
rules.

> **Documentation sync note:** Authoritative validation criteria and edge-case behavior for each rule live under
> [`docs/rules/`](../docs/rules/) (for example [`st_rules.md`](../docs/rules/st_rules.md)). This file is a narrative
> overview with examples; when the two disagree, prefer `docs/rules/` and the corresponding `rules/*_rules/rule_*.py`
> implementation. Acceptance fixtures under [`acceptances/`](../acceptances/) are the preferred regression harness.

## Rule Categories

### ST (Style/Format) - Code Formatting Rules
These rules primarily check code formatting, naming conventions, and structural consistency to ensure code has good
readability and maintainability.

### DC (Documentation/Comments) - Comment and Description Rules
These rules check comment formatting and quality to ensure code has good documentation.

### IO (Input/Output) - Input and Output Definition Rules
These rules check variable and output definition and usage standards to ensure module interface clarity and consistency.

### SC (Security Code) - Security Best Practices Rules
These rules enforce security best practices and prevent common security vulnerabilities in Terraform code.
They focus on preventing runtime errors and ensuring safe handling of potentially empty arrays, lists, and other data
structures.

---

## ST (Style/Format) Rule Details

### ST.001 - Resource and Data Source Instance Naming Convention

**Rule Description:** All data source and resource code block instance names must be defined as "test".

**Purpose:**
- Ensure resource naming consistency in test environments
- Avoid using production environment naming in example code
- Improve code readability and standardization

**Error Example:**

```hcl
# ❌ Error: Instance name is not "test"
resource "huaweicloud_vpc" "main" {
  name = "example-vpc"
  cidr = "10.0.0.0/16"
}

data "huaweicloud_availability_zones" "current" {
  region = "cn-north-1"
}

resource "huaweicloud_compute_instance" "example" {
  name      = "test-instance"
  flavor_id = "c6.large.2"
  image_id  = "ba10b6e8-de5d-4d96-b8c0-4d8e1d6c7890"
  vpc_id    = huaweicloud_vpc.main.id
}
```

**Correct Example:**

```hcl
# ✅ Correct: All instance names are "test"
resource "huaweicloud_vpc" "test" {
  name = "example-vpc"
  cidr = "10.0.0.0/16"
}

data "huaweicloud_availability_zones" "test" {
  region = "cn-north-1"
}

resource "huaweicloud_compute_instance" "test" {
  name      = "test-instance"
  flavor_id = "c6.large.2"
  image_id  = "ba10b6e8-de5d-4d96-b8c0-4d8e1d6c7890"
  vpc_id    = huaweicloud_vpc.test.id
}
```

**Best Practices:**
- Use "test" uniformly as instance name in example code and test environments
- Use more descriptive names in production environments
- Consider using variables to manage instance names for easy switching between environments

---

### ST.002 - Data Source Variable Default Value Check

**Rule Description:** All input variables used in data source blocks must be designed as optional parameters (with
default values).

**Purpose:**
- Ensure data sources can work properly with minimal configuration
- Prevent runtime errors from undefined variables in data source queries
- Allow resources to use required variables while data sources use optional ones
- Improve configuration management for data source filtering

**Error Example:**

```hcl
# ❌ Error: Variable used in data source without default value
# variables.tf
variable "memory_size" {
  description = "The memory size (GB) for queried ECS flavors"
  type        = number
  # Missing default value but used in data source
}

variable "instance_name" {
  description = "The name of the ECS instance"
  type        = string
  # No default - OK for resource use only
}

# main.tf
data "huaweicloud_compute_flavors" "test" {
  memory_size = var.memory_size    # Uses variable without default
}

resource "huaweicloud_compute_instance" "test" {
  name = var.instance_name         # OK - resource can use required variables
}
```

**Correct Example:**

```hcl
# ✅ Correct: Data source variables have defaults, resource variables can be required
# variables.tf
variable "memory_size" {
  description = "The memory size (GB) for queried ECS flavors"
  type        = number
  default     = 8                  # Required because used in data source
}

variable "instance_name" {
  description = "The name of the ECS instance"
  type        = string
  # No default - OK for resource use only
}

# main.tf
data "huaweicloud_compute_flavors" "test" {
  memory_size = var.memory_size    # Uses variable with default
}

resource "huaweicloud_compute_instance" "test" {
  name = var.instance_name         # OK - resource can use required variables
}

# terraform.tfvars
instance_name = "my-instance"      # Required variable declared
```

**Best Practices:**
- Provide default values for all variables used in data source blocks
- Use appropriate default values that make sense for filtering/querying
- Required variables (without defaults) can still be used in resource blocks
- Document the purpose of default values in variable descriptions

---

### ST.003 - Parameter Alignment Format Convention

**Rule Description:** Parameter assignments in code blocks must maintain proper alignment formatting with equals signs
aligned to maintain one space from the longest parameter name.

**Detailed criteria:** See [ST.003 in docs/rules/st_rules.md](../docs/rules/st_rules.md#st003---parameter-alignment-check)
for full validation criteria, sectioning rules, and edge cases. Fixtures:
[`acceptances/good/st003`](../acceptances/good/st003/), [`acceptances/bad/st003`](../acceptances/bad/st003/).

**Purpose:**
- Improve code readability and aesthetics
- Maintain consistent code formatting with proper alignment
- Facilitate code review and maintenance
- Comply with Terraform community formatting standards

**Format Requirements:**
- Equals signs must be aligned within the same code block section (blank lines split sections)
- Aligned equals signs should maintain exactly one space from the longest parameter name in the section
- Exactly one space after the equals sign and parameter value
- Parameters within the same section (not separated by blank lines) should follow these alignment rules

**Supported Block Types:**
- `resource`, `data`, `ephemeral`, `module`, `provider`, `locals`, `terraform`, `variable`, `output`
- `import`, `moved`, `check` (including single-line `{ ... }` bodies with assignments)
- `terraform.tfvars` variable assignments (grouped by blank lines)

**Key Special Cases (summary):**
- Sibling `param = {` stays in the current section and aligns with peers; nested fields form their own section
- Lines with tabs (ST.004) or odd indentation (ST.005-class) are skipped and do not set the equals baseline
- In `resource` / `data` / `module` / `ephemeral`, meta-parameters (`count`, `for_each`, `provider`, `lifecycle`,
  `depends_on`) are excluded from column alignment but still require exactly one space before `=`
- `for_each` inside `dynamic` (including same-line `dynamic "x" { for_each = ... }`) is a normal parameter
- Same-line multi-assignment: `=` spacing only (no column alignment)
- Heredoc bodies are ignored until the matching terminator
- tfvars: single-parameter groups still require compact `=` spacing; majority padding may be kept within a group

**Error Example:**

```hcl
# ❌ Error: Improper alignment
resource "huaweicloud_vpc" "test" {
  name                   = "test-vpc"        # The equal sign is not aligned
  cidr                   = "192.168.0.0/16"  # The equal sign is not aligned
  enterprise_project_id  = "0"               # The equal sign is not aligned
}

# ❌ Error: Improper alignment and formatting
resource "huaweicloud_compute_instance" "test" {
  name="test-instance"                                           # No spaces around equals
  flavor_id =c6.large.2                                          # No space after equals, not aligned
  image_id            =  "ba10b6e8-de5d-4d96-b8c0-4d8e1d6c7890"  # Multiple spaces after equals, not aligned
  vpc_id        =    huaweicloud_vpc.test.id                     # Inconsistent spacing, not aligned
  availability_zone="cn-north-1a"                                # No spaces around equals, not aligned
}
```

**Correct Example:**

```hcl
# ✅ Correct: Proper alignment and formatting
resource "huaweicloud_compute_instance" "test" {
  name              = "test-instance"
  flavor_id         = "c6.large.2"
  image_id          = "ba10b6e8-de5d-4d96-b8c0-4d8e1d6c7890"
  vpc_id            = huaweicloud_vpc.test.id
  availability_zone = "cn-north-1a"

  tags = {
    Environment = "test"
    Purpose     = "example"
  }
}
```

**Alignment Rules:**
- Find the longest parameter name in the section (e.g., "availability_zone" = 17 characters)
- All equals signs should align at position: base_indent + longest_parameter_name + quote_chars + 1 space
- In the example above: 2 spaces (indent) + 17 characters (longest name) + 1 space = column 20
- Shorter parameter names are padded with spaces to align their equals signs

**Best Practices:**
- Use `terraform fmt` command to automatically format code
- Configure Terraform formatting plugins in IDE
- Add format checking steps in CI/CD pipeline
- Use consistent formatting tools and configurations within the team
- Ensure proper alignment within each code block section
- Prefer adding/updating fixtures under `acceptances/good|bad/st003/` when changing this rule

---

### ST.004 - Indentation Character Convention

**Rule Description:** All indentation must use spaces only, not tabs.

**Purpose:**
- Ensures consistent formatting across different editors and environments
- Prevents indentation-related parsing issues
- Maintains uniform code appearance

**Good Example:**
```hcl
resource "huaweicloud_vpc" "test" {
  name = "test-vpc"
  cidr = "10.0.0.0/16"

  tags = {
    Environment = "test"
  }
}
```

**Bad Example:**
```hcl
resource "huaweicloud_vpc" "test" {
	name = "test-vpc"    # Uses tab character
	cidr = "10.0.0.0/16" # Uses tab character
}
```

**Best Practices:**
- Configure your editor to show whitespace characters
- Set up automatic tab-to-space conversion
- Use consistent indentation settings across the team

---

### ST.005 - Indentation Level Convention

**Rule Description:** Indentation must follow the rule of 2 spaces per nesting level.

**Purpose:**
- Ensures consistent code structure
- Improves readability and maintainability
- Follows Terraform community standards

**Good Example:**
```hcl
resource "huaweicloud_vpc" "test" {
  name = "test-vpc"
  cidr = "10.0.0.0/16"

  tags = {
    Environment = "test"
    Project     = "demo"
  }
}
```

**Bad Example:**
```hcl
resource "huaweicloud_vpc" "test" {
    name = "test-vpc"    # 4 spaces instead of 2
cidr = "10.0.0.0/16"     # No indentation

      tags = {           # 6 spaces instead of 2
    Environment = "test" # Inconsistent indentation
  }
}
```

**Best Practices:**
- Configure editor to use 2 spaces for indentation
- Use automatic formatting tools
- Maintain consistent indentation throughout the file

---

### ST.006 - Resource and Data Source Spacing Convention

**Rule Description:** There must be exactly one empty line between resource and data source blocks.

**Purpose:**
- Improves code organization and visual separation
- Maintains consistent block spacing standards
- Enhances code readability

**Good Example:**
```hcl
data "huaweicloud_availability_zones" "test" {
  region = var.region
}

resource "huaweicloud_vpc" "test" {
  name = var.vpc_name
  cidr = var.vpc_cidr
}

resource "huaweicloud_vpc_subnet" "test" {
  name   = var.subnet_name
  vpc_id = huaweicloud_vpc.test.id
}
```

**Bad Example:**
```hcl
data "huaweicloud_availability_zones" "test" {
  region = var.region
}
resource "huaweicloud_vpc" "test" {  # Missing empty line
  name = var.vpc_name
}


resource "huaweicloud_vpc_subnet" "test" {  # Too many empty lines
  name = var.subnet_name
}
```

**Best Practices:**
- Always separate blocks with exactly one empty line
- Use consistent spacing throughout the file
- Consider using automated formatting tools

---

### ST.007 - Parameter Block Spacing Check

**Rule Description:** Validates parameter block spacing within Terraform resource, data source, provider, terraform,
and locals blocks.  
This rule ensures consistent spacing between different types of parameters across all supported parameter types.

**Validation Criteria:**
- **Different parameter types**: Exactly 1 blank line required between different parameter types
- **Same-name structure blocks**: 0-1 blank lines allowed between blocks with the same name (compact or single spacing)
- **Adjacent dynamic blocks**: Exactly 1 blank line required between dynamic blocks
- **Same-type basic parameters**: At most 1 blank line between basic parameters
- **Same-type required provider blocks**: 0-1 blank lines allowed between required provider blocks (even with different
  names)
- **Structure and dynamic blocks with same name**: Exactly 1 blank line required

**Parameter Types:**

1. **Basic Parameter**: Simple key-value assignments including numbers, strings, booleans, and single-line conditional
   expressions
2. **Advanced Parameter**: Map or array assignments with equals sign before curly brace (distinguished from structure
   blocks)
3. **Structure Block**: Nested parameter blocks without equals sign before curly brace
4. **Dynamic Block**: Dynamic parameter blocks using the dynamic keyword
5. **Required Provider Block**: Provider assignments within terraform.required_providers block
6. **Provider Block**: Provider configuration blocks

**Spacing Rules:**
- **Different parameter types**: Exactly 1 blank line required
- **Same-type basic parameters**: 0-1 blank lines allowed
- **Same-type structure blocks with same name**: 0-1 blank lines allowed
- **Same-type required provider blocks**: 0-1 blank lines allowed (special case)
- **All other combinations**: Exactly 1 blank line required

**Purpose:**
- Improve code readability by creating clear visual separation between different parameter types
- Maintain logical grouping of related parameters
- Enforce consistent spacing standards within resource definitions
- Support all parameter types including basic parameters, advanced parameters, structure blocks, dynamic blocks,
  required provider blocks, and provider blocks

**Good Example:**
```hcl
resource "huaweicloud_compute_instance" "test" {
  name = var.instance_name
  flavor_id = data.huaweicloud_compute_flavors.test.flavors[0].id

  data_disks {
    type = "SSD"
    size = 20
  }

  data_disks {
    type = "SAS"
    size = 40
  }

  dynamic "data_disks" {
    for_each = var.data_disks_configurations
    content {
      type = data_disks.value.type
      size = data_disks.value.size
    }
  }

  network {
    uuid = huaweicloud_vpc_subnet.test.id
  }

  tags = merge(local.system_tags, var.custom_tags)
}
```

**Bad Example:**
```hcl
resource "huaweicloud_compute_instance" "test" {
  name = var.instance_name
  flavor_id = data.huaweicloud_compute_flavors.test.flavors[0].id
  data_disks {  # Missing blank line between basic parameter and structure block
    type = "SSD"
    size = 20
  }

  data_disks {  # Too many blank lines between same-name structure blocks
    type = "SAS"
    size = 40
  }

  dynamic "data_disks" {  # Missing blank line between structure and dynamic blocks
    for_each = var.data_disks_configurations
    content {
      type = data_disks.value.type
      size = data_disks.value.size
    }
  }
}
```

**Best Practices:**
- Use exactly one blank line between different parameter types
- Use 0-1 blank lines between same-name structure blocks
- Use exactly one blank line between dynamic blocks
- Use at most one blank line between basic parameters
- Maintain consistent spacing patterns throughout resource definitions

---

*Missing blank line between basic parameters and parameter blocks:*
```hcl
resource "huaweicloud_compute_instance" "test" {
  name              = var.instance_name
  flavor_id         = try(data.huaweicloud_compute_flavors.test.flavors[0].id, null)
  system_disk_type  = "SAS"
  system_disk_size  = 40
  data_disks {        # ❌ Error: Missing blank line between basic parameter and parameter block
    size = 40
    type = "SAS"
  }

  tags = {
    "key" = "value"
  }
}
```

*Missing blank line between parameter blocks and basic parameters:*
```hcl
resource "huaweicloud_compute_instance" "test" {
  name              = var.instance_name
  flavor_id         = try(data.huaweicloud_compute_flavors.test.flavors[0].id, null)
  system_disk_type  = "SAS"
  system_disk_size  = 40

  data_disks {
    size = 40
    type = "SAS"
  }
  tags = {            # ❌ Error: Missing blank line between parameter block and basic parameter
    "key" = "value"
  }
}
```

*Comment lines handling:*
```hcl
resource "huaweicloud_compute_instance" "test" {
  name              = var.instance_name
  flavor_id         = try(data.huaweicloud_compute_flavors.test.flavors[0].id, null)
  system_disk_type  = "SAS"
  system_disk_size  = 40
  # This is a comment line - does not count as blank line
  data_disks {        # ❌ Error: Missing blank line (comment lines don't count as blank lines)
    size = 40
    type = "SAS"
  }
}
```

**Best Practices:**
- Always separate different parameter types with exactly one empty line
- Group related basic parameters together before parameter blocks
- Use consistent spacing throughout the resource definition
- Remember that comment lines do not count as blank lines for spacing purposes
- Consider the logical flow when organizing parameters: basic configuration first, then complex nested structures

---

### ST.008 - Meta-parameter Spacing Check

**Rule Description:** Validates blank-line spacing around resource/data meta-parameters (`count`, `for_each`,
`provider`, `lifecycle`, `depends_on`). Complements ST.003 (which owns `=` spacing/alignment for those parameters).

**Validation Criteria:**
- Exactly 1 blank line between different meta-parameters
- Exactly 1 blank line between a meta-parameter and following non-meta parameters (when no other meta sits between)
- No blank lines before the first meta-parameter in a block
- `for_each` inside `dynamic` blocks is not treated as a resource-level meta-parameter for this rule

**Purpose:**
- Keep meta-parameters visually grouped and easy to scan
- Avoid ambiguous adjacency between lifecycle/provider meta and normal attributes

**Best Practices:**
- Place meta-parameters near the top of the resource/data block
- Keep one blank line between the meta group and ordinary attributes

**Cross-references**: Works with [ST.003](#st003---parameter-alignment-format-convention),
                      [ST.007](#st007---parameter-block-spacing-check)

---

### ST.009 - Variable Definition Order Convention

**Rule Description:** Variable definition order in `variables.tf` must match first-use order across sibling `*.tf`
files (excluding `variables.tf`). First-use order is alphabetical by filename, then top-to-bottom within each file.

**Purpose:**
- Improves code readability and logical flow
- Makes it easier to understand variable dependencies
- Facilitates code review and maintenance
- Ensures consistent variable organization across projects

**Error Example:**

```hcl
# ❌ Error: Variable definition order doesn't match usage order
# main.tf - Variables used in this order: region, vpc_name, vpc_cidr, subnet_name
resource "huaweicloud_vpc" "test" {
  name   = var.vpc_name      # Second variable used
  cidr   = var.vpc_cidr      # Third variable used
  region = var.region        # First variable used
}

resource "huaweicloud_vpc_subnet" "test" {
  name   = var.subnet_name   # Fourth variable used
  vpc_id = huaweicloud_vpc.test.id
}

# variables.tf - Variables defined in wrong order
variable "vpc_cidr" {        # Should be third, but defined second
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "region" {          # Should be first, but defined first (correct)
  description = "The region where resources are located"
  type        = string
  default     = "cn-north-1"
}

variable "vpc_name" {        # Should be second, but defined third
  description = "The name of the VPC"
  type        = string
  default     = "test-vpc"
}

variable "subnet_name" {     # Should be fourth, defined fourth (correct)
  description = "The name of the subnet"
  type        = string
  default     = "test-subnet"
}
```

**Correct Example:**

```hcl
# ✅ Correct: Variable definition order matches usage order
# main.tf - Variables used in this order: region, vpc_name, vpc_cidr, subnet_name
resource "huaweicloud_vpc" "test" {
  name   = var.vpc_name      # Second variable used
  cidr   = var.vpc_cidr      # Third variable used
  region = var.region        # First variable used
}

resource "huaweicloud_vpc_subnet" "test" {
  name   = var.subnet_name   # Fourth variable used
  vpc_id = huaweicloud_vpc.test.id
}

# variables.tf - Variables defined in correct order
variable "region" {          # First variable used in main.tf
  description = "The region where resources are located"
  type        = string
  default     = "cn-north-1"
}

variable "vpc_name" {        # Second variable used in main.tf
  description = "The name of the VPC"
  type        = string
  default     = "test-vpc"
}

variable "vpc_cidr" {        # Third variable used in main.tf
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_name" {     # Fourth variable used in main.tf
  description = "The name of the subnet"
  type        = string
  default     = "test-subnet"
}
```

**Best Practices:**
- Define variables in `variables.tf` in the same order they are first referenced in sibling implementation `*.tf` files
- Review variable usage order when adding new variables
- Consider grouping related variables together while maintaining usage order
- Use consistent variable ordering across similar modules
- Document any intentional deviations from usage order with comments

### ST.010 - Resource, Data Source, Variable, and Output Quote Check

**Rule Description:** All data sources, resources, variables, and outputs must have their type and name (or just name
for variables/outputs) enclosed in double quotes.

**Purpose:**
- Ensures consistent Terraform syntax across all configurations
- Prevents syntax errors and improves code readability
- Maintains compatibility with Terraform formatting tools
- Follows Terraform community standards for all block declarations

**Error Example:**

```hcl
# ❌ Error: Missing quotes around various declaration types
# main.tf - Various quoting violations
data huaweicloud_availability_zones test {
  region = var.region
}

data "huaweicloud_compute_flavors" test_flavor {
  performance_type = "normal"
  cpu_core_count   = 2
}

resource huaweicloud_vpc "test" {
  name = var.vpc_name
  cidr = var.vpc_cidr
}

resource "huaweicloud_vpc_subnet" test_subnet {
  name   = var.subnet_name
  vpc_id = huaweicloud_vpc.test.id
}

# variables.tf - Variable quoting violations
variable test_var {
  description = "Variable without quotes"
  type        = string
  default     = "test"
}

variable 'single_quote_var' {
  description = "Variable with single quotes"
  type        = string
  default     = "test"
}

# outputs.tf - Output quoting violations
output test_output {
  description = "Output without quotes"
  value       = "test_value"
}

output 'single_quote_output' {
  description = "Output with single quotes"
  value       = "test_value"
}
```

**Correct Example:**

```hcl
# ✅ Correct: Proper double quotes around all types and names
# main.tf - Consistent quoting style
data "huaweicloud_availability_zones" "test" {
  region = var.region
}

data "huaweicloud_compute_flavors" "test" {
  performance_type = "normal"
  cpu_core_count   = 2
}

resource "huaweicloud_vpc" "test" {
  name = var.vpc_name
  cidr = var.vpc_cidr
}

resource "huaweicloud_vpc_subnet" "test" {
  name   = var.subnet_name
  vpc_id = huaweicloud_vpc.test.id
}

# variables.tf - Proper variable quoting
variable "test_var" {
  description = "Variable with proper quotes"
  type        = string
  default     = "test"
}

variable "correct_var" {
  description = "Another variable with proper quotes"
  type        = string
  default     = "test"
}

# outputs.tf - Proper output quoting
output "test_output" {
  description = "Output with proper quotes"
  value       = "test_value"
}

output "correct_output" {
  description = "Another output with proper quotes"
  value       = "test_value"
}
```

**Best Practices:**
- Always use double quotes for resource/data source types and names
- Always use double quotes for variable and output names
- Maintain consistent quoting style throughout all Terraform files
- Use automated formatting tools like `terraform fmt` to ensure compliance
- Configure IDE/editor to highlight syntax violations

**Cross-references**: Works with [ST.001](#st001---resource-and-data-source-instance-naming-convention),
                      [ST.003](#st003---parameter-alignment-format-convention)

### ST.011 - Trailing Whitespace Check

**Rule Description:** All lines in Terraform files must not contain trailing whitespace characters (spaces, tabs, or
other whitespace) at the end of lines.

**Purpose:**
- Prevents unnecessary diff noise in version control systems
- Maintains clean and consistent code formatting
- Follows general coding best practices for all languages
- Ensures compatibility with automated formatting tools
- Reduces merge conflicts caused by inconsistent whitespace

**Error Example:**

```hcl
# ❌ Error: Lines with trailing whitespace
resource "huaweicloud_compute_instance" "test" { 
  name                 = "example"  
  instance_type        = "s6.large.2"	
  availability_zone    = "cn-north-4a"

  network {
    uuid = data.huaweicloud_vpc_subnet.test.id
  }
}

variable "region" {  
  description = "The region where resources will be created"
  type        = string
  default     = "cn-north-4"   
} 
```

**Correct Example:**

```hcl
# ✅ Correct: No trailing whitespace
resource "huaweicloud_compute_instance" "test" {
  name                 = "example"
  instance_type        = "s6.large.2"
  availability_zone    = "cn-north-4a"

  network {
    uuid = data.huaweicloud_vpc_subnet.test.id
  }
}

variable "region" {
  description = "The region where resources will be created"
  type        = string
  default     = "cn-north-4"
}
```

**Best Practices:**
- Configure your editor to automatically trim trailing whitespace on save
- Use `.editorconfig` files to standardize whitespace handling across team members
- Enable editor settings to visualize trailing whitespace
- Use automated formatting tools like `terraform fmt` which removes trailing whitespace
- Set up pre-commit hooks to prevent trailing whitespace from being committed

**Cross-references**: Works with [ST.004](#st004---indentation-character-convention),
                      [ST.005](#st005---indentation-level-convention)

### ST.012 - File Header and Footer Whitespace Check

**Rule Description:** Terraform files should not have empty lines before the first non-empty line and should have
exactly one empty line after the last non-empty line.

**Purpose:**
- Ensures consistent file formatting across all Terraform files
- Prevents unnecessary leading whitespace that can affect readability
- Maintains proper file endings for version control systems
- Follows professional code formatting standards
- Reduces merge conflicts caused by inconsistent file formatting

**Error Example:**

```hcl
# ❌ Error: File has empty lines before first non-empty line
# ❌ Error: File has no empty line after last non-empty line

resource "huaweicloud_vpc" "test" {
  name = "example-vpc"
  cidr = "192.168.0.0/16"
}

# This is the last line without proper trailing empty line
```

**Correct Example:**

```hcl
# ✅ Correct: No empty lines before first non-empty line
resource "huaweicloud_vpc" "test" {
  name = "example-vpc"
  cidr = "192.168.0.0/16"
}

# This is the last line
[empty line]
```

**Best Practices:**
- Configure your editor to automatically add/remove leading/trailing empty lines
- Use `.editorconfig` files to standardize file formatting across team members
- Set up pre-commit hooks to ensure proper file formatting
- Use automated formatting tools that handle file whitespace consistently
- Maintain consistent file formatting across all Terraform files in the project

**Cross-references**: Works with [ST.011](#st011---trailing-whitespace-check)

---

### ST.013 - Directory Naming Convention Check

**Rule Description:** Directory names must contain only letters, numbers, and hyphens, and must start and end with
letters.

**Purpose:**
- Enforce consistent directory naming across modules
- Improve cross-platform path compatibility
- Keep example/module trees easy to navigate

**Best Practices:**
- Prefer lowercase hyphenated names (e.g., `compute-instance`, `obs-bucket`)
- Avoid underscores, spaces, and leading/trailing hyphens or digits

---

### ST.014 - File Naming Convention Check

**Rule Description:** File names must contain only letters, numbers, and underscores, and must start and end with
letters. Terraform state files and `*.log` files are excluded.

**Purpose:**
- Enforce consistent file naming
- Improve project organization and tooling compatibility

**Best Practices:**
- Use snake_case for custom `.tf` helpers when not using standard names (`main.tf`, `variables.tf`, …)
- Keep standard Terraform filenames unchanged

---

## DC (Documentation/Comments) Rule Details

### DC.001 - Comment Format Convention

**Rule Description:** All comments must start with `#` character and maintain one English space between the `#` and the
comment text. `#` characters inside single-quoted or double-quoted string literals are ignored. Inline end-of-line
comments (any `#` outside quotes) are validated. Comments within HCL heredoc blocks (<<EOT, <<EOF, etc.) are excluded
from validation.

**Purpose:**
- Ensure comment format consistency and readability
- Comply with Terraform community comment standards
- Improve code professionalism and maintainability
- Facilitate automated tool processing of comment content
- Avoid false positives for `#` inside quoted string values
- Avoid false positives when validating embedded scripts or configuration files in heredoc blocks

**Error Example:**

```hcl
# ❌ Error: Improper comment formatting
#This is an incorrect comment format              # No space
#  This comment has multiple spaces               # Multiple spaces
resource "huaweicloud_resource_group" "test" {
  name     = "example-resources"
  location = "cn-north-1"                         #No space in inline comment
}

#Another incorrect comment
variable "example" {
  description = "An example variable"
  type        = string
  default     = "test"
}
```

**Correct Example:**

```hcl
# ✅ Correct: Proper comment formatting
# This is a correct comment format
# Create resource group to contain all related resources
resource "huaweicloud_resource_group" "test" {
  name     = "example-resources"
  location = "cn-north-1"              # Resource group location
}

# Define example variable
# Used to demonstrate proper variable definition
variable "example" {
  description = "An example variable"
  type        = string
  default     = "test"                 # Default value for test environment
}

# '#' inside quoted strings is not treated as a comment
resource "random_password" "test" {
  override_special = "~!@#%^*-_=+?"
}
```

**HCL Heredoc Example (comments inside are excluded from validation):**

```hcl
# ✅ Correct: Comments in heredoc blocks are excluded from DC.001 validation
locals = <<EOT
#! /bin/bash
echo "hello world!"
# This comment in heredoc block is not validated
EOT

resource "aws_instance" "test" {
  user_data = <<EOF
#!/bin/bash
# This comment is also excluded from validation
echo "Starting application..."
EOF
}
```

**Best Practices:**
- Add explanatory comments for complex resource configurations
- Use comments in variable and output definitions to explain purposes
- Use comments to document important configuration decisions and limitations
- Keep comment content accurate and up-to-date
- Avoid over-commenting obvious code
- `#` characters inside single-quoted or double-quoted strings are ignored
- Comments within heredoc blocks (<<EOT, <<EOF, etc.) are automatically excluded from validation

---

## IO (Input/Output) Rule Details

### IO.001 - Variable Definition File Convention

**Rule Description:** Validates that each input variable is properly defined in the `variables.tf` file and not in other
files. Each variable definition found in non-`variables.tf` files will be reported as a separate violation with specific
line numbers.

**Purpose:**
- Maintain project structure consistency and clarity
- Facilitate centralized variable management and maintenance
- Improve code readability and maintainability
- Comply with Terraform community best practices
- Ensure precise error reporting for each misplaced variable

**Project Structure Example:**

```
terraform-project/
├── main.tf             # Main resource definitions (For best practice required)
├── variables.tf        # All variable definitions (For best practice required if variables are difined)
├── outputs.tf          # All output definitions (For best practice required if outputs are difined)
├── terraform.tfvars    # Variable value definitions (For best practice required if optional variables are difined)
└── versions.tf         # Provider version constraints
```

**Error Example:**

```hcl
# ❌ Error: Defining variables in main.tf
# main.tf
variable "resource_group_name" {    # Line 3: Variables should be in variables.tf
  description = "Name of the resource group"
  type        = string
  default     = "example-rg"
}

resource "huaweicloud_resource_group" "test" {
  name     = var.resource_group_name
  location = var.location
}

variable "location" {               # Line 12: Variables should be in variables.tf
  description = "Huawei Cloud region"
  type        = string
  default     = "cn-north-1"
}
```

**Correct Example:**

```hcl
# ✅ Correct: Variables defined in variables.tf
# variables.tf
variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "example-rg"
}

variable "location" {
  description = "Huawei Cloud region for resources"
  type        = string
  default     = "cn-north-1"
}

# main.tf
resource "huaweicloud_resource_group" "test" {
  name     = var.resource_group_name
  location = var.location
}
```

**Best Practices:**
- Keep all variable definitions in `variables.tf`
- Use descriptive variable names
- Include clear descriptions for all variables
- Consider using variable validation blocks
- Document any special requirements or constraints

---

### IO.002 - Output Definition File Organization Convention

**Rule Description:** Validates that each output variable is properly defined in the `outputs.tf` file and not in other
files. Each output definition found in non-`outputs.tf` files will be reported as a separate violation with specific
line numbers.

**Purpose:**
- Maintain project structure clarity and consistency within each directory
- Facilitate centralized output management and documentation
- Improve module interface readability
- Comply with Terraform community best practices
- Ensure outputs are organized at the appropriate directory level
- Provide precise error reporting for each misplaced output

**Error Example:**

```hcl
# ❌ Error: Outputs defined in main.tf instead of outputs.tf
# main.tf
resource "huaweicloud_resource_group" "test" {
  name     = var.resource_group_name
  location = var.location
}

output "resource_group_id" {          # Line 6: Should be in outputs.tf
  description = "The ID of the created resource group"
  value       = huaweicloud_resource_group.test.id
}

output "resource_group_name" {        # Line 11: Should be in outputs.tf
  description = "The name of the created resource group"
  value       = huaweicloud_resource_group.test.name
}

# outputs.tf
# No output definitions - outputs incorrectly placed in main.tf
```

**Correct Example:**

```hcl
# ✅ Correct: Outputs defined in outputs.tf
# outputs.tf
output "resource_group_id" {
  description = "The ID of the created resource group"
  value       = huaweicloud_resource_group.test.id
}

output "resource_group_name" {
  description = "The name of the created resource group"
  value       = huaweicloud_resource_group.test.name
}

# main.tf
resource "huaweicloud_resource_group" "test" {
  name     = var.resource_group_name
  location = var.location
}
```

**Best Practices:**
- Keep all output definitions in `outputs.tf`
- Provide clear descriptions for all outputs
- Mark sensitive outputs appropriately
- Consider using output validation
- Document any special output formats or requirements

---

### IO.003 - Required Variable Declaration Check in terraform.tfvars

**Rule Description:** Validates that all required variables (variables without default values) are declared in the
`terraform.tfvars` file. Each missing variable declaration is reported individually with precise line numbers.

**Purpose:**
- Ensure all required variables have explicit value definitions
- Provide clear configuration entry points
- Facilitate configuration management for different environments
- Avoid runtime variable undefined errors
- Ensure precise error reporting for each missing variable declaration

**Error Example:**

```hcl
# ❌ Error: Missing required variable values in terraform.tfvars
# main.tf
variable "cpu_cores" {            # Line 2: Required variable missing from tfvars
  description = "Number of CPU cores"
  type        = number
  # No default value, this is a required variable
}

variable "memory_size" {          # Line 8: Required variable missing from tfvars
  description = "Memory size in GB"
  type        = number
  # No default value, this is a required variable
}

variable "flavor_id" {            # Line 14: Optional variable
  description = "The flavor ID"
  type        = string
  default     = "c6.2xlarge.4"   # Has default - optional
}

# terraform.tfvars
# Missing declarations for required variables cpu_cores and memory_size
flavor_id = "c6.4xlarge.8"       # Optional variable declared (not required)
```

**Correct Example:**

```hcl
# ✅ Correct: All required variables declared in terraform.tfvars
# variables.tf
variable "cpu_cores" {
  description = "Number of CPU cores"
  type        = number
  # No default - required
}

variable "memory_size" {
  description = "Memory size in GB"
  type        = number
  # No default - required
}

variable "flavor_id" {
  description = "The flavor ID"
  type        = string
  default     = "c6.2xlarge.4"   # Has default - optional
}

# terraform.tfvars
cpu_cores = 4                     # Required variable declared
memory_size = 8                   # Required variable declared
# flavor_id is optional, no need to declare (but can be overridden)
```

**Best Practices:**
- Create a `terraform.tfvars` file for all required variables
- Provide example values in `terraform.tfvars.example`
- Use environment-specific `.tfvars` files for different environments
- Document all required variables and their expected values
- Consider using variable validation blocks
- Ensure each required variable is declared individually in `terraform.tfvars`

---

### IO.004 - Variable Naming Convention Check

**Rule Description:** Validates that each input variable name follows naming conventions: can contain letters, numbers,
and underscores; must not start with underscore or number; must not end with number; must not contain consecutive
underscores.
For each invalid variable definition, an error is reported showing the file where the variable is defined (e.g., if an
invalid variable is defined in main.tf, the error file will show as main.tf).

**Purpose:**
- Ensure consistent variable naming patterns across all input variables
- Improve code readability and maintainability
- Prevent naming conflicts and confusion
- Comply with Terraform community naming standards
- Provide precise error identification for each invalid variable name with accurate file location reporting

**Error Example:**

```hcl
# ❌ Error: Invalid variable naming in main.tf
# main.tf
variable "_invalid_name" {    # Error: Starts with underscore
  description = "Invalid variable name"
  type        = string
}

variable "InvalidName" {      # Error: Contains uppercase letters
  description = "Invalid variable name"
  type        = string
}

variable "invalid-name" {     # Error: Contains hyphen
  description = "Invalid variable name"
  type        = string
}
```

**Correct Example:**

```hcl
# ✅ Correct: Valid variable naming
variable "valid_name" {
  description = "Valid variable name"
  type        = string
}

variable "another_valid_name" {
  description = "Another valid variable name"
  type        = string
}

variable "instance_count" {
  description = "Valid variable name with descriptive purpose"
  type        = number
}
```

**Best Practices:**
- Use lowercase letters and underscores only
- Never start variable names with underscores
- Use descriptive but concise names
- Follow consistent naming patterns across the project
- Consider using prefixes for related variables (e.g., `vpc_name`, `vpc_cidr`)
- Each variable naming violation is reported individually for precise error identification
- Error messages show the exact file where the variable is defined

---

### IO.005 - Output Naming Convention Check

**Rule Description:** Validates that each output variable name follows naming conventions: can contain letters, numbers,
and underscores; must not start with underscore or number; must not end with number; must not contain consecutive
underscores.
For each invalid output definition, an error is reported showing the file where the output is defined (e.g., if an
invalid output is defined in main.tf, the error file will show as main.tf).

**Purpose:**
- Ensure consistent output naming patterns across all output variables
- Improve module interface clarity and readability
- Maintain consistent output naming standards
- Comply with Terraform community naming standards
- Provide precise error identification for each invalid output name with accurate file location reporting

**Error Example:**

```hcl
# ❌ Error: Invalid output naming in main.tf
# main.tf
output "_invalid_output" {    # Error: Starts with underscore
  description = "Invalid output name"
  value       = "test"
}

output "BadOutputName" {      # Error: Contains uppercase letters
  description = "Invalid output name"
  value       = "test"
}

output "invalid-output" {     # Error: Contains hyphen
  description = "Invalid output name"
  value       = "test"
}
```

**Correct Example:**

```hcl
# ✅ Correct: Valid output naming
output "valid_output" {
  description = "Valid output name"
  value       = "test"
}

output "another_valid_output" {
  description = "Another valid output name"
  value       = "test"
}

output "instance_id" {
  description = "Valid output name with descriptive purpose"
  value       = "instance-123"
}
```

**Best Practices:**
- Use lowercase letters and underscores only
- Never start output names with underscores
- Use descriptive but concise names
- Follow consistent naming patterns across the project
- Consider using prefixes for related outputs (e.g., `vpc_id`, `vpc_cidr`)
- Each output naming violation is reported individually for precise error identification
- Error messages show the exact file where the output is defined

---

### IO.006 - Variable Description Convention

**Rule Description:** The input variables must have a description field defined and not empty.

**Purpose:**
- Improves code documentation and usability
- Facilitates automated documentation generation
- Helps users understand variable purposes

**Good Example:**
```hcl
variable "vpc_name" {
  description = "The name of the VPC to be created"
  type        = string
  default     = "test-vpc"
}

variable "environment" {
  description = "The deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}
```

**Bad Example:**
```hcl
variable "vpc_name" {
  # Missing description field
  type    = string
  default = "test-vpc"
}

variable "environment" {
  description = ""  # Empty description
  type        = string
  default     = "dev"
}
```

**Best Practices:**
- Always provide meaningful descriptions for variables
- Describe the purpose and expected values
- Include examples or constraints when helpful
- Keep descriptions concise but informative

---

### IO.007 - Output Description Check

**Rule Description:** All output variables must have a description field defined and not empty.

**Purpose:**
- Improve module documentation and usability
- Ensure outputs are properly documented for users
- Provide clear explanations of output purposes and values
- Enhance code maintainability and team collaboration

**Error Example:**

```hcl
# ❌ Error: Missing or empty description fields
output "instance_id" {
  value = huaweicloud_compute_instance.test.id
  # Missing description field
}

output "vpc_cidr_block" {
  description = ""  # Empty description
  value       = huaweicloud_vpc.test.cidr
}

output "resource_tags" {
  description = "   "  # Whitespace only description
  value       = local.common_tags
}
```

**Correct Example:**

```hcl
# ✅ Correct: Outputs with proper descriptions
output "instance_id" {
  description = "The ID of the created ECS instance"
  value       = huaweicloud_compute_instance.test.id
}

output "vpc_cidr_block" {
  description = "The CIDR block of the created VPC"
  value       = huaweicloud_vpc.test.cidr
}

output "resource_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}
```

**Best Practices:**
- Always include meaningful descriptions for all outputs
- Keep descriptions concise but informative
- Explain what the output represents and its intended use
- Avoid empty or whitespace-only descriptions
- Use consistent description formatting across the module

---

### IO.008 - Variable Type Convention

**Rule Description:** All input variables must have a type field defined.

**Purpose:**
- Improves type safety and validation
- Prevents runtime type-related errors
- Enhances code documentation and clarity

**Good Example:**
```hcl
variable "vpc_name" {
  description = "The name of the VPC"
  type        = string
  default     = "test-vpc"
}

variable "subnet_count" {
  description = "Number of subnets to create"
  type        = number
  default     = 2
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
```

**Bad Example:**
```hcl
variable "vpc_name" {
  description = "The name of the VPC"
  # Missing type field
  default     = "test-vpc"
}

variable "subnet_count" {
  description = "Number of subnets to create"
  # Missing type field
  default     = 2
}
```

**Best Practices:**
- Always specify the type for all variables
- Use appropriate Terraform type constraints
- Consider using complex types (list, map, object) when appropriate
- Validate input types to prevent runtime errors

---

### IO.009 - Variable Usage Check

**Rule Description:** Validates variable definitions and references within a module directory. Reports variables
defined in `variables.tf` but never referenced as `var.<name>`, and reports `var.<name>` references that are not
declared in `variables.tf`. References are counted in all sibling `*.tf` files, **including** `variables.tf` itself
(for example inside `validation {}` blocks).

**Purpose:**
- Identifies unused variable definitions and missing declarations
- Recognizes cross-variable validation as legitimate usage
- Helps keep `variables.tf` aligned with actual module usage
- Improves maintainability of module inputs

**Good Example:**
```hcl
# variables.tf
variable "vpc_name" {
  description = "The name of the VPC"
  type        = string
  default     = "test-vpc"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

# main.tf
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = var.vpc_name  # ✅ Variable is used
  }
}

resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = var.instance_type  # ✅ Variable is used
  
  tags = {
    Name = "WebServer"
  }
}
```

**Bad Example:**
```hcl
# variables.tf
variable "vpc_name" {
  description = "The name of the VPC"
  type        = string
  default     = "test-vpc"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "unused_variable" {
  description = "This variable is never used"
  type        = string
  default     = "unused-value"
}

# main.tf
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = var.vpc_name  # ✅ Variable is used
  }
}

resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = var.instance_type  # ✅ Variable is used
  
  tags = {
    Name = "WebServer"
  }
}

# ❌ Error: Variable 'unused_variable' is defined but never used
```

**Smart Exclusions:**
The rule automatically excludes common provider-related variables that may be used by the provider but not explicitly
referenced in configuration files:
- Provider configuration variables (e.g., `region`, `access_key`, `secret_key`)
- Authentication-related variables (e.g., `token`, `key_file`, `tenant_id`)
- Environment-specific variables (e.g., `endpoint`, `domain_id`, `project_id`)

**Best Practices:**
- Regularly review and remove unused variable definitions
- Keep variable definitions focused on actual usage requirements
- Prefer declaring every referenced `var.<name>` in `variables.tf`
- Document provider-only inputs that may appear unused in resources

**Error Output Format:**
```
ERROR: variables.tf (15): [IO.009] Variable 'unused_variable' is defined but never used
ERROR: variables.tf (7): [IO.009] Variable 'min_count' is referenced but not declared in variables.tf
```

---

### IO.010 - Variable Validation Block Check

**Rule Description:** When a variable defines one or more `validation {}` blocks, each block must include both
`condition` and `error_message`. Variables without validation blocks are not checked.

**Purpose:**
- Ensure validation failures are actionable
- Keep variable constraints documented at the definition site

**Error Example:**

```hcl
# ❌ Error: validation missing error_message
variable "vpc_name" {
  type = string
  validation {
    condition = can(regex("^[a-zA-Z0-9_-]+$", var.vpc_name))
  }
}
```

**Correct Example:**

```hcl
variable "vpc_name" {
  type = string
  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]+$", var.vpc_name))
    error_message = "VPC name must contain only alphanumeric characters, underscores, and hyphens."
  }
}
```

---

### IO.013 - Provider Definition File Location Check

**Rule Description:** Top-level `provider {}` configuration blocks must be defined in `providers.tf`, not in other
`.tf` files. Does not flag resource/module `provider` meta-arguments, and does not police `terraform {}` /
`required_providers` (see SC.002).

**Purpose:**
- Keep provider configuration colocated with version constraints
- Mirror IO.001/IO.002 file-organization conventions for providers

**Best Practices:**
- Put `provider "huaweicloud" { ... }` in `providers.tf` next to `terraform { required_providers ... }`

---

## SC (Security Code) Rule Details

### SC.001 - Array Index Access Safety Check

**Rule Description:** Validates that array index access operations use try() function to prevent index out of bounds
errors in specific scenarios.

**Purpose:**
- Prevent runtime errors from array index out of bounds
- Ensure safe handling of data source query results
- Promote defensive programming practices for list variable access
- Validate safe usage of HCL for expressions with array indexing
- Improve Terraform configuration reliability

**Scenarios Covered:**
1. **Data Source List Attribute References**: Data source returns empty list when no matching resources found
2. **Optional List Parameter Element References**: Optional input variables might be empty lists
3. **For Expressions in Local Variables**: For expressions generating dynamic lists that could be empty

**Error Example:**

```hcl
# ❌ Error: Unsafe array index access
# variables.tf
variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
  default     = []  # Could be empty
}

# main.tf
data "huaweicloud_compute_flavors" "test" {
  vcpus = 2
}

locals {
  queried_availability_zones = [for az in data.huaweicloud_availability_zones.test.names : az if az != "cn-north-1c"]
}

resource "huaweicloud_compute_instance" "test" {
  name              = "test-instance"
  flavor_id         = data.huaweicloud_compute_flavors.test.flavors[0].id  # Unsafe: might be empty
  subnet_id         = var.subnet_ids[0]                                    # Unsafe: variable might be empty
  availability_zone = local.queried_availability_zones[0]                  # Unsafe: for expression might be empty
}
```

**Correct Example:**

```hcl
# ✅ Correct: Safe array index access with try() function
# variables.tf
variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
  default     = []  # Could be empty
}

variable "default_subnet_id" {
  description = "Default subnet ID when subnet_ids is empty"
  type        = string
  default     = "default-subnet-123"
}

# main.tf
data "huaweicloud_compute_flavors" "test" {
  vcpus = 2
}

locals {
  queried_availability_zones = [for az in data.huaweicloud_availability_zones.test.names : az if az != "cn-north-1c"]
}

resource "huaweicloud_compute_instance" "test" {
  name              = "test-instance"
  flavor_id         = try(data.huaweicloud_compute_flavors.test.flavors[0].id, "c6.large.2")  # Safe with fallback
  subnet_id         = try(var.subnet_ids[0], var.default_subnet_id)                           # Safe with fallback
  availability_zone = try(local.queried_availability_zones[0], "cn-north-1a")                 # Safe with fallback
}
```

**Best Practices:**
- Always use try() function when accessing array elements that might not exist
- Provide meaningful fallback values for try() functions
- Consider using length() function to check array size before accessing elements
- Design data structures to avoid empty array scenarios when possible
- Use conditional expressions combined with try() for complex scenarios

**Alternative Safe Patterns:**

```hcl
# Pattern 1: Length check before access
resource "huaweicloud_compute_instance" "test" {
  flavor_id = length(data.huaweicloud_compute_flavors.test.flavors) > 0 ? 
              data.huaweicloud_compute_flavors.test.flavors[0].id : 
              "c6.large.2"
}

# Pattern 2: Using coalescelist for array handling
resource "huaweicloud_compute_instance" "test" {
  subnet_id = coalescelist(var.subnet_ids, [var.default_subnet_id])[0]
}

# Pattern 3: Using try() with multiple fallbacks
resource "huaweicloud_compute_instance" "test" {
  availability_zone = try(
    local.queried_availability_zones[0],
    data.huaweicloud_availability_zones.test.names[0],
    "cn-north-1a"
  )
}
```

---

### SC.002 - Terraform Required Version Declaration Check

**Rule Description:** `providers.tf` must contain a `terraform` block with a `required_version` declaration.

**Purpose:**
- Pin Terraform language compatibility for modules
- Make version expectations explicit for consumers

---

### SC.003 - Terraform Version Compatibility Check

**Rule Description:** Declared `required_version` must be compatible with language features used in the configuration
(for example newer type constraints or expressions that require a higher Terraform version).

**Purpose:**
- Prevent modules from declaring versions that cannot parse/run the code
- Surface version gaps early in CI

---

### SC.004 - HuaweiCloud Provider Version Validity Check

**Rule Description:** Deep opt-in check (`--deep` / `HCBP_DEEP_CHECKS`) that probes HuaweiCloud provider version
constraints for validity. Skipped by default.

**Purpose:**
- Catch invalid or outdated provider version constraints before consumers hit install failures

---

### SC.005 - Sensitive Variable Declaration Check

**Rule Description:** Variables whose names indicate sensitive data must declare `sensitive = true`.

**Purpose:**
- Reduce accidental exposure of secrets in plans and logs
- Align naming intent with Terraform sensitivity marking

---

### SC.006 - Hardcoded Credential Literal Check

**Rule Description:** Flags credential-related attributes that embed string literal secrets in `.tf` files.

**Purpose:**
- Discourage committing credentials in source
- Push secrets toward variables, env, or secret stores

---

### SC.007 - Sensitive Variable Non-Empty Default Check

**Rule Description:** Sensitive-named variables must not use dangerous non-empty default values.

**Purpose:**
- Prevent shipping real or placeholder secrets as defaults
- Keep sensitive inputs explicitly provided by callers

---

## Rule Ignoring and Customization

### Ignoring Specific Rules

In some cases, you may need to ignore specific rules. You can use the following methods:

1. **Command Line Arguments:**

```bash
# Ignore single rule
python3 terraform_lint.py --ignore-rules ST.001

# Ignore multiple rules
python3 terraform_lint.py --ignore-rules ST.001,DC.001,IO.002
```

2. **GitHub Actions Configuration:**

```yaml
- name: Terraform Lint
  uses: ./
  with:
    ignore-rules: 'ST.001,DC.001'
    exclude-paths: 'examples/*,test/*'
```

### Rule Extension

To add custom rules, please refer to the existing rule implementation patterns:

1. Add new check functions in the appropriate rule file
2. Register new check functions in the rule class
3. Update rule documentation and test cases

---

## Summary

These rules aim to improve the quality, consistency, and maintainability of Terraform code. Following these rules can:

- **Improve Code Quality:** Unified formatting and naming conventions
- **Enhance Readability:** Clear structure and comprehensive documentation
- **Facilitate Maintenance:** Modular design and standardized interfaces
- **Reduce Errors:** Strict variable management and validation
- **Team Collaboration:** Consistent code style and best practices

It is recommended to continuously use this checking tool during project development and adjust rule configurations
according to team needs.
