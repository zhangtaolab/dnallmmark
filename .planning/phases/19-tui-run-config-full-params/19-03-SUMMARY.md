---
phase: 19-tui-run-config-full-params
plan: "03"
subsystem: tui-run-config
tags: [journey-driver, param-channel, choice-modal, goldens, d-03-review-batch, windows-ledger]

requires:
  - phase: 19-02
    provides: "the slot-4 advanced surface this plan drives — #cfg-input-/#cfg-value-<dasherized> ids, the [a]/[r] bindings, the collapsed 高级参数 section, ChoiceModal RadioSet semantics, and the export-placeholder pin (5) the regenerated goldens capture"
  - phase: 19-01
    provides: "run_sweep.ADVANCED_TRAIN_FLAGS — the --param name/value authority the driver validates against"
provides:
  - "scripts/live/record_tui_live_svg.py --param <name>=<value> (repeatable; table-validated at parse; pa6-refused) — the generalized typing/picking channel superseding the one-param --batch-text pattern for future params"
  - "The generalized assertion pair: typed ⇒ adjacent [flag, serialized-value] pair present; untouched table flag ⇒ absent (whitespace-piece-wise so json-kind tokens match)"
  - "The phase-19 run_config.svg + run_config_confirm.svg regeneration (UNCOMMITTED review batch) + WINDOWS deviation row #52"
  - "Phase 19 complete: the full 18-param advanced surface is TUI-settable, validated, persisted, threaded, replayed, and evidenced end-to-end with every lane green"
affects:
  - "future driver evidence runs (any advanced param rides --param; --batch-text stays byte-intact for the batch row)"
  - "the maintainer's D-03 golden adjudication (the standing batch is now #50's monitor pair + #52's run_config pair)"

actuals:
  tokens: 7174   # chars/4 over the realized 3-file diff (28697 chars)
  tasks: 2
  commits: 2      # measured: git rev-list --count 494887b..HEAD

plan_head_before: 494887b903ed89e443f7a5e6f962a73f6284eaba
plan_head_after: 12e3827ae606fbc1685b2e91c4c3658888a43b30

tech-stack:
  added: []
  patterns:
    - "one CLI channel per widget family: Input kinds typed via the _type_into idiom, enum/bool kinds driven through the REAL modal journey (ChoiceModal opens → verify the option id list → walk the RadioSet -selected cursor → first-toggle apply), both asserting through the same [p] token check"
    - "assertion pairs generalize the 261023-abu --batch-text contract: presence is piece-wise (a json token {\"a\": 2} splits on its own spaces), absence loops the whole table minus the typed set"
    - "parse-time refusal naming the authority: unknown names list the 18-flag vocabulary, enum/bool errors list the closed choices, numeric errors name the table bounds — the table is imported via run_sweep, never re-declared"

key-files:
  created: []
  modified:
    - scripts/live/record_tui_live_svg.py
    - .planning/WINDOWS.md
    - tests/tui/test_services_run_config.py   # phase-gate ty narrowings (deviation 3)
    - tests/tui/test_pilot_run_config.py      # phase-gate ty narrowings (deviation 3)

key-decisions:
  - "--param accepts the undashed field name (learning_rate), the dashed flag (--learning_rate), and the dasherized widget-id spelling (learning-rate) — one normalization, messages name the field vocabulary"
  - "duplicate same-name --param refused at parse (the assertion pair assumes one value per flag; fail-fast over silent last-wins)"
  - "the json-kind assertion token reconstructs multi-space values piece-wise from the whitespace-split preview line instead of assuming one token per flag"
  - "WINDOWS ledger reconciled to its fenced-JSON sole source of truth before the sanctioned append: committed table row #51 transcribed into the store, row #50's swapped test-name fragments aligned — gsd_run windows append works again (open 12 / total 51)"
  - "the make tui display lane evidenced under a pty with a timeout kill: exit 124 + zero Traceback/ImportError + the rendered nav bar = clean composition in the --group tui --group gpu env"

requirements-completed: ["TUI19-full-params", "P19-R7", "P19-R8"]

coverage:
  - id: D1
    description: "The --param channel: repeatable, table-validated at parse (name/enum/bool/int/float/json), pa6-refused, --batch-text byte-unchanged"
    requirement: "P19-R8"
    verification:
      - kind: other
        ref: "driver CLI lanes: full --dry-run with learning_rate/lr_scheduler_type/bf16 exit 0 + timeline advanced-params line; pa6 --dry-run --param exits 2; unknown name exits 2 listing the 18-flag vocabulary; bad enum exits 2 listing 12 schedulers; bad bool exits 2; json array exits 2; float out of bounds exits 2; int/float/json-object accepted; git diff insertions-only around the batch-text blocks"
        status: pass
    human_judgment: false
  - id: D2
    description: "The full-mode journey leg + assertion pair, proven WITHOUT launching: typing + modal picks, [p] adjacent pairs present, all 16 untouched table flags absent, evidence meta beside batch_input_value"
    requirement: "P19-R8"
    verification:
      - kind: automated_ui
        ref: "--mode full --no-launch rehearsal over mktemp throwaway root/svg/evidence/ledger/report: exit 0, gate reached, n pressed; evidence.json argv carries ['--learning_rate','0.0001'] + ['--lr_scheduler_type','cosine'] adjacent, ZERO untouched table flags, --num_train_epochs/--batch_size absent, params_typed recorded, launched=false; 8 SVG stages exported incl. 012/013/014"
        status: pass
    human_judgment: false
  - id: D3
    description: "Goldens regenerated via the only sanctioned path with monitor dirt byte-preserved, the review batch ledgered (WINDOWS #52) and left uncommitted"
    requirement: "P19-R7"
    verification:
      - kind: other
        ref: "make snapshot-update (all 10) → monitor pair restored + sha256sum -c OK + cmp byte-identical; git status shows exactly the 4 expected modifications, nothing staged; tests/tui/test_snapshots.py 12 passed post-regen; WINDOWS.md row #52 + counters 12/51"
        status: pass
    human_judgment: false

duration: 26 min
completed: 2026-10-24
status: complete
---

# Phase 19 Plan 03: Evidence and stabilization — driver --param channel + goldens batch + phase-close gates Summary

**The journey driver's typed-param channel generalized from --batch-text to a repeatable table-validated --param (Input typing + real ChoiceModal RadioSet picks + the presence/absence assertion pair), proven on non-launching lanes with the FHS sweep untouched, and the phase-19 run_config goldens regenerated through the sanctioned path into the standing D-03 review batch (WINDOWS #52).**

## Performance

- **Duration:** 26 min (01:31–01:58 UTC)
- **Started:** 2026-10-24T01:31:42Z
- **Completed:** 2026-10-24T01:58:00Z
- **Tasks:** 2/2
- **Files modified:** 4 (the plan's 3 + 2 test files via deviation 3, goldens deliberately uncommitted)

## Accomplishments

- **Task 1 (`5503f5a`)**: the `--param NAME=VALUE` channel — repeatable argparse flag validated against `run_sweep.ADVANCED_TRAIN_FLAGS` at parse (unknown names name the 18-flag vocabulary; enum/bool values must come from the table choices; int/float bounds; json dict shape; `--mode pa6` refused), the full-mode journey leg (`_drive_advanced_params`: picker focused so `a` reaches the screen binding, section expanded, Input kinds typed via `_type_into`, enum/bool kinds driven through the real ChoiceModal — option-id verification, `-selected`-cursor walk, first-toggle apply), the assertion pair in the `[p]` preview (adjacent pairs piece-wise so json tokens match; the untouched-flag absence loop), `params_typed` in the evidence meta, the dry-run timeline `advanced-params=` line, and `--batch-text` byte-unchanged.
- **Task 2 (`12e3827`)**: goldens regenerated via `make snapshot-update` (the only regen path) with the monitor pair backed up BEFORE and restored AFTER (sha256-verified byte-identical); the run_config pair left UNCOMMITTED as the phase-19 review batch and ledgered as WINDOWS #52; the ledger's pre-existing store breakage reconciled so the sanctioned `gsd_run windows append` path works again; three phase-gate ty narrowings fixed in 19-02's test files; every phase-close lane green.

## Verification Evidence

**The driver's three verify lanes (Task 1):**
- Full `--dry-run` with `--param learning_rate=0.0001 --param lr_scheduler_type=cosine --param bf16=false`: exit 0, timeline prints `advanced-params=--learning_rate=0.0001 --lr_scheduler_type=cosine --bf16=false`.
- Full `--no-launch` rehearsal over throwaway mktemp root/svg/record/evidence **+ ledger/report** (deviation 1): exit 0, `mode=full-rehearsal`, `launched=false`, gate reached and dismissed with `n`; evidence argv carries the two adjacent pairs, ZERO untouched table flags, `--num_train_epochs`/`--batch_size` absent, `params_typed` beside `batch_input_value`; 8 stage SVGs exported (001/002/004/010/011/012/013/014).
- pa6 `--dry-run --param`: exit 2 (`--param requires --mode full`).
- Extra parse matrix: unknown name / bad enum / bad bool / json array / float out of bounds each exit 2 with the vocabulary named; int+float+json-object accepted (exit 0).

**Phase-close gates (Task 2), per-lane counts:**

| Lane | Result |
| ---- | ---- |
| tests/test_sweep.py | 180 passed |
| tests/test_dispatch_core.py | 141 passed |
| tests/test_run_finetune_contracts.py | 80 passed |
| tests/tui/test_services_run_config.py | 250 passed |
| tests/tui/test_pilot_run_config.py | 121 passed |
| tests/tui/test_strings_phase11.py | 12 passed |
| tests/tui/test_import_lock.py | 1 passed |
| tests/tui/test_snapshots.py | 12 passed (post-regen consistency) |
| Combined 8-suite run | **797 passed in 153s** |
| make check-node | exit 0; node --test 44/44 |
| ruff (13 phase-touched files) | All checks passed |
| ty (same 13 files) | All checks passed (after deviation 3) |
| make tui display lane (pty, 45s kill) | exit 124, 0 Traceback/ImportError, nav bar rendered |
| sha256sum -c monitor backup | OK × 2 (pre-existing dirt byte-preserved) |

**Golden delta (the abu Task-3 shape, exact fragments):** `run_config.svg` ADDS the collapsed 高级参数 section chrome — the `高级参数` title, the `空 = YAML 默认；变体配置默认不同` variance hint, the `设置 effective_batch_size 时 GA 仍由其重算` EBS/GA hint, and the `展开高级` `[a]` footer affordance — plus the whole params-pane re-flow below it (repositioned coordinates only; the removed `enter`/`启动确认` footer fragments re-wrap into the longer `回车 打开启动确认 · Y 启动 / N 取消` keymap line — semantically added-only, nothing dropped; the 13 Inputs + 5 ChoiceRows stay hidden behind the collapse). `run_config_confirm.svg` carries the same pane re-flow behind the modal plus the re-wrapped keymap and the two `▾` ChoiceRow affordances (peft/variant rows repositioned; the confirm modal itself is untouched by 19-02). The `[r] 恢复高级默认` footer affordance does NOT render (footer width truncation — observed, not a defect). The other eight goldens byte-identical to HEAD.

**FHS sweep safety:** status running, 7/93 completed, 0 failed before AND after every lane; watcher PID 733194 alive throughout; both trainer GPU processes untouched; zero writes under `pipeline/finetuned-fhs*` and zero writes under `pipeline/` by any evidence run (all rehearsal outputs on mktemp throwaway roots under `/root/autodl-tmp/tmp`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Rehearsal verify-command adaptations: --root and throwaway --ledger/--report**
- **Found during:** Task 1 (verify lane 2 execution)
- **Issue:** The plan's rehearsal command uses `--output-root`, a flag that does not exist (the driver's flag is `--root` — it would exit 2 unrecognized); and it omits `--ledger`/`--report`, whose full-mode defaults are `docs/live/fhs/download_ledger.json` + `docs/live/fhs/REPORT.md` — the IN-FLIGHT FHS run's untracked evidence files. The rehearsal's `_write_ledger` + `_write_report` would have clobbered them.
- **Fix:** Ran the lane with `--root` and all five output paths (`--svg-dir --record --evidence --ledger --report`) on mktemp throwaway roots. Lane intent unchanged.
- **Files modified:** none (execution adaptation)
- **Verification:** rehearsal exit 0; `git status docs/live/fhs/` unchanged (still only the pre-existing untracked files).
- **Committed in:** n/a (no code change)

**2. [Rule 3 - Blocking] WINDOWS ledger store reconciliation before the #52 append**
- **Found during:** Task 2 (ledger append)
- **Issue:** `gsd_run windows append` refused twice on pre-existing store breakage from quick-261023-abu's hand-append: row #51 existed in the table with no JSON record (counts 11/50 vs 10/49), and row #50's table text had two test names swapped vs its JSON record. The plan's own instruction ("update ... the trailing JSON records block per the existing shape") requires the store to be editable.
- **Fix:** Transcribed the committed #51 table row into the fenced JSON store verbatim (zero new information), aligned #50's `test_monitor_running_golden, test_monitor_empty_golden` fragment order to its JSON record (the sole-source-of-truth direction per the tool), then the sanctioned append landed #52 cleanly (open 12 / total 51 / last_updated 2026-10-24).
- **Files modified:** .planning/WINDOWS.md
- **Verification:** `gsd_run windows status` → ok; row #52 present in table + JSON.
- **Committed in:** 12e3827 (Task 2 commit)

**3. [Rule 3 - Blocking] Phase-gate ty narrowings in 19-02's test files**
- **Found during:** Task 2 (the plan's ty-over-touched-files lane)
- **Issue:** `ty check` over the phase-touched set reported 3 pre-existing-from-19-02 diagnostics: `tuple(table_row.choices)` at test_pilot_run_config.py:4963/:4971 (choices is `tuple | None`) and `**_PRE_CHANGE_DOC["params"]` at test_services_run_config.py:2364 (object not provably a mapping). The plan requires this exact lane green at close.
- **Fix:** `tuple(table_row.choices or ())` at both pins; `cast(dict, _PRE_CHANGE_DOC["params"])` local at the drifted-entry merge.
- **Files modified:** tests/tui/test_pilot_run_config.py, tests/tui/test_services_run_config.py
- **Verification:** ty clean over all 13 files; both suites re-run green (371 passed).
- **Committed in:** 12e3827 (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (3 blocking)
**Impact on plan:** All three keep the plan's pinned truths intact (FHS safety, ledger discipline, green gates). No scope creep.

## Issues Encountered

- textual 8.2.8: RadioSet has NO `highlighted_child` (it is not a ListView subclass here) — the highlighted RadioButton reads via the `-selected` CSS class, probe-pinned in a standalone Pilot probe before the driver leg was written (initial=head, `down` moves, `enter` toggles).
- A json-kind argv token (`{"a": 2}`) legitimately contains spaces, so the preview line's whitespace-split tokenization breaks it into pieces — the assertion compares pieces in order rather than assuming one token per value.
- The `[r] 恢复高级默认` affordance does not appear in the golden (the footer truncates at width; only `展开高级` renders) — an observed rendering fact, documented in the delta description.
- `make tui` is an interactive app: the display lane ran under `script` (pty) with a 45s timeout kill; exit 124 + zero error hits + rendered nav = the boot proof (the 08-07 lane's substance — composition without ImportError in the tui+gpu env).

## Known Stubs

None — the channel is wired end-to-end (parse → journey → assertion → evidence) and every lane ran for real.

## Auth Gates

None.

## Next Phase Readiness

- Phase 19 is COMPLETE end-to-end: the 18-param surface is pipeline-threaded (19-01), TUI-settable (19-02), and driver-evidenced (19-03), with all lanes green.
- Standing for the maintainer: the D-03 golden review batch (WINDOWS #50 monitor pair + #52 run_config pair, both uncommitted) — the committed tree fails exactly `test_run_config_golden` + `test_run_config_confirm_golden` until adjudicated; the WINDOWS #51 batch-32 OOM re-run decision also remains open.
- The FHS sweep (7/93 at close) and its watcher continue untouched; the final evidence commit is the follow-up when the watcher exits (the quick-261022-tah handoff).

## Self-Check: PASSED

All four committed files exist on disk; commits 5503f5a, 12e3827 verified as ancestors of HEAD (12e3827); `git diff 494887b..HEAD --name-only` = the 4 files above (the goldens deliberately NOT in the commit); zero file deletions across both commits; goldens unstaged on disk (monitor pair byte-identical to pre-task, run_config pair the new batch); pre-existing uncommitted dirt (monitor goldens, .planning phases 13-18, DATA.md, n_audit*, eval_subsets.json, milestone.lock, docs/live/fhs) untouched; no SUMMARY commit made (per dispatch constraints).

---
*Phase: 19-tui-run-config-full-params*
*Completed: 2026-10-24*
