---
phase: 16-tui-multi-gpu-surface
plan: 3
subsystem: ui
tags: [textual, tui, multi-gpu, capacity-gate, dispatch-argv, lockstep-amendment, registry-only]

requires:
  - phase: 13-dynamic-dispatch-core
    provides: the frozen run_sweep_shard CLI surface (--mode dispatch, --workers, --gpus arity) the composer targets
  - phase: 16-tui-multi-gpu-surface plan 16-01
    provides: the wave-1 base (both siblings landed at this plan's base 4645157)
provides:
  - RunSpec.workers/gpus + the three collect-all mirror codes + compose_dispatch_argv in tui/services/run_config.py (the 16-04 screen renders fields over these; compose_argv byte-untouched beside it)
  - GpuCapacityBlock + the multi-GPU capacity predicate (registry-only demand arithmetic, zero-arg-callable preserved) + the dispatch routing at launch_spec's spawn site in tui/services/sweep_launcher.py
  - The amended LNC_SINGLE_GPU_BLOCKED (name unchanged, {roots}+{workers}+{n}) with ALL 7 HEAD format sites migrated lockstep in one commit
  - The extended capacity/gate test families (zero weakening) incl. the T-16-06 /proc boundary pin
affects: [16-tui-multi-gpu-surface (16-04 slot-4 screen, 16-05 goldens), tui launch gate semantics]

actuals:
  tokens: 16626   # chars/4 over the 9-file realized diff (vs estimate 32000)
  tasks: 2
  commits: 2       # MEASURED: git rev-list --count 4645157..99144d5
  plan_head_before: 46451572087677b50f77e17c2a1b9748c7a2257a
  plan_head_after: 99144d5d2ecc5eb2d8385fa16a4d78c91f3a005e

tech-stack:
  added: []  # zero installs (T-16-SC): stdlib parsing only
  patterns:
    - "structured refusal detail: the frozen GpuCapacityBlock dataclass carries roots/requested/gpu_count service-side — screens format the amended copy, never compute (Pitfall 2 resolution)"
    - "registry-only demand arithmetic: per-entry demand parsed from LiveSweep.argv (script-name membership + the integer after --workers, default 1 fail-safe), per-root cached (the _plan_cache precedent) — probe_cli_sweeps stays display-only, pinned by test"
    - "in-place string amendment with lockstep format sites: every .format call site changes in the SAME commit; the grep gate (zero sites without workers=) is the mechanical proof"

key-files:
  created: []
  modified:
    - tui/services/run_config.py
    - tui/services/sweep_launcher.py
    - tui/screens/run_config.py
    - tui/screens/monitor.py
    - tui/strings.py
    - tests/tui/test_services_run_config.py
    - tests/tui/test_services_sweep_launcher.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_monitor.py

key-decisions:
  - "launch_spec threads requested_workers=getattr(spec, 'workers', 1) into stage-0 (the tolerant idiom — a spec-less double reads demand-only); launch_from_failures and all three monitor pre-checks stay ZERO-ARG (requested defaults 1; a re-run/resume is a one-worker plain launch, Pitfall 3)"
  - "The refusal problem-tuple DETAIL is the GpuCapacityBlock itself (not a pre-joined string) — _problem_line and the monitor notify branches format the amended copy from its fields; numbers computed service-side, the screens format only"
  - "Demand parse: argv membership by Path-name == run_sweep_shard.py (either mode — the demand keys on the script name, never --mode), the integer after a SEPARATE --workers element (flag-absent/parse-failure/malformed -> 1, the fail-safe per the threat register); per-root cache behind _entry_demand"
  - "workers_exceeds_gpus mirror fires on the SHORT side only (len(gpus) < workers, evaluated when both legs parsed clean) with a structured (workers, n) detail for the 16-04 copy; a longer list stays CLI-authoritative (its own arity refusal); NO workers-vs-models mirror exists (pinned by a registry-level test)"
  - "Pre-Phase-16 state documents load workers/gpus through the absent-key path (defaults 1/None — byte-identical launches); gpus None persists as None, never a resolved list (Pitfall 8)"
  - "RunConfigDouble gained the compose_dispatch_argv seam (dispatch_compose_calls counter, argv fallback) — the existing compose_calls assertions moved to the dispatch counter, the lockstep edit the routing forces"

patterns-established:
  - "Dispatch-argv routing at the service spawn site: every slot-4 launch composes run_sweep_shard --mode dispatch (UI-SPEC auto-default #9) — the composer changes, the spawn seams (tee/O_EXCL/killpg/registry key basis) untouched"

requirements-completed: [TUI-02]

coverage:
  - id: D1
    description: "RunSpec workers/gpus + the three mirrors + compose_dispatch_argv with persistence pins (defaults, round-trip, pre-Phase-16 backward edge, sorted-dedup normalization, present-only --gpus, always-explicit --workers, absolute root, compose_argv pins green unmodified)"
    requirement: TUI-02
    verification:
      - kind: unit
        ref: "tests/tui/test_services_run_config.py (19 new tests; 175 total green; grep >= 2 for compose_dispatch_argv/workers_exceeds_gpus)"
        status: pass
  - id: D2
    description: "The multi-GPU capacity predicate owns stage 0 with byte-identical position/vehicle; the amended refusal copy renders at every site with counts; the dispatch composer feeds the spawn; zero-arg + seam-tolerance survive; registry-only boundary pinned"
    requirement: TUI-02
    verification:
      - kind: unit
        ref: "tests/tui/test_services_sweep_launcher.py (capacity family: within-capacity admits, over-capacity refuses naming roots+counts with call-count proofs, static --workers 2 demand, flag-absent demand 1, zero-arg read, /proc boundary pin, E2' matching-phrase spawn, real-module routing pin)"
        status: pass
      - kind: automated_ui
        ref: "tests/tui/test_pilot_run_config.py + tests/tui/test_pilot_monitor.py (amended-copy render at all three pilot format sites; the 1047 seam-less-fake tolerance test passes VERBATIM unedited)"
        status: pass
  - id: D3
    description: "The gates: lockstep grep zero (no format site without workers=), make lint + make typecheck, ci.yml hash unchanged, effective_gpu_count + probe_cli_sweeps byte-identical"
    requirement: TUI-02
    verification:
      - kind: unit
        ref: "grep {workers} strings.py 3 >= 1; LNC format sites without workers= == 0 (7 sites total at this base); make lint && make typecheck green; git hash-object .github/workflows/ci.yml == 33d2252eb594e0faecece9e8015a332d8d6479ef; awk-extracted function bodies byte-identical vs HEAD"
        status: pass

duration: 37min
completed: 2026-10-21
status: complete
---

# Phase 16 Plan 3: TUI-02 Slot-4 Multi-GPU Service Tier Summary

**RunSpec workers/gpus with three collect-all mirrors and a frozen dispatch argv composer, plus the EHC-3 stage-0 predicate replaced in place by registry-only multi-GPU capacity arithmetic (GpuCapacityBlock detail) — stage order and vehicle byte-identical, the LNC_SINGLE_GPU_BLOCKED amendment landed lockstep across all 7 HEAD format sites in one commit.**

## Performance

- **Duration:** 37 min (plan estimate: 2 tasks; actual: 2 tasks, 2 commits)
- **Tokens (actuals, chars/4 over the diff):** 16,626 vs estimate 32,000 — the two services + the lockstep landed leaner than the estimate's ceiling; the behavior matrix landed as 19 run_config tests + 7 new/extended launcher tests + 3 pilot lockstep edits
- **Commits:** 2 (1c34bcf Task 1, 99144d5 Task 2), measured `git rev-list 4645157..99144d5` = 2

## Tasks Completed

### Task 1 — RunSpec workers/gpus + parse mirrors + compose_dispatch_argv + persistence pins — 1c34bcf

- **RED -> GREEN:** the 19-test suite was written first and failed at the constructor/attribute (17 RED) before the fields/composer landed; two GREEN-step test-side faults fixed (the base-element count is 14 not 12 — --seeds included; the direct-write fixture needed `state.mkdir`).
- `RunSpec` gains `workers: int = 1` and `gpus: tuple[str, ...] | None = None` (gpus normalizes sorted/deduped in `__post_init__`); `RUN_SWEEP_SHARD_SCRIPT` resolved the REPO_ROOT-basis way `RUN_SWEEP_SCRIPT` already is.
- `parse_params` mirrors: `workers_invalid` (int >= 1), `gpus_invalid` (indices-only — deliberately NARROWER than the CLI's UUID/MIG grammar, the documented Pitfall-7 asymmetry noted in the helper's docstring; an EMPTY field is absent, the epochs idiom), `workers_exceeds_gpus` (short-side only, structured `(workers, n)` detail); NO workers-vs-models code exists (registry-level test pin). Cross-check evaluated only when both legs parse clean.
- Persistence: workers/gpus ride `params` with absent-key defaults — a pre-Phase-16 document loads 1/None (pinned); gpus None persists as None, never a resolved list (Pitfall 8, pinned).
- `compose_dispatch_argv`: the frozen shape `[sys.executable, RUN_SWEEP_SHARD_SCRIPT, --mode, dispatch, --workers <ALWAYS explicit — A2>, (--gpus <joined> present-only), --models, --output-root <absolute>, --tasks, --seeds, <the SAME pinned present-only sweep-flag tail>]`; `compose_argv` byte-untouched beside it (git diff shows zero deletions inside it; its tier-1 pins green unmodified).

### Task 2 — capacity predicate swap + LNC lockstep amendment + capacity family + routing — 99144d5

- **RED -> GREEN:** the new capacity family failed at `GpuCapacityBlock` absence (7 RED) before the service landed; lint/typecheck GREEN-step fixes (FURB136 `max(demand, 1)`; the `cast(GpuCapacityBlock, detail)` narrowing for ty in `_problem_line`).
- `tui/strings.py`: `LNC_SINGLE_GPU_BLOCKED` amended IN PLACE (name unchanged, the MON_RERUN_CONFIRM precedent) to the UI-SPEC Copywriting wording verbatim — zh `⚠ GPU 容量不足 — 运行中训练任务（{roots}）+ 本次 {workers} workers 超过 {n} GPU：请等待完成、经退出门终止，或减少 workers` / the en twin.
- `tui/services/sweep_launcher.py`: frozen `GpuCapacityBlock(roots, requested_workers, gpu_count)`; `single_gpu_launch_blocked(requested_workers: int = 1)` keeps the NAME and zero-arg-callability — count 0 admits unconditionally (the EHC-3 letter), refuse iff `sum(registry demand) + requested > count`; `_entry_demand_for_argv` (script-name membership + the integer after `--workers`, default 1 fail-safe, `max(demand, 1)`) behind `_entry_demand`'s per-root cache (the `_plan_cache` precedent); `effective_gpu_count()` and `probe_cli_sweeps` byte-identical (awk-extracted bodies diffed vs HEAD).
- `launch_spec`: stage-0 position byte-identical, now threading `requested_workers=getattr(spec, "workers", 1)`, refusal detail = the block; the `_spawn` call routes through `rc.compose_dispatch_argv(spec)` (UI-SPEC auto-default #9) with the spawn key unchanged (`rc.resolve_dirs(spec).output_root_abs`, WR-01). `launch_from_failures` keeps the zero-arg stage-0 (detail = the block).
- Lockstep (ONE commit): `run_config.py` screen — the facade forwards `requested_workers`, the gate slot threads `spec.workers`, `_problem_line` formats from the block's fields; `monitor.py` — all three refusal renders format from the block (zero-arg pre-checks unchanged); the three pilot test format sites updated with the amended-copy assertions including the counts. The grep gate passes: `LNC_SINGLE_GPU_BLOCKED.format` sites without `workers=` == 0.
- Test families: `_live_single_gpu_launcher` gained the argv seed (+ `_shard_entry_argv`); new within-capacity/over-capacity/static-demand/flag-absent/zero-arg//proc-boundary tests; the existing EHC-03 subsumption test TIGHTENED to the block shape (extension, not weakening); `RunConfigDouble` gained the dispatch composer seam; the real-module spawn test became the routing pin (argv == compose_dispatch_argv, contains run_sweep_shard + `--mode dispatch`, registry key + cwd pins unchanged); the 1047 seam-tolerance test passes VERBATIM (zero edits).

## Verification Results

- `pytest tests/tui/test_services_sweep_launcher.py tests/tui/test_services_run_config.py tests/tui/test_pilot_run_config.py tests/tui/test_pilot_monitor.py -q` -> **473 passed** (re-run green post-commit)
- Lockstep greps: `{workers}` in strings.py = 3 >= 1; format sites without `workers=` = **0** (7 sites at this base: run_config.py:414-area, monitor.py x3, test_pilot_run_config.py, test_pilot_monitor.py x2)
- `make lint` + `make typecheck` -> **all checks passed**; `git hash-object .github/workflows/ci.yml` -> **33d2252eb594e0faecece9e8015a332d8d6479ef** (unchanged)
- Boundary proofs: `effective_gpu_count` and `probe_cli_sweeps` function bodies **byte-identical** vs HEAD (awk extraction + diff); zero diff hunks inside `compose_argv`
- `pytest tests/tui/test_pty_driver.py -q` -> **15 passed** (see Deviations: one intermittent environmental flake, re-run green x2)
- `pytest tests/tui/test_pilot_monitor.py tests/tui/test_strings_phase11.py tests/tui/test_import_lock.py -q` -> **136 passed**
- Broader lane (`tests/tui` minus the four already-run files) -> 1112 passed + the 6 documented environmental root-chmod failures (untouched files; the standing box baseline) + the 2 standing monitor golden failures (WINDOWS #46, 16-05 owns the D-03 regen)
- `git status` shows exactly the nine plan files committed; no uncommitted golden SVGs

## Deviations from Plan

### Notes (no rule needed)

**1. The format-site census: 7 sites (4 code + 3 test), not the plan prose's "5 code + 3 test"**
- **Found during:** Task 2 pre-edit census (the plan's own instruction: "verify the count at YOUR base before editing — 16-01/16-02 may have shifted lines")
- **Resolution:** the plan's `<verify>` enumerated list matches my base exactly (run_config.py:414-area, monitor.py x3, three test sites); the "5+3=8" arithmetic in the objective/acceptance prose is internally inconsistent with its own verify. Executed against the verified census: all 7 sites lockstep, grep gate 0.

**2. [Rule 1 - lockstep] The routing forced two existing launcher-test assertions to move**
- **Found during:** Task 2 GREEN
- **Issue:** `test_launch_spec_e2x_matching_phrase_spawns` asserted `compose_calls == 1` and the real-module test asserted `argv == run_config.compose_argv(spec)` — both test the OLD spawn routing.
- **Fix:** the double's counter assertion moved to `dispatch_compose_calls`; the real-module assertion became the plan's Test 9 routing pin (`argv == compose_dispatch_argv(spec)` + script-name/mode pins). Files: tests/tui/test_services_sweep_launcher.py. Commit: 99144d5. (The plan's own lockstep mandate — "the existing format-site tests ... are updated in the same commit" — anticipated same-commit test edits.)

**3. Intermittent pty byte-silence flake (environmental, pre-existing exposure)**
- **Found during:** the post-commit pty lane
- **Issue:** `test_monitor_quiet_cadence_is_byte_silent` failed ONCE (real probe over real 5090s — a genuine hardware value change writes legitimate bytes; 16-01 RESEARCH Pitfall 5's documented exposure), then passed on the next run and the full lane passed again (15/15, twice).
- **Resolution:** NOT a regression — this plan touches nothing in the probe/render path (the monitor diff is confined to the three refusal branches). Recorded to WINDOWS (deviation kind) so the Pitfall-5 escalation option (a test-scoped probe override) stays visible at ship time; no pin weakened.

## Known Stubs

None — the predicate, the composer, the mirrors, and the lockstep copy are wired end-to-end; every number in the refusal copy travels service-side in the GpuCapacityBlock.

## Handoff Notes (16-04 — the slot-4 screen)

- The problem COPY constants land with the screen: `CFG_WORKERS_INVALID_PROBLEM` / `CFG_GPUS_INVALID_PROBLEM` / `CFG_WORKERS_EXCEED_GPUS_PROBLEM` (UI-SPEC Copywriting table wording) — `_problem_line` maps the three codes; the `workers_exceeds_gpus` detail is the structured pair `(workers, gpu_count)`, format-ready for `{workers}`/`{n}`.
- The params pane's 多 GPU 调度 section threads `PARAM_WORKERS`/`PARAM_GPUS` into `_compose_spec`'s field dict — `parse_params` consumes them; `workers` carries its live default "1" (a VALUE, not a placeholder), `gpus` empty = None (all-detected).
- The confirm-face `LNC_GATE_DISPATCH_LINE` (16-04) composes from `spec.workers` + the resolved-or-all GPU rendering (auto-default #8: `GPUs all(2)` at preview time); the `[p]` argv preview shows `rc.compose_dispatch_argv(spec)` verbatim.
- The gate slot already threads `requested_workers=spec.workers` — the screen needs no further gate change beyond rendering the fields.

## Threat Mitigations Landed

- **T-16-05 (Elevation — launch-gate bypass via screen state):** stage-0 still fires service-side BEFORE the preview recompute with the refusal returning before the spawner (call-count proofs green over the new arithmetic); the screen pre-check stays UX.
- **T-16-06 (Tampering — capacity scope creep into /proc):** the predicate reads `live_sweeps()` + stored argv ONLY; `probe_cli_sweeps` byte-untouched and pinned display-only by `test_capacity_predicate_never_reads_proc` (a silent widening fails the pin); parse failures fail safe at demand 1.
- **T-16-SC (Tampering — package installs):** zero installs; stdlib parsing only.

## Self-Check: PASSED

- All nine plan files modified (none created); `git rev-list 4645157..99144d5` = 2; commits 1c34bcf + 99144d5 are ancestors of HEAD (99144d5)
- All verify lanes re-run green after the final commit (473 + 15 + 136 tests, lint, typecheck, grep + hash gates)
