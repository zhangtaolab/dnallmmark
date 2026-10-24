---
phase: quick-261019-v3g
plan: 01
subsystem: tui-env-check + pipeline-subset-seam
tags: [windows-ledger, storage-overview, subset-file, closeout]
status: complete
key-files:
  created: []
  modified:
    - tui/services/run_config.py
    - tui/screens/env_check.py
    - tui/strings.py
    - tests/tui/test_services_run_config.py
    - tests/tui/test_pilot_env_check.py
    - tests/test_sweep.py
    - tests/test_run_finetune_contracts.py
    - .planning/WINDOWS.md
decisions:
  - "Absent cache dir = neutral on-demand state (glyph ◌ dim + note), ✗ reserved for present-but-unwritable — the four-way rule over service-carried on_demand/writable data"
  - "New StorageRow fields are repr=False so the row repr (and the environmental defaults-test failure text) stays byte-stable"
  - "On-demand glyph renders rich-native dim on the Static path ($text-muted cannot ride Static's rich spans — the 8.2.8 probe pin)"
  - "WINDOWS #12 is a verify-and-pin closeout: the threading landed in 07-03, one day after the row was recorded — no production code changed"
actuals:
  tokens: 6535   # 26139 diff chars / 4 (estimate was 45000)
  tasks: 2
  commits: 2     # git rev-list --count 606c7b7..HEAD (code/test commits; docs commit follows)
  plan_head_before: 606c7b7
metrics:
  duration: 19m (14:38:55Z → 14:57:53Z)
  completed: 2026-10-19
---

# quick-261019-v3g: WINDOWS #33 storage cache honesty + #12 subset seam closeout Summary

One-liner: the env-check storage overview stops crying wolf about the never-written-yet HF cache (neutral ◌ + on-demand note, ✗ only for present-but-unwritable), and the sweep→child `--subset_file` seam is re-verified intact and pinned end-to-end on CPU.

**Status: COMPLETE** — both ledger rows closed (open_count 13 → 8), all lanes green except the one documented environmental failure, all 9 goldens sha256-identical.

## Task 1: WINDOWS #33 — honest on-demand cache glyph

**Landed:** `d7a574a` — `fix(tui): storage-overview cache row renders honest on-demand state (WINDOWS #33)`

- **Service tier** (`tui/services/run_config.py`): `StorageRow` gains defaulted `on_demand` (False) and `writable` (None) fields, both `repr=False` (the row repr stays byte-stable for existing diagnostics); new module-level `_cache_writable(path)` = `os.access(path, os.W_OK)` seam; `storage_overview` constructs the cache row with `on_demand=True` always (a fact of the KEY) and probes writability only when that path exists. Every existing 3-arg construction stays valid; zero behavioral change to paths or `exists`.
- **Strings** (`tui/strings.py`): `ENV_STATE_ON_DEMAND` (language-neutral `◌`, same value both languages — the monitor-strip indeterminate glyph) + `ENV_STORAGE_CACHE_ON_DEMAND` (zh `未创建 — 训练时自动生成` / en `not created — created on demand at training`), both in the ENV_STORAGE block; zh copy passes the approved-terminology gate (no retired terms, no bare sweep/cell).
- **Screen** (`tui/screens/env_check.py` `_render_storage`): the four-way rule — present-unwritable → ✗ error color; present → ✓ (pre-change branch, byte-identical); absent-on-demand → ◌ dim + note appended dim after the path; absent → ✗ (pre-change branch). Non-cache rows carry writable None / on_demand False, so they provably hit only the legacy branches.
- **Pins**: service pins extend both storage tests (new-field assertions only, zero existing assertions touched) + new present-cache probe test (real writable tmp dir → True; monkeypatched probe → False — deterministic, no chmod); three Pilot pins on the real EnvCheckScreen over injected fakes (absent→neutral glyph+note+dim spans, present-unwritable→✗ error color, present-writable→✓ success color, note never riding non-on-demand rows).

**Evidence (test tails):**
- Storage lane: `3 passed, 1 failed` — the failed member is `test_storage_overview_defaults_mirror_real_consumers`, the DOCUMENTED pre-existing environmental failure (the maintainer's live pipeline/logs on this box); its failure text is byte-identical pre/post (same assertion message, same `assert True is False`, same `StorageRow(key='log_dir', path='...', exists=True)` repr — the `repr=False` fields kept the repr stable; only pytest's location line shifted 1509→1521 mechanically from lines added to the sibling test above). The log_dir-absent assertion is unweakened; the new-field assertions are appended after it.
- Pilot env lane: `37 passed` (34 pre-existing + 3 new). Snapshot lane: `11 passed`. Strings tripwire: `12 passed`.
- Goldens: all 9 SVGs sha256-identical to the pre-task recording (fixtures render from 3-arg rows on the legacy branches — provably and now measured stable). No regeneration needed; run_config.svg untouched.
- ruff clean over the 5 touched files; `ty check` — All checks passed.

**Ledger:** row 33 → fixed via `gsd-tools windows fixed 33`; open_count 9.

## Task 2: WINDOWS #12 — --subset_file seam closeout (verify-and-pin)

**Landed:** `c30ac91` — `test(pipeline): pin sweep-to-child --subset_file seam end-to-end (WINDOWS #12)`

### Premise correction (verbatim from the plan, load-bearing)

> GROUND TRUTH CORRECTION (verified at plan time, 2026-10-19, HEAD 4d8a5e4): the planning context's #12 premise — "run_sweep does not thread --subset_file through; the compose path drops the flag; ~15 lines" — is STALE. The threading is COMPLETE at HEAD: run_sweep parse_args (pipeline/run_sweep.py:433), empty-guard (:1747), abs-resolution (:1805), sweep_flags (:1826), D-14 pre-validation (:1865), run_matrix partial binding (:1504-1513), build_argv two-element append (:1241-1242); run_finetune parse_args (:239-247), validate wiring (:787-800), apply (:1468-1474); TUI compose_argv (tui/services/run_config.py:1146-1148); shard passthrough verbatim. It landed in 07-03 (2026-10-11, commits 5799cbe/040351e) — ONE DAY AFTER WINDOWS #12 was recorded (2026-10-10); the ledger row was never reconciled. The 25 existing subset tests (11 sweep + 14 finetune contracts) are green at HEAD (verified this session). Therefore Task 2 is a VERIFY-AND-PIN closeout, NOT a re-implementation: fix code ONLY if the execution-time re-verification finds a real drop, never fabricate a fix for a non-gap, and state the correction plainly in the SUMMARY.

**Execution-time re-verification:** every waypoint above re-verified intact at HEAD d7a574a by direct source inspection (parse_args flag, empty-guard, abs-resolution, sweep_flags binding, D-14 `_validate_subset_file` pre-validation, `build_argv` `argv += ["--subset_file", str(subset_file)]` two-element append, run_finetune `type=Path` flag, `validate_subset_file` wiring before the model loop, `apply_eval_subset` test-split apply, TUI `compose_argv`). **No real drop found → production pipeline files UNTOUCHED** (`git diff pipeline/` empty; the commit contains tests only).

**What landed (tests only):**
- `tests/test_sweep.py` — `extract_finetune_parse_args()` (exec-extracts run_finetune's `parse_args` from source text into an `{argparse, Path}` namespace — the read-source-never-import idiom; run_finetune is never imported, no test imports it) + `test_build_argv_subset_tail_parses_as_run_finetune_argv`: `build_argv(..., subset_file=<tmp abs path>)`'s tail (element 2 onward) monkeypatched into `sys.argv` parses via the child's OWN parser with `args.subset_file` string-equal to the threaded path (+ target_model/target_dataset/seed); the subset-less twin parses to `subset_file None` (D-12 absent parity). A `--subset_file` naming drift between the two files now makes argparse SystemExit → CI fails — the previously-uncovered cross-file link.
- `tests/test_run_finetune_contracts.py` — `test_committed_eval_subsets_validate_against_current_registry`: the exec-extracted `validate_subset_file` over the committed `pipeline/eval_subsets.json` joined against the CURRENT `pipeline/datasets_info.json` (grown since 05-03 with phase-9/999.1 custom entries) asserts zero problems (keys present, coincident with Dataset_name rows, every ID within its task's Test bound).

**Evidence (test tails):** sweep subset lane `12 passed` (11 pre-existing + 1 new); contracts subset lane `15 passed` (14 pre-existing + 1 new); both full files `213 passed` — the 25 pre-existing subset lanes byte-unmodified and green. ruff clean over both test files + both pipeline files; ty clean; `git status` shows pipeline/ absent from the diff.

**Ledger:** row 12 → fixed via `gsd-tools windows fixed 12`; open_count reaches **8** (remaining opens: the maintainer-ruled model-card stubs #2-#8 and the other-machine smoke #21 — out of this batch's scope, exactly as the plan predicted).

## Deviations from Plan

**1. [Rule 1 - implementation correction] On-demand glyph style: rich-native dim, not $text-muted**
- **Found during:** Task 1 GREEN (first Pilot run).
- **Issue:** the plan specified "the neutral style dim (the ENV_STATE_PENDING kernel-table treatment)" — but the kernel-table `_STYLE_DIM` (`$text-muted`) is a Textual $token that cannot ride rich Text spans on the Static render path (the documented 8.2.8 probe pin in `_render_storage` itself; that is exactly why the function resolves theme success/error at render).
- **Fix:** the on-demand glyph span renders rich-native `"dim"` (the footer-note / migrated-label treatment), matching the note span. Pilot pin asserts both spans `"dim"`. Semantics unchanged: glyph-first, dim, distinct from ✓/✗ under NO_COLOR.
- **Files:** tui/screens/env_check.py, tests/tui/test_pilot_env_check.py. Commit d7a574a.

**2. [Rule 3 - ty compatibility] Extraction/query seams routed through untyped helpers**
- **Found during:** Task 1 and Task 2 gates (`ty check` reported 3 then 7 diagnostics on my new test code).
- **Issue:** (a) ty cannot resolve `screen.query(...)[i].content` (query yields `Widget`; `content` is `Static`'s) and does not narrow through isinstance in that position; (b) ty types a locally-built exec namespace's `namespace["parse_args"]` as a module/type union and rejects calling it.
- **Fix:** house-idiom helpers — `_storage_widget(screen, index)` beside the existing `_storage_row_texts` (the untyped-`screen` seam that already passes ty), and `extract_finetune_parse_args()` module-level (the `extract_subset_fns` idiom from test_run_finetune_contracts.py). Zero test-semantics change.
- **Files:** tests/tui/test_pilot_env_check.py, tests/test_sweep.py. Commits d7a574a, c30ac91.

**3. [Tooling note] `gsd-tools windows fixed <id>` takes no reason argument**
- The plan's action text says to close rows "with a reason"; the tool's signature is exactly one positional id (no `--reason`/`--note`), and the canonical ledger's fixed rows carry empty reason columns (reasons are the waived-row mechanism; see the 72f460a re-render). Rows 33 and 12 were closed via the tool (status-only, per the hard constraint "run them, do NOT hand-edit WINDOWS.md"); the honest reasons live in this SUMMARY (Task 1 and Task 2 sections above), which the ledger workflow treats as the fixed-row rationale record.

## Environmental Knowns (documented, not fixed — per plan)

- `test_storage_overview_defaults_mirror_real_consumers` fails ON THIS BOX only (the maintainer's live run created `pipeline/logs`); failure text byte-identical before/after this batch; green on CI's fresh checkout; the plan EXTENDS-ONLY its truth (log_dir-absent assertion unweakened).
- The intermittent slot-4 pty TIMEOUT did NOT fire in any run this session (Pilot lane 37/37, snapshots 11/11) — no reruns were needed.

## Verification Summary

- Storage service lane: 3 passed + the documented environmental member (identical failure).
- Pilot env + snapshots + strings lanes: 60 passed.
- Sweep + contracts lanes: 213 passed.
- ruff: All checks passed (8 touched files + both pipeline files).
- ty: All checks passed.
- Goldens: 9/9 sha256-identical to the pre-task baseline (`/tmp/gsd-v3g-golden-baseline.txt`); no regeneration, nothing left uncommitted.
- `git status --porcelain`: only `.planning/STATE.md` (orchestrator bookkeeping), `.planning/WINDOWS.md` (ledger closures, committed in the docs commit), `.planning/.gsd-allow-shrink` (pre-existing untracked orchestrator file), and this SUMMARY's directory — no surprises.
- WINDOWS.md: rows 33 and 12 `fixed`; open_count 8, fixed_count 28, total 42.
- Zero GPU execution; zero uv invocations (`.venv/bin/python`, `.venv/bin/ruff`, `.venv/bin/ty` only); no Co-Authored-By trailers on any commit.

## Self-Check: PASSED

- Files: all 7 modified files exist and carry the changes (committed).
- Commits: `d7a574a` and `c30ac91` both ancestors of HEAD on autorun.
- Goldens: byte-identical (diff of sha256 lists empty).
