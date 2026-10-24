---
status: passed
phase: 12-multi-gpu-orchestration-console-hardening
source: [12-VERIFICATION.md]
started: 2026-10-13T23:12:00+08:00
updated: 2026-10-13T23:12:00+08:00
---

## Current Test

number: 1
name: D-03 maintainer review of the 8 committed SVG goldens
expected: |
  Each of tests/tui/__snapshots__/{env_check,selection_models,selection_datasets,
  data_manager,run_config,monitor_running,monitor_empty,wizard}.svg renders the canonical
  screen faithfully against the 12-UI-SPEC corpus table — correct screens, panels, values
  visible (incl. params Input values post compact=True), no visual corruption. Automation
  proved byte-stability and red-on-drift; only a human eye can confirm visual rightness
  (the SC5 "maintainer-verified" clause).
awaiting: user response

## Tests

### 1. D-03 SVG golden review (8 files)
expected: Visual faithfulness of the 8 canonical screens vs 12-UI-SPEC corpus table (see Current Test above).
result: [passed] — resolved across the #35/#39/#42 golden rounds; final monitor pair (B+D Running tab) maintainer-approved 2026-10-19 19:57, landed b84afc0; CI green thereafter

### 2. WINDOWS #21 — other-machine N=2 multi-GPU smoke
expected: |
  On the multi-GPU machine (NOT GB10 — D-05 machine roles), run the 9-step procedure in
  docs/multi-gpu.md (bounded: 2 models × iDNA_ABF_datasets__5mC × 1 seed × 1 epoch):
  shard launch → per-worker monitoring → detach/re-attach → artifact merge (--merge) →
  consumer equivalence → WINDOWS #21 closed with the run evidence. This is the maintainer's
  run; GB10 is single-GPU dev/test only, so absence here is by design.
result: [blocked-external] — remains WINDOWS #21 (open, other-machine run required); ledger-tracked, /gsd-ship keeps it blocked while open

## Summary

total: 2
passed: 1
issues: 0
pending: 0
skipped: 0
blocked: 1

## Gaps
