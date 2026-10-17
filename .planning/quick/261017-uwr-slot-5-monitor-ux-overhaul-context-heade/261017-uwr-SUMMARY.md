---
phase: quick-261017-uwr
plan: 01
subsystem: tui
tags: [monitor, three-state, live-evidence, proc-probe, argv-matrix, glyphs, ordering, textual]

requires:
  - phase: 11-04
    provides: the pure sweep_monitor scanner (cells_view/frontier_scan/entry_fold)
  - phase: 11-03
    provides: SweepLauncher live-sweep registry + kill face
  - phase: 12-03
    provides: the fallback SVG golden lane (make snapshot-update)
provides:
  - Three-state cell derivation (CELL_INTERRUPTED) with live_pairs evidence threading through cells_view/frontier_scan/entries_progress
  - run_config.argv_matrix — the compose_argv inverse (same-source planned-pair recovery, --from-failures included)
  - sweep_launcher.probe_cli_sweeps — the bounded read-only /proc CLI-sweep probe
  - SweepLauncher.live_sweep_matrices — registry ∪ probe evidence behind a per-argv matrix cache
  - MonitorBackend._live_evidence — union live roots + per-root matrices at the screen's service seam; the missing entries_progress delegation (Rule 2)
  - The slot-5 context header (MON_CONTEXT_HEADER), ⏵/⏸ glyphs, live-on-top fold-group ordering with WR-05 cursor identity across reorders
affects: [12-05 gen_progress consumers, slot-5 monitor screen, snapshot goldens]

actuals:
  tokens: 25000    # chars/4 over the realized diff (99720 diff chars, 12 files)
  tasks: 4
  commits: 4        # MEASURED: git rev-list --count 0bdb774..HEAD

plan_head_before: 0bdb774083ac2def16f91353204719486d102dcb
plan_head_after: f3b42ba52c1fd16f1408948fdf9918b9b455803d

tech-stack:
  added: []          # zero new dependencies (no package installs anywhere)
  patterns:
    - "argv inverse as a same-source consumer: pair recovery goes through run_sweep.enumerate_matrix/load_failure_pairs, never a naive cross product"
    - "read-only /proc evidence: display-only liveness data crossing a trust boundary, total parsing, no subprocess/signal ever"
    - "evidence union at the adapter seam with tolerant getattr (pre-existing fakes degrade to legacy semantics)"

key-files:
  created: []
  modified:
    - tui/services/run_config.py
    - tui/services/sweep_launcher.py
    - tui/services/sweep_monitor.py
    - tui/screens/monitor.py
    - tui/strings.py
    - tests/tui/test_services_run_config.py
    - tests/tui/test_services_sweep_launcher.py
    - tests/tui/test_services_sweep_monitor.py
    - tests/tui/test_strings_phase11.py
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_snapshots.py
    - tests/tui/__snapshots__/monitor_running.svg   # regenerated, UNCOMMITTED (D-03)
    - tests/tui/__snapshots__/monitor_empty.svg     # regenerated, UNCOMMITTED (D-03)
    - .planning/WINDOWS.md

key-decisions:
  - "from-failures matrix = the driver's own enumerate-and-filter (load_failure_pairs pairs threaded through enumerate_matrix with the argv's peft/variant), not the bare base pairs — a lora re-run's cells are {model}+lora dirs, so the pairs-verbatim reading would false-interrupt the re-run's own live cells (UWR-2's never-a-false-interrupt governs; for a base re-run the result IS the pairs verbatim)"
  - "MON_PROGRESS_INDETERMINATE rides ⏵ (not ⠋) — the plan's glyph-vocabulary parenthetical ('no constant carries it anymore') demands it and the row's state/progress cells must agree; queue/env/data-manager glyph families untouched (their goldens byte-identical)"
  - "MonitorBackend gains the missing entries_progress delegation (Rule 2): every Pilot fake carried the method but the real adapter never did, so the production progress column was dead — landed with the evidence threading"
  - "live_sweeps()/kill face stay REGISTRY-ONLY at every layer (backend included) — a probed CLI sweep is display-live but never handle-killable; [k] keeps refusing with MON_KILL_UNAVAILABLE"
  - "live_pairs strict-miss at the backend: a root absent from the evidence dict reads the EMPTY frozenset (interrupted), which is exactly the dead-root case; None stays reachable only for direct scanner callers (gen_progress, legacy fakes) — byte-identical semantics there"

patterns-established:
  - "Evidence-union adapter: _live_evidence() merges registry handles with probed roots behind tolerant getattr; the kill predicate deliberately does NOT widen to the union"

requirements-completed: [UWR-1, UWR-2, UWR-3, UWR-4]

metrics:
  duration: 33 min
  completed: 2026-10-17

status: complete
---

# Phase quick-261017-uwr Plan 01: Slot-5 Monitor UX Overhaul Summary

**One-liner:** Three-state cell derivation (⏵ live / ✓ done / ⏸ interrupted) driven by real process evidence (launcher registry ∪ /proc probe -> planned-pair matrices), a one-row context header naming the attached root and its fold counts, and live-on-top ordering with cursor identity — closing WINDOWS #34.

## What Landed (per the maintainer ruling)

### (1) Context header — 「these rows come from WHERE?」

A one-row `no_wrap` Label (`#mon-context-header`) directly under the monitor title bar renders, for the ATTACHED root only (unattached -> empty string, the stats-line precedent):

- zh: `结果目录 {root} · {n} 训练项：⏵{running} 运行 / ✓{done} 完成 / ⏸{interrupted} 中断`
- en: `Output root {root} · {n} cells: ⏵{running} running / ✓{done} done / ⏸{interrupted} interrupted`

n = total entry rows; the three counts are the fold-state families (running / completed / interrupted — failed and queued rows stay visible in the table with their own glyphs but ride no header segment). Counts reuse `_render_cells`'s single per-row `entry_fold` pass (no double derivation; the screen derives nothing from the artifact tree). Attached-with-zero-rows renders n=0 with zero counts — never blank-while-attached. zh copy uses the approved terminology table (结果目录/训练项) over the ruling sketch's 「输出根/对」 wording (the table is binding).

### (2) Three-state derivation — WINDOWS #34 closed

Derivation table (state × evidence -> glyph):

| Cell shape (first match wins) | pair_live=None (legacy/fakes) | pair_live=True (live sweep plans the pair) | pair_live=False (nothing plans it) |
|---|---|---|---|
| readable record status (verbatim, terminal family) | status glyph (✓/✗/⊘/verbatim) | same | same — records always win |
| RESUME_MARKER, no record | ⊘ skipped | same | same |
| checkpoint-*/runs residue or fresh dir mtime, no marker | ⠋→⏵ running | ⏵ running | **⏸ interrupted** (the #34 fix) |
| inert dir (no record/marker/activity) | ◌ queued | ◌ queued | **⏸ interrupted** |
| the root's frontier-newest dir, no marker | ⏵ running | ⏵ running | **⏸ interrupted** (the early-running leg is gated) |

Fold precedence (seed level and frac level, `entry_fold` + `_fold_frac_states`): running > failed > interrupted > completed (all completed|skipped, non-empty) > queued. Interrupted is NOT a terminal record status — `TERMINAL_RECORD_STATUSES`, progress `done` counts, ETA math, and stats totals are untouched. `live_pairs=None` keeps byte-identical legacy semantics for every pre-existing caller (gen_progress included) and fake.

The kill-left PlantHelixSeek (10-16) / dnamamba (10-15) residue in finetuned-smoke now derives ⏸ 中断 — the maintainer's exact symptom.

### (3) Live-on-top ordering

The entries table sorts by fold group: group 0 running rows on top (freshest `CellRow.newest_mtime` first — cells_view fills the row's max seed-dir mtime — mtime-None last), group 1 unfinished non-running rows (failed/interrupted/queued/unrecognized, key ASC), group 2 completed rows sink (key ASC). `_set_table_rows` gained a remove+re-add reorder path (Textual has no move-row API) exercised only when the desired key ORDER changes; steady ticks take the existing in-place update path (zero added churn). The WR-05 cursor-key re-pin (`move_cursor` by key, `scroll=False`) preserves the operator's row identity across reorders — pinned by a Pilot flip test.

## Live-Evidence Design Notes (UWR-2)

- **`run_config.argv_matrix(argv)`** — the compose_argv inverse: pair-scan (recognized flags consume the next element), then the SAME `run_sweep.enumerate_matrix` the driver runs (alias cell names under peft/variant; fraction expansion), so the matrix matches the cell-dir identity. `--models`/`--tasks` absent = the driver's None filters = full-registry legs. `--from-failures` threads the driver's own `load_failure_pairs` + its enumerate-and-filter (run_sweep.py:1878-1896) so alias-lane re-runs stay alias-true. Unparseable shapes (no run_sweep.py element, absent/bad --seeds, out-of-vocab peft/variant, out-of-bounds --curve, unreadable failures manifest -> SystemExit/OSError/ValueError caught) return None = live-but-unknown = legacy rendering, never a false interrupt. Documented accepted edge: `--subset_file` is not re-filtered (over-claim renders queued, the safe direction).
- **`sweep_launcher.probe_cli_sweeps(proc_root="/proc")`** — bounded, read-only, total: numeric pid dirs, NUL-split cmdline bytes (utf-8/replace), Path-name run_sweep.py membership, `--output-root` extraction; a RELATIVE root resolves against `os.readlink(<pid>/cwd)` best-effort (the CLI hand-run edge). Absent proc root -> {} (non-Linux degrades honestly). Filesystem reads only — no subprocess, no signal, ever (a live sweep on this box is only ever read). Display-only evidence (T-uwr-01): it feeds glyphs/headers, never launches/kills/exits; raw argv never renders.
- **`SweepLauncher.live_sweep_matrices()`** — registry live handles (meta.argv) UNION probed roots (registry's argv authoritative on overlap) -> `{resolved root: frozenset[(model, task)] | None}`, behind an instance per-argv matrix cache (a full-matrix argv enumerates its ~8850 cells once per session, not per 2s tick). `live_sweeps()`/`kill_sweep()`/`detach()` byte-untouched.
- **`MonitorBackend._live_evidence()`** — the union seam (tolerant getattr: a launcher without the method degrades to registry-only, the entries_progress precedent); full/frontier/cells/entries_progress thread it; probe roots join the root-level running classification. `live_sweeps()` on the backend stays registry-only (the [k] kill gate never widens to probed roots).

## Golden Regen Outcome (the D-03 review evidence)

Regenerated via `make snapshot-update` (the only regeneration path), deliberately left UNCOMMITTED as working-tree changes — the 261016-vxr #29 pattern; the committed tree fails test_snapshots on exactly these two until the maintainer's D-03 review lands them:

| Golden | sha256 before -> after | Outcome |
|---|---|---|
| monitor_running.svg | e4e803e8bbb8b3a2… -> **a8c1e21f65bc2783…** | expected diff: header line 「结果目录 finetuned-mgpu-w0 · 4 训练项：⏵1 运行 / ✓1 完成 / ⏸1 中断」, ⏵ state + ⏵… progress glyphs, ⏸ 中断 0/1 row, live-on-top order (⏵ dnamamba → ⏸ PlantHelixSeek → ✗ mouse__DMS → ✓ sunk) |
| monitor_empty.svg | 3bcc4dca3c7ed747… -> **3634cead8484d52f…** | NOT byte-identical, but the minimal designed change: the new empty header Label occupies one layout row (all 56 text rows content-identical, shifted one line) + the embedded terminal-id hash; no visible copy change |
| data_manager.svg / data_manager_presence.svg / env_check.svg / run_config.svg / selection_models.svg / selection_datasets.svg / wizard.svg | unchanged | **all 7 byte-identical** (run_config.svg afa89e7e5452e15a… preserved) |

test_snapshots: 11/11 green against the working tree. The ONLY test_snapshots.py edit is the ONE interrupted pair row in `_running_monitor_service` (fixture data; no factory/drive/assertion weakened).

## WINDOWS Ledger

- **#34 resolved in place**: three-state derivation + live-matrix evidence + ⏸ glyph — the PlantHelixSeek/dnamamba residue now derives interrupted.
- **#35 opened (deviation)**: the two regenerated monitor SVGs deliberately uncommitted pending maintainer D-03 review.
- Markdown + JSON mirrored; total_count 34 -> 35 (open 23, fixed 12).

## Deviations from Plan

### Auto-fixed / refined

**1. [Rule 1 - plan-intent refinement] from-failures matrix threads the driver's enumerate-and-filter**
- **Found during:** Task 1 (argv_matrix design)
- **Issue:** the plan's literal "load_failure_pairs pairs verbatim" returns BASE names, but a `--peft lora` from-failures re-run (a first-class flow — the [r] rerun threads the source sweep's lane) creates `model+lora` cell dirs; a base-pair matrix would false-interrupt the re-run's own live cells, violating UWR-2's "never a false interrupt" and "alias cell names must match the cell-dir identity".
- **Fix:** pairs = load_failure_pairs (never re-implemented) filtered through the same enumerate_matrix + base_model_name the driver runs; for a base (none/none) re-run the result IS the pairs verbatim (the plan's test shape). Pinned by `test_argv_matrix_from_failures_lora_rerun_aliases_the_pairs`.
- **Files:** tui/services/run_config.py
- **Commit:** d19672a

**2. [Rule 2 - missing critical functionality] MonitorBackend.entries_progress delegation**
- **Found during:** Task 3 (evidence threading)
- **Issue:** the adapter had NO entries_progress method — the screen's tolerant getattr read {} and the production progress column was dead (every Pilot fake carried the method; the real path never did). The plan's Task 3 action names entries_progress threading at the backend seam, which requires the delegation to exist.
- **Fix:** `MonitorBackend.entries_progress(root)` delegates to `sweep_monitor.entries_progress(root, live_pairs=...)`.
- **Files:** tui/screens/monitor.py
- **Commit:** cc7579e

**3. [Rule 1 - consistency] MON_PROGRESS_INDETERMINATE glyph follows the triple**
- **Issue:** the plan drops ⠋ from MON_STATE_GLYPHS with "no constant carries it anymore", but MON_PROGRESS_INDETERMINATE ("⠋ …") still carried it — the running row would show ⏵ in state and ⠋ in progress.
- **Fix:** "⏵ …"/"⏵ …" (the MON family only; queue/env/data-manager glyph families and their goldens untouched).
- **Files:** tui/strings.py
- **Commit:** cc7579e

**4. [sanctioned value reflections] three existing members updated to new pinned values** (no pin weakened): `test_cells_view_mixed_tree_exact_per_seed_states` expected rows carry the now-filled `newest_mtime` (the plan's own fill requirement); `test_running_entry_without_progress_renders_indeterminate` narrow cell "⠋ 0/1" -> "⏵ 0/1"; the strings glyph-order member reflects the six-state vocabulary. Commits f23d807 / cc7579e.

## Gate Evidence

- `make lint` green; `make typecheck` green (after every task).
- Full suite: **1 failed / 1901 passed** — the single failure is EXACTLY the machine-local baseline member `test_services_run_config.py::test_storage_overview_defaults_mirror_real_consumers` (pipeline/logs exists on this box; pre-existing at the 1F/1869P baseline). Baseline membership holds: 1869P + **32 new tests** (16 argv/probe/matrix + 9 scanner three-state + 7 strings/pilot), zero new failures. make's pytest exit (the known 1F) short-circuited the node lane, run explicitly: **26/26**.
- tests/tui/test_snapshots.py: 11/11 green against the working tree; exactly the two monitor SVGs differ; all 7 non-monitor SVGs sha256-identical.
- Working tree carries the regenerated monitor_*.svg UNCOMMITTED; commits plain (zero attribution trailers); nothing pushed.

## Live-Read-Only Probe Observation (optional step, performed)

A one-off read-only probe (`probe_cli_sweeps()` + `argv_matrix`, fresh `python -I`) found **0 run_sweep.py processes** — the hyenadna finetuned-smoke sweep is not running at 2026-10-17 ~22:59 local (finished or stopped). No live-path confirmation was possible; per the plan's instruction the observation is recorded and skipped silently. The sweep was never signalled, killed, or written at any point.

## Known Stubs

None — every surface landed is wired to real evidence sources (registry handles + /proc probe -> argv_matrix -> scanner derivation -> screen render).

## Maintainer Items (D-03 review queue)

1. Review and commit `tests/tui/__snapshots__/monitor_running.svg` (a8c1e21f…) and `tests/tui/__snapshots__/monitor_empty.svg` (3634cead…) — WINDOWS #35; until they land, the committed tree fails test_snapshots on exactly those two.
2. Restart the console against a populated root (e.g. finetuned-smoke) to read the new screen: header line, ⏵ only on genuinely-live rows, ⏸ on the PlantHelixSeek/dnamamba residue, completed sunk.

## Self-Check: PASSED

All 13 claimed files exist on disk; all 4 commits (d19672a, f23d807, cc7579e, f3b42ba) verified as ancestors of HEAD; commit messages carry zero attribution trailers; the working tree carries exactly the two regenerated monitor SVGs as uncommitted changes (D-03 pending); WINDOWS.md JSON validates with 35 entries (23 open / 12 fixed) matching the markdown table and front matter.
