#!/usr/bin/env python3
"""
ST.008 - Meta-parameter Spacing Check

This module implements the ST.008 rule which validates that meta-parameters
(count, for_each, provider, lifecycle, depends_on) maintain proper spacing 
with other code elements within Terraform resource and data source blocks.

Rule Specification:
1. Meta-parameters must have exactly 1 blank line between them and other parameters
2. Meta-parameters must have exactly 1 blank line between each other
3. If meta-parameter is the first line in a block, it must not have blank lines before it
4. Reports specific line numbers for violations

Meta-parameters include:
- count: Resource/data source iteration based on conditions
- for_each: Resource/data source iteration based on collections
- provider: Non-default provider specification
- lifecycle: Lifecycle management settings
- depends_on: Resource dependencies

Examples:
    Valid spacing:
        resource "huaweicloud_compute_instance" "test" {
          count = var.instance_count > 0 ? 1 : 0

          name = var.instance_name
          image_id = var.image_id

          depends_on = [huaweicloud_vpc.test]
        }

    Invalid spacing:
        resource "huaweicloud_compute_instance" "test" {
          count = var.instance_count > 0 ? 1 : 0
          name = var.instance_name  # Missing blank line after count
          image_id = var.image_id

          depends_on = [huaweicloud_vpc.test]
        }

Author: Lance
License: Apache 2.0
"""

import re
from typing import Callable, List, Tuple, Dict, Optional

from rules.st_rules.rule_003 import _is_inside_dynamic_block


def check_st008_count_depends_on_spacing(file_path: str, content: str, log_error_func: Callable[[str, str, str, Optional[int]], None]) -> None:
    """
    Validate meta-parameter spacing according to ST.008 rule specifications.

    This function scans through the provided Terraform file content and validates
    that meta-parameters (count, for_each, provider, lifecycle, depends_on) maintain 
    proper spacing with other code elements within resource and data source blocks.

    The validation process:
    1. Parse content to identify all resource and data source blocks
    2. Within each block, identify all meta-parameters
    3. Check spacing rules:
        - Meta-parameters: exactly 1 blank line before and after (except when first)
        - Meta-parameters together: exactly 1 blank line between them
        - First meta-parameter: no blank lines before it
    4. Report violations through the error logging function

    Args:
        file_path (str): The path to the file being checked
        content (str): The complete content of the Terraform file
        log_error_func (Callable): Function to report rule violations

    Returns:
        None: Reports errors through the log_error_func callback
    """
    resource_blocks = _extract_resource_blocks_with_meta_parameters(content)
    
    for resource_info in resource_blocks:
        resource_name = resource_info['name']
        parameters = resource_info['parameters']
        
        # Check spacing for count and depends_on parameters
        spacing_errors = _check_meta_parameter_spacing(
            parameters, resource_name, content
        )
        
        for error_msg, line_num in spacing_errors:
            log_error_func(file_path, "ST.008", error_msg, line_num)


def _extract_resource_blocks_with_meta_parameters(content: str) -> List[Dict]:
    """
    Extract all resource and data source blocks with their parameters.

    Args:
        content (str): The Terraform file content

    Returns:
        List[Dict]: List of resource information with parameters
    """
    lines = content.split('\n')
    resources = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Match resource or data blocks (support quoted, single-quoted, and unquoted syntax)
        resource_match = re.match(r'(resource|data)\s+(?:"([^"]+)"|\'([^\']+)\'|([a-zA-Z_][a-zA-Z0-9_]*))\s+(?:"([^"]+)"|\'([^\']+)\'|([a-zA-Z_][a-zA-Z0-9_]*))\s*\{', line)
        
        if resource_match:
            block_type = resource_match.group(1)
            # Extract resource type (quoted, single-quoted, or unquoted)
            resource_type = resource_match.group(2) if resource_match.group(2) else (resource_match.group(3) if resource_match.group(3) else resource_match.group(4))
            # Extract resource name (quoted, single-quoted, or unquoted)
            resource_name = resource_match.group(5) if resource_match.group(5) else (resource_match.group(6) if resource_match.group(6) else resource_match.group(7))
            full_name = f'{block_type} "{resource_type}" "{resource_name}"'
            
            resource_start = i + 1
            
            # Count braces in the resource declaration line first
            brace_count = line.count('{') - line.count('}')
            i += 1
            
            # Find the end of the resource block
            resource_end = i
            while i < len(lines) and brace_count > 0:
                current_line = lines[i]
                brace_count += current_line.count('{') - current_line.count('}')
                i += 1
                resource_end = i  # Always update to include the current line
            
            # Extract parameters within this resource
            parameters = _extract_parameters_from_resource(
                lines[resource_start-1:resource_end], resource_start
            )
            
            resources.append({
                'name': full_name,
                'start_line': resource_start,
                'end_line': resource_end,
                'parameters': parameters
            })
        else:
            i += 1
    
    return resources


def _extract_parameters_from_resource(resource_lines: List[str], resource_start_line: int) -> List[Dict]:
    """
    Extract all parameters from within a resource, focusing on meta-parameters.

    Args:
        resource_lines (List[str]): Lines of the resource block
        resource_start_line (int): Starting line number of the resource

    Returns:
        List[Dict]: List of parameter information
    """
    parameters = []
    
    # Define meta-parameters
    meta_parameters = ['count', 'for_each', 'provider', 'lifecycle', 'depends_on']
    
    # Simple approach: scan each line for all parameters
    i = 1  # Skip the resource declaration line
    while i < len(resource_lines):
        line = resource_lines[i].strip()
        
        if not line or line.startswith('#'):
            i += 1
            continue
        
        # Check for other meta-parameters (simple assignments)
        meta_param_found = False
        for meta_param in ['count', 'for_each', 'provider', 'depends_on']:
            meta_match = re.match(f'{meta_param}\\s*=', line)
            if meta_match:
                # Special case: for_each inside dynamic blocks should not be treated as meta-parameter
                if meta_param == 'for_each' and _is_inside_dynamic_block(i, resource_lines):
                    # Still add it as a parameter but mark it as dynamic-internal
                    param_line = resource_start_line + i
                    parameters.append({
                        'type': 'dynamic_internal',
                        'name': meta_param,
                        'start_line': param_line,
                        'end_line': param_line
                    })
                    meta_param_found = True
                    break
                
                param_line = resource_start_line + i
                parameters.append({
                    'type': 'meta',
                    'name': meta_param,
                    'start_line': param_line,
                    'end_line': param_line
                })
                meta_param_found = True
                break
        
        # If not a meta-parameter, check for other parameters (for spacing context)
        if not meta_param_found:
            # Check for structure blocks (like content {, lifecycle {, etc.)
            block_match = re.match(r'(\w+)\s*\{', line)
            if block_match:
                param_name = block_match.group(1)
                param_line = resource_start_line + i
                # Find the end of this structure block
                brace_count = 1
                j = i + 1
                while j < len(resource_lines) and brace_count > 0:
                    current_line = resource_lines[j]
                    brace_count += current_line.count('{') - current_line.count('}')
                    j += 1
                block_end = resource_start_line + j - 1
                
                # Determine the type of structure block
                if param_name in ['lifecycle', 'content']:
                    # These are meta-parameter blocks
                    parameters.append({
                        'type': 'meta',
                        'name': param_name,
                        'start_line': param_line,
                        'end_line': block_end
                    })
                else:
                    # Other structure blocks
                    parameters.append({
                        'type': 'structure',
                        'name': param_name,
                        'start_line': param_line,
                        'end_line': block_end
                    })
                
                # Skip all lines inside this block
                i = j  # Skip to the line after the block
                continue  # Continue to next iteration of the while loop
            else:
                # Check for simple parameter assignments (only at top level, not inside blocks)
                param_match = re.match(r'(\w+)\s*=', line)
                if param_match:
                    param_name = param_match.group(1)
                    param_line = resource_start_line + i
                    parameters.append({
                        'type': 'other',
                        'name': param_name,
                        'start_line': param_line,
                        'end_line': param_line
                    })
        
        i += 1
    
    return parameters


def _check_meta_parameter_spacing(parameters: List[Dict], resource_name: str, content: str) -> List[Tuple[str, Optional[int]]]:
    """
    Check spacing rules for meta-parameters.

    Args:
        parameters (List[Dict]): List of parameters in order
        resource_name (str): The resource containing these parameters
        content (str): The full file content

    Returns:
        List[Tuple[str, Optional[int]]]: List of error messages and optional line numbers
    """
    errors = []
    lines = content.split('\n')
    
    # Filter for meta-parameters and dynamic-internal parameters
    meta_params = [p for p in parameters if p['type'] in ['meta', 'dynamic_internal']]
    
    if not meta_params:
        return errors  # No meta-parameters to check
    
    # Sort all parameters by their start line
    all_params = sorted(parameters, key=lambda x: x['start_line'])
    
    # Check spacing around each parameter
    for i, param in enumerate(all_params):
        # Only check meta-parameters and dynamic-internal parameters
        if param['type'] not in ['meta', 'dynamic_internal']:
            continue
        param_line = param['start_line'] - 1  # Convert to 0-based indexing
        
        # Find the previous parameter
        prev_param = None
        for j in range(i):
            if all_params[j]['start_line'] < param['start_line']:
                prev_param = all_params[j]
        
        # Check if this is the first parameter in the block
        is_first_param = prev_param is None
        
        # Check spacing with previous parameter
        if prev_param:
            # Special case: dynamic-internal for_each should not check spacing with previous parameters
            if param['type'] == 'dynamic_internal' and param['name'] == 'for_each':
                # Skip spacing check with previous parameter for dynamic-internal for_each
                pass
            else:
                prev_end = prev_param['end_line'] - 1  # Convert to 0-based indexing
                blank_lines = _count_blank_lines_between(lines, prev_end, param_line)
                
                # Check spacing rules based on parameter types
                if blank_lines != 1:
                    error_msg = _generate_spacing_error(
                        prev_param, param, blank_lines, resource_name, "before"
                    )
                    if error_msg:
                        errors.append((error_msg, param['start_line']))
        
        # Check spacing with next parameter (for meta-parameters)
        if param['type'] in ['meta', 'dynamic_internal']:
            # Find the next parameter
            next_param = None
            for j in range(i + 1, len(all_params)):
                if all_params[j]['start_line'] > param['start_line']:
                    next_param = all_params[j]
                    break
            
            if next_param:
                # Check if there are other meta-parameters between this meta-parameter and the next parameter
                has_other_meta_between = False
                for j in range(i + 1, len(all_params)):
                    if all_params[j]['start_line'] > param['start_line'] and all_params[j]['start_line'] < next_param['start_line']:
                        if all_params[j]['type'] in ['meta', 'dynamic_internal']:
                            has_other_meta_between = True
                            break
                
                # Only check spacing with non-meta parameters if there are no other meta-parameters between
                if not has_other_meta_between and next_param['type'] == 'other':
                    param_end = param['end_line'] - 1  # Convert to 0-based indexing
                    next_line = next_param['start_line'] - 1  # Convert to 0-based indexing
                    blank_lines = _count_blank_lines_between(lines, param_end, next_line)
                    
                    if blank_lines != 1:
                        error_msg = _generate_spacing_error(
                            param, next_param, blank_lines, resource_name, "after"
                        )
                        if error_msg:
                            errors.append((error_msg, next_param['start_line']))
        
        # Check if there are blank lines before the first meta-parameter
        if is_first_param and param['type'] == 'meta':
            # Find the resource start line (the line with the opening brace)
            resource_start_line = None
            for line_idx in range(param['start_line'] - 1, max(0, param['start_line'] - 10), -1):
                if line_idx < len(lines):
                    line = lines[line_idx].strip()
                    if '{' in line and ('resource' in line or 'data' in line):
                        resource_start_line = line_idx
                        break
            
            if resource_start_line is not None:
                blank_lines_before = _count_blank_lines_before_first_param(lines, resource_start_line)
                
                if blank_lines_before > 0:
                    error_msg = f"There is a blank line definition ahead of the {param['name']} meta-parameter in {resource_name}"
                    errors.append((error_msg, param['start_line']))
    
    return errors


def _count_blank_lines_between(lines: List[str], start_idx: int, end_idx: int) -> int:
    """
    Count blank lines between two line indices.

    Args:
        lines (List[str]): File lines
        start_idx (int): Start line index (0-based)
        end_idx (int): End line index (0-based)

    Returns:
        int: Number of blank lines between the indices
    """
    blank_lines = 0
    for line_idx in range(start_idx + 1, end_idx):
        if line_idx < len(lines):
            line_content = lines[line_idx].strip()
            if line_content == '':
                blank_lines += 1
            elif line_content.startswith('#'):
                # Comment lines don't count as blank lines but also don't reset the count
                continue
            else:
                # If there's any non-comment, non-blank content, reset blank line count
                blank_lines = 0
    
    return blank_lines


def _count_blank_lines_before_first_param(lines: List[str], resource_start_line: int) -> int:
    """
    Count blank lines before the first parameter in a resource block.

    Args:
        lines (List[str]): File lines
        resource_start_line (int): Resource start line index (0-based)

    Returns:
        int: Number of blank lines before first parameter
    """
    blank_lines = 0
    start_idx = resource_start_line + 1
    
    # Safety check to prevent infinite loops
    if start_idx >= len(lines):
        return 0
    
    for line_idx in range(start_idx, min(start_idx + 100, len(lines))):  # Limit to 100 lines max
        if line_idx >= len(lines):
            break
            
        line = lines[line_idx].strip()
        if line == '':
            blank_lines += 1
        elif line.startswith('#'):
            # Comment lines don't count as blank lines but also don't reset the count
            continue
        else:
            # Found first non-empty non-comment line
            break
    
    return blank_lines


def _generate_spacing_error(param1: Dict, param2: Dict, blank_lines: int, resource_name: str, position: str) -> Optional[str]:
    """
    Generate error message for spacing violations.

    Args:
        param1 (Dict): First parameter
        param2 (Dict): Second parameter
        blank_lines (int): Number of blank lines found
        resource_name (str): The resource name
        position (str): "before" or "after" to indicate position

    Returns:
        Optional[str]: Error message if violation found, None otherwise
    """
    # Only check spacing for meta-parameters and dynamic-internal parameters
    if param1['type'] not in ['meta', 'dynamic_internal'] and param2['type'] not in ['meta', 'dynamic_internal']:
        return None
    
    # Determine which parameter is the meta parameter
    if param1['type'] in ['meta', 'dynamic_internal']:
        meta_param = param1
        other_param = param2
    else:
        meta_param = param2
        other_param = param1
    
    if blank_lines == 0:
        if position == "before":
            if other_param['type'] in ['meta', 'dynamic_internal']:
                return f"There is no blank line between the {other_param['name']} meta-parameter and {meta_param['name']} meta-parameter"
            else:
                return f"There is no blank line between the {meta_param['name']} meta-parameter and other parameters"
        else:
            return f"There is no blank line between the {meta_param['name']} meta-parameter and other parameters"
    elif blank_lines > 1:
        if position == "before":
            if other_param['type'] in ['meta', 'dynamic_internal']:
                return f"There are too many blank lines between the {other_param['name']} meta-parameter and {meta_param['name']} meta-parameter"
            else:
                return f"There are too many blank lines between the {meta_param['name']} meta-parameter and other parameters"
        else:
            return f"There are too many blank lines between the {meta_param['name']} meta-parameter and other parameters"
    
    return None


def get_rule_description() -> dict:
    """
    Retrieve detailed information about the ST.008 rule.

    Returns:
        dict: A dictionary containing comprehensive rule information
    """
    return {
        "id": "ST.008",
        "name": "Meta-parameter spacing check",
        "description": (
            "Validates that meta-parameters (count, for_each, provider, lifecycle, depends_on) "
            "maintain proper spacing with other code elements within Terraform resource and "
            "data source blocks. This ensures consistent visual separation and improved readability."
        ),
        "category": "Style/Format",
        "severity": "error",
        "rationale": (
            "Proper spacing around meta-parameters improves code readability by creating "
            "clear visual separation between meta-parameters and regular resource parameters. "
            "This makes it easier to identify conditional resource creation, dependencies, "
            "and lifecycle management at a glance."
        ),
        "examples": {
            "valid": [
                '''
resource "huaweicloud_compute_instance" "test" {
  count = var.instance_count > 0 ? 1 : 0

  name = var.instance_name
  image_id = var.image_id

  depends_on = [huaweicloud_vpc.test]
}
''',
                '''
resource "huaweicloud_vpc" "test" {
  for_each = var.vpc_configurations

  name = each.value.name
  cidr = each.value.cidr

  provider = huaweicloud.region1

  lifecycle {
    create_before_destroy = true
  }
}
'''
            ],
            "invalid": [
                '''
resource "huaweicloud_compute_instance" "test" {
  count = var.instance_count > 0 ? 1 : 0
  name = var.instance_name  # Missing blank line after count
  image_id = var.image_id

  depends_on = [huaweicloud_vpc.test]
}
''',
                '''
resource "huaweicloud_vpc" "test" {
  name = var.vpc_name
  count = var.create_vpc ? 1 : 0  # Missing blank line before count
  depends_on = [huaweicloud_availability_zones.test]  # Missing blank line between count and depends_on
}
'''
            ]
        },
        "auto_fixable": True,
        "performance_impact": "minimal",
        "related_rules": ["ST.006", "ST.007"],
        "configuration": {
            "required_blank_lines_around_meta_parameters": 1,
            "required_blank_lines_between_meta_parameters": 1,
            "no_blank_lines_before_first_meta_parameter": True
        }
    }