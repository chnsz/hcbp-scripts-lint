#!/usr/bin/env python3
"""
ST.003 - Parameter Alignment Check

This module implements the ST.003 rule which validates that parameter assignments
in resource and data blocks have proper spacing around equals signs and maintain
consistent alignment within code blocks.

Rule Specification:
- Equals signs must be aligned within the same code block
- Aligned equals signs should maintain one space from the longest parameter name in the code block
- Exactly one space after the equals sign and parameter value

Alignment Calculation Formula:
- Expected equals location = indent_spaces + param_name_length + quote_chars + 1
- Where:
  - indent_spaces = indent_level * 2 (Terraform uses 2 spaces per indent level)
  - param_name_length = length of parameter name without quotes
  - quote_chars = 2 if parameter name is quoted, 0 otherwise
  - 1 = standard space before equals sign

Code Block Sectioning Rules:
- Sections are split on empty lines
- Comment lines are ignored for sectioning (do not split sections)
- Object boundaries ({ and }) create new sections
- Parameters within the same section must align with each other

Special Cases:
- Lines containing tab characters or odd indentation are skipped and do not set the equals baseline
- Supports resource, data, ephemeral, module, provider, locals, terraform, variable, output,
  import, moved, and check blocks (including single-line blocks with content inside `{}`)
- In resource/data/module/ephemeral blocks, meta-parameters (count, for_each, provider, depends_on, lifecycle)
  are excluded from column-alignment calculations, but still require exactly one space before '='
- Attributes named count in variables/locals/object types are not treated as meta-parameters
- for_each inside dynamic blocks (including same-line `dynamic "x" { for_each = ... }`) is treated as a
  normal parameter; after a closed dynamic block, top-level for_each is again a meta-parameter
- Same-line multi-assignment uses spacing checks only (no column alignment)
- Quote-aware alignment uses max(len(name) + quote_chars) per parameter
- Nested objects maintain their own alignment groups
- Sibling `param = {` declarations stay in the current section; nested fields form new sections
- .tfvars may keep consistent extra padding when a majority already share an equals column; single-parameter
  groups still require exactly one space before '='

Examples:
    Valid declarations:
        data "huaweicloud_compute_flavors" "test" {
          performance_type = "normal"
          cpu_core_count   = 4
          memory_size      = 8
        }

        resource "huaweicloud_compute_instance" "test" {
          name               = "tf_test_instance"
          flavor_id          = try(data.huaweicloud_compute_flavors.test.flavors[0].id, "c6.2xlarge.4")
          security_group_ids = [huaweicloud_networking_secgroup.test.id]
          # ...
        }

    Invalid declarations:
        data "huaweicloud_compute_flavors" "test" {
          performance_type="normal"    # No spaces around equals
          cpu_core_count= 4            # No space before equals
          memory_size =8               # No space after equals
        }

        resource "huaweicloud_compute_instance" "test" {
          # Parameter equal signs are not aligned or not properly spaced
          name = "tf_test_instance"
          flavor_id = try(data.huaweicloud_compute_flavors.test.flavors[0].id, "c6.2xlarge.4")
          security_group_ids = [huaweicloud_networking_secgroup.test.id]
          # ...
        }

Author: Lance
License: Apache 2.0
"""

import re
import sys
from typing import Callable, List, Tuple, Optional, Dict


def check_st003_parameter_alignment(file_path: str, content: str, log_error_func: Callable[[str, str, str, Optional[int]], None]) -> None:
    """
    Validate parameter alignment in data sources and resource blocks according to ST.003 rule specifications.

    This function scans through the provided Terraform file content and validates
    that parameter assignments within data source and resource blocks are properly
    aligned. This ensures consistent code formatting and improves readability
    across the entire codebase.

    The validation process:
    1. Remove comments from content for accurate parsing
    2. Extract all data source and resource blocks
    3. Split each block into sections separated by blank lines
    4. Check parameter alignment within each section
    5. Report violations through the error logging function

    Args:
        file_path (str): The path to the file being checked. Used for error reporting
                        to help developers identify the location of violations.

        content (str): The complete content of the Terraform file as a string.
                      This includes all data source and resource blocks.

        log_error_func (Callable[[str, str, str, Optional[int]], None]): A callback function used
                      to report rule violations. The function should accept four
                      parameters: file_path, rule_id, error_message, and line_number.
                      The line_number parameter is optional and can be None.

    Returns:
        None: This function doesn't return a value but reports errors through
              the log_error_func callback.

    Raises:
        No exceptions are raised by this function. All errors are handled
        gracefully and reported through the logging mechanism.
    """
    clean_content = _remove_comments_for_parsing(content)
    
    # Check if this is a terraform.tfvars file
    if file_path.endswith('.tfvars'):
        _check_tfvars_parameter_alignment(file_path, clean_content, log_error_func)
    else:
        blocks = _extract_code_blocks(clean_content)
        all_errors = []

        for block_type, start_line, block_lines in blocks:
            sections = _split_into_code_sections(block_lines)
            
            
            # Check alignment and spacing within each individual section
            for section in sections:
                errors = _check_parameter_alignment_in_section(section, block_type, start_line, block_lines)
                all_errors.extend(errors)
        
        # Sort errors by line number
        all_errors.sort(key=lambda x: x[0])
        
        # Deduplicate errors (same line number and error message)
        seen = set()
        unique_errors = []
        for line_num, error_msg in all_errors:
            key = (line_num, error_msg)
            if key not in seen:
                seen.add(key)
                unique_errors.append((line_num, error_msg))
        
        # Report sorted and deduplicated errors
        for line_num, error_msg in unique_errors:
            log_error_func(file_path, "ST.003", error_msg, line_num)


def _remove_comments_for_parsing(content: str) -> str:
    """
    Remove comments from content for parsing, but preserve line structure.

    Args:
        content (str): The original file content

    Returns:
        str: Content with comments removed
    """
    lines = content.split('\n')
    cleaned_lines = []

    for line in lines:
        if '#' in line:
            in_quotes = False
            quote_char = None
            for i, char in enumerate(line):
                if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = None
                elif char == '#' and not in_quotes:
                    # If the line is only a comment (after stripping), keep the original line
                    # to preserve line structure
                    stripped_before_comment = line[:i].strip()
                    if not stripped_before_comment:
                        line = line  # Keep original line (comment line)
                    else:
                        line = line[:i].rstrip()  # Remove comment but keep content
                    break
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def _extract_code_blocks(content: str) -> List[Tuple[str, int, List[str]]]:
    """
    Extract Terraform code blocks that contain parameter assignments.

    Supported blocks: data, resource, ephemeral, module, provider, locals, terraform,
    variable, output, import, moved, and check.

    Args:
        content (str): The cleaned Terraform content

    Returns:
        List[Tuple[str, int, List[str]]]: List of (block_type, start_line, block_lines)
    """
    lines = content.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Support quoted, single-quoted, and unquoted syntax
        data_match = re.match(r'data\s+(?:"([^"]+)"|\'([^\']+)\'|([a-zA-Z_][a-zA-Z0-9_]*))\s+(?:"([^"]+)"|\'([^\']+)\'|([a-zA-Z_][a-zA-Z0-9_]*))\s*\{', line)
        resource_match = re.match(r'resource\s+(?:"([^"]+)"|\'([^\']+)\'|([a-zA-Z_][a-zA-Z0-9_]*))\s+(?:"([^"]+)"|\'([^\']+)\'|([a-zA-Z_][a-zA-Z0-9_]*))\s*\{', line)
        ephemeral_match = re.match(r'ephemeral\s+(?:"([^"]+)"|\'([^\']+)\'|([a-zA-Z_][a-zA-Z0-9_]*))\s+(?:"([^"]+)"|\'([^\']+)\'|([a-zA-Z_][a-zA-Z0-9_]*))\s*\{', line)
        module_match = re.match(r'module\s+(?:"([^"]+)"|\'([^\']+)\'|([a-zA-Z_][a-zA-Z0-9_]*))\s*\{', line)
        provider_match = re.match(r'provider\s+(?:"([^"]+)"|\'([^\']+)\'|([a-zA-Z_][a-zA-Z0-9_]*))\s*\{', line)
        locals_match = re.match(r'locals\s*\{', line)
        terraform_match = re.match(r'terraform\s*\{', line)
        variable_match = re.match(r'variable\s+(?:"([^"]+)"|\'([^\']+)\'|([a-zA-Z_][a-zA-Z0-9_]*))\s*\{', line)
        output_match = re.match(r'output\s+(?:"([^"]+)"|\'([^\']+)\'|([a-zA-Z_][a-zA-Z0-9_]*))\s*\{', line)
        check_match = re.match(r'check\s+(?:"([^"]+)"|\'([^\']+)\'|([a-zA-Z_][a-zA-Z0-9_]*))\s*\{', line)
        import_match = re.match(r'import\s*\{', line)
        moved_match = re.match(r'moved\s*\{', line)

        if (data_match or resource_match or ephemeral_match or module_match or provider_match
                or locals_match or terraform_match or variable_match or output_match
                or check_match or import_match or moved_match):
            if data_match:
                data_type = data_match.group(1) if data_match.group(1) else (data_match.group(2) if data_match.group(2) else data_match.group(3))
                data_name = data_match.group(4) if data_match.group(4) else (data_match.group(5) if data_match.group(5) else data_match.group(6))
                block_type = f"data.{data_type}.{data_name}"
            elif resource_match:
                resource_type = resource_match.group(1) if resource_match.group(1) else (resource_match.group(2) if resource_match.group(2) else resource_match.group(3))
                resource_name = resource_match.group(4) if resource_match.group(4) else (resource_match.group(5) if resource_match.group(5) else resource_match.group(6))
                block_type = f"resource.{resource_type}.{resource_name}"
            elif ephemeral_match:
                ephemeral_type = ephemeral_match.group(1) if ephemeral_match.group(1) else (ephemeral_match.group(2) if ephemeral_match.group(2) else ephemeral_match.group(3))
                ephemeral_name = ephemeral_match.group(4) if ephemeral_match.group(4) else (ephemeral_match.group(5) if ephemeral_match.group(5) else ephemeral_match.group(6))
                block_type = f"ephemeral.{ephemeral_type}.{ephemeral_name}"
            elif module_match:
                module_name = module_match.group(1) if module_match.group(1) else (module_match.group(2) if module_match.group(2) else module_match.group(3))
                block_type = f"module.{module_name}"
            elif provider_match:
                provider_type = provider_match.group(1) if provider_match.group(1) else (provider_match.group(2) if provider_match.group(2) else provider_match.group(3))
                block_type = f"provider.{provider_type}"
            elif locals_match:
                block_type = "locals"
            elif terraform_match:
                block_type = "terraform"
            elif variable_match:
                variable_name = variable_match.group(1) if variable_match.group(1) else (variable_match.group(2) if variable_match.group(2) else variable_match.group(3))
                block_type = f"variable.{variable_name}"
            elif output_match:
                output_name = output_match.group(1) if output_match.group(1) else (output_match.group(2) if output_match.group(2) else output_match.group(3))
                block_type = f"output.{output_name}"
            elif check_match:
                check_name = check_match.group(1) if check_match.group(1) else (check_match.group(2) if check_match.group(2) else check_match.group(3))
                block_type = f"check.{check_name}"
            elif import_match:
                block_type = "import"
            else:  # moved_match
                block_type = "moved"

            block_lines = []
            # start_line is chosen so actual_line = start_line + relative_idx + 1
            # Multi-line: content starts on the line after the declaration.
            # Single-line: content lives on the declaration line itself.
            start_line = i + 1
            brace_count = 1
            i += 1

            # Opening and closing brace on the declaration line
            if '{' in line and '}' in line:
                first_brace = line.find('{')
                last_brace = line.rfind('}')
                if first_brace != -1 and last_brace > first_brace:
                    inner = line[first_brace + 1:last_brace].strip()
                    if inner:
                        # Strip so synthetic content is not treated as odd-indent (ST.005 skip).
                        block_lines = [inner]
                        # Content is on the declaration line (1-based i was already advanced).
                        start_line = i - 1  # 0-based index of declaration => actual = start_line + 0 + 1
            else:
                # Multi-line block, process until we find the closing brace
                while i < len(lines) and brace_count > 0:
                    current_line = lines[i]
                    block_lines.append(current_line)
                    for char in current_line:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                    i += 1

                # Remove the last line if it contains only the closing brace
                if block_lines and block_lines[-1].strip() == '}':
                    block_lines = block_lines[:-1]

            blocks.append((block_type, start_line, block_lines))
        else:
            i += 1

    return blocks


def _split_into_code_sections(block_lines: List[str]) -> List[List[Tuple[str, int]]]:
    """
    Split code block by empty lines and object boundaries into multiple sections.
    
    Note: block_lines is stored in the function closure for use in post-processing.
    """
    # Store block_lines for use in post-processing merge logic
    _split_into_code_sections._block_lines = block_lines
    """
    Split code block by empty lines and object boundaries into multiple sections.

    Args:
        block_lines (List[str]): Lines within a code block

    Returns:
        List[List[Tuple[str, int]]]: Sections with (line_content, line_index) tuples
    """
    sections = []
    current_section = []
    # Stack to track sections when entering object({ internal parameters
    # When we enter object({ internal params, we push current_section to stack
    # When we exit with }), we pop and continue with the previous section
    section_stack = []
    brace_level = 0
    bracket_level = 0
    prev_brace_level = 0
    prev_bracket_level = 0
    
    # Track heredoc state to skip content inside heredoc blocks
    in_heredoc = False
    heredoc_terminator = None

    for line_idx, line in enumerate(block_lines):
        prev_brace_level = brace_level
        prev_bracket_level = bracket_level
        stripped_line = line.strip()
        
        # Check for heredoc end pattern first (before checking start)
        # The terminator must be at the beginning of the line (after stripping)
        if in_heredoc and heredoc_terminator:
            if stripped_line == heredoc_terminator:
                in_heredoc = False
                heredoc_terminator = None
                # Continue to process the terminator line if it contains '=' or boundary markers
        
        # Skip lines inside heredoc blocks (but not the heredoc start line itself)
        if in_heredoc:
            continue
        
        # Check for heredoc start pattern (<<EOF, <<-EOF, etc.)
        # Match <<EOF or <<-EOF at the end of a line
        heredoc_terminator_match = _match_heredoc_start(line)
        if heredoc_terminator_match:
            in_heredoc = True
            heredoc_terminator = heredoc_terminator_match
            # Continue to process the heredoc start line if it contains '=' or boundary markers
        
        if stripped_line == '':
            # Empty line always splits sections, regardless of brace/bracket level
            if current_section:
                sections.append(current_section)
                current_section = []
            continue
        elif stripped_line.startswith('#'):
            # Skip comment lines but don't split sections
            continue
        else:
            # Check if braces/brackets are balanced on the same line (e.g., {for ...}, [for ...] expressions)
            # This check should be done before tracking brace/bracket levels to avoid false positives
            open_braces = line.count('{')
            close_braces = line.count('}')
            open_brackets = line.count('[')
            close_brackets = line.count(']')
            braces_balanced_on_line = (open_braces == close_braces and open_braces > 0)
            brackets_balanced_on_line = (open_brackets == close_brackets and open_brackets > 0)
            
            # Track brace and bracket levels before processing
            # Only increment level when left brackets/braces exceed right brackets/braces on the same line
            # This excludes cases where brackets/braces are balanced on the same line (e.g., {for ...}, [for ...])
            # Note: parentheses are ignored for level tracking
            net_brace_change = open_braces - close_braces
            net_bracket_change = open_brackets - close_brackets
            
            # Only change level when there's a net change (unmatched brackets/braces)
            # This ensures that balanced brackets/braces on the same line don't affect level
            if net_brace_change > 0:
                # More opening braces than closing braces - increment level
                brace_level += net_brace_change
            elif net_brace_change < 0:
                # More closing braces than opening braces - decrement level
                brace_level = max(0, brace_level + net_brace_change)  # Ensure level doesn't go negative
            
            if net_bracket_change > 0:
                # More opening brackets than closing brackets - increment level
                bracket_level += net_bracket_change
            elif net_bracket_change < 0:
                # More closing brackets than opening brackets - decrement level
                bracket_level = max(0, bracket_level + net_bracket_change)  # Ensure level doesn't go negative
            
            # Check if we're entering an object within a list (list(object({ form))
            # This happens in structures like: cache_http_status_and_ttl = list(object({
            # When we encounter a line that contains list(object({, we should start a new section
            # for the parameters inside the object (which will be on subsequent lines)
            # This check must come BEFORE the simple object({ check to handle list(object({ correctly
            if 'list(' in stripped_line and 'object(' in stripped_line and stripped_line.endswith('{'):
                # This is a list(object({ declaration line
                # Add it to current section, then start a new section for nested parameters
                # Create a copy of current_section to push to stack (since we'll append it to sections)
                # This ensures we can return to it after })) and add subsequent parameters to it
                current_section.append((line, line_idx))
                # Don't append to sections yet - we'll do that when we exit the nested structure
                # Instead, push a copy of current_section so we can continue adding to it after }))
                # Use list() to create a copy, not a reference
                section_stack.append(list(current_section))  # Remember the section with list(object({ declaration
                current_section = []
                continue
            
            # Check if we're entering an object (parameter = { form)
            # When encountering '{', we should NOT create new grouping for "param = {" declaration
            # because "param = {" should align with other parameters at the same level
            # Only "param = {" internal parameters should create new grouping
            # Note: "param = object({" also should align with other parameters at the same level
            # Also skip if braces are balanced on the same line (e.g., {for ...} expressions)
            if brace_level >= 1 and stripped_line.endswith('{') and not braces_balanced_on_line:
                # Check if this is a simple "parameter = {" form (not "parameter = object({")
                if _has_assignment_equals(stripped_line):
                    after_equals = _get_after_assignment_equals(stripped_line)
                    # Don't create new grouping for "param = {" declaration
                    # It should stay in the same group to align with other params at the same level
                    # Internal parameters will create new grouping when encountered
                    if after_equals == '{':
                        # "param = {" declaration - check if we need to split section by indent level
                        # If current_section has parameters with different indent levels, we should split
                        # However, don't split if we're inside a function call (e.g., jsonencode({...}))
                        # Check if any ancestor line contains a function call ending with {
                        current_indent = len(line) - len(line.lstrip())
                        is_inside_function_call = False
                        
                        # Search backwards through block_lines to find if we're inside a function call
                        # Look for a line with lower indent that has a function call
                        search_idx = line_idx - 1
                        while search_idx >= 0:
                            search_line = block_lines[search_idx]
                            search_stripped = search_line.strip()
                            if search_stripped == '' or search_stripped.startswith('#'):
                                search_idx -= 1
                                continue
                            search_indent = len(search_line) - len(search_line.lstrip())
                            # If we find a line with lower indent, check if it's a function call
                            if search_indent < current_indent:
                                if _has_assignment_equals(search_line):
                                    search_after_equals = _get_after_assignment_equals(search_line)
                                    # Match common Terraform functions that can contain objects/arrays
                                    function_patterns = ['jsonencode(', 'merge(', 'try(', 'lookup(', 'alltrue(', 'anytrue(', 
                                                         'cidrsubnet(', 'cidrhost(', 'flatten(', 'keys(', 'values(', 'zipmap(']
                                    if search_after_equals and any(search_after_equals.startswith(pattern) for pattern in function_patterns):
                                        if '{' in search_after_equals or '[' in search_after_equals:
                                            is_inside_function_call = True
                                            break
                                # If we find a parameter at lower indent, stop searching
                                break
                            search_idx -= 1
                        
                        # Also check current_section for function calls
                        if not is_inside_function_call and current_section:
                            # Check if the last line in current_section contains a function call ending with {
                            # We need to check all previous lines in the section, not just the last one
                            for prev_line, _ in reversed(current_section):
                                if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                    # Check if this is a function call like jsonencode({, merge({, etc.
                                    prev_after_equals = _get_after_assignment_equals(prev_line)
                                    # Match common Terraform functions that can contain objects/arrays
                                    function_patterns = ['jsonencode(', 'merge(', 'try(', 'lookup(', 'alltrue(', 'anytrue(', 
                                                         'cidrsubnet(', 'cidrhost(', 'flatten(', 'keys(', 'values(', 'zipmap(']
                                    if prev_after_equals and any(prev_after_equals.startswith(pattern) for pattern in function_patterns):
                                        if '{' in prev_after_equals or '[' in prev_after_equals:
                                            is_inside_function_call = True
                                            break
                                    # If we find a parameter at the same indent level, we're not inside a function call
                                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                                    if prev_indent == current_indent:
                                        break
                        
                        if not is_inside_function_call:
                            if current_section:
                                # Check if there are parameters with different indent levels in current_section
                                has_different_indent = False
                                for prev_line, _ in current_section:
                                    if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                        prev_indent = len(prev_line) - len(prev_line.lstrip())
                                        if prev_indent != current_indent:
                                            has_different_indent = True
                                            break
                                
                                if has_different_indent:
                                    # Split section: keep parameters with same indent as current line
                                    # Parameters with different indent should go to previous section
                                    same_indent_section = []
                                    different_indent_section = []
                                    for prev_line, prev_idx in current_section:
                                        if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                            prev_indent = len(prev_line) - len(prev_line.lstrip())
                                            if prev_indent == current_indent:
                                                same_indent_section.append((prev_line, prev_idx))
                                            else:
                                                different_indent_section.append((prev_line, prev_idx))
                                        else:
                                            # Non-parameter lines (comments, etc.) - keep with same indent section
                                            same_indent_section.append((prev_line, prev_idx))
                                    
                                    if different_indent_section:
                                        # Add different indent parameters to previous section
                                        sections.append(different_indent_section)
                                    # Continue with same indent section
                                    current_section = same_indent_section
                        # "param = {" declaration will be added to current section below
                        # If we're inside a function call, check if we should split section
                        # For function calls like jsonencode({...}), parameters inside should be in the same section
                        # if they have the same indent level, but should be split if they have different indent levels
                        elif is_inside_function_call:
                            # Inside function call, check if we should split section based on indent
                            if current_section:
                                # Check if there are parameters with different indent levels in current_section
                                has_different_indent = False
                                for prev_line, _ in current_section:
                                    if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                        prev_indent = len(prev_line) - len(prev_line.lstrip())
                                        if prev_indent != current_indent:
                                            has_different_indent = True
                                            break
                                
                                if has_different_indent:
                                    # Split section: keep parameters with same indent as current line
                                    # Parameters with different indent should go to previous section
                                    same_indent_section = []
                                    different_indent_section = []
                                    for prev_line, prev_idx in current_section:
                                        if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                            prev_indent = len(prev_line) - len(prev_line.lstrip())
                                            if prev_indent == current_indent:
                                                same_indent_section.append((prev_line, prev_idx))
                                            else:
                                                different_indent_section.append((prev_line, prev_idx))
                                        else:
                                            # Non-parameter lines (comments, etc.) - keep with same indent section
                                            same_indent_section.append((prev_line, prev_idx))
                                    
                                    if different_indent_section:
                                        # Add different indent parameters to previous section
                                        sections.append(different_indent_section)
                                    # Continue with same indent section
                                    current_section = same_indent_section
                            else:
                                # current_section is empty, but we're inside a function call
                                # Check if the previous line was an empty line (which splits sections)
                                # If so, we should NOT merge with previous section, even if we're in a function call
                                # Empty lines should always create new sections
                                prev_line_was_empty = False
                                if line_idx > 0:
                                    prev_line = block_lines[line_idx - 1]
                                    if prev_line.strip() == '':
                                        prev_line_was_empty = True
                                
                                # Only merge if previous line was NOT empty
                                # Empty lines should always split sections, even in function calls
                                if not prev_line_was_empty and sections:
                                    # Look for the last section that has parameters at the same indent level
                                    # We need to check all sections, not just the last one, because
                                    # sections might have been split due to closing braces
                                    found_section_to_merge = False
                                    for sec_idx in range(len(sections) - 1, -1, -1):
                                        prev_section = sections[sec_idx]
                                        # Check if this section has parameters at the same indent level
                                        for prev_line, prev_idx in prev_section:
                                            if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                                prev_indent = len(prev_line) - len(prev_line.lstrip())
                                                if prev_indent == current_indent:
                                                    # Found a section with parameters at the same indent level
                                                    # Merge current line into that section
                                                    found_section_to_merge = True
                                                    sections.pop(sec_idx)
                                                    current_section = prev_section
                                                    break
                                        if found_section_to_merge:
                                            break
                                # If no section with same indent was found, or previous line was empty,
                                # start a new current_section
                                # This ensures that parameters separated by empty lines are in different sections
                                # even if they're at the same indent level within a function call
            
            # Check if we're entering an array (parameter = [ form)
            # When encountering '[', we should NOT create new grouping for "param = [" declaration
            # because "param = [" should align with other parameters at the same level
            # Only "param = [" internal elements should create new grouping
            # This is similar to "param = {" handling above
            # Also skip if brackets are balanced on the same line (e.g., [for ...] expressions)
            if bracket_level == 1 and stripped_line.endswith('[') and not brackets_balanced_on_line:
                # Check if this is a simple "parameter = [" form
                if _has_assignment_equals(stripped_line):
                    after_equals = _get_after_assignment_equals(stripped_line)
                    if after_equals == '[':
                        # "param = [" declaration - check if we need to split section by indent level
                        # If current_section has parameters with different indent levels, we should split
                        current_indent = len(line) - len(line.lstrip())
                        # Check if we're inside a function call (e.g., jsonencode({...}))
                        is_inside_function_call = False
                        search_idx = line_idx - 1
                        while search_idx >= 0:
                            search_line = block_lines[search_idx]
                            search_stripped = search_line.strip()
                            if search_stripped == '' or search_stripped.startswith('#'):
                                search_idx -= 1
                                continue
                            search_indent = len(search_line) - len(search_line.lstrip())
                            if _has_assignment_equals(search_line):
                                search_after_equals = _get_after_assignment_equals(search_line)
                                function_patterns = ['jsonencode(', 'merge(', 'try(', 'lookup(', 'alltrue(', 'anytrue(', 
                                                     'cidrsubnet(', 'cidrhost(', 'flatten(', 'keys(', 'values(', 'zipmap(']
                                if search_after_equals and any(search_after_equals.startswith(pattern) for pattern in function_patterns):
                                    if '{' in search_after_equals or '[' in search_after_equals:
                                        is_inside_function_call = True
                                        break
                            if search_indent < current_indent:
                                break
                            search_idx -= 1
                        
                        if current_section:
                            # Check if there are parameters with different indent levels in current_section
                            has_different_indent = False
                            for prev_line, _ in current_section:
                                if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                                    if prev_indent != current_indent:
                                        has_different_indent = True
                                        break
                            
                            if has_different_indent:
                                # Check if we just exited a top-level array and this is a top-level param
                                # If so, keep them in the same section for alignment
                                # This handles cases like: flattened_data_volumes = [...] followed by default_data_volumes_configuration_with_virtual_spaces = [...]
                                should_keep_together = False
                                if current_indent == 2:
                                    # Check if the previous line was closing a top-level array
                                    # Look for closing bracket/brace patterns in the previous line
                                    if line_idx > 0:
                                        prev_line_content = block_lines[line_idx - 1]
                                        prev_line_stripped = prev_line_content.strip()
                                        # Check if previous line closes an array (contains ']' or '])')
                                        # Accept patterns like ']', '])', '])', etc.
                                        if ']' in prev_line_stripped:
                                            # Check if current_section has top-level params at the same indent
                                            has_top_level_in_section = False
                                            for prev_line, _ in current_section:
                                                if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                                                    if prev_indent == current_indent:
                                                        has_top_level_in_section = True
                                                        break
                                            if has_top_level_in_section:
                                                should_keep_together = True
                                
                                if not should_keep_together:
                                    # Split section: keep parameters with same indent as current line
                                    # Parameters with different indent should go to previous section
                                    same_indent_section = []
                                    different_indent_section = []
                                    for prev_line, prev_idx in current_section:
                                        if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                            prev_indent = len(prev_line) - len(prev_line.lstrip())
                                            if prev_indent == current_indent:
                                                same_indent_section.append((prev_line, prev_idx))
                                            else:
                                                different_indent_section.append((prev_line, prev_idx))
                                        else:
                                            # Non-parameter lines (comments, etc.) - keep with same indent section
                                            same_indent_section.append((prev_line, prev_idx))
                                    
                                    if different_indent_section:
                                        # Add different indent parameters to previous section
                                        sections.append(different_indent_section)
                                    # Continue with same indent section
                                    current_section = same_indent_section
                                # If should_keep_together is True, don't split - keep current_section as is
                        elif is_inside_function_call:
                            # current_section is empty, but we're inside a function call
                            # Check if there's a previous section with parameters at the same indent level
                            # If so, we should merge with that section instead of creating a new one
                            if sections:
                                # Look for the last section that has parameters at the same indent level
                                # We need to check all sections, not just the last one, because
                                # sections might have been split due to closing braces
                                found_section_to_merge = False
                                for sec_idx in range(len(sections) - 1, -1, -1):
                                    prev_section = sections[sec_idx]
                                    # Check if this section has parameters at the same indent level
                                    for prev_line, prev_idx in prev_section:
                                        if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                            prev_indent = len(prev_line) - len(prev_line.lstrip())
                                            if prev_indent == current_indent:
                                                # Found a section with parameters at the same indent level
                                                # Merge current line into that section
                                                found_section_to_merge = True
                                                sections.pop(sec_idx)
                                                current_section = prev_section
                                                break
                                    if found_section_to_merge:
                                        break
                        # "param = [" declaration will be added to current section below
                        # Don't create new section - it should align with other params at the same level
            
            # Check if we're in an array and encountering a standalone '{' (new object element)
            # This happens in structures like: default = [ { ... }, { ... } ]
            # However, if we're still inside an object (brace_level > 0), we should NOT clear current_section
            # because the array declaration and subsequent parameters should align with each other
            # Also skip if braces/brackets are balanced on the same line (e.g., {for ...}, [for ...] expressions)
            # Also skip if we're inside a function call (e.g., jsonencode({...}))
            is_inside_function_call_for_array = False
            if line_idx > 0:
                prev_line_in_block = block_lines[line_idx - 1]
                if _has_assignment_equals(prev_line_in_block) and not prev_line_in_block.strip().startswith('#'):
                    prev_after_equals = _get_after_assignment_equals(prev_line_in_block)
                    function_patterns = ['jsonencode(', 'merge(', 'try(', 'lookup(', 'alltrue(', 'anytrue(', 
                                         'cidrsubnet(', 'cidrhost(', 'flatten(', 'keys(', 'values(', 'zipmap(']
                    if prev_after_equals and any(prev_after_equals.startswith(pattern) for pattern in function_patterns):
                        if '{' in prev_after_equals or '[' in prev_after_equals:
                            is_inside_function_call_for_array = True
            
            if bracket_level >= 1 and stripped_line == '{' and '=' not in stripped_line and not braces_balanced_on_line and not is_inside_function_call_for_array:
                # Starting a new object within an array
                # Only clear current_section if we're at the top level (brace_level == 0)
                # If we're still inside an object, keep current_section so subsequent parameters can align
                if brace_level == 0:
                    # Top-level array with object elements
                    if current_section:
                        sections.append(current_section)
                        current_section = []
                # If brace_level > 0, we're still inside an object, so don't clear current_section
                # The object element will be added to current_section below
            
            # Check if we're entering parameters inside object({, list(object({, or simple param = {
            # When we encounter a parameter line inside these structures, we need to ensure it's in a new section
            # But only if the previous line was the declaration, not if it's another parameter at the same level
            # Also skip if the braces/brackets are balanced on the same line (e.g., {for ...}, [for ...] expressions)
            # If braces/brackets are balanced on the same line, skip this check entirely
            if (brace_level >= 1 and _has_assignment_equals(stripped_line) and not stripped_line.endswith('{') and not stripped_line.endswith('[') and 
                not braces_balanced_on_line and not brackets_balanced_on_line):
                # We're inside an object, and this is a parameter line
                # Check if the previous line in current_section contains "object(", "list(object(", or ends with "= {"
                if current_section:
                        last_line_content = current_section[-1][0] if current_section else ""
                        # Check if the last line contains object({ pattern (but not list(object({ which is handled separately)
                        if 'object(' in last_line_content and '{' in last_line_content:
                            # Check if it's list(object({ (already handled above) or simple object({
                            if not ('list(' in last_line_content):
                                # The previous line was object({ declaration
                                # Check if this parameter has more indentation (is actually inside the object)
                                current_indent = len(line) - len(line.lstrip())
                                last_indent = len(last_line_content) - len(last_line_content.lstrip())
                                if current_indent > last_indent:
                                    # This parameter is inside the object
                                    # We need to create a new section for object({ internal params
                                    # But we should keep the object({ declaration in the previous section
                                    # so it can align with other parameters at the same level
                                    # Push current_section to stack so we can return to it after })
                                    sections.append(current_section)
                                    section_stack.append(current_section)  # Remember the section with object({ declaration
                                    current_section = []
                            elif bracket_level >= 1:
                                # The previous line was list(object({ declaration (nested)
                                # Check if this is a nested list(object({ inside another list(object({
                                # If so, we need to handle it similarly to the top-level list(object({
                                # by pushing current_section to stack instead of adding to sections
                                if 'list(' in last_line_content and 'object(' in last_line_content:
                                    # This is a nested list(object({ declaration
                                    # Push a copy of current_section to stack so we can return to it after }))
                                    current_section.append((line, line_idx))
                                    section_stack.append(list(current_section))
                                    current_section = []
                                    continue
                                else:
                                    # The previous line was list(object({ declaration, but this is not a nested list(object({
                                    # This means we're entering parameters inside the outer list(object({
                                    # We should NOT push current_section to stack here because it's already in the stack
                                    # from when we encountered the outer list(object({ declaration
                                    # Just continue, the parameter will be added to current_section below
                                    pass
                        # Check if the last line is a simple "param = {" declaration
                        # OR if the last line ends with '{' (could be "param = {", "param = flatten([...])", etc.)
                        elif _has_assignment_equals(last_line_content) and last_line_content.endswith('{'):
                            after_equals_last = _get_after_assignment_equals(last_line_content)
                            if after_equals_last == '{':
                                # The previous line was "param = {" declaration
                                # Check if this parameter has more indentation (is actually inside the object)
                                current_indent = len(line) - len(line.lstrip())
                                last_indent = len(last_line_content) - len(last_line_content.lstrip())
                                if current_indent > last_indent:
                                    # This parameter is inside the "param = {" object
                                    # Create a new section for internal params
                                    # Push current_section to stack so we can return to it after })
                                    sections.append(current_section)
                                    section_stack.append(current_section)  # Remember the section with "param = {" declaration
                                    current_section = []
                            else:
                                # The previous line ends with '{' but is not "param = {" (e.g., "param = flatten([...])")
                                # Check if this parameter has more indentation (is actually inside the object/expression)
                                current_indent = len(line) - len(line.lstrip())
                                last_indent = len(last_line_content) - len(last_line_content.lstrip())
                                if current_indent > last_indent:
                                    # This parameter is inside the object/expression
                                    # Create a new section for internal params
                                    # Push current_section to stack so we can return to it after })
                                    sections.append(current_section)
                                    section_stack.append(current_section)  # Remember the section with the declaration
                                    current_section = []
            
            # Check if we're exiting an object
            # When we encounter }), })), }, etc., we need to check if we should return to previous section
            # This happens when we were in object({ internal params and now exiting with })
            # Check if line starts with } or contains }) pattern (like }), })), }, etc.)
            # Skip if braces/brackets are balanced on the same line (e.g., {for ...} or [for ...] expressions)
            if ((stripped_line.startswith('}') or '})' in stripped_line or (stripped_line.endswith(')') and '}' in stripped_line)) and
                not braces_balanced_on_line and not brackets_balanced_on_line):
                # If we have a section in the stack, it means we were in object({ internal params
                # and we should return to the previous section (which contains object({ declaration)
                # so that subsequent parameters at the same level can align with object({ declaration
                if section_stack:
                    # End current section (object({ internal params)
                    if current_section:
                        sections.append(current_section)
                    # Return to previous section (which contains object({ declaration)
                    # Important: When we have nested list(object({ structures, the stack may contain
                    # multiple sections. We need to pop in the correct order:
                    # - Top of stack: section for nested list(object({ (if any)
                    # - Bottom of stack: section for outer list(object({ (contains description and type)
                    # To correctly restore the section, we need to check if we're exiting the outer list(object({
                    # by comparing the indent level of the next parameter with the indent level of the declaration
                    # in the sections on the stack
                    current_section = section_stack.pop()
                    # Add the }) or })) line to the previous section so it's part of the same group
                    current_section.append((line, line_idx))
                    # Check if the next line is a parameter at the same indent level as the declaration
                    # If so, we should keep it in the same section to ensure proper alignment
                    # This ensures that parameters like 'default' and 'nullable' after list(object({...}))
                    # are in the same section as 'type' and 'description' for proper alignment
                    if line_idx + 1 < len(block_lines):
                        next_line = block_lines[line_idx + 1]
                        next_stripped = next_line.strip()
                        # Check if next line is a parameter (contains '=' and not a comment)
                        if _has_assignment_equals(next_line) and not next_stripped.startswith('#'):
                            next_indent = len(next_line) - len(next_line.lstrip())
                            # Find the indent of the declaration parameter in current_section
                            # Look for the parameter that contains object({ or list(object({
                            declaration_indent = None
                            for prev_line, prev_idx in current_section:
                                if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                    if 'object(' in prev_line or ('list(' in prev_line and 'object(' in prev_line):
                                        declaration_indent = len(prev_line) - len(prev_line.lstrip())
                                        break
                            # If we found a declaration, check if next line has the same indent
                            if declaration_indent is not None:
                                if next_indent == declaration_indent:
                                    # Next parameter is at the same indent level as declaration
                                    # This means we're exiting the outer list(object({ and should restore
                                    # the section containing description and type
                                    # Don't split section - it will be added to current_section in the next iteration
                                    pass
                                elif next_indent < declaration_indent:
                                    # Next parameter is at a lower indent level than the declaration in current_section
                                    # This means we're exiting the outer list(object({ and should restore
                                    # the section containing description and type
                                    # However, if current_section doesn't contain description and type,
                                    # we need to check if there's another section in the stack
                                    if section_stack:
                                        has_description_in_current = any('description' in line for line, _ in current_section)
                                        if not has_description_in_current:
                                            # current_section doesn't contain description and type
                                            # Check if the next section in the stack contains them
                                            if section_stack:
                                                next_section = section_stack[-1]
                                                has_description_in_next = any('description' in line for line, _ in next_section)
                                                if has_description_in_next:
                                                    # The next section in the stack contains description and type
                                                    # We should use that section instead
                                                    current_section = section_stack.pop()
                                                    current_section.append((line, line_idx))
                    continue
                elif brace_level == 0:
                    # Exiting top-level object grouping
                    # However, don't split section if the next line is a parameter at the same indent level
                    # This handles cases like locals blocks where a parameter value ends with }]]) 
                    # but the next line is another parameter that should be in the same section
                    # Also handle cases like jsonencode({...}) where parameters inside should be in the same section
                    should_split = True
                    if line_idx + 1 < len(block_lines):
                        next_line = block_lines[line_idx + 1]
                        next_stripped = next_line.strip()
                        # Check if next line is a parameter (contains '=' and not a comment)
                        if _has_assignment_equals(next_line) and not next_stripped.startswith('#'):
                            # Check if next line has the same indent as parameters in current_section
                            next_indent = len(next_line) - len(next_line.lstrip())
                            # Find the indent of parameters in current_section
                            # Also check if we're inside a function call (e.g., jsonencode({...}))
                            # If so, parameters at the same indent level should stay in the same section
                            is_inside_function_call = False
                            # Check if we're inside a function call by searching backwards from current line
                            search_idx = line_idx - 1
                            while search_idx >= 0:
                                search_line = block_lines[search_idx]
                                search_stripped = search_line.strip()
                                if search_stripped == '' or search_stripped.startswith('#'):
                                    search_idx -= 1
                                    continue
                                search_indent = len(search_line) - len(search_line.lstrip())
                                if _has_assignment_equals(search_line):
                                    search_after_equals = _get_after_assignment_equals(search_line)
                                    function_patterns = ['jsonencode(', 'merge(', 'try(', 'lookup(', 'alltrue(', 'anytrue(', 
                                                         'cidrsubnet(', 'cidrhost(', 'flatten(', 'keys(', 'values(', 'zipmap(']
                                    if search_after_equals and any(search_after_equals.startswith(pattern) for pattern in function_patterns):
                                        if '{' in search_after_equals or '[' in search_after_equals:
                                            is_inside_function_call = True
                                            break
                                if search_indent < next_indent:
                                    break
                                search_idx -= 1
                            
                            # If we're inside a function call, check if next line has the same indent as parameters in current_section
                            if is_inside_function_call:
                                if current_section:
                                    # Check if next line has the same indent as parameters in current_section
                                    for prev_line, prev_idx in current_section:
                                        if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                            prev_indent = len(prev_line) - len(prev_line.lstrip())
                                            if prev_indent == next_indent:
                                                # Next line is a parameter at the same indent level, don't split
                                                should_split = False
                                                break
                                else:
                                    # current_section is empty, but we're inside a function call
                                    # Check if there's a previous section with parameters at the same indent level
                                    # If so, we should NOT split, but instead merge with that section
                                    if sections:
                                        for sec_idx in range(len(sections) - 1, -1, -1):
                                            prev_section = sections[sec_idx]
                                            # Check if this section has parameters at the same indent level
                                            found_same_indent = False
                                            for prev_line, prev_idx in prev_section:
                                                if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                                                    if prev_indent == next_indent:
                                                        # Found a section with parameters at the same indent level
                                                        # Don't split - we'll merge with this section when we add the next line
                                                        found_same_indent = True
                                                        should_split = False
                                                        break
                                            if found_same_indent:
                                                break
                            else:
                                # Not inside function call, check normally
                                for prev_line, prev_idx in current_section:
                                    if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                        prev_indent = len(prev_line) - len(prev_line.lstrip())
                                        if prev_indent == next_indent:
                                            # Next line is a parameter at the same indent level, don't split
                                            should_split = False
                                            break
                    if should_split:
                        if current_section:
                            sections.append(current_section)
                            current_section = []
            
            # Check if we're exiting an array
            # When we encounter ], we need to check if we should exit array grouping
            # Check if line starts with ] or is exactly ']'
            # However, if we're still inside an object (brace_level > 0), we should NOT clear current_section
            # because subsequent parameters at the same level should align with the array declaration
            if bracket_level == 0 and (stripped_line == ']' or stripped_line.startswith(']')):
                # Exiting array grouping
                # Only clear current_section if we're also exiting the top-level object (brace_level == 0)
                # If we're still inside an object, keep current_section so subsequent parameters can align
                if brace_level == 0:
                    # Exiting top-level array (not inside an object)
                    # Check if we need to keep current_section for subsequent top-level params to align
                    # This handles cases like: flattened_data_volumes = [...] followed by default_data_volumes_configuration_with_virtual_spaces = ...
                    # They should be in the same section for alignment
                    if prev_bracket_level > 0:
                        # We just exited a top-level array
                        # Check if current_section has top-level parameters (parameters at the same indent as the array declaration)
                        has_top_level_params = False
                        if current_section:
                            for prev_line, prev_idx in current_section:
                                if _has_assignment_equals(prev_line) and not prev_line.strip().startswith('#'):
                                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                                    # Check if this is a top-level parameter (indent of 2 spaces in locals/resource blocks)
                                    if prev_indent == 2:
                                        has_top_level_params = True
                                        break
                        
                        if has_top_level_params:
                            # Keep current_section so subsequent top-level params can join it for alignment
                            # The array closing line will be added to current_section below
                            # Check if the next line is a top-level param - if so, ensure it stays in the same section
                            if line_idx + 1 < len(block_lines):
                                next_line = block_lines[line_idx + 1]
                                next_stripped = next_line.strip()
                                if _has_assignment_equals(next_line) and not next_stripped.startswith('#'):
                                    next_indent = len(next_line) - len(next_line.lstrip())
                                    if next_indent == 2:
                                        # Next line is a top-level param - keep current_section so it can join
                                        pass
                        else:
                            # No top-level params in current_section, split normally
                            if current_section:
                                sections.append(current_section)
                                current_section = []
                    else:
                        # Not exiting from an array, split normally
                        if current_section:
                            sections.append(current_section)
                            current_section = []
                # If brace_level > 0, we're still inside an object, so don't clear current_section
                # The array closing line will be added to current_section below
            
            # Add line to current section
            current_section.append((line, line_idx))

    # Add final section if exists
    if current_section:
        sections.append(current_section)
    
    # Post-process: Merge sections with top-level parameters that were separated by array closures
    # This handles cases like: flattened_data_volumes = [...] followed by default_data_volumes_configuration_with_virtual_spaces = [...]
    # They should be in the same section for alignment
    merged_top_level_sections = []
    i = 0
    while i < len(sections):
        current_sec = sections[i]
        # Check if this section has top-level parameters (indent=2)
        has_top_level = False
        top_level_params = []
        for line, idx in current_sec:
            if _has_assignment_equals(line) and not line.strip().startswith('#'):
                indent = len(line) - len(line.lstrip())
                if indent == 2:
                    has_top_level = True
                    top_level_params.append((line, idx))
        
        if has_top_level and len(top_level_params) > 0:
            # This section has top-level params - check if any subsequent section also has top-level params
            # Skip intermediate sections without top-level params (they may contain nested params or empty lines)
            # If so, merge them
            merged_sec = list(current_sec)
            j = i + 1
            while j < len(sections):
                next_sec = sections[j]
                next_has_top_level = False
                for line, idx in next_sec:
                    if _has_assignment_equals(line) and not line.strip().startswith('#'):
                        indent = len(line) - len(line.lstrip())
                        if indent == 2:
                            next_has_top_level = True
                            break
                
                if next_has_top_level:
                    # Check if there's a gap in line indices between current_sec and next_sec
                    # A gap due to empty lines should prevent merging, but gaps due to array/object content should allow merging
                    # This ensures that parameters separated by empty lines stay in different sections,
                    # but parameters separated by array closures can be merged (for alignment)
                    current_sec_last_idx = max(idx for _, idx in current_sec) if current_sec else -1
                    next_sec_first_idx = min(idx for _, idx in next_sec) if next_sec else -1
                    
                    # If there's a gap, check if it's due to an empty line
                    if current_sec_last_idx >= 0 and next_sec_first_idx >= 0:
                        gap = next_sec_first_idx - current_sec_last_idx
                        if gap > 1:
                            # Check if the gap contains an empty line
                            # Access block_lines from function closure
                            block_lines = getattr(_split_into_code_sections, '_block_lines', [])
                            has_empty_line_in_gap = False
                            for gap_idx in range(current_sec_last_idx + 1, next_sec_first_idx):
                                if gap_idx < len(block_lines):
                                    if block_lines[gap_idx].strip() == '':
                                        has_empty_line_in_gap = True
                                        break
                            
                            if has_empty_line_in_gap:
                                # Gap contains an empty line - don't merge (empty lines should split sections)
                                break
                            # Gap doesn't contain empty line (likely array/object content) - allow merging
                    
                    # Merge next section into current section
                    merged_sec_set = {(line, idx) for line, idx in merged_sec}
                    for line, idx in next_sec:
                        if (line, idx) not in merged_sec_set:
                            merged_sec.append((line, idx))
                            merged_sec_set.add((line, idx))
                    sections.pop(j)
                    # Don't increment j since we removed an element - continue checking next section
                    continue
                else:
                    # Next section doesn't have top-level params
                    # Only skip it if ALL its parameters are nested (indent > 2) or it has no parameters
                    # If it has any parameters at indent=2, we should stop merging (they belong to a different group)
                    has_top_level_like_params = False
                    has_any_params = False
                    for line, _ in next_sec:
                        if _has_assignment_equals(line) and not line.strip().startswith('#'):
                            has_any_params = True
                            indent = len(line) - len(line.lstrip())
                            if indent == 2:
                                # Found a parameter at indent=2 - this might be a different top-level group
                                # Stop merging to avoid incorrectly merging different groups
                                has_top_level_like_params = True
                                break
                    
                    # First check if this section is empty (contains only empty lines)
                    # Empty sections should prevent merging (empty lines should split sections)
                    is_empty_section = True
                    for line, _ in next_sec:
                        stripped = line.strip()
                        if stripped and not stripped.startswith('#'):
                            is_empty_section = False
                            break
                    
                    if is_empty_section:
                        # Empty section - stop merging (empty lines should split sections)
                        break
                    
                    if has_top_level_like_params:
                        # This section has parameters at indent=2 - stop merging
                        # They might belong to a different group (e.g., different resource blocks)
                        break
                    elif has_any_params:
                        # This section has parameters but all are nested (indent > 2)
                        # Skip it and continue searching for the next top-level section
                        j += 1
                        continue
                    else:
                        # This section has no parameters but is not empty (might be only comments)
                        # Skip it and continue searching
                        j += 1
                        continue
            
            merged_top_level_sections.append(merged_sec)
            i += 1
        else:
            # No top-level params, add as is
            merged_top_level_sections.append(current_sec)
            i += 1
    
    sections = merged_top_level_sections
    
    # Post-process: Merge sections that contain parameters at the same indent level within function calls
    # This handles cases where parameters like cache_key = { are separated from other parameters
    # at the same indent level within jsonencode({...}) blocks
    # Strategy: First, separate parameters inside function calls from those outside.
    # Then, merge sections containing parameters at the same indent level within the same function call.
    
    # Step 1: Separate parameters inside function calls from those outside
    separated_sections = []
    for current_sec in sections:
        param_lines = [(line, idx) for line, idx in current_sec if _has_assignment_equals(line) and not line.strip().startswith('#')]
        
        if len(param_lines) == 0:
            # No parameters, keep as is
            separated_sections.append(current_sec)
            continue
        
        # Separate parameters inside function calls from those outside
        params_inside_function = []  # (line_content, line_idx, indent, function_call_line_idx, function_call_line_content)
        params_outside_function = []  # (line_content, line_idx)
        non_param_lines = [(line, idx) for line, idx in current_sec if '=' not in line or line.strip().startswith('#')]
        
        for line_content, line_idx in param_lines:
            current_indent = len(block_lines[line_idx]) - len(block_lines[line_idx].lstrip())
            
            # Search backwards to find if we're inside a function call
            # Only consider parameters that are actually inside function call argument lists (inside braces/brackets)
            is_inside_function_call = False
            function_call_line_idx = None
            search_idx = line_idx - 1
            while search_idx >= 0:
                search_line = block_lines[search_idx]
                search_stripped = search_line.strip()
                if search_stripped == '' or search_stripped.startswith('#'):
                    search_idx -= 1
                    continue
                search_indent = len(search_line) - len(search_line.lstrip())
                if _has_assignment_equals(search_line):
                    search_after_equals = _get_after_assignment_equals(search_line)
                    function_patterns = ['jsonencode(', 'merge(', 'try(', 'lookup(', 'alltrue(', 'anytrue(', 
                                         'cidrsubnet(', 'cidrhost(', 'flatten(', 'keys(', 'values(', 'zipmap(']
                    if search_after_equals and any(search_after_equals.startswith(pattern) for pattern in function_patterns):
                        if '{' in search_after_equals or '[' in search_after_equals:
                            # Found a function call, but we need to verify that current parameter is actually inside it
                            # Check if current parameter's indent is greater than function call line's indent
                            # This ensures we only separate parameters that are truly inside the function call's argument list
                            if current_indent > search_indent:
                                is_inside_function_call = True
                                function_call_line_idx = search_idx
                                break
                if search_indent < current_indent:
                    break
                search_idx -= 1
            
            if is_inside_function_call and function_call_line_idx is not None:
                function_call_line_content = block_lines[function_call_line_idx].strip()
                params_inside_function.append((line_content, line_idx, current_indent, function_call_line_idx, function_call_line_content))
            else:
                params_outside_function.append((line_content, line_idx))
        
        # If we have both types of parameters, we need to split the section
        if params_outside_function and params_inside_function:
            # Create a section for outside parameters
            outside_param_set = set(params_outside_function)
            outside_sec = []
            for line, idx in current_sec:
                if (line, idx) in outside_param_set:
                    outside_sec.append((line, idx))
                elif (line, idx) in non_param_lines:
                    # Include non-param lines that are between outside parameters
                    # Check if this line is between outside parameters
                    outside_indices = [idx for _, idx in params_outside_function]
                    if outside_indices and min(outside_indices) <= idx <= max(outside_indices):
                        outside_sec.append((line, idx))
            if outside_sec:
                separated_sections.append(outside_sec)
        
        # If we have parameters inside function calls, create separate sections for each function call group
        if params_inside_function:
            # Group parameters by function call and indent level
            function_call_groups = {}
            for line_content, line_idx, indent, func_call_idx, func_call_content in params_inside_function:
                key = (func_call_idx, func_call_content, indent)
                if key not in function_call_groups:
                    function_call_groups[key] = []
                function_call_groups[key].append((line_content, line_idx))
            
            # Create a section for each group
            for (func_call_idx, func_call_content, indent), group_params in function_call_groups.items():
                group_param_set = set(group_params)
                group_sec = []
                for line, idx in current_sec:
                    if (line, idx) in group_param_set:
                        group_sec.append((line, idx))
                    elif (line, idx) in non_param_lines:
                        # Include non-param lines that are between these parameters
                        group_indices = [idx for _, idx in group_params]
                        if group_indices and min(group_indices) <= idx <= max(group_indices):
                            group_sec.append((line, idx))
                if group_sec:
                    separated_sections.append(group_sec)
        
        # If we only have parameters outside function calls, keep the section as is
        if params_outside_function and not params_inside_function:
            separated_sections.append(current_sec)
    
    # Step 2: Merge sections containing parameters at the same indent level within the same function call
    merged_sections = []
    i = 0
    while i < len(separated_sections):
        current_sec = separated_sections[i]
        param_lines = [(line, idx) for line, idx in current_sec if _has_assignment_equals(line) and not line.strip().startswith('#')]
        
        if len(param_lines) == 1:
            # Single parameter section - check if it's inside a function call
            line_content, line_idx = param_lines[0]
            current_indent = len(block_lines[line_idx]) - len(block_lines[line_idx].lstrip())
            
            # Search backwards to find if we're inside a function call
            is_inside_function_call = False
            function_call_line_idx = None
            search_idx = line_idx - 1
            while search_idx >= 0:
                search_line = block_lines[search_idx]
                search_stripped = search_line.strip()
                if search_stripped == '' or search_stripped.startswith('#'):
                    search_idx -= 1
                    continue
                search_indent = len(search_line) - len(search_line.lstrip())
                if _has_assignment_equals(search_line):
                    search_after_equals = _get_after_assignment_equals(search_line)
                    function_patterns = ['jsonencode(', 'merge(', 'try(', 'lookup(', 'alltrue(', 'anytrue(', 
                                         'cidrsubnet(', 'cidrhost(', 'flatten(', 'keys(', 'values(', 'zipmap(']
                    if search_after_equals and any(search_after_equals.startswith(pattern) for pattern in function_patterns):
                        if '{' in search_after_equals or '[' in search_after_equals:
                            is_inside_function_call = True
                            function_call_line_idx = search_idx
                            break
                if search_indent < current_indent:
                    break
                search_idx -= 1
            
            if is_inside_function_call and function_call_line_idx is not None:
                # Get the function call line content for comparison (strip for comparison)
                function_call_line_content = block_lines[function_call_line_idx].strip()
                
                # Look for the next section with parameters at the same indent level within the same function call
                merged_sec = list(current_sec)
                j = i + 1
                found_match = False
                while j < len(separated_sections):
                    next_sec = separated_sections[j]
                    # Check if next section has parameters at the same indent level
                    next_param_lines = [(line, idx) for line, idx in next_sec if _has_assignment_equals(line) and not line.strip().startswith('#')]
                    if not next_param_lines:
                        # No parameters in this section, skip it
                        j += 1
                        continue
                    
                    has_same_indent = False
                    is_same_function_call = False
                    for next_line_content, next_line_idx in next_param_lines:
                        next_indent = len(block_lines[next_line_idx]) - len(block_lines[next_line_idx].lstrip())
                        if next_indent == current_indent:
                            # Check if it's inside the same function call by comparing function call line content
                            next_search_idx = next_line_idx - 1
                            while next_search_idx >= 0:
                                next_search_line = block_lines[next_search_idx]
                                next_search_stripped = next_search_line.strip()
                                if next_search_stripped == '' or next_search_stripped.startswith('#'):
                                    next_search_idx -= 1
                                    continue
                                next_search_indent = len(next_search_line) - len(next_search_line.lstrip())
                                if _has_assignment_equals(next_search_line):
                                    next_search_after_equals = _get_after_assignment_equals(next_search_line)
                                    function_patterns = ['jsonencode(', 'merge(', 'try(', 'lookup(', 'alltrue(', 'anytrue(', 
                                                         'cidrsubnet(', 'cidrhost(', 'flatten(', 'keys(', 'values(', 'zipmap(']
                                    if next_search_after_equals and any(next_search_after_equals.startswith(pattern) for pattern in function_patterns):
                                        if '{' in next_search_after_equals or '[' in next_search_after_equals:
                                            # Check if this is the same function call by comparing stripped line content
                                            if next_search_line.strip() == function_call_line_content:
                                                has_same_indent = True
                                                is_same_function_call = True
                                                break
                                if next_search_indent < next_indent:
                                    break
                                next_search_idx -= 1
                            if has_same_indent:
                                break
                        elif next_indent < current_indent:
                            # We've gone past the function call scope, stop searching
                            break
                    
                    if has_same_indent and is_same_function_call:
                        # Merge next section into current section (avoid duplicates)
                        merged_sec_set = {(line, idx) for line, idx in merged_sec}
                        for line, idx in next_sec:
                            if (line, idx) not in merged_sec_set:
                                merged_sec.append((line, idx))
                                merged_sec_set.add((line, idx))
                        # Remove next section from sections list
                        separated_sections.pop(j)
                        found_match = True
                        # Don't increment j since we removed an element - next element is now at index j
                        # Continue checking for more sections to merge (loop will continue with same j)
                        continue
                    else:
                        # If indent is lower, we've left the function call scope, stop searching
                        if next_param_lines:
                            next_line_content, next_line_idx = next_param_lines[0]
                            next_indent = len(block_lines[next_line_idx]) - len(block_lines[next_line_idx].lstrip())
                            if next_indent < current_indent:
                                break
                        # Otherwise, continue to next section
                        j += 1
                        continue
                
                # Add merged section
                merged_sections.append(merged_sec)
                i += 1
            else:
                # Not inside function call, add as is
                merged_sections.append(current_sec)
                i += 1
        else:
            # Multiple parameters or no parameters, add as is
            merged_sections.append(current_sec)
            i += 1
    
    return merged_sections


_HEREDOC_START_RE = re.compile(r'<<-?([A-Za-z_][A-Za-z0-9_]*)\s*$')


def _match_heredoc_start(line: str) -> Optional[str]:
    """Return heredoc terminator if line opens a heredoc, else None."""
    match = _HEREDOC_START_RE.search(line)
    return match.group(1) if match else None


def _find_all_assignment_equals_positions(line: str) -> List[int]:
    """
    Find all assignment '=' operator positions in a line.

    Comparison / fat-arrow operators (==, !=, <=, >=, =>) are ignored so
    expression content is not misidentified as parameter assignments.
    """
    positions: List[int] = []
    in_quotes = False
    quote_char = None
    i = 0
    while i < len(line):
        char = line[i]
        if char in ('"', "'") and (i == 0 or line[i - 1] != '\\'):
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
        elif not in_quotes and char == '=':
            prev_char = line[i - 1] if i > 0 else ''
            next_char = line[i + 1] if i + 1 < len(line) else ''
            # Skip comparison / fat-arrow operators: ==, !=, <=, >=, =>
            if next_char == '=' or next_char == '>':
                i += 2
                continue
            if prev_char in '!<>':
                i += 1
                continue
            positions.append(i)
        i += 1
    return positions


def _find_assignment_equals_pos(line: str) -> int:
    """Find the first assignment '=' operator in a line, or -1."""
    positions = _find_all_assignment_equals_positions(line)
    return positions[0] if positions else -1


def _has_assignment_equals(line: str) -> bool:
    """Return True if the line contains an assignment '=' operator."""
    return _find_assignment_equals_pos(line) != -1


def _get_after_assignment_equals(line: str) -> str:
    """Return the text after the assignment '=' operator, stripped."""
    pos = _find_assignment_equals_pos(line)
    return line[pos + 1:].strip() if pos != -1 else ''


def _get_before_assignment_equals(line: str) -> str:
    """Return the text before the assignment '=' operator."""
    pos = _find_assignment_equals_pos(line)
    return line[:pos] if pos != -1 else ''


def _extract_assignment_param_name(before_equals: str) -> Optional[str]:
    """
    Extract the parameter name from text before an assignment '='.

    Handles normal `name =` lines and trailing assignments after a block open,
    e.g. `dynamic "tags" { for_each = ... }`.
    """
    simple = re.match(r'^\s*(["\']?)([^"\'=\s]+)\1\s*$', before_equals)
    if simple:
        return simple.group(2)

    # Same-line nested assignment: ... { param_name <spaces>
    trailing = re.search(r'\{\s*(["\']?)([A-Za-z_][A-Za-z0-9_]*)\1\s*$', before_equals)
    if trailing:
        return trailing.group(2)

    return None


def _check_parameter_alignment_in_section(
    section: List[Tuple[str, int]], block_type: str, block_start_line: int, block_lines: List[str] = None
) -> List[Tuple[int, str]]:
    """
    Check parameter alignment in a code section.

    Args:
        section: List of (line_content, relative_line_idx) tuples
        block_type: Type of the block being checked
        block_start_line: Starting line number of the block

    Returns:
        List[Tuple[int, str]]: List of (line_number, error_message) tuples
    """
    errors = []
    parameter_lines = []
    
    # Track heredoc state to skip content inside heredoc blocks
    in_heredoc = False
    heredoc_terminator = None
    
    # Check if this section is inside a function call (e.g., jsonencode({...}))
    # However, we should still check alignment for parameters inside jsonencode({...})
    # because they are object literals that should be aligned
    # Only skip if we're inside function call parameters (not object literals)
    is_inside_function_call = False
    
    if block_lines and section:
        # Check each parameter line in the section to see if any is inside a function call
        # We need to check all lines, not just the first one
        for line_content, relative_line_idx in section:
            if '=' not in line_content or line_content.strip().startswith('#'):
                continue
            
            current_indent = len(block_lines[relative_line_idx]) - len(block_lines[relative_line_idx].lstrip())
            
            # Search backwards through block_lines to find if this line is inside a function call
            search_idx = relative_line_idx - 1
            while search_idx >= 0:
                search_line = block_lines[search_idx]
                search_stripped = search_line.strip()
                if search_stripped == '' or search_stripped.startswith('#'):
                    search_idx -= 1
                    continue
                search_indent = len(search_line) - len(search_line.lstrip())
                # If we find a line with lower or equal indent, check if it's a function call
                if search_indent <= current_indent:
                    if _has_assignment_equals(search_line):
                        search_after_equals = _get_after_assignment_equals(search_line)
                        # Match common Terraform functions that can contain objects/arrays
                        function_patterns = ['jsonencode(', 'merge(', 'try(', 'lookup(', 'alltrue(', 'anytrue(', 
                                             'cidrsubnet(', 'cidrhost(', 'flatten(', 'keys(', 'values(', 'zipmap(']
                        if search_after_equals and any(search_after_equals.startswith(pattern) for pattern in function_patterns):
                            # Check if the function call contains '{' or '[' on the same line
                            # If so, the parameters inside are object/array literals that should be checked
                            # Only skip if we're in function call parameters (not object literals)
                            # For jsonencode({...}), merge({...}), etc., the content inside should be checked
                            # because it's an object literal, not function parameters
                            if '{' in search_after_equals or '[' in search_after_equals:
                                # This is a function call with object/array literal on the same line
                                # The parameters inside are object/array literals, not function parameters
                                # So we should still check alignment for them
                                # Only skip if we're actually in function call parameters (not object literals)
                                # For now, we'll check alignment for object literals inside function calls
                                pass
                    # If we find a parameter at lower indent that's not a function call, stop searching
                    if search_indent < current_indent:
                        break
                search_idx -= 1
    
    # Note: We no longer skip alignment checks for sections inside function calls
    # because parameters inside jsonencode({...}), merge({...}), etc. are object literals
    # that should be checked for alignment

    # Extract parameter lines from section
    for line_content, relative_line_idx in section:
        line = line_content.rstrip()
        line_stripped = line.strip()
        
        # Check for heredoc end pattern first (before checking start)
        # The terminator must be at the beginning of the line (after stripping)
        if in_heredoc and heredoc_terminator:
            if line_stripped == heredoc_terminator:
                in_heredoc = False
                heredoc_terminator = None
                # Continue to process the terminator line if it contains '=' or boundary markers
        
        # Skip lines inside heredoc blocks (but not the heredoc start line itself)
        if in_heredoc:
            continue
        
        # Check for heredoc start pattern (<<EOF, <<-EOF, etc.)
        # Match <<EOF or <<-EOF at the end of a line
        heredoc_terminator_match = _match_heredoc_start(line)
        if heredoc_terminator_match:
            in_heredoc = True
            heredoc_terminator = heredoc_terminator_match
            # Continue to process the heredoc start line if it contains '=' or boundary markers
        
        if _has_assignment_equals(line) and not line_stripped.startswith('#'):
            # Skip block declarations
            if not re.match(r'^\s*(data|resource|ephemeral|variable|output|locals|module|check|import|moved)\s+', line):
                # Skip provider declarations in required_providers blocks
                if (re.match(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*\{', line) and
                    any('required_providers' in prev_line for prev_line, _ in section)):
                    continue
                
                # Skip Terraform for expressions (e.g., for image in collection : image if condition)
                if re.match(r'^\s*for\s+', line):
                    continue
                
                parameter_lines.append((line, relative_line_idx))

    if len(parameter_lines) == 0:
        return errors

    # Group parameters by indentation level
    # Parameters at different indentation levels should be checked separately
    # This ensures that nested parameters (e.g., inside list(object({...}))) 
    # are not grouped with top-level parameters (e.g., default, nullable)
    indent_groups = {}
    for line, relative_line_idx in parameter_lines:
        line_with_spaces = line.expandtabs(2)
        indent_spaces = len(line_with_spaces) - len(line_with_spaces.lstrip())
        indent_level = indent_spaces // 2  # Terraform uses 2 spaces per indent level
        
        if indent_level not in indent_groups:
            indent_groups[indent_level] = []
        indent_groups[indent_level].append((line, relative_line_idx))

    # Check each indentation group
    for indent_level, group_lines in indent_groups.items():
        # Sort group_lines by relative_line_idx to ensure correct order
        group_lines_sorted = sorted(group_lines, key=lambda x: x[1])
        
        # Split group by empty lines in the original block_lines
        # Parameters separated by empty lines should be in different alignment groups
        sub_groups = []
        current_sub_group = []
        prev_line_idx = None
        
        for line, relative_line_idx in group_lines_sorted:
            if prev_line_idx is not None and block_lines:
                # Check if there's an empty line between prev_line_idx and relative_line_idx
                has_empty_line_between = False
                for check_idx in range(prev_line_idx + 1, relative_line_idx):
                    if check_idx < len(block_lines) and block_lines[check_idx].strip() == '':
                        has_empty_line_between = True
                        break
                
                if has_empty_line_between:
                    # Empty line separates - start new sub-group
                    if current_sub_group:
                        sub_groups.append(current_sub_group)
                    current_sub_group = [(line, relative_line_idx)]
                else:
                    current_sub_group.append((line, relative_line_idx))
            else:
                current_sub_group.append((line, relative_line_idx))
            
            prev_line_idx = relative_line_idx
        
        if current_sub_group:
            sub_groups.append(current_sub_group)
        
        # Check alignment for each sub-group
        for sub_group in sub_groups:
            group_errors = _check_group_alignment(sub_group, indent_level, block_type, block_start_line, block_lines)
            errors.extend(group_errors)
            
            # Check '=' after-spacing; skip lines already owned by ST.004/ST.005
            for line, relative_line_idx in sub_group:
                if _should_skip_due_to_format_conflicts(
                    line, indent_level, relative_line_idx, block_lines
                ):
                    continue
                spacing_errors = _check_parameter_spacing(
                    line, relative_line_idx, block_type, block_start_line
                )
                errors.extend(spacing_errors)

    return errors


def _has_st004_issue(line: str) -> bool:
    """Check if line has ST.004 issue (tab character)."""
    return '\t' in line


def _has_st005_issue(line: str, indent_level: int = 0, relative_line_idx: int = 0,
                     block_lines: List[str] = None) -> bool:
    """
    Return True when the line has a clear ST.005-class indentation issue.

    Only odd space counts are treated as conflicts here. Nesting-depth mistakes
    that still use even indentation are left for ST.005 itself; ST.003 may still
    report alignment on those lines (complementary, not conflicting).

    Extra parameters are retained for call-site compatibility.
    """
    _ = (indent_level, relative_line_idx, block_lines)
    actual_indent = len(line) - len(line.lstrip())
    return actual_indent % 2 != 0


# Resource/data/module-level meta-parameters owned by ST.008 for blank-line spacing.
# They must not participate in column alignment, but still use compact '=' spacing.
_RESOURCE_META_PARAMETERS = frozenset(['count', 'for_each', 'provider', 'depends_on', 'lifecycle'])
_DYNAMIC_BLOCK_OPEN_RE = re.compile(
    r'dynamic\s+(?:"[^"]+"|\'[^\']+\'|[a-zA-Z_][a-zA-Z0-9_]*)\s*\{'
)
_FOR_EACH_IDENT_RE = re.compile(r'(?<![A-Za-z0-9_])for_each(?![A-Za-z0-9_])')


def _find_unquoted_for_each_pos(line: str) -> Optional[int]:
    """Return start index of an unquoted `for_each` identifier, or None."""
    in_double = False
    in_single = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '\\' and (in_double or in_single) and i + 1 < len(line):
            i += 2
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "'" and not in_double:
            in_single = not in_single
        elif not in_double and not in_single:
            match = _FOR_EACH_IDENT_RE.match(line, i)
            if match:
                return match.start()
        i += 1
    return None


def _scan_braces_for_dynamic(line: str, end: int, brace_depth: int,
                             dynamic_open_depths: List[int]) -> int:
    """Scan line[:end] updating brace depth / dynamic stack; return new brace_depth."""
    stripped = line.strip()
    if not stripped or stripped.startswith('#'):
        return brace_depth

    # Only treat as dynamic open if the opening '{' falls inside the scanned range.
    opens_dynamic = bool(_DYNAMIC_BLOCK_OPEN_RE.match(stripped))
    in_double = False
    in_single = False
    i = 0
    while i < end:
        ch = line[i]
        if ch == '\\' and (in_double or in_single) and i + 1 < len(line):
            i += 2
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "'" and not in_double:
            in_single = not in_single
        elif not in_double and not in_single:
            if ch == '{':
                brace_depth += 1
                if opens_dynamic:
                    dynamic_open_depths.append(brace_depth)
                    opens_dynamic = False
            elif ch == '}':
                if dynamic_open_depths and brace_depth == dynamic_open_depths[-1]:
                    dynamic_open_depths.pop()
                brace_depth = max(0, brace_depth - 1)
        i += 1
    return brace_depth


def _is_inside_dynamic_block(relative_line_idx: int, block_lines: Optional[List[str]]) -> bool:
    """
    Return True if the `for_each` at relative_line_idx is inside an open dynamic block.

    Uses brace-depth tracking (quote-aware) so a closed dynamic block does not
    keep later top-level `for_each` marked as dynamic-internal.

    The current line is scanned only up to an unquoted `for_each` token so
    same-line forms like `dynamic "x" { for_each = ... }` are detected.
    """
    if not block_lines or relative_line_idx < 0 or relative_line_idx >= len(block_lines):
        return False

    brace_depth = 0
    # Brace depths at which a dynamic block was opened (depth after consuming '{').
    dynamic_open_depths: List[int] = []

    for j in range(relative_line_idx):
        brace_depth = _scan_braces_for_dynamic(
            block_lines[j], len(block_lines[j]), brace_depth, dynamic_open_depths
        )

    current = block_lines[relative_line_idx]
    for_each_pos = _find_unquoted_for_each_pos(current)
    if for_each_pos is not None:
        brace_depth = _scan_braces_for_dynamic(
            current, for_each_pos, brace_depth, dynamic_open_depths
        )

    return bool(dynamic_open_depths)


def _is_resource_or_data_block(block_type: Optional[str]) -> bool:
    """Return True for blocks where Terraform meta-parameters (count/for_each/...) apply."""
    return bool(block_type and (
        block_type.startswith('resource.')
        or block_type.startswith('data.')
        or block_type.startswith('module.')
        or block_type.startswith('ephemeral.')
    ))


def _line_excluded_from_alignment_baseline(line: str) -> bool:
    """Tab (ST.004) and odd-indent (ST.005-class) lines must not set the equals baseline."""
    if '\t' in line:
        return True
    actual_indent = len(line) - len(line.lstrip())
    return actual_indent % 2 != 0


def _is_resource_meta_parameter(param_name: str, relative_line_idx: int = 0,
                                block_lines: Optional[List[str]] = None,
                                block_type: Optional[str] = None) -> bool:
    """
    Return True for meta-parameters that skip column alignment.

    Only applies inside resource/data/module blocks so ordinary attributes named
    `count` (e.g. in variable object types or locals) are unaffected.

    `for_each` inside a dynamic block is treated as a normal parameter (aligned with
    ST.008), so it still participates in compact/column checks of its local group.
    """
    if not _is_resource_or_data_block(block_type):
        return False
    if param_name not in _RESOURCE_META_PARAMETERS:
        return False
    if param_name == 'for_each' and _is_inside_dynamic_block(relative_line_idx, block_lines):
        return False
    return True


def _should_skip_due_to_format_conflicts(line: str, indent_level: int,
                                         relative_line_idx: int = 0,
                                         block_lines: Optional[List[str]] = None) -> bool:
    """Skip ST.003 when ST.004/ST.005 already apply to the line."""
    if _has_st004_issue(line):
        return True
    if _has_st005_issue(line, indent_level, relative_line_idx, block_lines):
        return True
    return False


def _param_name_quote_chars(line: str, equals_pos: Optional[int] = None) -> int:
    """Return 2 if the parameter name before '=' is quoted, otherwise 0."""
    if equals_pos is None:
        before = _get_before_assignment_equals(line).strip()
    else:
        before = line[:equals_pos].strip()
    if len(before) >= 2 and before[0] == before[-1] and before[0] in ('"', "'"):
        return 2
    return 0


def _param_visual_name_width(param_name: str, line: str, equals_pos: Optional[int] = None) -> int:
    """Visual width of a parameter name including surrounding quotes."""
    return len(param_name) + _param_name_quote_chars(line, equals_pos)


def _expected_equals_location_from_params(indent_spaces: int,
                                          params: List[Tuple[str, str, int]]) -> int:
    """
    Compute expected '=' column from (param_name, line, equals_pos) items.

    Uses max(len(name) + quote_chars) so mixed quoted/unquoted names do not
    incorrectly add +2 for every parameter in the group.
    """
    max_width = max(
        _param_visual_name_width(param_name, line, equals_pos)
        for param_name, line, equals_pos in params
    )
    return indent_spaces + max_width + 1


def _count_spaces_before_equals(line: str, equals_pos: int) -> int:
    """Count whitespace characters between the parameter name and '='."""
    before_equals = line[:equals_pos]
    return len(before_equals) - len(before_equals.rstrip())


def _compact_equals_before_spacing_error(actual_line_num: int, block_type: str,
                                         line: str, equals_pos: int) -> Optional[Tuple[int, str]]:
    """Return an error if there is not exactly one space before '='."""
    if _count_spaces_before_equals(line, equals_pos) == 1:
        return None
    return (
        actual_line_num,
        f"Parameter assignment equals sign spacing incorrect in {block_type}. "
        f"Expected exactly 1 space between parameter name and '='"
    )


def _check_equals_after_spacing(line: str, relative_line_idx: int, block_type: str, 
                                block_start_line: int) -> List[Tuple[int, str]]:
    """Check space after equals sign (must be exactly 1 space) for every assignment on the line."""
    errors = []
    actual_line_num = block_start_line + relative_line_idx + 1

    for equals_pos in _find_all_assignment_equals_positions(line):
        after_equals = line[equals_pos + 1:]

        if not after_equals.startswith(' '):
            errors.append((
                actual_line_num,
                f"Parameter assignment should have exactly one space after '=' in {block_type}"
            ))
        elif after_equals.startswith('  '):
            errors.append((
                actual_line_num,
                f"Parameter assignment should have exactly one space after '=' in {block_type}, found multiple spaces"
            ))

    return errors


def _check_group_alignment(
    group_lines: List[Tuple[str, int]], 
    indent_level: int, 
    block_type: str, 
    block_start_line: int,
    block_lines: List[str] = None
) -> List[Tuple[int, str]]:
    """Check alignment within a group of parameters."""
    errors = []
    
    # Extract parameter names and find longest
    param_data = []
    for line, relative_line_idx in group_lines:
        equals_positions = _find_all_assignment_equals_positions(line)
        if not equals_positions:
            continue

        # Same-line multi-assignment: spacing-only (no column alignment).
        if len(equals_positions) > 1:
            actual_line_num = block_start_line + relative_line_idx + 1
            if not _should_skip_due_to_format_conflicts(
                line, indent_level, relative_line_idx, block_lines
            ):
                for equals_pos in equals_positions:
                    compact_error = _compact_equals_before_spacing_error(
                        actual_line_num, block_type, line, equals_pos
                    )
                    if compact_error:
                        errors.append(compact_error)
            continue

        equals_pos = equals_positions[0]
        
        # Skip array/list declarations
        before_equals = line[:equals_pos]
        if before_equals.strip().startswith('[') or (before_equals.strip() == '' and line.strip().startswith('[')):
            continue
        
        # Check if this is a nested block declaration (e.g., "extend_param = {")
        after_equals = line[equals_pos + 1:].strip()
        is_nested_block = after_equals.startswith('{')
        
        param_name = _extract_assignment_param_name(before_equals)
        if param_name:
            # Include nested blocks for alignment checking
            # Don't skip them, they should still be aligned with other parameters
            param_data.append((param_name, line, relative_line_idx, equals_pos, is_nested_block))
    
    if len(param_data) < 1:
        return errors
    
    # Special case: if there's only one parameter in the section, only check that there's exactly 1 space before '='
    # This handles cases where a parameter is in its own section (e.g., separated by empty lines).
    # Resource meta-parameters are included here so padded forms like `provider             = x` are caught.
    if len(param_data) == 1:
        param_name, line, relative_line_idx, equals_pos, is_nested_block = param_data[0]
        actual_line_num = block_start_line + relative_line_idx + 1
        
        if _should_skip_due_to_format_conflicts(line, indent_level, relative_line_idx, block_lines):
            return errors
        
        compact_error = _compact_equals_before_spacing_error(
            actual_line_num, block_type, line, equals_pos
        )
        if compact_error:
            errors.append(compact_error)
        
        return errors

    # Column alignment uses only non-meta, non-conflict parameters so they do not distort the baseline.
    alignment_params = [
        item for item in param_data
        if not _is_resource_meta_parameter(item[0], item[2], block_lines, block_type)
        and not _line_excluded_from_alignment_baseline(item[1])
    ]
    
    indent_spaces = indent_level * 2  # Convert indent level back to spaces
    expected_equals_location = None

    if alignment_params:
        visual_params = [
            (param_name, line, equals_pos)
            for param_name, line, _, equals_pos, _ in alignment_params
        ]
        # Formula: indent + max(len(name) + quote_chars) + 1 space before '='
        # (.tfvars uses _check_group_alignment_tfvars instead of this path.)
        expected_equals_location = _expected_equals_location_from_params(indent_spaces, visual_params)

    # Check each parameter: meta -> compact spacing only; others -> column alignment
    for param_name, line, relative_line_idx, equals_pos, is_nested_block in param_data:
        actual_line_num = block_start_line + relative_line_idx + 1

        if _should_skip_due_to_format_conflicts(line, indent_level, relative_line_idx, block_lines):
            continue

        if _is_resource_meta_parameter(param_name, relative_line_idx, block_lines, block_type):
            compact_error = _compact_equals_before_spacing_error(
                actual_line_num, block_type, line, equals_pos
            )
            if compact_error:
                errors.append(compact_error)
            continue

        if expected_equals_location is None:
            continue

        # Skip alignment check if equals position matches expected location
        if equals_pos == expected_equals_location:
            continue

        quote_chars = _param_name_quote_chars(line, equals_pos)
        required_spaces_before_equals = (
            expected_equals_location - indent_spaces - len(param_name) - quote_chars
        )
        
        if equals_pos < expected_equals_location:
            errors.append((
                actual_line_num,
                f"Parameter assignment equals sign not aligned in {block_type}. "
                f"Expected {required_spaces_before_equals} spaces between parameter name and '=', "
                f"equals sign should be at column {expected_equals_location + 1}"
            ))
        elif equals_pos > expected_equals_location:
            errors.append((
                actual_line_num,
                f"Parameter assignment equals sign not aligned in {block_type}. "
                f"Too many spaces before '=', equals sign should be at column {expected_equals_location + 1}"
            ))
    
    return errors


def _check_parameter_spacing(
    line: str, 
    relative_line_idx: int, 
    block_type: str, 
    block_start_line: int
) -> List[Tuple[int, str]]:
    """Check spacing around equals sign - only check space after equals sign."""
    # Use the dedicated function for checking space after equals
    return _check_equals_after_spacing(line, relative_line_idx, block_type, block_start_line)


def get_rule_description() -> dict:
    """
    Retrieve detailed information about the ST.003 rule.

    This function provides metadata about the rule including its purpose,
    validation criteria, and examples. This information can be used for
    documentation generation, help systems, or configuration interfaces.

    Returns:
        dict: A dictionary containing comprehensive rule information including:
            - id: The unique rule identifier
            - name: Human-readable rule name
            - description: Detailed explanation of what the rule validates
            - category: The rule category (Style/Format)
            - severity: The severity level of violations
            - examples: Dictionary with valid and invalid examples

    Example:
        >>> info = get_rule_description()
        >>> print(info['name'])
        Parameter alignment check
    """
    return {
        "id": "ST.003",
        "name": "Parameter alignment check",
        "description": (
            "Validates that parameter assignments in resource, data, ephemeral, module, provider, locals, "
            "terraform, variable, output, import, moved, and check blocks have equals signs aligned "
            "(quote-aware) with one space after '='. In resource/data/module/ephemeral blocks, meta-parameters "
            "skip column alignment but still require compact '=' spacing. terraform.tfvars is also supported, "
            "with single-parameter groups requiring exactly one space before '='."
        ),
        "category": "Style/Format",
        "severity": "error",
        "rationale": (
            "Proper parameter alignment with consistent spacing improves code readability and maintains "
            "consistent formatting standards. Aligning equals signs with proper spacing from the longest "
            "parameter name makes it easier to scan through configuration parameters and understand "
            "the structure at a glance."
        ),
        "examples": {
            "valid": [
                '''
data "huaweicloud_compute_flavors" "test" {
  performance_type = "normal"
  cpu_core_count   = 4
  memory_size      = 8
}

resource "huaweicloud_compute_instance" "test" {
  name               = "tf_test_instance"
  flavor_id          = try(data.huaweicloud_compute_flavors.test.flavors[0].id, "c6.2xlarge.4")
  security_group_ids = [huaweicloud_networking_secgroup.test.id]
  # ...
}

provider "huaweicloud" {
  region     = var.region_name
  access_key = var.access_key
  secret_key = var.secret_key
}

locals {
  is_available = true
  environment = "dev"
  tags        = {
    "Environment" = "Development"
  }
}

terraform {
  required_version = ">= 1.0"
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = ">= 1.0"
    }
  }
}

variable "instance_name" {
  description = "The name of the ECS instance"
  type        = string
  default     = "test-instance"
}
'''
            ],
            "invalid": [
                '''
data "huaweicloud_compute_flavors" "test" {
  performance_type="normal"    # No spaces around equals
  cpu_core_count= 4            # No space before equals
  memory_size =8               # No space after equals
}

resource "huaweicloud_compute_instance" "test" {
  # Parameter equal signs are not aligned or properly spaced
  name = "tf_test_instance"
  flavor_id = try(data.huaweicloud_compute_flavors.test.flavors[0].id, "c6.2xlarge.4")
  security_group_ids = [huaweicloud_networking_secgroup.test.id]
  # ...
}

provider "huaweicloud" {
  region = var.region_name               # Equals signs not aligned
  access_key= var.access_key             # No space before equals
  secret_key =var.secret_key             # No space after equals
}

locals {
  is_available=true                      # No space before equals
  environment =  "dev"                   # Multiple spaces after equals
  tags         =  {                      # Multiple spaces after equals
    "Environment" = "Development"
  }
}

terraform {
  required_version= ">= 1.0"             # No space before equals
  required_providers {
    huaweicloud = {
      source= "huaweicloud/huaweicloud"  # No space before equals
      version =  ">= 1.0"                # Multiple spaces after equals
    }
  }
}

variable "instance_name" {
  description= "The name of the ECS instance"  # No space before equals
  type =  string                              # Multiple spaces after equals
  default = "test-instance"
}
'''
            ]
        },
        "auto_fixable": True,
        "performance_impact": "minimal"
    }


def _has_blank_line_between(lines: List[str], start_line_idx: int, end_line_idx: int) -> bool:
    """
    Check if there's a blank line between two line indices in the original content.
    Only counts truly empty lines, ignores comment-only lines.
    
    Args:
        lines: Original content lines
        start_line_idx: Start line index (0-based)
        end_line_idx: End line index (0-based)
    
    Returns:
        bool: True if there's a blank line between the two indices
    """
    for i in range(start_line_idx + 1, end_line_idx):
        if i >= len(lines):
            break
        stripped = lines[i].strip()
        # True blank line: empty string
        if stripped == '':
            return True
    return False


def _is_equals_in_string_value(line: str) -> bool:
    """
    Check if the equals sign is inside a string value (quotes).
    
    This function identifies cases where '=' is part of a string value like "==", "!=", ">=", "<=",
    rather than a parameter assignment operator.
    
    Args:
        line: The line to check
        
    Returns:
        bool: True if the equals sign is inside a string value, False otherwise
    """
    equals_pos = _find_assignment_equals_pos(line)
    if equals_pos == -1:
        return False
    
    line_stripped = line.strip()
    
    # List of comparison operators that might appear in string values
    # These include: ==, !=, >=, <=, and variations
    comparison_ops = ['==', '!=', '>=', '<=', '==', '!=', '>=', '<=']
    
    # If the line starts with a quote and contains comparison operators, it's likely a string value
    # Examples: '"=="', '"!="', '">="', '"<="', '      "==",'
    if line_stripped.startswith('"'):
        for op in comparison_ops:
            if f'"{op}' in line or f'{op}"' in line:
                return True
    if line_stripped.startswith("'"):
        for op in comparison_ops:
            if f"'{op}" in line or f"{op}'" in line:
                return True
    
    # Check if after equals starts with quote and contains comparison operators
    after_equals = line[equals_pos + 1:].strip()
    if after_equals.startswith('"'):
        for op in comparison_ops:
            if f'"{op}' in after_equals or f'{op}"' in after_equals:
                # Check if before_equals is empty or just whitespace (meaning this is a value, not assignment)
                before_equals = line[:equals_pos].strip()
                if not before_equals or before_equals == '':
                    return True
    
    if after_equals.startswith("'"):
        for op in comparison_ops:
            if f"'{op}" in after_equals or f"{op}'" in after_equals:
                before_equals = line[:equals_pos].strip()
                if not before_equals or before_equals == '':
                    return True
    
    return False


def _check_tfvars_parameter_alignment(file_path: str, content: str, log_error_func: Callable[[str, str, str, Optional[int]], None]) -> None:
    """
    Check parameter alignment in terraform.tfvars files.
    
    This function handles variable assignments in .tfvars files, which don't follow
    the same block structure as .tf files. It groups consecutive variable assignments
    and checks their alignment.
    
    Args:
        file_path (str): Path to the file being checked
        content (str): Cleaned file content (comments removed)
        log_error_func (Callable): Error logging function
    """
    lines = content.split('\n')
    
    # Track heredoc state to skip content inside heredoc blocks
    in_heredoc = False
    heredoc_terminator = None
    
    # Find all variable assignment lines and boundary markers
    assignment_lines = []
    for i, line in enumerate(lines):
        # Check heredoc state
        line_stripped = line.strip()
        
        # Check for heredoc end pattern first (before checking start)
        # The terminator must be at the beginning of the line (after stripping)
        if in_heredoc and heredoc_terminator:
            if line_stripped == heredoc_terminator:
                in_heredoc = False
                heredoc_terminator = None
                # Continue to process the terminator line if it contains '=' or boundary markers
        
        # Skip lines inside heredoc blocks (but not the heredoc start line itself)
        if in_heredoc:
            continue
        
        # Check for heredoc start pattern (<<EOF, <<-EOF, etc.)
        # This must be checked AFTER we've processed the line (if it contains '=' or boundary markers)
        # Match <<EOF or <<-EOF at the end of a line
        heredoc_terminator_match = _match_heredoc_start(line)
        if heredoc_terminator_match:
            in_heredoc = True
            heredoc_terminator = heredoc_terminator_match
            # Continue to process the heredoc start line if it contains '=' or boundary markers
        
        stripped = line_stripped
        if stripped and _has_assignment_equals(stripped):
            # Include all assignment lines (comments already removed)
            assignment_lines.append((i + 1, line))
        elif stripped.rstrip(',') in ['{', '}', '[', ']']:
            # Include brace and bracket lines as boundary markers (allow trailing commas)
            assignment_lines.append((i + 1, line))
    
    if not assignment_lines:
        return
    
    # Group assignment lines by structural boundaries
    # This handles nested structures like arrays and objects in tfvars files
    sections = []
    current_section = []
    brace_level = 0
    bracket_level = 0
    top_level_indent = 0  # Track the indent of the current top-level section
    
    # Helper function to check if a section contains top-level parameters
    def _section_has_top_level_param(sec):
        for _ln, _l in sec:
            if _has_assignment_equals(_l) and (len(_l) - len(_l.lstrip())) == 0:
                return True
        return False
    
    for idx, (line_num, line) in enumerate(assignment_lines):
        stripped_line = line.strip()
        # Also strip trailing comma for boundary checks
        stripped_for_boundary = stripped_line.rstrip(',')
        
        # Save levels BEFORE updating them
        prev_brace_level_saved = brace_level
        prev_bracket_level_saved = bracket_level
        
        # Track brace and bracket levels to detect nested structures
        # Ensure levels don't go negative (defensive programming)
        for char in stripped_line:
            if char == '{':
                brace_level += 1
            elif char == '}':
                brace_level = max(0, brace_level - 1)
            elif char == '[':
                bracket_level += 1
            elif char == ']':
                bracket_level = max(0, bracket_level - 1)
        
        # Check if we're entering an array (line ends with [)
        if stripped_line.endswith('[') and bracket_level == 1 and _has_assignment_equals(stripped_line):
            after_equals = _get_after_assignment_equals(stripped_line)
            if after_equals == '[':
                # Array declaration line - check if we should split based on blank lines
                line_indent = len(line) - len(line.lstrip())
                prev_brace_level = prev_brace_level_saved
                prev_bracket_level = prev_bracket_level_saved
                
                # For top-level array declarations, don't split section
                # Top-level array declarations should be in the same group as previous top-level parameters
                # They will be aligned together, with the longest parameter name determining the alignment position
                is_top_level_array = (line_indent == 0 and 
                                    prev_brace_level == 0 and 
                                    prev_bracket_level == 0)
                
                # Add to current section without splitting
                # This allows top-level parameters, array declarations, and object declarations
                # to be in the same group if they're not separated by other top-level parameters
                current_section.append((line_num, line))
                continue
        
        # Check if we're entering an object (parameter = {)
        # But only if it's NOT a top-level parameter (top-level should be aligned first)
        if stripped_line.endswith('{') and _has_assignment_equals(stripped_line):
            after_equals = _get_after_assignment_equals(stripped_line)
            if after_equals == '{':
                # Check if this is a top-level parameter
                # We need to use levels BEFORE this line updates them
                line_indent = len(line) - len(line.lstrip())
                prev_brace_level = prev_brace_level_saved
                prev_bracket_level = prev_bracket_level_saved
                
                is_top_level = (line_indent == 0 and 
                              prev_brace_level == 0 and 
                              prev_bracket_level == 0)
                
                if not is_top_level:
                    # Entering non-top-level object grouping
                    # Continue processing to check blank lines between
                    pass
        
        # Don't split section on ] or } - just exit the grouping level
        # Sections should only be split on blank lines or when entering new structures
        
        # When exiting an array (bracket_level becomes 0), check if we should merge with previous section
        # This handles cases where a top-level array declaration is followed by other top-level params
        # Example: rule_conditions = [...] followed by approval_content = ...
        # They should be in the same section for alignment
        if bracket_level == 0 and prev_bracket_level_saved > 0:
            # We just exited an array - check if next top-level param should join current section
            # This will be handled in the regular grouping logic below
            pass
        
        # Don't clear current_section when exiting array
        # This allows subsequent top-level params to join the same section
        # Check if we're starting a new object element inside an array (standalone '{')
        # In tfvars, each object element within an array should form its own alignment group
        # Split sections when encountering a standalone '{' inside any array level
        if bracket_level >= 1 and stripped_for_boundary == '{' and '=' not in stripped_line:
            # Only split if current_section is not tracking top-level parameters
            if current_section and not _section_has_top_level_param(current_section):
                sections.append(current_section)
                current_section = []
        
        # When exiting an array at top level, ensure subsequent top-level params join the same section
        # This handles cases like: rule_conditions = [...] followed by approval_content = ...
        # This check must happen BEFORE processing regular grouping, so the merge happens before
        # the next line (line 23) is processed
        # Note: This check happens when we encounter the closing bracket ']', so bracket_level just became 0
        if bracket_level == 0 and prev_bracket_level_saved > 0 and prev_brace_level_saved == 0:
            # We just exited a top-level array
            # Check if we need to merge sections to ensure subsequent top-level params can join
            # The key insight: when a top-level array closes, we want subsequent top-level params
            # to be in the same section as the array declaration, so they can align together
            if len(sections) > 0:
                prev_section = sections[-1] if sections else None
                if prev_section and _section_has_top_level_param(prev_section):
                    # Previous section has top-level params (like rule_conditions = [)
                    # Merge current_section with prev_section so subsequent top-level params can join
                    sections.pop()
                    if current_section:
                        # Add nested params from current_section to prev_section
                        prev_section.extend(current_section)
                    # Set current_section to prev_section so subsequent top-level params join it
                    current_section = prev_section
            elif current_section and _section_has_top_level_param(current_section):
                # current_section already has top-level params, no need to merge
                # This handles the case where the array content didn't cause section splitting
                pass
            elif not current_section and len(sections) > 0:
                # current_section is empty, check if we should restore from previous section
                prev_section = sections[-1] if sections else None
                if prev_section and _section_has_top_level_param(prev_section):
                    sections.pop()
                    current_section = prev_section
            # If current_section doesn't have top-level params and there's no previous section with top-level params,
            # we'll handle the merge when the next top-level param is processed (in the regular grouping logic below)
        
        # Regular grouping logic (handles gaps between lines)
        # Check if we should process this line for regular grouping
        process_regular_grouping = True
        is_boundary_marker = stripped_for_boundary in ['{', '}', '[', ']'] and '=' not in stripped_line
        if is_boundary_marker:
            # Standalone braces/brackets are handled above, skip regular grouping
            process_regular_grouping = False
            # But still add boundary markers to current_section (they may be needed for section tracking)
            # Especially important for array closing brackets that affect section grouping
            if current_section:
                current_section.append((line_num, line))
            elif not current_section and len(sections) > 0:
                # If current_section is empty, add to the last section
                sections[-1].append((line_num, line))
            else:
                # No current_section and no sections, create a new one
                current_section = [(line_num, line)]
        
        if process_regular_grouping:
            # Calculate current line's indent
            line_indent = len(line) - len(line.lstrip())
            
            if not current_section:
                # First line
                top_level_indent = line_indent
                current_section.append((line_num, line))
            else:
                # Check if this is a top-level parameter
                # A parameter is top-level if:
                # 1. It has the same indent as the current section's top-level indent
                # 2. It's not inside any nested structures (we check BEFORE this line increases the levels)
                # 3. We need to use the PREVIOUS brace_level and bracket_level (before this line increases them)
                prev_brace_level = prev_brace_level_saved
                prev_bracket_level = prev_bracket_level_saved
                
                # For top-level parameters (prev_brace_level == 0 and prev_bracket_level == 0),
                # we should align them even if they contain { or [
                # Also include parameters inside array objects that have the same indent level
                # For tfvars, top-level parameters have indent level 0
                is_top_level = (line_indent == top_level_indent and 
                              _has_assignment_equals(stripped_line) and
                              ((prev_brace_level == 0 and prev_bracket_level == 0) or line_indent == 0))
                
                # Check if this is a parameter inside an object (regardless of indent level)
                # This handles cases where parameters have different indentation within the same object
                # For tfvars, parameters in the same object should be grouped together
                is_object_param = (_has_assignment_equals(stripped_line) and
                                 prev_brace_level >= 1 and
                                 not stripped_line.strip().startswith('#'))
                
                if is_top_level or is_object_param:
                    # This is another top-level parameter, array object parameter, or object parameter
                    # Find the previous parameter at the same level (top-level for top-level, nested for nested)
                    prev_line_num = None
                    for prev_ln, prev_l in reversed(current_section):
                        prev_stripped = prev_l.strip()
                        prev_stripped_boundary = prev_stripped.rstrip(',')
                        # Skip pure boundary markers (lines that are only ], }, [, or {)
                        # But include parameter declarations like "param = [" or "param = {"
                        if _has_assignment_equals(prev_l):
                            # This is a parameter declaration
                            # For top-level parameters, only use previous top-level parameters
                            # For nested parameters, use any previous parameter
                            if is_top_level:
                                prev_indent = len(prev_l) - len(prev_l.lstrip())
                                if prev_indent == 0:
                                    # Previous parameter is also top-level, use it
                                    prev_line_num = prev_ln
                                    break
                            else:
                                # For nested parameters, use any previous parameter
                                prev_line_num = prev_ln
                                break
                        elif prev_stripped_boundary not in ['{', '}', '[', ']']:
                            # Not a boundary marker, but also not a parameter - skip
                            continue
                    
                    # If no previous parameter found at same level, check previous section for top-level params
                    if prev_line_num is None and is_top_level and len(sections) > 0:
                        # Look for last top-level param in previous section
                        prev_section = sections[-1] if sections else None
                        if prev_section:
                            for prev_ln, prev_l in reversed(prev_section):
                                if _has_assignment_equals(prev_l):
                                    prev_indent = len(prev_l) - len(prev_l.lstrip())
                                    if prev_indent == 0:
                                        prev_line_num = prev_ln
                                        break
                    
                    # If still no previous parameter found, use the last line in section
                    if prev_line_num is None and current_section:
                        prev_line_num = current_section[-1][0]
                    
                    has_gap = False
                    if prev_line_num is not None:
                        has_gap = _has_blank_line_between(lines, prev_line_num - 1, line_num - 1)
                    
                    # For tfvars, split on blank lines unless they're inside arrays/objects
                    # If there's a blank line and we're both at the top level, always split
                    if has_gap and prev_brace_level == 0 and prev_bracket_level == 0:
                        # Both are top-level parameters separated by a blank line
                        # Split into separate sections
                        sections.append(current_section)
                        current_section = [(line_num, line)]
                        
                    else:
                        # If current_section tracks top-level params, and this line is an object param
                        # within an array/object, start a new section for nested params
                        # If this is a top-level parameter and we're currently in a section with nested params,
                        # we should return to the previous section with top-level params (if it exists)
                        # BUT only if there's no blank line between the previous section and current line
                        # Otherwise, if this is a nested param and current section has top-level params, split for nested params
                        if is_top_level and not _section_has_top_level_param(current_section) and len(sections) > 0:
                            # Current line is top-level param, but current section only has nested params
                            # Check if previous section has top-level params - if so, check for blank line before merging
                            prev_section = sections[-1] if sections else None
                            if prev_section and _section_has_top_level_param(prev_section):
                                # Find the last top-level parameter in previous section
                                # Also check for array/object declarations that might be the last top-level element
                                last_top_level_line_num = None
                                # First, try to find the last top-level param in prev_section
                                for prev_ln, prev_l in reversed(prev_section):
                                    if _has_assignment_equals(prev_l):
                                        prev_indent = len(prev_l) - len(prev_l.lstrip())
                                        if prev_indent == 0:
                                            last_top_level_line_num = prev_ln
                                            break
                                
                                # If we still haven't found a top-level param, check the current_section
                                # for array closing brackets that might help us find the last top-level param
                                if last_top_level_line_num is None:
                                    for prev_ln, prev_l in reversed(current_section):
                                        if prev_l.strip().rstrip(',') == ']' and len(prev_l) - len(prev_l.lstrip()) == 0:
                                            # This is a top-level array closing in current_section
                                            # The array declaration should be in prev_section
                                            for prev_ln2, prev_l2 in reversed(prev_section):
                                                if _has_assignment_equals(prev_l2) and (len(prev_l2) - len(prev_l2.lstrip())) == 0:
                                                    equals_pos = _find_assignment_equals_pos(prev_l2)
                                                    after_equals = prev_l2[equals_pos + 1:].strip()
                                                    if after_equals.startswith('['):
                                                        last_top_level_line_num = prev_ln2
                                                        break
                                            if last_top_level_line_num:
                                                break
                                
                                # If still not found, just use the last top-level param in prev_section
                                # This handles cases where the array closing bracket logic didn't work
                                if last_top_level_line_num is None:
                                    for prev_ln, prev_l in reversed(prev_section):
                                        if _has_assignment_equals(prev_l) and (len(prev_l) - len(prev_l.lstrip())) == 0:
                                            last_top_level_line_num = prev_ln
                                            break
                                
                                # Check if there's a blank line between last top-level param and current line
                                has_blank_line = False
                                if last_top_level_line_num is not None:
                                    has_blank_line = _has_blank_line_between(lines, last_top_level_line_num - 1, line_num - 1)
                                
                                if not has_blank_line:
                                    # No blank line - merge previous section with current_section and add this line
                                    sections.pop()
                                    # Add nested params from current_section to prev_section
                                    if current_section:
                                        prev_section.extend(current_section)
                                    # Add the current top-level param
                                    prev_section.append((line_num, line))
                                    current_section = prev_section
                                else:
                                    # Blank line separates - start new section
                                    if current_section:
                                        sections.append(current_section)
                                    current_section = [(line_num, line)]
                            else:
                                # No previous section with top-level params, start new section
                                if current_section:
                                    sections.append(current_section)
                                current_section = [(line_num, line)]
                        elif is_top_level and _section_has_top_level_param(current_section):
                            # Current line is top-level param and current section has top-level params
                            # Check for blank line to decide if we should split
                            prev_line_num = None
                            for prev_ln, prev_l in reversed(current_section):
                                if _has_assignment_equals(prev_l) and (len(prev_l) - len(prev_l.lstrip())) == 0:
                                    prev_line_num = prev_ln
                                    break
                                # Also check for array closing brackets at top level
                                elif prev_l.strip().rstrip(',') == ']' and len(prev_l) - len(prev_l.lstrip()) == 0:
                                    # This is a top-level array closing - find the array declaration before it
                                    for prev_ln2, prev_l2 in reversed(current_section):
                                        if _has_assignment_equals(prev_l2) and (len(prev_l2) - len(prev_l2.lstrip())) == 0:
                                            equals_pos = _find_assignment_equals_pos(prev_l2)
                                            after_equals = prev_l2[equals_pos + 1:].strip()
                                            if after_equals.startswith('['):
                                                prev_line_num = prev_ln2
                                                break
                                    if prev_line_num:
                                        break
                            
                            has_gap = False
                            if prev_line_num is not None:
                                has_gap = _has_blank_line_between(lines, prev_line_num - 1, line_num - 1)
                            
                            if has_gap and prev_brace_level == 0 and prev_bracket_level == 0:
                                # Both are top-level parameters separated by a blank line
                                # Split into separate sections
                                sections.append(current_section)
                                current_section = [(line_num, line)]
                            else:
                                # Same group, add to current section
                                current_section.append((line_num, line))
                        elif is_object_param and _section_has_top_level_param(current_section) and not is_top_level:
                            # Current line is object param (nested), and section has top-level params - split for nested params
                            sections.append(current_section)
                            current_section = [(line_num, line)]
                        else:
                            # Same group, add to current section
                            current_section.append((line_num, line))
                else:
                    # Not a top-level parameter, check gap from previous line
                    prev_line_num = current_section[-1][0]
                    has_gap = _has_blank_line_between(lines, prev_line_num - 1, line_num - 1)
                    if has_gap:
                        # Blank line separates sections
                        sections.append(current_section)
                        current_section = [(line_num, line)]
                    else:
                        # Same line group, add to current section
                        current_section.append((line_num, line))
    
    if current_section:
        sections.append(current_section)
    
    # Final merge pass: ensure top-level parameters that should be in the same section are merged
    # This handles cases where the merge logic during processing didn't work correctly
    # Specifically, merge sections where:
    # - Previous section has top-level params ending with an array/object declaration
    # - Current section has top-level params
    # - No blank line between them
    # - The last top-level param in prev_section is an array/object declaration (not a simple assignment)
    merged_sections = []
    for i, section in enumerate(sections):
        if i == 0:
            merged_sections.append(section)
            continue
        
        prev_section = merged_sections[-1] if merged_sections else None
        if prev_section and _section_has_top_level_param(prev_section):
            # Find the last top-level param in prev_section
            last_top_level_line_num = None
            last_top_level_line = None
            for prev_ln, prev_l in reversed(prev_section):
                if _has_assignment_equals(prev_l) and (len(prev_l) - len(prev_l.lstrip())) == 0:
                    last_top_level_line_num = prev_ln
                    last_top_level_line = prev_l
                    break
            
            # Check if the last top-level param is an array/object declaration
            # Only merge if it's an array/object declaration (ends with [ or {)
            is_array_or_object_decl = False
            if last_top_level_line is not None:
                equals_pos = _find_assignment_equals_pos(last_top_level_line)
                if equals_pos != -1:
                    after_equals = last_top_level_line[equals_pos + 1:].strip()
                    is_array_or_object_decl = after_equals.startswith('[') or after_equals.startswith('{')
            
            # Find the first top-level param in current section
            # Only merge if current section also has top-level params
            first_top_level_line_num = None
            current_section_has_top_level = False
            for curr_ln, curr_l in section:
                if _has_assignment_equals(curr_l) and (len(curr_l) - len(curr_l.lstrip())) == 0:
                    current_section_has_top_level = True
                    if first_top_level_line_num is None:
                        first_top_level_line_num = curr_ln
                    break
            
            # Only merge if:
            # 1. The last top-level param in prev_section is an array/object declaration
            # 2. Current section also has top-level params (not just nested params)
            # 3. There's no blank line between them
            if is_array_or_object_decl and last_top_level_line_num is not None and first_top_level_line_num is not None and current_section_has_top_level:
                has_blank_line = _has_blank_line_between(lines, last_top_level_line_num - 1, first_top_level_line_num - 1)
                if not has_blank_line:
                    # Merge sections
                    merged_sections[-1].extend(section)
                    continue
        
        merged_sections.append(section)
    
    sections = merged_sections
    
    # Check alignment in each section
    all_errors = []
    processed_lines = set()  # Track processed lines to avoid duplicates
    
    last_top_level_expected: Optional[int] = None
    last_top_level_group_size: Optional[int] = None
    last_multi_param_section_idx: Optional[int] = None
    for section_idx, section in enumerate(sections):
        # Convert (line_num, line) to (line, relative_line_idx) format
        # For tfvars, we need to preserve original line numbers
        converted_section = [(line, line_num) for line_num, line in section]
        # Use the first line number minus 1 as the base line number
        # because _check_parameter_alignment_in_section adds 1 to the line number
        base_line_num = section[0][0] - 1
        
        # Compute override expected for single top-level param sections using last seen top-level expected
        # Determine if this section has a top-level group with >=2 params to refresh the expected
        # or only one param, in which case use the last expected
        # Build groups quickly to detect counts
        temp_params = []
        for line, actual_line_num in converted_section:
            if _has_assignment_equals(line) and not line.strip().startswith('#'):
                indent = len(line) - len(line.lstrip())
                indent_level = indent // 2
                temp_params.append((indent_level, actual_line_num, line))
        top_level_params = [(n, l) for il, n, l in temp_params if il == 0]
        top_level_override = None
        if len(top_level_params) >= 2:
            # Recompute expected for this section's top-level group
            group_lines = [(n, l) for n, l in top_level_params]
            last_top_level_expected = _compute_expected_equals_location_tfvars(group_lines, 0)
            last_top_level_group_size = len(top_level_params)
            last_multi_param_section_idx = section_idx
        elif len(top_level_params) == 1 and last_top_level_expected is not None:
            # Only use override if:
            # 1. The previous section had at least 2 top-level parameters
            # 2. There are no other top-level parameters between the previous section and current section
            # 3. There's NO blank line between the previous section's last top-level param and current section's first param
            # This ensures that single-parameter groups separated by blank lines don't incorrectly
            # align with previous single-parameter groups, and that parameters with other top-level
            # parameters between them don't align
            if last_top_level_group_size is not None and last_top_level_group_size >= 2 and last_multi_param_section_idx is not None:
                # Check if there are other top-level object declarations (param = {) between the last multi-param section and current section
                # Array declarations (param = [) should not prevent alignment
                has_other_top_level_object_decls = False
                last_multi_param_section = sections[last_multi_param_section_idx]
                last_multi_param_last_line_num = last_multi_param_section[-1][0] if last_multi_param_section else 0
                current_first_line_num = section[0][0] if section else 0
                # Check all sections between last multi-param section and current section
                for check_idx in range(last_multi_param_section_idx + 1, section_idx):
                    check_section = sections[check_idx]
                    for check_line_num, check_line in check_section:
                        if check_line_num > last_multi_param_last_line_num and check_line_num < current_first_line_num:
                            if _has_assignment_equals(check_line):
                                check_indent = len(check_line) - len(check_line.lstrip())
                                if check_indent == 0 and not check_line.strip().startswith('#'):
                                    # Check if this is an object declaration (param = {), not array (param = [)
                                    check_equals_pos = _find_assignment_equals_pos(check_line)
                                    if check_equals_pos != -1:
                                        check_after_equals = check_line[check_equals_pos + 1:].strip()
                                        if check_after_equals.startswith('{'):
                                            has_other_top_level_object_decls = True
                                            break
                    if has_other_top_level_object_decls:
                        break
                
                # Check if there's a blank line between last multi-param section's last top-level param and current section's first param
                has_blank_line_between_sections = False
                if not has_other_top_level_object_decls:
                    # Find the last top-level parameter in last_multi_param_section
                    last_top_level_param_line_num = None
                    for check_line_num, check_line in reversed(last_multi_param_section):
                        if _has_assignment_equals(check_line):
                            check_indent = len(check_line) - len(check_line.lstrip())
                            if check_indent == 0 and not check_line.strip().startswith('#'):
                                last_top_level_param_line_num = check_line_num
                                break
                    
                    # Find the first top-level parameter in current section
                    current_first_top_level_param_line_num = None
                    for check_line_num, check_line in section:
                        if _has_assignment_equals(check_line):
                            check_indent = len(check_line) - len(check_line.lstrip())
                            if check_indent == 0 and not check_line.strip().startswith('#'):
                                current_first_top_level_param_line_num = check_line_num
                                break
                    
                    # Check if there's a blank line between them
                    if last_top_level_param_line_num is not None and current_first_top_level_param_line_num is not None:
                        has_blank_line_between_sections = _has_blank_line_between(lines, last_top_level_param_line_num - 1, current_first_top_level_param_line_num - 1)
                
                if not has_other_top_level_object_decls and not has_blank_line_between_sections:
                    top_level_override = last_top_level_expected
            # Don't update last_top_level_group_size here - preserve it for subsequent sections

        errors = _check_tfvars_parameter_alignment_in_section(converted_section, "tfvars", top_level_expected_override=top_level_override, original_lines=lines)
        
        # Only add errors for lines that haven't been processed yet
        for line_num, msg in errors:
            if line_num not in processed_lines:
                all_errors.append((line_num, msg))
                processed_lines.add(line_num)
    
    # Sort errors by line number
    all_errors.sort(key=lambda x: x[0])
    
    # Report sorted errors
    for line_num, error_msg in all_errors:
        log_error_func(file_path, "ST.003", error_msg, line_num)


def _check_tfvars_parameter_alignment_in_section(section: List[Tuple[str, int]], block_type: str, top_level_expected_override: Optional[int] = None, original_lines: Optional[List[str]] = None) -> List[Tuple[int, str]]:
    """
    Check parameter alignment in a tfvars section.
    
    This is a wrapper that directly uses actual line numbers from tfvars.
    
    Args:
        section: List of (line_content, actual_line_num) tuples
        block_type: Type of the block being checked
    
    Returns:
        List[Tuple[int, str]]: List of (line_number, error_message) tuples
    """
    errors = []
    parameter_lines = []
    
    # Extract parameter lines from section
    for line_content, actual_line_num in section:
        line = line_content.rstrip()
        if _has_assignment_equals(line) and not line.strip().startswith('#'):
            # Skip block declarations
            if not re.match(r'^\s*(data|resource|ephemeral|variable|output|locals|module|check|import|moved)\s+', line):
                # Skip lines where equals sign is inside a string value (e.g., "==", "!=")
                if _is_equals_in_string_value(line):
                    continue
                parameter_lines.append((line, actual_line_num))
    
    if len(parameter_lines) == 0:
        return errors
    
    # Group by indentation level, but also split groups on blank lines
    # Blank lines reset grouping, so parameters separated by blank lines should be in different groups
    # groups[indent_level] is a list of groups, where each group is a list of (line_num, line) tuples
    groups = {}
    current_groups = {}  # Track current group for each indent level
    prev_line_num = None
    
    for line, actual_line_num in parameter_lines:
        indent = len(line) - len(line.lstrip())
        indent_level = indent // 2
        # Skip odd indent (indent not multiple of 2) - these are ST.005 issues
        if indent % 2 != 0:
            continue
        
        # Check if there's a blank line between this parameter and the previous one
        # We need to access the original file content to check for blank lines
        # Only check for blank lines if the previous parameter has the same indent level
        # This ensures that parameters at different indent levels don't affect each other's grouping
        if prev_line_num is not None and original_lines is not None:
            # Find the previous parameter with the same indent level
            prev_same_level_line_num = None
            # Find the index of current parameter in parameter_lines
            current_idx = None
            for idx, (pl_line, pl_line_num) in enumerate(parameter_lines):
                if pl_line_num == actual_line_num and pl_line == line:
                    current_idx = idx
                    break
            
            if current_idx is not None:
                for prev_line, prev_actual_line_num in reversed(parameter_lines[:current_idx]):
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    prev_indent_level = prev_indent // 2
                    if prev_indent_level == indent_level:
                        prev_same_level_line_num = prev_actual_line_num
                        break
            
            if prev_same_level_line_num is not None:
                has_gap = _has_blank_line_between(original_lines, prev_same_level_line_num - 1, actual_line_num - 1)
                
                # For nested parameters (indent_level > 0), also check for structural boundaries
                # Parameters in different objects (separated by } and {) should be in different groups
                has_structural_boundary = False
                if indent_level > 0 and original_lines is not None:
                    # Check if there's a closing brace followed by an opening brace between the two parameters
                    # This indicates they're in different objects
                    for check_line_idx in range(prev_same_level_line_num - 1, actual_line_num - 1):
                        if check_line_idx < len(original_lines):
                            check_line_raw = original_lines[check_line_idx]
                            check_line = check_line_raw.strip().rstrip(',')
                            # Skip comment lines
                            if check_line.startswith('#'):
                                continue
                            # Check for closing brace at same or higher indent level
                            if check_line == '}':
                                check_indent = len(check_line_raw) - len(check_line_raw.lstrip())
                                # If the closing brace is at a lower indent level than our parameters, it's a boundary
                                if check_indent < indent:
                                    # Look for an opening brace or object declaration after this closing brace
                                    for next_line_idx in range(check_line_idx + 1, actual_line_num - 1):
                                        if next_line_idx < len(original_lines):
                                            next_line_raw = original_lines[next_line_idx]
                                            next_line = next_line_raw.strip().rstrip(',')
                                            # Skip comment lines
                                            if next_line.startswith('#'):
                                                continue
                                            # Check for standalone opening brace
                                            if next_line == '{':
                                                has_structural_boundary = True
                                                break
                                            # Check for object declaration (param = {)
                                            if _has_assignment_equals(next_line):
                                                equals_pos = _find_assignment_equals_pos(next_line)
                                                after_equals = next_line[equals_pos + 1:].strip()
                                                if after_equals.startswith('{'):
                                                    has_structural_boundary = True
                                                    break
                                    if has_structural_boundary:
                                        break
                
                if has_gap or has_structural_boundary:
                    # There is a blank line or structural boundary between parameters at the same indent level - split groups
                    if indent_level in current_groups and current_groups[indent_level]:
                        if indent_level not in groups:
                            groups[indent_level] = []
                        groups[indent_level].append(current_groups[indent_level])
                        current_groups[indent_level] = []
        
        if indent_level not in groups:
            groups[indent_level] = []
        if indent_level not in current_groups:
            current_groups[indent_level] = []
        
        current_groups[indent_level].append((actual_line_num, line))
        prev_line_num = actual_line_num
    
    # Finalize any remaining groups
    for indent_level, group in current_groups.items():
        if group:
            if indent_level not in groups:
                groups[indent_level] = []
            groups[indent_level].append(group)
    
    # Check alignment and spacing for each group
    for indent_level, group_list in groups.items():
        # group_list is a list of groups, where each group is a list of (line_num, line) tuples
        for group_lines in group_list:
            # Sort by line number to maintain order
            group_lines.sort()
        
            # If this is a top-level group with only one parameter and we have an override, apply it
            # This allows top-level parameters separated by blank lines to still align with previous top-level parameters
            if indent_level == 0 and len(group_lines) == 1 and top_level_expected_override is not None:
                actual_line_num, line = group_lines[0]
                display_line = line.expandtabs(2)
                equals_pos = _find_assignment_equals_pos(display_line)
                # Only apply override for top-level object declarations (param = {), not arrays
                after_equals_strip = display_line[equals_pos + 1:].strip() if equals_pos != -1 else ''
                if equals_pos != -1 and after_equals_strip.startswith('{') and '\t' not in line and equals_pos != top_level_expected_override:
                    # Compute param display length with quotes if any for message spacing
                    before_equals = display_line[:equals_pos]
                    if before_equals.strip().startswith('"') or before_equals.strip().startswith("'"):
                        name_match = re.match(r"^\s*([\"\'])([^\"'\s=]+)\1", before_equals)
                        param_name = name_match.group(2) if name_match else before_equals.strip().strip("\"'")
                        name_len = len(param_name) + 2
                    else:
                        param_name = before_equals.strip()
                        name_len = len(param_name)
                    indent_spaces = indent_level * 2
                    required_spaces_before_equals = top_level_expected_override - indent_spaces - name_len
                    
                    # If using override would result in negative spaces, it means current param is longer
                    # than the previous longest param. In this case, don't use override, let it fall through
                    # to normal alignment check which will use current param's own length
                    if required_spaces_before_equals < 0:
                        # Don't use override, fall through to normal alignment check
                        pass
                    else:
                        errors.append((
                            actual_line_num,
                            f"Parameter assignment equals sign not aligned in {block_type}. "
                            f"Expected {required_spaces_before_equals} spaces between parameter name and '=', "
                            f"equals sign should be at column {top_level_expected_override + 1}"
                        ))
                        # Always check spacing after '=' as usual
                        spacing_errors = _check_parameter_spacing_tfvars(line, actual_line_num, block_type)
                        errors.extend(spacing_errors)
                        continue
                # If we didn't use override (either not an object declaration or would result in negative spaces),
                # fall through to normal alignment check. But still check spacing after '=' as usual
                spacing_errors = _check_parameter_spacing_tfvars(line, actual_line_num, block_type)
                errors.extend(spacing_errors)
                # Don't continue here - let it fall through to normal alignment check

            alignment_errors = _check_group_alignment_tfvars(group_lines, indent_level, block_type)
            errors.extend(alignment_errors)
            
            # Check spacing for each line in the group
            for actual_line_num, line in group_lines:
                spacing_errors = _check_parameter_spacing_tfvars(line, actual_line_num, block_type)
                errors.extend(spacing_errors)
    
    return errors


def _compute_expected_equals_location_tfvars(group_lines: List[Tuple[int, str]], indent_level: int) -> Optional[int]:
    """Compute expected equals location for a tfvars group similarly to _check_group_alignment_tfvars."""
    # Reuse the same param_data building logic
    param_data = []
    for actual_line_num, line in group_lines:
        display_line = line.expandtabs(2)
        equals_pos = _find_assignment_equals_pos(display_line)
        if equals_pos == -1:
            continue
        before_equals = display_line[:equals_pos]
        if before_equals.strip().startswith('[') or (before_equals.strip() == '' and line.strip().startswith('[')):
            continue
        after_equals = display_line[equals_pos + 1:].strip()
        is_object_or_array_decl = after_equals.startswith('[') or after_equals.startswith('{')
        actual_indent = len(line) - len(line.lstrip())
        should_skip_from_expected_calc = is_object_or_array_decl and actual_indent > 0
        if before_equals.strip().startswith('"') or before_equals.strip().startswith("'"):
            m = re.match(r"^\s*([\"\'])([^\"'\s=]+)\1", before_equals)
            param_name = m.group(2) if m else None
        else:
            m = re.match(r"^\s*([^\"'\s=]+)", before_equals)
            param_name = m.group(1) if m else None
        if param_name is not None:
            param_data.append((param_name, line, actual_line_num, equals_pos, should_skip_from_expected_calc))
    if not param_data:
        return None
    indent_spaces = indent_level * 2
    # Compute longest visual width (name + quotes) considering skip logic
    non_skipped_non_tab_params = [p for p in param_data if not p[4] and '\t' not in p[1]]
    if non_skipped_non_tab_params:
        longest_param_width = max(_param_visual_name_width(p[0], p[1], p[3]) for p in non_skipped_non_tab_params)
        skipped_non_tab_params = [p for p in param_data if p[4] and '\t' not in p[1]]
        if skipped_non_tab_params:
            longest_skipped_width = max(_param_visual_name_width(p[0], p[1], p[3]) for p in skipped_non_tab_params)
            if longest_skipped_width > longest_param_width and longest_skipped_width - longest_param_width >= 4:
                longest_param_width = longest_skipped_width
    else:
        non_tab_params = [p for p in param_data if '\t' not in p[1]]
        if non_tab_params:
            longest_param_width = max(_param_visual_name_width(p[0], p[1], p[3]) for p in non_tab_params)
        else:
            longest_param_width = max(_param_visual_name_width(p[0], p[1], p[3]) for p in param_data)
    return indent_spaces + longest_param_width + 1


def _check_group_alignment_tfvars(group_lines: List[Tuple[int, str]], indent_level: int, block_type: str) -> List[Tuple[int, str]]:
    """Check alignment within a group of tfvars parameters, using actual line numbers."""
    errors = []
    
    # Deduplicate group_lines to avoid processing the same line multiple times
    seen_lines = set()
    unique_group_lines = []
    for line_num, line in group_lines:
        if line_num not in seen_lines:
            seen_lines.add(line_num)
            unique_group_lines.append((line_num, line))
    
    group_lines = unique_group_lines
    
    # Extract parameter names and find longest
    param_data = []
    for actual_line_num, line in group_lines:
        display_line = line.expandtabs(2)
        equals_pos = _find_assignment_equals_pos(display_line)
        if equals_pos == -1:
            continue
        
        # Skip lines where equals sign is inside a string value (e.g., "==", "!=")
        if _is_equals_in_string_value(display_line):
            continue
        
        before_equals = display_line[:equals_pos]
        if before_equals.strip().startswith('[') or (before_equals.strip() == '' and line.strip().startswith('[')):
            continue
        
        # Check if this is an array/object declaration line (e.g., "param = [" or "param = {")
        # For top-level declarations (indent=0), we should check alignment
        # For nested declarations, we should skip them from expected position calculation only
        after_equals = display_line[equals_pos + 1:].strip()
        is_object_or_array_decl = after_equals.startswith('[') or after_equals.startswith('{')
        
        # Skip object/array declarations from expected position calculation if they're nested
        # But still check their alignment if they're top-level
        actual_indent = len(line) - len(line.lstrip())
        should_skip_from_expected_calc = is_object_or_array_decl and actual_indent > 0
            
        # Match parameter name, optionally with quotes
        # For quoted params like "format", we need to handle the quotes
        # For unquoted params like type, we just need the name
        if before_equals.strip().startswith('"') or before_equals.strip().startswith("'"):
            param_name_match = re.match(r'^\s*(["\'])([^"\'=\s]+)\1', before_equals)
            if param_name_match:
                param_name = param_name_match.group(2)
            else:
                param_name_match = None
        else:
            param_name_match = re.match(r'^\s*([^"\'=\s]+)', before_equals)
            if param_name_match:
                param_name = param_name_match.group(1)
            else:
                param_name_match = None
        
        if param_name_match:
            # Store original line for later skip checks, but equals_pos based on expanded tabs
            # Also store whether this should be skipped from expected position calculation
            param_data.append((param_name, line, actual_line_num, equals_pos, should_skip_from_expected_calc))
    
    # Single-parameter groups: require compact before '=' (same as .tf). Column alignment N/A.
    if len(param_data) < 2:
        if len(param_data) == 1:
            param_name, line, actual_line_num, equals_pos, _should_skip = param_data[0]
            if '\t' not in line:
                compact_error = _compact_equals_before_spacing_error(
                    actual_line_num, block_type, line, equals_pos
                )
                if compact_error:
                    errors.append(compact_error)
        return errors
    
    # Find longest visual parameter width (name + quotes)
    # First get longest from non-skipped and non-tab parameters (for expected position calculation)
    # Parameters with tabs (ST.004) should not influence expected position
    non_skipped_non_tab_widths = [
        _param_visual_name_width(p[0], p[1], p[3]) for p in param_data
        if not p[4] and '\t' not in p[1]  # p[4] is should_skip, p[1] is line
    ]
    if non_skipped_non_tab_widths:
        longest_param_width = max(non_skipped_non_tab_widths)
        # If we have skipped parameters (object/array declarations) that are significantly longer,
        # use them for alignment calculation
        skipped_params_widths = [
            _param_visual_name_width(p[0], p[1], p[3]) for p in param_data if p[4] and '\t' not in p[1]
        ]
        if skipped_params_widths:
            longest_skipped_width = max(skipped_params_widths)
            if longest_skipped_width > longest_param_width and longest_skipped_width - longest_param_width >= 4:
                longest_param_width = longest_skipped_width
    else:
        # All parameters are skipped or have tabs, use all non-tab params
        non_tab_widths = [_param_visual_name_width(p[0], p[1], p[3]) for p in param_data if '\t' not in p[1]]
        if non_tab_widths:
            longest_param_width = max(non_tab_widths)
        else:
            # All have tabs, use all params
            longest_param_width = max(_param_visual_name_width(p[0], p[1], p[3]) for p in param_data)
    indent_spaces = indent_level * 2
    
    # For tfvars files, check if most parameters are already aligned
    # Exclude tab lines from alignment position counting
    unique_equals_positions = {}
    for param_name, line, actual_line_num, equals_pos, _ in param_data:
        # Skip tab lines from counting (ST.004 issues should not influence alignment expectations)
        if '\t' in line:
            continue
        if equals_pos not in unique_equals_positions:
            unique_equals_positions[equals_pos] = 0
        unique_equals_positions[equals_pos] += 1
    
    # If all params are already aligned at one position, still check spacing after equals
    # and skip lines with tabs (ST.004) - but still check alignment based on longest param
    if len(unique_equals_positions) == 1:
        expected_equals_location = indent_spaces + longest_param_width + 1
        
        # If the aligned position doesn't match the expected position, they need realignment
        aligned_position = list(unique_equals_positions.keys())[0]
        
        # If all parameters are aligned together at a position >= expected, accept it
        # This handles cases where parameters are consistently aligned even if slightly more than minimum
        if aligned_position < expected_equals_location:
            # Parameters are aligned but not to the longest parameter - need realignment
            # Check alignment for all parameters
            for param_name, line, actual_line_num, equals_pos, should_skip in param_data:
                # Skip nested object/array declaration lines from alignment check
                if should_skip:
                    continue
                
                # Skip lines with tabs (ST.004)
                if '\t' in line:
                    continue
                
                if equals_pos != expected_equals_location:
                    quote_chars = _param_name_quote_chars(line, equals_pos)
                    required_spaces_before_equals = (
                        expected_equals_location - indent_spaces - len(param_name) - quote_chars
                    )
                    errors.append((
                        actual_line_num,
                        f"Parameter assignment equals sign not aligned in {block_type}. "
                        f"Expected {required_spaces_before_equals} spaces between parameter name and '=', "
                        f"equals sign should be at column {expected_equals_location + 1}"
                    ))
        elif aligned_position > expected_equals_location:
            # Parameters are aligned but with more spacing than minimum - this is acceptable
            # as long as they're all consistently aligned together
            # No error needed - consistency is maintained
            pass
        
        # Also check spacing after equals for all parameters
        for param_name, line, actual_line_num, equals_pos, should_skip in param_data:
            # Skip nested object/array declaration lines
            if should_skip:
                continue
            
            # Skip lines with tabs (ST.004)
            if '\t' in line:
                continue
            
            # Use the original line to find equals and check spacing
            original_equals_pos = _find_assignment_equals_pos(line)
            if original_equals_pos == -1:
                continue
                
            after_equals = line[original_equals_pos + 1:]
            if len(after_equals) == 0 or not after_equals[0] == ' ':
                errors.append((
                    actual_line_num,
                    f"Parameter assignment should have at least one space after '=' in {block_type}"
                ))
        
        return errors
    
    # Check if there are multiple alignment groups
    # If most parameters are aligned at one position, use that position
    # Note: unique_equals_positions already excludes tab lines, so count only non-tab params
    if unique_equals_positions:
        most_common_pos = max(unique_equals_positions.items(), key=lambda x: x[1])
        most_common_count = most_common_pos[1]
        # Count only non-tab parameters for total_params (to match unique_equals_positions)
        total_params = sum(1 for p in param_data if '\t' not in p[1])
    else:
        # All params have tabs (shouldn't happen, but handle it)
        most_common_pos = (0, 0)
        most_common_count = 0
        total_params = sum(1 for p in param_data if '\t' not in p[1])
        if total_params == 0:
            total_params = len(param_data)
    
    # Calculate expected position based on longest visual parameter width
    # First try to get longest from non-skipped and non-tab parameters
    # Parameters with tabs (ST.004) should not influence expected position
    non_skipped_non_tab_params = [p for p in param_data if not p[4] and '\t' not in p[1]]  # p[4] is should_skip, p[1] is line
    if non_skipped_non_tab_params:
        longest_param_width = max(_param_visual_name_width(p[0], p[1], p[3]) for p in non_skipped_non_tab_params)
        skipped_non_tab_params = [p for p in param_data if p[4] and '\t' not in p[1]]
        if skipped_non_tab_params:
            longest_skipped_width = max(_param_visual_name_width(p[0], p[1], p[3]) for p in skipped_non_tab_params)
            if longest_skipped_width > longest_param_width and longest_skipped_width - longest_param_width >= 4:
                longest_param_width = longest_skipped_width
    else:
        # All parameters are skipped or have tabs, use all non-tab params
        non_tab_params = [p for p in param_data if '\t' not in p[1]]
        if non_tab_params:
            longest_param_width = max(_param_visual_name_width(p[0], p[1], p[3]) for p in non_tab_params)
        else:
            # All have tabs, use all params
            longest_param_width = max(_param_visual_name_width(p[0], p[1], p[3]) for p in param_data)
    # The equals position is: indent + max(visual name width) + 1 space between param and =
    expected_equals_location = indent_spaces + longest_param_width + 1
    
    # If more than half of parameters are already aligned at a specific position,
    # use that position (they're already aligned, so it's valid)
    use_most_common = False
    expected_based_on_longest = indent_spaces + longest_param_width + 1
    
    if most_common_count > total_params / 2 or (total_params == 2 and most_common_count == 2):
        if abs(most_common_pos[0] - expected_based_on_longest) >= 2:
            use_most_common = False
        else:
            expected_equals_location = most_common_pos[0]
            use_most_common = True
        
        if use_most_common:
            for param_name, line, actual_line_num, equals_pos, should_skip in param_data:
                if should_skip:
                    continue
                
                if equals_pos != expected_equals_location:
                    if most_common_count > 1 and equals_pos == most_common_pos[0]:
                        continue
                    
                    if abs(equals_pos - expected_equals_location) <= 1:
                        continue
                    
                    quote_chars = _param_name_quote_chars(line, equals_pos)
                    required_spaces_before_equals = (
                        expected_equals_location - indent_spaces - len(param_name) - quote_chars
                    )
                    if equals_pos < expected_equals_location:
                        errors.append((
                            actual_line_num,
                            f"Parameter assignment equals sign not aligned in {block_type}. "
                            f"Expected {required_spaces_before_equals} spaces between parameter name and '=', "
                            f"equals sign should be at column {expected_equals_location + 1}"
                        ))
                    elif equals_pos > expected_equals_location:
                        errors.append((
                            actual_line_num,
                            f"Parameter assignment equals sign not aligned in {block_type}. "
                            f"Too many spaces before '=', equals sign should be at column {expected_equals_location + 1}"
                        ))
            
            for param_name, line, actual_line_num, equals_pos, should_skip in param_data:
                if should_skip:
                    continue
                
                after_equals = line[equals_pos + 1:]
                if len(after_equals) == 0 or not after_equals[0] == ' ':
                    errors.append((
                        actual_line_num,
                        f"Parameter assignment should have at least one space after '=' in {block_type}"
                    ))
            
            return errors
    
    # Calculate expected equals location based on longest visual parameter width
    expected_equals_location_base = indent_spaces + longest_param_width + 1
    
    # If we already determined to use most common position, keep it
    # Otherwise use the base calculation
    if not use_most_common:
        expected_equals_location = expected_equals_location_base
    
    # Check alignment for each parameter
    for param_name, line, actual_line_num, equals_pos, should_skip in param_data:
        # Skip alignment check for nested object/array declaration lines
        if should_skip:
            continue
        
        # Skip alignment check if equals position matches expected location
        if equals_pos == expected_equals_location:
            continue
        
        # If most params are already aligned, respect that alignment
        if use_most_common:
            if equals_pos == most_common_pos[0]:
                # This parameter is aligned with the majority, skip check
                continue
        
        # Skip emitting alignment error on lines with tabs (ST.004), but still allow them to influence expected position
        if '\t' in line:
            continue

        # Check if indentation is incorrect
        actual_indent = len(line) - len(line.lstrip())
        if actual_indent % 2 != 0:
            continue
        
        # For parameters with quotes, add quote characters to length
        param_display_length = len(param_name)
        before_eq_for_quote = _get_before_assignment_equals(line)
        if before_eq_for_quote.strip().startswith('"') or before_eq_for_quote.strip().startswith("'"):
            param_display_length += 2  # Add quotes length
        
        # Check if this parameter is already aligned with at least 2 other NON-TAB parameters
        # Tab lines (ST.004) should not count for alignment - we only want to skip if aligned with valid parameters
        # However, we should only skip if the alignment position matches the expected location
        # or if it matches the most_common position and the difference from expected is small
        non_tab_aligned_count = sum(1 for p in param_data if p[3] == equals_pos and '\t' not in p[1])
        if non_tab_aligned_count >= 2:
            # Check if this alignment position is acceptable
            # If it matches expected location, or matches most_common and is close to expected, skip
            if equals_pos == expected_equals_location:
                # Aligned at expected location, skip
                continue
            elif use_most_common and equals_pos == most_common_pos[0]:
                # Aligned with most_common and we're using most_common, skip
                continue
            elif abs(equals_pos - expected_equals_location) <= 1:
                # Close to expected location (within 1 column), skip
                continue
            # Check if this parameter is aligned with the majority position
            # If most parameters are already aligned at a different position (most_common_pos),
            # and this parameter is at that position, skip the check
            # This handles cases where multiple parameters form a valid alignment group,
            # but the expected position is based on an object declaration in a different context
            # However, don't skip if this parameter should align with an object declaration
            # (i.e., if it's immediately followed by an object declaration parameter)
            # IMPORTANT: Only skip if this position is actually the most common position (has the most parameters)
            # AND the most common count is significantly more than other positions
            # This prevents small groups (like 2 parameters) from incorrectly skipping alignment checks
            elif not use_most_common and unique_equals_positions and equals_pos == most_common_pos[0]:
                # Only skip if the most common position has significantly more parameters than this position
                # This ensures that small alignment groups don't incorrectly skip checks
                # For example, if 5 params are at position 23 and 2 params are at position 17,
                # the 2 params at position 17 should still be checked for alignment
                # However, if this position IS the most common position, we should still check alignment
                # unless it matches the expected location or is close to it
                # So we should NOT skip if this position is the most common but doesn't match expected
                # Actually, if this position is the most common but doesn't match expected, we should report an error
                # So we should only skip if this position matches expected or is close to it
                # IMPORTANT: If the difference between equals_pos and expected_equals_location is > 1,
                # we should NOT skip, even if this position is the most common, because it's clearly misaligned
                # Also, if most_common_count is not significantly more than non_tab_aligned_count (i.e., they're equal),
                # we should NOT skip, because this means the current parameter is part of a small group that should be checked
                if most_common_count > non_tab_aligned_count and (equals_pos == expected_equals_location or abs(equals_pos - expected_equals_location) <= 1):
                    # Most common position has more parameters than this position, skip check
                    # Check if this parameter should align with an object declaration
                    # Find the index of current parameter in param_data
                    current_idx = None
                    for idx, (_, _, ln, _, _) in enumerate(param_data):
                        if ln == actual_line_num:
                            current_idx = idx
                            break
                    
                    # Check if next parameter is an object declaration and should be used for alignment
                    should_align_with_next_decl = False
                    if current_idx is not None and current_idx + 1 < len(param_data):
                        next_param = param_data[current_idx + 1]
                        if next_param[4]:  # next_param[4] is should_skip (object declaration)
                            # Check if there's a blank line between current and next parameter
                            # Find the line numbers from group_lines
                            next_line_num = next_param[2]  # next_param[2] is actual_line_num
                            current_line_num = actual_line_num
                            
                            # If line numbers differ by more than 1, there might be blank lines
                            # But we need to check group_lines to see the actual lines
                            # For now, if next_line_num - current_line_num == 1, they're adjacent
                            if next_line_num - current_line_num == 1:
                                # Adjacent lines, check if object declaration length was used for expected position
                                skipped_params_len = [len(p[0]) for p in param_data if p[4] and '\t' not in p[1]]
                                if skipped_params_len:
                                    longest_skipped_len = max(skipped_params_len)
                                    non_skipped_params = [p for p in param_data if not p[4] and '\t' not in p[1]]
                                    non_skipped_len = max(len(p[0]) for p in non_skipped_params) if non_skipped_params else 0
                                    if longest_skipped_len > non_skipped_len and longest_skipped_len - non_skipped_len >= 4:
                                        # Object declaration length was used, and this param is immediately before it
                                        should_align_with_next_decl = True
                            # If line numbers differ by more than 1, they're not adjacent, don't align
                    
                    if not should_align_with_next_decl:
                        # Most parameters are aligned at a position different from expected
                        # This parameter is aligned with the majority, skip check
                        continue
                    # Otherwise, should align with next declaration, continue to report error
                # If the condition above is not met (i.e., equals_pos differs from expected by more than 1),
                # fall through to report the error below
            # If none of the skip conditions are met, this parameter is aligned incorrectly
            # with other parameters but not at the expected location - report the error
        
        required_spaces_before_equals = expected_equals_location - indent_spaces - param_display_length
        
        if equals_pos < expected_equals_location:
            errors.append((
                actual_line_num,
                f"Parameter assignment equals sign not aligned in {block_type}. "
                f"Expected {required_spaces_before_equals} spaces between parameter name and '=', "
                f"equals sign should be at column {expected_equals_location + 1}"
            ))
        elif equals_pos > expected_equals_location:
            errors.append((
                actual_line_num,
                f"Parameter assignment equals sign not aligned in {block_type}. "
                f"Too many spaces before '=', equals sign should be at column {expected_equals_location + 1}"
            ))
    
    return errors


def _check_parameter_spacing_tfvars(line: str, actual_line_num: int, block_type: str) -> List[Tuple[int, str]]:
    """Check spacing around equals sign for tfvars, using actual line number."""
    errors = []
    equals_pos = _find_assignment_equals_pos(line)
    
    if equals_pos == -1:
        return errors
    
    # Check space before equals
    before_equals_raw = line[:equals_pos]
    if not before_equals_raw.strip() or not before_equals_raw.endswith(' '):
        errors.append((
            actual_line_num,
            f"Parameter assignment should have at least one space before '=' in {block_type}"
        ))
    
    # Check space after equals
    after_equals = line[equals_pos + 1:]
    if len(after_equals) == 0 or not after_equals[0] == ' ':
        errors.append((
            actual_line_num,
            f"Parameter assignment should have at least one space after '=' in {block_type}"
        ))
    elif len(after_equals) > 1 and after_equals[:2] == '  ':
        errors.append((
            actual_line_num,
            f"Parameter assignment should have exactly one space after '=' in {block_type}, found multiple spaces"
        ))
    
    return errors


def _is_inside_block_structure_tfvars(current_line: str, all_lines: List[str], current_line_num: int) -> bool:
    """
    Check if the current line is inside a block structure in terraform.tfvars files.
    
    This is similar to the function in rule_005.py but adapted for .tfvars files.
    
    Args:
        current_line (str): The current line being checked
        all_lines (List[str]): All lines in the file
        current_line_num (int): Current line number (1-indexed)
        
    Returns:
        bool: True if the line is inside a block structure, False otherwise
    """
    # Check if this line is inside a block structure (including lines with =, {, or })
    if ((_has_assignment_equals(current_line.strip()) or current_line.strip().startswith('{') or current_line.strip().startswith('}')) 
        and not current_line.strip().startswith('#')):
        # Look backwards to see if we're inside a block structure
        brace_count = 0
        bracket_count = 0
        
        for i in range(current_line_num - 2, -1, -1):  # Start from 2 lines before current
            if i >= len(all_lines):
                continue
                
            line = all_lines[i].strip()
            if not line:
                continue
                
            # Count braces and brackets to track block structure
            for char in line:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                elif char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
            
            # If we have unmatched opening braces/brackets, we're inside a block
            if brace_count > 0 or bracket_count > 0:
                return True
                
            # If we find a line that ends with { or [, check if it's part of a block structure
            if line.endswith('{') or line.endswith('['):
                # Check if this is a block structure (not just a simple assignment)
                if _has_assignment_equals(line) and ('{' in line or '[' in line):
                    return True
                break
        return False
    else:
        return False


