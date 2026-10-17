# Phase 4 Deferred Items

Discovered during execution, out of plan scope (scope boundary: not auto-fixed).

| # | Found during | Item | Why deferred |
|---|--------------|------|--------------|
| 1 | 04-05 Task 1 | `baseline/compare.py:55` — docstring See-also still names `script/get_task_performance.py` ("project script-skeleton conventions"); the file is deleted | `compare.py` is not in 04-05's files_modified; the reference is a stale doc cross-link only, no functional impact |
| 2 | 04-05 Task 2 | `script/convert_registry.py:71` — docstring cross-reference to `script/get_task_performance.py` (deleted) | convert_registry.py joined lint scope (IN-08) but the plan only sanctioned ruff findings, not docstring edits |
| 3 | 04-05 Task 1 | `scripts/generate-tasks-index.js:31` — comment "same convention as script/get_task_performance.py" | JS generator not in the plan's files_modified; comment describes a convention by a now-deleted example |
| 4 | 04-05 Task 1 | `.claude/CLAUDE.md` — several codebase-profile references to `script/get_task_performance.py` (lines 27, 57, 96, 152, 200, 202, 233, 321, 352 of the pre-04-05 file) | Generated profile document, not in the plan; GSD guidance is to not hand-edit CLAUDE.md — regenerate the profile at the next `/gsd-map-codebase` or profile refresh |
| 5 | Pre-existing | `README.md` project-structure block does not list `script/freeze_snapshot.py`, `script/convert_registry.py`, `script/make_dev_splits.py` (pre-04-05 incompleteness; 04-05 only swapped the deleted pivot entry for `export_runs.py`) | Cosmetic listing gap predating this plan |
