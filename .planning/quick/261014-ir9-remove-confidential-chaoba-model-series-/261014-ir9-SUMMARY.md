---
phase: quick-261014-ir9
plan: 01
subsystem: registry
tags: [security, registry, data-removal, tests]
status: complete
commit: 1f16b3d
requires:
  - "HEAD at/after 650ba0a (planning baseline)"
provides:
  - "Official model registry with 59 entries, zero confidential-series references in tracked files"
  - "Every real-registry count pin consistent with 59 (tests, operator copy, docstrings, docs, schema comment)"
affects:
  - "pipeline models registry consumers (run_finetune, run_sweep, zero_shot_vep, TUI services)"
key-files:
  created: []
  modified:
    - pipeline/models_info.json
    - pipeline/run_finetune.py
    - pipeline/run_sweep.py
    - schemas/vep_zero_shot.json
    - script/export_runs.py
    - script/zero_shot_vep.py
    - tui/strings.py
    - tui/services/about.py
    - tui/services/registries.py
    - tui/services/run_config.py
    - tui/services/sweep_launcher.py
    - tui/services/sweep_monitor.py
    - tui/screens/matrix.py
    - tui/screens/monitor.py
    - docs/ARCHITECTURE.md
    - docs/DEVELOPMENT.md
    - docs/ONBOARDING.md
    - docs/TUI-GUIDE.md
    - docs/multi-gpu.md
    - tests/test_model_registry.py
    - tests/test_registry_unification.py
    - tests/test_run_finetune_contracts.py
    - tests/test_sweep.py
    - tests/test_sweep_shard.py
    - tests/test_zero_shot_vep.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_selection_custom.py
    - tests/tui/test_services_about.py
    - tests/tui/test_services_custom_entries.py
    - tests/tui/test_services_gauntlet.py
    - tests/tui/test_services_registries.py
    - tests/tui/test_services_run_config.py
    - tests/tui/test_services_sweep_launcher.py
decisions:
  - "HEAD-only remediation per plan: git history retains the 3 confidential entries by explicit maintainer decision; private loading via the local custom_models.json overlay (no code changes for that path)"
  - "Count-embedding test function names are current-count statements: test_registry_parses_with_62_entries... and test_official_counts_committed_registries_are_62_50 renamed to their 59 forms (zero external references)"
metrics:
  duration: 39 min
  completed: 2026-10-14T06:26:39Z
actuals:
  tokens: 15086   # chars/4 over the realized diff (60,346 diff chars)
  tasks: 1
  commits: 1
---

# Quick Task 261014-ir9: Remove Confidential Chaoba Model Series — Summary

One-liner: deleted the 3-entry confidential Chaoba series from the official model registry (62 → 59) and re-based every real-registry count pin and stale current-count statement (tests, operator copy, service docstrings, maintainer docs, schema comment) so zero confidential references remain in tracked files at HEAD.

## What Was Done

**Part A — confidential-content removal (the 3 chaoba-string sites):**
- `pipeline/models_info.json`: deleted the `Chaoba`, `Chaoba_all_species`, `Chaoba_denseMamba` blocks (planning-time lines 2-55). Registry now parses at exactly 59 entries, first key `CrossDNA_519M`, 4-space indent and all other blocks byte-untouched.
- `pipeline/run_finetune.py` (~987-988): the 261014-c2l storage-root-override comment example swapped `models/Chaoba` → `models/DNABERT-2-117M` (verified registry key with `Model_path "models/DNABERT-2-117M"`); surrounding prose byte-identical.
- `tests/tui/test_services_registries.py`: `test_model_entries_carry_raw_values_with_empty_string_absents` re-anchored Chaoba → `mamba2_370M` (verified same shape: `type ""`, `species ""`, card `Model_size "370M"`); the unchanged `"" in types` existence assert stays covered by the 4 remaining empty-type entries.

**Part B — registry-count re-pins (8 test files):**
- B1 `tests/test_model_registry.py`: `CARD_BEARING_COUNT = 59`; both `len == 59` asserts + messages; docstrings/decomposition notes carry the removal fact (62 → 59, 261014-ir9) appended to historical narration.
- B2 `tests/test_registry_unification.py`: `len(registry) == 59`, `len(card_bearing) == 59` + messages; module docstring decomposition now "38 shared + 18 tabular-only + 6 json-only − 3 removed (261014-ir9)".
- B3 `tests/test_zero_shot_vep.py`: full-enumeration `len(rows) == 59`, unique models 59, models-filter `len(rows) == 59`; EMPTY-type exclusions 7 → 4 (evaluated stays 50, mlm 32 / clm 18, DL 5).
- B4 `tests/tui/test_services_registries.py`: `(59, 50)` counts pin, `len(entries) == 59`, docstrings 59.
- B5 `tests/tui/test_services_about.py`: three `RegistryCounts` pins → 59/50; docstrings 59/50.
- B6 `tests/tui/test_services_custom_entries.py`: official-only base 59, landed-candidate 60 (59+1), post-undo 59; docstring "60 models / 51 datasets over the official 59/50".
- B7 `tests/tui/test_pilot_selection.py`: `len(data.model_entries) == 59` at both sites; docstrings 59/50.
- B8 `tests/tui/test_pilot_selection_custom.py`: official-base arithmetic throughout — `len(merged) == 59`, landed index/`_row(table, 59)`, `models_total=60` with 1 enabled custom, `official_models=59` ×3, `move_cursor(row=59)`, dataset-case `models_total=59` (tasks_total=51 and official_datasets=50 stay).
- B9 `tests/tui/test_services_run_config.py`: `len(official.models) == 59`; docstring 59 models; the historical "08-03 RegistryCounts(62, 50) precedent" citation untouched per plan.

**Part C — stale current-count statements:**
- C1 `tui/strings.py`: comment 59/50; **operator copy `LNC_E2_WARNING`** → "59 模型 × 50 数据集 × 3 种子 = 8850 cell" (59×50×3).
- C2 `tui/services/about.py` (4 docstrings), C3 `tui/services/registries.py` (2), C4 `tui/services/run_config.py` (D-02 comment → 59×50×3), C5 `pipeline/run_sweep.py` (~8,850 cells 59x50x3), C6 `script/zero_shot_vep.py` (59 rows; decomposition "5 DL + 4 empty-type"), C7 `docs/DEVELOPMENT.md` (59 entries currently), C8 `tests/test_sweep.py` (2950 cells; ~8,850), C9 `tests/test_sweep_shard.py` (59-model view), C10 `tests/tui/test_services_gauntlet.py` (59/50).

## Executor Sweep Catches (beyond the plan's enumeration — same Parts A-C discipline)

The plan's final instruction required a full `git grep` sweep; these current-count sites were missed by planning and fixed identically:

| File | Site | Fix |
|------|------|-----|
| `tests/test_zero_shot_vep.py` ~626 | docstring "the full 62-row registry emission" | 59-row |
| `docs/ARCHITECTURE.md` ~6 | "trains 62 registered DNA LLMs" | 59 |
| `docs/ONBOARDING.md` ~39 | converter sample output "62 rows" | 59 rows |
| `docs/TUI-GUIDE.md` ~94 | "62×50 presence matrix" | 59×50 |
| `docs/TUI-GUIDE.md` ~149 | verbatim quote of `LNC_E2_WARNING` (would have contradicted the changed operator string) | 59 / 8850 |
| `docs/multi-gpu.md` ~21, ~29 | "62-model benchmark matrix" / "62-model sweep throughput" | 59-model |
| `tui/screens/matrix.py` ~153 | docstring "read-only 62x50 presence matrix" | 59x50 |
| `tui/screens/monitor.py` ~715 | "3100-row table" cursor-pin rationale | 2950-row |
| `tui/services/sweep_launcher.py` ~62 | "IS the full 9300-cell matrix" | 8850-cell |
| `tui/services/sweep_monitor.py` ~930 | "done 3005/9300-style corruption" example | 3005/8850 |
| `script/export_runs.py` ~332 | "62/62 complete since the 04-04 fills" | 59/59 + removal note |
| `schemas/vep_zero_shot.json` $comment | "one entry per models_info registry model — 62 always" | 59 always (JSON re-validated) |
| `tests/test_run_finetune_contracts.py` ~149 | "the 62-entry unified registry" | 59-entry |
| `tests/tui/test_services_sweep_launcher.py` ~972 | docstring "full 9300-cell matrix" (test enumerates the REAL official keys) | 8850-cell |

Sites considered and deliberately LEFT (past-tense/history/fakes, per the plan's untouched discipline): `script/zero_shot_vep.py` ~850 ("previously ... producing 62 not-selected rows" — pre-fix behavior narration); `tests/test_model_registry.py` ~4/~8 (03-02/03-03 historical narration, removal fact appended elsewhere in the same docstring); `tests/tui/test_pilot_env_check.py` ~145/359/625 ("all 62 registry model dir(s)" strings are contract-shaped FAKE pass/fail items, not real-kernel comparisons — lane green proves it); `tests/tui/test_pilot_monitor.py` 9300s (fabricated injection totals); `tui/strings.py` ~340 ("62-char keys" is a key length); the plan's full DELIBERATELY UNTOUCHED list.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan B8 arithmetic slip at test_pilot_selection_custom.py:573**
- **Found during:** Task 1 verification (pilot lane run)
- **Issue:** Plan specified `len(keys_after) == 62  # 59 official + the disabled custom`, but the management-table composition is 59 official + 1 disabled custom = **60** keys (pre-change it was 62 + 1 = 63). The plan's own comment states the correct intent.
- **Fix:** Pinned `== 60` with the plan's comment verbatim; test passes.
- **Commit:** 1f16b3d

**2. [Rule 2 - Correctness] Count-embedding test names kept truthful**
- **Found during:** Task 1 (B1/B5 edits)
- **Issue:** `test_registry_parses_with_62_entries_and_name_key_contract` and `test_official_counts_committed_registries_are_62_50` embed the old count; a "62" name asserting 59 is exactly the untrustworthiness this milestone removes.
- **Fix:** Renamed to the `_59_` forms after verifying zero external references (grep across repo).
- **Commit:** 1f16b3d

**3. [Rule 2 - Correctness] 14 additional stale current-count sites fixed** (table above) — all one-number docstring/comment/sample edits in the exact Part C discipline; no structural changes were needed, so the plan's stop-and-report threshold was never reached.

## Verification

- `git grep -i chaoba -- ':!.planning'` → **zero hits** (tracked-file acceptance gate).
- JSON gate: `pipeline/models_info.json` parses, exactly 59 entries, none of the three confidential keys, `CrossDNA_519M` first key, `mamba2_370M` present.
- Registry-dependent lanes: **332/332 green** (277 across the 8-file lane + 55 across both pilot lanes) — the planning-time baseline holds exactly.
- `make test-fast`: 1,676 passed / 9 failed — the 9 are all inside the documented pre-existing set (5 schemas + 4 root-user chmod persist sims; the 10th documented member, the determinism stale pin, passed this run). A 10th failure appeared in the first full run (`test_snapshots.py::test_monitor_running_golden`) — the documented collateral snapshot flake: the same test passes 11/11 in lane isolation, and the monitor.py change is a non-rendering docstring comment. **No NEW failures.**
- `make lint`: all checks passed. `make typecheck`: all checks passed.
- Diff discipline: outside `models_info.json` (the 54-line in-file deletion) every hunk is a comment, docstring, count literal, test name, or the single operator string `LNC_E2_WARNING`; zero executable-logic changes.

## Residual Risk (maintainer-accepted)

- **Git history retains the three confidential entries** (names, sizes, tokenizers) — explicit maintainer decision: HEAD-only remediation, NO history rewriting. Once the repo is public they are recoverable from history. Full eradication would be a separate history-rewrite + force-push decision outside this task (threat register T-ir9-02, accepted).
- **Private loading** of the removed models continues to work through the existing `custom_models.json` overlay under the XDG config root (the maintainer hand-writes that file locally; out of repo scope; no code was changed for that path).
- No data-chain regeneration was needed (confirmed at planning time: no performance/leaderboard/derived-data references to the series exist; `baseline/data-v1.sha256` does not cover `models_info.json`).

## Self-Check: PASSED

- Created/modified artifacts verified on disk (33 tracked files in commit 1f16b3d; SUMMARY present at this path).
- Commit 1f16b3d is HEAD of `autorun` and contains exactly the 33 files staged (no whole-file deletions; working tree clean after commit).
