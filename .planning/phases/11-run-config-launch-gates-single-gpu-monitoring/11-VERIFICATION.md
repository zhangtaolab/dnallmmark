---
phase: 11-run-config-launch-gates-single-gpu-monitoring
verified: 2026-10-14T16:21:56Z
status: gaps_found
score: 4/5 must-haves verified
covered_files:
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-01-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-01-SUMMARY.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-02-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-02-SUMMARY.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-03-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-03-SUMMARY.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-04-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-04-SUMMARY.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-05-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-05-SUMMARY.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-06-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-06-SUMMARY.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-07-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-07-SUMMARY.md
  - pipeline/run_sweep.py
  - tests/test_sweep.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/test_services_run_config.py
  - tests/tui/test_services_sweep_launcher.py
  - tests/tui/test_services_sweep_monitor.py
  - tests/tui/test_strings_phase11.py
  - tui/app.py
  - tui/screens/monitor.py
  - tui/screens/nav.py
  - tui/screens/run_config.py
  - tui/services/run_config.py
  - tui/services/sweep_launcher.py
  - tui/services/sweep_monitor.py
  - tui/strings.py
  - tui/styles.tcss
covered_digest: "v3:sha256:361f633d71f3ddbfd5522654a92ec8cd8bbcc42403f399552dc0961df0bfc684"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 4/5
  previous_verified: 2026-10-13T17:35:00Z
  stale_refresh: true
  gaps_closed:
    - "SC5 smoke execution half (the prior pass's single human item) — executed live 2026-10-13 under maintainer authorization (11-UAT.md passed; WINDOWS.md #20 closed)"
  gaps_remaining: []
  regressions: []
gaps:
  - truth: "SC4 — attach mode for externally (CLI) launched sweeps monitors the attached root (goal: 'monitor/recover the sweep from the same console'; MON-02)"
    status: failed
    reason: "CR-01 (review): MonitorScreen.attach() stores the RAW operator path (tui/screens/monitor.py:1131 `self._attached_root = Path(str(root))`) while the [a] validation layer resolves internally — a ~-spelled root VALIDATES (add_manual_root expands+resolves, persists, returns True), toasts success, then every non-frontier reader reads the literal nonexistent path: cells_view/stats/failures_view/cell_record all do plain Path(root) (sweep_monitor.py:761/980/815/1133) → empty table + misleading 未附加 copy while a sweep IS attached; frontier_scan (:555) resolves and disagrees; str(_attached_root) never matches the resolved discovered-table keys (◆ never renders); attached_running_counts() feeds ExitModal the phantom string. REPRODUCED this pass (real services, temp HOME): add_manual_root('~/sweeps/run1')=True, cells_view(raw)=0 rows, cells_view(resolved)=1 row, frontier_scan resolves. All Pilot attach tests use absolute paths over a fake service (test_pilot_monitor.py:879) — the gap is untested. Not delta-introduced (sites date to e6da784/af0e559 2026-10-13, present-but-unflagged at the prior pass) but every flagged file was git-modified since the prior verified timestamp and the reproduction is deterministic → blocking-class under #3304, in-contract."
    artifacts:
      - path: "tui/screens/monitor.py"
        issue: "attach() stores Path(str(root)) without expanduser().resolve() (:1124-1138); action_attach_path on_submit (:1519-1527) feeds the unexpanded PathInputModal value (selection.py strips whitespace only)"
    missing:
      - "attach(): store Path(str(root)).expanduser().resolve() (note_launch's pre-resolution becomes a no-op)"
      - "A Pilot case feeding a ~ -spelled path through the [a] modal over the REAL scanner pinning the fix"
  - truth: "WR-01 — launcher registry key / tee rootname / gate pre-check resolve spec.output_root against TUI-process CWD, contradicting compose_argv's REPO_ROOT-absolute threading (D-14 any-CWD discipline)"
    status: partial
    reason: "launch_spec passes RAW spec.output_root to _spawn (sweep_launcher.py:556-558); the registry key is str(Path(output_root).resolve()) — CWD-based (:448) — while compose_argv threads _abs_against_repo_root (run_config.py:1137). TUI started outside the repo with a relative root → the sweep writes {repo}/finetuned but registry/attach/kill/detach key on {cwd}/finetuned (phantom; auto-attaches an empty monitor via CR-01's mechanism). REPRODUCED this pass from a temp CWD: argv --output-root {repo}/finetuned vs outcome.root {tmp}/finetuned. Site dates to ea51363/8fe61a2 (2026-10-13); sweep_launcher.py modified since pass. Normal mode (make tui from repo root) unaffected."
    artifacts:
      - path: "tui/services/sweep_launcher.py"
        issue: "launch_spec :556-558 threads raw spec.output_root; registry key :448 CWD-based"
      - path: "tui/screens/run_config.py"
        issue: "the CR-02 live-root pre-check shares the CWD basis (:1905-1907)"
    missing:
      - "resolve the registry key through rc.resolve_dirs(spec).output_root_abs (the same seam the argv uses) in launch_spec + the screen pre-check"
  - truth: "WR-02 — [r] re-run seed fan-out falls back to a silent [42] when the cell table is empty"
    status: partial
    reason: "monitor.py:1226-1228: seeds derived from self._cell_rows `or [42]` — attach → [f] → [r] → confirm before the first full/frontier scan lands re-runs failed pairs at seed 42 ONLY, silently a different experiment than confirmed. The authoritative seeds are in hand: every FailureRow carries .seed. Site dates to e6da784 (2026-10-13)."
    artifacts:
      - path: "tui/screens/monitor.py"
        issue: "_run_rerun_launch seed derivation `or [42]` default (:1226-1228)"
    missing:
      - "derive seeds from failures_view rows (row.seed); refuse loudly (RerunFailed) when nothing derivable — never a default"
  - truth: "WR-03 — MON_RERUN_CONFIRM names entry-count n but the launch enumerates pairs × the sweep's full seed set (confirmed GPU spend understated ~3x)"
    status: partial
    reason: "FailuresModal.action_rerun_failures passes len(self._failures) (ENTRIES) into MON_RERUN_CONFIRM.format(n=count) (monitor.py:574-580, strings.py:995); launch_from_failures enumerates distinct (model,task) pairs × seeds (D-11). A 3-seed sweep with all failures at seed 42 confirms '重跑 10 个失败 cell' then launches up to 30 trainings. A destructive-action confirmation that materially understates the authorization."
    artifacts:
      - path: "tui/screens/monitor.py"
        issue: "confirm count = failure entries, not pairs × seeds (:574-580)"
    missing:
      - "compute the planned-cell estimate len({(model_base, task)}) × len(seeds) for the confirm copy (or name the seed fan-out in the copy)"
  - truth: "WR-04 — tee log filename is second-resolution timestamp + basename only; two same-basename roots launched in the same second truncate each other's logs"
    status: partial
    reason: "TEE_FILENAME_FORMAT sweep_{ts}_{rootname}.log (sweep_launcher.py:102-103, 465-474); the CR-02 guard blocks only same-root relaunch. Two different roots sharing the basename 'finetuned' (the common default) spawned within one second (slot-4 confirm racing a monitor [r]) interleave from different offsets — corrupts the tail monitor + the audit log for a multi-day run. Site dates to ea51363 (2026-10-13)."
    artifacts:
      - path: "tui/services/sweep_launcher.py"
        issue: "non-unique tee filename (ts second-resolution + basename)"
    missing:
      - "make the name unique per spawn (registry counter/pid, or open mode 'x' with a suffixed fallback, or fold parent+name into {rootname})"
  - truth: "WR-05 — ExitModal handles only roots[0]; [k] 终止后退出 exits with other live sweeps still running"
    status: partial
    reason: "action_quit picks roots[0] (sorted) and builds ExitModal around that single root (app.py:843-849); [k] kills exactly that process group (:217-218 kill_quit), [enter] detaches exactly that one, then the app exits. Multiple live sweeps at different roots are a supported state (CR-02 blocks only same-root). The operator's kill belief is factually wrong; message done/total come from the possibly-unrelated attached root. Site dates to e6da784 (2026-10-13)."
    artifacts:
      - path: "tui/app.py"
        issue: "single-root ExitModal (:843-849); kill_quit/detach_quit act on one root"
    missing:
      - "when len(roots) > 1: name every live root in the message and make [k] kill all of them (or refuse the plain triple naming each root)"
advisory:
  - finding: "IN-01 LNC_E2_WARNING hardcodes 59 × 50 × 8850 — the drift mechanism REALIZED in this delta (1f16b3d hand-edited 62→59/9300→8850 for the confidential-model removal); the gate predicate itself computes fresh (is_full_e2x, superset — stays correct)"
    category: architectural
    reason: "authorization copy can lie about what is being authorized when registries evolve; fix = format counts from GateSummary or add a drift tripwire test pinning the constant against official_keys()"
    evidence_status: "git-dated (1f16b3d 2026-10-14); no functional failure — gate verdict unaffected"
  - finding: "IN-02 stale NAV placeholder comment (strings.py:578-579 says slots 3/4/5 undelivered; all six slots live) · IN-03 expected_seeds parameter dead in production · IN-04 cell-detail modal never reads curve-cell records (frac_* run_records) · IN-05 cell-row key {model}__{task} collision-prone for keys containing __"
    category: other
    reason: "info-tier polish findings from 11-REVIEW.md, all confirmed present at current HEAD; none goal-breaking"
    evidence_status: "code-read confirmation only"
  - finding: "test_storage_overview_defaults_mirror_real_consumers fails ON THIS BOX ONLY while the live smoke runs: pipeline/logs exists (gitignored; created by the running sweep) violating the test's fresh-checkout assertion. Production behavior (exists=True) is correct — an environment-sensitive test assumption, not a code regression. Plausibly one of the 7 known full-suite baseline failures."
    category: other
    reason: "test should monkeypatch or tolerate a gitignored logs dir; no phase-11 truth affected"
    evidence_status: "reproduced (pytest run) + git check-ignore evidence"
---

# Phase 11: Run Config, Launch Gates & Single-GPU Monitoring — Stale-Refresh Re-Verification

**Phase Goal:** The operator's core loop is closed and safe — compose a complete run spec, preview it from the same pure planning functions execution uses, pass the env + confirmation gates, launch `run_sweep.py` as a detached subprocess, and monitor/recover the sweep from the same console — proven end-to-end by a maintainer-authorized bounded smoke on GB10, with E2' provably still maintainer-gated
**Verified:** 2026-10-14T16:21:56Z (HEAD `5989cd7`, branch `autorun`; working tree code-clean)
**Status:** gaps_found
**Re-verification:** Yes — STALE-REFRESH (prior pass 2026-10-13T17:35Z at `bc8e52c`; covered source changed since: phase 12, quick tasks f4w/c2l/mlc/ir9/dcl + gap rounds; this delta touches every phase-11 covered code file except nav/screens-misc — full re-verification against current HEAD)

## Goal Achievement

### Observable Truths (SC1-5, ROADMAP verbatim anchor)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | **SC1** run-config screen: full parameter set + separated dirs + same-source dry-run preview with enumerated cell counts | ✓ VERIFIED | D-05 wiring intact at HEAD: `tui/services/run_config.py:115` module-level `import run_sweep`, `:907` `run_sweep.enumerate_matrix(...)` (zero re-implemented enumeration); `compose_argv` threads REPO_ROOT-absolute dirs (`:1137` `_abs_against_repo_root(spec.output_root)`, subset/cache/model_root/dataset_root/log_dir same); nav slot 4 promoted (`tui/screens/nav.py:89`). Tests green at HEAD: `test_params_defaults_render`, `test_preview_line_renders_and_updates_on_mark`, `test_preview_modal_renders_argv_and_problems`, `test_importing_service_leaves_gpu_stack_absent` (all re-run this pass) |
| 2 | **SC2** terraform-style launch gate: env preflight blocks with reason, preview precedes explicit confirm, E2' typed phrase unbypassable | ✓ VERIFIED | Refusal chain intact and order-correct at HEAD (`sweep_launcher.py:503-558`: preview problems → official-keys fail-closed → E2' exact phrase, each BEFORE the spawner; re-run path gated identically via `_from_failures_refusal` recomputing the effective matrix through the real `run_sweep.load_failure_pairs` + `is_full_e2x`). Tests green this pass: `test_launch_from_failures_complete_manifest_three_seeds_demands_phrase`, `test_launch_spec_e2x_wrong_phrase_refuses_spawner_silent`, `test_phrase_matches_never_matches_an_empty_expected_phrase`, `test_validate_composition_refuses_filesystem_root_output_root`, Pilot `test_gate_e2x_phrase_flow` / `test_gate_env_block_renders_reasons_verbatim` / `test_gate_problems_blocked_launch_never_called`. The frozen phase-8 face was edited AFTER the prior pass by quick task 261014-dcl (env_gate +22/quick_check +11) — owner-tracked in phase 8's own ledger; the phase-11 consumption chain (`run_quick_check` → `gate_verdict`, `sweep_launcher.py:327`) is intact and launcher suite green |
| 3 | **SC3** execution always a `run_sweep.py` subprocess (LIST argv + PYTHONUNBUFFERED=1 + start_new_session); exit kill/detach/cancel; detached sweeps resume-safe to re-attach | ✓ VERIFIED | `_spawn` pins at HEAD: `list(argv)`, `start_new_session=True`, cwd=pipeline/, env PYTHONUNBUFFERED=1, stdout→tee/stderr→STDOUT; SIGTERM→killpg→SIGKILL escalation; `live_sweeps()` prunes exited Popens; CR-02 duplicate-root guard. Tests green this pass: `test_spawn_pins_list_argv_session_cwd_env_tee` + the 10 kill/detach/duplicate/prune service lanes. LIVE (read-only, tonight's smoke): parent `run_sweep.py --models 2 --tasks 2 --seeds 42 --num_train_epochs 1 --output-root pipeline/finetuned/smoke-2x2-261014 --log_dir pipeline/logs` (PID 2586649, detached, 1h46m+) spawned child `run_finetune.py` with `--output_dir /abs/.../smoke-2x2-261014 --log_dir /abs/.../pipeline/logs` as separate absolute argv elements — the compose→spawn chain proven on the real host. Resume-safety substrate: RESUME_MARKER skip contract (sweep tests) + live ⊘ round trip (2026-10-13 UAT). WR-05 (multi-sweep exit modal) and WR-01 (CWD-basis key) are logged gaps that do not break this truth in the supported launch mode |
| 4 | **SC4** monitor dashboard: cell states via 2s/60s tolerant scans, stats/ETA, attach for CLI sweeps, gated re-run, bounded tail + tee, ⊘ resume | ✗ FAILED | Cadence/states/stats/ETA/failures/tail/resume all VERIFIED at HEAD: `FRONTIER_INTERVAL_SECONDS=2.0`/`FULL_INTERVAL_SECONDS=60.0` exclusive workers; artifact constants imported from run_sweep; full monitor Pilot suite **34 passed** this pass (+1 vs prior — delta added coverage), rerun lanes 6 passed, scanner+launcher+run_config service lanes green. **The attach seam is broken for a validated input class — CR-01:** `attach()` stores the RAW operator path while `[a]` validation resolves internally; a `~/sweeps/x` root VALIDATES, persists, toasts success — then cells_view/failures_view read the literal nonexistent path → empty monitor + misleading 未附加 copy, `frontier_scan` (which resolves) disagrees, the ◆ marker never matches, ExitModal sees the phantom string. **Deterministically reproduced this pass** over the real services: `add_manual_root('~/sweeps/run1')=True`, `cells_view(raw)=0 rows`, `cells_view(resolved)=1 row`. Goal wording "monitor/recover the sweep from the same console" is breached exactly at MON-02's CLI-attach surface; untested because every Pilot attach test uses an absolute path over a fake service (`test_pilot_monitor.py:879`). WR-01 compounds it (phantom auto-attach when the TUI runs outside the repo). See gaps #1-2 |
| 5 | **SC5** bounded smoke runs launch→monitor→failure-re-run E2E on GB10 while E2' demonstrably blocks; every capability headless via CLI | ✓ VERIFIED | The prior pass's single open item CLOSED: 1×1×1 smoke executed live 2026-10-13 under maintainer authorization ("跑") — 11-UAT.md status **passed** with full evidence (launch → D-13 auto-nav → ⠋→✓ @1:21 → detach/reattach → ⊘ trainer_state skip → poisoned-cell failure leg → [f]→r confirm-gated re-run → true completion; E2' step-8: wrong dirname dead-locked, zero processes); WINDOWS.md #20 closed. ADDITIONAL live grounding (tonight, read-only): a maintainer-authorized 2×2 GPU smoke RUNNING through this exact chain — argv resolution (relative→absolute), cell layout `{root}/{model}/{task}/seed_42/`, log dir tee all confirmed on disk/ps. E2'-blocks re-proven CI-side this pass (3 named gate tests green). CLI parity: all 16 driver flags present in `run_sweep.py --help` (13 named + log_dir/model_root/dataset_root) |

**Score:** 4/5 truths verified (SC4 failed on the attach seam; the smoke's execution half that was open at the prior pass is closed by live evidence)

### Code-Review Findings Adjudication (#3304 evidence gate)

Sites dated with `git log -S`; "modified since pass" = the flagged file changed after the prior verified timestamp (2026-10-13T17:35Z / `bc8e52c`); every flagged phase-11 file was modified in the delta.

| Finding | Site dated | Modified since pass | Deterministic evidence | In-contract | Verdict |
|---------|-----------|--------------------|----------------------|-------------|---------|
| CR-01 attach stores raw path → empty monitor | e6da784 + af0e559 (2026-10-13 — present, unflagged at prior pass) | monitor.py: yes (exit_on_error/docstring) | YES — reproduced this pass (real services, temp HOME) | YES — SC4 attach / MON-02 / goal wording | 🛑 BLOCKER (gap #1) |
| WR-01 registry key CWD-basis vs argv REPO_ROOT | ea51363 + 8fe61a2 (2026-10-13) | sweep_launcher.py: yes | YES — reproduced this pass (temp CWD: argv {repo}/finetuned vs key {tmp}/finetuned) | Adjacent — D-14 any-CWD discipline; breaks monitor of TUI-launched sweep in the outside-repo mode only | ⚠️ WARNING (gap #2) |
| WR-02 `[r]` silent `or [42]` seed fallback | e6da784 (2026-10-13) | monitor.py: yes | Code-path read (`_cell_rows` empty → [42]); no red test exists | YES — MON-03 re-run correctness | ⚠️ WARNING (gap #3) |
| WR-03 confirm understates GPU spend ~3x | e6da784 (2026-10-13) | monitor.py: yes | Code-path read (entries n vs pairs × seeds) | YES — "safe" / confirmation-gate honesty (goal wording) | ⚠️ WARNING (gap #4) |
| WR-04 tee same-second collision | ea51363 (2026-10-13) | sweep_launcher.py: yes | Format-string read; race requires two same-basename roots in one second | Adjacent — MON-04 tee integrity | ⚠️ WARNING (gap #5) |
| WR-05 ExitModal single-sweep | e6da784 (2026-10-13) | app.py: yes | Code-path read (roots[0]; kill_quit one root) | YES — LNC-02 exit triple correctness under supported multi-sweep state | ⚠️ WARNING (gap #6) |
| IN-01 E2' copy hardcodes 59×50×8850 | 1f16b3d (2026-10-14 — DELTA-realized: the quick task hand-edited the counts, proving the drift) | strings.py: yes | Git-dated edit; gate predicate computes fresh (unaffected) | No — copy drift risk only | 📋 Advisory |
| IN-02..05 (stale comment / dead param / curve records / `__` join key) | phase-11-era sites | files modified | Code-read confirmation | No — polish | 📋 Advisory |

None of these is covered by a later milestone phase (Phase 12's SCs are sharding/web-mirror/goldens/merge — no monitor-attach/exit/tee hardening) → no deferral (Step 9b). All 11 remain `open` in 11-REVIEW-DISPOSITION.md (untriaged); this adjudication is the verification-side input to that record.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tui/services/run_config.py` | RunSpec/preview/dirs/phrase/argv service | ✓ VERIFIED | Present, substantive (import run_sweep :115; enumerate_matrix :907; compose_argv REPO_ROOT threading); 73+ service tests green (delta added ~20 more) |
| `tui/services/sweep_launcher.py` | Spawn/tee/kill/detach/gate service | ✓ VERIFIED (with WR-01/WR-04 gaps) | Spawn pins test green; refusal chain intact; registry-key basis gap logged |
| `tui/services/sweep_monitor.py` | Scanner: discovery/cells/stats/ETA/tail | ✓ VERIFIED (with CR-01 reader-path gap) | Artifact constants imported from run_sweep; tolerant readers; full suite green |
| `tui/screens/run_config.py` | Slot-4 screen | ✓ VERIFIED | Gate/preview/params Pilot lanes green this pass (12+ named tests) |
| `tui/screens/monitor.py` | Slot-5 screen | ✗ STUB-free but attach seam broken | 34 Pilot tests green; `[a]` attach path semantics gap (CR-01) |
| `tui/app.py` | Factories/seams/ExitModal/D-13 hook | ✓ VERIFIED (with WR-05 gap) | build_* factories + sweep_launched + action_quit present; single-root modal gap logged |
| `tui/screens/nav.py` | Slots 4+5 promoted | ✓ VERIFIED | `NavSlot(4, …run_config)`, `NavSlot(5, …monitor)` (`:89-90`); nav Pilot suite green |
| `tui/strings.py` | CFG_/LNC_/MON_ single home | ✓ VERIFIED | Tripwire suite green (in the 379-passed batch); IN-01 copy-drift advisory |
| `pipeline/run_sweep.py` | `--config-variant` aliasing (D-18) + parity flags | ✓ VERIFIED | 98+ sweep tests green in the batch run; 16 CLI flags present |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| run_config service | `pipeline/run_sweep` | module-level import | ✓ WIRED | `:115` import; `:907` enumerate_matrix live call (re-confirmed at HEAD) |
| sweep_launcher | env_gate + quick_check | direct import (`:327`) | ✓ WIRED | chain intact after 261014-dcl edits; launcher suite green |
| sweep_monitor | run_sweep artifact names | direct imports | ✓ WIRED | MANIFEST/FAILURES/RECORD/RESUME_MARKER single-sourced |
| monitor screen `[a]` modal | monitor service add_manual_root → attach | on_submit | ✗ NOT_WIRED (semantically) | The two layers disagree on path semantics — validation resolves, attach stores raw (CR-01) |
| monitor screen | launcher (tee/from-failures) | MonitorBackend injection | ✓ WIRED | rerun/tee lanes green (6 Pilot rerun tests) |
| app.py sweep_launched | monitor attach (D-13) | note_launch → resolved root_key | ✓ WIRED | …but the key is CWD-based upstream (WR-01) when TUI runs outside repo |
| app.py action_quit | ExitModal → launcher kill/detach | roots[0] | ⚠️ PARTIAL | single-root handling under multi-sweep state (WR-05) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| run_config preview | `cells` | `run_sweep.enumerate_matrix` over committed registries | Yes (purity test green) | ✓ FLOWING |
| monitor cell table | `cells_view` records | run_record.json/manifest/markers on disk | Yes for resolved roots; NO through a raw `~` attach path | ⚠️ STATIC (CR-01 path only) |
| live smoke chain | child argv | parent run_sweep argv | Yes — live ps: relative→absolute resolution, per-cell output dirs | ✓ FLOWING |

### Behavioral Spot-Checks (all run this pass at HEAD `5989cd7`)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| CR-01 reproduction (real services, `~` attach) | standalone script, temp HOME/XDG | validation True; cells_view(raw)=0; cells_view(resolved)=1; frontier_scan resolves | ✗ FAIL (gap confirmed) |
| WR-01 reproduction (non-repo CWD launch) | standalone script, fake spawner | argv root {repo}/finetuned; registry key {tmp}/finetuned | ✗ FAIL (gap confirmed) |
| E2' gate blocks full-matrix re-run, spawner-silent | `pytest …::test_launch_from_failures_complete_manifest_three_seeds_demands_phrase` | passed | ✓ PASS |
| E2' wrong/absent phrase → spawner never called | `pytest …::test_launch_spec_e2x_wrong_phrase_refuses_spawner_silent` | passed | ✓ PASS |
| "/" root + empty-phrase fail-closed (WR-07 fix) | `pytest …::test_phrase_matches_never_matches_an_empty_expected_phrase …::test_validate_composition_refuses_filesystem_root_output_root` | 3 passed | ✓ PASS |
| Import purity (D-05) | `pytest …::test_importing_service_leaves_gpu_stack_absent` | passed | ✓ PASS |
| SC1 Pilot lanes (params/preview/modal) | 3 named tests | passed | ✓ PASS |
| SC2 gate Pilot lanes | `test_gate_e2x_phrase_flow` + 3 named | passed | ✓ PASS |
| SC4 monitor Pilot suite (full file) | `pytest tests/tui/test_pilot_monitor.py -q` | **34 passed** | ✓ PASS |
| SC3 kill/detach/duplicate/prune lanes | `-k "kill or detach or duplicate or live_sweeps or prune"` | 10 passed | ✓ PASS |
| Covered service/sweep lanes | `pytest tests/test_sweep.py tests/tui/test_services_{run_config,sweep_launcher,sweep_monitor}.py tests/tui/test_strings_phase11.py tests/tui/test_import_lock.py` | 379 passed, **1 failed** | ⚠️ env-only failure (see Advisory #3 — `pipeline/logs` exists because the live smoke runs; test asserts fresh-checkout; gitignored dir, production behavior correct) |
| nav + env-check Pilot suites | full files | 45 passed | ✓ PASS |
| CLI parity flags | `run_sweep.py --help` | all 16 present | ✓ PASS |

**Full-suite baseline context (this box, per orchestrator): 7 failed / 1734 passed / 9 xfailed.** The one failure I hit in phase-covered files (`test_storage_overview_defaults_mirror_real_consumers`) is environmental (live-smoke artifacts violate a fresh-checkout test assumption), not a code regression. No phase-11 named lane fails.

### Probe Execution

N/A — no phase-declared or conventional probe scripts; this phase's evidence vehicles are the pytest Pilot/tier-1 harness + the maintainer-run smokes.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CFG-01 | 11-01/02/05/06 | Full parameter surface | ✓ SATISFIED | SC1 evidence; tests green at HEAD |
| CFG-02 | 11-02/06 | Dirs separation (D-14) | ✓ SATISFIED | compose_argv REPO_ROOT threading verified; WR-01 registry-key basis logged as gap (argv side correct) |
| CFG-03 | 11-02/06 | Same-source preview | ✓ SATISFIED | D-05 wiring + purity test at HEAD |
| LNC-01 | 11-05/06 | Gate copy + presentation | ✓ SATISFIED | strings tripwire + gate Pilot lanes green |
| LNC-02 | 11-01/03/06 | Subprocess discipline + exit triple | ✓ SATISFIED (WR-05 logged) | SC3 evidence incl. live smoke argv chain |
| LNC-03 | 11-02/03/06/07 | E2' unbypassable | ✓ SATISFIED | SC2 evidence re-run green at HEAD |
| MON-01 | 11-04/05/07 | Cell states, 2s/60s tolerant scans | ✓ SATISFIED | 34 Pilot + scanner suite green |
| MON-02 | 11-04/05/07 | Stats + CLI-sweep attach | ✗ NOT SATISFIED (attach seam) | CR-01 — reproduced; gap #1 |
| MON-03 | 11-04/05/07 | Live failures + confirm-gated re-run | ✓ SATISFIED (WR-02/WR-03 logged) | rerun lanes green; seed-fallback + confirm-count gaps recorded |
| MON-04 | 11-04/05/07 | Log tail + tee persistence | ✓ SATISFIED (WR-04 logged) | tail/tee tests green; collision gap recorded |
| MON-05 | 11-04/05/07 | ⊘ resume recognition | ✓ SATISFIED | tests + live UAT round trip |

REQUIREMENTS.md: all 11 phase requirements marked [x]; no orphaned requirements (Phase 11 grep → the CFG/LNC/MON set exactly).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| tui/screens/monitor.py | 1131, 1519-1527 | Raw-path attach (validated-but-unmonitored root) | 🛑 Blocker | CR-01 — gap #1 |
| tui/services/sweep_launcher.py | 448, 556-558 | CWD-basis registry key vs argv | ⚠️ Warning | WR-01 — gap #2 |
| tui/screens/monitor.py | 1226-1228, 574-580 | Silent seed default; understated confirm | ⚠️ Warning | WR-02/03 — gaps #3-4 |
| tui/services/sweep_launcher.py | 102-103, 465-474 | Non-unique tee filename | ⚠️ Warning | WR-04 — gap #5 |
| tui/app.py | 843-849, 217-218 | Single-root exit modal | ⚠️ Warning | WR-05 — gap #6 |
| tui/strings.py | 901, 578-579 | Hardcoded E2' counts; stale comment | ℹ️ Info | IN-01/02 — advisory |
| tui/services/sweep_monitor.py | 739-747 | Dead expected_seeds param | ℹ️ Info | IN-03 — advisory |
| tui/screens/monitor.py | 429-435, 1071 | Curve records unread; `__` join key | ℹ️ Info | IN-04/05 — advisory |

Zero TBD/FIXME/XXX markers across all phase code files. Zero NotImplementedError.

### Human Verification Required

None — the prior pass's single human item (GB10 smoke execution) was closed by the live 2026-10-13 UAT; tonight's running 2×2 smoke provides additional live grounding (read-only). No new behavior-unverified truths.

### Gaps Summary

The phase's compose→preview→gate→launch chain is intact and re-proven at HEAD, including on a live GPU sweep running through this exact chain right now. What the stale-refresh surfaced — via tonight's incremental review, adjudicated and reproduced here — is concentrated in the monitor/attach/exit seam the phase's own goal names: **one blocker** (CR-01: the `[a]` attach stores the raw operator path, so a `~`-spelled CLI sweep root validates, toasts success, and then monitors nothing — reproduced over the real services; untested because every Pilot attach test uses an absolute path) and **five warnings** (WR-01 CWD-basis registry key reproduced; WR-02 silent `[42]` re-run default; WR-03 confirm understating GPU spend ~3x; WR-04 same-second tee truncation; WR-05 multi-sweep exit modal). None is delta-introduced (all sites date to 2026-10-13, present-but-unflagged at the prior pass) — but every flagged file was git-modified since that pass and CR-01/WR-01 carry deterministic reproductions, so they are blocking/warning-class under #3304, not advisory. IN-01's copy-drift mechanism was realized in this very delta (the counts were hand-edited 62→59 for the confidential-model removal) — recorded as advisory since the gate predicate computes fresh. Structured in frontmatter `gaps` for `/gsd-plan-phase --gaps`; the fix surface is small (a one-line resolve in `attach()` + the WR hardening set + pinning Pilot cases).

---

_Verified: 2026-10-14T16:21:56Z_
_Verifier: Claude (gsd-verifier)_
