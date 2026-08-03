# ST (Style/Format) Rules Package

> 📖 **For detailed ST rules documentation, see [docs/rules/st_rules.md](../../docs/rules/st_rules.md)**

This package contains all style and format related checking rules for Terraform scripts.  
The package has been refactored into a modular structure where each rule is implemented in a separate module for better
maintainability and extensibility.

## 📁 Package Structure

```
st_rules/
├── __init__.py   # Package initialization and exports
├── README.md     # This documentation file
├── reference.py  # Main STRules coordinator class
├── rule_001.py   # ST.001 - Resource and data source naming convention check
├── rule_002.py   # ST.002 - Variable default value check
├── rule_003.py   # ST.003 - Parameter alignment check
├── rule_004.py   # ST.004 - Indentation character check
├── rule_005.py   # ST.005 - Indentation level check
├── rule_006.py   # ST.006 - Resource and data source spacing check
├── rule_007.py   # ST.007 - Parameter block spacing check
├── rule_008.py   # ST.008 - Meta-parameter spacing check
├── rule_009.py   # ST.009 - Variable definition order check
├── rule_010.py   # ST.010 - Resource, data source, variable, and output quote check
├── rule_011.py   # ST.011 - Trailing whitespace check
├── rule_012.py   # ST.012 - File header and footer whitespace check
├── rule_013.py   # ST.013 - Directory naming convention check
└── rule_014.py   # ST.014 - File naming convention check
```

## 🎯 Available Rules

| Rule ID | Name | Description | Module |
|---------|------|-------------|---------|
| ST.001 | Resource and data source naming convention check | Validates naming conventions for resources and data sources | `rule_001.py` |
| ST.002 | Variable default value check | Ensures variables used in data sources have default values | `rule_002.py` |
| ST.003 | Parameter alignment check | Validates proper parameter alignment and formatting with equals signs aligned to maintain one space from the longest parameter name. | `rule_003.py` |
| ST.004 | Indentation character check | Ensures only spaces are used for indentation (no tabs) | `rule_004.py` |
| ST.005 | Indentation level check | Validates consistent 2-space indentation levels. For terraform.tfvars files, heredoc blocks (<<EOT, <<EOF, etc.) are excluded from validation | `rule_005.py` |
| ST.006 | Resource and data source spacing check | Ensures exactly 1 empty line between resource/data blocks | `rule_006.py` |
| ST.007 | Parameter block spacing check | Validates spacing between different types of parameters within resource, data source, provider, terraform, and locals blocks | `rule_007.py` |
| ST.008 | Meta-parameter spacing check | Validates spacing around meta-parameters (count, for_each, provider, lifecycle, depends_on) | `rule_008.py` |
| ST.009 | Variable definition order check | Validates variable order consistency between files | `rule_009.py` |
| ST.010 | Resource, data source, variable, and output quote check | Ensures double quotes around resource/data source names | `rule_010.py` |
| ST.011 | Trailing whitespace check | Removes trailing spaces and tabs from line endings | `rule_011.py` |
| ST.012 | File header and footer whitespace check | Ensures no extra whitespace at the beginning or end of the file | `rule_012.py` |
| ST.013 | Directory naming convention check | Validates directory names contain only letters, numbers, and hyphens, and start/end with letters | `rule_013.py` |
| ST.014 | File naming convention check | Validates file names contain only letters, numbers, and underscores, and start/end with letters | `rule_014.py` |


## 📋 Rule Details

### ST.001 - Resource and Data Source Naming Convention Check

**Purpose**: Ensures consistent instance naming for resources/data sources and snake_case for variables.

**Validation Criteria**:
- Resource and data source instance names (second identifier) must be `test`
- Variable names must use snake_case (lowercase letters, numbers, underscores; no leading digits)

### ST.002 - Variable Default Value Check  

**Purpose**: Ensures variables used in data sources have default values.

**Validation Criteria**:
- Variables referenced in data source blocks must have default values defined
- Prevents runtime errors from undefined variables

### ST.003 - Parameter Alignment Check

**Purpose**: Validates proper parameter alignment and formatting with equals signs aligned to maintain one space from
the longest parameter name.

**Validation Criteria**:
- Equals signs must be aligned within the same code block
- Aligned equals signs should maintain exactly one space from the longest parameter name in the code block
- Exactly one space after the equals sign and parameter value
- Supports resource, data source, ephemeral, module, provider, locals, terraform, variable, output,
  import, moved, and check blocks (including single-line blocks that contain assignments inside `{}`)
- Supports terraform.tfvars files for variable assignment alignment checking
- Intelligently handles nested object structures by grouping parameters within objects
- Uses expandtabs(2) to properly handle tab characters in indentation calculation
- Even single-parameter groups are checked for proper spacing before the equals sign
- Comment lines are ignored during sectioning and parameter extraction
- Parameters with quotes (e.g., "Environment") are handled correctly with quote_chars = 2
- Nested objects maintain their own alignment groups
- Parameters followed by `{` (nested blocks) are still checked for alignment and spacing

**Alignment Calculation Formula**:
- Expected equals location = indent_spaces + param_name_length + quote_chars + 1
- Where:
  - indent_spaces = indent_level * 2 (Terraform uses 2 spaces per indent level)
  - param_name_length = length of parameter name without quotes
  - quote_chars = 2 if parameter name is quoted (e.g., "format"), 0 otherwise
  - 1 = standard space before equals sign

**Code Block Sectioning Rules**:
- Sections are split on empty lines (true blank lines, not comment lines)
- Empty lines always split sections, regardless of brace level or nesting
- Comment lines are ignored for sectioning (do not split sections)
- Object boundaries ({ and }) create new sections for nested content
- Sibling `param = {` declarations stay in the current section so they align with peer parameters; nested
  fields inside the object form their own section
- For terraform.tfvars files, groups consecutive variable assignments based on actual blank lines
- Nested structures maintain their own alignment groups within objects and arrays

**Special Cases**:
- Lines with tabs (ST.004) or odd indentation (ST.005-class) are skipped and do not set the equals baseline
- In `resource` / `data` / `module` / `ephemeral` blocks, meta-parameters (count, for_each, provider, lifecycle,
  depends_on) are excluded from column-alignment calculations, but still require exactly one space before `=`
- Attributes merely named `count` in variables/locals/object types are not treated as meta-parameters
- `for_each` inside `dynamic` blocks (including same-line `dynamic "x" { for_each = ... }`) is treated as a normal
  parameter; top-level `for_each` after a closed dynamic block is still a meta-parameter (brace-depth tracked)
- Same-line multi-assignment is checked for `=` spacing only (no column alignment)
- Heredoc bodies (`<<EOF` / `<<eot`, etc.) are ignored until the matching terminator
- Column alignment uses max(len(name) + quote_chars) so mixed quoted/unquoted names do not add a global +2
- ST.003 (compact `=` spacing) and ST.008 (blank lines around meta-parameters) are complementary and may both report
- .tfvars may keep consistent extra padding when a majority already share an equals column; single-parameter
  groups still require exactly one space before `=`

**Examples**:

Valid alignment:
```hcl
# All parameters in a group aligned to longest name
resource "huaweicloud_compute_instance" "test" {
  name               = "test-instance"  # "name" is 4 chars, needs 10 spaces before =
  flavor_id          = "c6.large.2"     # "flavor_id" is 9 chars, needs 5 spaces before =
  availability_zone  = "cn-north-1a"    # "availability_zone" is 17 chars (longest), needs 0 spaces before =
}

# Groups separated by blank lines
locals {
  is_available = true  # Group 1 (single parameter)
  
  system_tags = {      # Group 2 (single parameter with nested object)
    "Environment" = "Development"  # Group 3 (nested parameters aligned)
    "Owner"       = "DevOps"       # Group 3 (aligned with "Environment")
  }
}

# Terraform.tfvars - blank lines create separate groups
vpc_name = "test-vpc"    # Group 1

vpc_cidr    = "10.0.0.0/16"  # Group 2 (longest is "vpc_cidr")
subnet_name = "test-subnet"  # Group 2
```

Invalid alignment:
```hcl
# Not aligned with longest parameter
resource "huaweicloud_compute_instance" "test" {
  name= "test-instance"     # ST.003 Error: missing space before =
  flavor_id = "c6.large.2"
  availability_zone = "cn-north-1a"  # ST.003 Error: not aligned (should be at same column as flavor_id)
}

# Multiple spaces after =, not aligned
locals {
  is_available =  true  # ST.003 Error: multiple spaces after =
  system_tags =  {     # ST.003 Error: multiple spaces after =
    "format"        = "ext4"      # Group aligned within object
    "partition_size" = 10         # Group aligned (longest name)
  }
}
```

### ST.004 - Indentation Character Check

**Purpose**: Ensures only spaces are used for indentation.

**Validation Criteria**:
- No tab characters allowed for indentation
- Only space characters should be used

### ST.005 - Indentation Level Check

**Purpose**: Validates consistent 2-space indentation levels.

**Validation Criteria**:
- Each indentation level must use exactly 2 spaces
- Consistent indentation depth throughout the file
- For terraform.tfvars files, heredoc blocks (<<EOT, <<EOF, etc.) are excluded from validation

### ST.006 - Resource and Data Source Spacing Check

**Purpose**: Ensures proper spacing between resource and data source blocks.

**Validation Criteria**:
- Exactly 1 empty line required between different resource/data blocks
- No excessive spacing between blocks
- Comment lines are ignored during block detection
- Comment lines between blocks (without blank lines) are considered acceptable

**Comment Line Handling**:
- Comment lines (starting with '#') are skipped during block extraction
- If only comment lines exist between blocks, this is acceptable
- Comment lines do not count toward the required blank line count

### ST.007 - Parameter Block Spacing Check

**Purpose**: Validates parameter block spacing within Terraform resource, data source, provider, terraform, and locals
blocks.

**Validation Criteria**:
- **Different parameter types**: Exactly 1 blank line required between different parameter types
- **Same-name structure blocks**: 0-1 blank lines allowed between blocks with the same name (compact or single spacing)
- **Adjacent dynamic blocks**: Exactly 1 blank line required between dynamic blocks
- **Same-type basic parameters**: At most 1 blank line between basic parameters
- **Same-type required provider blocks**: 0-1 blank lines allowed between required provider blocks (even with different
  names)
- **Structure and dynamic blocks with same name**: Exactly 1 blank line required

**Parameter Types**:

1. **Basic Parameter**: Simple key-value assignments including numbers, strings, booleans, and single-line conditional
   expressions

   ```hcl
   name = var.instance_name
   count = var.instance_count > 0 ? 1 : 0
   enabled = true
   ```

2. **Advanced Parameter**: Map or array assignments with equals sign before curly brace (distinguished from structure
   blocks)

   ```hcl
   tags = {
     Environment = "production"
     Owner = "team"
   }
   security_groups = ["sg-12345", "sg-67890"]
   ```

3. **Structure Block**: Nested parameter blocks without equals sign before curly brace

   ```hcl
   data_disks {
     type = "SSD"
     size = 20
   }
   network {
     uuid = huaweicloud_vpc_subnet.test.id
   }
   ```

4. **Dynamic Block**: Dynamic parameter blocks using the dynamic keyword

   ```hcl
   dynamic "data_disks" {
     for_each = var.data_disks_configurations
     content {
       type = data_disks.value.type
       size = data_disks.value.size
     }
   }
   ```

5. **Required Provider Block**: Provider assignments within terraform.required_providers block

   ```hcl
   terraform {
     required_providers {
       huaweicloud = {
         source = "huaweicloud/huaweicloud"
         version = ">= 1.57.0"
       }
       kubernetes = {
         source = "hashicorp/kubernetes"
         version = ">= 1.6.2"
       }
     }
   }
   ```

6. **Provider Block**: Provider configuration blocks

   ```hcl
   provider "huaweicloud" {
     region = var.region_name
     access_key = var.access_key
     secret_key = var.secret_key
   }
   ```

**Spacing Rules**:
- **Different parameter types**: Exactly 1 blank line required
- **Same-type basic parameters**: 0-1 blank lines allowed
- **Same-type structure blocks with same name**: 0-1 blank lines allowed
- **Same-type required provider blocks**: 0-1 blank lines allowed (special case)
- **All other combinations**: Exactly 1 blank line required

**Examples**:
```hcl
# Valid spacing
resource "huaweicloud_compute_instance" "test" {
  # Basic parameters
  name = var.instance_name
  flavor_id = data.huaweicloud_compute_flavors.test.flavors[0].id

  # Structure block
  data_disks {
    type = "SSD"
    size = 20
  }

  # Same-name structure block (0-1 blank lines allowed)
  data_disks {
    type = "SAS"
    size = 40
  }

  # Dynamic block
  dynamic "data_disks" {
    for_each = var.data_disks_configurations
    content {
      type = data_disks.value.type
      size = data_disks.value.size
    }
  }

  # Advanced parameter
  tags = merge(local.system_tags, var.custom_tags)
}

# Valid terraform block spacing
terraform {
  required_version = ">= 1.9.0"

  required_providers {
    huaweicloud = {
      source = "huaweicloud/huaweicloud"
      version = ">= 1.57.0"
    }

    kubernetes = {
      source = "hashicorp/kubernetes"
      version = ">= 1.6.2"
    }
  }
}
```

### ST.008 - Meta-parameter Spacing Check

**Purpose**: Validates proper spacing around meta-parameters within Terraform resource and data source blocks.

**Validation Criteria**:
- **Meta-parameters**: count, for_each, provider, lifecycle, depends_on
- **Meta-parameter to meta-parameter**: Exactly 1 blank line required between different meta-parameters
- **Meta-parameter to non-meta-parameter**: Exactly 1 blank line required between meta-parameters and other parameters
  (only when no other meta-parameters are present between them)
- **First meta-parameter**: No blank lines allowed before the first meta-parameter in a block
- **Dynamic block for_each**: for_each inside dynamic blocks should be tightly coupled with the dynamic keyword (no
  blank line)

**Special Cases**:
- When meta-parameters are adjacent to other meta-parameters, only check spacing between these meta-parameters
- When meta-parameters are followed by non-meta-parameters, check spacing only if there are no other meta-parameters
  between them
- for_each inside dynamic blocks is treated as a special case and should be tightly coupled with the dynamic keyword

### ST.009 - Variable Definition Order Check

**Purpose**: Validates variable order consistency between first-use across sibling `*.tf` files and `variables.tf`.

**Validation Criteria**:
- Variable definition order in variables.tf must match first-use order across sibling `*.tf` (excluding `variables.tf`)
- Cross-file analysis for maintaining logical organization
- Provider-related variables (access_key, secret_key, region_name) are excluded from ordering validation
- Excludes authentication and region configuration variables to avoid interference with business logic ordering

### ST.010 - Resource, Data Source, Variable, and Output Quote Check

**Purpose**: Ensures double quotes around resource and data source names.

**Validation Criteria**:
- All resource and data source type and name identifiers must use double quotes
- Consistent quoting style across all Terraform files

### ST.011 - Trailing Whitespace Check

**Purpose**: Removes trailing spaces and tabs from line endings.

**Validation Criteria**:
- No trailing whitespace characters at the end of lines
- Clean line endings for better version control

### ST.012 - File Header and Footer Whitespace Check

**Purpose**: Ensures no extra whitespace at the beginning or end of the file.

**Validation Criteria**:
- No leading or trailing whitespace at the beginning of the file
- No leading or trailing whitespace at the end of the file

### ST.013 - Directory Naming Convention Check

**Purpose**: Validates that all directory names follow proper naming conventions.

**Validation Criteria**:
- Directory names must contain only letters, numbers, and hyphens
- Directory names must start and end with a letter
- No consecutive hyphens allowed
- Recursively checks all subdirectories at any depth
- Automatically skips hidden directories and system directories

**Examples**:
- Valid: `my-project`, `terraform-modules`, `test-env-1`, `data-processing`
- Invalid: `_private-dir` (starts with underscore), `my-project-` (ends with hyphen), `123-project` (starts with number)

### ST.014 - File Naming Convention Check

**Purpose**: Validates that all file names follow proper naming conventions.

**Validation Criteria**:
- File names must contain only letters, numbers, and underscores
- File names must start and end with a letter
- No consecutive underscores allowed
- Recursively checks all files at any depth
- Automatically skips hidden files and system files

**Examples**:
- Valid: `main.tf`, `variables.tf`, `terraform_config.tf`, `test_file.tfvars`
- Invalid: `_private.tf` (starts with underscore), `config-.tf` (ends with underscore), `123_config.tf` (starts with number)

## 🔄 Backward Compatibility

The package maintains full backward compatibility with the original `st_rules.py` module. Existing code will continue to work without modifications:

```python
# This still works
from rules.st_rules import STRules

# Legacy methods are supported
st_rules = STRules()
st_rules.run_all_checks(file_path, content, log_error_func)
st_rules.is_rule_enabled("ST.001")
```

**Note**: While legacy methods like `enable_rule()` and `disable_rule()` are still available, it's recommended to use
the new `execute_all_rules()` method with the `excluded_rules` parameter for better control.

## 🏗️ Architecture Benefits

The modular architecture provides several advantages:

1. **Maintainability**: Each rule is isolated in its own module
2. **Extensibility**: New rules can be added without modifying existing code
3. **Testability**: Individual rules can be tested in isolation
4. **Documentation**: Each rule has comprehensive inline documentation
5. **Performance**: Rules can be selectively enabled/disabled
6. **Code Quality**: Detailed type hints and error handling

## 📝 Contributing

When contributing new rules or modifications:

1. Follow the established naming conventions
2. Include comprehensive documentation and examples
3. Add appropriate type hints
4. Test thoroughly with both valid and invalid cases
5. Update this README with new rule information
6. Ensure error logging function signature matches: `(file_path, rule_id, message, line_number)`
