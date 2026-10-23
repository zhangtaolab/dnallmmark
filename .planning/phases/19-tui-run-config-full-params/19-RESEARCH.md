# Phase 19: TUI 运行配置全参数化（基础/高级两层） - Research

**Researched:** 2026-10-23
**Domain:** TUI run-config service/screen extension + pipeline passthrough-flag chain (run_sweep → dispatch_core → run_finetune → dnallm TrainingConfig → HF TrainingArguments)
**Confidence:** HIGH (every load-bearing fact read from source this session; enum vocabularies probed live against the installed venv)

## Summary

Phase 19 extends the slot-4 run-config screen so the full dnallm `TrainingConfig` surface (the TrainingArguments face) is TUI-settable, in two layers: the existing basic params (seeds / epochs / batch_size / workers / gpus / 输出根 — all already landed) plus a NEW advanced params area (learning_rate, weight_decay, adam_beta1/2, adam_epsilon, max_grad_norm, warmup_ratio, lr_scheduler_type + kwargs, gradient_accumulation_steps, logging/eval/save strategies + steps, bf16, …).

The single most important finding: **every advanced param named in the ROADMAP goal is already a dnallm `TrainingConfig` Pydantic field** [VERIFIED: ../DNALLM/dnallm/configuration/configs.py:270-340], and the sanctioned in-child channel is the existing **quirk-mutation pattern** `configs["finetune"].<field> = value` [VERIFIED: pipeline/run_finetune.py:1090-1091,1247-1256] — NOT the `extra_args` env seam. The env seam (`DNALLMMARK_DATALOADER_WORKERS`) was needed only because `dataloader_num_workers` is *not* a TrainingConfig field; a param that IS a field rides the plain `configs["finetune"].x = v` assignment, and the trainer's `training_args = self.train_config.model_dump()` + `extra_args.update` [VERIFIED: ../DNALLM/dnallm/finetune/trainer.py:574-576] carries it into `TrainingArguments(**training_args)`.

The second key finding: **one param = a 9-surface chain**, and quick-261023-abu (commits 8ea81fa + c9cf047) is the exact, freshest precedent — ~430 changed lines across ~10 files for ONE param whose pipeline flag already existed. Phase 19's params do **not** already have `run_finetune.py` flags (only `--num_train_epochs`, `--effective_batch_size`, `--batch_size` exist today), so each param additionally touches `run_finetune.py` argparse + config mutation + the read-source contract tests. Multiplying ~10-14 advanced params by the full chain demands a **data-driven, batched implementation** (one registry table driving flag creation, parse, validation, argv threading, screen rows, and persistence) rather than 14 hand-copies of the batch_size diff — but the batch_size chain remains the shape to mirror per surface.

**Primary recommendation:** Build the advanced layer as a table-driven param family (a single frozen ADVANCED_PARAMS spec listing flag name / type / bounds / YAML default placeholder / enum vocabulary per param) landing in 3 waves: (1) pipeline chain (run_sweep flags + dispatch_core lanes + run_finetune argparse/config-mutation), (2) TUI service+screen (RunSpec fields, parse_params, persistence, collapsed advanced section with ChoiceModal dropdowns for enums), (3) tests+goldens+driver. Mirror 8ea81fa/c9cf047 surface-for-surface; do NOT expose `per_device_*_batch_size`, `metric_for_best_model`, or the per-dataset-mutated fields; place the `gradient_accumulation_steps` override BEFORE the D-07 snapshot at run_finetune.py:1100.

**No CONTEXT.md exists for this phase** (`.planning/phases/19-tui-run-config-full-params/` holds only `.gitkeep`). The ROADMAP Goal (ROADMAP.md:211) is the authoritative scope; no formal requirement IDs are mapped ("TBD").

<phase_requirements>
## Phase Requirements (derived from the ROADMAP Goal — no formal REQ IDs exist)

| ID | Description (from ROADMAP.md:211 goal text) | Research Support |
|----|---------------------------------------------|------------------|
| P19-R1 | 基础参数区: seeds / epochs / batch_size / workers / gpus / 输出根 — batch_size already landed by quick-261023-abu | Already shipped: all rows exist in tui/screens/run_config.py:1338-1492; this phase only regroups them under the two-layer visual structure |
| P19-R2 | 高级参数区: learning_rate, weight_decay, adam_beta1/2, adam_epsilon, max_grad_norm, warmup_ratio, lr_scheduler_type 及 kwargs, gradient_accumulation_steps, effective_batch_size (exists), logging/eval/save 策略与步长, bf16 等 | All are TrainingConfig fields (dnallm configs.py:270-340) — full param-by-param table in Architecture Patterns below; needs the 9-surface chain per param |
| P19-R3 | 每个参数带 YAML 默认值占位/示例 (placeholder = the active YAML's default) | YAML defaults quoted verbatim below (base + variant configs differ — Pitfall 3); placeholder grammar = CFG_GPUS_DEFAULT / CFG_BATCH_SIZE_DEFAULT precedent |
| P19-R4 | 枚举类参数 (lr_scheduler_type、策略类) 用下拉选择 | ChoiceRow + ChoiceModal (RadioSet) idiom is the in-codebase dropdown [VERIFIED: tui/screens/run_config.py:591-620, 867-900]; enum vocabularies probed live (12 schedulers, 3 strategies) |
| P19-R5 | 数值参数做范围校验并提供恢复默认 | parse_params collect-all + PROBLEM_* vocabulary + "empty field = YAML default governs" = restore-default semantics; needs per-type parsers (_parse_positive_int exists; float/int-range/bool/JSON-dict needed) |
| P19-R6 | spec 持久化延续现有 run-spec state 设计 (会话覆盖、文件默认) | _persist_payload/_spec_from_doc absent-key tolerant-load pattern [VERIFIED: tui/services/run_config.py:578-783]; params ride run_config.json, YAML file remains the "file default" tier |
| P19-R7 | goldens 与 pilot 测试同步更新 | run_config.svg + run_config_confirm.svg join the D-03 uncommitted batch (WINDOWS #50/#51 dirt already open); test_pilot_run_config.py + test_services_run_config.py + test_strings_phase11.py tripwires |
| P19-R8 | journey driver (scripts/live/record_tui_live_svg.py) 参数打字通道同步扩展 | --batch-text idiom [VERIFIED: scripts/live/record_tui_live_svg.py:1703-1768, 2841-2846] — generalize to typed advanced params |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Param value validation (bounds/enums) | TUI service (parse_params collect-all) | run_sweep/dispatch_core CLI mirrors + child (authoritative) | Cheap pre-filters in tui/services/run_config.py; the sys.exit-ing CLI validators are the authorities (Pattern 7, defense in depth) |
| Param → argv threading | TUI service composers (compose_argv/compose_dispatch_argv) | run_sweep build_argv → run_finetune argparse | Present-only D-12 discipline at every hop; the pinned element order lives in the tier-1 suite |
| Param → TrainingArguments | run_finetune config mutation (configs["finetune"].x = v) | dnallm trainer model_dump → TrainingArguments | Quirk-mutation pattern; extra_args env seam only for non-TrainingConfig fields |
| Enum dropdown UI | Screen (ChoiceRow + ChoiceModal RadioSet) | strings.py labels | Existing peft/variant idiom; screens render, never compute |
| Two-layer (基础/高级) layout | Screen compose (collapsed advanced section) | styles.tcss existing classes | display=False idiom (subset input precedent, run_config.py:1381); VerticalScroll column already scrolls |
| Spec persistence | TUI service (run_config.json, atomic) | settings service | Absent-key tolerant load keeps pre-change state files byte-identical |
| Goldens regeneration | tests/tui/test_snapshots.py (--regenerate, maintainer-only) | make snapshot-update | D-03 discipline: regenerate, leave uncommitted for review |
| Journey driver typing channel | scripts/live/record_tui_live_svg.py | — | --batch-text precedent; typed value + argv-preview assertion pair |

## Standard Stack

### Core

No new packages. The entire phase is built on the existing locked stack:

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | 8.2.8 (uv.lock, [tui] group) | ChoiceRow/ChoiceModal/RadioSet/Input widgets | The locked TUI framework; probe-pinned widget facts recorded in STATE.md (Select widget NEVER used in tui/ — see Patterns) |
| transformers | 5.17.0 (installed venv) | The TrainingArguments target surface; enum authorities (SchedulerType, IntervalStrategy) | Probed live this session: 12 schedulers, 3 strategies; warmup_ratio REMOVED from TrainingArguments in v5 |
| dnallm (editable dev clone) | v1.3.3 at /root/autodl-tmp/Github/DNALLM | TrainingConfig Pydantic model (the field surface), DNATrainer model_dump→TrainingArguments | Installed editable into .venv (verified: dnallm.__file__ resolves into the clone); suite repo stays READ-ONLY (Out of Scope table) |
| pytest / pytest-asyncio / pexpect | existing dev group | service unit + Pilot + pty lanes | Unchanged |

### Installation

None. `uv sync --group tui --group dev` already provides everything.

## Package Legitimacy Audit

No external packages are installed or recommended by this phase. **Audit: not applicable — zero new dependencies** (verified: the design adds no imports beyond stdlib + existing locked textual/transformers/dnallm surfaces).

## Architecture Patterns

### The 9-surface param chain (per param) — the batch_size precedent mapped

Every advanced param that must reach training touches ALL of these. batch_size (quick-261023-abu, commits 8ea81fa/c9cf047) is the exact shape; here is the complete census with current line anchors:

```
TUI screen Input/ChoiceRow (#cfg-input-<name>)
  └─ _compose_spec raw dict entry            tui/screens/run_config.py:1788-1801
      └─ parse_params block (parser + PROBLEM_*)   tui/services/run_config.py:405-512
          └─ RunSpec field (+ DEFAULT in _persist_payload / _spec_from_doc
             absent-key tolerant load)         tui/services/run_config.py:262-298, 578-608, 691-783
              ├─ compose_argv append (present-only)  tui/services/run_config.py:1254-1329
              └─ compose_dispatch_argv append        tui/services/run_config.py:1332-1416
                  └─ run_sweep_shard passthrough remainder (FREE — unrecognized
                     tokens forward verbatim; ZERO shard changes)  run_sweep_shard.py:321-344
                      └─ run_sweep: argparse flag + flag_problems mirror (:1779-1853)
                         + sweep_flags dict (:1874-1888) + build_argv/launch_subprocess
                         kwargs (:1162-1293) + run_matrix launch_kwargs partial (:1546-1555)
                          ├─ static workers: remainder verbatim per worker
                          └─ dispatch_core: parse_sweep_remainder re-parse (:2078) +
                             flag_problems mirror (:2103-2145) + lane_values (:2355-2370
                             ordinary, :1719-1730 rerun) + dry-run sweep_flags (:2296-2316)
                             + worker context build_argv call (:1041-1054)
                             + _RERUN_LANE_TOKENS refusal list (:193-198)
                              └─ run_finetune: NEW argparse flag (does NOT exist yet for
                                 advanced params) + configs["finetune"].<field> = value
                                 mutation (the :1090-1091 num_train_epochs slot)
                                  └─ dnallm trainer: model_dump → TrainingArguments
                                     (trainer.py:574-588) — flows automatically because
                                     the field IS a TrainingConfig field
```

Footprint measured from the batch_size commits: 8ea81fa = 227 insertions over 4 files (pipeline chain only); c9cf047 = 204 insertions over 6 files (TUI chain); plus run_finetune-side flags + goldens commits. Phase 19 needs the run_finetune leg too (batch_size's already existed).

### The TrainingConfig field surface — verbatim quote [VERIFIED: ../DNALLM/dnallm/configuration/configs.py:270-340]

```python
class TrainingConfig(BaseModel):
    _VALID_REPORT_TO: set[str] = {"tensorboard", "wandb", "none", "all"}
    output_dir: str | None = None
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 8
    per_device_eval_batch_size: int = 16
    gradient_accumulation_steps: int = 1
    max_steps: int | None = -1
    logging_strategy: str = "steps"
    logging_steps: int = 100
    eval_strategy: str = "steps"
    eval_steps: int = 100
    save_strategy: str = "steps"
    save_steps: int = 500
    save_total_limit: int = 20
    save_safetensors: bool = True
    learning_rate: float = 5e-5
    weight_decay: float = 0.01
    adam_beta1: float = 0.9
    adam_beta2: float = 0.999
    adam_epsilon: float = 1e-8
    max_grad_norm: float = Field(default=1.0, ge=0)
    warmup_ratio: float = 0.1
    lr_scheduler_type: str = "linear"
    lr_scheduler_kwargs: dict | None = None
    seed: int = 42
    bf16: bool = False
    fp16: bool = False
    gradient_checkpointing: bool = False
    load_best_model_at_end: bool = False
    metric_for_best_model: str = "eval_loss"
    report_to: list[str] = Field(default_factory=lambda: ["tensorboard"], ...)
    resume_from_checkpoint: str | None = None
```

Every ROADMAP-goal advanced param is in this list. Non-TrainingArguments fields POPPED before the ctor [VERIFIED: ../DNALLM/dnallm/finetune/trainer.py:577-588, quoted]: `training_args.pop("callbacks", None)`, `training_args.pop("hyperparameter_search", None)`, `training_args.pop("use_qlora", None)`, `training_args.pop("use_ia3", None)`, `training_args.pop("peft_dry_run", None)`, `training_args.pop("allow_test_as_eval", None)`, `training_args.pop("quantization_config", None)`, plus `self._save_safetensors = training_args.pop("save_safetensors", True)` and `self._warmup_ratio = training_args.pop("warmup_ratio", None)`.

### The two channels into TrainingArguments — which to use per param

1. **TrainingConfig field (the phase-19 case):** `configs["finetune"].<field> = value` in run_finetune.py, placed in the per-model override slot AFTER the variant reload (the num_train_epochs precedent, :1082-1091) or per-dataset where semantics demand. The trainer's model_dump carries it. This is the sanctioned channel — precedents verbatim [VERIFIED: pipeline/run_finetune.py:1090-1091]:
   ```python
   if num_train_epochs is not None:
       configs["finetune"].num_train_epochs = num_train_epochs
   ```
2. **extra_args env seam (NOT needed here):** for fields TrainingConfig lacks (dataloader_num_workers). run_finetune.py:1602-1611 builds `extra_args` and the ctor takes `extra_args=extra_args or None`; trainer.py:575-576 `training_args.update(self.extra_args)` — extra_args OVERRIDE config values. Phase-19 params should NOT use this channel.

### The enum vocabularies — live-probed against .venv transformers 5.17.0 [VERIFIED: python -I probe of transformers.trainer_utils, 2026-10-23]

- `SchedulerType`: `['linear', 'cosine', 'cosine_with_restarts', 'polynomial', 'constant', 'constant_with_warmup', 'inverse_sqrt', 'reduce_lr_on_plateau', 'cosine_with_min_lr', 'cosine_warmup_with_min_lr', 'warmup_stable_decay', 'greedy']` (12 values)
- `IntervalStrategy` (logging_strategy / eval_strategy / save_strategy): `['no', 'steps', 'epoch']` (3 values)
- TrainingArguments in v5: `lr_scheduler_kwargs` IS a field; `warmup_ratio` is NOT (removed in v5 — dnallm converts: trainer.py:661-672 `warmup_steps = int(self._warmup_ratio * num_training_steps)`); `adam_beta1/2`, `weight_decay`, `max_grad_norm`, `learning_rate` ARE fields.

### YAML default placeholders — the honest values [VERIFIED: pipeline/finetune_config.yaml:19-58]

Base config `finetune:` section defaults (these become the TUI placeholders): `num_train_epochs: 3`, `per_device_train_batch_size: 8`, `per_device_eval_batch_size: 8`, `gradient_accumulation_steps: 1`, `max_steps: -1`, `logging_strategy: "steps"`, `logging_steps: 500`, `eval_strategy: "steps"`, `eval_steps: 500`, `save_strategy: "steps"`, `save_steps: 500`, `save_total_limit: 2`, `learning_rate: 2e-5`, `weight_decay: 0.01`, `adam_beta1: 0.9`, `adam_beta2: 0.999`, `adam_epsilon: 1e-8`, `max_grad_norm: 1.0`, `warmup_ratio: 0.1`, `lr_scheduler_type: "linear"`, `lr_scheduler_kwargs: {}`, `seed: 42`, `bf16: True`, `fp16: False`, `load_best_model_at_end: True`, `metric_for_best_model: "eval_loss"`, `report_to: "tensorboard"`.

**Variant configs differ** (see Pitfall 3): with_head/probe set `logging_steps: 100`, `eval_steps: 100`, `save_steps: 200`, `save_total_limit: 20`, per-device batch 48, `bf16: False`; curve sets `logging_steps: 50`, `eval_steps: 100`, `save_steps: 100`, `save_total_limit: 2`, `bf16: True` [VERIFIED: pipeline/finetune_config_{with_head,probe,curve}.yaml finetune: sections].

### The dropdown idiom — ChoiceRow + ChoiceModal (NOT textual Select)

There is ZERO `Select`/`OptionList` usage in tui/ today [VERIFIED: grep over tui/, only PickerList(SelectionList) and ChoiceRow]. The enum dropdown idiom is [VERIFIED: tui/screens/run_config.py:591-620, 867-900]:

```python
class ChoiceRow(Static, can_focus=True):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "pick_choice", show=False), ...]
    def action_pick_choice(self) -> None:
        handler = getattr(self.screen, "action_pick_choice", None)
        ...

class ChoiceModal(_PickerReturnModal):
    def compose(self) -> ComposeResult:
        with Vertical(id="cfg-choice-box", classes="modal-box"):
            yield RadioSet(*[
                RadioButton(option, option == self._current, id=option)
                for option in self._options])
            yield Footer()
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        value = str(event.pressed.id or "")
        self.dismiss()
        self._on_pick(value)
```

"First toggle applies and closes (k9s-quick)". Reuse this verbatim for lr_scheduler_type + the three strategy params. Caveat: RadioButton `id=option` — ids must be valid Textual ids (the 12 scheduler names are; verify at implementation). A 12-option RadioSet fits the modal fine.

### The two-layer screen structure

The params column (`#cfg-params-col`, a VerticalScroll — it already scrolls) currently renders: seeds → PEFT → Variant → Curve → Fair-subset → epochs → EBS → batch_size → [多 GPU 调度 title] workers → gpus → [结果目录 title] 5 dir rows [VERIFIED: tui/screens/run_config.py:1336-1492]. Pattern for the advanced area:

- Section title in the `cfg-section-title` class (the CFG_MGPU_TITLE / CFG_DIRS_TITLE mechanism, :1418/:1436)
- Rows hidden by default via the `display = False` idiom (the subset input precedent, :1381) — one [a]-style toggle binding flipping the whole block, or a Checkbox (the fair-subset toggle precedent, :1374)
- Each row: `Horizontal(classes="cfg-param-row")` + `Label(cfg-param-label)` + `Input(compact=True, placeholder=<YAML default>)` — the compact=True Rule-1 discipline applies to EVERY new Input (12-03: default height-3 Input clips invisible in height-1 rows)
- Existing CSS classes only where possible; a `.cfg-adv-section` collapse affordance may need one new class — plan for minimal styles.tcss additions

### Restore-default semantics

The existing discipline already IS restore-default: an EMPTY field contributes no partial → RunSpec default (None) → no flag threaded → the YAML governs. The goal's 恢复默认 lands as (a) the empty-field-is-default placeholder communication and (b) a bulk "clear advanced fields" action — the [s] save-defaults family (CFG_SAVE_DEFAULTS_*) and the CFG_SAVE_DEFAULTS_HINT line ("恢复默认：删除配置文件或清空各目录后保存") are the copy precedents. Per-field restore = clearing the input; the planner should decide bulk-clear binding vs per-field only (the goal says 提供恢复默认 — a bulk advanced-reset action is the cheapest honest reading).

### Spec persistence (session-overrides-file continuation)

`_persist_payload` writes `params: {seeds, peft, config_variant, curve_fractions, subset_file, num_train_epochs, effective_batch_size, batch_size, workers, gpus}` [VERIFIED: tui/services/run_config.py:585-608]. New advanced params join this dict; `_spec_from_doc` reads each with the **absent-key = default** pattern (the batch_size precedent at :718-722 — a pre-change document loads byte-identically) and present-but-drifted = whole-default-policy reset. `SCHEMA_VERSION` stays 1 (additive keys, the workers/gpus precedent — no schema bump was needed for batch_size either).

### Persistence example — the absent-key tolerant load, verbatim [VERIFIED: tui/services/run_config.py:718-725]

```python
    # 261023-abu: the absent-key path — a pre-change document (no
    # batch_size key) loads None (byte-identical launches); a
    # present-but-drifted value is whole-default-policy drift.
    ok_batch, batch = _optional_int_at_least_one(
        params.get("batch_size"))
```

### System Architecture Diagram (param data flow)

```
operator types/selects value (slot-4 advanced row)
        │ Input/ChoiceRow → _compose_spec raw dict
        ▼
parse_params (collect-all: type/bounds/enum mirrors → partials | PROBLEM_*)
        │ invalid → problem tuples → preview line/modal (generic fallback)
        ▼
RunSpec field (None = YAML governs) ──→ save_state (run_config.json, atomic)
        │
        ├─ preview / gate chain (UNCHANGED: E2' reads models/tasks/seeds only)
        ▼
compose_dispatch_argv (present-only, pinned tail order)
        ▼
run_sweep_shard --mode dispatch (passthrough remainder — zero shard changes)
        ▼
dispatch_core: re-parse → lane_values → claim JSON (replay feed)
        → worker build_argv → run_finetune child argv
        ▼
run_finetune argparse → configs["finetune"].<field> = value (after variant reload)
        ▼
dnallm DNATrainer → train_config.model_dump() → TrainingArguments(**…) → training
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Enum dropdown in TUI | textual `Select` widget (unprobed in this codebase, 8.2.8 widget-seam risk) | ChoiceRow + ChoiceModal RadioSet idiom | Three probe-pinned 8.2.8 widget traps are already recorded in STATE.md; the ChoiceModal is Pilot-proven on this exact screen |
| Scheduler/strategy vocabularies | Hardcode a guessed scheduler list | Probe-pinned lists above (12 SchedulerType / 3 IntervalStrategy values from transformers 5.17.0) | transformers v5 renamed/added entries (greedy, warmup_stable_decay); training-data lists are stale |
| Param validation | Per-param bespoke validators in the screen | parse_params collect-all machine problems in the service tier | The screens-render-never-compute law (D-07); the CLI mirrors + child stay authorities |
| Claim-lane replay fidelity | New replay mechanism | Extend lane_values + tolerant `.get()` replay | The 14-03 absent-parity design already handles additive lane keys (a pre-change claim lacking a key replays with the flag absent) |
| Passthrough threading through the shard | Touch run_sweep_shard.py | The parse_known_args remainder | Unrecognized tokens forward VERBATIM to every worker (shard owns only 5+mode flags) — zero shard changes, proven by 8ea81fa |

**Key insight:** The architecture already anticipates this phase — the passthrough remainder, the additive lane dicts, the absent-key persistence, and the quirk-mutation slot all exist precisely so new params are additive. The work is disciplined replication, not design.

## Common Pitfalls

### Pitfall 1: gradient_accumulation_steps conflicts with the child's per-dataset GA arithmetic
**What goes wrong:** The child RESETS `configs["finetune"].gradient_accumulation_steps = default_grad_accum` per dataset (D-07, run_finetune.py:1100-1112) and then OVERRIDES it under `--effective_batch_size` (`required_grad_accum = max(1, effective_batch_size // bs_new)`, :1435-1444) or the WR-04 tier-compensation path (:1445-1459). A TUI GA override placed in the dataset loop would be clobbered; placed naively at the model level it would be reset per dataset.
**How to avoid:** A threaded GA must become the SNAPSHOT BASE — set `configs["finetune"].gradient_accumulation_steps = override` BEFORE the `default_grad_accum = configs["finetune"].gradient_accumulation_steps` snapshot at :1100, so every per-dataset reset restores the operator's value. Document that `--effective_batch_size` still recomputes GA from the effective target (EBS wins when both set — the existing child semantics; surface this in the TUI hint copy). Alternatively the planner may DESCOPE GA from the TUI (it is listed in the goal, so prefer the snapshot-base fix).
**Warning signs:** a run where EBS is unset but GA silently reverts to the YAML value.

### Pitfall 2: warmup_ratio must ride TrainingConfig, never TrainingArguments-shaped channels
**What goes wrong:** transformers v5 REMOVED `warmup_ratio` from TrainingArguments (verified: `'warmup_ratio' in TrainingArguments.__dataclass_fields__` → False). Threading it via extra_args would crash the ctor with an unexpected-kwarg TypeError.
**How to avoid:** `configs["finetune"].warmup_ratio = value` only — dnallm's trainer pops it and converts to `warmup_steps` after the dataset size is known [VERIFIED: ../DNALLM/dnallm/finetune/trainer.py:586-588,661-672]. Range (0,1] mirrors the curve-fractions bound style.

### Pitfall 3: variant YAMLs carry DIFFERENT advanced defaults — placeholder honesty
**What goes wrong:** A placeholder "500" for logging_steps is wrong under head/probe variants (100) or curve (50); batch 8 vs 48; bf16 True vs False. The goal explicitly asks for YAML 默认值占位 per param.
**How to avoid:** Placeholders state the BASE config's default and the hint copy names the variance ("默认 500（变体配置不同）" style), OR the placeholder derives dynamically from the active `config_variant` field. Simplest honest form: static base-config placeholder + one dim hint line for the advanced section noting variant configs differ. Decide in plan; do not silently show a wrong "default".

### Pitfall 4: bf16/fp16 interplay with the fp32-only quirk list
**What goes wrong:** `models_only_support_fp32` forces `configs["finetune"].fp16 = False; configs["finetune"].bf16 = False` INSIDE the dataset loop (run_finetune.py:1242-1249) — AFTER any model-level TUI override.
**How to avoid:** This precedence is CORRECT (memory-safety quirk beats operator preference) — keep the TUI bf16 override at the model-level slot and document that fp32-only models ignore it. Do not "fix" the quirk block.

### Pitfall 5: per-dataset mutated fields must NOT be exposed
**What goes wrong:** `per_device_train_batch_size` / `per_device_eval_batch_size` are set per dataset by the tier-cap + VRAM estimators (:1419-1420); `metric_for_best_model` is set from the registry row (:1399). Exposing them in the TUI invites silently-clobbered settings and confusion with the two EXISTING batch knobs (batch_size = starting micro-batch scaled by determine_batch_size's cap ladder :602-644; effective_batch_size = GA-derived target).
**How to avoid:** Expose exactly the goal's list; the per-device batch story is already fully covered by batch_size + EBS (documented "never conflated" in three places).

### Pitfall 6: lr_scheduler_kwargs is a dict — needs a JSON-typed channel
**What goes wrong:** A plain int/float parser cannot express `{"num_restarts": 2}`.
**How to avoid:** Input accepting a JSON object literal, parsed with json.loads + isinstance(dict) collect-all validation (a `_parse_json_object` helper; the subset-file JSON validation idiom). Empty = `{}`/None = YAML governs. The YAML's own comment block (finetune_config.yaml:44-51) documents the per-scheduler kwargs examples — mirror them in the hint copy. Type discipline: values inside the dict pass through to TrainingArguments verbatim (the child/transformers validates).

### Pitfall 7: one flag, NINE pinned surfaces — drift between them
**What goes wrong:** A param added to run_sweep argparse but missing from dispatch_core's lane_values replays incorrectly on --rerun-failed; missing from `_RERUN_LANE_TOKENS` allows blended-lane re-runs; missing from the dry-run sweep_flags hides it from the manifest; missing from run_finetune argparse makes the child die on the unknown flag (argparse exits 2 — one burned cell per claim).
**How to avoid:** Per-param checklist in every plan task: (1) run_sweep argparse+flag_problems+sweep_flags+build_argv/launch_subprocess+run_matrix partial, (2) dispatch_core mirror+lane_values(×2)+context+dry-run+_RERUN_LANE_TOKENS, (3) run_finetune argparse+config mutation, (4) TUI PARAM_*/parser/RunSpec/persistence(×2)/composers(×2), (5) strings, (6) screen row+prefill+raw entry, (7) tests ×4 files, (8) goldens, (9) driver channel. The argv tail position for the new advanced flags must be pinned ONCE (suggest: a contiguous advanced block after `--batch_size`, before `--cache_dir`) and pinned element-for-element in test_services_run_config.py (the test_compose_argv_full_spec_element_for_element shape).

### Pitfall 8: golden regeneration discipline + pre-existing dirt
**What goes wrong:** run_config.svg / run_config_confirm.svg WILL change (new rows). The monitor goldens already carry uncommitted dirt (WINDOWS #50/#51, git-diff confirmed this session: monitor_empty.svg 192 lines, monitor_running.svg 218 lines changed).
**How to avoid:** Regenerate via `make snapshot-update` ONLY (the D-03 maintainer-review gate; `pytest --snapshot-update` does nothing — no plugin). Leave ALL regenerated goldens uncommitted as one review batch; open/extend the WINDOWS ledger row; never commit regenerated SVGs with the feature code.

### Pitfall 9: strings tripwire + i18n locks
**What goes wrong:** Every new CFG_* constant must join EXPECTED_CFG_CONSTANTS in tests/tui/test_strings_phase11.py:37-80 in the SAME change or the bidirectional inventory test fails; zh copy must follow the approved terminology table (injectivity both directions); the SERVICE tier must stay zero-Chinese (WR-05 lock, test_import_lock.py glob).
**How to avoid:** One strings.py + one tripwire edit per batch of constants (the "one block, one tripwire edit" precedent). Long labels: the narrow-mode shortening mechanism (`_NARROW_WIDTH = 100`, `_apply_width_mode`, run_config.py:1891-1907) needs a SHORT twin per long label — `gradient_accumulation_steps` (27 chars) will need one (the CFG_FIELD_EBS_SHORT precedent "eff_batch_size").

### Pitfall 10: E2'/gate chain interplay — verify NO gate changes
**What goes wrong:** Assuming advanced params join the launch gate or the E2' typed-phrase computation.
**How to avoid:** `is_full_e2x` reads models/tasks/seeds ONLY (service docstring D-02/D-07); the gate chain (env gate → problems → confirm → E2') is unchanged by param values. The ONLY new gate-visible surface is preview problems (parse mirrors) and the [p] argv preview (new flags visible). Keep it that way — the goal says nothing about gate changes.

### Pitfall 11: in-flight FHS sweep — read-only research now, live evidence later
**What goes wrong:** The 93-cell FungiHelixSeek sweep (quick-261022-tah) and its watcher are running detached on this box; a phase-19 launch test on the same root/GPUs would interfere.
**How to avoid:** All CI-safe lanes (pytest/tui, lint, typecheck) are CPU-only and safe. Any live TUI journey/pilot-with-real-backend evidence must use a FRESH throwaway root (the fresh-root discipline, STATE.md 15-01) and avoid GPU contention; coordinate with the maintainer for live evidence timing (the goal's driver extension evidence can run --dry-run / preview-only).

### Pitfall 12: seed field collision (TrainingConfig.seed vs RunSpec.seeds)
**What goes wrong:** TrainingConfig has `seed: int = 42` — exposing it as an advanced param would create TWO seed knobs (the sweep's per-cell `--seed` already threads from RunSpec.seeds and the child sets torch/np seeds from it).
**How to avoid:** Do NOT expose `seed` in the advanced area; the YAML `seed: 42` is effectively dead under sweep launches (the child's --seed governs). Same for `output_dir` (composed per cell), `resume_from_checkpoint` (marker-driven), `report_to`/`load_best_model_at_end`/`metric_for_best_model` (suite/registry-driven or out of goal scope), `max_steps` (epochs-or-steps confusion; goal doesn't list it — descope unless maintainer adds it).

## Code Examples

### The parse_params block shape (batch_size verbatim) [VERIFIED: tui/services/run_config.py:467-478]

```python
    raw_batch = _clean_str(raw.get(PARAM_BATCH_SIZE))
    if raw_batch is not None:
        batch = _parse_positive_int(raw_batch)
        if batch is None:
            problems.append(
                (PROBLEM_BATCH_SIZE_INVALID, raw.get(PARAM_BATCH_SIZE)))
        else:
            partials["batch_size"] = batch
```

New parsers needed: `_parse_positive_float(value, lo, hi)` (learning_rate (0,~1], weight_decay [0,1), adam_beta1/2 (0,1), adam_epsilon (0,1), max_grad_norm [0,∞), warmup_ratio (0,1]), `_parse_bool` (bf16 — or a ChoiceRow none/on/off… decide: the goal lists bf16 as a param; an Input accepting true/false is the low-friction shape, a 2-3 option ChoiceRow is the enum-consistent shape), `_parse_json_object` (lr_scheduler_kwargs). Each mirrors an existing bound style; a table-driven `parse_params` extension (loop over a frozen param spec) beats 14 copies.

### The screen row shape (batch_size verbatim) [VERIFIED: tui/screens/run_config.py:1401-1408]

```python
                with Horizontal(classes="cfg-param-row"):
                    yield Label(S.CFG_FIELD_BATCH_SIZE,
                                id="cfg-label-batch-size",
                                classes="cfg-param-label")
                    yield Input(
                        value="", placeholder=S.CFG_BATCH_SIZE_DEFAULT,
                        id="cfg-input-batch-size",
                        classes="cfg-param-input", compact=True)
```

### The run_sweep flag + guard shape [VERIFIED: pipeline/run_sweep.py:466-478, 1785-1791]

```python
    parser.add_argument(
        "--batch_size",
        type=int,
        default=None,
        help="Starting per-device batch size threaded to every child as "
             "--batch_size <N> ... (261023-abu; plain valued flag, the "
             "--num_train_epochs shape — no bare-flag const semantics)"
    )
```
```python
    if args.batch_size is not None and args.batch_size < 1:
        flag_problems.append(
            f"--batch_size must be >= 1, got {args.batch_size}"
        )
```

### The lane_values shape [VERIFIED: pipeline/dispatch_core.py:2355-2370]

```python
    lane_values = {
        "peft": sweep_args.peft,
        "config_variant": config_variant,
        "subset_file": subset_file_abs,
        "effective_batch_size": sweep_args.effective_batch_size,
        "batch_size": sweep_args.batch_size,
        "num_train_epochs": sweep_args.num_train_epochs,
        "cache_dir": cache_dir_abs,
        "model_root": model_root_abs,
        "dataset_root": dataset_root_abs,
        "log_dir": log_dir_abs,
    }
```

### The journey driver typed-param channel [VERIFIED: scripts/live/record_tui_live_svg.py:1706-1708, 1756-1762]

```python
    if ctx.args.batch_text:
        await _type_into(pilot, screen, "#cfg-input-batch-size",
                         ctx.args.batch_text)
```
```python
        if "--batch_size" not in tokens or ctx.args.batch_text not in (
                tokens[tokens.index("--batch_size") + 1:
                       tokens.index("--batch_size") + 2]):
            raise AssertionError(
                f"dispatch argv preview missing --batch_size "
                f"{ctx.args.batch_text} (the batch input was typed): "
```

Generalize as a repeated `--param <name>=<value>` typed channel or a small set of named flags; the assertion pair (typed ⇒ flag present with value; untouched ⇒ flag absent) is the discipline.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| warmup_ratio as a TrainingArguments field | Removed in transformers v5; dnallm converts to warmup_steps post-dataset-sizing | transformers 5.x (installed 5.17.0) | Must ride TrainingConfig only (Pitfall 2) |
| Scheduler enum ~8 values | 12 values incl. greedy, warmup_stable_decay, cosine_with_min_lr | transformers 5.17 | Dropdown vocabulary from the live probe, not memory |
| TUI params: 8 hand-built rows | batch_size chain precedent (8ea81fa/c9cf047) table-ready | 2026-10-23 | The ADVANCED_PARAMS table approach is the natural generalization |

**Deprecated/outdated:** none in-repo; do not pattern-match `--effective_batch_size`'s bare-flag `nargs='?' const=16` semantics for new flags (explicitly avoided for batch_size — "plain valued flag, the --num_train_epochs shape").

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The ROADMAP "等" (etc.) in the advanced list is bounded to the TrainingConfig surface quoted above minus the do-not-expose set (Pitfall 12); final param list confirmed at discuss/plan | P19-R2 | Scope creep or missing param — planner should lock the exact param table as decision #1 |
| A2 | A table-driven implementation (one frozen param-spec structure driving all surfaces) is acceptable within the "surgical fixes" constraint (it replaces N hand-copies, each of which would be bigger) | Primary recommendation | If maintainer prefers literal per-param replication of the batch_size diff, plan gains ~2x task size but no design change |
| A3 | Advanced section collapsed-by-default with a single toggle binding satisfies 两层结构 (no separate screen/mode) | Two-layer pattern | If maintainer wants a separate advanced screen, screen work roughly doubles |
| A4 | bf16 enters as an Input (true/false) or small ChoiceRow — enum-consistent ChoiceRow preferred | P19-R5 | Minor UI shape only |
| A5 | No dispatch_state.json / schema changes needed (lane keys are additive claim-JSON content, not state schema) | Chain | schemas/dispatch_state.json untouched — verified the lane dict rides claim JSONs, not the state schema |
| A6 | The DNALLM dev clone at ../DNALLM (v1.3.3, editable-installed) remains the installed suite for the phase's live runs; suite repo stays read-only | Environment | If the venv's dnallm differs at execution time, TrainingConfig field surface must be re-probed |

## Open Questions

1. **Exact advanced param list** — the goal names ~11 + "等". Recommended list (all TrainingConfig fields, YAML-default-placeholderable, no child-side clobber): learning_rate, weight_decay, adam_beta1, adam_beta2, adam_epsilon, max_grad_norm, warmup_ratio, lr_scheduler_type (dropdown), lr_scheduler_kwargs (JSON), gradient_accumulation_steps (Pitfall 1 placement), logging_strategy/eval_strategy/save_strategy (dropdowns), logging_steps/eval_steps/save_steps, save_total_limit, bf16. Excluded per Pitfall 12: seed, per_device_*_batch_size, metric_for_best_model, output_dir, resume_from_checkpoint, max_steps, report_to, load_best_model_at_end. - Recommendation: lock this table in the plan's first decision; it drives everything.
2. **Advanced argv tail position** — suggest one contiguous advanced block after `--batch_size` and before `--cache_dir` in the pinned order; must be pinned once. - Recommendation: alphabetical within the advanced block for determinism.
3. **Placeholder vs variant-defaults honesty (Pitfall 3)** — static base placeholder + variance hint, or dynamic per-variant placeholder. - Recommendation: static + hint (fewer moving parts; variant lane users are advanced operators).
4. **Does GA stay in scope** given Pitfall 1's snapshot-base subtlety? - Recommendation: keep it (goal lists it) with the snapshot-base fix + a hint that EBS recomputes GA.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| .venv (uv-managed, data+tui+dev groups) | all test/lint lanes | ✓ | Python 3.13, locked | — |
| transformers | TrainingArguments surface + enum probes | ✓ | 5.17.0 | — |
| dnallm (editable) | TrainingConfig source of truth | ✓ | v1.3.3 = ../DNALLM HEAD (da4f8ba) | re-probe fields if reinstalled |
| textual | TUI screen/test lanes | ✓ | 8.2.8 (uv.lock) | — |
| GPU (2× RTX 5090) | live journey evidence ONLY | ✓ but IN FLIGHT (FHS sweep + watcher detached) | — | --dry-run / preview-only driver evidence; coordinate timing with maintainer |
| make snapshot-update | golden regeneration | ✓ | maintainer-only path | — |

**Missing dependencies with fallback:** none blocking. **Missing, blocking:** none.

## Security Domain

security_enforcement enabled (config), ASVS level 1, block-on high. This phase adds no network surface, no secrets, no new trust boundaries.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | The existing collect-all parse_params tier: type parsers + bounds mirrors + enum vocabularies; every value passes through argparse (type=int/float/choices) at the child; JSON-typed lr_scheduler_kwargs parsed with json.loads + dict shape check (never eval) |
| V2/V3/V4/V6 | no | No auth/session/crypto surface (local operator console) |

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious lr_scheduler_kwargs JSON | Tampering | json.loads + isinstance(dict) only; values flow into TrainingArguments which type-checks kwargs per scheduler; never exec/eval |
| Argue-the-argv injection | Tampering | LIST argv discipline everywhere (never shell strings, D-06) — unchanged |
| State-file tampering (run_config.json) | Tampering | Tolerant load: ANY drift → whole-default spec (never a partially-misread one) — existing control covers new keys |

## Sources

### Primary (HIGH confidence — read this session)
- tui/services/run_config.py (whole file structure: PARAM_*/PROBLEM_* :148-198, RunSpec :205-298, parse_params :405-512, persistence :567-857, composers :1254-1460)
- tui/screens/run_config.py (compose :1317-1498, ChoiceRow/ChoiceModal :591-620/:867-900, _compose_spec :1783-1820, _problem_line :412-453, _apply_width_mode :1891-1907)
- tui/strings.py CFG_ block (:1311-1530) + tests/tui/test_strings_phase11.py inventory (:33-80)
- pipeline/run_sweep.py (argparse :340-553, build_argv :1162-1293, run_matrix :1473-1555, main flag_problems/sweep_flags :1677-1888)
- pipeline/run_finetune.py (argparse :77-324, variant reload + epochs override :1063-1100, grad-accum snapshot/reset :1093-1112, quirk mutations :1242-1275, batch sizing + GA arithmetic :1373-1462, extra_args env seam :1601-1627)
- pipeline/dispatch_core.py (_RERUN_LANE_TOKENS :192-198, claim payload :536-574, worker build_argv :1041-1054, rerun lane_values :1719-1730, ordinary lane_values :2355-2370, flag mirrors :2103-2145, dry-run sweep_flags :2296-2316)
- pipeline/run_sweep_shard.py (parse_args passthrough contract :321-344)
- pipeline/finetune_config.yaml + 3 variant YAMLs (finetune: sections verbatim)
- ../DNALLM/dnallm/configuration/configs.py:270-340 (TrainingConfig verbatim) + dnallm/finetune/trainer.py:574-588,661-672 (model_dump/pops/warmup conversion)
- Live probes (2026-10-23, .venv): transformers 5.17.0 SchedulerType (12 values), IntervalStrategy (3 values), field-presence checks (warmup_ratio absent, lr_scheduler_kwargs/adam_beta1 present); dnallm editable install resolves to ../DNALLM
- Quick-261023-abu commits 8ea81fa / c9cf047 / dfbbfae (footprint measurement); git diff of tests/tui/__snapshots__ (WINDOWS #50/#51 dirt confirmed)
- Tests: test_services_run_config.py (124 tests), test_pilot_run_config.py (109, batch pilot :875-919), test_snapshots.py (golden discipline), test_dispatch_core.py (92), test_sweep.py (117), test_run_finetune_contracts.py (read-source-never-import pattern)

### Secondary
- .planning/STATE.md (decisions log, 261023-abu entries), .planning/ROADMAP.md:209-217 (phase 19 goal), .planning/REQUIREMENTS.md (v1.3 context; no phase-19 REQ IDs)

## Metadata

**Confidence breakdown:**
- Param chain architecture: HIGH — every surface read with line anchors; the batch_size precedent measured commit-by-commit
- TrainingConfig/trainer flow: HIGH — suite source read + live import probe of the editable install
- Enum vocabularies: HIGH — probed against the installed transformers 5.17.0 this session
- Screen two-layer UX shape: MEDIUM — the building blocks (section titles, display-toggle, scroll column) are verified; the exact collapse interaction is a plan decision (A3)
- Scope of "等": LOW-MEDIUM — bounded by analysis (A1), needs plan-time lock

**Research date:** 2026-10-23
**Valid until:** 2026-11-22 (stable repo; re-probe enum lists if transformers/dnallm versions move)
