---
phase: 12-multi-gpu-orchestration-console-hardening
verified: 2026-10-16T07:51:41Z
status: passed
score: 5/5 must-haves verified
covered_files: [".planning/phases/12-multi-gpu-orchestration-console-hardening/12-01-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-01-SUMMARY.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-02-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-02-SUMMARY.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-03-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-03-SUMMARY.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-04-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-04-SUMMARY.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-05-PLAN.md", ".planning/phases/12-multi-gpu-orchestration-console-hardening/12-05-SUMMARY.md", "Makefile", "README.md", "dnallm-mark/css/progress.css", "dnallm-mark/css/styles.css", "dnallm-mark/data/progress/.gitkeep", "dnallm-mark/js/config.js", "dnallm-mark/js/data.js", "dnallm-mark/js/progress.js", "dnallm-mark/progress.html", "docs/multi-gpu.md", "pipeline/run_sweep_shard.py", "script/gen_progress.py", "tests/js/progress-page.test.js", "tests/test_sweep_shard.py", "tests/tui/__snapshots__/data_manager.svg", "tests/tui/__snapshots__/data_manager_presence.svg", "tests/tui/__snapshots__/env_check.svg", "tests/tui/__snapshots__/monitor_empty.svg", "tests/tui/__snapshots__/monitor_running.svg", "tests/tui/__snapshots__/run_config.svg", "tests/tui/__snapshots__/selection_datasets.svg", "tests/tui/__snapshots__/selection_models.svg", "tests/tui/__snapshots__/wizard.svg", "tests/tui/test_gen_progress.py", "tests/tui/test_pilot_monitor.py", "tests/tui/test_pilot_run_config.py", "tests/tui/test_snapshots.py", "tui/screens/run_config.py", "tui/strings.py"]
covered_digest: "v3:sha256:35277062daf673f6b4732c64638279a01517b51367fedf1489813b7ba7ffcb33"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 4/5
  gaps_closed:
    - "SC5 maintainer-review clause — D-03 visual review approved 2026-10-15 (on record in maintainer-authored commits d5cb44b + e70bf9f); all 9 goldens regenerated and committed, strict-xfail markers + _GOLDEN_REFRESH_REASON retired, 9 golden tests now regular green (11 passed this pass incl. determinism + sensitivity); WINDOWS #23/#24/#25 resolved"
  gaps_remaining: []
  regressions: [] # zero regressions: every behaviorally-proven claim re-proven green over the current tree (49/49 orchestrator, 11/11 goldens, 8/8 generator, delta A + B1/B2 named tests, JS lane 26/26)
advisory:
  - finding: "WINDOWS #21 (open, unrun-verify) — the 9-step N=2 multi-GPU smoke procedure remains maintainer-executed on other hardware"
    category: other
    reason: "By-design machine-role split (D-05: GB10 is single-GPU dev/test only; multi-GPU validation happens elsewhere), recorded as ledger obligation in WINDOWS row 21 and blocking /gsd-ship while open via windows_enforce. No Success Criterion is breached: every SC asserts a capability that IS proven here (CLI-invokable sharding via real-subprocess chains incl. the two-worker dry-run; per-worker monitoring, merge, and isolated re-run all test-pinned; docs/runbook on disk; goldens maintainer-approved). The prior passed report adjudicated this same split; carried per that reasoning. Closure = maintainer executes docs/multi-gpu.md §'The 9-step N=2 multi-GPU smoke procedure' and records outcomes against row 21."
    evidence_status: "none required (ledger obligation, not a defect; no failing test, no SC breach — all 5 SCs verified green this pass)"
  - finding: "WR-02 (carried) — pipeline/directories_config.py (post-phase quick-261014-f4w module, not phase scope) still absent from the make lint lane"
    category: architectural
    reason: "Re-checked this pass: file exists, grep of Makefile lint lists has 0 hits. Unchanged from the prior pass's adjudication — new-scope, no deterministic evidence (module is ty-covered via the whole pipeline/ tree and ruff-clean today); recorded open in 12-REVIEW-DISPOSITION.md; follow-through belongs to the f4w task lineage."
    evidence_status: "none provided (future-drift risk only; no failing test)"
---

# Phase 12: Multi-GPU Orchestration & Console Hardening Verification Report

**Phase Goal:** With single-GPU validated, throughput scales out — CLI-invocable static model sharding × CUDA_VISIBLE_DEVICES with per-worker monitoring, artifact merge, and isolated failure re-run, plus the documented DDP-vs-sharding applicability decision — and the console ships its release extras: a static read-only web progress mirror and maintainer-verified snapshot goldens pinning the canonical screens
**Verified:** 2026-10-16T07:51:41Z
**Status:** passed
**Re-verification:** Yes — REFRESH pass (final phase of the deferred 07→12 chain); prior pass was human_needed 4/5 with two by-design human items, of which the D-03 golden review has since landed on record

## Goal Achievement

### Observable Truths

Must-haves carried verbatim (ROADMAP Success Criteria × 5 PLAN frontmatters; no scope change). Refresh scope established first: against the prior verified timestamp (2026-10-14T17:33:12Z), `git log --since` shows ZERO commits for `pipeline/run_sweep_shard.py`, `script/gen_progress.py`, all six web-mirror files, `tests/test_sweep_shard.py`, `tests/tui/test_gen_progress.py`, and `tests/js/progress-page.test.js` — their prior three-level + data-flow verdicts carry forward verbatim, with behavioral re-proof run again anyway (belt-and-suspenders). Changed covered files this round: the 9 golden SVGs + `tests/tui/test_snapshots.py` (d5cb44b golden refresh + 4c11655 zh-pin wiring), `Makefile` (ea69e38 QUICK_PEX_DEMO lint var), `README.md` (ab61868 demo links + b89e87c docs-refresh), `docs/multi-gpu.md` (b89e87c docs-refresh), and the TUI surface files touched by sanctioned quicks (c4j/ehc/a4f/hhx: `tui/strings.py`, `tui/screens/run_config.py`, `tests/tui/test_pilot_monitor.py`, `tests/tui/test_pilot_run_config.py`) — all code-reviewed via the scoped 08-REVIEW (601aa51 + disposition d800613, all findings fixed) and behaviorally re-proven here by named tests over the CURRENT tree.

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | SC1: Multi-worker orchestration is invokable from the CLI (not TUI-only): N workers over disjoint static model shards with CUDA_VISIBLE_DEVICES isolation, marker-skip as the only concurrency guard | ✓ VERIFIED | `pipeline/run_sweep_shard.py` byte-stable since the prior pass (1252 lines; 0 commits since 2026-10-14T17:33:12Z) — prior L1-L4 verdict holds verbatim, and re-confirmed on disk this pass: sibling imports `registry_loader`/`run_sweep` at :181-182 with `WORKER_SCRIPT = run_sweep.PIPELINE_DIR / "run_sweep.py"` at :184, per-worker `CUDA_VISIBLE_DEVICES: str(gpu_i)` env in spawn kwargs (:196 area, :112 docstring contract), argparse surface incl. `--merge` (:373). Prohibition machinery re-grep'd clean at word boundaries: no nvidia-smi probing, no socket/flock/fcntl/port code (only docstring statements OF the prohibition at :119/:340). Behavioral re-proof over the POST-change tree: `pytest tests/test_sweep_shard.py -q` → **49 passed in 0.44s**, including `test_real_two_worker_dry_run_subprocess_chain` (:808), `test_n1_degenerate_real_subprocess_smoke` (:1614), `test_dry_run_disjointness_in_process` (:740), `test_worker_argv_and_spawn_kwargs_under_default_gpus` (:371) — real-subprocess chains re-proven against the CURRENT `run_sweep.py` |
| 2 | SC2: The operator sees per-worker monitoring views, artifacts merge across workers, and a failed worker's shard re-runs in isolation without touching healthy workers | ✓ VERIFIED | Merge/isolation code byte-stable (same module). The 49/49 run includes `test_merge_happy_path_copies_allowlist_and_rewrites` (:1136), `test_merged_root_is_consumer_equivalent` (:1364), `test_merge_leaves_worker_roots_immutable` (:1461), `test_d08_from_failures_rerun_is_isolated_to_w0` (:1522) — all green. Delta A re-proof over the CURRENT monitor (hardened by the sanctioned ehc/c4j/hhx/a4f quicks): `pytest tests/tui/test_pilot_monitor.py::test_delta_a_discovered_pane_renders_worker_roots_independently` → **1 passed** — N-root discovered-table rendering survives the post-phase TUI rework intact |
| 3 | SC3: The DDP vs model-sharding applicability decision is documented and landed — single-large-model acceleration vs multi-model throughput | ✓ VERIFIED | `docs/multi-gpu.md` (249 lines) section map re-confirmed: decision matrix §"The decision: model sharding vs DDP" at :17 (with the run_finetune WORLD_SIZE/LOCAL_RANK scaffolding citations and the explicit deferral-by-decision), CLI runbook :40 (dry-run-first launch, per-worker watch, killpg/Ctrl-C :95, D-08 one-line isolated re-run :111, D-09 merge :134, web mirror :162), machine roles §(D-05) :179, E2' trust boundary :189, 9-step N=2 procedure :200. README links live at :122 and :573 (both re-verified post ab61868/b89e87c) |
| 4 | SC4: A read-only web progress mirror generated from sweep artifacts lets the team follow progress in a browser — static files only, no backend | ✓ VERIFIED | All artifacts byte-stable since the prior pass (38/427/71-line page trio, 250-line generator, one-line site integrations) — prior verdicts carry. Wiring re-confirmed on disk: `NAV_LINKS` Progress entry `config.js:70`, `DataAPI.loadProgress` `data.js:106-110`, `@import url('./progress.css')` `styles.css:25`, `js/navbar.js:34` renders `CONFIG.NAV_LINKS` site-wide, `gen_progress.py:92` imports `tui.services.sweep_monitor` (same-source discipline), CDN grep in progress.html = **0 hits**. Behavioral re-proof: `pytest tests/tui/test_gen_progress.py -q` → **8 passed in 0.02s**; `node --test tests/js/*.test.js` → **26 pass / 0 fail** (matches the known-good gate) |
| 5 | SC5: Canonical screens are pinned by Textual snapshot SVG goldens reviewed and committed by the maintainer, failing CI CPU-side on visual regression | ✓ VERIFIED (upgraded from PRESENT_BEHAVIOR_UNVERIFIED) | The prior pass's human gate has LANDED, with direct git + ledger evidence: **d5cb44b** (2026-10-15, maintainer-authored by Tao Zhang) regenerated all 9 goldens via `make snapshot-update` — commit message: "Maintainer D-03 review approved 2026-10-15; strict-xfail markers and _GOLDEN_REFRESH_REASON retired with the goldens now byte-matching" — and **e70bf9f** resolved WINDOWS #23/#24/#25 (rows now `fixed`, resolved_at 2026-10-15T06:45). On disk this pass: **0 xfail markers** in test_snapshots.py, `GOLDENS` registry = exactly 9 entries (:841-864; env_check, selection_models, selection_datasets, data_manager, data_manager_presence, run_config, monitor_running, monitor_empty, wizard), 9 committed SVGs in `tests/tui/__snapshots__/`, `make snapshot-update` sole regeneration path (Makefile:132; module `--regenerate` documented at :59-63 — CI compares, never regenerates). Behavioral proof: `pytest tests/tui/test_snapshots.py -q` → **11 passed in 6.23s** — all 9 golden compares green as REGULAR tests (red-on-drift restored) plus determinism + sensitivity. The maintainer-review clause is closed by observed record (maintainer-authored commit + ledger resolution), not presence-only inference |

**Score:** 5/5 truths verified (0 present, behavior-unverified — the SC5 review clause, the prior pass's only unverified item, is closed by the on-record D-03 approval)

### Plan-Prohibition Checks (negative must-haves)

| Prohibition | Status | Evidence |
| --- | --- | --- |
| 12-01: no edit to run_sweep.py / run_finetune.py during the phase; pipeline/ gains exactly one new file | ✓ HELD (phase-scoped) | Prior-pass git evidence carries; post-phase run_sweep.py storage-flag additions are sanctioned quick-task work outside the phase contract — orchestrator compatibility re-proven by the 49/49 real-subprocess suite over the current run_sweep.py |
| 12-01: no lock/claim-file/port machinery; marker-skip only guard | ✓ HELD | run_sweep_shard.py bytes unchanged since prior verification + word-boundary re-grep clean this pass |
| 12-01: no nvidia-smi probing / GPU enumeration / N>1 assumption | ✓ HELD | Same — only docstring statements OF the prohibition (:119, :340) |
| 12-02: zero backend, zero CDN on new page, zero new deps | ✓ HELD | progress.html CDN grep = 0 hits this pass; page trio + generator byte-stable; no dependency changes touching them |
| 12-02: no fabricated values (honesty rules, web-side) | ✓ HELD | progress.js byte-stable; JS lane 26/26 green (the lane pins these rules) |
| 12-03: no fix at wrong layer; no new bindings; strings.py/styles.tcss untouched DURING the plan | ✓ HELD (phase-scoped) | The sanctioned `_PickerReturnModal` dismiss() override survived the post-phase ehc/hhx rework — B1/B2 named tests green over the current run_config.py (2 passed). Post-phase strings.py changes are the sanctioned bilingual-registry quicks (ehc/hhx), reviewed via 08-REVIEW |
| 12-03: no snapshot-plugin/syrupy/cairosvg install; string equality is the compare | ✓ HELD | pyproject.toml + uv.lock grep for syrupy/cairosvg/pytest-textual-snapshot = **0 hits** this pass; test_snapshots.py compares UTF-8 SVG strings |
| 12-04: no symlink/move merge; copy + SHA256 only | ✓ HELD | Merge path bytes unchanged since prior pass (prior `_copy_verified` verdict carries verbatim; 49/49 green) |
| 12-04: no orchestrator convenience flags beyond --merge/--include-checkpoints; no run_sweep edits during phase | ✓ HELD | Bytes unchanged; argparse surface frozen (7 add_argument sites) |
| 12-05: zero production-code changes in plan 05; never execute N=2 GPU procedure | ✓ HELD (phase-scoped) | Prior-pass commit evidence carries; no N=2 run exists on this host (WINDOWS #21 correctly still open) |

### Required Artifacts

Byte-stable artifacts (empty `git log --since` vs prior verified timestamp) carry their prior three-level VERIFIED verdicts; changed artifacts re-verified on disk this pass.

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------ | ------- |
| `pipeline/run_sweep_shard.py` | launch + merge orchestrator | ✓ VERIFIED | 1252 lines, byte-stable; 49/49 suite green this pass |
| `tests/test_sweep_shard.py` | tier-1 + merge + isolation suites | ✓ VERIFIED | 1662 lines, byte-stable; 49/49 green; all 8 named proof tests present (:371-:1614) |
| `script/gen_progress.py` | scanner-serializing generator | ✓ VERIFIED | 250 lines, byte-stable; 8/8 green |
| `tests/tui/test_gen_progress.py` | golden-JSON tests | ✓ VERIFIED | 382 lines, byte-stable; 8/8 green this pass |
| `dnallm-mark/progress.html` / `js/progress.js` / `css/progress.css` | frozen UI-SPEC page | ✓ VERIFIED | 38/427/71 lines, byte-stable; zero CDN re-confirmed |
| `js/config.js`, `js/data.js`, `css/styles.css` | one-line site edits | ✓ VERIFIED | Byte-stable; NAV_LINKS :70, loadProgress :106, @import :25 verified present |
| `tests/js/progress-page.test.js` | DOM-less JS lane | ✓ VERIFIED | 150 lines, byte-stable; JS lane 26 pass / 0 fail this pass |
| `tui/screens/run_config.py` | delta B only (phase scope) | ✓ VERIFIED | Fix survived the ehc/hhx rework — B1/B2 named tests 2 passed over the current file; post-phase additions reviewed via scoped 08-REVIEW (disposition fixed) |
| `tests/tui/test_pilot_run_config.py` | B1-B5 Pilot tests | ✓ VERIFIED | B1/B2 named tests green this pass (2 passed) |
| `tests/tui/test_snapshots.py` | harness + goldens + determinism/sensitivity | ✓ VERIFIED | GOLDENS = 9 entries (:841), **zero xfail markers**, `_GOLDEN_REFRESH_REASON` retired; 11 passed this pass (9 golden compares + determinism + sensitivity) |
| `tests/tui/__snapshots__/*.svg` | committed corpus | ✓ VERIFIED (9, maintainer-approved) | 9 SVGs on disk, regenerated in d5cb44b under the approved D-03 review; byte-matching (11/11 green proves compare integrity) |
| `Makefile` | lint guard + snapshot-update | ✓ VERIFIED | PHASE12_MODULES :174 intact (run_sweep_shard + gen_progress); snapshot-update :132 intact; the one post-phase delta is the QUICK_PEX_DEMO existence-guard lint var (:182, ea69e38 — additive) |
| `docs/multi-gpu.md` | D-04 decision doc | ✓ VERIFIED | Decision matrix :17; runbook + 9-step procedure + mirror steps verified present post docs-refresh (b89e87c) |
| `README.md` | links to the decision doc | ✓ VERIFIED | :122 + :573 (demo-docs commit ab61868 + docs-refresh b89e87c kept both live) |
| `tests/tui/test_pilot_monitor.py` | delta A proof | ✓ VERIFIED | Named delta A test green this pass over the post-quicks monitor |
| `.planning/WINDOWS.md` | entry 21 unrun-verify | ✓ VERIFIED | Row 21 open (unrun-verify) — correct state; #23/#24/#25 fixed 2026-10-15; counters open 19 / total 28 |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| run_sweep_shard | run_sweep + registry_loader | sibling imports | ✓ WIRED | :181-182 re-confirmed on disk; real-subprocess tests green over current run_sweep.py |
| worker env CUDA_VISIBLE_DEVICES | torch | verbatim inheritance | ✓ WIRED | Spawn-kwargs test green in the 49/49 run |
| gen_progress | tui.services.sweep_monitor | import + serialization | ✓ WIRED | :92 re-confirmed; 8/8 goldens green |
| gen_progress --output | data/progress/sweep.json → loadProgress → ProgressPage | fetch chain | ✓ WIRED | data.js:106 + JS lane 26/26 green |
| NAV_LINKS | site-wide navbar | js/navbar renders CONFIG.NAV_LINKS | ✓ WIRED | navbar.js:34; config.js:70 Progress entry present |
| _PickerReturnModal.dismiss | #cfg-picker refocus | call_after_refresh | ✓ WIRED | B1/B2 named tests green over the current run_config.py |
| make snapshot-update | regeneration entry | module --regenerate block | ✓ WIRED | Makefile:132 → test_snapshots.py --regenerate (d5cb44b proves the path end-to-end: it was used for the approved refresh) |
| --merge | worker_root() | one naming authority | ✓ WIRED | Byte-stable module; merge tests green |
| merged root | export_runs / sweep_monitor / gen_progress | consumer equivalence | ✓ WIRED | test_merged_root_is_consumer_equivalent green in the 49/49 run |
| docs step 7 | script/gen_progress.py | mirror command in runbook | ✓ WIRED | docs/multi-gpu.md :162-173 |
| WINDOWS #21 | docs procedure → 12-05-SUMMARY | one thread | ✓ WIRED | Row 21 open; 9-step procedure at docs :200 |

### Data-Flow Trace (Level 4)

Byte-stable artifacts carry their prior FLOWING verdicts (no commits since prior pass = no data-path change); the golden corpus's data path changed BY DESIGN and is re-traced.

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| progress.html page | sweep.json payload | gen_progress → sweep_monitor over real artifact roots | Yes — scanner-driven; JS lane pins the render rules | ✓ FLOWING |
| gen_progress.py | generated_at | injected/real clock | Yes — byte-stable; golden tests pin | ✓ FLOWING |
| run_sweep_shard verdict table | failed-cell count | worker sweep_failures.json | Yes — byte-stable; verdict-table test green | ✓ FLOWING |
| merged manifest | cells/failures unions | per-worker manifests + verified copies | Yes — consumer-equivalence test green this pass | ✓ FLOWING |
| test goldens | SVG bytes | export_screenshot over driven apps | Yes — regenerated from real renders via make snapshot-update (d5cb44b); 9/9 compare green | ✓ FLOWING |

### Behavioral Spot-Checks

Module lanes and named tests only — the full workspace suite is a pinned known-good gate on this exact tree (1808 passed incl. the 9 golden tests green, node 26/26, ruff+ty green) and was deliberately not re-run; each lane below re-proves the phase's own claims over the CURRENT tree.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Goldens module: 9 golden compares (now regular green) + determinism + sensitivity | `uv run --group dev --group tui pytest tests/tui/test_snapshots.py -q` | 11 passed in 6.23s | ✓ PASS |
| Orchestrator full module (LPT, validation, spawn, aggregation, merge, isolation, N=1 + two-worker real subprocess) | `uv run --group dev --group tui pytest tests/test_sweep_shard.py -q` | 49 passed in 0.44s | ✓ PASS |
| Generator golden contract | `uv run --group dev --group tui pytest tests/tui/test_gen_progress.py -q` | 8 passed in 0.02s | ✓ PASS |
| Delta A: N-root discovered table renders worker roots independently (post-quicks monitor) | `pytest tests/tui/test_pilot_monitor.py::test_delta_a_discovered_pane_renders_worker_roots_independently -q` | 1 passed | ✓ PASS |
| Delta B: modal dismiss refocuses picker + digits navigate immediately (post-quicks run_config) | `pytest ...::test_b1_preview_modal_esc_refocuses_picker ...::test_b2_digit_navigates_immediately_after_preview_dismiss -q` | 2 passed in 1.83s (combined with delta A) | ✓ PASS |
| Full JS lane incl. progress-page honesty rules | `node --test tests/js/*.test.js` | 26 pass / 0 fail | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes declared by this phase's plans or summaries; the verification contract is pytest + node lanes (executed above). SKIPPED (no probes declared).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| MGPU-01 | 12-01, 12-05 | CLI-invocable model sharding × CUDA_VISIBLE_DEVICES multi-worker static orchestration | ✓ SATISFIED | Truth 1 (SC1) evidence |
| MGPU-02 | 12-04, 12-05 | Per-worker monitoring views + artifact merge + isolated failure re-run | ✓ SATISFIED | Truth 2 (SC2) evidence |
| MGPU-03 | 12-04 | DDP vs model-sharding applicability decision landed | ✓ SATISFIED | Truth 3 (SC3) evidence |
| WEB-01 | 12-02 | Read-only web progress mirror, static artifacts, no backend | ✓ SATISFIED | Truth 4 (SC4) evidence |
| TEST-01 | 12-03 | Textual snapshot SVG goldens for canonical screens, maintainer-verified commit | ✓ SATISFIED | Truth 5 (SC5) evidence — maintainer review now on record (d5cb44b/e70bf9f); goldens green as regular CI-compared tests |

Orphaned-requirement check: REQUIREMENTS.md maps exactly MGPU-01/02/03, WEB-01, TEST-01 to Phase 12 (rows 125-130, all `[x]` Complete; row 128's I18N-01 belongs to Phase 8). All five claimed by plan frontmatter. No orphans.

### Decision Coverage

`check.decision-coverage-verify` reports `skipped: true, blocking: false, reason: "CONTEXT.md missing"` — the verb expects a file named `CONTEXT.md`, while this phase's context lives at `12-CONTEXT.md` (non-blocking skip). Manual coverage from the verified artifacts: D-01 (CLI-only orchestration; monitor unchanged), D-02 (web mirror inside the static site), D-03 (maintainer-approved goldens — closed this round), D-04 (decision doc landed), D-05 (machine-role split honored; no GPU probe in code), D-06 (marker-skip only), D-07 (single new entry), D-08 (one-line re-run, no convenience flag), D-09 (copy + SHA256 merge), D-10 (en nav link), D-11 (frozen clocks: generator `now=` + golden determinism), D-12 (the one dismiss() override). No decision found dishonored.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | — | — | Debt-marker scan (TBD/FIXME/XXX) clean across ALL covered files including every post-change one (strings.py, run_config.py, test_snapshots.py, Makefile, README, docs/multi-gpu.md, the goldens); TODO/HACK scan clean on the TUI surface files |

### Incremental-Change Adjudication (post-prior-pass quicks touching covered files)

The stale covered set named by the refresh context was examined individually; every staleness cause is resolved and none is a gap:

| Change | Commit(s) | Adjudication |
| ------ | --------- | ------------ |
| 9 goldens + test wiring (markers retired) | d5cb44b, 4c11655 | ✓ Resolved — exactly the 12-TEST-01 golden-refresh condition: maintainer D-03 review approved 2026-10-15 (on record), goldens committed, markers + `_GOLDEN_REFRESH_REASON` retired, 11/11 green. WR-01 (the prior pass's strict-xfail window advisory) is CLOSED by this |
| Makefile lint wiring | ea69e38 | ✓ Lint-only — additive `QUICK_PEX_DEMO` existence-guard var (:182); PHASE12_MODULES (:174) and snapshot-update (:132) contracts intact |
| README demo-doc links | ab61868 (+b89e87c docs refresh) | ✓ Docs-only — both multi-gpu links live (:122, :573) |
| TUI surface rework (c4j/ehc/a4f/hhx) | 6a59178..190d1c4 | ✓ Reviewed via the scoped 08-REVIEW (601aa51, disposition d800613 — all findings fixed) and behaviorally re-proven here: delta A 1 passed, B1/B2 2 passed, goldens 11/11 over the reworked screens (the goldens now PIN the reworked screens — that is their purpose) |
| docs/multi-gpu.md refresh | b89e87c | ✓ Docs-only — section map verified intact this pass |

### Coincidental-Reliance Check

None flagged. Byte-stability (0 commits vs the prior verified timestamp for the orchestrator and the entire web mirror) makes the carried verdicts non-incidental; the changed files were behaviorally re-proven against the current tree by named tests and module lanes; SC5's upgrade rests on directly observed maintainer-authored git + ledger records, not inference.

### Advisory (New Scope, Unevidenced)

Carried/re-checked findings reported, not blocking — see `advisory:` frontmatter.

| # | Finding | Category | Why Advisory |
| --- |---------|----------|--------------|
| 1 | WINDOWS #21 — N=2 smoke on other hardware (D-05 machine-role split) | other | Ledger obligation by design; no SC breached (all 5 verified); /gsd-ship keeps it visible while open |
| 2 | WR-02 (carried) — directories_config.py absent from make lint lane | architectural | New-scope, no deterministic evidence; not phase scope; recorded open in 12-REVIEW-DISPOSITION.md |

### Human Verification Required

None. The prior pass's two human items are resolved: (1) the D-03 golden review was executed and approved by the maintainer on 2026-10-15, recorded in maintainer-authored commits d5cb44b/e70bf9f and the WINDOWS ledger resolution — the SC5 "maintainer-verified" clause is closed by that record plus the 11/11 green compare suite; (2) the WINDOWS #21 N=2 smoke is adjudicated a maintainer ledger obligation on other hardware by the D-05 machine-role decision (the standing memory directive: Phase 12 MGPU built here, validated elsewhere), tracked open in the ledger and enforced by `/gsd-ship` — it is not a phase-goal gap because every Success Criterion asserts a capability that is verified here, and the prior passed report adjudicated this same split.

### Gaps Summary

No gaps. The refresh pass verified the current tree end-to-end: the orchestrator and the entire web mirror are byte-stable since the prior verified pass and re-proven green (49/49 incl. real-subprocess chains, merge/isolation/consumer-equivalence; 8/8 generator; 26/26 JS lane); the changed TUI surface survived the sanctioned post-phase quicks (delta A + B1/B2 named tests green; quicks code-reviewed via the scoped 08-REVIEW); and the phase's one open human gate — the D-03 maintainer review of the goldens — landed on record 2026-10-15 with the golden refresh committed, the strict-xfail window retired, and all 9 golden tests now regular green CI comparisons. All plan prohibitions held. Requirements MGPU-01/02/03, WEB-01, TEST-01 all satisfied with no orphans. Two advisories carried (WINDOWS #21 ledger obligation; WR-02 lint-lane follow-through) — neither blocks. Phase goal achieved; 5/5.

---

_Verified: 2026-10-16T07:51:41Z_
_Verifier: Claude (gsd-verifier)_
