---
phase: 03-dev-reconciliation-revision-blockers
recorded: 2026-10-10T02:35:00+08:00
source: [03-REVIEW.md, 03-REVIEW-FIX.md]
iterations: 3
total_findings: 27
fixed: 13
skipped: 3
open: 11
status: reconciled
---

# Phase 03 — Review Disposition Ledger

Fix loop: --auto, 3 iterations (cap), fix commits 7c703a7..f817250 on autorun. Final suite: 193 passed + 5 xfailed + node 2; make lint / make typecheck clean.

| ID | Severity | Finding | Disposition | Evidence |
|----|----------|---------|-------------|----------|
| CR-01 | critical | fp32-only models would train under global bf16 | fixed | 7c703a7 (+ parity contract test) |
| CR-02 | critical | exit-0-no-metrics cell recorded completed/null | fixed | 9932727 (+ test) |
| WR-01 | warning | grad_accum snapshot before with_head reload | fixed | 725782b (+ contract test) |
| WR-02 | warning | dataset-dir absence aborts rest of run | fixed | 8cd586d (+ isdir guard + test) |
| WR-03 | warning | ACGT-only alphabet vs legacy N-allowing | skipped: deferred Phase 4 (quirk-parity surface, maintainer-sanctioned) | REVIEW-FIX iter1 |
| WR-04 | warning | unported quirk registries (limited_length, safetensors membership, tier rounding) | skipped: deferred Phase 4 (same rationale) | REVIEW-FIX iter1 |
| WR-05 | warning | make_dev_splits docstring over-promises self-healing | fixed | db46c4e (doc-only) |
| WR-06 | warning | stale sweep_failures.json on clean re-runs | fixed | 52b0b3a (+ empty-not-absent test) |
| WR-07 | warning | filter typos exit 0 | fixed | 0352311 (+a00ae96, 2 CLI tests) |
| WR-08 | warning | README omits cd pipeline; stale output layout | fixed | af12068 |
| WR-09 | warning | deprecation banner vs same-phase edits | skipped: false premise (edits predate banner; git history) | REVIEW-FIX iter1 |
| WR-10 | warning | mem_ratio ignored; dead branch | fixed | f820423 |
| WR-11 | warning | corrupt final_metrics.json aborts whole sweep | fixed | 062f72e (+ regression test) |
| WR-12 | warning | resume overwrites existing run_record.json | fixed | 43acfa8 (+ two-run test) |
| WR-13 | warning | trainer_state marker copied before final_metrics | fixed | dbabb8b (+ ordering contract test) |
| WR-14 | warning | provided-but-empty flag values bypass fail-fast (full-matrix / 0-cell exit 0) | fixed | f817250 (+ 7 test cases) |
| IN-01 | info | duplicate gpu_memory_override assignment | open (documented, out of fix scope) | REVIEW iter3 |
| IN-02 | info | split_task duplicates carve_stratified_dev inline | open | REVIEW iter3 |
| IN-03 | info | unstripped --target_dataset elements | open | REVIEW iter3 |
| IN-04 | info | --to-csv direction untested | open | REVIEW iter3 |
| IN-05 | info | README annotation errors (L346/L356) | open | REVIEW iter3 |
| IN-06 | info | documented Zenodo preview JWT (allowlisted, intentional) | open (informational, sanctioned) | REVIEW iter1 |
| IN-07 | info | CR-02 error string asserts one cause | open | REVIEW iter3 |
| IN-08 | info | convert_registry.py missing from make lint scope (currently clean) | open | REVIEW iter3 |
| IN-09 | info | UnicodeDecodeError not caught (unreachable: ASCII writer) | open | REVIEW iter3 |
| IN-10 | info | _write_json non-atomic; truncated record preserved forever post-WR-12 | open | REVIEW iter3 |
| IN-11 | info | WR-13 comment over-claims power-loss coverage (no fsync) | open | REVIEW iter3 |

Notes: the loop hit its 3-iteration cap with the final re-review predating the WR-14 fix; REVIEW-FIX.md (status: all_fixed) and this ledger carry the authoritative disposition. Iteration backups (03-REVIEW.iter*.md) retained per the degradation-path contract. Known locked defects (AUD-01 species, comparator bool/int, non-finite get_float) are xfail(strict=True)-pinned and routed to Phase 4 — never re-reported.
