# Terraform Scripts Lint Tool - Technical Introduction

## Overview

The Terraform Scripts Lint Tool is a comprehensive static analysis tool designed to enforce coding standards and best
practices for Terraform infrastructure-as-code projects. Built with Python 3 and designed for seamless integration with
GitHub Actions, this tool provides automated code quality checking for Terraform configurations.

## Core Architecture

### 1. Main Linting Engine (`.github/scripts/terraform_lint.py`)

**Purpose**: Central orchestration and execution engine for all linting operations.

**Key Components**:
- **TerraformLinter Class**: Main controller that coordinates all linting activities
- **Path Management**: Intelligent file discovery and filtering system
- **Rule Execution**: Orchestrates rule checking across different categories
- **Report Generation**: Produces comprehensive lint reports with metrics

**Implementation Highlights**:

```python
class TerraformLinter:
    def __init__(self, ignored_rules, include_paths, exclude_paths):
        # Initialize rule checkers for different categories
        self.st_rules = STRules()  # Style/Format rules
        self.dc_rules = DCRules()  # Documentation/Comments rules
        self.io_rules = IORules()  # Input/Output rules
        self.sc_rules = SCRules()  # Security Code rules
```

**Key Features**:
- Multi-encoding file support (UTF-8, Latin-1, CP1252)
- Performance-optimized path filtering
- Comprehensive error handling and logging
- Modular rule system integration

### 2. Rule System Architecture

The tool implements a modular rule system organized into four distinct categories:

#### ST Rules (`rules/st_rules.py`) - Style/Format
**Purpose**: Enforce code formatting and style consistency.

**Core Rules**:
- **ST.001**: Resource and data source naming conventions
- **ST.002**: Default value checking convention
- **ST.003**: Parameter alignment and spacing standards
- **ST.004**: Indentation character validation (spaces only)
- **ST.005**: Indentation level consistency (2 spaces per level, excludes heredoc blocks in .tfvars files)
- **ST.006**: Resource and data source block spacing (exactly 1 empty line)
- **ST.007**: Parameter block spacing check (within resource, data source, provider, terraform, and locals blocks)
- **ST.008**: Meta-parameter spacing check (validates spacing around meta-parameters like count, for_each, provider, lifecycle, depends_on)
- **ST.009**: Variable definition order check (definition order in `variables.tf` must match first-use order across
  sibling `*.tf` files, excluding `variables.tf`)
- **ST.010**: Resource, data source, variable, and output quote check (double quotes around names)
- **ST.011**: Trailing whitespace check (no trailing spaces or tabs at line ends)
- **ST.012**: File header and footer whitespace check (no empty lines before first non-empty line, exactly one empty
  line after last non-empty line)
- **ST.013**: Directory naming convention check (validates directory names contain only letters, numbers, and hyphens,
  and start/end with letters)
- **ST.014**: File naming convention check (validates file names contain only letters, numbers, and underscores, and
  start/end with letters)

**Implementation Pattern**:

```python
class STRules:
    def check_st001_naming_convention(self, file_path, content, log_error_func):
        # Extract resources and data sources
        # Validate naming patterns
        # Report violations
```

**Technical Features**:
- HCL syntax parsing with comment handling
- Block-level code analysis
- Parameter alignment validation
- Regular expression-based pattern matching

#### DC Rules (`rules/dc_rules.py`) - Documentation/Comments
**Purpose**: Ensure consistent documentation and comment formatting.

**Core Rules**:
- **DC.001**: Comment format standardization (spacing after #; ignore `#` inside quotes)

**Implementation Approach**:
- Line-by-line comment analysis
- Format validation with precise spacing rules
- Context-aware comment detection

#### IO Rules (`rules/io_rules.py`) - Input/Output Organization
**Purpose**: Enforce proper organization of variables, outputs, and file structure.

**Core Rules**:
- **IO.001**: Variable definition file organization
- **IO.002**: Output definition file organization
- **IO.003**: Required variable declaration check in terraform.tfvars or `*.auto.tfvars`
- **IO.004**: Variable naming convention check
- **IO.005**: Output naming convention check
- **IO.006**: Variable description validation (non-empty descriptions required)
- **IO.007**: Output description validation (non-empty descriptions required)
- **IO.008**: Variable type validation (type field required)
- **IO.009**: Variable usage check (unused definitions and undeclared `var.*` references, including inside `variables.tf`)
- **IO.010**: Variable validation block check
- **IO.013**: Provider definition file location check (`provider {}` in `providers.tf`)

**Advanced Features**:
- Cross-file dependency analysis
- Terraform.tfvars validation
- Variable reference tracking
- File organization enforcement

#### SC Rules (`rules/sc_rules.py`) - Security Code
**Purpose**: Enforce security best practices and prevent common security vulnerabilities in Terraform code.

**Core Rules**:
- **SC.001**: Array index access safety check (risky data/var/local indexes; same-line try/element/one/can)
- **SC.002**: Terraform required version declaration check (ensures providers.tf contains proper version constraints)
- **SC.003**: Terraform version compatibility check (validates version compatibility with used features)
- **SC.004**: HuaweiCloud provider version validity check (deep opt-in: `--deep` / Action `deep-check`; skipped by default)
- **SC.005**: Sensitive variable declaration check (validates that sensitive variables are properly declared with
  Sensitive=true)
- **SC.006**: Hardcoded credential literal check (credential attributes must not embed string secrets in `.tf` files)
- **SC.007**: Sensitive variable non-empty default check (sensitive-named variables must not use dangerous defaults)

**Implementation Features**:
- **Data Source Safety**: Validates safe array index access in data source list attribute references
- **Variable Safety**: Checks optional list parameter element references for safe access patterns
- **Expression Safety**: Validates for expressions in local variables and resource parameter expressions
- **try() Function Enforcement**: Ensures proper use of try() function to prevent runtime errors

**Security Scenarios Covered**:
- Data source returns empty list when no matching resources found
- Optional input variables might be empty lists
- For expressions generating dynamic lists that could be empty

**Implementation Pattern**:

```python
class SCRules:
    def check_sc001_array_index_safety(self, file_path, content, log_error_func):
        # Extract list variables from directory
        # Identify unsafe array index access patterns
        # Validate try() function usage
        # Report security violations
```

**Technical Features**:
- Cross-file list variable analysis
- Pattern matching for unsafe array access
- try() function detection and validation
- Security-focused error reporting with suggestions

### 3. GitHub Actions Integration (`action.yml`)

**Purpose**: Seamless CI/CD integration with comprehensive configuration options.

**Configuration Structure**:

```yaml
inputs:
  directory:          # Target directory specification
  ignore-rules:       # Selective rule exclusion
  include-paths:      # Precise path inclusion
  exclude-paths:      # Pattern-based path exclusion
  fail-on-error:      # Workflow failure control

outputs:
  result:            # Overall lint result
  error-count:       # Quantified error metrics
  warning-count:     # Warning statistics
  report-file:       # Generated report location
```

**Execution Pipeline**:
1. Environment setup and validation
2. Parameter processing and normalization
3. Lint execution with comprehensive logging
4. Report generation and artifact upload

### 4. Performance Optimization System

#### Intelligent Path Filtering
**Implementation**: Multi-stage filtering system that eliminates unnecessary file processing at the filesystem level.

```python
def should_exclude_path(self, file_path: str) -> bool:
    # Normalize paths for consistent comparison
    # Apply include/exclude pattern matching
    # Optimize for common directory structures
```

#### Memory Management
**Strategy**: Stream-based file processing to minimize memory footprint.
- Files processed individually rather than batch loading
- Content parsed on-demand
- Garbage collection optimization for large codebases

#### Concurrent Processing Support
**Design**: Stateless rule checking enables parallel execution.
- No shared state between file checks
- Thread-safe error collection
- Scalable architecture for large projects

### 5. Error Handling and Reporting System

#### Multi-Level Error Management

```python
def log_error(self, file_path: str, rule_id: str, message: str):
    if not self.should_ignore_rule(rule_id):
        error_msg = f"ERROR: {file_path}: [{rule_id}] {message}"
        self.errors.append(error_msg)
```

#### Comprehensive Reporting
- **Structured Output**: JSON-compatible error format
- **Performance Metrics**: Processing statistics and timing
- **Actionable Messages**: Clear guidance for issue resolution
- **Categorized Results**: Errors and warnings properly classified

### 6. Security Architecture

#### Data Protection Measures
- **Local Processing**: All analysis performed locally without external communication
- **Read-Only Operations**: No file modification capabilities
- **Minimal Permissions**: Requires only repository read access
- **Sandbox Execution**: Designed for secure CI/CD environments

#### Input Validation
- Path traversal protection
- File type validation
- Size limit enforcement
- Encoding verification

## Technical Implementation Details

### File Processing Pipeline

1. **Discovery Phase**:
   - Recursive directory traversal
   - File type filtering (.tf, .tfvars)
   - Path inclusion/exclusion application

2. **Analysis Phase**:
   - Multi-encoding content reading
   - Comment-aware parsing
   - Rule-specific validation

3. **Reporting Phase**:
   - Error aggregation and categorization
   - Performance metrics calculation
   - Report generation and output

### Rule Extension Framework

**Adding New Rules**:

```python
# 1. Define rule metadata
self.rules = {
    "XX.001": {
        "name": "Rule description",
        "description": "Detailed explanation",
        "category": "Rule category"
    }
}

# 2. Implement checking logic
def check_xx001_rule_name(self, file_path, content, log_error_func):
    # Rule implementation
    pass

# 3. Register in run_all_checks
def run_all_checks(self, file_path, content, log_error_func):
    self.check_xx001_rule_name(file_path, content, log_error_func)
```

### Configuration Management

**Parameter Processing**:
- Command-line argument parsing with argparse
- Environment variable support
- Default value management
- Validation and normalization

**Path Pattern Matching**:
- Glob pattern support with fnmatch
- Directory-aware filtering
- Cross-platform path handling
- Performance-optimized matching algorithms

## Integration Capabilities

### GitHub Actions Ecosystem
- **Workflow Integration**: Native GitHub Actions support
- **Artifact Management**: Automatic report upload
- **Status Reporting**: Proper exit codes and status messages
- **Matrix Builds**: Support for multi-environment testing

### Local Development
- **Command-Line Interface**: Full-featured CLI for local usage
- **IDE Integration**: Compatible with popular development environments
- **Pre-commit Hooks**: Easy integration with git workflows
- **Custom Scripting**: Programmatic API access

## Quality Assurance

### Testing Framework
- **Unit Tests**: Individual rule validation
- **Integration Tests**: End-to-end workflow verification
- **Performance Tests**: Large codebase handling validation
- **Compatibility Tests**: Multi-platform and version testing

### Code Quality Standards
- **Type Hints**: Comprehensive type annotation
- **Documentation**: Detailed docstrings and comments
- **Error Handling**: Robust exception management
- **Performance Monitoring**: Built-in metrics and profiling

This architecture provides a solid foundation for maintaining high-quality Terraform codebases while remaining flexible
and extensible for future requirements.
