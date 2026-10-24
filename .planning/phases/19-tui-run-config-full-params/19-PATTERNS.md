# Phase 19: TUI 运行配置全参数化（基础/高级两层） - Pattern Map

**Mapped:** 2026-10-23
**Files analyzed:** 12 (all modified; no new source files — tests/goldens are edits to existing)
**Analogs found:** 12 / 12 (every surface has a batch_size / 261023-abu or Phase-16 precedent)

The master precedent is **quick-261023-abu (commits 8ea81fa + c9cf047)** — the batch_size
9-surface chain. RESEARCH.md §"9-surface param chain" (lines 74-99) is the authoritative map;
this file gives the per-surface analog + excerpt to copy. The dnallm suite (`../DNALLM/`) is
READ-ONLY — never an edit target.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pipeline/run_finetune.py` | CLI entry (argparse + config mutation) | batch transform | `--num_train_epochs` slot (:1082-1091) + batch_size flag | exact |
| `pipeline/run_sweep.py` | orchestrator CLI | batch | `--batch_size` / `--num_train_epochs` family (:466-478, :1785-1791) | exact |
| `pipeline/dispatch_core.py` | dispatcher (lane values, mirrors) | batch | batch_size lane additions (:2355-2370, :2103-2145) | exact |
| `pipeline/run_sweep_shard.py` | passthrough shard | request-response | **NO CHANGES** (remainder passthrough, :321-344) | n/a (explicitly untouched) |
| `tui/services/run_config.py` | service (validation, RunSpec, persistence, composers) | transform | PARAM_*/PROBLEM_* + parse_params + _persist_payload blocks | exact |
| `tui/screens/run_config.py` | component (screen rows, dropdowns, two-layer layout) | event-driven | batch_size row (:1401-1408) + ChoiceRow/ChoiceModal (:591-620/:867-900) | exact |
| `tui/strings.py` | config (i18n labels) | n/a | CFG_FIELD_BATCH_SIZE/CFG_BATCH_SIZE_DEFAULT block (:1346-1348) | exact |
| `tests/tui/test_services_run_config.py` | test | n/a | batch_size parser/composer/persistence tests | exact |
| `tests/tui/test_pilot_run_config.py` | test (Pilot) | n/a | batch pilot case (:875-919) | exact |
| `tests/tui/test_strings_phase11.py` | test (tripwire) | n/a | EXPECTED_CFG_CONSTANTS inventory (:37-80) | exact |
| `tests/tui/__snapshots__/run_config*.svg` | golden | n/a | existing goldens; regen via `make snapshot-update` | exact |
| `scripts/live/record_tui_live_svg.py` | journey driver | file-I/O | `--batch-text` typed channel (:1703-1768, :2841-2846) | exact |

## Pattern Assignments

### `tui/services/run_config.py` — the param registry + validation + persistence tier

**Analog:** itself (batch_size, 261023-abu). All four blocks:

**PARAM_*/PROBLEM_* vocabulary** (lines 164-198) — new params add `PARAM_<NAME>` keys and
`PROBLEM_<NAME>_INVALID` codes here, never inline strings:
```python
PROBLEM_BATCH_SIZE_INVALID = "batch_size_invalid"
...
PARAM_EPOCHS = "num_train_epochs"
PARAM_EBS = "effective_batch_size"
PARAM_BATCH_SIZE = "batch_size"
```

**parse_params collect-all block** (verbatim shape, lines 467-478):
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
New parsers: `_parse_positive_float(value, lo, hi)`, `_parse_bool`,
`_parse_json_object` (json.loads + isinstance(dict) — never eval; the subset-file JSON
validation idiom). Prefer a table-driven loop over a frozen ADVANCED_PARAMS spec (RESEARCH
primary recommendation) over 14 hand-copies.

**Persistence sync pair** — `_persist_payload` params dict (lines 585-600) and
`_spec_from_doc` absent-key tolerant load (lines 714-725):
```python
        "params": {
            "seeds": list(spec.seeds),
            ...
            "batch_size": spec.batch_size,
            "workers": spec.workers,
            "gpus": (list(spec.gpus) if spec.gpus is not None else None),
        },
```
```python
    ok_batch, batch = _optional_int_at_least_one(
        params.get("batch_size"))
```
Rules: additive keys only, `SCHEMA_VERSION` stays 1, absent key → None (pre-change
documents load byte-identically), present-but-drifted → whole-default-policy reset.

**compose_argv / compose_dispatch_argv present-only appends** (lines 1313-1319):
```python
    if spec.num_train_epochs is not None:
        argv += ["--num_train_epochs", str(spec.num_train_epochs)]
    if spec.effective_batch_size is not None:
        argv += ["--effective_batch_size",
                 str(spec.effective_batch_size)]
    if spec.batch_size is not None:
        argv += ["--batch_size", str(spec.batch_size)]
```
New advanced flags go as ONE contiguous block after `--batch_size`, before `--cache_dir`;
pin element-for-element in test_services_run_config.py (the
test_compose_argv_full_spec_element_for_element shape). D-12: plain valued flags (the
`--num_train_epochs` shape) — NEVER `nargs='?' const=` semantics.

---

### `tui/screens/run_config.py` — rows, dropdown, two-layer layout

**Analog:** itself.

**Input row shape** (batch_size verbatim, lines 1401-1408) — `compact=True` is mandatory
(12-03 Rule-1):
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

**Dropdown idiom — ChoiceRow + ChoiceModal (RadioSet), NOT textual Select** (zero Select
usage in tui/; lines 591-614 + modal at :867-900):
```python
class ChoiceRow(Static, can_focus=True):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "pick_choice", show=False),
    ]
    def action_pick_choice(self) -> None:
        handler = getattr(self.screen, "action_pick_choice", None)
        if handler is not None:
            handler()
```
Reuse verbatim for lr_scheduler_type (12 options) and logging/eval/save_strategy (3
options each) — vocabularies from the live probe (RESEARCH lines 154-155), not memory.
Caveat: RadioButton `id=option` must be a valid Textual id.

**Two-layer structure**: section title via `cfg-section-title` (CFG_MGPU_TITLE mechanism,
:1418); collapsed advanced block via `display = False` (subset-input precedent, :1381) or
Checkbox (:1374); the `#cfg-params-col` VerticalScroll already scrolls — no new scroll
machinery. `_compose_spec` raw dict entries (:1788-1801) feed parse_params.

---

### `pipeline/run_sweep.py` — flag family

**Analog:** `--batch_size` (lines 466-478 argparse, 1785-1791 guard):
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
Per-param checklist (Pitfall 7): argparse + flag_problems mirror + sweep_flags dict
(:1874-1888) + build_argv/launch_subprocess kwargs (:1162-1293) + run_matrix partial
(:1546-1555). Note run_sweep.py:35 already shows a
`"batch_size": null, "gradient_accumulation_steps": null` manifest dict — extend that
shape for new advanced params.

### `pipeline/dispatch_core.py` — lane mirrors

**Analog:** batch_size lane entries. `lane_values` dict (lines 2355-2370):
```python
    lane_values = {
        "peft": sweep_args.peft,
        "config_variant": config_variant,
        ...
        "batch_size": sweep_args.batch_size,
        "num_train_epochs": sweep_args.num_train_epochs,
        ...
    }
```
Additive lane keys ride claim JSONs (no dispatch_state.json schema change, A5). Also:
parse_sweep_remainder re-parse (:2078), flag_problems mirror (:2103-2145), rerun
lane_values (:1719-1730), dry-run sweep_flags (:2296-2316), worker context build_argv
(:1041-1054), `_RERUN_LANE_TOKENS` (:193-198) — ALL of these per param or rerun/replay
breaks.

### `pipeline/run_finetune.py` — the new leg batch_size never needed

**Analog:** `--num_train_epochs` argparse + the quirk-mutation slot (lines 1090-1091):
```python
    if num_train_epochs is not None:
        configs["finetune"].num_train_epochs = num_train_epochs
```
Sanctioned channel is `configs["finetune"].<field> = value` placed AFTER the variant
reload; NOT the `extra_args` env seam (that is only for non-TrainingConfig fields like
dataloader_num_workers). Critical placements: GA override BEFORE the
`default_grad_accum = configs["finetune"].gradient_accumulation_steps` snapshot at
:1100 (Pitfall 1); keep bf16 at model level (fp32-only quirk block :1242-1249 correctly
wins, Pitfall 4); warmup_ratio MUST ride TrainingConfig only (transformers v5 removed it
from TrainingArguments, Pitfall 2).

### `tui/strings.py` — labels/placeholders

**Analog:** the batch_size block (lines 1346-1348) via `_t(...)`; placeholder grammar
follows CFG_GPUS_DEFAULT / CFG_BATCH_SIZE_DEFAULT ("—（默认: …）"). Static base-YAML
placeholder + variance hint (Pitfall 3, Open Question 3 recommendation). Long labels need
a `_SHORT` twin for narrow mode (CFG_FIELD_EBS_SHORT "eff_batch_size" at :1334 —
`gradient_accumulation_steps` (27 chars) will need one).

### `tests/tui/test_strings_phase11.py` — tripwire sync

**Analog:** the batch_size inventory entry (lines 76-79): every new CFG_* constant joins
`EXPECTED_CFG_CONSTANTS` in the SAME change or the bidirectional inventory test fails.
```python
    # 261023-abu: the per-device starting batch row — ...
    "CFG_FIELD_BATCH_SIZE", "CFG_BATCH_SIZE_DEFAULT",
```
One strings.py block + one tripwire edit per batch ("one block, one tripwire edit").
SERVICE tier stays zero-Chinese (WR-05, test_import_lock.py).

### Goldens (`tests/tui/__snapshots__/run_config*.svg`)

**Analog/discipline:** `make snapshot-update` (Makefile:132-133 runs
`tests/tui/test_snapshots.py --regenerate`) is the ONLY regen path — `pytest
--snapshot-update` does nothing. Leave regenerated SVGs UNCOMMITTED as one review batch;
never commit with feature code; the monitor goldens already carry WINDOWS #50/#51 dirt.

### `scripts/live/record_tui_live_svg.py` — typed-param channel

**Analog:** `--batch-text` (lines 1706-1708 typing + 1756-1762 assertion):
```python
    if ctx.args.batch_text:
        await _type_into(pilot, screen, "#cfg-input-batch-size",
                         ctx.args.batch_text)
```
```python
        if "--batch_size" not in tokens or ctx.args.batch_text not in (
                tokens[tokens.index("--batch_size") + 1:
                       tokens.index("--batch_size") + 2]):
            raise AssertionError(...)
```
Generalize as `--param <name>=<value>` repeats; keep the assertion pair (typed ⇒ flag
present with value; untouched ⇒ flag absent). Evidence can be --dry-run/preview-only
(in-flight FHS sweep — Pitfall 11).

## Shared Patterns

- **Present-only threading (D-12):** every hop appends `if value is not None` — compose_argv
  (:1313-1319), run_sweep build_argv, dispatch lanes. Empty TUI field ⇒ no flag ⇒ YAML governs
  (= restore-default semantics).
- **Collect-all validation, screens render never compute (D-07):** parse_params partials +
  PROBLEM_* tuples in the service; CLI mirrors + child argparse stay authorities.
- **Absent-key tolerant persistence:** additive params dict keys, absent → None, drift →
  whole-default reset (`_spec_from_doc` :714-725).
- **LIST argv discipline (D-06):** never shell strings.
- **Atomic state write:** `settings.atomic_write` + `sort_keys=True, indent=4` (save_state,
  :621-629).

## No Analog Found

None — every surface has a same-file precedent. The genuinely NEW composites (ADVANCED_PARAMS
table driving all surfaces; `_parse_positive_float` / `_parse_bool` / `_parse_json_object`
parsers; collapsed advanced section) are recombinations of the excerpts above per RESEARCH.md.

## Metadata

**Analog search scope:** tui/, pipeline/, tests/tui/, scripts/live/, Makefile (all
git-tracked, verified via `git ls-files`)
**Files scanned:** ~12 targeted reads/greps
**Pattern extraction date:** 2026-10-23
