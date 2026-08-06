# Terraform Scripts Lint - Unified Rules Management System

[![GitHub Release](https://img.shields.io/github/v/release/chnsz/hcbp-scripts-lint)](https://github.com/chnsz/hcbp-scripts-lint/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-compatible-green.svg)](action.yml)

A comprehensive and enhanced linting tool for Terraform scripts that uses a **unified rules management system** to
ensure code quality, consistency, and best practices. This tool provides advanced rule coordination, detailed analytics,
and flexible configuration options for teams of all sizes.

## 🚀 Quick Start

Get up and running in 5 minutes with our comprehensive Terraform linting tool. Whether you're using GitHub Actions or
local development, we provide everything you need to ensure code quality and consistency across your Terraform projects.

**Key Features:**
- 33 Linting Rules across 4 categories (ST, IO, DC, SC)
- GitHub Actions Integration with artifact support
- Performance Monitoring and detailed reporting
- Flexible Configuration with rule filtering and path exclusion
- Comment Control to disable rules inline

📖 **[Complete Quick Start Guide](docs/guides/quickstart.md)** - Detailed setup, configuration, and usage examples

Acceptance fixtures for rule validation live under [`acceptances/`](acceptances/) (`good` / `bad` per rule). Demo trees
are under [`examples/`](examples/).

---

## 🔧 Installation & Usage

### GitHub Actions (Recommended)

Add the following step to your GitHub Actions workflow:

```yaml
- name: Lint Terraform Examples
  id: terraform-lint
  uses: chnsz/hcbp-scripts-lint@v2
  with:
    directory: 'examples'
    fail-on-error: 'true'
    exclude-paths: '*.md,*.txt,*.json,*.yml,*.yaml'
    changed-files-only: 'true'
    base-ref: ${{ github.event.pull_request.base.sha }}
    performance-monitoring: 'true'
    report-format: 'both'
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

> ⚠️ **Notes on cross-repository push**: If you push from a personal repository branch to a target repository, you may
  encounter an error that the branch does not exist. Please refer to the [Cross-repository push configuration guide](docs/project/cross_repo_push.md)
  to learn how to correctly configure the checkout step.

#### ⚙️ GitHub Actions Inputs

| Input | Description | Default | Required |
|-------|-------------|---------|----------|
| `directory` | Target directory to check | `.` | No |
| `rule-categories` | Rule categories to execute (ST,IO,DC,SC) | `ST,IO,DC,SC` | No |
| `ignore-rules` | Comma-separated list of rules to ignore | `` | No |
| `include-paths` | Path patterns to include | `` | No |
| `exclude-paths` | Path patterns to exclude | `` | No |
| `changed-files-only` | Check only changed files | `false` | No |
| `base-ref` | Base reference for git diff | `origin/main` | No |
| `performance-monitoring` | Enable performance analytics (true/false, case-insensitive) | `true` | No |
| `report-format` | Output format (text, json, or both) | `text` | No |
| `detailed-summary` | Show detailed error information in GitHub Actions summary | `true` | No |
| `fail-on-error` | Fail workflow on errors | `true` | No |

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chnsz/hcbp-scripts-lint.git
   cd hcbp-scripts-lint
   ```

2. **Run the linter:**
   ```bash
   python3 .github/scripts/terraform_lint.py --directory ./terraform
   ```

3. **Advanced usage with filtering:**
   ```bash
   python3 .github/scripts/terraform_lint.py \
     --directory ./infrastructure \
     --categories "ST,IO" \
     --ignore-rules "ST.001,ST.003" \
     --exclude-paths "examples/*,test/*" \
     --performance-monitoring
   ```

#### 🎛️ Command Line Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--directory` | Directory to lint | Current directory |
| `--ignore-rules` | Comma-separated list of rules to ignore | None |
| `--include-paths` | Comma-separated list of paths to include | All .tf files |
| `--exclude-paths` | Comma-separated list of paths to exclude | None |
| `--changed-files-only` | Check only changed files | false |
| `--base-ref` | Base reference for changed files | origin/main |
| `--rule-categories` | Comma-separated list of rule categories | ST,IO,DC,SC |
| `--report-format` | Output format (text, json, or both) | text |
| `--performance-monitoring` | Enable performance monitoring | true |
| `--fail-on-error` | Exit with error code on violations | true |

### Tool Usage

Download the tool to the local execution machine using a shell script.  
You can then run the tool using the encapsulated `hcbp-lint` command. For more information, see `hcbp-lint --help`.

```bash
curl -fsSL https://raw.githubusercontent.com/chnsz/hcbp-scripts-lint/master/tools/en-us/quick_install.sh | bash
```

#### Upgrading

After installation, pull the latest version without re-running the install script:

```bash
hcbp-lint -u
# or
hcbp-lint --upgrade
```

Requirements:
- Installed via `quick_install.sh` (git clone to `~/.local/share/terraform-linter`)
- Network access to GitHub
- Git available in PATH

> **Note:** `-u` only upgrades the tool itself and does not lint your Terraform code.
> It cannot be combined with lint options in the same command.

Preview an available upgrade without modifying the installation:

```bash
hcbp-lint -u --dry-run
```

Upgrade a specific installation path:

```bash
hcbp-lint -u --install-dir ~/.local/share/terraform-linter
```

The command options are as follows:

```bash
hcbp-lint [OPTIONS]

Options:
  -d, --directory TEXT               Target directory to check
  --categories TEXT                  Rule categories (ST,IO,DC,SC)
  --ignore-rules TEXT                Rules to ignore (comma-separated)
  --include-paths TEXT               Paths to include (comma-separated)
  --exclude-paths TEXT               Paths to exclude (comma-separated)
  --changed-files-only               Check only changed files
  --base-ref TEXT                    Base reference for git diff
  --performance-monitoring           Enable performance monitoring (true/false, case-insensitive)
  --report-format [text|json|both]   Output report format
  -u, --upgrade                      Pull latest release (git install only)
  --install-dir TEXT                 Override local installation directory (use with -u)
  --dry-run                          Preview upgrade without applying changes (requires -u)
  --help                             Show help message
```

## 📊 Enhanced Summary Reports

### GitHub Actions Summary with Detailed Error Analysis

A comprehensive linting tool for Terraform scripts with advanced rule management and comment-based control.

## Features

- **Multi-Category Rules**: 25 rules across ST (Style/Format), IO (Input/Output), DC (Documentation/Comments), and
  SC (Security Code) categories
- **Comment Control**: Enable/disable specific rules using inline comments
- **Flexible Configuration**: Path filtering, rule exclusion, and performance monitoring
- **GitHub Actions Integration**: Seamless CI/CD integration with artifact support
- **Changed Files Mode**: Optimized for large repositories with selective file checking
- **Comprehensive Reporting**: Detailed error reporting with line numbers and suggestions

## Comment Control

You can control rule execution using inline comments in your Terraform files:

```hcl
# ST.001 Disable
resource "huaweicloud_vpc_route" "vpc_route" {
  vpc_id      = huaweicloud_vpc.vpcA.id
  destination = "192.168.0.0/16"
  type        = "peering"
  nexthop     = huaweicloud_vpc_peering_connection.peering.id
}
# ST.001 Enable
```

### Supported Comment Formats

The tool supports modifying the detection behavior logic of specific rules in subsequent lines of the current file by
commenting on them (the format is **# {Rule Type}.{Rule Number} Disable/Enable**).
For example:

- `# ST.001 Disable` - Disables ST.001 rule from this line onwards in the current file
- `# ST.001 Enable` - Re-enables ST.001 rule from this line onwards in the current file

```hcl
# Disable naming convention check for this section
# ST.001 Disable
resource "huaweicloud_vpc_route" "custom_name" {
  vpc_id      = huaweicloud_vpc.vpcA.id
  destination = "192.168.0.0/16"
  type        = "peering"
  nexthop     = huaweicloud_vpc_peering_connection.peering.id
}
# ST.001 Enable

# Disable parameter alignment check for this section
# ST.003 Disable
resource "huaweicloud_compute_instance" "test" {
  name = "test-instance"
  flavor_id = "c6.large.2"
  image_id = "test-image"
  system_disk_size = 40
}
# ST.003 Enable
```

## Rule Categories

### ST (Style/Format) Rules

- **ST.001**: Resource and data source naming convention check
- **ST.002**: Variable default value requirement for data sources
- **ST.003**: Parameter alignment with equals signs
- **ST.004**: Indentation character validation (spaces only)
- **ST.005**: Indentation level validation (2 spaces per level)
- **ST.006**: Resource and data source spacing check
- **ST.007**: Parameter block spacing check (within resource, data source, provider, terraform, and locals blocks)
- **ST.008**: Meta-parameter spacing check (incl. meta → structure/dynamic blank lines)
- **ST.009**: Variable definition order validation
- **ST.010**: Quote usage consistency check
- **ST.011**: Trailing whitespace detection
- **ST.012**: File header and footer whitespace check
- **ST.013**: Directory naming convention check
- **ST.014**: File naming convention check

For more information, please refer to the [ST rules documentation](docs/rules/st_rules.md).

### IO (Input/Output) Rules

- **IO.001**: Variable definition file organization
- **IO.002**: Output definition file organization
- **IO.003**: Required variable declaration in tfvars
- **IO.004**: Variable naming convention check
- **IO.005**: Output naming convention check
- **IO.006**: Variable description requirement
- **IO.007**: Output description requirement
- **IO.008**: Variable type definition requirement
- **IO.009**: Variable usage check (unused + undeclared `var.*`, including refs in `variables.tf`)
- **IO.010**: Variable validation block check (`condition` + `error_message`)
- **IO.013**: Provider definition file location check (`provider {}` in `providers.tf`)

For more information, please refer to the [IO rules documentation](docs/rules/io_rules.md).

### DC (Documentation/Comments) Rules
- **DC.001**: Comment formatting standards (`#` + one space; ignore `#` inside quoted strings; exclude heredoc)

For more information, please refer to the [DC rules documentation](docs/rules/dc_rules.md).

### SC (Security Code) Rules
- **SC.001**: Unsafe array index access detection
- **SC.002**: Terraform required version declaration check
- **SC.003**: Terraform version compatibility check
- **SC.004**: HuaweiCloud provider version validity check
- **SC.005**: Sensitive variable declaration check
- **SC.006**: Hardcoded credential literal check
- **SC.007**: Sensitive variable non-empty default check

For more information, please refer to the [SC rules documentation](docs/rules/sc_rules.md).

## Performance

- **Large Repository Support**: Optimized for repositories with 500+ Terraform files
- **Changed Files Mode**: Reduces execution time from minutes to seconds in large codebases
- **Parallel Processing**: Efficient rule execution with intelligent scheduling
- **Memory Optimization**: Stream-based processing maintains low memory usage

## Security

- **Local Processing Only**: No network requests or data transmission
- **Read-Only Operations**: No file modifications, only analysis
- **Minimal Permissions**: Requires only read access to target files
- **No Data Collection**: Complete privacy with local-only processing

## Contributing

See [docs/project/contributing.md](docs/project/contributing.md) for development guidelines and contribution
instructions.

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

## Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/chnsz/hcbp-scripts-lint/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/chnsz/hcbp-scripts-lint/discussions)
- 📖 **Documentation**: [Complete Documentation](docs/README.md)
- 🚀 **Quick Start**: [docs/guides/quickstart.md](docs/guides/quickstart.md)
