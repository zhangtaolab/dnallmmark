---
phase: quick-261016-a4f
plan: 01
subsystem: env-check fail-closed hardening (pipeline env_smoke + TUI env screen)
tags: [env-smoke, fail-closed, wr-fix, code-review, tui]
requires:
  - 07-REVIEW.md findings WR-01..04 + IN-01 (commit 16e21b5's own defects)
provides:
  - env_smoke directory kernels fail-closed on every broken-registry shape (non-dict top level, empty path entries) — no traceback, no false PASS
  - env screen never strands a run on a raising persist (degraded completion render) and never renders a fabricated zero-count route line
affects:
  - pipeline/env_smoke.py
  - tui/screens/env_check.py
  - tui/strings.py
key-files:
  created:
    - .planning/quick/261016-a4f-fix-4-warning-1-info-from-the-07-scoped-/261016-a4f-SUMMARY.md
  modified:
    - pipeline/env_smoke.py
    - tests/test_env_smoke_bytes.py
    - tui/screens/env_check.py
    - tui/strings.py
    - tests/tui/test_pilot_env_check.py
    - .planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-REVIEW-DISPOSITION.md
    - .planning/STATE.md
decisions:
  - WR-01 shape validation lives INSIDE _read_registry (the single reader owns the whole broken-registry conversion — the kernels can never traceback again, mirroring the reviewer's own fix sketch)
  - WR-03 posts ONE degraded CheckRunComplete (new optional persist_error field, default None) rather than a second message class — the on_mount cache call site and every healthy path stay byte-identical via the default
  - WR-03's fallback checked_at is computed in the screen on the SAME basis the real backend's persist derives its own (datetime.now().astimezone().strftime(CHECKED_AT_FORMAT)) — it labels the attempt moment; nothing was written
  - WR-04 renders the failed kernel's OWN first FAIL line verbatim (kernel lines are data — no glyph prefix, no translation) instead of adding a third route-wording constant; the defensive empty-lines fallback keeps the helper render-safe
metrics:
  duration: 18 min
  completed: 2026-10-16
status: complete
actuals:
  tokens: 21000
  tasks: 3
  commits: 2
---

# Quick Task 261016-a4f: Fix 4 Warnings + 1 Info from the 07 scoped review Summary

One-liner: env_smoke's directory kernels now fail-closed on non-dict top-level and empty-path registry shapes, and the env screen gained a guarded persist tail (degraded completion) plus honest no-count routing — the 16e21b5 fail-closed contract finally holds for its own stated scope.

## What Was Fixed (per finding)

### WR-01 — non-dict top-level registry no longer tracebacks
- **Fix:** `_read_registry` (pipeline/env_smoke.py:479-486) owns the top-level shape validation: the `json.load` result is assigned, then an `isinstance(parsed, dict)` check after the try converts a readable, valid-JSON list/string/number/null into the SAME named one-line FAIL result family — `"FAIL: read registry {path} — not a JSON object (top-level {type})"`. The existing except tuple and its FAIL wording are byte-identical. Docstring extended (lines 435-446).
- **Test:** `test_directory_kernels_fail_closed_on_non_dict_top_level_registry` (tests/test_env_smoke_bytes.py:464) — a top-level list AND a null file against BOTH kernels: ok False, exactly ONE line, `FAIL: read registry` prefix, path in line, `not a JSON object` in line, `top-level list` / `top-level NoneType` in line.
- **Commit:** f64e764

### WR-02 — empty Model_path counts as MISSING
- **Fix:** `check_model_dirs` (pipeline/env_smoke.py:521-526) mirrors the sibling kernel's empty-string guard: the present condition is now `not isinstance(value, str) or not value or not Path(base + value).is_dir()` — `base + ""` resolving to the existing base dir no longer renders a false all-present PASS. `check_dataset_dirs` untouched (already guarded). Docstring updated (lines 500-502).
- **Test:** `test_directory_kernels_count_shape_broken_entries_as_missing` extended (tests/test_env_smoke_bytes.py:500) with `m-emptypath`/`d-emptypath` entries — both kernels FAIL 3 of 4 with the three broken names listed in sorted-key order.
- **Commit:** f64e764

### WR-03 — guarded persist tail (the third raise site)
- **Fix:** `run_full_check`'s persist call (tui/screens/env_check.py:514-533) is wrapped in `try/except Exception` (the same noqa: BLE001 idiom as the two WR-01 guards). On failure: the display timestamp is computed locally on the same basis the real backend's persist uses (lines 523-525), the error text formats as `"{type}: {exc}"`, and ONE `CheckRunComplete` posts with the new optional `persist_error` field (message ctor line 380). The completion handler threads it into `_render_check_outcome` (line 581), which renders `ENV_LAST_CHECK_DEGRADED` (tui/strings.py:257) instead of the plain `ENV_LAST_CHECK_LINE` — a bare timestamp would promise a persisted same-day cache that does not exist. Healthy + cache-hit paths byte-identical via the None default; worker docstring updated (lines 479-486).
- **Test:** `test_raising_persist_still_completes_with_degraded_last_check` (tests/tui/test_pilot_env_check.py:1159) — `app.return_code is None`, every row keeps its final glyph, verdict block rendered (non-empty), last-check line contains `OSError: state dir is read-only` in the degraded shape (prefix+timestamp+suffix pinned against the imported constant) and is NOT the plain form, persist attempted exactly once.
- **Commit:** 7217ca1

### WR-04 — honest routing for listing-less failures
- **Fix:** new `_route_line(result, template)` helper (tui/screens/env_check.py:256) next to `_missing_count`: count > 0 renders the count-based template exactly as before; NO listing lines (the registry read-failure / degraded shapes, count unknowable) renders the kernel's own first FAIL line VERBATIM (data — no glyph prefix, no translation); a defensive count-based fallback covers empty lines (render, never crash). Both routing sites in `_render_check_outcome` route through it (lines 629, 638).
- **Test:** `test_read_failure_dir_kernel_renders_own_fail_line_not_zero_count` (tests/tui/test_pilot_env_check.py:1208) — the kernel's FAIL line renders verbatim in the verdict block; `ENV_ROUTE_MISSING_MODELS.format(n=0)` and `ENV_ROUTE_MISSING_DATASETS.format(n=0)` are NOT among the lines. The pre-existing listing-carrying routing test (line 613) stays green unmodified.
- **Commit:** 7217ca1

### IN-01 — `_degraded_result` annotation narrowed
- **Fix:** `exc: BaseException` → `exc: Exception` (tui/screens/env_check.py:286), matching both `except Exception` call sites; the docstring notes KeyboardInterrupt/SystemExit deliberately never reach it (they must propagate).
- **Commit:** 7217ca1

## TDD Evidence (per the 16e21b5 precedent — tests + fix in one commit per task)

- **Task 1 RED:** `TypeError: list indices must be integers or slices, not dict` at env_smoke.py:503 (the exact reproduction 07-REVIEW documented) + shape-test assertion diff `2 of 4` vs expected `3 of 4` (empty Model_path counted PRESENT). Both failed on the planned assertions.
- **Task 2 RED:** WR-03 test failed with `_verdict_lines` == `[]` (the stranded run — no completion posted); WR-04 test failed with the rendered `⚠ 0 个模型目录缺失 — ...` fabricated route line in place of the kernel's FAIL line. Both failed on the planned assertions. (The inert strings constant landed before RED so the module collects — an ImportError is not valid RED.)
- **GREEN:** each fix made its target tests pass with zero other-suite movement.

## Gate Results

| Gate | Result |
|------|--------|
| `make lint` (ruff) | green |
| `make typecheck` (ty) | green, zero diagnostics |
| `make test` (pytest) | 7 failed / 1798 passed — EXACTLY the pinned 7F baseline (test_determinism 1, test_schemas 5, test_services_run_config 1), zero new failures; 1798 = 1795 baseline + 3 new tests |
| node suite | 26/26 green |
| 9 golden SVG tests (test_snapshots.py) | green UNMODIFIED (D-03 discipline — never regenerated) |
| S1-S4 env_smoke goldens | green unmodified |

## Commits (plain, zero trailers)

- f64e764 — fix(261016-a4f): WR-01/WR-02 — env_smoke fail-closes non-dict registry top level + empty Model_path
- 7217ca1 — fix(261016-a4f): WR-03/WR-04/IN-01 — guarded env-screen persist tail + honest unreadable-registry routing

Disposition rows for WR-01..04 + IN-01 set to `fixed` with these hashes in 07-REVIEW-DISPOSITION.md (open 8 → 3; CR-01/IN-02/IN-03 untouched with their carried markers). STATE.md carries the 261016-a4f quick row. Docs commit + push handled by the orchestrator.

## Deviations from Plan

None — plan executed exactly as written. Two execution notes, both sanctioned by the prompt's constraints:

- The docs commit + push steps of Task 3 were NOT performed by this executor (orchestrator instruction: it owns the docs commit and the push). All bookkeeping edits (disposition, STATE row, this SUMMARY) are in the working tree.
- Task 1's first commit (53baa76) was amended to f64e764 to fix a commit-message typo (check_dataset_docs → check_dataset_dirs) before anything was pushed.

## Self-Check: PASSED

- pipeline/env_smoke.py, tests/test_env_smoke_bytes.py, tui/screens/env_check.py, tui/strings.py, tests/tui/test_pilot_env_check.py — all modified on disk (git status clean for code files after commits)
- f64e764, 7217ca1 — both are ancestors of HEAD on autorun
- Disposition + STATE.md edits present in working tree for the orchestrator's docs commit
