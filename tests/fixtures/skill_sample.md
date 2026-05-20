---
name: python-debug
description: Debug common Python runtime errors
version: 0.1.0
source_model: claude-opus-4
extracted_from:
  total_traces: 10
  passed_traces: 8
  failed_traces: 2
  extractor: reflective@0.1
  extracted_at: '2024-01-15T10:00:00+00:00'
triggers:
  - error
  - traceback
  - exception
domains:
  - python
  - debugging
license: Apache-2.0
---

## When to use

Apply this skill when debugging Python runtime errors including TypeError,
AttributeError, KeyError, and IndexError.

## Procedure

1. Read the full traceback from bottom to top
2. Identify the exception type and message
3. Locate the failing line in context
4. Check variable types and values at the failure point
5. Apply the appropriate fix pattern

## Examples

### task_id: fix-type-error-concat

Input: `result = "count: " + 42`
Fix: `result = "count: " + str(42)`

## Anti-patterns

- Do not catch broad exceptions without re-raising
- Do not use `type()` checks when `isinstance()` is appropriate
- Do not silence errors with empty except blocks
