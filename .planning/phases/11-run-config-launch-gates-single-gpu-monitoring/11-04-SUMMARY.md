---
phase: 11-run-config-launch-gates-single-gpu-monitoring
plan: 04
subsystem: tui-services
tags: [sweep-monitor, discovery-scan, eta, tolerant-readers, log-tail, mon]

requires:
  - phase: 11-01
    provides: the run_sweep artifact-name constants (MANIFEST_NAME/FAILURES_NAME/RECORD_NAME/RESUME_MARKER/METRICS_NAME) + HEAD_KEEP_BASE_NAMES this scanner imports single-source (D-05)
  - phase: 08-04
    provides: settings.state_dir + atomic_write (manual-roots XDG persistence)
  - phase: 07-02
    provides: artifact_loader.load_json_artifact (the tolerant None-sentinel contract, D-19)
provides:
  - tui/services/sweep_monitor.py — the pure artifact-tree scanner: three-state root discovery (finished/running/artifacts_only), tolerant record/manifest/failures readers with last-known-good retention, cells_view per-(model, task) row derivation with resume-marker + curve-fraction states, resume_count, stats/elapsed/ETA (D-17), failures_view (records-while-running / file-when-finished), read_log_tail, format_hms/format_eta, XDG-persisted manual roots
  - the pinned constants STALE_GRACE_SECONDS=600 (O2, documented maintainer-tunable) and ETA_VARIANCE_RATIO=3.0 (O4) as the tuning surface
  - machine state strings for every monitor glyph (completed/failed/skipped/running/queued + verbatim unknown record statuses) — the 11-07 screen maps glyphs, never computes
affects: [11-07 monitor screen (stats line + cell table + discovered pane + [f]/[t] modals consume this service), 11-03 sweep launcher (live_roots injection + expected-total map)]

actuals:
  tokens: 21613   # chars/4 over the realized diff (86450 chars, 2 files)
  tasks: 3
  commits: 6      # measured: git rev-list --count de45827..HEAD
plan_head_before: de45827708966dcf9ee10f74bf78900f1803abb3
plan_head_after: 10c8def7741243cff84760a9fd889ea11469e19b

tech-stack:
  added: []   # stdlib + the existing artifact_loader/run_sweep/settings seams only
  patterns:
    - "pure-scanner service: no timers/threads/subprocesses/textual; every clock injectable (now= epoch) or explicitly mtime-pinned in tests"
    - "bounded walks: depth-guarded files-only watermark walk (depth 5) + per-directory entry caps on every scan path (T-11-04-04)"
    - "last-known-good per record FILE path (missing reads absent, damaged reads previous parse) — deleting a record never resurrects a stale view"

key-files:
  created:
    - tui/services/sweep_monitor.py
    - tests/tui/test_services_sweep_monitor.py
  modified: []

key-decisions:
  - "done = TERMINAL record statuses (completed|failed|skipped) everywhere (SweepSummary, stats, ETA remaining): progress and remaining share one set so a failed or resumed cell never inflates the remaining count; planned manifest cells never count"
  - "eta_estimate gained the optional model_totals keyword (the plan's stated formula needs the per-model plan): stats threads it from manifest cells; without it the pinned global-median x remaining fallback applies"
  - "pending is checked before none, per the plan's literal order: unknown total + zero completions renders pending, not none (both are honest degradations; the combined case is unspecified by D-17)"
  - "classification keeps the plan's predicate order (manifest beats live_roots): a re-run at a root holding a finished manifest classifies finished until the new run's own manifest lands — documented in full_scan's docstring as the accepted edge"
  - "base_model_name NOT imported despite key_links listing it: no call site consumes it (model identity stays the verbatim alias per the cell-derivation truth), and an unused import fails the ruff F401 gate"
  - "log-tail drops the byte-window's leading partial line (never renders a torn first line); empty-but-present file returns () while missing/unreadable returns None — the screen's unavailable state keys on None"

patterns-established:
  - "three-state discovery predicate: manifest => finished / live|watermark-advance|grace => running / else artifacts_only (unknown totals, no running glyph)"
  - "tolerant-reader layering: artifact_loader None-sentinel at parse level, dict/list shape checks at loader level, per-path LKG cache at service level, fallback rules at derivation level"

requirements-completed: [MON-01, MON-02, MON-03, MON-05]

coverage:
  - id: D1
    description: "Three-state discovery + manual roots + watermark/grace churn (D-03/O2)"
    requirement: MON-01
    verification:
      - kind: unit
        ref: "tests/tui/test_services_sweep_monitor.py::test_full_scan_finished_tree_reads_counts_from_manifest (+12 siblings in Lane 1)"
        status: pass
  - id: D2
    description: "Cell derivation with resume recognition, curve nesting, alias fidelity, tolerant readers (D-09/MON-05)"
    requirement: MON-01
    verification:
      - kind: unit
        ref: "tests/tui/test_services_sweep_monitor.py::test_cells_view_mixed_tree_exact_per_seed_states (+8 siblings in Lane 2, incl. the mid-write truncation last-known-good proof)"
        status: pass
  - id: D3
    description: "D-17 elapsed/ETA math exact-value proofs (median, per-model, ratio-3.0 range, pending/none, skipped exclusion)"
    requirement: MON-02
    verification:
      - kind: unit
        ref: "tests/tui/test_services_sweep_monitor.py::test_stats_done_total_current_elapsed_exact (+10 ETA siblings in Lane 3)"
        status: pass
  - id: D4
    description: "Live failure list: records while running, sweep_failures.json once finished (MON-03/O3)"
    requirement: MON-03
    verification:
      - kind: unit
        ref: "tests/tui/test_services_sweep_monitor.py::test_failures_view_records_while_running_file_when_finished"
        status: pass
  - id: D5
    description: "Bounded log tail (MON-04) — lines+bytes bounded, missing => None"
    requirement: MON-02
    verification:
      - kind: unit
        ref: "tests/tui/test_services_sweep_monitor.py::test_read_log_tail_bounded_lines_and_bytes (+ missing/unreadable sibling)"
        status: pass
  - id: D6
    description: "Plan-level gates"
    requirement: MON-01
    verification:
      - kind: command
        ref: "make test (1264 passed = 1222 baseline + 42 new) && make lint && make typecheck — all green"
        status: pass

---

# Phase 11 Plan 04: Sweep Monitor Service Summary

One-liner: the pure artifact-tree scanner — three-state sweep discovery (finished / running / artifacts_only), tolerant record reads with last-known-good, per-seed cell states with resume + curve fractions, and D-17's exact median/range ETA math — 42 tier-1 tests over synthetic tmp trees, all gates green.

## What Was Built

`tui/services/sweep_monitor.py` (zero textual, AST-lock covered automatically; artifact names imported from `run_sweep`, never re-typed):

- **Discovery (Task 1)** — `full_scan(roots, live_roots, prev_watermarks, now)`: manifest present ⇒ `finished` (total/done from manifest cells); live-root injection / watermark advance / newest mtime within `STALE_GRACE_SECONDS=600` ⇒ `running`; else `artifacts_only` (unknown totals). Nonexistent roots skipped silently; `watermarks` feed the next scan. `frontier_scan`: the light 2s pass bounded to seed dirs + direct children. `manual_roots`/`add_manual_root`/`remove_manual_root`: XDG-persisted (`monitor_roots.json`, tolerant load + atomic save), attach gated by `is_sweep_root` (manifest | failures | any record | seed-layout-with-artifacts).
- **Cells (Task 2)** — `cells_view(root, expected_seeds)`: rows per (model, task) from seed dirs ∪ manifest cells; per-seed first-match derivation (record status incl. verbatim unknowns → resume marker → activity → queued); curve `fraction_states` + fold; alias identity verbatim. `resume_count`: manifest-skipped once finished else skipped records (WR-12 provenance). `load_record` keeps a per-path last-known-good for damaged files (missing reads absent); corrupt manifests are treated absent.
- **Stats (Task 3)** — `stats(root, expected_total, fallback_start, now)`: done/total/current/elapsed + ETA; `eta_estimate`: completed-only durations (skipped excluded, malformed/skewed stamps dropped), pending < 1 completion, none on unknown total / zero remaining, per-model median × per-model remaining when the manifest plan threads through (global median for completion-less models), strict max/min > 3.0 ⇒ min–max range. `failures_view` (records live / file authoritative). `read_log_tail` (seek-from-end, lines+bytes bounded, partial leading line dropped, None on missing). `format_hms`/`format_eta`.

## Verification Evidence

### Three-state classification spot-table (tmp fixtures, injected clocks)

| Fixture | Signal | State | done/total |
|---|---|---|---|
| manifest with 3 completed + 1 failed + 1 skipped + 2 planned cells | manifest present | finished | 4/6 |
| stale tree + Popen-alive injection (`live_roots`) | live root | running | terminal-count/None |
| scan-1 watermark 7200s old → record touched to NOW, scan-2 now=NOW+7200 | watermark advance (newest is NOT within grace) | running | terminal-count/None |
| newest mtime exactly `now − 600` | grace boundary (inclusive) | running | terminal-count/None |
| no manifest, mtimes 7200s old (the seed_9527 shape) | nothing | artifacts_only | terminal-count/**None** |
| nonexistent root | — | skipped silently | — |

### Gates

- `uv run --group dev --group tui pytest tests/tui/test_services_sweep_monitor.py tests/tui/test_import_lock.py -q` — 43 passed.
- `make test` — **1264 passed** (1222 baseline + 42 new), node lane 18 passed.
- `make lint` — All checks passed (incl. the ambient SIM/F ruleset).
- `make typecheck` — All checks passed (ty).

## Deviations from Plan

### Task-boundary shifts (Rule 3 — blocking-dependency resolution)

The plan's Task 1 structurally consumes pieces its text assigns to Task 2 (its own behavior note says manual-root attach is "refused by ... Task 2's is_sweep_root"): `is_sweep_root`, the three tolerant readers, and the seed-state derivation core landed with **Task 1's GREEN** commit (full_scan needs `load_manifest` + record counting; `add_manual_root` needs `is_sweep_root`; `frontier_scan` needs the derivation); Task 2's suite then pins all of their behaviors (the truncation/LKG, corrupt-manifest, predicate edges). No behavior changed — only which commit first carries the code.

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrupt-manifest fixture tripped the grace rule**
- **Found during:** Task 2 GREEN
- **Issue:** the corrupt manifest was written AFTER `age_tree`, so its fresh mtime classified the root running under the injected past clock — testing the wrong thing.
- **Fix:** re-age the tree after each manifest write; the corruption→absent fallback is now actually under test.
- **Files modified:** tests/tui/test_services_sweep_monitor.py
- **Commit:** 4f5d41f

### Documented decisions (plan-left-open points, no behavior conflict)

- `done` = terminal statuses (completed|failed|skipped) shared by progress + ETA remaining (see key-decisions).
- `eta_estimate` gained optional `model_totals` (the plan's formula requires the per-model plan; `stats` threads it).
- `base_model_name` not imported (key_links listed it; no call site — an unused import fails ruff F401).
- pending-before-none order kept literally per the plan sentence (unknown total + 0 completions ⇒ pending).
- manifest-beats-live classification order kept literally (re-run at a finished root reads finished until its own manifest lands; documented in `full_scan`).

## Auth Gates

None — no auth-adjacent surface (pure filesystem scanner).

## Known Stubs

None — no NotImplementedError/TODO/placeholder remains (grep-verified); every public function is test-covered (42 tests).

## Threat Surface

No new surface beyond the plan's threat model: all six T-11-04 mitigations landed (tolerant readers + LKG = T-11-04-01; artifacts_only third state + 600s pin = T-11-04-02; unknown-total honesty = T-11-04-03; bounded/depth-guarded walks = T-11-04-04; parse-only readers = T-11-04-05; bounded log read = T-11-04-06). Zero packages installed (T-11-04-SC).

## What 11-07 Can Now Assume

The monitor screen owns ONLY cadence + rendering: call `full_scan` (60s) / `frontier_scan` (2s) / `cells_view` / `stats` / `failures_view` / `read_log_tail` from workers and map the machine state strings to glyphs — `SweepSummary.state` (3 values), `CellSeed.state` (completed/failed/skipped/running/queued or a verbatim record status), `EtaEstimate.mode` (pending/point/range/none with `total is None` ⇒ the unknown-total copy), `format_hms`/`format_eta` for the stats line, and `live_roots` + `expected_total`/`fallback_start` as the launcher-injection seams from 11-03.

## Self-Check: PASSED

All created files exist on disk; all 6 task commits are ancestors of HEAD (verified via `git merge-base --is-ancestor`).
