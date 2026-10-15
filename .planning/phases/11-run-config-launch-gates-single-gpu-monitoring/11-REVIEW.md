---
phase: 11-run-config-launch-gates-single-gpu-monitoring
reviewed: 2026-10-14T16:11:10Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - pipeline/run_sweep.py
  - tests/test_sweep.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_services_run_config.py
  - tests/tui/test_services_sweep_launcher.py
  - tests/tui/test_strings_phase11.py
  - tui/app.py
  - tui/screens/monitor.py
  - tui/screens/run_config.py
  - tui/services/run_config.py
  - tui/services/sweep_launcher.py
  - tui/services/sweep_monitor.py
  - tui/strings.py
  - tui/styles.tcss
findings:
  critical: 1
  warning: 5
  info: 5
  total: 11
status: issues_found
---

# Phase 11 (Incremental): Code Review Report

**Reviewed:** 2026-10-14T16:11:10Z
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found
**Scope:** incremental delta since diff_base `cbfc4e6a7f` — quick tasks 261014-f4w (directories.json startup config + `--log_dir` + slot-4 save/picker seeding), 261014-c2l (storage-root threading), 261014-mlc (nav labels + queue backend bridge), and tonight's gap rounds (run_config state consumption chain). Cross-referenced `pipeline/directories_config.py`, `tui/services/settings.py`, `pipeline/run_finetune.py` flag surface, and the live 2x2 GPU smoke (`pipeline/logs/smoke-2x2-261014.log` + `ps` argv of the running processes) as ground truth.

## Summary

The delta's core seams verify clean against live evidence. The running smoke proves the launcher argv chain end-to-end: the parent `run_sweep.py --log_dir pipeline/logs --output-root pipeline/finetuned/smoke-2x2-261014 --num_train_epochs 1` resolved both relative paths absolute at the driver layer and spawned the child with `--log_dir /home/forrest/Github/dnallmmark/pipeline/logs` and `--output_dir .../pipeline/finetuned/smoke-2x2-261014` as separate list elements; the on-disk cell layout (`{root}/{model}/{task}/seed_42/`) matches `cell_dir_for`. Flag > file > default precedence, absent-everywhere parity, fail-loud malformed-file abort, WR-05 empty-flag guards, the pinned argv tail order, the directories.json seeding/save round-trips, and the CR-01/CR-02/WR-02..WR-07 gap-round fixes are all both implemented and pinned by tests (`tests/test_sweep.py:3243-3491`, `tests/tui/test_services_run_config.py:1243-1561`, `tests/tui/test_services_sweep_launcher.py`, `tests/tui/test_pilot_monitor.py`).

What remains is concentrated in the monitor/attach/exit seams that the incremental work touched only peripherally. One correctness bug in the `[a]` attach path (unresolved path stored, so a `~`/relative attach silently monitors nothing), plus five robustness gaps: a CWD-basis divergence in the launcher's registry key, a silent `[42]` seed fallback in the re-run, a confirm dialog that understates the re-run's GPU spend, a same-second tee-log collision, and the exit modal's single-sweep assumption.

## Critical Issues

### CR-01: `[a]` attach stores the raw operator path — `~`/relative attaches silently monitor nothing

**File:** `tui/screens/monitor.py:1131` (with call site `tui/screens/monitor.py:1519-1527`)
**Issue:** `MonitorScreen.attach()` stores `self._attached_root = Path(str(root))` without `expanduser().resolve()`. Three call sites feed it: `note_launch` and the discovered-table enter (both already-resolved strings — fine), and `action_attach_path`'s `on_submit`, which passes the RAW value from `PathInputModal` (`tui/screens/selection.py:1170-1175` strips whitespace but never expands/resolves). The validation side (`add_manual_root`) resolves internally, so `~/sweeps/run1` VALIDATES and persists correctly, then attaches the literal path `~/sweeps/run1`.

Every non-frontier reader then reads through the unresolved form: `MonitorBackend.cells_view/stats/resume_count/failures_view/cell_record` all do plain `Path(root)` (`tui/services/sweep_monitor.py:761, 980, 815, 1133, 433-435`) — `Path("~/sweeps/run1")` does not exist, so the cell table stays empty, stats stay blank, and `[f]` shows no failures. Meanwhile `frontier_scan` (`sweep_monitor.py:555-556`) DOES `expanduser().resolve()`, so the two cadences disagree; `str(self._attached_root)` never matches the discovered-table keys (resolved), so the `◆` marker never renders on the row the operator just attached; and `attached_running_counts()` reports a root string the launcher registry will never key on. The cells region renders its "未附加 sweep" empty copy while a sweep IS attached — incorrect behavior in exactly this phase's named focus (attach semantics).

All Pilot tests use absolute tmp paths (`test_pilot_monitor.py:879`), so the gap is untested.
**Fix:**
```python
# tui/screens/monitor.py — attach()
def attach(self, root) -> None:
    ...
    self._attached_root = Path(str(root)).expanduser().resolve()
```
(Keep `note_launch`'s pre-resolution as-is; it becomes a no-op.) Add a Pilot case feeding `str(tmp_path)` via the `[a]` modal with a `~`-relative spelling to pin the fix.

## Warnings

### WR-01: SweepLauncher registry key resolves against the TUI process CWD, contradicting the service tier's any-CWD contract (D-14)

**File:** `tui/services/sweep_launcher.py:448` (and `:556-558`, `tui/screens/run_config.py:1905-1907`)
**Issue:** `launch_spec` passes the RAW `spec.output_root` to `_spawn`, whose registry key is `str(Path(output_root).resolve())` — resolved against the TUI process CWD. But `compose_argv` (`tui/services/run_config.py:1137`) threads `_abs_against_repo_root(spec.output_root)`, whose docstring explicitly designs for "the TUI process may run from any CWD". When the TUI is started outside the repo root with a relative output root (e.g. the default `./finetuned`): the spawned sweep writes to `{repo}/finetuned` (argv wins), while the registry key, the tee `{rootname}`, the gate's CR-02 live-root pre-check (`run_config.py:1906`, same CWD basis), and `sweep_launched`→`note_launch`→`attach` all point at `{cwd}/finetuned` — a directory that will never exist. The monitor then auto-attaches a phantom root (empty table, per CR-01's mechanism) and the live-roots signal never matches the scanner's keys. Harmless when the TUI is launched from the repo root (the normal mode), but it silently violates the tier's own stated discipline.
**Fix:** In `launch_spec` (and the screen pre-check), resolve the key through the one seam the argv already uses:
```python
return self._spawn(
    rc.compose_argv(spec),
    rc.resolve_dirs(spec).output_root_abs,   # REPO_ROOT-based, matches argv
    spawner=spawner, clock=clock)
```

### WR-02: `[r]` re-run seed fan-out falls back to a silent `[42]` when the cell table is empty — a different experiment than the one confirmed

**File:** `tui/screens/monitor.py:1222-1228`
**Issue:** `_run_rerun_launch` derives the re-run's seeds from `self._cell_rows` and falls back to `or [42]`. `_cell_rows` is populated only by a full/frontier scan while attached, so attach → `[f]` → `[r]` → confirm before the first scan lands (or any manifest-only edge with no discoverable seed dirs) re-runs the failed pairs at seed 42 ONLY. If the source sweep used other seeds, the confirmed alias cells at those seeds are never re-attempted while seed-42 cells (possibly never part of the failure set) train — silently. The service already has the authoritative seed set in hand: every `FailureRow` carries `.seed`, read from the same failures data the modal was built from.
**Fix:** Derive seeds from the failures view (or thread the modal's rows into the pipeline) and refuse loudly when nothing derivable — never a default:
```python
seeds = sorted({row.seed for row in self._service.failures_view(root)}) or \
        sorted({cs.seed for r in self._cell_rows.values() for cs in r.seeds})
if not seeds:
    self.post_message(self.RerunFailed("no seeds derivable for re-run", root, run_id))
    return
```

### WR-03: The re-run confirm names entry-count `n`, but the launch enumerates pairs × the sweep's full seed set — the confirmed GPU spend can be understated ~3x

**File:** `tui/screens/monitor.py:1166` (with `:574-580`)
**Issue:** `FailuresModal.action_rerun_failures` passes `len(self._failures)` — the count of (model, task, seed) ENTRIES — into `MON_RERUN_CONFIRM.format(n=count)`. `launch_from_failures` then enumerates distinct (model, task) pairs × the sweep's seed set (D-11's documented "across ALL requested seeds"). For a sweep run at seeds {42,43,44} whose failures are all at seed 42, confirming "重跑 10 个失败 cell" launches 10 pairs × 3 seeds = up to 30 trainings (the 43/44 cells never ran, so the trainer_state marker does not skip them). The post-launch toast cannot correct this (the expected total is honestly unknown). This is a destructive-action confirmation that materially understates what is being authorized.
**Fix:** Compute the planned-cell estimate for the confirm copy: `len({(r.model_base, r.task) for r in failures}) * len(seeds)` — or at minimum extend the copy to name the seed fan-out (e.g. `{n} 个失败 cell × seeds {seeds}`).

### WR-04: Tee log filename uses second-resolution timestamp + basename only — two same-basename roots launched in the same second truncate each other's logs

**File:** `tui/services/sweep_launcher.py:102-103, 465-474`
**Issue:** `TEE_FILENAME_FORMAT = "sweep_{ts}_{rootname}.log"` with `ts` at one-second resolution and `{rootname}` = the resolved root's basename. The CR-02 guard only refuses a second LIVE launch at the SAME root; two different roots sharing a basename (e.g. `.../finetuned` and `/mnt/autodl-tmp/finetuned` — the common default basename) can be spawned within the same second (a slot-4 gate confirm racing a monitor `[r]` re-run, which share no mutual exclusion). The second `open(tee_path, "w")` truncates the first sweep's log; both children then interleave into one file from different offsets, corrupting the tail monitor and the audit log for a multi-day run.
**Fix:** Make the name unique per spawn — cheapest: include the registry-keyed counter/pid, or open with mode `"x"` and fall back to a suffixed name; alternatively fold more of the root into `{rootname}` (parent + name) and keep `"w"`.

### WR-05: The exit modal handles only one live sweep — `[k] 终止后退出` exits with the others still running

**File:** `tui/app.py:843-849` (with `tui/app.py:177-218`)
**Issue:** Multiple simultaneous live sweeps at different roots are a supported state (the CR-02 guard blocks only same-root relaunch; nothing prevents launching at root B while root A runs). `action_quit` picks `roots[0]` (sorted) when the launcher registry is non-empty and builds the ExitModal around that single root; `[k]` kills exactly that process group, `[enter]` detaches exactly that one, then the app exits. With two live sweeps, "终止后退出" leaves the second sweep running with no indication — the operator's kill belief is factually wrong (and the message's done/total come from the possibly-unrelated attached root, mixing sources).
**Fix:** When `len(roots) > 1`, either word the message to name every live root and make `[k]` kill all of them (`for root in roots: self._launcher.kill_sweep(root)`), or refuse the plain triple with a "multiple live sweeps" message naming each root.

## Info

### IN-01: `LNC_E2_WARNING` hardcodes the registry counts (59 × 50 × 8850) — copy drifts when the registries evolve

**File:** `tui/strings.py:901`
**Issue:** The E2' escalation banner freezes `59 模型 × 50 数据集 × 3 种子 = 8850 cell`. The gate itself computes fresh (`is_full_e2x` over the live official keys — superset, so it stays correct), but this exact string already had to be hand-edited once for the confidential-model removal (62→59 commits touched sibling docstrings). A future registry change silently makes the authorization copy lie about what is being authorized.
**Fix:** Format the counts from `GateSummary` (e.g. add `{models}`/`{tasks}`/`{seeds}`/`{cells}` fields to the constant) or add a drift tripwire test pinning the constant against `official_keys()`.

### IN-02: Stale placeholder comment over the NAV block

**File:** `tui/strings.py:578-579`
**Issue:** `# Placeholder suffix (slots 3/4/5 — implemented by their delivering phases)` — slots 3/4/5 are all live now; `NAV_PLACEHOLDER_SUFFIX` has no consumer among the six slots.
**Fix:** Update the comment (or remove the constant if truly unused — verify against `tui/screens/nav.py` first).

### IN-03: `cells_view`'s `expected_seeds` parameter is dead in production

**File:** `tui/services/sweep_monitor.py:739-747` (with `tui/screens/monitor.py:382-384`)
**Issue:** The docstring promises "configured-but-not-yet-started seeds render queued (the queued columns)", but `MonitorBackend.cells_view` never threads `expected_seeds` (and nothing injects the configured seed set into the monitor), so the feature is unreachable outside direct service tests.
**Fix:** Either thread the expected seeds (e.g. from `note_launch`'s spec/preview seeds) or drop the parameter and the claim.

### IN-04: Cell-detail modal never reads curve-cell records

**File:** `tui/screens/monitor.py:429-435`
**Issue:** `MonitorBackend.cell_record` reads only `{root}/{model}/{task}/seed_{n}/run_record.json`. Under `--curve`, records live at `seed_{n}/frac_{f}/run_record.json` — the detail modal for a curve row shows fraction states but the "record fields verbatim" block stays empty for every seed.
**Fix:** When the row's `CellSeed.fraction_states` is non-None, read each frac dir's record (join the frac states with their records).

### IN-05: Cell-row key `f"{model}__{task}"` is collision-prone for keys containing `__`

**File:** `tui/screens/monitor.py:1071` (and `:1100`)
**Issue:** Dataset registry keys use the `Source__task` convention (CLAUDE.md), and the custom-model wizard only forbids path separators in keys — a custom model key containing `__` can produce the same join key as a different (model, task) pair (`("a__b", "c")` vs `("a", "b__c")`), merging two rows into one (frontier merge and render share the key).
**Fix:** Use a separator registry keys cannot contain (e.g. `"\x1f"`) or a nested dict keyed by the tuple.

---

_Positive verification notes (delta-specific):_ launcher argv tail order `--cache_dir --model_root --dataset_root --log_dir` is pinned test-side (`tests/test_sweep.py:3257-3275`) and confirmed live; precedence flag > file > default has explicit tests at every consumer (`tests/test_sweep.py:3359-3470`, `tests/tui/test_services_run_config.py:1297-1345`); the `--output-root` argparse-default flip to `None` with `./finetuned` fallback preserves the absent-everywhere byte-identity (`tests/test_sweep.py:3449-3469`); the gate pipeline's fresh-recompute/no-spawn-on-refusal properties, the CR-02 same-root guard, the tee-history `[t]` fallback (IN-05), and WR-02/WR-04 monitor scoping are all pinned in `tests/tui/test_services_sweep_launcher.py` and `tests/tui/test_pilot_monitor.py`. No issues found in `tui/styles.tcss` (token discipline holds), `tests/tui/test_strings_phase11.py` (bidirectional inventory lock passes against the current module), or the queue-backend bridge delta in `tui/app.py`.

_Reviewed: 2026-10-14T16:11:10Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
