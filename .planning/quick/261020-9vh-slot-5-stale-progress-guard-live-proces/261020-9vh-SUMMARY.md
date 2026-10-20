---
phase: quick-261020-9vh
plan: 01
status: complete
subsystem: tui-monitor
tags: [monitor, slot-5, stale-progress, reused-root, live-start-evidence, proc-probe, tolerant-seam, pty-lane, goldens]
commits:
  - 4997239
  - b15be8d
files:
  - tui/services/sweep_monitor.py
  - tui/services/sweep_launcher.py
  - tui/screens/monitor.py
  - tui/screens/run_config.py
  - tests/tui/test_services_sweep_monitor.py
  - tests/tui/test_services_sweep_launcher.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pty_driver.py
goldens_no_delta:
  all_9_svgs_sha256_identical_before_after: true
  monitor_running_svg: 258ab609191b89ff6ffae7cbca91537bbb69a2445391c812dc5e845344e2d000
  monitor_empty_svg: d468d33791cb75877b6232c3bdd461fb832aacb76f513dd36e2c7e5f56017289
windows_entry: "none opened — no stubs, no skipped tests, no unrun verifies; goldens were NOT forced (no regeneration run)"
duration_minutes: 23
---

# quick-261020-9vh: slot-5 stale-progress guard — a reused root never renders the previous killed run's numbers — summary

The stale-checkpoint guard: when a root is LIVE (launcher registry
spawn moment OR /proc probe start time), a running pair whose NEWEST
checkpoint's trainer_state.json FILE mtime PREDATES the live process's
start renders the EXISTING honest indeterminate grammar (MON_PROGRESS_INDETERMINATE
/ glyph-only / the dim dash) — never the previous run's numbers (the
maintainer's 40%-from-checkpoint-19968 case). Only the NUMBERS go
unknown: the cell's STATE stays RUNNING (checkpoint presence is the
activity signal), so glyphs, strip counts, done/total, elapsed/ETA are
untouched; the moment the live run saves its own first checkpoint
(mtime >= start) the real numbers return automatically — zero
render-tier changes, zero new operator copy, zero new sig legs. Every
fallback (no method / raising / non-numeric / unprobed root / missing
stat or btime / non-Linux) keeps today's parse — pinned, not assumed.

## Task 1 — the guard + the evidence seam + the threading + tier-1 pins (commit 4997239)

**Landed:**
- `sweep_monitor.cell_progress` gains the ADDITIVE `stale_before=None`
  (the guard between the best-checkpoint selection and the parse:
  `_trainer_state_mtime` — the VXR-1 wall-clock source — None-or-
  strictly-`<` returns the all-None CellProgress; the `==` boundary
  parses); `entries_progress` gains `live_started=None` threaded as
  `stale_before` into each running seed's parse — the EXISTING
  `progress.step is None` drop omits the pair, so every consumer
  (entries cell, pane, tree labels, wide table, drill) renders the
  existing honest grammar with zero render-code changes. Module +
  function docstrings record the 261020-9vh contract.
- `sweep_launcher`: the `/proc` walk shared into `_iter_cli_sweeps`
  (`probe_cli_sweeps` rewritten over it — behavior byte-identical, its
  3 tests + every monkeypatch fake untouched); NEW
  `probe_cli_sweep_starts(proc_root)` (module-level, monkeypatchable
  independently — hermetic) over `_boot_time` (`<proc>/stat` btime
  line) + `_clock_ticks` (`SC_CLK_TCK`) + `_proc_start_epoch`
  (`<pid>/stat` post-paren index 19 = field 22, `btime + ticks /
  CLK_TCK`; every OSError/ValueError/IndexError -> None); NEW
  `_iso_to_epoch` (tz-aware registry stamps round-trip exactly — a
  naive parse would fabricate staleness by the local offset); NEW
  `SweepLauncher.live_sweep_started()` — registry `started_at` first,
  probe union via `setdefault` (registry wins per root, the
  live_sweep_matrices precedence). DISPLAY-ONLY throughout.
- `run_config.LauncherBackend.live_sweep_started()` one-line forward
  under `live_sweep_matrices` (the 2026-10-19 reattach lesson: the app
  injects THIS facade into MonitorBackend — without the forward the
  guard is dead in production wiring).
- `monitor.MonitorBackend._live_started_for(root)` (the
  `_live_evidence` tolerant-getattr idiom: launcher None / no method /
  raising / bool-or-non-numeric -> None = today's parse) +
  `entries_progress` threads `live_started=` — the single call site
  both cadence workers and the drill read ride. NOT declared in
  MonitorServiceProtocol / MonitorLauncherProtocol (no fake is ever
  ty-flagged).

**Pins:** `test_cell_progress_stale_before_degrades_all_none` (stale /
fresh-vs-earlier-start / param-absent / `==`-boundary legs);
`test_entries_progress_live_started_guards_stale_checkpoints` (drop /
None-fallback / fresh-pair control); `test_probe_cli_sweep_starts_
reads_stat_and_btime` (exact epoch `btime + ticks/SC_CLK_TCK` /
missing-stat tolerance / missing-btime `{}`);
`test_live_sweep_started_merges_registry_iso_and_probe` (registry via
the injectable `launch_argv` clock pinned to a fixed tz-aware
datetime -> exact epoch; probe adds the CLI root + a DIFFERENT value
under the registry root -> setdefault keeps the registry's);
`test_backend_entries_progress_threads_live_started_guard` (tier-1,
beside the reattach pin :2936 — REAL MonitorBackend over the
LauncherBackend facade, both probes monkeypatched to the tmp root,
start now-60s -> NO entry for the ~13h-stale pair; starts probe `{}`
-> the 40% entry returns; a SimpleNamespace launcher with matrices
but without the method -> same today-behavior).

**Test evidence:** service files **151 passed** (147 baseline + 4 new);
pilot selector 3 passed (the new backend pin + reattach + indeterminate
render pins); full pilot file **105 passed**; ruff + `ty check tui/
tests/` clean.

## Task 2 — the pty production-path pin + goldens no-delta + full gates (commit b15be8d)

**Landed (tests/tui/test_pty_driver.py):** the member-local
`_fabricate_stale_progress_root` (GUE__emp_H3 pair: checkpoint-120
with the FULL {"global_step": 19968, "max_steps": 49911} payload, the
pair's whole subtree os.utime'd ~1h stale — the `_fabricate_
interrupted_root` idiom; GUE__prom_300_all pair: FRESH checkpoint-121
{"global_step": 60, "max_steps": 300}; returns `(root, fresh_state)`
so the member re-pins the fresh mtime AFTER the sleeper fork — a
fixture-time mtime would predate the start and the guard would take
the fresh pair too) + `test_monitor_stale_progress_guard_with_probed_
live_process`: a REAL sleeper (`python -c 'import time;
time.sleep(120)' run_sweep.py --models … --output-root <root>` — zero
GPU, zero run_sweep code) spawned before the console, so the REAL
console's REAL MonitorBackend derives live evidence through the REAL
/proc + facade and the guard fires end-to-end: the matrix drain
carries the RUNNING glyph (state untouched) and NEVER "19968"; w->w
reaches the wide table (the full-width surface for the shared
`_entry_progress_cell` grammar) whose drain carries the fresh pair's
"60/300 20%" AND the stale pair's "⏵ …" and never "19968". The shared
`_fabricate_running_root` and every prior member byte-untouched. The
sleeper terminates in the outermost finally; the maintainer's real
sweep (different root key) is only ever read.

**Test evidence:** pty lane **14/14** (13 prior members green and
byte-stable + the new production-path member; ONE transient
`test_slot4_gate_refusal_is_visible` pty flake in the first full-lane
run — passed standalone and in the full-lane retry; slot-4 surface,
untouched by this change); snapshot lane **11/11** with **goldens
NO-DELTA** — all 9 SVGs sha256-identical before/after (`/tmp/
9vh-goldens-before.txt` vs after; monitor_running 258ab609…,
monitor_empty d468d337… — the committed b84afc0 bytes; NO regeneration
needed or run); full suite `pytest tests/tui -q` **1286 passed** with
NO deselect (the storage member is hermetic since 46cb37f — the
plan's deselect clause is obsolete); ruff + `ty check tui/ tests/`
clean; `git status --porcelain` confined to the committed test file +
this bookkeeping; no Co-Authored-By trailers; the live sweep
(PID 3623080, finetuned-smoke) read-only throughout; zero GPU launches.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — test-fixture timing] the live start must sit BETWEEN the two checkpoint writes**
- **Found during:** Task 1, the entries_progress service pin.
- **Issue:** the first draft passed `live_started=NOW_REAL()` evaluated
  at CALL time — after BOTH writes — so the fresh control pair was
  milliseconds-stale vs the start and the guard dropped it too
  (empty map).
- **Fix:** the start pins to `NOW_REAL() - 10` — after the stale
  write, before the fresh write (the reused-root shape in miniature).
- **Files:** tests/tui/test_services_sweep_monitor.py. **Commit:** 4997239.

**2. [Rule 3 — blocking] GUE__virus_species_4 is NOT a committed-registry task**
- **Found during:** Task 1, the pilot backend pin (KeyError: the 40%
  entry never returned because the pair derived INTERRUPTED).
- **Issue:** the plan's task key resolves to an EMPTY planned matrix
  in `run_config.argv_matrix` (the registry does not carry
  GUE__virus_species_4), so the probed live-pair evidence never covers
  the pair and the cells derive interrupted, not running — the pinned
  render is unreachable with the plan's names.
- **Fix:** registry-member keys — GUE__emp_H3 (the reattach pin's own
  key) in the pilot pin; GUE__emp_H3 + GUE__prom_300_all in the pty
  fixture. Same truth, load-bearing assertions unchanged.
- **Files:** tests/tui/test_pilot_monitor.py, tests/tui/test_pty_driver.py.
  **Commits:** 4997239, b15be8d.

**3. [Rule 3 — surface] the drill modal's progress column falls off its right edge**
- **Found during:** Task 2, the new pty member (the drill drain showed
  both rows' state but an empty progress column).
- **Issue:** at 120 cols the RunCellsModal's ~60-col table renders
  model/task/state and clips the progress column — neither "20%" nor
  "⏵ …" is observable on the drill surface.
- **Fix:** the member pins the progress grammar on the [w] WIDE table
  (the plan's own truth #1 names it; full 120-col width renders the
  shared `_entry_progress_cell` form for BOTH pairs side by side —
  verified: "⏵ running … ⏵ …" beside "⏵ running … 60/300 20%"). The
  matrix-drain legs (RUNNING glyph present, 19968 absent) unchanged.
- **Files:** tests/tui/test_pty_driver.py. **Commit:** b15be8d.

**4. [Plan-wording superseded] the full-suite deselect is obsolete**
- The plan's verify deselects
  `test_storage_overview_defaults_mirror_real_consumers` as
  environmental; the member has been hermetic since 46cb37f (the
  orchestrator's standing constraint). The suite ran with NO deselect:
  1286 passed, zero failures.

### Transients

- `test_slot4_gate_refusal_is_visible` failed ONCE in the first
  full-lane pty run, then passed standalone AND in the full-lane
  retry (the documented slot-4 flake class; no monitor interaction).

## Verification-gate cross-check

- Task 1 gate: 151 service-file passes (147 baseline + 4 pins) + the
  3-member pilot selector + ruff/ty clean — green.
- Task 2 gate: pty lane 14/14; snapshot lane 11/11; goldens sha256
  no-delta (all 9); full tui suite 1286 passed (no deselect); ruff +
  ty clean; status confined — green.
- Live repro respect: PID 3623080 / finetuned-smoke read-only (the
  pty probe reads cmdline/stat only); zero GPU launches; all pty work
  on isolated tmp roots.

## Self-Check: PASSED

Commits 4997239 and b15be8d are ancestors of HEAD; the eight scoped
files landed in them; all 9 goldens sha256-identical to the committed
bytes (no regeneration, no SVG in the worktree); no attribution
trailers; the maintainer's live sweep untouched.
