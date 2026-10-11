---
phase: 07
review: 07-REVIEW.md
fix_dispatch: 2026-10-11 16:18 CST
critical: 1
warning: 6
info: 5
fixed: 7
open: 5
wont_fix: 0
---

# Phase 7 Review Disposition

Source: `07-REVIEW.md` (commit 2987dca) + fix dispatch (commits 3145a74..406e1be, dispositions inline in REVIEW.md at 67027b2).

| Finding | Severity | Summary | Disposition |
|---------|----------|---------|-------------|
| CR-01 | Critical | save_to_json num_tokens=0 ZeroDivisionError → silent retrain loop, lost flops_report | **fixed** (3145a74) — both guards `is not None and > 0`; regression test pins null-extrapolation output |
| WR-01 | Warning | subset JSON `null` collides with unreadable sentinel, bypasses startup validation | **fixed** (7d731d7) — distinct `object()` sentinel; `None` payload joins the non-object abort tests |
| WR-02 | Warning | empty eval-subset ID list = full test-split evaluation, breaks comparability | **fixed** (c21a34e) — child validator refuses empty lists by name; audit omits unified==0 tasks with WARNING; `apply_eval_subset` unchanged (unreachable post-validation) |
| WR-03 | Warning | test_sweep.py unpinned ambient overlay env → machine-dependent frozen-order tests | **fixed** (d6f0df8) — module-scope autouse fixture pins both env vars; verified vs hostile ambient overlay |
| WR-04 | Warning | chmod-0o000 test fails spuriously under root CI | **fixed** (6e1f7b8) — root skip guard + finally restore + import os |
| WR-05 | Warning | `--cache_dir ""` resolves to CWD and threads HF_HOME=repo root | **fixed** (d50510a) — twin empty-value guard, collect-all, names flag + raw value |
| WR-06 | Warning | registry-key vs Dataset_name divergence silently fails cells outside subset-file runs | **fixed** (406e1be) — `_validate_dataset_name_alignment` refuses at sweep start over the overlay-merged view; join-on-Dataset_name rejected as non-surgical |
| IN-01 | Info | unused `samples` variable (run_finetune.py:1454) | open |
| IN-02 | Info | duplicate gpu_memory_override assignment (run_finetune.py:708-709) | open |
| IN-03 | Info | README CLI docs missing the four new sweep flags (+peft/variant/fraction) | open |
| IN-04 | Info | CLAUDE.md claims 3.11+ vs README badge 3.13+ | open |
| IN-05 | Info | CPU-run max_mem_gb records 0.0 vs "records nulls" docstring | open |

**Post-fix gates:** `make lint` ✓ · `make typecheck` ✓ · `make test-fast` 557 passed / 1 deselected ✓

Info findings (5) remain open by scope decision (maintainer chose CR+WR fix scope, 2026-10-11 16:10 CST).
