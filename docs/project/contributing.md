# Contributing to Terraform Scripts Lint Tool

Thank you for your interest in contributing to the Terraform Scripts Lint Tool! This document provides guidelines
and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Adding New Rules](#adding-new-rules)
- [Release Process](#release-process)
- [Getting Help](#getting-help)
- [Recognition](#recognition)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please be respectful,
inclusive, and constructive in all interactions.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.6 or higher
- Git
- Basic understanding of Terraform and HCL syntax
- Familiarity with linting tools and static analysis

### Development Environment

1. **Fork the Repository**

   ```bash
   # Fork the repository on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/hcbp-scripts-lint.git
   cd hcbp-scripts-lint
   ```

2. **Set Up Development Environment**

   ```bash
   # Create a virtual environment (optional but recommended)
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install development dependencies
   pip install -r requirements-dev.txt  # If available
   ```

3. **Verify Installation**

   ```bash
   # Test the tool works correctly
   python3 .github/scripts/terraform_lint.py --help
   # Smoke-check against bundled examples
   python3 .github/scripts/terraform_lint.py --directory examples/good-examples/basic
   # Rule acceptance fixtures (preferred for validating rule behavior)
   python3 .github/scripts/terraform_lint.py --directory acceptances/good/st003/meta-compact
   ```

## Development Setup

### Project Structure

```
hcbp-scripts-lint/
├── .github/
│   ├── scripts/
│   │   └── terraform_lint.py    # Main linting script
│   └── workflows/               # GitHub Actions workflows / examples
├── rules/                       # Modular rule packages (st/io/dc/sc_rules)
├── acceptances/                 # Good/bad fixtures for rule acceptance tests
├── examples/                    # Demo / sample Terraform trees
├── docs/                        # User and contributor documentation
├── action.yml                   # GitHub Action configuration
└── README.md                    # Main documentation
```

### Key Components

- **terraform_lint.py**: Main linting engine and CLI interface
- **Rule Modules**: Individual rule implementations under `rules/*_rules/`
- **Acceptances**: Primary good/bad fixtures used to validate rule behavior (`acceptances/good|bad/<rule>/`)
- **Examples**: Broader demo trees under `examples/good-examples` and `examples/bad-examples`
- **Documentation**: Guides under `docs/` (authoritative rule prose often mirrored in `rules/*/README.md`)

## Contributing Guidelines

### Types of Contributions

We welcome several types of contributions:

1. **Bug Reports**: Report issues with existing functionality
2. **Feature Requests**: Suggest new features or improvements
3. **Code Contributions**: Implement new features or fix bugs
4. **Documentation**: Improve or expand documentation
5. **Testing**: Add test cases or improve test coverage
6. **Examples**: Provide additional examples or use cases

### Reporting Issues

When reporting bugs or requesting features:

1. **Search Existing Issues**: Check if the issue already exists
2. **Use Issue Templates**: Follow the provided templates when available
3. **Provide Details**: Include relevant information such as:
   - Operating system and version
   - Python version
   - Tool version
   - Steps to reproduce
   - Expected vs. actual behavior
   - Sample Terraform code (if applicable)

### Suggesting Features

For feature requests:

1. **Describe the Problem**: Explain what problem the feature would solve
2. **Propose a Solution**: Describe your proposed solution
3. **Consider Alternatives**: Mention alternative solutions you've considered
4. **Provide Examples**: Include examples of how the feature would be used

## Pull Request Process

### Before Submitting

1. **Create an Issue**: For significant changes, create an issue first to discuss the approach
2. **Fork and Branch**: Create a feature branch from the main branch
3. **Follow Conventions**: Use descriptive branch names (e.g., `feature/add-new-rule`, `fix/parsing-bug`)

### Submitting a Pull Request

1. **Create the Pull Request**

   ```bash
   # Push your changes to your fork
   git push origin feature/your-feature-name

   # Create a pull request on GitHub
   ```

2. **Pull Request Checklist**
   - [ ] Code follows the project's coding standards
   - [ ] Tests pass locally
   - [ ] New functionality includes appropriate tests
   - [ ] Documentation is updated if needed
   - [ ] Commit messages are clear and descriptive
   - [ ] No merge conflicts with the main branch

3. **Pull Request Description**
   - Clearly describe what the PR does
   - Reference related issues (e.g., "Fixes #123")
   - Include any breaking changes
   - Add screenshots or examples if applicable

### Review Process

1. **Automated Checks**: Ensure all CI checks pass
2. **Code Review**: Maintainers will review your code
3. **Feedback**: Address any feedback or requested changes
4. **Approval**: Once approved, maintainers will merge the PR

## Coding Standards

### Python Code Style

- **PEP 8**: Follow Python PEP 8 style guidelines
- **Line Length**: Maximum 120 characters per line
- **Indentation**: Use 4 spaces for indentation
- **Imports**: Group imports according to PEP 8 guidelines
- **Naming**: Use descriptive variable and function names

### Code Quality

- **Type Hints**: Use type hints where appropriate
- **Docstrings**: Include comprehensive docstrings for all functions and classes
- **Comments**: Add comments for complex logic or business rules
- **Error Handling**: Implement proper error handling and logging

### Example Code Style

```python
def check_rule_example(file_path: str, content: str) -> List[str]:
    """
    Check a specific rule against file content.

    Args:
        file_path: Path to the file being checked
        content: File content to analyze

    Returns:
        List of error messages found

    Raises:
        ValueError: If file_path is invalid
    """
    errors = []

    # Implementation logic here
    if not file_path:
        raise ValueError("File path cannot be empty")

    return errors
```

## Testing

### Running Tests

Rule behavior is primarily validated with acceptance fixtures under `acceptances/` (Terraform `.tf` / `.tfvars`
cases). Example ST.003-only run:

```bash
IGNORE='ST.001,ST.002,ST.004,ST.005,ST.006,ST.007,ST.008,ST.009,ST.010,ST.011,ST.012,ST.013,ST.014,DC.001,IO.001,IO.002,IO.003,IO.004,IO.005,IO.006,IO.007,IO.008,IO.009,IO.010,IO.013,SC.001,SC.002,SC.003,SC.004,SC.005,SC.006,SC.007'

# Good case: expect no [ST.003]
python3.10 .github/scripts/terraform_lint.py \
  --directory acceptances/good/st003/meta-compact \
  --ignore-rules "$IGNORE"

# Bad case: expect [ST.003] findings
python3.10 .github/scripts/terraform_lint.py \
  --directory acceptances/bad/st003/meta-padded-provider \
  --ignore-rules "$IGNORE"
```

`examples/` remains useful for demos and broader samples; prefer `acceptances/` when adding or regressing a specific
rule.

This repository does not currently ship a top-level `tests/` pytest suite. Prefer acceptance fixtures above; if you add
unit tests later, place them under `tests/` and document how to run them in the PR.

### Writing Tests

- **Fixtures first**: Add good/bad cases under `acceptances/` for rule behavior
- **Test Cases**: Include both positive and negative cases
- **Edge Cases**: Cover edge cases and error conditions
- **Documentation**: Note expected findings (rule id / line) in the fixture README when helpful

### Fixture Layout

```
acceptances/
├── good/<rule>/case-name/   # expect no findings for the rule under test
└── bad/<rule>/case-name/    # expect the target rule to report
```

Run with `--ignore-rules` set to all other rule IDs when validating a single rule.

## Documentation

### Documentation Standards

- **Clarity**: Write clear, concise documentation
- **Examples**: Include practical examples
- **Completeness**: Cover all features and edge cases
- **Maintenance**: Keep documentation up-to-date with code changes

### Types of Documentation

1. **Code Documentation**: Docstrings and inline comments
2. **User Documentation**: README, usage guides, examples
3. **Developer Documentation**: Contributing guides, architecture docs
4. **Rule Documentation**: Detailed rule descriptions and examples

### Markdown Guidelines

- **Line Length**: Maximum 120 characters per line
- **Headers**: Use consistent header hierarchy
- **Code Blocks**: Use appropriate syntax highlighting
- **Links**: Use descriptive link text

## Adding New Rules

### Rule Development Process

1. **Rule Design**: Define the rule's purpose and scope
2. **Implementation**: Implement the rule logic under `rules/<category>_rules/rule_XXX.py`
3. **Testing**: Add good/bad fixtures under `acceptances/good|bad/<rule>/` (preferred); update `examples/` only for demos
4. **Documentation**: Update `docs/rules/<category>_rules.md` (authoritative) and keep `rules/introduction.md` in sync
5. **Examples**: Provide good and bad acceptance cases that exercise the new behavior

### Rule Implementation Template

```python
def check_new_rule(file_path: str, content: str, file_lines: List[str]) -> List[str]:
    """
    Check for [rule description].

    Args:
        file_path: Path to the file being checked
        content: Complete file content
        file_lines: List of individual lines

    Returns:
        List of error messages
    """
    errors = []

    # Rule implementation logic

    return errors
```

### Rule Documentation Template

```markdown
### CATEGORY.XXX - Rule Name

**Purpose**: Brief description of what the rule checks.

**Checks**:
- Specific check 1
- Specific check 2

**Error Example**:

```hcl
# Bad example
```

**Correct Example**:

```hcl
# Good example
```

**Best Practices**:
- Best practice 1
- Best practice 2
```

## Release Process

### Version Management

- **Semantic Versioning**: Follow semantic versioning (MAJOR.MINOR.PATCH)
- **Changelog**: Update CHANGELOG.md with all changes
- **Tags**: Create git tags for releases
- **GitHub Releases**: Create GitHub releases with release notes

### Release Checklist

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Version numbers are bumped
- [ ] Release notes are prepared

## Getting Help

### Communication Channels

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Pull Request Comments**: For code-specific discussions

### Resources

- **Documentation**: Check existing documentation first
- **Examples**: Review example code and test cases
- **Code**: Read the source code for implementation details

## Recognition

We appreciate all contributions and will acknowledge contributors in:

- **CHANGELOG.md**: Major contributions noted in release notes
- **README.md**: Contributors section (if applicable)
- **GitHub**: Contributor graphs and statistics

Thank you for contributing to the Terraform Scripts Lint Tool!
