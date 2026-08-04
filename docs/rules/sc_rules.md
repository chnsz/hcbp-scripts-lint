# SC (Security Code) Rules Package

This package contains all security-related checking rules for Terraform scripts.  
The package has been refactored into a modular structure where each rule is implemented in a separate module for better
maintainability and extensibility.

## 📁 Package Structure

```
sc_rules/
├── __init__.py   # Package initialization and exports
├── README.md     # This documentation file
├── reference.py  # Main SCRules coordinator class
├── rule_001.py   # SC.001 - Array index access safety check
├── rule_002.py   # SC.002 - Terraform required version declaration check
├── rule_003.py   # SC.003 - Terraform version compatibility check
├── rule_004.py   # SC.004 - HuaweiCloud provider version validity check
├── rule_005.py   # SC.005 - Sensitive variable declaration check
├── rule_006.py   # SC.006 - Hardcoded credential literal check
└── rule_007.py   # SC.007 - Sensitive variable non-empty default check
```

## 🎯 Available Rules

| Rule ID | Name | Description | Module |
|---------|------|-------------|---------|
| SC.001 | Array index access safety check | Enforce safe access for risky data/var/local indexes | `rule_001.py` |
| SC.002 | Terraform required version declaration check | Validates that providers.tf files contain terraform block with required_version declaration | `rule_002.py` |
| SC.003 | Terraform version compatibility check | Validates that declared required_version is compatible with features used | `rule_003.py` |
| SC.004 | HuaweiCloud provider version validity check | Deep opt-in probe of version constraints (GitHub + terraform validate) | `rule_004.py` |
| SC.005 | Sensitive variable declaration check | Validates that sensitive variables are properly declared with Sensitive=true | `rule_005.py` |
| SC.006 | Hardcoded credential literal check | Flags credential attribute string literals in `.tf` files | `rule_006.py` |
| SC.007 | Sensitive variable non-empty default check | Sensitive-named variables must not use dangerous non-empty defaults | `rule_007.py` |

## 🚀 Usage

### Basic Usage

```python
from rules.sc_rules import SCRules

# Initialize the rules coordinator
sc_rules = SCRules()

# Define error logging function (note the Optional[int] parameter for line number)
def log_error(file_path, rule_id, message, line_number=None):
    if line_number:
        print(f"ERROR: {file_path} ({line_number}): [{rule_id}] {message}")
    else:
        print(f"ERROR: {file_path}: [{rule_id}] {message}")

# Execute all SC rules on file content
file_content = '''resource "aws_instance" "example" {
  ami = data.aws_ami.ubuntu.images[0].image_id
}'''
sc_rules.execute_all_rules("main.tf", file_content, log_error)

# Execute a specific rule
sc_rules.execute_rule("SC.001", "main.tf", file_content, log_error)

# For backward compatibility, you can also use the legacy method
sc_rules.run_all_checks("main.tf", file_content, log_error)
```

### Advanced Usage

```python
from rules.sc_rules import SCRules

sc_rules = SCRules()

# Get rule information
rule_info = sc_rules.get_rule_info("SC.001")
if rule_info:
    print(f"Rule name: {rule_info['name']}")
    print(f"Description: {rule_info['description']}")
    print(f"Category: {rule_info['category']}")

# Get all available rules
all_rules = sc_rules.get_available_rules()
print(f"Available SC rules: {all_rules}")

# Execute rules with exclusions
excluded_rules = ["SC.001"]  # Example: skip array safety checks
results = sc_rules.execute_all_rules("main.tf", file_content, log_error, excluded_rules)

# Get rules summary
summary = sc_rules.get_rules_summary()
print(f"Total SC rules: {summary['total']}")
print(f"Modular rules: {summary['modular']}")

# Legacy methods (for backward compatibility)
if sc_rules.is_rule_enabled("SC.001"):
    print("SC.001 is available")

# Note: enable_rule() and disable_rule() are legacy methods
# Use excluded_rules parameter in execute_all_rules() instead
```

## 🔧 Adding New Rules

To add a new SC rule, follow these steps:

### 1. Create Rule Implementation File

Create a new file `rule_XXX.py` in this directory:

```python
#!/usr/bin/env python3
"""
SC.XXX - Rule Name

Detailed description of what this security rule validates.

Author: Lance
License: Apache 2.0
"""

from typing import Callable, Optional, Dict, Any

def check_scXXX_rule_name(file_path: str, content: str, log_error_func: Callable[[str, str, str, Optional[int]], None]) -> None:
    """
    Validate according to SC.XXX rule specifications.

    Args:
        file_path (str): Path to the file being checked
        content (str): Complete file content
        log_error_func (Callable): Error logging function with signature:
                                 (file_path, rule_id, message, line_number)
    """
    # Implementation here
    pass

def get_rule_description() -> Dict[str, Any]:
    """
    Get detailed rule information.

    Returns:
        Dict[str, Any]: Rule metadata and examples
    """
    return {
        "id": "SC.XXX",
        "name": "Rule Name",
        "description": "Detailed description",
        "category": "Security Code",
        "severity": "error",
        "examples": {
            "valid": [],
            "invalid": []
        }
    }
```

### 2. Update Reference Class

Add the new rule to `reference.py`:

```python
# Import the new rule
from .rule_XXX import check_scXXX_rule_name, get_rule_description as get_scXXX_description

class SCRules:
    def _build_rules_registry(self) -> Dict[str, Dict[str, Any]]:
        return {
            # Existing rules...
            "SC.XXX": {
                "check_function": check_scXXX_rule_name,
                "description_function": get_scXXX_description,
                "name": "Rule Name",
                "status": "modular"
            }
        }
```

### 3. Update Documentation

Update this README.md file to include the new rule in the Available Rules table.

## 🧪 Testing

The package includes comprehensive testing through the main linting system:

```bash
# Test exclude a SC rule
python3 .github/scripts/terraform_lint.py examples/bad-examples/basic --ignore-rules "SC.001"

# Test all rules including SC
python3 .github/scripts/terraform_lint.py examples/bad-examples/basic
```

## 📋 Rule Details

### SC.001 - Array Index Access Safety Check

**Purpose**: Enforces safe array access patterns to prevent index out of bounds errors.

**Scenarios Covered**:
- Data source list attribute references
- Optional list parameter element references
- Complex nested list access patterns

**Validation Criteria**:
- Flags bare `data.*[N]`, collection-typed `var.*[N]`, and locals from for-expressions / `data.*` aliases
- Literal local lists are not flagged
- Same-line safe wrappers: `try()`, `element()`, `one()`, `can()`, or `length(...) > 0 ? ... : ...`

**Examples**:

**❌ Unsafe (Direct Index Access)**:
```hcl
# Direct array access - can cause errors if index doesn't exist
resource "aws_instance" "example" {
  ami = data.aws_ami.ubuntu.images[0].image_id
}

# Direct access to optional list elements
resource "aws_security_group" "example" {
  ingress {
    cidr_blocks = var.allowed_cidr_blocks[0]
  }
}
```

**✅ Safe (Using try() Function)**:
```hcl
# Safe array access with try() and fallback
resource "aws_instance" "example" {
  ami = try(data.aws_ami.ubuntu.images[0].image_id, "ami-default")
}

# Safe access with null fallback
resource "aws_security_group" "example" {
  ingress {
    cidr_blocks = try(var.allowed_cidr_blocks[0], null)
  }
}

# Using length() check for safety
locals {
  first_cidr = length(var.allowed_cidr_blocks) > 0 ? var.allowed_cidr_blocks[0] : null
}
```

**Best Practices**:
1. Always use `try()` function when accessing array elements by index
2. Provide meaningful fallback values appropriate for the context
3. Consider using `length()` checks for complex validation logic
4. Document expected array structures in variable descriptions

**Alternative Safe Patterns**:
- Use `for_each` instead of direct indexing when possible
- Use `coalesce()` for multiple fallback options
- Implement proper validation in variable definitions

### SC.004 - HuaweiCloud Provider Version Validity Check

**Purpose**: Validates huaweicloud provider version constraints by testing with current and previous versions to ensure
proper version boundaries.

**Requires deep mode**: skipped by default; enable with `--deep`, `HCBP_DEEP_CHECKS=1`, or Action `deep-check: true`.
Runs only on `providers.tf`.

**Scenarios Covered**:
- Version constraint is too permissive (previous version also works)
- Version constraint is too restrictive (current version doesn't work)
- Version constraint points to non-existent version
- Version constraint syntax is invalid

**Validation Criteria**:
- Fetches real version data from GitHub releases
- Finds the previous available version (excluding known problematic versions)
- Executes terraform validate with current version (should pass)
- Executes terraform validate with previous version (should fail)

**Examples**:

**❌ Too Permissive (Previous Version Also Works)**:
```hcl
# Version constraint too permissive - previous version also works
terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = ">= 1.76.0"  # Previous version 1.75.x also works
    }
  }
}
```

**✅ Properly Set (Only Current Version Works)**:
```hcl
# Properly set version constraint - only current version works
terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = ">= 1.77.1"  # Previous version 1.76.5 fails validation
    }
  }
}
```

**❌ Non-existent Version**:
```hcl
# Version doesn't exist in GitHub releases
terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = ">= 99.0.0"  # Non-existent version
    }
  }
}
```

**❌ Invalid Syntax**:
```hcl
# Invalid version constraint syntax
terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "invalid-version"  # Invalid syntax
    }
  }
}
```

**Best Practices**:
1. Use semantic versioning constraints (>=, ~>, etc.)
2. Test version constraints in development environment
3. Check GitHub releases for available versions
4. Exclude known problematic versions (1.63.0-1.63.2, 1.64.0-1.64.2, 1.77.0)
5. Ensure current version passes terraform validate
6. Verify previous version fails terraform validate

**Technical Details**:
- Fetches versions from GitHub API with pagination support
- Excludes known problematic versions automatically
- Executes actual terraform commands for validation
- Provides detailed error messages with suggestions

### SC.005 - Sensitive Variable Declaration Check

**Purpose**: Validates that sensitive variables are properly declared with Sensitive=true to prevent sensitive data
exposure in Terraform state files and logs.

**Sensitive Variable Patterns**:
- **Exact Match**: email, age, access_key, secret_key, sex, signature, api_key, token, private_key
- **Segment Match**: auth, token, api_key (underscore-delimited segment equals pattern)
- **Contains Match**: phone, password, pwd, private_key, credential
- **Allowlist** (segment matches only): auth_type, authorization_mode, oauth_scope, certificate_name

**Validation Criteria**:
- Variables matching sensitive patterns must have `sensitive = true` declaration
- Matching priority: exact → segment → contains
- Segment matches are skipped when the full variable name is in the allowlist
- Parses quoted, single-quoted, and unquoted `variable` headers (unquoted names may still violate ST.010)
- Supports various spacing formats: `sensitive = true`, `sensitive=true`, `sensitive  =  true`
- Ignores comments and only validates actual declarations
- Prevents sensitive data from appearing in Terraform state and logs

**Examples**:

**❌ Missing Sensitive Declaration**:
```hcl
variable "email" {
  type        = string
  description = "User email address"
  # Missing sensitive = true - will trigger error
}

variable "user_password" {
  type        = string
  description = "User password"
  # Missing sensitive = true - will trigger error (fuzzy match)
}
```

**✅ Proper Sensitive Declaration**:
```hcl
variable "email" {
  type        = string
  description = "User email address"
  sensitive   = true
}

variable "user_password" {
  type        = string
  description = "User password"
  sensitive   = true
}

variable "access_key" {
  type        = string
  description = "API access key"
  sensitive   = true
}

variable "api_token" {
  type        = string
  description = "API token"
  sensitive   = true
}

variable "auth_type" {
  type        = string
  description = "Authentication type"
  # Allowlisted — sensitive not required
}
```

**Best Practices**:
1. Always declare sensitive variables with `sensitive = true`
2. Review variable names against sensitive patterns list
3. Use descriptive variable names for non-sensitive data
4. Use allowlisted names only for non-credential configuration switches
5. Regularly audit variable declarations for sensitive data exposure

**Security Impact**:
- **Risk Level**: High
- **Exposure Points**: Terraform state files, Terraform plan output, Terraform apply logs, CI/CD pipeline logs
- **Mitigation**: Declaring sensitive variables prevents their values from being displayed in logs and state files


### SC.006 - Hardcoded Credential Literal Check

**Purpose**: Detect credential attribute string literals embedded in `.tf` files.

**Validation Criteria**:
- Flags `access_key` / `secret_key` / `token` / `api_key` / `password` / `private_key` / `security_token` string literals
- Allows `var.*` references and placeholders (`CHANGEME`, etc.)
- Does not scan `*.tfvars` or perform global entropy detection

### SC.007 - Sensitive Variable Non-Empty Default Check

**Purpose**: Sensitive-named variables must not declare a dangerous non-empty string default.

**Validation Criteria**:
- Uses the same name heuristics as SC.005
- Allows missing default, `""`, `null`, and placeholders
- Complements SC.005 (flag) with default hygiene


## 🔄 Backward Compatibility

The package maintains full backward compatibility with the original `sc_rules.py` module. Existing code will continue to
work without modifications:

```python
# This still works
from rules.sc_rules import SCRules

# Legacy methods are supported
sc_rules = SCRules()
sc_rules.run_all_checks(file_path, content, log_error_func)
sc_rules.is_rule_enabled("SC.001")
```

**Note**: While legacy methods like `enable_rule()` and `disable_rule()` are still available, it's recommended to use
the new `execute_all_rules()` method with the `excluded_rules` parameter for better control.

## 🏗️ Architecture Benefits

The modular architecture provides several advantages:

1. **Maintainability**: Each rule is isolated in its own module
2. **Extensibility**: New security rules can be added without modifying existing code
3. **Testability**: Individual rules can be tested in isolation
4. **Documentation**: Each rule has comprehensive inline documentation
5. **Performance**: Rules can be selectively enabled/disabled
6. **Security Focus**: Dedicated security rule validation with clear examples

## 📝 Contributing

When contributing new security rules or modifications:

1. Follow the established naming conventions
2. Include comprehensive documentation and security examples
3. Add appropriate type hints
4. Test thoroughly with both safe and unsafe code patterns
5. Update this README with new rule information
6. Consider security implications and provide clear mitigation strategies
7. Ensure error logging function signature matches: `(file_path, rule_id, message, line_number)`

## 🔒 Security Considerations

Security rules in this package focus on:

- **Runtime Safety**: Preventing index out of bounds and null reference errors
- **Error Handling**: Ensuring graceful degradation when resources are unavailable
- **Best Practices**: Promoting secure coding patterns in Terraform
- **Defensive Programming**: Encouraging protective measures against common vulnerabilities

When adding new security rules, consider:
- Impact on infrastructure reliability
- Common attack vectors in cloud environments
- Terraform-specific security anti-patterns
- Integration with security scanning tools
