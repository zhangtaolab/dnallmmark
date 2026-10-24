---
phase: 19-tui-run-config-full-params
verified: 2026-10-24T02:14:32Z
status: passed
score: 15/15 must-haves verified
covered_files: [".planning/WINDOWS.md", ".planning/phases/19-tui-run-config-full-params/19-01-PLAN.md", ".planning/phases/19-tui-run-config-full-params/19-01-SUMMARY.md", ".planning/phases/19-tui-run-config-full-params/19-02-PLAN.md", ".planning/phases/19-tui-run-config-full-params/19-02-SUMMARY.md", ".planning/phases/19-tui-run-config-full-params/19-03-PLAN.md", ".planning/phases/19-tui-run-config-full-params/19-03-SUMMARY.md", "pipeline/dispatch_core.py", "pipeline/run_finetune.py", "pipeline/run_sweep.py", "scripts/live/record_tui_live_svg.py", "tests/test_dispatch_core.py", "tests/test_run_finetune_contracts.py", "tests/test_sweep.py", "tests/tui/__snapshots__/run_config.svg", "tests/tui/__snapshots__/run_config_confirm.svg", "tests/tui/test_pilot_run_config.py", "tests/tui/test_services_run_config.py", "tests/tui/test_strings_phase11.py", "tui/screens/run_config.py", "tui/services/run_config.py", "tui/strings.py"]
covered_digest: "v3:sha256:2704963fc2787063a70104734273af9edb4b04f2a0eb89924081adbb13494e6b"
behavior_unverified: 0
overrides_applied: 0
---

# Phase 19: TUI 运行配置全参数化（基础/高级两层）Verification Report

**Phase Goal:** DNALLM 的全部微调参数（TrainingArguments 面）都可作为 TUI 运行配置的任务选项。两层结构：基础参数区 + 高级参数区（18 参数）。每个参数带 YAML 默认值占位/示例；枚举类参数用下拉选择；数值参数做范围校验并提供恢复默认；spec 持久化延续；goldens 与 pilot 测试同步更新；journey driver 参数打字通道同步扩展。
**Verified:** 2026-10-24T02:14:32Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

Goal-backward verdict per ROADMAP goal clause:

| # | Goal clause | Verdict | Evidence |
| - | ----------- | ------- | -------- |
| 1 | All TrainingArguments-surface params settable from TUI run config | **PASS** | 18-row `ADVANCED_TRAIN_FLAGS` (run_sweep.py:407-452) drives the whole chain; screen generates 13 Inputs + 5 ChoiceRows at compose time (tui/screens/run_config.py:1539-1561); EBS rides the pre-existing basic row (`#cfg-input-ebs`); live rehearsal drove the REAL app and threaded `['--learning_rate','0.0001']` + `['--lr_scheduler_type','cosine']` with zero untouched flags |
| 2 | Two-layer structure (basic + advanced 18) | **PASS** | `#cfg-adv-title` 高级参数 section, `#cfg-adv-params` Vertical collapsed by default (`adv_section.display = False`, screen:1562); `[a]` toggle / `[r]` bulk-restore bindings (screen:1284-1285, 2219-2241); basic rows unchanged above it |
| 3 | YAML-default placeholder per param | **PASS** | Every Input `placeholder=S.CFG_ADV_DEFAULT.format(value=row.default_display)` — the "—（默认: {value}）" grammar (screen:1557-1558, strings.py:1568-1569); golden carries the variance hint (`空&#160;=&#160;YAML&#160;默认；变体配置默认不同`) and EBS/GA hint (重算 ×1) |
| 4 | Enum params via dropdown | **PASS** | 5 enum/bool rows (eval/logging/save_strategy, lr_scheduler_type, bf16) render ChoiceRows; `action_pick_choice` generalizes to `_open_advanced_choice_modal` (screen:2277-2307) — RadioSet modal with leading 默认 pseudo-option whose id stays raw vocabulary; modal pick of `cosine` verified in the live rehearsal |
| 5 | Range validation + restore-default | **PASS** | `_parse_bounded_float` with table lo/hi (service:397+), invalid → `PROBLEM_ADVANCED_INVALID` + threads nothing; fresh-recompute semantics: cleared/empty → absent (YAML governs, P19-R5) — service:584-609; `[r]` clears all Inputs + resets ChoiceRows; driver parse refuses `--param learning_rate=99` (exit 2, my run) |
| 6 | spec persistence continues | **PASS** | `params["advanced"] = dict(spec.advanced)` only-when-non-empty (service:699-700); tolerant per-entry re-validation on load, drifted entry → absent never misread (service:896-910, `_advanced_doc_entry`); pre-change doc (no family key) loads empty — pinned by `test_pre_change_doc_advanced_absent_loads_empty` (passed in my full-suite run) |
| 7 | Goldens + pilot tests synced | **PASS** | run_config pair regenerated on disk (differs from HEAD, sha256-proven) and `test_snapshots.py` passes against the working tree (my run); pilot/services/strings suites extended — all green; WINDOWS row #52 ledgers the uncommitted review batch (open 12 / total 51) |
| 8 | Journey driver --param channel | **PASS** | `--param NAME=VALUE` repeatable, table-validated at parse (driver:966-1050), pa6-refused (driver:3110-3111); `_drive_advanced_params` types Inputs + walks the REAL ChoiceModal RadioSet (driver:1081-1141); assertion pair (driver:1971-2002) proven by my rehearsal run |

**Overall: PASS** — the phase goal is achieved in the codebase, not just claimed.

### Observable Truths

Plan must-have truths (19-01: 5, 19-02: 6, 19-03: 4):

| # | Plan | Truth | Status | Evidence |
| - | ---- | ----- | ------ | -------- |
| 1 | 19-01 | `--learning_rate 1e-4` on run_sweep reaches child argv as adjacent pair, one contiguous block AFTER --batch_size BEFORE --cache_dir | ✓ VERIFIED | Source: run_sweep.py:1534-1547; `test_build_argv_full_advanced_block_exact_alphabetical_order` (element-for-element, passed in my 796-test run); live dry-run reproduced the 19-01 tracer gate: manifest cell `sweep_flags.advanced.learning_rate == 0.0001` |
| 2 | 19-01 | Advanced dict replays verbatim under --rerun-failed; pre-change claim replays with ZERO advanced argv elements | ✓ VERIFIED | dispatch_core.py:1726-1754 tolerant per-entry replay filtered to table flags; `test_rerun_replays_full_advanced_dict_verbatim` + `test_rerun_pre_change_claim_replays_advanced_absent` passed |
| 3 | 19-01 | No advanced flags → argv/manifests/claims byte-identical (10-element base argv lock green) | ✓ VERIFIED | `test_build_argv_absent_advanced_adds_zero_elements`, `test_dispatch_no_advanced_launch_records_no_advanced_lane_key`, `test_compose_argv_defaults_exactly_ten_base_elements` all passed; my composer probe printed the defaults argv len == 10; only-when-non-empty writes (run_sweep.py:2356-2357, dispatch_core.py:2413-2414) |
| 4 | 19-01 | run_finetune mutation loop AFTER variant reload + epochs override, BEFORE default_grad_accum snapshot (PD-19-4) | ✓ VERIFIED | Source-read: loop at run_finetune.py:1213-1214 sits between the epochs override (:1194-1195) and the snapshot (:1223); `test_advanced_train_flag_registered_and_mutation_slot_pinned` (source-order regex pin) passed; cadence re-apply (deviation 1) present at :1603-1608 |
| 5 | 19-01 | 18 flags parse at both argparse layers; bounds/json guards refuse; enum garbage refused by choices | ✓ VERIFIED | Registration loops run_sweep.py:750-788, run_finetune.py:372-388; `advanced_flag_problems` (455-499); my driver parse matrix: unknown name / bad enum / out-of-bounds float / pa6+--param each exit 2 |
| 6 | 19-02 | Slot-4 params column renders two layers — basic rows unchanged + collapsed 高级参数 section with all 18 (a toggles, r restores) | ✓ VERIFIED | Screen:1522-1562 + 2219-2241; pilot battery (`test_advanced_section_collapsed_by_default_and_a_toggles`, `test_advanced_reset_clears_every_input_and_base_argv`, row-generation, prefill, SHORT twins) passed |
| 7 | 19-02 | Valid value threads the pair into BOTH composers in the pinned block; invalid renders problem + threads nothing; empty threads nothing | ✓ VERIFIED | My probe: `compose_argv` and `compose_dispatch_argv` both thread `['--learning_rate','0.0001']` before `--cache_dir`, untouched flags absent; `_advanced_argv_elements` shared (service:1420+, called at 1529 and 1620); parser matrix + problem-line pilots passed |
| 8 | 19-02 | Enum params + bf16 pick via ChoiceRow + ChoiceModal RadioSet with leading 默认 option that threads nothing | ✓ VERIFIED | `_open_advanced_choice_modal` builds `("default",) + choices` with the 默认 label rendering `default_display` (screen:2293-2296); raw collection maps pseudo-option → None (screen:1990-1991); modal pilots incl. 13-option scheduler proof passed; live rehearsal picked cosine through the real modal |
| 9 | 19-02 | Every input carries the "—（默认: …）" placeholder; hint names variant variance + GA/EBS interplay | ✓ VERIFIED | `S.CFG_ADV_DEFAULT` grammar on all 13 Inputs; `S.CFG_ADV_HINT` (空=YAML默认；变体配置默认不同) + `S.CFG_ADV_HINT_GA` (设置 effective_batch_size 时 GA 仍由其重算) render in the golden (fragments confirmed in the SVG) |
| 10 | 19-02 | run_config.json persists advanced under one nested params key; pre-change doc loads family absent; drifted loads as absent | ✓ VERIFIED | Service:699-700 + 896-910; `test_persistence_advanced_round_trip_and_only_when_non_empty`, `test_pre_change_doc_advanced_absent_loads_empty`, `test_advanced_drifted_entry_loads_as_absent_never_misread` passed |
| 11 | 19-02 | Defaults spec composes exactly the 10 base argv elements (D-12 lock) | ✓ VERIFIED | My probe: `len(compose_argv(RunSpec(...))) == 10`; lock test passed unmodified |
| 12 | 19-03 | Driver accepts repeated --param, types Inputs + modal-picks enums, [p] assertion REQUIRES typed pairs present + untouched flags absent | ✓ VERIFIED | My full rehearsal: exit 0, `params_typed` recorded, evidence argv carries both adjacent pairs, ZERO untouched table flags, `--num_train_epochs`/`--batch_size` absent (driver:1971-2002 assertion loop) |
| 13 | 19-03 | Evidence runs WITHOUT launching on fresh throwaway roots; FHS sweep never touched | ✓ VERIFIED | My rehearsal: `launched: False`, `mode: full-rehearsal`, all 5 output paths on mktemp roots, 8 stage SVGs (001/002/004/010/011/012/013/014); FHS watcher PID 733194 + dispatch worker alive before/during/after, `docs/live/fhs/` untouched by my runs |
| 14 | 19-03 | run_config goldens regenerated via make snapshot-update ONLY, left UNCOMMITTED; monitor dirt byte-preserved; WINDOWS row records batch | ✓ VERIFIED | On-disk run_config pair differs from HEAD (sha256); `test_snapshots.py` 12/12 pass on-disk → regeneration matches the live render; monitor pair remains the #50 uncommitted dirt; WINDOWS row #52 present, counters open 12 / total 51, last_updated 2026-10-24T01:46:11Z; `make snapshot-update` is the Makefile regen target |
| 15 | 19-03 | Every phase gate green at close | ✓ VERIFIED | Re-run by me: 7-lane pytest 796 passed / 0 failed (exit 0, 153.7s; SUMMARY's 797 = this + test_import_lock.py's 1); ruff over 13 files: All checks passed; ty over 13 files: All checks passed; node --test: 44 pass / 0 fail |

**Score:** 15/15 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `pipeline/run_sweep.py` | ADVANCED_TRAIN_FLAGS 18-row table + argparse loop + guards/collect + argv block + threading | ✓ VERIFIED | Lines 361-525, 750-788, 1534-1547, 2188+; substantive, wired, live-proven |
| `pipeline/dispatch_core.py` | nested advanced lane key ×2, context threading, dry-run mirror, derived rerun tokens | ✓ VERIFIED | 193-203 (derived tokens), 1726-1754 (replay), 1061, 2168-2174, 2353-2357, 2409-2414 |
| `pipeline/run_finetune.py` | local 18-flag tuple + parse loop + PD-19-4 mutation loop + cadence re-apply | ✓ VERIFIED | 76-118, 368-390, 884-903, 1197-1214, 1603-1608 |
| `tui/services/run_config.py` | table-driven parse/persistence/composers, RunSpec.advanced, problem code | ✓ VERIFIED | 189-210, 303, 397+, 570-609, 699-700, 896-910, 1420+, 1529, 1620 |
| `tui/screens/run_config.py` | two-layer column, 13 Inputs + 5 ChoiceRows, a/r bindings, generalized pick | ✓ VERIFIED | 152-179, 1522-1562, 1284-1285, 2219-2307; `Select(` count == 0 (RadioSet idiom held) |
| `tui/strings.py` | CFG_ADV_* block + tripwire extension | ✓ VERIFIED | 1561-1593+; `EXPECTED_CFG_CONSTANTS` tripwire green in my run |
| `scripts/live/record_tui_live_svg.py` | --param channel, typing/picking helpers, assertion pair, evidence meta | ✓ VERIFIED | 966-1141, 1971-2002, 2979-2985, 3110-3118; live-proven by my rehearsal |
| `tests/tui/__snapshots__/run_config{,_confirm}.svg` | regenerated, uncommitted | ✓ VERIFIED | On disk, differ from HEAD, snapshot suite passes against them |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| TUI screen rows | tui/services/run_config.py | `raw[PARAM_ADVANCED]` nested dict → `parse_params` (screen:1982-1993) | ✓ WIRED | Live rehearsal threads typed values end-to-end |
| tui/services/run_config.py | pipeline/run_sweep.py | existing `import run_sweep` — `ADVANCED_TRAIN_FLAGS` single vocabulary | ✓ WIRED | `run_config_service.run_sweep.ADVANCED_TRAIN_FLAGS` in screen loops; parity tests green |
| pipeline/dispatch_core.py | pipeline/run_sweep.py | `import run_sweep` — derived `ADVANCED_LANE_TOKENS`, shared guards/collectors | ✓ WIRED | dispatch_core.py:196-203, 2173-2174; derivation pin test green |
| compose_dispatch_argv | run_sweep_shard/dispatch_core → build_argv | PD-19-2 block mirrored element-for-element | ✓ WIRED | Parity tests both composers + `test_dispatch_dry_run_advanced_parity_with_run_sweep_dry_run` green |
| run_sweep argv | run_finetune config | argparse family + mutation loop | ✓ WIRED | Table parity test (`test_advanced_family_parity_with_run_sweep_table`); dry-run manifest → configs["finetune"] assignment chain source-verified |
| Driver --param | ADVANCED_TRAIN_FLAGS table | imports run_sweep, refuses unknown names at parse | ✓ WIRED | My exit-2 matrix confirmed |

### Data-Flow Trace (Level 4)

learning_rate end-to-end (the dispatch's requested tracer):

`#cfg-input-learning-rate` (Input) → raw `advanced_raw["--learning_rate"]` (screen:1982-1992) → `_parse_bounded_float(text, 1e-9, 1.0)` → `partials["advanced"]["learning_rate"]` (service:584-609) → `RunSpec.advanced` → `params["advanced"]` persistence (699-700) → `_advanced_argv_elements` → `["--learning_rate","0.0001"]` in both composers after `--batch_size` before `--cache_dir` (1529/1620) → dispatch passthrough re-parsed by `parse_sweep_remainder` → `lane_values["advanced"]`/`context["advanced"]` → worker `build_argv(advanced=...)` (dispatch_core:1061) → child argparse → present-only collect (run_finetune:892-903) → `configs["finetune"].learning_rate = 0.0001` at the PD-19-4 slot (1213-1214). **✓ FLOWING** — proven live at every hop (composer probe, dry-run manifest, rehearsal argv).

lr_scheduler_type end-to-end (enum tracer):

ChoiceRow `#cfg-value-lr-scheduler-type` → [enter] → `action_pick_choice` → `_open_advanced_choice_modal` (12-scheduler + 默认 RadioSet) → pick `cosine` → raw `"--lr_scheduler_type": "cosine"` (pseudo-option `default` → None) → enum dispatch (value in row.choices) → composer pair `['--lr_scheduler_type','cosine']` → argparse `choices` at both CLI layers → `configs["finetune"].lr_scheduler_type = "cosine"`. **✓ FLOWING** — the modal pick ran for real in my rehearsal.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| 7-lane phase-close pytest | `uv run --group dev pytest tests/test_sweep.py tests/test_dispatch_core.py tests/test_run_finetune_contracts.py tests/tui/test_services_run_config.py tests/tui/test_pilot_run_config.py tests/tui/test_strings_phase11.py tests/tui/test_snapshots.py -q` | 796 passed, 0 failed, exit 0 (153.7s) | ✓ PASS |
| Live dry-run tracer | `run_sweep.py --seeds 9527 --dry-run --models CrossDNA_519M --tasks BEND__CpG_methylation --learning_rate 0.0001 --output-root <mktemp>` | exit 0; manifest cell `advanced: {"learning_rate": 0.0001}` | ✓ PASS |
| Composer probe | RunSpec(advanced={learning_rate:1e-4, lr_scheduler_type:cosine}, cache_dir, batch_size) | both composers thread both pairs before --cache_dir; zero untouched flags; defaults argv len == 10 | ✓ PASS |
| Driver parse refusals | `--mode pa6 --dry-run --param …` / unknown name / bad enum / lr=99 | all exit 2 | ✓ PASS |
| Driver dry-run lane | `--mode full --dry-run --param learning_rate=0.0001 --param lr_scheduler_type=cosine --param bf16=false` | exit 0 (timeline lane, no app spawn) | ✓ PASS |
| Driver full rehearsal | `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 … --mode full --no-launch --param learning_rate=0.0001 --param lr_scheduler_type=cosine` (all 5 outputs on mktemp) | exit 0, 38.6s; launched=false; params_typed recorded; both adjacent pairs present; ZERO untouched table flags; --num_train_epochs/--batch_size absent; 8 stage SVGs | ✓ PASS |
| ruff / ty (13 files) / node | `uv run ruff check …` / `uv run ty check …` / `node --test tests/js/*.test.js` | All checks passed ×2; 44 pass / 0 fail | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| Journey driver — dry-run lane | `bash`-equivalent: `uv run python scripts/live/record_tui_live_svg.py --mode full --dry-run … --param ×3` | exit 0 | PASS |
| Journey driver — rehearsal lane | `uv run python scripts/live/record_tui_live_svg.py --mode full --no-launch … --param ×2` (runbook env) | exit 0, launched=false | PASS |
| Journey driver — parse-refusal matrix ×4 | see spot-checks | exit 2 each | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| TUI19-full-params | 01+02+03 | umbrella | ✓ SATISFIED | all eight goal clauses PASS (table above) |
| P19-R1 | 19-02 | basic params layer (seeds/epochs/batch_size/workers/gpus/output root) | ✓ SATISFIED | pre-existing rows unchanged above the collapsed section (screen:1448-1620) |
| P19-R2 | 19-01+19-02 | advanced 18-param full chain | ✓ SATISFIED | truths 1-8 |
| P19-R3 | 19-02 | YAML default placeholders | ✓ SATISFIED | truth 9 |
| P19-R4 | 19-02 | enum dropdowns | ✓ SATISFIED | truth 8 |
| P19-R5 | 19-01+19-02 | range validation + restore default | ✓ SATISFIED | truths 5, 7 |
| P19-R6 | 19-02 | spec persistence | ✓ SATISFIED | truth 10 |
| P19-R7 | 19-03 | goldens + pilot tests synced | ✓ SATISFIED | truths 14, 15 |
| P19-R8 | 19-03 | journey driver --param channel | ✓ SATISFIED | truth 12 |

Orphaned requirements: none (REQUIREMENTS.md carries no formal REQ IDs for this phase; P19-R1..R8 derive from 19-RESEARCH.md and every one is claimed by a plan and satisfied).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| tui/strings.py | 424+ | `*_PLACEHOLDER` constant names | ℹ️ Info | Legitimate UI placeholder-string constants from earlier phases, not debt markers |

No TBD/FIXME/XXX anywhere in the seven phase-touched source files. No empty-return stubs found. Deviations in the SUMMARYs (cadence re-apply, exec-namespace widening, fresh-recompute semantics, json.dumps prefill, rehearsal flag adaptation, WINDOWS store reconciliation, ty narrowings) are all documented in-place and code-confirmed.

### Honesty Checks (dispatch focus)

1. **Commits**: all 8 (8f9a8d7, 31734e3, bd545d0, a0f7a03, 8c2a5ca, b9df042, 5503f5a, 12e3827) exist as ancestors of HEAD; `origin/autorun` is 0 ahead / 0 behind — pushed (consistent with the milestone-close push ruling's flip at gates-green). Per-plan `git diff --name-only` over each commit range equals the plan's `files_modified` exactly (19-03's two extra test files = documented deviation 3; goldens deliberately absent from commits).
2. **Snapshot lane**: the dispatch anticipated TWO expected failures in `test_snapshots.py` — they did NOT materialize on the working tree (12/12 passed): the regenerated goldens are ON DISK uncommitted, and the suite compares against disk. I proved the documented committed-tree state instead: both run_config goldens' HEAD sha256 ≠ disk sha256 while the on-disk tests pass ⇒ a fresh checkout of HEAD fails exactly `test_run_config_golden` + `test_run_config_confirm_golden` (plus the pre-existing #50 monitor pair, its own open row). That is the honest expected state as ledgered in WINDOWS #52; nothing is hidden.
3. **FHS sweep untouched**: watcher PID 733194 (`record_tui_live_svg.py --mode full`) and the dispatch worker alive throughout my verification; my evidence runs wrote only to mktemp throwaway roots (cleaned up); `docs/live/fhs/` mtimes show only the sweep's own ongoing writes.
4. **SUMMARY numbers**: 19-01 "401 across three pipeline suites" (180+141+80) and 19-03 "combined 797" (my 796 + import_lock 1) both consistent with my re-run; every named coverage test exists in the claimed file (18/18 existence-checked) and passed.

### Human Verification Required

None generated by this verification. All truths have behavioral evidence (re-run suites + my own probes/rehearsal). The standing D-03 golden review batch (WINDOWS #50 monitor pair + #52 run_config pair, 12 open windows total) remains the maintainer's pending decision — tracked and gated by the project's own windows enforcement, by design of this phase.

### Gaps Summary

No gaps. All 15 plan truths verified with behavioral evidence; all eight ROADMAP goal clauses PASS; all lanes re-run green by this verifier; the uncommitted-goldens state is the planned, ledgered review batch, not a defect.

---

_Verified: 2026-10-24T02:14:32Z_
_Verifier: Claude (gsd-verifier)_
