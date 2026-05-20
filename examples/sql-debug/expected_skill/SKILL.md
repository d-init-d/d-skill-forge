---
name: sql-debug-skill
description: Debug common SQL query errors by identifying anti-patterns and applying targeted fixes.
version: 0.1.0
source_model: mock-strong
extracted_from:
  total_traces: 10
  passed_traces: 10
  failed_traces: 0
  extractor: manual@0.1
  extracted_at: '2026-01-01T00:00:00Z'
triggers:
  - sql
  - debug
  - query
  - fix
domains:
  - sql-debug
license: Apache-2.0
---

## When to use

Apply this skill when you encounter a SQL query that produces incorrect results, errors, or unintended side effects. Covers: missing JOINs, NULL comparisons, GROUP BY misuse, ambiguous columns, integer division, clause ordering, missing WHERE, implicit column lists, COUNT semantics, and correlated subqueries.

## Procedure

1. Read the query and identify which tables and columns are referenced
2. Check JOIN conditions — ensure all referenced tables are properly joined
3. Check NULL handling — use IS NULL / IS NOT NULL instead of = NULL
4. Check GROUP BY — all non-aggregated SELECT columns must appear in GROUP BY
5. Check column ambiguity — qualify columns with table aliases when joining
6. Check arithmetic — cast integers before division to avoid truncation
7. Check clause order — ORDER BY must come before LIMIT
8. Check safety — UPDATE/DELETE must have WHERE unless intentionally affecting all rows
9. Check INSERT — always specify explicit column lists
10. Check COUNT — use COUNT(*) for row counts, COUNT(col) only to exclude NULLs intentionally
11. Check subqueries — ensure correlated subqueries reference the correct outer alias

### Fix patterns

- **Missing JOIN**: Add explicit JOIN with ON condition linking the tables
- **NULL comparison**: Replace `= NULL` with `IS NULL` and `!= NULL` with `IS NOT NULL`
- **GROUP BY**: Add missing columns to GROUP BY or wrap them in an aggregate function
- **Ambiguous column**: Prefix with table alias (e.g., `users.id` instead of `id`)
- **Integer division**: Use `CAST(col AS DECIMAL)` or multiply by `1.0`
- **Clause order**: Move ORDER BY before LIMIT
- **Missing WHERE**: Add a WHERE clause to restrict affected rows
- **INSERT columns**: Add explicit column list after table name
- **COUNT semantics**: Use `COUNT(*)` when counting all rows
- **Subquery correlation**: Reference the outer query alias in the subquery WHERE clause

## Examples

### fix-missing-join

Input: `SELECT users.name, orders.total FROM users, orders WHERE users.id = 1;`
Fix: `SELECT users.name, orders.total FROM users JOIN orders ON users.id = orders.user_id WHERE users.id = 1;`

### fix-null-comparison

Input: `SELECT * FROM employees WHERE manager_id = NULL;`
Fix: `SELECT * FROM employees WHERE manager_id IS NULL;`

### fix-integer-division

Input: `SELECT completed_tasks / total_tasks AS completion_rate FROM projects;`
Fix: `SELECT CAST(completed_tasks AS DECIMAL) / total_tasks AS completion_rate FROM projects;`

## Anti-patterns

- Do not use implicit joins (comma-separated FROM) — always use explicit JOIN syntax
- Do not compare with NULL using = or != operators
- Do not SELECT columns not in GROUP BY without aggregating them
- Do not write UPDATE or DELETE without WHERE unless you intend to affect all rows
- Do not rely on column position in INSERT — always specify column names
