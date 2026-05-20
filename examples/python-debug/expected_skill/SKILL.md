---
name: python-debug
description: Debug common Python runtime errors by reading tracebacks and applying targeted fixes.
version: 0.1.0
source_model: claude-opus-4
extracted_from:
  total_traces: 15
  passed_traces: 13
  failed_traces: 2
  extractor: reflective@0.1
  extracted_at: '2024-06-01T00:00:00+00:00'
triggers:
  - traceback
  - error
  - exception
  - TypeError
  - AttributeError
  - KeyError
  - IndexError
domains:
  - python
  - debugging
license: Apache-2.0
---

## When to use

Apply this skill when you encounter a Python runtime error (traceback) and need to identify the root cause and produce a minimal fix. Covers: TypeError, AttributeError, KeyError, IndexError, ImportError, ValueError, RecursionError, async misuse, off-by-one errors, and mutable default arguments.

## Procedure

1. Read the traceback bottom-to-top: identify the exception type and message
2. Locate the failing line and its immediate context
3. Classify the error into one of the known patterns below
4. Apply the corresponding fix pattern
5. Verify the fix handles edge cases (None values, empty collections, boundary indices)

### Fix patterns

- **TypeError (concat)**: Use `str()` or f-string to convert non-string operands
- **TypeError (None operation)**: Add a guard or provide a default return value
- **AttributeError (None)**: Add `if x is not None` guard or use `getattr(x, attr, default)`
- **AttributeError (typo)**: Correct the method/attribute name spelling
- **KeyError**: Use `dict.get(key, default)` instead of direct access
- **IndexError (empty)**: Check `if collection` before indexing
- **IndexError (off-by-one)**: Use `len(x) - 1` or adjust range bounds
- **ImportError**: Correct the import name casing/spelling
- **ValueError (parse)**: Wrap in try/except with a fallback value
- **ValueError (unpack)**: Match the number of variables to the tuple length
- **Mutable default**: Use `None` as default, assign inside the function body
- **Async (missing await)**: Add `await` before coroutine calls
- **Off-by-one (range)**: Use `range(start, end + 1)` for inclusive upper bound
- **RecursionError**: Add a base case that returns without recursing

## Examples

### fix-type-error-concat

Input: `result = "count: " + 42`
Fix: `result = "count: " + str(42)`

### fix-key-error-missing

Input: `user['role']` when key doesn't exist
Fix: `user.get('role', 'unknown')`

### fix-mutable-default

Input: `def add_item(item, lst=[])`
Fix: `def add_item(item, lst=None): lst = lst if lst is not None else []`

## Anti-patterns

- Do not catch broad `Exception` without re-raising or logging
- Do not use `type(x) == T` when `isinstance(x, T)` is appropriate
- Do not silence errors with empty `except: pass` blocks
- Do not add defensive checks everywhere — fix the root cause instead
- Do not use `hasattr` as a substitute for understanding the data model
