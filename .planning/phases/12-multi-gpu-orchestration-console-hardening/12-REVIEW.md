---
phase: 12-multi-gpu-orchestration-console-hardening
reviewed: 2026-10-13T15:04:41Z
depth: quick
files_reviewed: 6
files_reviewed_list:
  - pipeline/run_sweep_shard.py
  - tests/test_sweep_shard.py
  - tui/screens/run_config.py
  - tests/tui/test_pilot_run_config.py
  - tui/strings.py
  - tests/tui/test_strings_phase11.py
findings:
  critical: 0
  warning: 0
  info: 1
  total: 1
status: issues_found
---

# Phase 12: Code Review Report — Delta Re-Review (Iteration 2)

**Reviewed:** 2026-10-13T15:04:41Z
**Depth:** quick (delta convergence pass)
**Files Reviewed:** 6 (the WR-01..WR-08 fix surface)
**Status:** issues_found (0 new critical / 0 new warning / 1 new info)

## Convergence Note

- **Iteration:** 2 (delta re-review after the fix loop)
- **Delta scope:** commits `d8c54a8..b010e65` — the 8 warning fixes WR-01..WR-08
- **Prior review (iteration 1, standard depth):** 0 critical / 8 warnings /
  3 info. All 8 warnings fixed per `12-REVIEW-FIX.md` (one atomic commit per
  finding, RED→GREEN); the 3 IN- items stay open per the disposition and are
  NOT re-reported here.
- **Verdict:** every one of the 8 fixes was independently re-verified against
  the current source and resolves its finding without introducing a new
  Critical or Warning defect. One new Info-level hardening note (IN-04, an
  edge of the WR-07 fix) is recorded below; it is conservative in impact and
  can be dispositioned like the standing IN- items.

### Fix verification (WR-01..WR-08)

- **WR-01 (verbatim `--gpus`)** — VERIFIED. `_parse_gpus`
  (`pipeline/run_sweep_shard.py:399-427`) keeps stripped tokens as verbatim
  strings; the only malformed token is an empty element; the default builds
  `"0".."N-1"` strings (`:1159`) and the spawn env forwards `gpus[i]` with no
  `str()` wrap (`:1208`). Edge traces: an all-empty `--gpus` value yields
  arity 0≠N (refused), a partially-empty list whose surviving arity happens
  to match is still refused by the collected empty-element problem, and
  duplicate/MIG/UUID tokens forward verbatim (pinned by
  `test_gpus_non_numeric_tokens_forward_verbatim`,
  `test_gpus_override_and_duplicate_tokens_forward_verbatim` — non-vacuous:
  both fail under int coercion).
- **WR-02 (per-launch timestamped worker logs)** — VERIFIED.
  `WORKER_LOG_TIMESTAMP_FORMAT` (`:192`) matches the launcher's
  `%Y%m%d_%H%M%S`; `worker_log_path` (`:219-240`) returns
  `{base}-mgpu-w{i}-{stamp}.log`; `main()` derives ONE stamp before the spawn
  loop via the injectable `clock` seam (`:1170-1171`); the verdict table
  reports the log THIS launch teed into (`:1235`).
  `test_resume_relaunch_never_truncates_prior_worker_log` is non-vacuous —
  under the old frozen naming both launches open the same `"w"` path. (A
  same-second relaunch would reuse a stamp, but that property is inherent to
  the launcher tee idiom the dispatch directed this fix to copy — not a new
  defect.)
- **WR-03 (stale-cell refusal on re-merge)** — VERIFIED. The guard
  (`:943-962`) enumerates the merged root's `MERGE_ALLOWLIST`-named files not
  covered by this merge's copy plan and refuses BEFORE any copy with count +
  up to 5 paths + remedy; the root-level manifests themselves are correctly
  excluded (they are rewritten every merge). Identical worker sets stay
  idempotent (pinned positive control
  `test_remerge_unchanged_worker_set_stays_idempotent_under_stale_guard`).
  Edge traces: a worker file that vanished since the last merge under an
  UNCHANGED worker set refuses fail-closed (safe direction, remedy text still
  applies); `--include-checkpoints` asymmetry between merges leaves only
  checkpoint residue, which no downstream consumer reads (the guard is
  deliberately scoped to the exporter-visible allowlist — the finding's
  subject).
- **WR-04 (copy-step OSError → designed refusal)** — VERIFIED. The
  `mkdir`+`copyfile` pair in `_copy_verified` (`:568-572`) converts
  `OSError` to `False`, landing in the collect-all mismatch refusal with
  src→dst entries and NO merged manifests written; `PermissionError` and
  shutil's `SameFileError`/`SpecialReadError` are `OSError` subclasses; the
  post-copy re-hash failure path (`_sha256_file` → `None`) also returns
  `False`. Pinned at both unit and merge level
  (`test_copy_verified_unit_oserror_converts_to_refusal`,
  `test_merge_refuses_with_designed_diagnostic_on_copy_oserror`).
- **WR-05 (deterministic lane-set canonicalization)** — VERIFIED.
  `_canonical_lane_value` (`:636-657`) canonicalizes sets/frozensets through
  `sorted()` before `json.dumps` (the sets are always sets of canonical
  strings, so sorting is total); `None → "null"` stays distinct from
  `"[]"`; `isinstance(value, (set, frozenset))` catches subclasses (the
  `_ReversedIterSet` pin is non-vacuous); the refusal diagnostic sorts the
  set for display. False-refusal and false-accept both re-traced clean.
- **WR-06 (refuse `--models` in merge mode)** — VERIFIED. `run_merge`
  (`:777-782`) refuses a provided `--models` — including a provided-but-empty
  string value (`is not None`) — collect-all before any worker-root read;
  docstring and `--models` help text aligned;
  `test_merge_refuses_models_flag` pins message + no merged manifest.
- **WR-07 (sanitize marked-then-disabled customs at load)** — VERIFIED, one
  Info-level edge recorded as IN-04 below. `_sanitize_disabled_custom_marks`
  (`tui/screens/run_config.py:1124-1149`) runs in
  `on_run_config_screen_loaded` right after the entries land and before any
  render/preview, so spec, status line, preview, and launch enumeration agree;
  the first preview-worker save persists the sanitized spec (pinned:
  `test_marked_then_disabled_custom_leaves_spec_at_load` covers BOTH axes and
  is non-vacuous — the spec retains the keys without the fix); the
  render-side `and not is_disabled` suppression stays as defense-in-depth.
- **WR-08 (subset-OFF copy wholly in `tui/strings.py`)** — VERIFIED.
  `CFG_SUBSET_OFF_WITH_PATH = "关（{path}）"` (`tui/strings.py:696`); the
  screen renders it via `.format(path=path)` (`run_config.py:1385`) and the
  now-unused `CFG_SUBSET_OFF` import is gone from the screen module; the
  constant is registered in the bidirectional phase-11 inventory
  (`tests/tui/test_strings_phase11.py:44-45`); the grep lock's extended ranges
  `[一-鿿　-〿＀-￯]` were verified to cover U+3000–U+303F + U+FF00–U+FFEF
  (U+FF08/U+FF09 included); `test_params_defaults_render` pins the exact
  constant shape. A repo-wide scan confirms ZERO CJK
  punctuation/fullwidth literals in any other `tui/` module today, so the
  deliberately narrower (run_config-only) lock extension leaves no live
  violation in the sibling suites.

### Verification gates re-run for this pass

- Module suites: `tests/test_sweep_shard.py` +
  `tests/tui/test_pilot_run_config.py` + `tests/tui/test_strings_phase11.py`
  — 102 passed.
- `ruff check` over all six delta files — all checks passed.
- `ty check` over the two changed source modules — all checks passed.
- Extended I18N grep lock executed against the current
  `tui/screens/run_config.py` — 0 offenders.

## Info

### IN-04: WR-07 sanitizer is kind-blind — a cross-kind key collision would drop a valid mark of the other kind

**File:** `tui/screens/run_config.py:1138-1147`
**Issue:** `_sanitize_disabled_custom_marks` builds ONE disabled-key set from
`custom_status` — which spans BOTH kinds (the backend folds custom models and
custom datasets into a single kind-less dict, `run_config.py:263-285`) — and
applies it to BOTH spec axes. The custom-entries land path is per-kind
(`read_entries(kind)`), so nothing structurally forbids a disabled custom
MODEL whose key exactly equals a marked DATASET key (or vice versa); in that
case the sanitizer drops the other kind's legitimate mark at load. Reaching it
requires a deliberately perverse cross-kind name collision (model keys and
dataset keys follow disjoint conventions — `plant-dnabert-6mer` vs
`Source__task` — so accidental collision is essentially impossible), the
failure direction is conservative (a mark is dropped, visibly reflected in the
status-line counts, and re-markable since the colliding official row is not
disabled), and it is an edge of the review's own prescribed fix shape. Recorded
as a hardening note, dispositionable like the standing IN- items.
**Fix:** If hardening is ever wanted: thread kind through `PickerEntries`
(e.g. `custom_status` values gain `"kind": "models" | "datasets"`) and filter
`spec.models` against disabled models only, `spec.tasks` against disabled
datasets only.

---

_Reviewed: 2026-10-13T15:04:41Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick (delta convergence pass, iteration 2)_
