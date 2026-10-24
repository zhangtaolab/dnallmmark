---
phase: quick-261020-blt
plan: 01
status: complete
subsystem: tui-monitor
tags: [monitor, running-tab, planned-cells, queued-rows, live-sweep-plans, seeds, union, pty-lane, goldens]
commits:
  - 7e90a0b
  - 68a74fb
files:
  - tui/services/run_config.py
  - tui/services/sweep_launcher.py
  - tui/screens/run_config.py
  - tui/screens/monitor.py
  - tests/tui/test_services_run_config.py
  - tests/tui/test_services_sweep_launcher.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pty_driver.py
goldens_no_delta:
  all_9_svgs_sha256_identical_before_after: true
  monitor_running_svg: 258ab609191b89ff6ffae7cbca91537bbb69a2445391c812dc5e845344e2d000
  monitor_empty_svg: d468d33791cb75877b6232c3bdd461fb832aacb76f513dd36e2c7e5f56017289
windows_entry: "none opened — no stubs, no skipped tests, no unrun verifies; goldens NOT forced (no regeneration run); strings.py untouched"
duration_minutes: 28
actuals:
  tokens: 15100   # chars/4 over the realized code diff (60457 chars / 4)
  tasks: 2
  commits: 2       # 7e90a0b + 68a74fb (measured: git rev-list 99b687e..68a74fb)
---

# quick-261020-blt: slot-5 planned-but-unstarted cells render QUEUED — summary

The maintainer's twice-reported "only one model shows" case
(2026-10-20 07:08 live, 08:17 live; reproduced and root-caused by the
orchestrator) is fixed end-to-end: a 2-model CLI sweep that dies in
model-1's first cell leaves model-2 with NO dirs on disk, and the
Running tab now renders the WHOLE plan anyway — every
planned-but-undiscovered (model, task) pair synthesizes a QUEUED row
through the existing grammar, every discovered row completes its
planned-but-unstarted seeds as queued, and off-plan residue seeds
drop when (and only when) the plan's seeds are known (the o8e law at
seed level). Counts count the UNION: the strip's glyph counts +
done/total, the tree's model labels, and the [w] wide table derive
over discovered ∪ planned — total = Σ pairs × planned seeds (the
repro: 4 pairs × 3 seeds = 0/12). The evidence chain is
`run_config.argv_plan` (the argv_matrix parse body verbatim,
returning (pairs, seeds); argv_matrix delegates byte-compatibly) ->
`SweepLauncher.live_sweep_plans` (registry argv authoritative per
root, the /proc probe union behind the per-argv `_plan_cache`;
`live_sweep_matrices` is now the leg-0 projection — its 3 tests and
every monkeypatch fake untouched) -> `LauncherBackend.live_sweep_plans`
(the facade forward; app.py build_monitor_screen:816 injects this
facade as the monitor screen's launcher_service) ->
`MonitorScreen._read_live_plans` (worker-side, tolerant; the o8e
pairs-only adapter over `live_sweep_matrices` keeps every pre-blt
double's render byte-identical) -> `_root_scoped_rows` — THE one
per-root seam. The drill (RunCellsModal), History, and [e] read the
SERVICE `cells_view` (root-wide discovered truth): a synthesized row
never reaches them, by construction not by filter. The gate law holds
by construction — the union's models/tasks tuples join the cards
signature's shape legs (a plan landing mid-session rebuilds once),
and the union is a pure function of (plan, discovered rows), so
steady ticks write zero.

## Task 1 — the evidence chain + the screen union + the pilot pins (commit 7e90a0b)

**Landed:**

- `tui/services/run_config.py`: NEW `argv_plan(argv, registry_dir=None)
  -> tuple[frozenset[tuple[str, str]], tuple[int, ...]] | None`
  directly under `argv_matrix` — the argv_matrix parse body VERBATIM
  (the run_sweep.py element test, `_argv_flag_values`, the
  seeds/peft/config-variant/curve validations, `enumerate_matrix`,
  the `--from-failures` filter) with the return changed to
  `(pairs, seeds)`; `argv_matrix` rewritten as the delegation
  (`plan[0] if plan is not None else None`). Docstrings record the
  261020-blt contract (pairs non-None IMPLIES seeds non-empty through
  this reader).
- `tui/services/sweep_launcher.py`: `_matrix_for`/`_matrix_cache` ->
  `_plan_for`/`_plan_cache` over `run_config.argv_plan` (same
  argv-tuple keying, the moved ~8850-cells enumerate-once rationale);
  NEW `live_sweep_plans()` (registry legs first over
  `live_sweeps()`/`meta.argv`, probe union via `if root not in plans`;
  None = live-but-unknown; DISPLAY-ONLY); `live_sweep_matrices()`
  rewritten as the one-line leg-0 projection.
- `tui/screens/run_config.py`: `LauncherBackend.live_sweep_plans()`
  one-line forward under `live_sweep_started`, docstring citing the
  facade lesson (the union would be dead in production wiring without
  it — pinned end-to-end by Task 2's pty member).
- `tui/screens/monitor.py`: `_read_live_matrices` ->
  `_read_live_plans` with the reader precedence (plans getter first;
  ABSENT -> the o8e adapter `{root: (value, None) if frozenset else
  None}`; both absent / any raising call -> None = keep the previous
  cache); `FullScanned`/`FrontierScanned` `matrices` legs ->
  `plans` (both worker reads, both handler stores — the
  store-BEFORE-render order and the load-bearing flap comment kept
  verbatim); `self._live_matrices` -> `self._live_plans`; NEW
  `_root_live_plan(root)` (the tuple only when leg 0 is a non-empty
  frozenset) with `_root_live_pairs` reading leg 0 (same None
  vocabulary, the screen-None-vs-service-empty divergence paragraph
  kept); NEW `_root_scoped_rows(root)` — THE one per-root seam (the
  o8e drop, then the union in three legs: synthesized all-queued rows
  for missing pairs over the seed basis; discovered rows rebuilt to
  EXACTLY the known planned seeds — discovered CellSeeds verbatim,
  missing ones queued, off-plan residue dropped; a BORROWED basis
  stays verbatim, never a fabricated seed number; an empty borrow
  synthesizes name-only rows); `_card_rows` merges `_root_scoped_rows`
  over `card.roots` (the `_merge_group_rows` call unchanged — queued
  priority 4 loses to every discovered state); `_render_wide` reads
  the seam instead of the raw `_cell_rows` + inline filter;
  scope-law comments on `_read_run_cells` and `_run_resume_launch`
  (both read the SERVICE cells_view); module docstring gains the blt
  paragraph. NO gate code, NO strings.py change, NO service-tier
  change (MonitorBackend + the Protocols untouched).
- Pins: `test_argv_plan_returns_pairs_and_seeds` (the verified 2x2
  argv -> the literal 4-pair frozenset + (42,43,44); the no---seeds
  argv -> None; argv_matrix over the same argvs through the
  delegation); `test_live_sweep_plans_carries_pairs_and_seeds`
  (registry multi-model argv -> (4 pairs, (42,43,44)); probe root
  joins; broken argv -> None; live_sweep_matrices = leg-0 / None over
  the same launcher; the enumerate spy counts once per distinct argv
  across BOTH methods — the broken argv never enumerates);
  `FakeMonitorLauncher` gains `live_plans` (the live_matrices pattern;
  the existing `live_matrices` param stays so the o8e pins keep
  exercising the adapter); THREE pilot pins —
  `test_planned_cells_union_renders_queued_rows_and_counts` (the
  maintainer's case: BOTH models render, ⏵1 + ◌11, 0/12 not 1/36,
  the discovered cluster ⏵◌◌, the wide table 12 rows with model-2's
  6, and the drill from a focused SYNTHESIZED group lists ONLY the
  discovered model with the cursor at row 0 through the in-rows
  guard),
  `test_planned_union_pairs_only_adapter_never_fabricates_seeds` (the
  discovered row's own single seed verbatim — never ⏵◌◌; the three
  missing pairs borrow seed 42 -> ⌵1 ◌3 0/4; never 0/12 or 1/36),
  `test_planned_union_joins_structure_signature_steady_silent`
  (empty-holder root-wide ONE model -> plan lands -> REBUILD with
  ListItem identity changed, TWO models -> steady tick zero clears +
  zero Label writes, identity survives).

**Test evidence:** service files **227 passed** (155 run_config incl.
the new pin + 70 launcher incl. the new pin + 2 pre-existing in the
selected set; baseline 225 + 2 new); pilot selector **16 passed**
(13 baseline + 3 new); full pilot file **108 passed** (105 + 3); ruff
+ `ty check tui/ tests/` clean over every touched file.

## Task 2 — the pty repro pin + goldens no-delta + full gates (commit 68a74fb)

**Landed (tests/tui/test_pty_driver.py):** the member-local
`_fabricate_partial_matrix_root` (ONLY
plant-dnabert-6mer/GUE__emp_H3/seed_42/checkpoint-120 with fresh
mtimes — the no-manifest grace classifies the root RUNNING; NOTHING
else exists under the root) +
`test_monitor_planned_but_unstarted_cells_render_queued`: a REAL
CPU-sleep sleeper (`python -c 'import time; time.sleep(120)'
run_sweep.py --models plant-dnabert-6mer,plant-dnamamba-6mer --tasks
GUE__emp_H3,GUE__prom_300_all --seeds 42,43,44 --output-root <root>`,
cwd=tmp_path, spawned BEFORE the console) drives the REAL production
chain — the REAL /proc probe -> live_sweep_plans -> the
LauncherBackend facade forward -> the screen union — and the drained
Running paint asserts BOTH model rows ("dnabert-6mer" AND
"dnamamba-6mer" — the fixture has NO dnamamba dirs, so the string can
only come from the synthesized row), the strip total "0/12", and the
running glyph. The registry warning is honored in the fixture and
docstring: GUE__emp_H3 + GUE__prom_300_all enumerate for BOTH models
(exactly 4 pairs re-verified live at execution time); the plan's
GUE__virus_species_4 prohibition is recorded beside it. The sleeper
is pid-scoped (`sleeper.terminate(); sleeper.wait()` in the outermost
finally); the probe only ever READS /proc; zero GPU, zero run_sweep
code executed. The shared `_fabricate_running_root` and the 14 prior
members are byte-untouched.

**Test evidence:** pty lane **15/15** (14 prior + the new member);
snapshot lane **11/11** with **goldens NO-DELTA** — all 9 SVGs
sha256-identical before/after (`/tmp/blt-goldens-before.txt` vs
after; monitor_running 258ab609…, monitor_empty d468d337… — the
committed bytes; NO regeneration needed or run; no SVG in the
worktree); full tui suite **1292 passed** with NO deselect (the
storage member stayed green — hermetic since 46cb37f, the 9vh
finding); ruff + `ty check tui/ tests/` clean; `git status
--porcelain` confined to the one test file + the orchestrator's
`.planning` bookkeeping; no Co-Authored-By trailers; the maintainer's
live /proc processes read-only throughout (the pty probe reads
cmdline only; only OUR Popen was ever signaled); zero GPU launches.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — i18n lock] the module-docstring paragraph quoted the
maintainer's Chinese complaint verbatim**
- **Found during:** Task 1, the full pilot file run
  (`test_monitor_module_carries_zero_chinese_literals` — 7 Chinese
  characters found in monitor.py).
- **Issue:** the plan's objective text names the case with its
  Chinese phrase; my first docstring draft carried it into
  monitor.py, which the zero-Chinese-literals grep lock forbids
  (Chinese lives in strings.py only — and strings.py is
  out of scope by constraint).
- **Fix:** the docstring says "only one model shows" (English);
  the Chinese phrase survives only in the plan and the TEST file's
  docstring, where the lock does not apply (the pilot module
  docstring itself already carries Chinese task copy).
- **Files:** tui/screens/monitor.py. **Commit:** 7e90a0b.

**2. [Plan-wording imprecision, same-truth] "FOUR mon-matrix-row
texts" and the pairs-only leg's "0/1"**
- **Found during:** Task 1, the first run of the new pilot pins.
- **Issue:** the matrix grammar is one row per MODEL with per-TASK
  columns (the o8e fallback pin's "4 rows" fixture simply had 4
  distinct models), so the 2-model plan renders TWO matrix rows whose
  clusters carry the four pairs; and in the pairs-only leg the strip
  counts the whole union's honest basis (⏵1 + ◌3 = 0/4), not the
  discovered row's lone 0/1.
- **Fix:** the maintainer-case pin asserts len(rows) == 2 with BOTH
  model names, the discovered cluster "⏵◌◌" beside the all-synthesized
  "◌◌◌", and model-2's row entirely queued; the pairs-only pin
  asserts the discovered cluster is exactly one glyph (never ⏵◌◌),
  ⏵1 + ◌3, 0/4, and never 0/12 or 1/36. The load-bearing truths
  (both models render; counts over the union; seeds never fabricated)
  are exactly the plan's.
- **Files:** tests/tui/test_pilot_monitor.py. **Commit:** 7e90a0b.

**3. [Plan-wording superseded] the full-suite deselect + the
uncommitted-SVG note**
- The plan's Task 2 gate deselects
  `test_storage_overview_defaults_mirror_real_consumers` and expects
  monitor_running.svg/monitor_empty.svg as UNCOMMITTED worktree bytes
  under WINDOWS #42; both statements predate 46cb37f/9vh — the
  storage member is hermetic and the two SVGs are the committed
  bytes with no worktree copy. The suite ran with NO deselect
  (1292 passed) and the goldens verified sha-identical against the
  committed bytes.

## Verification-gate cross-check

- Task 1 gate: service files 227 green (the argv_plan +
  live_sweep_plans pins among them); pilot selector 16 green (the 3
  new pins + the 4 o8e pins + the fallback + reattach pins through
  the adapter); ruff + ty clean — green.
- Task 2 gate: pty lane 15/15 with the repro member's BOTH-models +
  0/12 assertions over the REAL production path; snapshot lane 11/11;
  goldens sha256 no-delta (all 9, before/after record above); full
  tui suite 1292 passed; ruff + ty clean; git status confined —
  green.
- Scope law: the drill pinned at the synthesized-focus leg (model-2
  absent from the modal, cursor row 0); History/[e] read the service
  cells_view by construction; strings.py and the service tier
  untouched.
- Hard constraints: atomic plain commits with no attribution
  trailers; `.venv/bin/python` only; zero GPU (the sleeper is a pure
  CPU sleep); `live_sweep_matrices` byte-compatible (its 3 tests +
  every fake untouched; the 4 o8e pins green unedited through the
  adapter); the union joins the structure signature + steady
  zero-write pinned; goldens sha-verified no-delta; the registry
  warning honored (GUE__emp_H3 + GUE__prom_300_all, both re-verified
  to enumerate 4 pairs at execution time); scope confined to the
  plan's 7 files + strings.py untouched.

## Self-Check: PASSED

Commits 7e90a0b and 68a74fb are ancestors of HEAD; the eight scoped
files landed in them; all 9 goldens sha256-identical to the committed
bytes (no regeneration, no SVG in the worktree); no attribution
trailers; the maintainer's live processes read-only; zero GPU.
