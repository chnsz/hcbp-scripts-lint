# GitHub Actions Workflows

This directory contains example GitHub Actions workflows that demonstrate how to use the Terraform Scripts Lint Tool in
your CI/CD pipeline.

## Files

### `terraform_lint_example.yml`

This is a comprehensive example workflow that shows various ways to integrate the Terraform Scripts Lint Tool into your
GitHub Actions pipeline. It includes:

- **Basic Usage**: Simple linting with default settings
- **Advanced Configuration**: Custom path filtering and rule ignoring
- **Multi-Environment Testing**: Matrix strategy for different environments
- **Integration Examples**: How to combine with other Terraform tools
- **Performance Tips**: Optimization suggestions for large repositories

### Other workflow files

- `lint_example.yml` — additional lint workflow sample
- `cli_upgrade_tests.yml` — CLI upgrade related tests

## Reference

### [terraform_lint_example.yml](terraform_lint_example.yml)

## How to Use

1. **Copy the Example File**:

   ```bash
   cp .github/workflows/terraform_lint_example.yml .github/workflows/terraform-lint.yml
   ```

2. **Customize for Your Project**:
   - Modify the trigger conditions (`on:` section)
   - Adjust directory paths and file patterns
   - Configure rule ignoring based on your needs
   - Set appropriate failure conditions

3. **Basic Setup Example**:

   ```yaml
   name: Terraform Lint
   on: [push, pull_request]

   jobs:
     terraform-lint:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - name: Terraform Lint
           uses: chnsz/hcbp-scripts-lint@v1
           with:
             directory: './terraform'
             fail-on-error: 'true'
   ```

## Common Use Cases

### 1. Development Environment (Flexible)

```yaml
- name: Development Lint
  uses: chnsz/hcbp-scripts-lint@v1
  with:
    directory: './terraform'
    fail-on-error: 'false'
    ignore-rules: 'ST.001,ST.002'
```

### 2. Production Environment (Strict)

```yaml
- name: Production Lint
  uses: chnsz/hcbp-scripts-lint@v1
  with:
    directory: './terraform'
    fail-on-error: 'true'
```

### 3. Selective Path Filtering

```yaml
- name: Selective Lint
  uses: chnsz/hcbp-scripts-lint@v1
  with:
    directory: './terraform'
    include-paths: 'modules/**,environments/prod/**'
    exclude-paths: '**/*.md,**/test/**'
```

## Troubleshooting

If you encounter issues:

1. Check the [main documentation](../../docs/guides/troubleshooting.md)
2. Review the [GitHub Setup Guide](../../docs/github/setup.md)
3. Open an issue in the repository

## Notes

- Prefer copying `terraform_lint_example.yml` as a starting point for consumer repositories.
- Artifact naming in Action outputs uses snake_case report files such as `terraform_lint_report.txt` /
  `terraform_lint_report.json` (see Action logs/summary for the exact artifact name).
