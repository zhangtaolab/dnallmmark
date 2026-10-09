---
status: testing
phase: 02-data-contracts-test-harness
source: [02-VERIFICATION.md]
started: 2026-10-09T04:38:00Z
updated: 2026-10-09T04:38:00Z
---

## Current Test

number: 1
name: REL-04 probe-accounting sufficiency
expected: |
  Human accepts the zero-diff criterion (make data == committed tree byte-for-byte, exit 0)
  as sufficient for REL-04's single-command guarantee, or names an additional defensible
  criterion (e.g. exit-status semantics, partial-failure modes of the recipe lines) for a
  follow-up plan.
awaiting: user response

## Tests

### 1. REL-04 probe-accounting sufficiency
expected: Human accepts the zero-diff criterion (make data == committed tree byte-for-byte + exit 0) as sufficient for REL-04's single-command guarantee, or names an additional defensible criterion for a follow-up plan.
result: [pending]

### 2. TEST-02 probe-accounting sufficiency
expected: Human accepts the approx + thread-pinning + lane-segregation criteria (pytest.approx on every float, OMP/OPENBLAS/MKL/NUMEXPR/VECLIB pinned to 1 and asserted at test time, slow lane segregated) as sufficient for TEST-02's stability-by-construction guarantee, or names an additional defensible criterion (e.g. repeated-run flake bounds) for a follow-up plan.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
