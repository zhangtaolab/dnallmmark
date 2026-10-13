---
phase: 11-run-config-launch-gates-single-gpu-monitoring
review_path: 11-REVIEW.md
disposition_at: 2026-10-13
fixer: gsd-code-fixer (Claude)
commits: 12
status: applied
---

# Phase 11: Code Review Fix Disposition

**Source review:** `11-REVIEW.md` (2026-10-13, deep, 14 findings: 2 CR / 7 WR / 5 IN)
**Branch:** `autorun` (fix commits landed via the review-fix worktree, fast-forwarded)

## Per-finding table

| ID | Verdict | Commit | What landed |
|----|---------|--------|-------------|
| CR-01 | **fixed** | `f974d0c` | `[f]→[r]` from-failures re-run now gated like `launch_spec` |
| CR-02 | **fixed** | `d6a5a69` | duplicate-root launch refused (service guard + problems-stage surface) |
| WR-01 | **fixed** | `3a1fb71` | re-run carries the source sweep's PEFT/variant lane |
| WR-02 | **fixed** | `73f37bb` | stats/elapsed/ETA scoped to the current run at a populated root |
| WR-03 | **fixed** | `621925c` | gate + re-run workers wrapped; exceptions surface, never wedge |
| WR-04 | **fixed** | `e5f3e37` | live registry prunes exited Popens at read time |
| WR-05 | **fixed** | `50cddc7` | diff-preserving table updates; cursor survives cadence ticks |
| WR-06 | **fixed** | `abde757` | both `./finetuned` resolution homes scanned by default |
| WR-07 | **fixed** | `47dd63f` | typed gate fails closed on an empty expected phrase |
| IN-01 | **fixed** (doc) | `27efd69` | `DirPlan.cache_dir_abs` docstring corrected |
| IN-02 | **kept open** | — | policy: custom-key `+lane-suffix` validation (see below) |
| IN-03 | **kept open** | — | watch-at-smoke: stats re-read cost per 2s tick (see below) |
| IN-04 | **kept open** | — | polish: inline `sweep_scale` on the event loop (see below) |
| IN-05 | **fixed** | `27efd69` | tee path survives detach/kill via launch history |

Follow-up: `3fa3fea` — ty conformance for the new protocol members
(Pilot fakes + the app-facing `LauncherServiceProtocol.phrase_matches`).

## Fix notes

### CR-01 — the E2' gate on the re-run path

`launch_from_failures` now recomputes the effective matrix BEFORE
composing: `run_sweep.load_failure_pairs(path, DEFAULT_REGISTRY_DIR)` ×
the requested seeds, wrapped in a synthetic `RunSpec` and judged by the
REAL `run_config.is_full_e2x` (zero copied matrix logic, D-05).
Refusal order mirrors `launch_spec`: official-keys diagnostic and an
unevaluatable manifest (`SystemExit`/`OSError`/`ValueError` from the
driver's own parser, message unwrapped from `SystemExit.code`) refuse
at stage `problems`; an E2'-class effective matrix (pairs superset
official ∧ ≥3 seeds — a genuine complete failures manifest over the
sweep's 3 seeds) demands the exact typed phrase at stage `phrase`. The
monitor's phrase-stage refusal re-prompts the same `E2PhraseModal` as
slot 4 and re-launches WITH the typed phrase; a problems refusal
surfaces as the launch-failed toast naming the problems (never a
silent no-op). The raw `launch_argv` seam stays ungated BY DESIGN
(pinned by `test_launch_argv_e2x_shaped_matrix_argv_is_not_phrase_gated`,
docstring updated — the retired "never the full matrix by construction"
warning is superseded by the real gate, exactly as the fix scope
directed). `run_sweep` itself is untouched — the gate lives entirely
in the TUI service layer.

### CR-02 — duplicate-root guard

`_spawn` refuses when the resolved root holds a live entry
(`poll() is None`): failed `LaunchOutcome` naming the live root; the
first entry survives (Popen still killable, tee fd still owned); the
spawner is never consulted. A dead entry is pruned (handle dropped, tee
closed) and the root reclaimed — self-heal. The run-config gate
pipeline additionally refuses at the problems stage
(`("live_root", root)` — data rendering per the `official_keys`
precedent) BEFORE the env preflight or any confirm. The monitor's
re-run path surfaces the service refusal through the existing failed
toast.

### WR-01 — the lane

`sweep_monitor.rerun_lane(root)`: `config_variant` from the manifest's
merged per-cell `config_variant` sweep flag (the ONLY source that
catches `head`, which keeps base names for the frozen pair); `peft`
from the failures entries' `model`/`base_model` alias pair. Read
through the `MonitorServiceProtocol` seam inside the re-run worker,
threaded into `launch_from_failures` — never a `none/none` default for
a lane sweep.

### WR-02 — run scoping

With a `fallback_start` injected (the TUI noted a run at this root —
the `[f]→[r]` flow), `stats()` scopes records to `started_at >=` the
start (unparseable stamps drop) and a manifest whose mtime predates
the start is stale (supplies neither total nor per-model ETA plan)
until the run's own manifest lands at sweep end.
`note_launch(root, 0)` (the re-run note) clears the stale
`_expected_totals` entry. Without the injection (CLI-launched /
finished views) the unscoped behavior is byte-identical. **Known
accepted edge (pre-existing, plan-pinned class):** `resume_count`
mid-re-run at a populated root still reads the prior manifest's skip
count — same stale-manifest-until-end shape as the pinned
classification predicate order; NOT widened in this pass. Resumed
cells whose old records predate the launch are excluded from `done`
(the reviewer's accepted tradeoff; fresh-root launches — the common
path — are unaffected).

### WR-03 — worker wrapping (+ sibling audit)

The four gate workers post `GateWorkerError` on any exception; the
handler validates the run id (stage or launch space), releases
`_gate_active`, and toasts `LNC_LAUNCH_FAILED_TOAST` — the
confirm-then-crash worst instance surfaces. Siblings found and
covered: the mount `_load` worker joins the same surface (never a
silently blank screen); `_run_preview` degrades tolerantly (previous
line stands; the same fault resurfaces at the next gate attempt — no
per-keystroke toast flood); the monitor's `_run_rerun_preflight` /
`_run_rerun_launch` post `RerunFailed` → the same toast (a
confirm-then-crash re-run is never silent); `LogTailModal._refresh_tick`
skips a raised read. The monitor's scan workers were already tolerant
(unchanged).

### WR-04 — registry pruning

`live_sweeps()` polls every entry and prunes the dead (entry dropped,
parent-side tee closed); `MonitorBackend._live_roots` and the
ExitModal predicate inherit it. Dead-without-manifest roots degrade to
the scanner's honest mtime/artifacts classification. The five
liveness-asserting tier-1 tests moved to an alive-Popen fixture (the
dead-by-default fake was asserting the pre-fix accident).

### WR-05 — diff-preserving tables

`_set_table_rows` (the `PickerList.set_rows` precedent carried to
`DataTable`): columns rebuild only on a key-set change (narrow toggle,
new seed column); known rows `update_cell` in place, new rows append,
vanished rows drop; the cursor re-pins to its ROW KEY with
`scroll=False`. Both monitor tables render through it; the
mount-time column pre-build is gone. **Sibling audit note:** the
phase-8 selection screen's `_rebuild_rows` still clear+rebuilds —
operator-initiated (view switch/filter/mark), NOT cadence-driven, and
outside the phase-11 diff; left untouched per the surgical-fix
constraint.

### WR-06 — both homes

`DEFAULT_OUTPUT_ROOTS = (pipeline/finetuned, finetuned)` — the TUI
launch home (cwd pinned to `pipeline/`) and run_sweep's documented
repo-root CLI home. Nonexistent roots skip silently. The pinned
constants tripwire test updated accordingly.

### WR-07 — fail closed

`phrase_matches` returns `bool(expected) and typed == expected`; an
output root resolving to the filesystem root can never match (not
even the empty string). `validate_composition` refuses such a root as
`("output_root_invalid", value)`; rendered through the new
`CFG_OUTPUT_ROOT_PROBLEM` copy, registered in the bidirectional
strings inventory (`EXPECTED_CFG_CONSTANTS`).

### IN-05 — tee history

`tee_path_for` falls back to `_tee_history[root]` (recorded at spawn;
relaunch overwrites) when the live entry is gone — `[t]` never
renders the false "CLI-launched, no tee" copy for a TUI-launched
sweep after the exit modal's default detach. Implemented in the
launcher service (one place covers slot-4 launches AND re-runs)
rather than monitor-side state — same honesty, less plumbing than
the suggested `_expected_totals`-adjacent dict.

## Kept-open rationale

- **IN-02 (alias-namespace collision, `+lane-suffix` custom keys):**
  policy, not mechanics — refusing custom registry keys containing
  `+lora/+ia3/+head/+probe/+curve` (or refusing when a derived alias
  equals another key) is a validation-boundary decision that affects
  hand-authored overlays that may already exist on operator machines.
  The correct vehicle is a sweep-start collect-all in `run_sweep`
  (mirroring `_validate_dataset_name_alignment`), which per the fix
  discipline is a `pipeline/` change this review's minimal fixes did
  not demand. Verified the hazard needs a hand-named custom entry (no
  official key contains `+`). Recommend routing to the phase-12
  hardening list or a maintainer ruling.
- **IN-03 (stats leg re-reads every record each 2s tick):** the
  reviewer's own disposition — correctness unaffected; watch at the
  GB10 smoke (D-15) where real trees exist. If cadence degrades, the
  fix shape (mtime-keyed record cache or moving the recompute to the
  60s worker) is already named in the finding. Acting pre-smoke would
  add unmeasured complexity against the D-13 proof.
- **IN-04 (`sweep_scale` inline on the event loop):** bounded (one
  manifest read+parse per finished root per 60s) and honest
  degradation risk is nil; folding it into the `_run_full_scan`
  worker is real but pure polish. Deferred with the finding's own
  suggested shape recorded.

## Verification

- Per-fix: the affected module suites only (RED-first where
  feasible), run in the isolated review-fix worktree via the repo
  `.venv` interpreter — reproducible from this tree at these SHAs.
- Full gates (run ONCE, in the main checkout after the fast-forward,
  per the speed directive): `make test` (pytest + JS lanes),
  `make lint` (ruff), `make typecheck` (ty) — counts and output in
  the fix report.
- Regression tests added: 24 new tests across
  `tests/tui/test_services_sweep_launcher.py` (13),
  `tests/tui/test_services_sweep_monitor.py` (5),
  `tests/tui/test_services_run_config.py` (2),
  `tests/tui/test_pilot_monitor.py` (5 + fake extensions),
  `tests/tui/test_pilot_run_config.py` (3 + fake extensions),
  plus the updated pinned-constants/inventory tripwires
  (`test_pinned_constants_and_default_output_root`,
  `EXPECTED_CFG_CONSTANTS`).

_Fixed: 2026-10-13 — gsd-code-fixer (Claude)_
