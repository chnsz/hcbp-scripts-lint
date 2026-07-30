# DC (Documentation/Comments) Rules Package

This package contains all documentation and comment related checking rules for Terraform scripts.  
The package has been refactored into a modular structure where each rule is implemented in a separate module for better
maintainability and extensibility.

## 📁 Package Structure

```
dc_rules/
├── __init__.py  # Package initialization and exports
├── README.md    # This documentation file
├── reference.py # Main DCRules coordinator class
└── rule_001.py  # DC.001 rule implementation
```

## 🎯 Available Rules

| Rule ID | Name | Description | Module |
|---------|------|-------------|---------|
| DC.001 | Comment format check | Validates comment formatting; ignores `#` inside quotes; excludes heredoc | `rule_001.py` |

## 🚀 Usage

### Basic Usage

```python
from rules.dc_rules import DCRules

# Initialize the rules coordinator
dc_rules = DCRules()

# Define error logging function (note the Optional[int] parameter for line number)
def log_error(file_path, rule_id, message, line_number=None):
    if line_number:
        print(f"ERROR: {file_path} ({line_number}): [{rule_id}] {message}")
    else:
        print(f"ERROR: {file_path}: [{rule_id}] {message}")

# Execute all DC rules on file content
file_content = "# Good comment\n#Bad comment"
dc_rules.execute_all_rules("example.tf", file_content, log_error)

# Execute a specific rule
dc_rules.execute_rule("DC.001", "example.tf", file_content, log_error)

# For backward compatibility, you can also use the legacy method
dc_rules.run_all_checks("example.tf", file_content, log_error)
```

### Advanced Usage

```python
from rules.dc_rules import DCRules

dc_rules = DCRules()

# Get rule information
rule_info = dc_rules.get_rule_info("DC.001")
if rule_info:
    print(f"Rule name: {rule_info['name']}")
    print(f"Description: {rule_info['description']}")
    print(f"Category: {rule_info['category']}")

# Get all available rules
all_rules = dc_rules.get_available_rules()
print(f"Available DC rules: {all_rules}")

# Execute rules with exclusions
excluded_rules = ["DC.001"]  # Example: exclude specific rules
results = dc_rules.execute_all_rules("example.tf", file_content, log_error, excluded_rules)

# Get rules summary
summary = dc_rules.get_rules_summary()
print(f"Total DC rules: {summary['total']}")
print(f"Modular rules: {summary['modular']}")

# Legacy methods (for backward compatibility)
if dc_rules.is_rule_enabled("DC.001"):
    print("DC.001 is available")

# Note: enable_rule() and disable_rule() are legacy methods
# Use excluded_rules parameter in execute_all_rules() instead
```

## 🔧 Adding New Rules

To add a new DC rule, follow these steps:

### 1. Create Rule Implementation File

Create a new file `rule_XXX.py` in this directory:

```python
#!/usr/bin/env python3
"""
DC.XXX - Rule Name

Detailed description of what this rule validates.

Author: Lance
License: Apache 2.0
"""

from typing import Callable, Optional, Dict, Any

def check_dcXXX_rule_name(file_path: str, content: str, log_error_func: Callable[[str, str, str, Optional[int]], None]) -> None:
    """
    Validate according to DC.XXX rule specifications.

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
        "id": "DC.XXX",
        "name": "Rule Name",
        "description": "Detailed description",
        "category": "Documentation/Comments",
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
from .rule_XXX import check_dcXXX_rule_name, get_rule_description as get_dcXXX_description

class DCRules:
    def _build_rules_registry(self) -> Dict[str, Dict[str, Any]]:
        return {
            # Existing rules...
            "DC.XXX": {
                "check_function": check_dcXXX_rule_name,
                "description_function": get_dcXXX_description,
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
# Test exclude a DC rule
python3 .github/scripts/terraform_lint.py examples/bad-example/basic --ignore-rules "DC.001"

# Test all rules including DC
python3 .github/scripts/terraform_lint.py examples/bad-example/basic
```

## 📋 Rule Details

### DC.001 - Comment Format Check

**Purpose**: Ensures consistent comment formatting across Terraform files. `#` characters inside single-quoted or
double-quoted string literals are ignored. Inline end-of-line comments outside quotes are validated. Comments within
HCL heredoc blocks (<<EOT, <<EOF, etc.) are excluded from validation.

**Validation Criteria**:
- Comments must start with `#` character
- Exactly one space must follow the `#` character
- Empty comments (only `#`) are allowed
- `#` inside single-quoted or double-quoted strings is not treated as a comment
- Inline end-of-line comments (any `#` outside quotes) are validated
- Comments within HCL heredoc blocks are excluded from validation

**Examples**:

✅ **Valid**:
```hcl
# This is a properly formatted comment
# TODO: Add validation logic
#
resource "random_password" "test" {
  override_special = "~!@#%^*-_=+?"  # '#' inside quotes is ignored
}
```

❌ **Invalid**:
```hcl
#This comment has no space after #
#  This comment has multiple spaces after #
#	This comment has a tab after #
location = "cn-north-1"  #No space in inline comment
```

**HCL Heredoc Example (comments inside are excluded from validation)**:
```hcl
# ✅ Comments in heredoc blocks are excluded from DC.001 validation
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

## 🔄 Backward Compatibility

The package maintains full backward compatibility with the original `dc_rules.py` module. Existing code will continue to
work without modifications:

```python
# This still works
from rules.dc_rules import DCRules

# Legacy methods are supported
dc_rules = DCRules()
dc_rules.run_all_checks(file_path, content, log_error_func)
dc_rules.is_rule_enabled("DC.001")
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
