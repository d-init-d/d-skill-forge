---
name: regex-puzzles-skill
description: Construct correct regular expressions for common text matching and validation challenges.
version: 0.1.0
source_model: mock-strong
extracted_from:
  total_traces: 10
  passed_traces: 10
  failed_traces: 0
  extractor: manual@0.1
  extracted_at: '2026-01-01T00:00:00Z'
triggers:
  - regex
  - pattern
  - match
  - validate
domains:
  - regex-puzzles
license: Apache-2.0
---

## When to use

Apply this skill when you need to construct or debug a regular expression for text matching, validation, or extraction. Covers: IPv4 addresses, email validation, phone extraction, password strength lookaheads, non-greedy quantifiers, named groups, backreferences, negated character classes, anchors, and Unicode properties.

## Procedure

1. Identify what needs to be matched — literal text, patterns, or structure
2. Choose anchoring strategy — full-string match (^...$) vs substring search
3. Build the pattern incrementally from left to right
4. Use character classes for sets of allowed characters
5. Apply quantifiers (*, +, {n,m}) with greedy/non-greedy as needed
6. Use groups for capturing and backreferences
7. Add lookaheads/lookbehinds for zero-width assertions
8. Test against both matching and non-matching inputs
9. Consider edge cases: empty strings, Unicode, special characters

### Pattern recipes

- **IPv4**: Match each octet as `(25[0-5]|2[0-4]\d|[01]?\d\d?)` separated by `\.`
- **Email**: Use `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
- **Phone**: Account for optional parens and separators: `\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}`
- **Password lookahead**: Chain `(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%])` before `.{8,}`
- **Non-greedy**: Use `.*?` instead of `.*` to match shortest possible
- **Named groups**: Use `(?P<name>...)` syntax for readable captures
- **Backreference**: Capture with `(\w+)` then match repeat with `\1`
- **Negation**: Use `[^...]` to exclude characters from a class
- **Anchors**: Use `^` and `$` (with multiline flag if needed)
- **Unicode**: Use `\p{L}` for any Unicode letter

## Examples

### match-ipv4-address

Pattern: `^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$`

### password-lookahead

Pattern: `^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$`

### backreference-repeated-word

Pattern: `\b(\w+)\s+\1\b`

## Anti-patterns

- Do not use `.*` when you mean `.*?` — greedy matching causes over-capture
- Do not forget to escape literal dots — `.` matches any character without escaping
- Do not nest quantifiers without bounds (e.g., `(a+)+`) — causes catastrophic backtracking
- Do not use regex for full HTML/XML parsing — use a proper parser instead
- Do not assume ASCII-only input — use Unicode-aware patterns when appropriate
