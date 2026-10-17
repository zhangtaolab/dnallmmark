---
phase: 03-dev-reconciliation-revision-blockers
fixed_at: 2026-10-10T02:32:29+08:00
review_path: .planning/phases/03-dev-reconciliation-revision-blockers/03-REVIEW.md
iteration: 3
findings_in_scope: 1
fixed: 1
skipped: 0
status: all_fixed
---

# Phase 03: Code Review Fix Report

**Fixed at:** 2026-10-10
**Source review:** `.planning/phases/03-dev-reconciliation-revision-blockers/03-REVIEW.md` (iteration 3 — convergence check)
**Iteration:** 3 (this report is the cumulative final fix report; iteration-1 and iteration-2 dispositions are carried forward below)
**Scope:** critical_warning per config, narrowed by the maintainer directive to this iteration's single in-scope finding: **WR-14** (degenerate all-empty-element flag values bypassing the WR-07 fail-fast — both directions empirically demonstrated by the reviewer against the real `run_sweep.py` CLI)

**Summary:**
- Findings in scope: 1 (the single new Warning from the iteration-3 review)
- Fixed: 1 (with regression tests covering both demonstrated shapes)
- Skipped: 0
- Out of scope, documented open: IN-01..IN-11 (critical_warning scope excludes Info; IN-09..IN-11 are new this iteration, none escalating a documented-open item)
- Deferred/locked honored, untouched: WR-03/WR-04 (Phase-4 deferrals), WR-09 (false premise, stands resolved), the three `xfail(strict=True)` locks in `tests/test_known_defects.py`

## Fixed Issues

### WR-14: Degenerate all-empty filter/seed values bypass the WR-07 fail-fast — a separator-only filter silently enumerates the FULL matrix, an empty `--seeds` silently runs 0 cells and exits 0

**Files modified:** `pipeline/run_sweep.py`, `tests/test_sweep.py`
**Commit:** `f817250`
**Applied fix:** After strip normalization in `main()`, a **provided** flag whose post-strip value is empty now fails fast (`sys.exit` with a `[Error] ...` message naming the flag and echoing its raw value — mirroring WR-07's exit style) for `--models`/`--tasks`/`--seeds` alike:

- **Shape (a) — all-empty-element filters.** The `--models`/`--tasks` normalization switched from truthiness (`if args.models`) to `is not None`, so a provided-but-degenerate value (`--models ,` or `--models ""` / whitespace-only, e.g. shell indirection `--models "$A,$B"` with both variables empty) strips to `[]` and **exits 1** instead of falling through `_validate_filters`' falsy early-return (`:256`) and `enumerate_matrix`'s `if models_filter:` (`:219`/`:225`) — the path that silently inverted to the FULL registry matrix (empirically 62 models x 50 tasks = 3100 cells). The message tells the operator to omit the flag for all-models semantics.
- **Shape (b) — empty seed set.** `--seeds` is argparse-`required=True`, but any *present* value satisfies it, including `""` and `","`; an empty post-strip set now **exits 1** instead of `run_matrix([])` writing a 0-cell manifest and exiting 0.
- **Preserved semantics:** empty-*because-absent* (flag not given) keeps today's full-matrix behavior — only explicitly-provided-but-empty fails. A why-comment at the site records the WR-07-invariant rationale.

Empirically re-verified against the real registries post-fix: `--models ,`, `--tasks ,`, `--seeds ,`, `--seeds ""` each exit 1 with the flag + raw value in the message and **no output root created**; omitted filters still enumerate the full 3100-cell matrix (exit 0).

**Regression tests added** (7 cases, `tests/test_sweep.py`):
- `test_cli_exits_nonzero_on_provided_but_empty_filter_values` — parametrized over `--models ,`, `--models ""`, `--tasks ,`, `--tasks ""`: asserts SystemExit, the flag named and its raw value echoed in the message, and no output written before the abort (uses `--dry-run` so a regression fails as a clean missing-SystemExit rather than ever reaching the real launch seam — D-05).
- `test_cli_exits_nonzero_on_provided_but_empty_seed_values` — parametrized over `--seeds ""`, `--seeds ,`: same assertions (pre-fix this shape wrote a manifest and exited 0).
- `test_cli_absent_filters_keep_full_matrix_semantics` — guard-rail: omitting both filters still enumerates every registry model x truthy-Train task (6 fixture cells), pinning that the fail-fast fires only on provided-but-empty values.
- Test-module docstring gains a "degenerate flag values" behavior bullet.

## Out of Scope (documented open)

- **IN-01..IN-08** — carried from iterations 1-2, all Info-tier, excluded by `fix_scope: critical_warning` and the maintainer directive. IN-06 is a documented maintainer decision (D-08/AUDIT.md, Phase-6 retirement tracked); the others remain open for Phase 4 routing.
- **IN-09..IN-11 (new in iteration 3)** — all Info-tier, out of fix scope per the maintainer directive ("documented-open"): IN-09 (`json.JSONDecodeError`-only catch leaves `UnicodeDecodeError` escaping — negligible reachability), IN-10 (`_write_json` non-atomic; WR-12 guard could preserve a truncated record — no programmatic consumer), IN-11 (WR-13 comment overstates power-loss coverage absent fsync).
- **Deferred/locked (binding, untouched):** WR-03/WR-04 (Phase-4 quirk parity surface), the three `xfail(strict=True)` known-defect locks (AUD-01 species, comparator bool/int, non-finite `get_float`), WR-09 (false premise, stands resolved).

## Prior Rounds (carried forward)

### Iteration 2 (fixes verified correct + complete by the iteration-3 review)

3 in scope, 3 fixed, 0 skipped. All three were re-verified at source level and behavior level by the iteration-3 re-review with zero regressions found.

| Finding | Disposition | Commit |
|---|---|---|
| WR-11 corrupt final_metrics.json fails the cell, not the sweep | fixed | `062f72e` |
| WR-12 never overwrite an existing run_record.json for a skipped cell | fixed | `43acfa8` |
| WR-13 write final_metrics.json before the trainer_state.json resume marker | fixed | `dbabb8b` |

### Iteration 1 (fixes verified correct + complete by the iteration-2 review)

12 in scope, 9 fixed, 3 skipped. Full detail preserved in `03-REVIEW-FIX.iter2.md`.

| Finding | Disposition | Commit |
|---|---|---|
| CR-01 fp32-only model handling | fixed | `7c703a7` |
| CR-02 exit-0-no-metrics = failed | fixed | `9932727` |
| WR-01 grad_accum snapshot ordering | fixed | `725782b` |
| WR-02 dataset-dir presence guard | fixed | `8cd586d` |
| WR-05 make_dev_splits docstring narrowing | fixed | `db46c4e` |
| WR-06 always write sweep_failures.json | fixed | `52b0b3a` |
| WR-07 filter validation, non-zero exit | fixed | `0352311` (+ style follow-up `a00ae96`) |
| WR-08 README CWD / run_sweep docs | fixed | `af12068` |
| WR-10 mem_ratio passed to estimator | fixed | `f820423` |
| WR-03 ACGT-only alphabet | skipped: deferred to Phase 4 (maintainer-sanctioned) | — |
| WR-04 unported quirk registries | skipped: deferred to Phase 4 (maintainer-sanctioned) | — |
| WR-09 deprecation banner premise | skipped: false premise (git history contradicts it) | — |

## Verification

**Where the gates ran:** per-fix verification (ast syntax check + targeted `pytest tests/test_sweep.py` + ruff over the touched files + empirical CLI runs against the real registries) ran inside the isolated worktree (`.claude/worktrees/rf-03-*`) using the main checkout's `.venv` interpreters (`ty` there required `--python .venv/bin/python`); the full suite was also run in the worktree pre-merge, and the **authoritative** gate run below ran in the **main checkout** after `f817250` was fast-forwarded onto `autorun` — the numbers are reproducible from the tree as merged (`f817250`).

- `make test` — pytest: **193 passed + 5 xfailed** (iteration-2 baseline 186 + 5, plus the 7 new WR-14 test cases — purely additive); node lane: **2 pass / 0 fail**
- `make lint` (ruff over tests/ + the Phase-3-authored files) — **All checks passed**
- `make typecheck` (ty) — **All checks passed**

CODE-ONLY honored: no model runs, no GPU work, no installs (`uv lock --check` confirmed the lock current before `make`, so every `uv run` sync was a no-op; no dependency files touched). `/home/forrest/Github/DNALLM` was never written to (read-only). The `xfail(strict=True)` locks were not touched.

## Commit Index (this iteration)

| Commit | Finding | Subject |
|---|---|---|
| `f817250` | WR-14 | fail fast on provided-but-empty --models/--tasks/--seeds values |

---

_Fixed: 2026-10-10T02:32:29+08:00_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 3_
