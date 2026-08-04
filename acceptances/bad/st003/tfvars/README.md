# ST.003 Bad Examples - terraform.tfvars Scripts

This directory contains test cases demonstrating ST.003 rule violations in `terraform.tfvars` files. These examples are used to validate that the ST.003 rule correctly identifies parameter alignment issues.

## Purpose

The ST.003 rule checks that parameter assignment equals signs are properly aligned within the same section in `terraform.tfvars` files. This directory contains examples of common misalignment scenarios that should be detected as errors.

## Test Cases

### case1

This case demonstrates **4 ST.003 errors** related to top-level parameter alignment:

**Errors:**
1. **Line 37**: `response_rules = [` - Equals sign not aligned. Expected at column 24 (9 spaces before '='), but actual alignment is incorrect.
2. **Line 45**: `api_name         = "tf_test_apig_api_auth"` - Equals sign not aligned. Expected at column 24 (15 spaces before '='), but actual alignment is incorrect.
3. **Line 47**: `api_request_path = "/backend/users"` - Equals sign not aligned. Expected at column 24 (7 spaces before '='), but actual alignment is incorrect.
4. **Line 49**: `api_backend_params = [` - Equals sign not aligned. Expected at column 24 (5 spaces before '='), but actual alignment is incorrect.

**Issue Description:**
The top-level parameters from lines 1-35 are correctly aligned at column 24. However, after the `response_rules` array declaration (lines 37-43), the subsequent top-level parameters (lines 45, 47, 49) are not aligned with the previous parameters. They should all align at column 24 to maintain consistency.

**Expected Behavior:**
All top-level parameters should be aligned at the same column position (column 24 in this case), even if they are separated by array or object declarations.

### single-padded-before

Single-parameter group with more than one space before `=` (should report compact spacing).

## Running Tests

To verify the ST.003 rule detects these errors, run:

```bash
python3.10 .github/scripts/terraform_lint.py \
  --directory acceptances/bad/st003/tfvars/case1 \
  --ignore-rules "ST.001,ST.002,ST.004,ST.005,ST.006,ST.007,ST.008,ST.009,ST.010,ST.011,ST.012,ST.013,ST.014,DC.001,IO.001,IO.002,IO.003,IO.004,IO.005,IO.006,IO.007,IO.008,IO.009,IO.010,IO.013,SC.001,SC.002,SC.003,SC.004,SC.005,SC.006,SC.007" \
  | grep "ERROR"
```

**Expected Output:**
The command should report exactly **4 errors** for `case1/terraform.tfvars`.
