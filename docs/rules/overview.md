# Terraform Linting Rules - Complete Guide

This document provides comprehensive documentation for all Terraform script checking rules, including detailed
descriptions, examples, and implementation principles.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Rule Categories](#rule-categories)
- [ST (Style/Format) Rules](#st-styleformat-rules)
- [IO (Input/Output) Rules](#io-inputoutput-rules)
- [DC (Documentation/Comments) Rules](#dc-documentationcomments-rules)
- [SC (Security Code) Rules](#sc-security-code-rules)
- [Rule Implementation](#rule-implementation)
- [Adding New Rules](#adding-new-rules)

## Architecture Overview

The rules are organized into four main categories, each implemented as a separate package:

- **ST Rules** (`st_rules/`): Style and Format rules
- **DC Rules** (`dc_rules/`): Documentation and Comments rules
- **IO Rules** (`io_rules/`): Input/Output definition rules
- **SC Rules** (`sc_rules/`): Security Code rules

Each package follows the same modular design pattern for consistency and ease of maintenance.

## Directory Structure

```
rules/
├── rules_manager.py            # Unified rules management system
├── __init__.py                 # Package initialization and exports
├── st_rules/                   # ST rules modular package
│   ├── __init__.py             # Package initialization
│   ├── reference.py            # Main STRules coordinator class
│   ├── rule_001.py             # ST.001 - Naming convention check
│   ├── rule_002.py             # ST.002 - Variable default value check
│   ├── rule_003.py             # ST.003 - Parameter alignment check
│   ├── rule_004.py             # ST.004 - Indentation character check
│   ├── rule_005.py             # ST.005 - Indentation level check
│   ├── rule_006.py             # ST.006 - Resource spacing check
│   ├── rule_007.py             # ST.007 - Same parameter block spacing
│   ├── rule_008.py             # ST.008 - Meta-parameter spacing check
│   ├── rule_009.py             # ST.009 - Variable definition order check
│   ├── rule_010.py             # ST.010 - Quote usage consistency check
│   ├── rule_011.py             # ST.011 - Trailing whitespace check
│   ├── rule_012.py             # ST.012 - File header and footer whitespace check
│   ├── rule_013.py             # ST.013 - Directory naming convention check
│   ├── rule_014.py             # ST.014 - File naming convention check
│   └── README.md               # Detailed ST rules documentation
├── dc_rules/                   # DC rules modular package
│   ├── __init__.py             # Package initialization
│   ├── reference.py            # Main DCRules coordinator class
│   ├── rule_001.py             # DC.001 - Comment format check
│   └── README.md               # Detailed DC rules documentation
├── io_rules/                   # IO rules modular package
│   ├── __init__.py             # Package initialization
│   ├── reference.py            # Main IORules coordinator class
│   ├── rule_001.py             # IO.001 - Variable File Location
│   ├── rule_002.py             # IO.002 - Output File Location
│   ├── rule_003.py             # IO.003 - Required Variable Declaration
│   ├── rule_004.py             # IO.004 - Variable Naming Convention
│   ├── rule_005.py             # IO.005 - Output Naming Convention
│   ├── rule_006.py             # IO.006 - Variable Description Check
│   ├── rule_007.py             # IO.007 - Output Description Check
│   ├── rule_008.py             # IO.008 - Variable Type Check
│   ├── rule_009.py             # IO.009 - Variable usage check
│   ├── rule_010.py             # IO.010 - Variable validation block check
│   ├── rule_013.py             # IO.013 - Provider definition file location check
│   └── README.md               # Detailed IO rules documentation
└── sc_rules/                   # SC rules modular package
    ├── __init__.py             # Package initialization
    ├── reference.py            # Main SCRules coordinator class
    ├── rule_001.py             # SC.001 - Array index access safety check
    ├── rule_002.py             # SC.002 - Terraform required version declaration check
    ├── rule_003.py             # SC.003 - Terraform version compatibility check
    ├── rule_004.py             # SC.004 - HuaweiCloud provider version validity check
    ├── rule_005.py             # SC.005 - Sensitive variable declaration check
    ├── rule_006.py             # SC.006 - Hardcoded credential literal check
    ├── rule_007.py             # SC.007 - Sensitive variable non-empty default check
    └── README.md               # Detailed SC rules documentation
```

## Rule Categories

### ST (Style/Format) - Code Formatting Rules

These rules primarily check code formatting, naming conventions, and structural consistency to ensure code has good
readability and maintainability.

### DC (Documentation/Comments) - Comment and Description Rules

These rules check comment formatting and quality to ensure code has good documentation.

### IO (Input/Output) - Input and Output Definition Rules

These rules check variable and output definition and usage standards to ensure module interface clarity and consistency.

### SC (Security Code) - Security Best Practices Rules

These rules enforce security best practices and prevent common security vulnerabilities in Terraform code. They focus on
preventing runtime errors and ensuring safe handling of potentially empty arrays, lists, and other data structures.

## ST (Style/Format) Rules

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
```

**Correct Example:**
```hcl
# ✅ Correct: Instance name is "test"
resource "huaweicloud_vpc" "test" {
  name = "example-vpc"
  cidr = "10.0.0.0/16"
}

data "huaweicloud_availability_zones" "test" {
  region = "cn-north-1"
}
```

### ST.002 - Data Source Variable Default Value Check

**Rule Description:** Validates that all input variables used in data source blocks have default values.
This ensures data sources can work properly with minimal configuration while allowing resources to use required
variables.

**Purpose:**
- Ensure data sources can function independently
- Prevent runtime errors in data source lookups
- Maintain clear separation between required and optional variables

**Error Example:**
```hcl
# ❌ Error: Variable used in data source without default value
variable "memory_size" {
  description = "The memory size (GB) for queried ECS flavors"
  type        = number
  # Missing default value
}

data "huaweicloud_compute_flavors" "test" {
  memory_size = var.memory_size  # This will cause error
}
```

**Correct Example:**
```hcl
# ✅ Correct: Variable has default value
variable "memory_size" {
  description = "The memory size (GB) for queried ECS flavors"
  type        = number
  default     = 8  # Default value provided
}

data "huaweicloud_compute_flavors" "test" {
  memory_size = var.memory_size  # Works correctly
}
```

### ST.003 - Parameter Alignment with Equals Signs

**Rule Description:** Validates that parameter assignments have properly aligned equals signs within the same section.
Supported blocks include resource, data, ephemeral, module, provider, locals, terraform, variable, output, import,
moved, and check (including single-line `{ ... }` bodies). Also supports terraform.tfvars variable assignment alignment.  
All equals signs must align at the same column position within the same group for optimal readability.

**Detailed criteria:** See [ST.003 in st_rules.md](st_rules.md#st003---parameter-alignment-check).

**Purpose:**
- Improve code visual consistency
- Enhance readability of parameter assignments
- Enforce professional formatting standards
- Support the block types listed above, plus terraform.tfvars
- Intelligently handle nested object structures for proper parameter grouping
- Group parameters based on empty lines (blank lines split groups, comment lines don't)
- Sibling `param = {` stays in the current section; nested fields form their own section
- Check alignment only within the same group
- Provide comprehensive error reporting for all alignment issues
- Properly filter out comment lines in all supported file types
- Skip lines with tabs (ST.004) or odd indentation (ST.005-class) so they do not set the equals baseline
- Meta-parameters in resource/data/module/ephemeral require compact `=` spacing but are excluded from column alignment
- Single-parameter groups are still checked for proper spacing

**Error Example:**
```hcl
# ❌ Error: Equals signs not aligned
resource "huaweicloud_vpc_subnet" "test" {
  name = var.subnet_name
  cidr = cidrsubnet(var.vpc_cidr, 4, 1)
  gateway_ip = cidrhost(cidrsubnet(var.vpc_cidr, 4, 1), 1)
  vpc_id = huaweicloud_vpc.test.id
}
```

**Correct Example:**
```hcl
# ✅ Correct: Equals signs properly aligned
resource "huaweicloud_vpc_subnet" "test" {
  name       = var.subnet_name
  cidr       = cidrsubnet(var.vpc_cidr, 4, 1)
  gateway_ip = cidrhost(cidrsubnet(var.vpc_cidr, 4, 1), 1)
  vpc_id     = huaweicloud_vpc.test.id
}
```

### ST.004 - Indentation Character Validation

**Rule Description:** Validates that only spaces are used for indentation, no tabs are allowed.

**Purpose:**
- Ensure consistent indentation across all files
- Prevent mixed indentation issues
- Improve code portability

### ST.005 - Indentation Level Validation

**Rule Description:** Validates that indentation levels follow the correct nesting pattern where each level uses exactly
current_level * 2 spaces. Heredoc blocks (<<EOT, <<EOF, <<POLICY, etc.) are excluded from validation across all file
types. Top-level variable declarations in terraform.tfvars files are properly recognized and excluded from indentation
requirements. Error messages display the actual expected level based on context, not the incorrect indentation level.
Properly handles complex data structures including arrays and objects in terraform.tfvars files.

**Purpose:**
- Enforce consistent indentation standards
- Prevent indentation-related errors
- Support various content types appropriately
- Provide accurate error reporting with correct level information
- Skip tab character detection to avoid duplicate error reporting with ST.004 rule
- Detect missing indentation for block structure elements in complex data structures

### ST.006 - Block Spacing Check

**Rule Description:** Validates that there is exactly one empty line between different Terraform blocks (resource,
data source, variable, output, locals, terraform, provider). Comment lines between blocks do not count as
spacing - blank lines are still required even when comments are present.

**Purpose:**
- Improve code readability
- Create clear visual separation between blocks
- Enforce consistent spacing standards
- Require blank lines between blocks regardless of comment presence
- Support all Terraform block types including terraform and provider blocks

**Comment Line Handling:**
- Comment lines (starting with '#') are ignored during block extraction
- Blank lines are required between blocks even when comment lines are present
- Supports all quote format combinations (quoted/unquoted type and name)
- Comment lines do not count toward the required blank line count

### ST.007 - Parameter Block Spacing Check

**Rule Description:** Validates parameter block spacing within Terraform resource, data source, provider, terraform, and
locals blocks.  
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

### ST.008 - Meta-parameter Spacing Check

**Rule Description:** Validates proper spacing around meta-parameters within Terraform resource and data source blocks.  
This rule ensures consistent spacing between meta-parameters (count, for_each, provider, lifecycle, depends_on) and
other parameters.

**Validation Criteria:**
- **Meta-parameters**: count, for_each, provider, lifecycle, depends_on
- **Meta-parameter to meta-parameter**: Exactly 1 blank line required between different meta-parameters
- **Meta-parameter to non-meta neighbor**: Exactly 1 blank line required between meta-parameters and other parameters
  **or structure/dynamic blocks** (e.g. `count` then `network {` / `dynamic "x" {`), only when no other meta-parameters
  are present between them
- **First meta-parameter**: No blank lines allowed before the first meta-parameter in a block
- **Dynamic block for_each**: for_each inside dynamic blocks should be tightly coupled with the dynamic keyword (no
  blank line)

**Special Cases:**
- When meta-parameters are adjacent to other meta-parameters, only check spacing between these meta-parameters
- When meta-parameters are followed by non-meta neighbors (`=` assignments or structure/dynamic blocks), check spacing
  only if there are no other meta-parameters between them
- for_each inside dynamic blocks is treated as a special case and should be tightly coupled with the dynamic keyword
- ST.007 defers meta-parameter blank-line spacing to ST.008 (including meta → structure/dynamic)

**Purpose:**
- Improve code readability by creating clear visual separation between meta-parameters and other parameters
- Maintain logical grouping of related parameters
- Enforce consistent spacing standards for meta-parameters
- Support all meta-parameter types including count, for_each, provider, lifecycle, and depends_on

**Error Example:**
```hcl
# ❌ Error: Incorrect meta-parameter spacing
resource "huaweicloud_compute_instance" "test" {
  # ST.008 Error: There is a blank line definition ahead of the count meta-parameter
  count = var.instance_count > 0 ? 1 : 0

  # ST.008 Error: There is no blank line between the count meta-parameter and other parameters
  name = var.instance_name
  flavor_id = data.huaweicloud_compute_flavors.test.flavors[0].id

  # ST.008 Error: There are too many blank lines between the depends_on meta-parameter and other parameters


  depends_on = [huaweicloud_vpc.test]
}

# ❌ Error: no blank line between count and a following structure block
resource "huaweicloud_vpc" "gap" {
  count = 1
  network {
    uuid = var.subnet_id
  }
}
```

**Correct Example:**
```hcl
# ✅ Correct: Proper meta-parameter spacing
resource "huaweicloud_compute_instance" "test" {
  count = var.instance_count > 0 ? 1 : 0

  name = var.instance_name
  flavor_id = data.huaweicloud_compute_flavors.test.flavors[0].id

  depends_on = [huaweicloud_vpc.test]

  dynamic "data_disks" {
    for_each = var.data_disks_configurations
    content {
      type = data_disks.value.type
      size = data_disks.value.size
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}
```

### ST.009 - Variable Definition Order Validation

**Rule Description:** Validates that variable definitions in `variables.tf` follow the same order as their first
usage across sibling `*.tf` files (excluding `variables.tf`). First-use order is alphabetical by filename, then
top-to-bottom within each file. Provider-related variables are excluded from ordering validation.

**Purpose:**
- Ensure logical variable organization
- Improve code maintainability
- Support provider configuration patterns

### ST.010 - Resource, Data Source, Variable, Output, and Provider Quote Check

**Rule Description:** Validates that all resource, data source, variable, output, and provider declarations use proper
double quotes around their type and name declarations.

**Purpose:**
- Enforce proper double quote usage for all Terraform block declarations
- Ensure consistent syntax and prevent parsing errors
- Support all Terraform block types including provider blocks

### ST.011 - Trailing Whitespace Detection

**Rule Description:** Detects and reports trailing whitespace at the end of lines.

**Purpose:**
- Clean up unnecessary whitespace
- Prevent version control noise
- Improve code cleanliness

### ST.012 - File Header and Footer Whitespace Check

**Rule Description:** Validates that Terraform files have proper whitespace formatting at the beginning and end.

**Purpose:**
- Ensure consistent file formatting
- Improve file readability
- Standardize file structure

### ST.013 - Directory Naming Convention Check

**Rule Description:** Validates that directory names follow proper naming conventions.

**Purpose:**
- Enforce consistent directory naming
- Improve project organization
- Support cross-platform compatibility

### ST.014 - File Naming Convention Check

**Rule Description:** Validates that file names follow proper naming conventions. Excludes Terraform state files
(terraform.tfstate and variations) and log files (*.log).

**Purpose:**
- Enforce consistent file naming
- Improve project organization
- Support cross-platform compatibility

## IO (Input/Output) Rules

### IO.001 - Variable Definition File Organization

**Rule Description:** Validates that variable definitions are placed in the appropriate files (variables.tf).

**Purpose:**
- Ensure proper file organization
- Improve code maintainability
- Enforce modular structure

### IO.002 - Output Definition File Organization

**Rule Description:** Validates that output definitions are placed in the appropriate files (outputs.tf).

**Purpose:**
- Ensure proper file organization
- Improve code maintainability
- Enforce modular structure

### IO.003 - Required Variable Declaration Check

**Rule Description:** Validates that variables without default values are declared in
`terraform.tfvars` or sibling `*.auto.tfvars` (Terraform auto-load set), excluding
provider-related variables like region / region_*, access_key, secret_key, domain_name.
`default = null` counts as a default. Does not verify whether variables are referenced
as `var.<name>` (see IO.009). Env-split `*.tfvars` and `*.tfvars.json` are not loaded.

**Purpose:**
- Ensure all required variables are properly declared
- Prevent runtime errors
- Support provider configuration patterns

### IO.004 - Variable Naming Convention Check

**Rule Description:** Validates that each input variable name follows naming conventions: can contain letters, numbers,
and underscores; must not start with underscore or number; must not end with number; must not contain consecutive
underscores.

**Purpose:**
- Enforce consistent variable naming
- Improve code readability
- Follow Terraform best practices

### IO.005 - Output Naming Convention Check

**Rule Description:** Validates that each output variable name follows naming conventions: can contain letters, numbers,
and underscores; must not start with underscore or number; must not end with number; must not contain consecutive
underscores.

**Purpose:**
- Enforce consistent output naming
- Improve code readability
- Follow Terraform best practices

### IO.006 - Variable Description Requirement

**Rule Description:** Validates that all input variables have non-empty description fields.

**Purpose:**
- Ensure proper documentation
- Improve code maintainability
- Enforce documentation standards

### IO.007 - Output Description Requirement

**Rule Description:** Validates that all output variables have non-empty description fields.

**Purpose:**
- Ensure proper documentation
- Improve code maintainability
- Enforce documentation standards

### IO.008 - Variable Type Definition Requirement

**Rule Description:** Validates that all input variables have type field defined.

**Purpose:**
- Ensure type safety
- Improve code reliability
- Enforce best practices

### IO.009 - Variable Usage Check

**Rule Description:** Validates that variables declared in `variables.tf` are actually used (references counted in all
sibling `*.tf` files including `variables.tf`, e.g. validation blocks), and that every `var.<name>` reference in the
module directory is declared in `variables.tf`.

**Purpose:**
- Remove dead variable definitions
- Improve code maintainability
- Reduce configuration complexity

### IO.010 - Variable Validation Block Check

**Rule Description:** When a variable declares one or more `validation {}` blocks, each block must include `condition`
and `error_message` fields. Variables without validation blocks are not flagged.

**Purpose:**
- Ensure validation blocks are structurally complete
- Provide actionable error messages for invalid input
- Complement IO.008 type declarations without requiring every variable to use validation

### IO.013 - Provider Definition File Location Check

**Rule Description:** Validates that top-level `provider {}` configuration blocks are defined in `providers.tf`,
not in other `.tf` files. Resource/module `provider = …` meta-arguments are ignored. Complements SC.002/003/004,
which already gate version checks on `providers.tf`.

**Purpose:**
- Keep provider configuration next to `required_providers`
- Align file organization with IO.001/IO.002
- Reinforce the example-repo `providers.tf` convention

**Validation Criteria:**
- Each `validation {}` block must have a `condition` field
- Each `validation {}` block must have a non-empty `error_message` field
- `error_message` must be at least 10 characters and must not equal the variable name
- Empty `validation {}` blocks are not allowed
- Applies only to `variables.tf`

## DC (Documentation/Comments) Rules

### DC.001 - Comment Formatting Standards

**Rule Description:** Validates that comments follow proper formatting standards. Comments must start with '#' character
and maintain one space. `#` characters inside single-quoted or double-quoted string literals are ignored. Inline
end-of-line comments outside quotes are validated. Comments within HCL heredoc blocks are excluded from validation.

**Purpose:**
- Ensure consistent comment formatting
- Improve code readability
- Avoid false positives for `#` inside quoted string values
- Support various content types

## SC (Security Code) Rules

### SC.001 - Unsafe Array Index Access Detection

**Rule Description:** Detects unsafe array index access patterns that could cause runtime errors.

**Purpose:**
- Prevent runtime errors
- Ensure safe array access
- Improve code reliability

### SC.002 - Terraform Required Version Declaration Check

**Rule Description:** Validates that `providers.tf` files contain proper `terraform` block with `required_version`
declaration.

**Purpose:**
- Ensure version consistency
- Prevent compatibility issues
- Enforce version management

### SC.003 - Terraform Version Compatibility Check

**Rule Description:** Analyzes Terraform configuration to determine minimum required version and validates that declared
`required_version` is compatible with used features.

**Purpose:**
- Ensure version compatibility
- Prevent feature incompatibility
- Enforce proper version management

### SC.004 - HuaweiCloud Provider Version Validity Check

**Rule Description:** Validates that the declared HuaweiCloud provider version is valid and available.

**Purpose:**
- Ensure provider version validity
- Prevent deployment failures
- Enforce proper provider management

### SC.005 - Sensitive Variable Declaration Check

**Rule Description:** Validates that sensitive variables are properly declared with `sensitive = true` to prevent data
exposure in state files and logs. Uses exact, segment, and contains name matching with an allowlist for
common non-credential names such as `auth_type`.

**Purpose:**
- Protect sensitive data
- Enforce security best practices
- Prevent data exposure

### SC.006 - Hardcoded Credential Literal Check

**Rule Description:** Flags string literals assigned to known credential attributes
(`access_key`, `secret_key`, `token`, etc.) in `.tf` files. Variable references and
placeholders such as `CHANGEME` are allowed.

### SC.007 - Sensitive Variable Non-Empty Default Check

**Rule Description:** Sensitive-named variables must not declare a non-empty,
non-placeholder string `default`. Complements SC.005 with default hygiene.

## Rule Implementation

### Modular Architecture

Each rule is implemented as a separate Python module with the following structure:

```python
def check_rule_xxx(file_path: str, content: str, log_error_func: Callable) -> None:
    """Main rule checking function."""
    # Rule implementation logic
    pass

def get_rule_description() -> dict:
    """Return rule metadata and description."""
    return {
        "name": "Rule Name",
        "description": "Rule description",
        "category": "ST|IO|DC|SC",
        "status": "modular"
    }
```

### Rule Registration

Rules are registered in their respective `reference.py` files:

```python
_rules_registry = {
    "RULE_ID": {
        "check_function": check_rule_xxx,
        "description_function": get_rule_description,
        "name": "Rule Name",
        "status": "modular"
    }
}
```

### Error Reporting

Rules report errors using the provided `log_error_func`:

```python
log_error_func(file_path, "RULE_ID", "Error message", line_number)
```

## Adding New Rules

### 1. Create Rule Module

Create a new Python file in the appropriate rules directory:

```python
# Example only — next free ST id may differ (current ST rules end at ST.014)
# rules/st_rules/rule_015.py
def check_st015_new_rule(file_path: str, content: str, log_error_func: Callable) -> None:
    """Check for new rule violations."""
    # Implementation logic
    pass

def get_rule_description() -> dict:
    """Return rule metadata."""
    return {
        "name": "New Rule Name",
        "description": "Rule description",
        "category": "ST",
        "status": "modular"
    }
```

### 2. Register Rule

Add the rule to the appropriate `reference.py` file:

```python
from .rule_015 import check_st015_new_rule, get_rule_description as get_st015_description

_rules_registry = {
    # ... existing rules ...
    "ST.015": {  # example id — use the next available rule id
        "check_function": check_st015_new_rule,
        "description_function": get_st015_description,
        "name": "New Rule Name",
        "status": "modular"
    }
}
```

### 3. Update Documentation

Update the relevant documentation files:
- `docs/rules/<category>_rules.md` - Authoritative rule criteria (preferred)
- `docs/rules/overview.md` - Add rule summary
- `README.md` - Update rule count and list
- `rules/README.md` / `rules/introduction.md` - Keep catalogs in sync

### 4. Add Tests

Add good/bad fixtures under `acceptances/good|bad/<rule>/` (preferred). Use `examples/` only for demos.

## Best Practices

1. **Consistent Naming**: Use consistent naming conventions for rule functions and files
2. **Clear Error Messages**: Provide clear, actionable error messages
3. **Performance**: Ensure rules are efficient and don't significantly impact performance
4. **Documentation**: Document all rules thoroughly with examples
5. **Testing**: Create comprehensive test cases for each rule
6. **Backward Compatibility**: Ensure new rules don't break existing functionality

## Support

For questions about rules or adding new rules:

- Check the [Troubleshooting Guide](../guides/troubleshooting.md)
- Review existing rule implementations
- Open an issue in the [project repository](https://github.com/chnsz/hcbp-scripts-lint/issues)
