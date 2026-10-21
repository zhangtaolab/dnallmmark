---
phase: 16-tui-multi-gpu-surface
plan: 5
subsystem: ui
tags: [textual, tui, snapshot-goldens, d-03-review, fabricated-fixtures, machine-independent, confirm-face]

requires:
  - phase: 16-tui-multi-gpu-surface plan 16-01
    provides: the GpuProbeProvider constructor seam + the standing #mon-gpu panel these goldens pin
  - phase: 16-tui-multi-gpu-surface plan 16-02
    provides: the DispatchStateReader constructor seam + the card dispatch block these goldens pin
  - phase: 16-tui-multi-gpu-surface plan 16-04
    provides: the 多 GPU 调度 params section + LNC_GATE_DISPATCH_LINE on the confirm faces + _RunConfigGoldenService's compose_dispatch_argv delegation
provides:
  - The run_config_confirm golden corpus entry (app builder over a deterministic workers=2 / GPUs 0,1 spec, driven through [enter] to _GateConfirmModal) + the gpu/dispatch fixture wiring on the monitor corpus entries in tests/tui/test_snapshots.py
  - Three regenerated SVGs (run_config, monitor_empty, monitor_running) + one NEW SVG (run_config_confirm) — UNCOMMITTED pending the maintainer's D-03 review (WINDOWS #50)
  - The Rule-1 wrap-clip fix on _GateConfirmModal (the dispatch line as its own Static above the scroll-bounded log)
affects: [tui slot-4 confirm face, the golden comparison lane, the D-03 review batch]

actuals:
  tokens: 8255    # chars/4 over the realized code+ledger diff (vs estimate 14000)
  tasks: 2
  commits: 3      # MEASURED: git rev-list --count 42dc7a6..0061351 (the docs commit lands after this file)
  plan_head_before: 42dc7a693d1a783ee6a0562070a55914c3212a4d
  plan_head_after: 006135187d4fd3f1622df51fab6bd8ce64b91ac1

tech-stack:
  added: []  # zero installs (T-16-SC): existing dev+tui groups only
  patterns:
    - "deterministic frontier-tick golden drives: app.screen._tick_frontier() + settle inside the frozen-clock window (the Pilot G-panel precedent) — never the 2s wall timer inside an export window"
    - "constructor-seam fabrication in goldens: frozen GpuRow / DispatchStateView dataclasses threaded through _golden_app, absent-by-default — identical bytes on a GPU box and a GPU-less CI runner (Pitfall 10)"
    - "Static-above-the-scroll-bound for wrapping copy lines: a line that must stay visible never rides an auto-scrolled RichLog at its bound (the E2' face placement, generalized)"

key-files:
  created:
    - tests/tui/__snapshots__/run_config_confirm.svg   # UNCOMMITTED (D-03)
  modified:
    - tests/tui/test_snapshots.py
    - tui/screens/run_config.py                        # Rule-1 wrap-clip fix
    - tests/tui/test_pilot_run_config.py               # lockstep (3 test sites)
    - .planning/WINDOWS.md
    - tests/tui/__snapshots__/run_config.svg           # UNCOMMITTED (D-03)
    - tests/tui/__snapshots__/monitor_empty.svg        # UNCOMMITTED (D-03)
    - tests/tui/__snapshots__/monitor_running.svg      # UNCOMMITTED (D-03)

key-decisions:
  - "The monitor drives fire the frontier tick DETERMINISTICALLY (app.screen._tick_frontier() + settle, the Pilot G-panel precedent) — the 2s wall timer never fires inside an export window, so the G panel and dispatch block render by construction, not by timing luck"
  - "_golden_app threads BOTH 16-01/16-02 constructor seams defaulting to the absent fakes — the whole corpus (not just the monitor entries) renders machine-independent bytes; the GPU box and CI see identical SVGs"
  - "monitor_running's dispatch fixture holds the snapshot invariant by construction (12+1+1+21+1 active == 36, the strip's done/total) with stale/malformed frozen False — honest golden data, zero clock reads"
  - "The confirm fixture is the 16-04 pilot shape frozen: GateSummary(workers=2, gpus_display='0,1', 15 fabricated pairs) over a spec with workers=2/gpus=('0','1') — 15 pairs pin the cap + the LNC_GATE_PAIRS_MORE line (1+12+1 arithmetic)"
  - "The cursor-blink kill widened from app.screen.query to app.query — the confirm modal stacks over the params screen whose Inputs must stay reachable for the D-11 rule (defensive; unfocused inputs render no cursor)"
  - "WINDOWS numbering: the plan's '#46' was stale (the ledger already carried #46-#49 from 16-01/16-03/16-04) — the new batch is #50; #46/#48 closed (their red windows resolved by this regeneration, folded into #50); #49 removed as an accidental uncommitted double-append of #48"

patterns-established:
  - "Deterministic tick-firing in golden drives (explicit _tick_frontier() call, the same idiom the Pilot suite uses for cadence surfaces)"

requirements-completed: [TUI-04]

coverage:
  - id: D1
    description: "Exactly four golden surfaces change (run_config + monitor pair REGENERATE, run_config_confirm NEW), fabricated through the constructor seams, machine-independent; every other golden byte-identical to HEAD"
    requirement: TUI-04
    verification:
      - kind: unit
        ref: "the porcelain set pin (git status over tests/tui/__snapshots__/ names EXACTLY the four surfaces) + the text-level run_config diff (ADDED-only: the 多 GPU 调度 section rows) + pytest tests/tui/test_snapshots.py -q -> 12 passed on the working tree"
        status: pass
  - id: D2
    description: "Regeneration through make snapshot-update ONLY; the SVGs stay UNCOMMITTED; the phase's commits contain ZERO snapshot paths"
    requirement: TUI-04
    verification:
      - kind: unit
        ref: "make snapshot-update (the sole regen path, Makefile:132-133); git log 5d4ed50..HEAD -- tests/tui/__snapshots__/ EMPTY; porcelain pending count 4; WINDOWS #50 names the D-03 handoff"
        status: pass
  - id: D3
    description: "Phase-close full CPU gates green on the working tree beyond the documented environmental class"
    requirement: TUI-04
    verification:
      - kind: unit
        ref: "pytest tests/tui -q -> 1364 passed / 6 failed (exactly the documented root-user chmod baseline: test_pilot_data_manager 1 + test_services_download_queue 5, identical test names to the 16-04 baseline; the 3 golden reds + WINDOWS #46/#48 windows all green); node --test 26/26; make lint + make typecheck green; ci.yml hash 33d2252e... unchanged"
        status: pass

duration: 26min
completed: 2026-10-21
status: complete
---

# Phase 16 Plan 5: TUI-04 Snapshot Goldens + D-03 Review Batch Summary

**Three regenerated goldens + the NEW run_config_confirm golden over fabricated machine-independent fixtures (GpuRow lanes / DispatchStateView / a workers=2 GPUs-0,1 confirm spec through the _golden_app constructor seams), left UNCOMMITTED under the D-03 discipline as WINDOWS #50 — plus the Rule-1 fix that moved the confirm face's dispatch line out of the scroll-bounded log where its own wrap was clipping it.**

## Performance

- **Duration:** 26 min (plan estimate: 2 tasks; actual: 2 tasks, 3 code commits + the docs commit)
- **Tokens (actuals, chars/4 over the code+ledger diff):** 8,255 vs estimate 14,000 — the corpus extension landed as mostly-additive fixture blocks; the estimate's ceiling assumed heavier drive surgery
- **Commits:** 3 (1d07303 Rule-1 fix, 1317ef4 corpus, 0061351 WINDOWS), measured `git rev-list 42dc7a6..0061351` = 3

## Tasks Completed

### Task 1 — corpus wiring (run_config_confirm NEW + monitor fixture fabrication) + regeneration — 1317ef4 (+1d07303)

- **`tests/tui/test_snapshots.py`:** `_golden_app` gained `launcher/gpu/dispatch` params threading `gpu_probe_provider`/`dispatch_state_reader` into `DnallmMarkTui`, DEFAULTING to the absent fakes (`_absent_gpu_probe` returns the None absent outcome; `_absent_dispatch_reader` returns None) — the entire corpus now renders machine-independent bytes, zero nvidia-smi, zero dispatch_state reads on any lane (Pitfall 10).
- **monitor_empty** pins the ABSENT probe shape: the MON_GPU_ABSENT header note, zero lane rows (the CI-honest degradation, D16-02). **monitor_running** pins two fabricated GpuRow lanes (the UI-SPEC Surface A wireframe values: 47%/15340/32607 MiB/61°C and 12%/958/32607 MiB/33°C) plus a fabricated frozen DispatchStateView (status running, 12/36 done, queue 21, worker 0 busy on plant-dnamamba-6mer × GUE__emp_H3 × seed_42, worker 1 idle — the snapshot invariant holds by construction 12+1+1+21+1==36). Both drives fire `app.screen._tick_frontier()` + settle INSIDE the frozen-clock window — the deterministic Pilot G-panel precedent; the 2s wall timer never fires inside an export window.
- **run_config_confirm (NEW, A5):** `_ConfirmGateLauncherFake` carries GateSummary(models=2, tasks=1, seeds=3, cells=6, workers=2, gpus_display="0,1", 15 fabricated pairs — the 16-04 pilot fixture shape frozen); the spec fixture carries `workers=2, gpus=("0","1")`; the drive opens slot-4, presses [enter] (the picker holds focus: the gate), settles rounds=4, and asserts `_GateConfirmModal` landed. The golden carries the dispatch-plan line above the capped 15-pair list (…共 15 组).
- The cursor-blink kill widened `app.screen.query(Input)` -> `app.query(Input)` (the modal-covered params inputs stay reachable for the D-11 rule).
- **[Rule 1 - Bug] the confirm-face wrap-clip defect (found driving the new golden):** the zh/en LNC_GATE_DISPATCH_LINE is ~50+ console cells (CJK double-width) and wraps to 2 visual rows inside `#cfg-gate-log` (max-height 14); 14 logical lines therefore outgrew the bound and RichLog auto_scroll clipped the line's own top half (probed: `scroll_y=1`; only the "训练项（预览）" wrap fragment rendered — the D16-11 contract demands the line visible above the pair list). Fix: the line renders as its own Static ABOVE the log — the E2' face's own placement — and the log drops to 12 capped pairs + the more-line (13 ≤ 14). Files: tui/screens/run_config.py, tests/tui/test_pilot_run_config.py (three lockstep test sites moved from `log.lines[0]` to the `#cfg-gate-dispatch` Static + a `scroll_y == 0` pin + the 13-line bound check). Commit 1d07303.
- `make snapshot-update` (the ONLY regen path) regenerated all ten goldens; the porcelain delta names EXACTLY the four surfaces (run_config.svg + monitor pair modified, run_config_confirm.svg untracked); a text-level old-vs-new diff over run_config.svg proves the delta ADDED-only (the 多 GPU 调度 title/separator/workers-1/GPUs-placeholder/hint rows — nothing removed); the other six SVGs regenerated byte-identical to HEAD. The four SVGs stay UNCOMMITTED (D16-03).

### Task 2 — WINDOWS D-03 deviation row + phase-close full gates + discipline verification — 0061351

- **WINDOWS #50** opens the Phase-16 D-03 review batch (kind deviation, the four golden files as the path field): the surfaces carried (slot-4 多 GPU 调度 section + the confirm-face dispatch line, monitor G lanes + dispatch rows), the fabricated machine-independent fixtures, the deliberate UNCOMMITTED state pending the maintainer's review (a NEW batch — the tree was clean at phase start, Pitfall 9), and the consequence that the committed tree fails exactly the four golden tests until the review lands (the documented #39 pattern). The plan's "#46" numbering was stale — the ledger already carried #46-#49; #46/#48 closed (their red windows resolved by this regeneration, folded into #50 — one obligation one row, the 12-05 precedent) and #49 removed (an accidental uncommitted double-append of #48; nothing referenced it). Counts: open 10 / fixed 33 / total 49. The previously-uncommitted #47 pty-flake row rode along (the ledger file lands whole).
- **Phase-close full CPU gates on the working tree:** `pytest tests/tui -q` -> **1364 passed, 6 failed** — the 6 decompose exactly as the documented environmental root-user chmod baseline (test_pilot_data_manager 1 + test_services_download_queue 5, identical test names to the 16-04 baseline; this box runs as root so the chmod persist-failure sims cannot pass); the 3 golden reds went green and the new confirm golden passes (16-04's 1360P/9F -> 1364P/6F = +3 recovered +1 new). `node --test tests/js/*.test.js` -> **26/26**. `make lint` + `make typecheck` -> all checks passed. `git hash-object .github/workflows/ci.yml` == `33d2252eb594e0faecece9e8015a332d8d6479ef` (unchanged).
- **Discipline machine-verified:** `git log 5d4ed50..HEAD -- tests/tui/__snapshots__/` EMPTY (zero snapshot commits in the phase range); porcelain pending count 4; the WINDOWS grep finds run_config_confirm.

## Verification Results

- `make snapshot-update` -> 10 goldens written; porcelain set == exactly the four surfaces
- `pytest tests/tui/test_snapshots.py -q` -> **12 passed** (10 goldens + 2 determinism/non-vacuity tests) on the working tree
- `pytest tests/tui/test_pilot_run_config.py -q -k "dispatch or stage_order or gate_happy or pair"` -> 8 passed (the Rule-1 lockstep)
- `pytest tests/tui -q` -> **1364 passed, 6 environmental** (the documented root-chmod class, unchanged)
- `node --test` 26/26; `make lint` / `make typecheck` green; ci.yml hash pin green
- Text-level run_config.svg diff: ADDED-only (the section rows); the six untouched SVGs byte-identical to HEAD

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The confirm face's dispatch-plan line clipped by its own wrap inside the scroll-bounded gate log**
- **Found during:** Task 1, driving the new run_config_confirm golden — the exported SVG carried only the wrap fragment "训练项（预览）" where the D16-11 contract demands the full line above the pair list
- **Issue:** the ~50-cell zh/en wording wraps to 2 visual rows inside `#cfg-gate-log` (max-height 14); 14 logical lines > the bound and RichLog auto_scroll scrolled the line's top half out of view (probed scroll_y=1 at the design grid, both languages, all realistic GateSummary values)
- **Fix:** the line renders as its own Static ABOVE the log (the E2' face's placement); the log carries 12 capped pairs + the more-line (13 ≤ 14); three 16-04 pilot test sites lockstepped. Files: tui/screens/run_config.py, tests/tui/test_pilot_run_config.py. Commit: 1d07303.

**2. [Rule 1 - Bug] WINDOWS #49 was an accidental double-append of #48 (uncommitted)**
- **Found during:** Task 2, reading the ledger before appending
- **Issue:** identical descriptions recorded 6 seconds apart; #49 existed only in the working tree (never committed), nothing referenced it
- **Fix:** removed #49 before appending; counts recomputed (open 10 / fixed 33 / total 49). Files: .planning/WINDOWS.md. Commit: 0061351.

### Notes (no rule needed)

- **The plan's WINDOWS numbering ("next free number after #45 — i.e. #46") was stale** — the ledger already carried #46 (16-01), #47 (16-03), #48/#49 (16-04). The new batch row is **#50**; #46/#48's red-window rows closed as resolved-by-this-regeneration (folded into #50), keeping one obligation one row.
- **tui/screens/run_config.py + tests/tui/test_pilot_run_config.py are outside the plan's `files_modified` list** — the Rule-1 wrap-clip fix (Deviation 1) required them; committing the corpus without the fix would have pinned a defective render into the NEW golden. Committed as a separate commit preceding the corpus commit so every intermediate committed tree stays coherent.
- The Task-1 verify's porcelain check and the Task-2 discipline checks both pass with `run_config_confirm.svg` UNTRACKED (the `??` porcelain form) — the plan's awk `$2` projection handles it as written.

## Known Stubs

None — every golden renders through the real screen stack over fabricated frozen dataclasses; nothing is mocked at the widget level.

## Handoff Notes (the maintainer's D-03 review)

- **Review batch WINDOWS #50:** inspect `git diff tests/tui/__snapshots__/` + the new `run_config_confirm.svg` in a browser/editor, then commit the four SVGs together with a closing note on #50 (the #35/#39/#42 precedent). Until then the COMMITTED tree fails exactly `test_run_config_golden`, `test_run_config_confirm_golden`, `test_monitor_running_golden`, `test_monitor_empty_golden` — the working tree is green.
- The monitor golden deltas carry exactly the Phase-16 chrome (the #mon-gpu panel with fabricated lanes / the absent note; the dispatch block under the summary strip); the run_config delta is the ADDED-only params section.
- Phase 16 closes with TUI-01..TUI-04 all delivered: the ROADMAP success criteria 1-4 map to 16-01 (probe service + G panel), 16-03/16-04 (slot-4 launch through the unchanged chain, gate-order extended not weakened), 16-02 (slot-5 dispatch rows), and this plan (criterion 4's goldens half + the review batch opened).

## Threat Mitigations Landed

- **T-16-08 (Tampering — the D-03 review discipline):** machine-verified — the git-log-over-snapshots emptiness check over the phase range, the exactly-four-files porcelain pin, and the untouched-SVG byte-identity (six goldens regenerated byte-identical) all ran as plan verify commands; WINDOWS #50 makes the batch visible to the maintainer; the SVGs rode NO commit.
- **T-16-SC (Tampering — package installs):** zero installs — regeneration ran the existing dev+tui groups only; the ci.yml blob hash is pinned unchanged.

## Self-Check: PASSED

- tests/tui/__snapshots__/run_config_confirm.svg exists (untracked, pending D-03); the three modified SVGs pending in the tree
- Commits 1d07303, 1317ef4, 0061351 are ancestors of HEAD; `git rev-list 42dc7a6..HEAD` = 3 (pre-docs)
- All verify lanes re-run green after the final code commit (12 snapshot tests, 8 lockstep pilot tests, full tui 1364P/6-env, node 26/26, lint, typecheck, hash pin)
