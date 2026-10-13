---
phase: 11-run-config-launch-gates-single-gpu-monitoring
reviewed: 2026-10-13T00:00:00Z
depth: deep
files_reviewed: 20
files_reviewed_list:
  - pipeline/run_sweep.py
  - tests/test_sweep.py
  - tui/services/run_config.py
  - tui/services/sweep_launcher.py
  - tui/services/sweep_monitor.py
  - tui/screens/run_config.py
  - tui/screens/monitor.py
  - tui/app.py
  - tui/screens/nav.py
  - tui/strings.py
  - tui/styles.tcss
  - tests/tui/test_services_run_config.py
  - tests/tui/test_services_sweep_launcher.py
  - tests/tui/test_services_sweep_monitor.py
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/test_strings_phase11.py
findings:
  critical: 2
  warning: 7
  info: 5
  total: 14
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-10-13
**Depth:** deep (per-file + cross-module: run_sweep ↔ run_finetune save-name chain, TUI service ↔ screen ↔ app wiring, launcher ↔ monitor ↔ scanner state flow)
**Files Reviewed:** 20 (diff `986c2a8..HEAD`, 33 code commits)
**Status:** issues_found

## Summary

The phase's core invariants mostly hold under adversarial reading. Verified sound: the 11-01 aliasing agrees exactly with the child's save-name chain (`run_finetune.py:1198-1213` — explicit `--save_model_name` wins; `HEAD_KEEP_BASE_NAMES` matches the child's frozen pair verbatim, so no variant cell can collide with a base cell except the *intended* head-keeps-base pair); variant×PEFT is refused collect-all at sweep start; the E2' verdict is superset-based, overlay-free (`json.load`, not `registry_loader`), and fail-closed on unreadable official registries; `launch_spec` truly recomputes preview/official-keys/phrase fresh (verified independent of screen state); the tui import chain stays torch-free (stdlib-only through `run_sweep`/`artifact_loader`/`registry_loader`); `read_log_tail` and `artifact_loader` decode with tolerance; XDG mutations are atomic.

Two CR-class defects remain: (1) the D-07 "E2' unbypassable" claim fails on the monitor's [f]→[r] from-failures path — the "never the full matrix by construction" premise is false for a complete failures manifest, which launches a 9300-cell sweep with no typed phrase; (2) nothing prevents launching a second sweep into a live root — the registry entry is silently overwritten (orphaned Popen, leaked tee fd) and two run_sweep processes then race the same cell dirs. The remaining warnings cluster around monitoring truthfulness on re-runs/populated roots, a gate wedge on worker exceptions, and 2s-cadence table rebuilds that reset the DataTable cursor.

## Critical Issues

### CR-01: E2' typed-phrase gate is bypassable via [f]→[r] with a complete failures manifest

**File:** `tui/services/sweep_launcher.py:504-527` and `:529-562`; `tui/screens/monitor.py:1095-1107`; `pipeline/run_sweep.py:1720-1724`
**Issue:** `launch_argv`/`launch_from_failures` never consult `is_full_e2x`/`phrase_matches`, justified by the docstring claim that "a from-failures enumeration is EXACTLY the failed (model, task) pairs of a prior sweep — it can never be the full matrix by construction" (`sweep_launcher.py:507-515`). That premise is false. run_sweep's own contract re-enumerates **all cells of every listed (model, task) pair across ALL requested seeds** (`run_sweep.py:133-136`, filter at `:1720-1724`). A `sweep_failures.json` that lists all 62×50 pairs is a *genuine, un-hand-edited artifact* — exactly what the driver writes when a full E2' sweep fails every cell (repo/env fault that passes preflight, disk-full hitting each cell, a bad `--subset_file` that dies per-cell). The monitor's re-run derives seeds from every seed ever seen at the root (`monitor.py:1099-1103` — 3 for a full sweep), so `[f]` → `[r]` on such a root composes `run_sweep --from-failures <path> --seeds 42,43,44 --output-root <root>` = the full 9300-cell E2' matrix, gated only by the generic `MON_RERUN_CONFIRM` confirm — never the typed phrase. D-07 states the three-seed authorization boundary must be unbypassable from inside the UI ("判定与短语校验使 UI 内部无法静默跳过"); this path reaches `_spawn` with an E2'-class matrix un-gated. A hand-edited manifest reaches the same place. (The raw `launch_argv` seam itself is intended per the phase brief and pinned by `tests/tui/test_services_sweep_launcher.py:766` — the defect is that `launch_from_failures`, a *composed* UI path, inherits the seam's no-gate property on a false premise.)
**Fix:** In `launch_from_failures` (or the monitor's re-run preflight, before the confirm): recompute the effective matrix — `run_sweep.load_failure_pairs(path, DEFAULT_REGISTRY_DIR)` × the requested seeds via `enumerate_matrix` — and apply the same `is_full_e2x`-class predicate (`pairs superset official && len(seeds) >= 3`); on a hit, demand `phrase_matches` exactly as `launch_spec` does (stage `phrase` refusal). Alternatively refuse re-runs whose pair set covers the official registry, naming the count.

### CR-02: No duplicate-root launch guard — second launch silently orphans the first sweep and both race the same cell dirs

**File:** `tui/services/sweep_launcher.py:441` (overwrite), `:385-443`; `tui/screens/run_config.py:1463-1475` (gate pipeline — no `live_sweeps` check anywhere in the screen)
**Issue:** `_spawn` does `self._live[root] = {...}` unconditionally. Launching a second sweep into an already-live root (trivially reachable: default output root is `./finetuned`; launch, auto-nav to the monitor, come back to slot 4, tweak params, press enter again — the persisted spec keeps the same root) (a) overwrites the registry entry: the first Popen handle is orphaned (unkillable via ExitModal/kill_sweep; its parent-side tee fd leaks for the process lifetime), and (b) leaves **two run_sweep processes enumerating the identical cell list into the identical output root**: both pass the missing-`trainer_state.json` check for the same cells and spawn two run_finetune children writing the same `seed_N` dir concurrently — colliding checkpoint saves, double-written `final_metrics.json`/`trainer_state.json`/`run_record.json`, interleaved tensorboard event files. On a single GPU (D-15 boundary) both also contend for VRAM. Corrupted run artifacts with "completed" records — a data-integrity risk for numbers destined for the public leaderboard.
**Fix:** `_spawn` refuses when `root in self._live` and the entry's `poll() is None` (return a failed `LaunchOutcome` with a diagnostic); surface it in the gate pipeline as a problems-stage refusal naming the live root (the operator must kill/detach or pick a different output root first).

## Warnings

### WR-01: Monitor [f] re-run drops the original sweep's PEFT/config-variant lane — re-trains BASE cells instead

**File:** `tui/screens/monitor.py:1095-1107`; `tui/services/sweep_launcher.py:529-562`
**Issue:** `_run_rerun_launch` calls `launch_from_failures(failures_path, seeds, root)` with `peft`/`config_variant` defaulting to `"none"`. A `--peft lora` (or `--config-variant probe`) sweep's failures manifest lists alias identities with `base_model` set; run_sweep re-enumerates the **base** cells for those pairs. Concrete failure: the failures modal shows alias rows (`x+lora × task × seed_42`), the operator confirms "re-run N failures", and what actually launches is a *base* (non-adapter, non-variant) sweep of those pairs — base cells carry no trainer_state markers, so they are fully retrained as a different experiment than the one confirmed, while the failed alias cells are never re-attempted. Different GPU spend than confirmed, and a wrong-lane artifact set lands in the same root.
**Fix:** Recover the lane from the failed records themselves (each `run_record.json` carries `peft`/`config_variant`; read one via the tolerant reader) and thread it into `launch_from_failures`; at minimum, render the effective lane (base vs alias) in `MON_RERUN_CONFIRM` so the mismatch is visible.

### WR-02: Stats/elapsed/ETA are corrupted for any run at a populated root (the re-run flow) — done>total, days-old elapsed, fabricated ETA

**File:** `tui/services/sweep_monitor.py:911-941` (`stats`: `done` counts ALL records on disk; `expected_total` takes precedence over the manifest), `:889-908` (`_elapsed_seconds`: earliest `started_at` across all history), `:944-1016` (`eta_estimate`: `remaining = total - done` with cumulative `done`); `tui/screens/monitor.py:1012-1021` (`note_launch(root, 0)` never clears a stale `_expected_totals[root]`)
**Issue:** Records accumulate at a root across runs (WR-12 discipline keeps old records). Scenario: root holds a finished full sweep (≈3000 completed records); a from-failures re-run (15 cells) starts at the same root — the exact [f]→[r] flow. The stats line then shows `done 3005/9300` (stale injected `expected_total` wins over the fresh manifest), elapsed = now − the *original* sweep's first record (days), and the ETA = (9300−3005) × median of the old sweep's durations — a fabricated multi-day ETA for a 15-cell re-run. After the re-run's manifest lands (total=15), `expected_total=9300` still takes precedence, so the wrong total persists for the whole TUI session. This contradicts the screen's own "honesty over motion" contract and D-17.
**Fix:** Prefer a *fresh* manifest's total over the stale injected one (clear or let the manifest override `_expected_totals` once `load_manifest` is non-None for the run's lifecycle), and scope `done`/`elapsed` to the current run (manifest cell identities, or records whose `started_at` >= this run's fallback_start) instead of every record under the root.

### WR-03: Launch-gate pipeline wedges permanently on a worker exception (`_gate_active` never released)

**File:** `tui/screens/run_config.py:1463-1475` (sets `_gate_active = True`), `:1477-1567` (all four gate workers have no try/except — contrast the tolerant monitor workers at `tui/screens/monitor.py:871-885`)
**Issue:** `action_open_gate` sets `_gate_active = True` and releases it only in message handlers. If any gate worker raises, no message is posted and the flag stays True — every subsequent `[enter]` returns at the re-entrancy guard; the gate is dead for that screen instance (navigating away and back silently rebuilds). Concrete triggers verified in the import chain: `registry_loader` raises `OSError` when an official registry file is missing/unreadable (`pipeline/registry_loader.py` fail-loud contract) and `SystemExit` on a malformed custom overlay — both reachable from `preview()` inside `_run_gate_enumeration`/`_run_confirm_data`/`_run_launch`; `probe_ineligible()` raises `ValueError` if the `PROBE_INELIGIBLE` literal drifts out of regex range. Worst instance: `_run_launch` dying *after* the operator confirmed = silent no-op launch with no error surface.
**Fix:** Wrap each gate worker body in try/except (the monitor's `except Exception: return` pattern, or better: post a failure message) and release `_gate_active` + surface an error toast on failure.

### WR-04: Live-sweep registry never prunes exited processes — dead TUI-launched sweeps render "● 运行中" forever

**File:** `tui/services/sweep_launcher.py:634-642` (`live_sweeps` returns all keys, never polls), `tui/screens/monitor.py:356-359` (`_live_roots` feeds every scan); `tui/services/sweep_monitor.py:508-516` (live-root membership wins over every churn/mtime signal)
**Issue:** Nothing ever calls `poll()` on registered Popens except kill. A TUI-launched run_sweep that dies without writing a manifest (kernel OOM-kill, external SIGKILL, CUDA crash taking down the driver) leaves its root in `live_roots` for the rest of the TUI session: `full_scan` classifies it `running` unconditionally (live wins), so the discovered pane shows a false running state indefinitely and the ExitModal keeps offering kill/detach for a corpse. Monitoring dishonesty with no self-healing path short of an app restart.
**Fix:** In `live_sweeps()` (or `MonitorBackend._live_roots`), filter to entries whose `handle.poll() is None` — optionally pruning dead entries and closing their tee handles at that point.

### WR-05: Monitor tables clear+rebuild every 2s tick — DataTable cursor/scroll reset; enter can act on the wrong row

**File:** `tui/screens/monitor.py:963-998` (frontier handler re-renders all panes each tick), `:1129-1145` + `:1180-1219` (`_rebuild_discovered_columns`/`_render_cells` do `table.clear(columns=True)` + re-add)
**Issue:** Textual 8.2.8's `DataTable.clear()` resets `cursor_coordinate` to (0,0) and zeroes scroll (verified: `.venv/lib/python3.13/site-packages/textual/widgets/_data_table.py:1600-1608`). While a sweep is attached, every 2s frontier tick rebuilds both tables, so keyboard navigation snaps back to row 0/scroll top continuously; worse, an `[enter]` pressed after a tick lands mid-reset acts on **row 0** — attaching the wrong sweep root from the discovered list, or opening the wrong cell detail from the (up to 3100-row) cells table. The run-config screen already solved this class: `PickerList.set_rows` preserves the highlight (`tui/screens/run_config.py:477-492`); the monitor tables do not.
**Fix:** Preserve the cursor row key (and scroll offset) across the rebuild the way `set_rows` does, or skip the rebuild when the focused table's data is unchanged / while the table has focus.

### WR-06: Default scan root misses CLI-launched sweeps started per run_sweep's own documented usage

**File:** `tui/services/sweep_monitor.py:63-70` (`DEFAULT_OUTPUT_ROOTS = (REPO_ROOT / "pipeline" / "finetuned",)` with the comment "run_sweep's default ./finetuned resolves to pipeline/finetuned from the repo root")
**Issue:** The comment's resolution claim is false: `Path("./finetuned").resolve()` in a CLI process resolves against *that process's CWD*. run_sweep's module docstring instructs running from the repo root (`python pipeline/run_sweep.py --dry-run ... --output-root ./finetuned`), which writes to `{repo}/finetuned`, not `{repo}/pipeline/finetuned`. Only TUI launches are covered (the launcher pins subprocess cwd to `pipeline/`). Result: D-03's "自动扫描默认输出根（含 CLI 启动）" does not hold for the documented CLI invocation — the sweep is invisible until manually attached via `[a]`.
**Fix:** Scan both `{repo}/finetuned` and `{repo}/pipeline/finetuned` (dedup resolved paths), or correct the comment and document `[a]` as the only path for repo-root CLI runs.

### WR-07: E2' typed gate fails open on an empty expected phrase

**File:** `tui/services/run_config.py:915-942` (`expected_phrase` = basename of the resolved root; `phrase_matches` = exact equality, no emptiness guard)
**Issue:** `Path("/").resolve().name` (also `"//"`) is `""`. An operator who sets the output root to `/` (or a path resolving to the filesystem root) makes `expected_phrase` the empty string; in `E2PhraseModal`, typing one character and deleting it fires `Input.Changed` with `""`, `matches("")` → True (indicator flips to match), and enter launches the full matrix with an empty "phrase". Convoluted preconditions, but this is an authorization boundary that must fail closed, and it fails open. (The same root would also make the sweep write to `/{model}/...` — all the more reason to refuse it early.)
**Fix:** Treat an empty expected phrase as a validation problem (add to `validate_composition`/gate problems: refuse an output root whose resolved form is the filesystem root / has an empty basename); `phrase_matches` should never compare against `""`.

## Info

### IN-01: `DirPlan.cache_dir_abs` docstring contradicts `compose_argv`

**File:** `tui/services/run_config.py:607-608` vs `:1007-1008`
**Issue:** The `DirPlan` docstring says `cache_dir_abs` is "never threaded", but `compose_argv` threads `--cache_dir` whenever set (copy-paste from the `dataset_root` line, which genuinely is D-19 not-threaded). Doc-only, but it is the kind of stale contract comment this repo treats as load-bearing.
**Fix:** Correct the docstring ("threaded by `compose_argv` when set; `DirPlan` exposes the resolved form").

### IN-02: Alias namespace collision with custom registry keys is unvalidated

**File:** `pipeline/run_sweep.py:521-528` (`cell_model` alias derivation)
**Issue:** A custom-overlay model literally named `x+probe` (or `+head/+curve/+lora/+ia3`) collides with the derived alias of base model `x`: identical cell dir → shared trainer_state → silent cross-skipping between two semantically different cells, the exact retrain/skip-forever class `_validate_dataset_name_alignment` guards against for dataset rows. Verified no official key contains `+` (62 models, 50 datasets checked), so this needs a hand-named custom entry; the `+lora` variant of the hazard predates this phase (06-02) and the variant lane widens it to three more suffixes.
**Fix:** A cheap sweep-start validation: refuse when any derived alias equals another registry key (or when any registry key contains a `+<lane-suffix>` tail), collect-all with the existing discipline.

### IN-03: The "light 2s frontier" stats leg re-reads every record under the root each tick

**File:** `tui/services/sweep_monitor.py:911-941` (`stats` → `_collect_records` walks all seed/frac dirs); `tui/screens/monitor.py:906-915` (`_run_frontier` calls `_stats_of` every 2s)
**Issue:** `frontier_scan` is bounded to seed-dir direct children, but the stats call beside it is O(total records) file I/O per tick — at full-sweep scale (~9300 records) that is thousands of opens+parses every 2 seconds for the attached root. Correctness is unaffected (the exclusive worker just degrades cadence; the D-13 responsiveness proof used fakes), but it is worth watching at the GB10 smoke (D-15) where real trees exist.
**Fix:** None required for correctness; if the smoke shows cadence degradation, cache parsed records by (path, mtime) or move the stats recompute to the 60s worker between frontier ticks.

### IN-04: `sweep_scale` runs inline on the event loop inside the full-scan message handler

**File:** `tui/screens/monitor.py:927-930`
**Issue:** `on_monitor_screen_full_scanned` calls `self._service.sweep_scale(summary.root)` synchronously for every finished root — a manifest read+parse on the event loop, against the module's own "a tick NEVER scans inline" discipline. Bounded (one manifest per finished root per 60s), hence Info.
**Fix:** Fold the scale read into the `_run_full_scan` worker (it already walks the same roots) and carry it in the `FullScanned` message.

### IN-05: `[t]` tee tail is lost after detach/kill — misleading "CLI-launched, no tee" rendering for TUI-launched sweeps

**File:** `tui/services/sweep_launcher.py:644-657` (`tee_path_for` is registry-only; detach/kill drop the entry); `tui/screens/monitor.py:1330-1339`
**Issue:** After `[enter]`-detach (the exit default) the tee *file* still exists under `state/logs/`, but `tee_path_for` returns None and `[t]` renders `MON_LOG_UNAVAILABLE` ("该 sweep 由 CLI 启动, 无 tee 落盘") — false copy for a sweep this TUI launched. Minor honesty gap in the same family the screen otherwise polices.
**Fix:** Persist the tee path per root outside the live registry (e.g. record it in the monitor's launch-injection state alongside `_expected_totals`), and fall back to it in `action_show_log_tail`.

---

## Verified-intended (checked, not defects — do not re-flag)

- Head-variant frozen pair keeps base names in **both** directions and matches `run_finetune.py:1207-1209` verbatim (read-source parity test pins drift); head-on-frozen-pair sharing the base cell dir/marker is the documented semantics ("their with-head config IS their base config").
- Variant×PEFT refusal (driver collect-all + service `variant_peft` problem + child probe×peft backstop); absent-variant byte parity (enumeration/argv/manifest keys).
- `launch_spec` refusal order and the fresh-recompute claim hold: preview problems → official-keys diagnostic (fail-closed) → phrase; the screen's cached `_last_preview` is never consulted on the launch path.
- `probe_ineligible` read-source extraction extracts exactly the frozen 9 names today (comment-embedded quoted tokens all coincide with list members); pinned by the parity test.
- Import purity: `tui.services.run_config` → `run_sweep`/`registry_loader`, `sweep_monitor` → `artifact_loader`, all stdlib-only; no torch/dnallm/transformers in the chain.
- `read_log_tail` (errors="replace", bounded window, partial-line drop) and `artifact_loader` (UnicodeDecodeError tolerated) cover the phase-9/10 decode-error class; services are CJK-free; `save_state`/manual-roots writes go through `settings.atomic_write`.
- ExitModal default detach; STALE_GRACE_SECONDS=600 as a documented tunable; `NAV_PLACEHOLDER_*` zero-consumer retention; the SIM115 noqa on the long-lived tee handle; D-19 no-dataset-root-flag (known deferred copy item).

---

_Reviewed: 2026-10-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_

## Re-review iteration 2 (HEAD 40cb0bd)

**Fix range:** `7979541..40cb0bd` (12 commits; disposition `11-REVIEW-DISPOSITION.md`). Every original failure scenario was re-run against HEAD — service-level live probes against the real registries (total-failure manifest built from the actual 62×50 official keys), plus the tier-1/tier-2 suites. Gates: `pytest tests/tui tests/test_sweep.py` → **1032 passed** (212.78s); `ruff check tui tests` → all checks passed; `ty check tui` → all checks passed.

### Per-finding verdicts

| ID | Verdict | Evidence at HEAD |
|----|---------|------------------|
| CR-01 | **CONFIRMED-FIXED** | Live probe over the real official registries: a complete 62×50 failures manifest × seeds {42,43,44} → `GateRefusal stage=phrase`, spawner call count 0; wrong phrase → refused; correct phrase → `spawned=True`; a genuinely partial manifest (3 models) × 3 seeds → spawns with NO phrase demanded (no over-gating). `_from_failures_refusal` (sweep_launcher.py:587-654) reuses the REAL `is_full_e2x` over a synthetic spec of `load_failure_pairs` base pairs — zero copied matrix logic; unevaluatable manifests refuse at stage `problems`. Monitor phrase flow: the re-prompt pushes the same `E2PhraseModal` with `matches` bound to the re-run's OWN root (no wrong-root match: `expected_phrase` resolves the identical root value the spawn uses; the degenerate "/" case fails closed), and the confirm closure re-enters `_run_rerun_launch` with the phrase — run-id-guarded, modal blocks concurrent re-entry. Pinned by `test_launch_from_failures_complete_manifest_three_seeds_demands_phrase` / `..._partial_manifest_never_phrase_gated` / `test_rerun_e2x_phrase_refusal_reprompts_then_launches`. Raw `launch_argv` seam stays ungated by design (its own pinned test) — safety no longer rests on the retired false premise. |
| CR-02 | **CONFIRMED-FIXED** | Live probe: first launch spawns, second launch into the same live root → `spawned=False` naming the live root, first entry survives (Popen still owned/killable, tee fd retained). Dead entries are pruned and the root reclaimed (probe P7). The gate pipeline additionally refuses at the problems stage (`live_root`) before env preflight/confirm. Residual theoretical double-`_spawn` window (live-check → Popen → insert, ~ms) is unreachable through the UI (both paths modal-serialized; the service guard is the backstop) — not a finding. |
| WR-01 | **CONFIRMED-FIXED** | Live probe: manifest cells' `config_variant` sweep flag → `('none','probe')` (catches `head` — frozen pair keeps base names but the merged flag names the lane); failures alias/base pair → `('lora','none')`. Missing/garbled artifacts derive honest `('none','none')`, and the important residual is CLOSED: a sweep killed before its end-of-sweep artifacts exist now has NO failures file, so the CR-01 problems-stage refusal refuses the whole re-run (naming the manifest) — honest refusal instead of the old wrong-lane base re-train. Only a hand-authored failures file without a manifest can still yield none/none — negligible and documented. |
| WR-02 | **CONFIRMED-FIXED** | Live probe at a populated root with a fresh run noted: scoped `stats` → done 1 (this run only), elapsed 1s (was days), ETA none (no fabrication); a manifest whose mtime predates the run start supplies neither total nor per-model ETA plan (probe: total None). `note_launch(root, 0)` clears the stale expected total. Unscoped (CLI/finished) path byte-identical. Residuals accepted and documented by the fixer: mid-run `resume_count` reads the stale manifest's skip count (pre-existing plan-pinned class), and the pre-existing re-run toast may quote the prior sweep's cell count before the clear (cosmetic, unchanged code). |
| WR-03 | **CONFIRMED-FIXED** | All four gate workers + the mount `_load` worker post `GateWorkerError` on exception; the handler validates the run id against BOTH id spaces, releases `_gate_active`, and toasts — confirm-then-crash now surfaces (`LNC_LAUNCH_FAILED_TOAST`). `_run_preview` degrades tolerantly (no per-keystroke toast flood; the fault resurfaces at the next gate attempt). Monitor re-run workers post `RerunFailed` → same toast (Pilot-tested). Loop serialization makes the release ordering race-free. |
| WR-04 | **CONFIRMED-FIXED** | Live probe: a dead entry is pruned at `live_sweeps()` read time (zombie reaped via `poll()`, parent tee fd closed — also fixing the finished-sweep fd retention), the ExitModal predicate and the monitor's live-root injection inherit the honest view. Mutation-during-iteration avoided (`sorted()` snapshot). `kill_sweep`/`detach` pop-first paths unaffected. |
| WR-05 | **CONFIRMED-FIXED** | `_set_table_rows` replaces clear+rebuild: columns rebuild only on a key-set change; known rows `update_cell` in place; the cursor re-pins by ROW KEY with `scroll=False`. Pilot test `test_table_updates_preserve_cursor_across_ticks` pins key-identity survival on BOTH tables across a frontier tick and a full-scan rebuild (asserts the row key, not the coordinate). See IN-06 for the one cosmetic residual this introduces. |
| WR-06 | **CONFIRMED-FIXED** | `DEFAULT_OUTPUT_ROOTS = (pipeline/finetuned, finetuned)` — probed; both resolution homes covered, nonexistent roots skip silently; the pinned-constants tripwire updated. |
| WR-07 | **CONFIRMED-FIXED** | Live probe: `validate_composition` on `output_root="/"` → `('output_root_invalid', '/')` (problems-stage refusal, rendered via `CFG_OUTPUT_ROOT_PROBLEM`, registered in the bidirectional strings inventory); `phrase_matches('',  '/')` → `False` — fails closed even before the problem fires. |
| IN-01 | **CONFIRMED-FIXED** | `DirPlan.cache_dir_abs` docstring corrected (threaded by `compose_argv`). |
| IN-05 | **CONFIRMED-FIXED** | `_tee_history` recorded at spawn; `tee_path_for` falls back after detach/kill — `[t]` never renders the false "CLI-launched" copy for a TUI-launched sweep. History is per-root last-write (relaunch overwrites) — correct. |
| IN-02 | **KEPT OPEN — accepted** | Rationale sound: needs a `pipeline/` sweep-start validation (policy vehicle, `_validate_dataset_name_alignment` precedent), hazard requires a hand-named custom key (`+lora/+ia3/+head/+probe/+curve`; no official key contains `+` — re-verified), pre-existing since 06-02, not widened by the fixes. No hidden CR/WR risk: custom↔official key collisions are already refused by `registry_loader`; only derived-alias collisions remain. Route to phase-12 hardening / maintainer ruling as recommended. |
| IN-03 | **KEPT OPEN — accepted** | Correctness unaffected (exclusive worker degrades cadence, never fails); the watch-at-smoke disposition with the fix shape pre-named is the right call against the D-13 proof. |
| IN-04 | **KEPT OPEN — accepted** | Bounded (one manifest read per finished root per 60s), honest-degradation risk nil; pure polish. |

### Introduced-findings sweep (fix diff as fresh surface)

Audited: the CR-01 gate's placement and phrase flow (verified above), WR-01's lane sources (missing/garbled → honest default + the killed-sweep case now refused by the manifest gate), WR-03's release ordering (loop-serialized, no `finally` double-reset), WR-04's `poll()` side effects (reap-only, pruning closes the tee fd — the intended leak fix), WR-05's row identity (stable keys: resolved-root strings / `{model}__{task}`), and the protocol extensions' ty conformance (`ty check tui` green; both backends implement `phrase_matches`). New imports (`run_sweep` in sweep_launcher, `run_config` in sweep_monitor) stay stdlib-only — import purity and the services CJK lock hold (suite green incl. `test_import_lock`).

One minor introduced item:

### IN-06: Diff-preserving tables never reorder — display order drifts from the sorted contract

**File:** `tui/screens/monitor.py:705-763` (`_set_table_rows` appends new rows at the bottom; existing rows are never moved)
**Issue:** New rows (a new sweep root discovered; a new (model, task) row appearing live as the driver mkdirs) are `add_row`-appended at the END rather than inserted at their sorted position, and no full reorder ever occurs (only a column-key-set change triggers one). Over a session the cells table's display order diverges from the `sorted()` contract its data is built in. Cosmetic only — row keys, cell data, and the cursor pin are all correct, so the wrong-row-enter hazard WR-05 fixed cannot recur.
**Fix:** When the incoming key order differs from the table's current row order, fall back to a cursor-preserving full rebuild (clear + re-add in order + re-pin by key) — the same helper, one extra branch.

### FINAL RELEASE VERDICT: **CLEAN**

No CR- or WR-class findings remain at HEAD 40cb0bd; all 11 claimed fixes are CONFIRMED-FIXED against re-run original scenarios, the 3 kept-open INs are accepted with sound rationales (IN-02 routed to phase-12), and the one introduced item (IN-06) is cosmetic and non-blocking. Gates at HEAD: 1032 tests passed (tests/tui + tests/test_sweep.py), ruff clean, ty clean.

_Re-reviewed: 2026-10-13 — gsd-code-reviewer (Claude), iteration 2_
