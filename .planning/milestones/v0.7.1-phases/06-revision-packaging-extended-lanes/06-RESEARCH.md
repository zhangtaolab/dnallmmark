# Phase 6: Revision Packaging & Extended Lanes - Research

**Researched:** 2026-10-11
**Domain:** dnallm 1.2.1 adaptation verification; PEFT/frozen-probe/learning-curve/VEP lane mechanisms; provenance + snapshot + reproducibility packaging
**Confidence:** HIGH (code-grounded against both repos; every load-bearing claim carries a file:line anchor)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Extended-Lane Depth (Area 1 — accepted 2026-10-11)**
- All five lanes (LoRA, IA³, frozen probes, zero-shot VEP, learning curves) deliver full CODE MECHANISMS + fake-executor/synthetic-fixture tests, each independently cuttable (incomplete lane → response-letter future work with mechanism documented)
- LoRA + IA³ share one peft mechanism — suite-native since dnallm 1.2.1 (trainer.py imports get_peft_model/LoraConfig/IA3Config); IA³'s former "suite-support-gated last" condition is lifted
- Cost-accuracy frontier table: generation MACHINERY now (synthetic-fixture driven, schema'd, tests pin the shape), real numbers land automatically post-E2'
- Zero-shot VEP lane: offline scorer `script/zero_shot_vep.py` (CLM/MLM dual scoring + sanity checks + synthetic-fixture tests) — no GPU-path integration
- Learning curves: `run_sweep` extension (`--curve` schedule + probe checkpoint hooks), provable via --dry-run with fake executors

**Provenance & Snapshot (Area 2 — accepted 2026-10-11)**
- Provenance is REGISTRY-DRIVEN: datasets_info.json gains provenance columns (source, citation, license, preprocessing, ModelScope-default download URL + alternates); convert_registry.py extended to round-trip them; abort-on-wrong-count ingest discipline (D-10 continuity — no hand-curated parallel table)
- Unknown license/citation → explicit `Unspecified` + source link row, never blank (same discipline as the 7 missing-GUE rows); the generated provenance table is reviewed by the maintainer before publication
- Snapshot wired NOW: script/freeze_snapshot.py (tested, unwired since Phase 4) runs over the committed data-v1.1.0 tree → tar + SHA-256 manifest + frozen commit hash, supporting SI/Zenodo deposition; a documented re-freeze procedure covers the post-E2' data-v2 snapshot
- Provenance manifest downloads as CSV+JSON dual artifacts (mirrors the n_audit convention)

**Documentation Architecture (Area 3 — accepted 2026-10-11)**
- `docs/METHODOLOGY.md` (new docs/ dir): the four aggregation methods + F6 dual views documented in ONE place; README links to it
- README reproduction section: literal copy-pasteable command blocks (install → data → aggregate → serve) with expected outputs per step + a fresh-clone proof in the CI-replay style
- `docs/ONBOARDING.md`: new-model/new-dataset process as a dry-run-validated checklist (registry edit → convert_registry → audit → sweep --dry-run — mechanism validated with no GPU runs)
- Dead logic `recalculateComparison` (dnallm-mark/js/data.js:232) removed in a dedicated early commit BEFORE the methodology doc lands (docs never reference dead code; node tests prove no callers)

**Zenodo DOI & 1.2.1 Adaptation Mechanics (Area 4 — accepted 2026-10-11)**
- DOI swap (SC-7): a scripted one-click swap (README link + .gitleaks.toml allowlist rule removed in the SAME commit — WR-01 rule) is prepared and documented; the MAINTAINER executes it when Zenodo record 19135551 goes public (currently 404/not public — verified 2026-10-11). No agent polling/auto-swap
- `seed_result.json` (new suite per-seed file, shape {split, timestamp, metrics}): TOLERANT ADOPTION — the exporter gains a lenient reader that merges it as per-seed evidence when present and is non-fatal when absent; coexists with our run_record.json
- 1.2.1 adaptation verification is the FIRST plan of Phase 6 (quirk-list re-verification vs 1.2.1, peft config-surface mapping for the lane plans, env_smoke version expectations, seed_result.json decision landing); the lane plans depend on it

### Claude's Discretion
Implementation details within these envelopes (exact column names, script structure, doc section order, test placement) — following established repo patterns.

### Deferred Ideas (OUT OF SCOPE)
- Lane RUNS (LoRA/IA³/probes/VEP-execution/curves-execution) — post-E2', maintainer dual-gate GPU actions
- E2' launch itself (env_smoke on GB10 + explicit go) and the data-v2 tag — maintainer-only
- Reviewer-response report (F1-F10/G1-G7) — milestone close, gitignored, per standing maintainer directive (NOT a phase-6 plan deliverable)
- First real GitHub-runner CI execution + branch protection — maintainer setup (05-USER-SETUP.md)
</user_constraints>

## Project Constraints (from CLAUDE.md + session directives)

- **Tech stack frozen**: vanilla ES-module JS (no build step) + Python; static hosting only; no backend/API. Docs and packaging must not change architecture.
- **CI feasibility**: GitHub Actions must stay GPU-free AND dnallm-import-free (REL-02 / D-05: `torch.**`, `dnallm.**`, `transformers.**`, `peft.**` are `replace-imports-with-any` in ty; torch is never installed CPU-side).
- **Fix discipline**: surgical fixes; no opportunistic refactors.
- **DNALLM sibling repo is READ-ONLY** (`/home/forrest/Github/DNALLM`) — read freely, never write.
- **Lint + typecheck gates**: ruff AND ty must stay green from Phase 3 on (memory directive). New files join the Makefile lint list.

### Smoke sanction (CONSTRAINT CHANGE, 2026-10-11)

Maintainer directive (verbatim): "约束变更，可以跑 smoke test" followed by "可以用gpu测试". **Smoke tests are now SANCTIONED, including on the GB10 GPU directly.** Boundary:

| Action | Status |
|---|---|
| Install `[gpu]` group (torch==2.11.0/transformers==5.17.0) + dnallm from the local clone on this machine | SANCTIONED (part of the sanction) |
| EXECUTE `pipeline/env_smoke.py` (not just py_compile) | SANCTIONED — this host IS the GB10 |
| run_finetune tiny-model × 1-epoch smoke runs; run_sweep real smoke cells | SANCTIONED as explicit, bounded phase-6 plan TASKS (never as research-side execution) |
| VEP scorer / PEFT / curve-checkpoint smoke on tiny real models via GB10 | SANCTIONED |
| Full E2' three-seed sweep | STILL GATED (maintainer explicit dual-gate authorization only) |
| CI | STAYS GPU-free (unchanged) |

Consequences for phase-6 plans (folded into findings below): the adaptation plan can carry a real install+execute env_smoke task with a GPU-side PASS/FAIL verification; lane plans may add tiny-model smoke verification tasks where they were fake-executor-only; `env_smoke.py`'s module docstring contract ("Agents NEVER execute or import it — py_compile is the only sanctioned agent-side proof", env_smoke.py:4-10) must be AMENDED in the same adaptation commit to record the new sanction boundary. Note the smoke sanction does NOT lift the research-time constraint — this research pass executed nothing heavy; all findings below remain source-grounded.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REL-03 | README reproducibility section — literal copy-pasteable commands (install → data → aggregate → serve) | Findings E3; README today has NO such section (only feature bullets + pipeline usage); `make data` chain and `start-server.sh` are the blocks to literalize; CI-replay fixture is the fresh-clone proof pattern |
| DATA-04 | Provenance table for all 50 datasets (source, citation, license, preprocessing, download URL) | Findings E1: datasets_info.json 11-column schema today; convert_registry KIND_PRESETS extension path verified |
| DATA-05 | Downloadable data manifest (CSV/JSON) with full metadata + direct links | n_audit CSV+JSON dual-artifact convention (dnallm-mark/data/n_audit.{json,csv}) is the shape to mirror |
| DATA-07 | Aggregation-methodology documentation + removal of dead `js/data.js:recalculateComparison()` | Findings E4: zero callers confirmed; node suite requires data.js today (removal proof path) |
| EXT-01 | New-model onboarding documented + validated end-to-end | Findings E2/E5: registry → quirks → dry-run chain exists; `--dry-run` + fake executor is the validation vehicle |
| EXT-02 | New-dataset onboarding documented + validated end-to-end | Same; plus convert_registry round-trip + metric-mapping surface |
| REV-05 (F4) | LoRA/IA³/frozen probes + cost-accuracy frontier table | Findings A1 (peft surface), B (mechanism), C1 (head_config.frozen), B2 (frontier machinery) |
| REV-08 (F5+F8) | Zero-shot VEP lane (CLM/MLM scoring, sanity checks) + learning curves | Findings D (suite VEP core discovered — reuse, don't reimplement), C2 (curve schedule) |
| REV-03 tail | Snapshot wiring (tar + SHA-256 + frozen commit hash) | Findings E2: freeze_snapshot.py is complete + tested; manifest.json stamp pattern verified |
</phase_requirements>

## Summary

Phase 6's gating discovery: **dnallm v1.2.1 already ships nearly every mechanism the extension lanes need, battle-tested inside the suite.** The peft surface (LoRA via `DNATrainer(use_lora=True)` + `lora:` YAML section; IA³ via `finetune.use_ia3` + optional `ia3:` section) comes with 30 per-family target-module presets, a validate-and-exit `peft_dry_run` mode, and trainable-ratio guards. The zero-shot VEP scoring core (`dnallm/inference/vep.py`, 997 lines + a 1,515-line suite test file) implements exactly the CLM/MLM dual paradigm with a same-slot alignment rule, skip-as-data accounting, and ClinVar AUROC/AUPRC — our `script/zero_shot_vep.py` should be a registry batch DRIVER that lazily reuses these kernels, not a reimplementation. Frozen probes are expressible TODAY via `task.head_config.frozen: true` (suite-native, generic across non-special models). The learning-curve lane is a run_sweep extension following the proven `--priority-file`/`--from-failures` discipline.

On the packaging side: `freeze_snapshot.py` is a tested-but-unwired primitive needing only a Makefile target + path policy; datasets_info.json needs ~6 provenance columns threaded through convert_registry's KIND_PRESETS; the README reproduction section does not exist yet and is assembled from the already-working `make data`/`start-server.sh` chain; `recalculateComparison` (js/data.js:232) has zero callers and a clean removal path.

The environment facts changed mid-research: **the maintainer sanctioned smoke tests (including GPU) on this machine, which IS the GB10** — torch/peft are NOT currently installed (.venv = data/dev groups only, Python 3.13.16, numpy 2.5.3, pandas 2.3.3) and `pipeline/models/` does not exist, so the adaptation plan's install+smoke task is concrete and actionable. Pin compatibility is clean: dnallm 1.2.1 declares `torch>=2.4.0,<2.12` and `transformers>=4.49.0,<6`, both containing our `[gpu]` pins (torch==2.11.0, transformers==5.17.0).

**Primary recommendation:** Plan 1 = dnallm-1.2.1 adaptation verification (peft surface mapping + quirk re-verification + env_smoke update & sanctioned GPU execution + seed_result tolerant reader + install); Plans 2+ = the five lanes as independently cuttable mechanisms, each with the CPU-side fake/synthetic tests plus (where meaningful) one bounded GB10 smoke task; final plans = provenance+snapshot wiring, docs (dead-code removal first), DOI-swap preparation.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| PEFT adapter config resolution | dnallm suite (trainer.py ctor) | our run_finetune (passthrough flags) | Suite owns preset selection, dry-run validation, ratio guards; we only thread CLI/YAML through |
| PEFT lane cell enumeration | our run_sweep | run_finetune argv | Matrix expansion (peft variants, curve fractions) is sweep-driver logic, mirroring --priority-file precedent |
| VEP scoring math | dnallm suite (inference/vep.py kernels) | our script/zero_shot_vep.py (registry driving) | Kernels are tested suite code; reimplementation forks the statistical vocabulary (the tie-rule lesson) |
| VEP paradigm selection per model | our models_info.json (`type` column) | suite `_check_paradigm_compatible` guard | Registry knows MLM/CLM/DL; suite guard raises on mismatch as backstop |
| Frozen-backbone freezing | dnallm suite (`head_config.frozen`) | our run_finetune (config-variant loading) | `requires_grad=False` on backbone is model-construction-time; head plumbing is suite-native |
| Train-split fraction subsetting | our run_finetune / run_sweep | HF `Dataset.select` (suite precedent) | Same primitive as `--subset_file` (05-RESEARCH Pattern 5); eval stays governed by eval_subsets.json |
| seed_result.json tolerant read | our export_runs | — | Offline aggregation is our layer; suite only writes the file in its own (unused-by-us) run_seeds path |
| Provenance values | maintainer (review) | research (draft) + registry (storage) | CONTEXT Q2: registry-driven, maintainer-reviewed before publication |
| Snapshot freezing | our freeze_snapshot.py | Makefile wiring | Tested primitive exists; policy (paths, output dir, hash derivation) is packaging logic |
| Frontier table generation | our new machinery (schema + synthetic fixtures) | run_record/final_metrics producers | Machinery is ours; inputs are the existing record contracts |

## Findings

### A. dnallm 1.2.1 adaptation verification (gates the lane plans)

**Reference pin.** The suite repo's working tree is currently on branch `dev` at `98f7aa5` (= `milestone/v1.2-43-g98f7aa5`); tag `v1.2.1` = `30dfd6d`. Verified this session: `git diff v1.2.1..dev -- dnallm/` is EMPTY and the working tree is clean for `dnallm/`, and `pyproject.toml` is identical — every file:line citation below is valid for BOTH v1.2.1 and the current tree. The maintainer is actively working in that repo (branch moved during this research); the adaptation plan should re-pin by tag, not branch. [VERIFIED: git diff/gstatus this session]

#### A1. peft config surface (the lane-enablement map)

All anchors are `/home/forrest/Github/DNALLM/dnallm/...` at v1.2.1.

- **peft is a hard import**: `from peft import get_peft_model, LoraConfig, IA3Config` at module top (trainer.py:58). `import dnallm` pulls torch (via `.models`) AND peft (via `.finetune`) — dnallm/__init__.py:23-33 imports `.models`, `.datahandling`, `.finetune`, `.inference`, `.cli` unconditionally. Any dnallm import anywhere in our CPU-side code or CI remains forbidden (unchanged discipline). [VERIFIED: dnallm/__init__.py:23-33, trainer.py:58]

- **LoRA enablement is a CONSTRUCTOR KWARG, not a config field**: `DNATrainer(model=..., config=configs, datasets=..., extra_args=..., use_lora=True)` (trainer.py:369-376). Our call site today passes no `use_lora` (run_finetune.py:1027-1032) — the passthrough is a one-kwarg change plus YAML.

- **IA³ enablement IS a config field**: `TrainingConfig.use_ia3: bool = False` (configs.py:326-334). Set `configs["finetune"].use_ia3 = True`.

- **The `lora:` YAML section is REQUIRED for LoRA; `ia3:` is optional** — the exact branch, verbatim [VERIFIED: trainer.py:421]:
  ```python
  raw_section = config["lora"] if peft_kind == "lora" else config.get("ia3", Ia3Config())
  ```
  `use_lora=True` with no `lora:` section raises `KeyError: 'lora'`. IA³ without an `ia3:` section defaults to `Ia3Config()` and then preset resolution. `load_config` fills these sections only when the YAML carries them (configs.py:727-733).

- **dnallm's LoraConfig (pydantic) fields** [VERIFIED: configs.py:400-423, values verbatim]: `r: int = 8`, `lora_alpha: int = 16`, `target_modules: list[str] | None = None`, `lora_dropout: float = 0.1`, `bias: str = "none"` (pattern `^(none|all|lora_only)$`), `lora_bias: bool = False`, `inference_mode: bool = False`, `task_type: str | None = "SEQ_CLS"`.

- **dnallm's Ia3Config (pydantic) fields** [VERIFIED: configs.py:436-478, values verbatim]: `target_modules: list[str] | None = None`, `exclude_modules: list[str] | None = None`, `feedforward_modules: list[str] | None = None`, `fan_in_fan_out: bool = False`, `init_ia3_weights: bool = True`, `modules_to_save: list[str] | None = None`, `task_type: str | None = "SEQ_CLS"`. Cross-checked against peft upstream: `feedforward_modules` must be a subset of `target_modules` (peft validates), `exclude_modules` landed ~Oct 2024 (peft PR #2102) [CITED: huggingface.co/docs/peft/package_reference/ia3, github.com/huggingface/peft/pull/2102]. The suite filters kwargs through `PEFT_IA3_FIELD_NAMES = frozenset(f.name for f in dataclass_fields(IA3Config))` (trainer.py:72-75) so older peft (0.14) does not crash on unknown kwargs — dnallm pins `peft>=0.14.0` (pyproject.toml:52).

- **Preset auto-selection** (when `target_modules=None`): the trainer matches the live model against `dnallm/configuration/presets/lora_targets.yaml` — 30 family rows covering our registry's families (Plant DNABERT/DNAGemma/DNAGPT/DNAMamba/DNAModernBert/NT, AgroNT, NT, Caduceus-Ph/PS, PlantCaduceus, PlantCAD2, DNABERT/-2/-S, EVO-1/2, GENA-LM(+BigBird), GENERator, GenomeOcean, GPN, GROVER, HyenaDNA, Jamba-DNA, JanusDNA, LucaOne, megaDNA, Mistral-DNA, ModernBert-DNA, MutBERT, OmniNA, Omni-DNA, plant-genomic-jamba, ProkBERT). Matching is two-tier: name markers against `config._name_or_path` (longest marker wins), then `config.model_type`; no match → `ValueError` telling the user to set target_modules or run peft_dry_run (trainer.py:164-208). Each row carries `lora_target_modules`, `ia3_target_modules`, `feedforward_modules`, `lora_r`, `ia3_ratio_band`, `lora_ratio_band` [VERIFIED: presets/lora_targets.yaml:49-534].

- **`finetune.peft_dry_run` — validate-and-exit** (trainer.py:335-344, 451-461): resolves the final adapter config, matches target_modules against live `model.named_modules()`, raises on zero matches, prints a report, performs NO training, and leaves `trainer.trainer = None` so trainer-dependent methods fail with a matchable ValueError. Requires an adapter method (refuses to silently full-train, trainer.py:411-416). **This is the ideal cheap GPU-side verification for the PEFT lane plans** (sanctioned smoke: load model, dry-run, assert matched-module count) — far cheaper than a 1-epoch train.

- **Guards the lane design inherits for free**: LoRA×IA³ rejected at ctor (trainer.py:397-402); IA³×QLoRA rejected at config time (configs.py:374-389); trainable-ratio band guard after attach, computed from `requires_grad` tensors (trainer.py:248-288); `remove_unused_columns` forced False for adapters (trainer.py:541-547). QLoRA exists (`use_qlora` + `prepare_model_for_kbit_training`, trainer.py:470-474) but is OUT OF PHASE SCOPE (lanes are LoRA + IA³ per CONTEXT).

- **Config flow in our run_finetune** (how passthrough lands): per-model `configs = load_config("./finetune_config.yaml")` reload (run_finetune.py:619), per-dataset mutation of `configs["finetune"]` fields, then `DNATrainer(model=model, config=configs, datasets=dataset, extra_args=extra_args or None)` (run_finetune.py:1027-1032). The peft passthrough is: a `lora:`/`ia3:` section in the YAML (or a config-variant YAML), `configs["finetune"].use_ia3 = True` for IA³, and `use_lora=True` ctor kwarg for LoRA. All three are CPU-untouchable (import boundary) — contract tests stay source-textual (see Pitfalls).

#### A2. seed_result.json — exact writer + shape

- Constant: `SEED_RESULT_FILENAME = "seed_result.json"` (sweep.py:168), written by the suite's `run_seeds` per seed, immediately after `fn(seed, seed_dir)` returns (sweep.py:308-324). Payload verbatim [VERIFIED: sweep.py:314-324]:
  ```python
  {
      "model_name": model_name,
      "task_name": task_name,
      "seed": seed,
      "timestamp": datetime.now(UTC).isoformat(),
      "metrics": metrics,
  }
  ```
  **Note the CONTEXT's "{split, timestamp, metrics}" paraphrase is loose**: the suite file carries `model_name`/`task_name`/`seed`, not `split`. The `{split, timestamp, metrics, runtime}` shape belongs to a DIFFERENT suite file — `eval_{split}_result.json`, written by `DNATrainer.evaluate(split=...)` (trainer.py:903-904, 965-977). The tolerant reader should accept the actual shape above (and can cheaply also accept `eval_*_result.json` if present — same evidence class). [VERIFIED: sweep.py:308-332, trainer.py:965-977]

- **We never produce seed_result.json today**: our run_sweep launches run_finetune subprocesses (run_sweep.py:619-634); the suite's `run_seeds` is not in our path. run_finetune writes `final_metrics.json` + copies `trainer_state.json` (run_finetune.py:1051-1053); run_sweep writes `run_record.json` (run_sweep.py:663-682). The exporter's tolerant reader is therefore FORWARD-COMPAT adoption: merge `seed_result.json` as per-seed evidence when present (metrics block), non-fatal when absent — landing point is `load_run_records`/`_collect_cell_values` (export_runs.py:420-451, 466+). Precedent for tolerance: `LEGACY_DATASET_METRIC` alias map (export_runs.py:384+) and the malformed-record abort discipline (a present-but-malformed seed_result should follow whichever policy the planner picks — recommend: absent = skip silently, present-but-malformed = loud abort, matching run_record handling at export_runs.py:426-427).

#### A3. quirk lists vs 1.2.1

Our six registries (run_finetune.py:552-602): `model_not_use_safetensors` (11), `deeplearning_models` (4), `models_no_char_n` (4+6), `models_with_limited_length` (2), `models_only_support_fp32` (4), plus the `special_models` pair `["evo2_1b_base", "megaDNA_updated"]` loading the with_head YAML (run_finetune.py:630-632). Verified against 1.2.1:

- **safetensors quirk flows unchanged**: `save_safetensors` is a TrainingConfig field (configs.py:288); the trainer pops it (`self._save_safetensors = training_args.pop("save_safetensors", True)`, trainer.py:534) and threads it into `safe_serialization` at both save sites (trainer.py:798/809, 865/876). Our `configs["finetune"].save_safetensors = False` (run_finetune.py:784-786) keeps working. [VERIFIED: trainer.py:534, 798-876]
- **trust_remote_code is unconditional** in every load path (model.py:120, 592, 602, 1050, 1074) — no per-model list needed, unchanged.
- **NEW vs our adaptation revision**: the whole v1.2 revision (commit 92a8106, ~26.9k insertions) landed between `483a35c` (the revision our run_finetune docstrings cite, e.g. run_finetune.py:676-677 "trainer.py L568-605 @ revision 483a35c") and v1.2.1. `models/model.py` changed in that commit; **`attn_implementation: "eager"` is now hardcoded** in `_load_model_by_task_type`'s `model_load_kwargs` (model.py:591-594) — attention implementation is pinned eager for all generic-path loads. The adaptation plan should note this as a behavioral pin (no flash-attempt) and refresh the stale inline revision citations (the EVAL-01 block now sits at trainer.py:571-605 in v1.2.1 — same content, shifted lines). [VERIFIED: model.py:590-594; git log 483a35c..v1.2.1]
- **EVAL-01 semantics preserved**: `allow_test_as_eval: bool = False` (configs.py:317-325); our config-purity contract (the key never appears in our YAMLs) remains the right guard; the run_finetune Dev-less refusal (run_finetune.py:684-695) still matches suite behavior. [VERIFIED: configs.py:317-325, trainer.py:571-605]
- **Tokenizer fallback for transformers v5** now exists (`load_tokenizer_with_fallback` → `PreTrainedTokenizerFast` → `DNAOneHotTokenizer`, tokenizer.py:256-270) — relevant to k-mer models under transformers 5.17; flag for the smoke task to watch. [VERIFIED: tokenizer.py:256-270]
- `load_local_data`/`validate_sequences`/`sampling` import surface intact (CONTEXT pre-verified; unchanged in diff). The metric registry 28-canonical/zero-drift claim was verified in the CONTEXT session and the file is unchanged since (metric_registry.py present; not re-enumerated this session — carried as CONTEXT-verified).

#### A4. env_smoke expectations vs 1.2.1 pins

- dnallm 1.2.1 pins (pyproject.toml, verbatim rows) [VERIFIED: /home/forrest/Github/DNALLM/pyproject.toml:6,31,48,52,57,65,67]: `requires-python = ">=3.11"`, `"datasets<=3.2.0"`, `"numpy>=2.0.0"`, `"peft>=0.14.0"`, `"scikit-allel>=1.3.13,<2"`, `"torch>=2.4.0,<2.12"`, `"transformers>=4.49.0,<6"`. Also core: `bitsandbytes>=0.43.0`, `mcp>=1.3.0,<2`, `modelscope[framework]>=1.23.2`, `jax>=0.5.2`, `altair[all]>=5.5.0`, `numba>0.56.2`, `pandas>=2.2.3`, `scipy>=1.15.2`, `evaluate>=0.4.3`.
- **Our [gpu] pins sit inside every bound**: torch==2.11.0 ∈ [2.4.0, 2.12); transformers==5.17.0 ∈ [4.49.0, 6); .venv Python 3.13.16 ≥ 3.11. No pin change needed. The mismatch-resolution question is now concretely answerable by the sanctioned install+smoke task (uv resolves dnallm's heavy core deps — jax/modelscope/bitsandbytes are multi-GB; expect install time, and expect `datasets` to resolve ≤3.2.0 which is NEW to our env). [VERIFIED: pyproject.toml both repos]
- **env_smoke.py gaps for 1.2.1**: (a) stale "dnallm 0.8.0" version labels in docstrings and messages (env_smoke.py:32-37, 41-43, 134-136, 182-188, 195-199, 212-215) — the underlying facts (datasets cap, numpy floor) are still true for 1.2.1 but should be relabeled; (b) no `peft` check — the lanes now depend on it, so a PASS/FAIL line for `import peft` + version print is a natural addition (non-gating or gating, planner's call); (c) the docstring contract "Agents NEVER execute or import it" (env_smoke.py:4-10) must be amended to record the smoke sanction. Its 6 checks otherwise remain correct: pins parsed from pyproject (never duplicated), dnallm import, CUDA device, matmul, numpy floor, dataset-dir presence with the 7-GUE visibility. [VERIFIED: env_smoke.py:1-57, 368-404]

#### A5. new suite modules — adopt/guard

- `cli/` (train, inference, vep, mutagenesis, model_config_generator), `inference/` (vep.py, probing.py 700L, benchmark, mutagenesis, interpret, plot), `interpret/` (motifs), `tasks/` (metric_registry, metrics), `mcp/` (server + own requirements.txt). None are imported by our chain; `dnallm/__init__.py` pulls `.inference` and `.cli` at import time (heavier import surface, still torch-bound). Nothing in our run/export chain needs adoption from cli/inference/interpret EXCEPT vep.py kernels (lane D) and probing.py (possible frozen-probe reference — see C1). mcp is server infrastructure with separate requirements — guard: never let a `dnallm` import in our CPU-side scripts happen at module level (unchanged). [VERIFIED: dnallm/__init__.py:23-33, module listings]

### B. PEFT lane mechanism (LoRA + IA³ shared)

**Minimal integration shape** (recommendation, following established patterns):

1. **YAML**: add `lora:` + `ia3:` sections to `pipeline/finetune_config.yaml` (commented defaults; active only when the trainer is asked). Because `use_lora=True` requires `config["lora"]` to exist (A1), the section must be present even for non-peft runs — harmless: `load_config` constructs the pydantic object and nothing reads it without the enablement signal.
2. **run_finetune passthrough**: `--peft {none,lora,ia3}` (choices) → for `lora`: `use_lora=True` ctor kwarg; for `ia3`: `configs["finetune"].use_ia3 = True`. Mutually exclusive by argparse construction (the suite's ctor guard is the backstop). Record the mode in the cell's outputs (see 4).
3. **Alias isolation**: reuse the EXISTING `--save_model_name` flag (run_finetune.py:181, 794) — adapter runs use `{model}+lora` / `{model}+ia3`, giving separate output dirs AND separate `trainer_state.json` resume markers (run_finetune.py:795-800) without touching the layout code. Registry lookup stays on the base name (target_model filters before save_model_name applies).
4. **run_sweep threading**: a `--peft` flag on run_sweep composes into `build_argv` (run_sweep.py:595-616) — the same LIST-not-string discipline (T-03-10); dry-run manifests then show the adapter cells without any execution. A `peft` field in `run_record.json` (default `"none"`) marks the mode; export/join layers strip the `+lora`/`+ia3` suffix for the models_info metadata join while keeping the alias as the emitted model name (the D-18 alias-normalization precedent from 05-04 handles exactly this class of name-form drift).
5. **CPU-testable surface**: (a) source-contract tests (the read-source-never-import pattern, tests/test_run_finetune_contracts.py:6-10) asserting the passthrough wiring — kwarg present at the ctor site, use_ia3 set before ctor, `lora:` section present in the YAML; (b) run_sweep fake-executor tests (tests/test_sweep.py discipline) asserting argv composition, record fields, alias cell dirs; (c) schema tests for any new record fields. What CANNOT be CPU-tested: actual adapter attach — covered by the sanctioned GB10 smoke (a `peft_dry_run=true` tiny-model task: load one small model, construct DNATrainer with use_lora, assert the dry-run report and exit — no training, minutes not hours).

**Frontier table machinery** (schema-first, synthetic-fixture driven):

- Columns derivable from EXISTING record contracts: `method` (none/lora/ia3, from run_record), `wall_hours` (started_at/finished_at per cell, run_sweep.py:663-682), `total_flos` (already required in metrics — its absence is a hard exporter error, export_runs.py:494-499), `score` / `score_delta` (join adapter-cell export vs full-run export per (model, task)).
- **One producer gap**: trainable-params %. The suite computes and prints it (`print_trainable_parameters()`, `_guard_trainable_ratio` returns `(trainable, total, ratio)`, trainer.py:248-288) but does NOT persist it. Smallest change: run_finetune computes `sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)` after DNATrainer construction and persists `trainable_params`/`total_params`/`trainable_params_pct` into `final_metrics.json` (or the run_record via a new field). This lands in the peft plan; the frontier machinery then reads it.
- Output: `dnallm-mark/data/frontier.{json,csv}` (n_audit dual-artifact convention) + a new schema bucket in tests/test_schemas.py SCHEMA_FILES + DATA.md-style generated appendix. Generation machinery tested on synthetic run-record trees (the `_build_fixture_tree` pattern, tests/test_export_runs.py). GPU-hours ESTIMATE (vs wall): document as wall-clock based, since precise accounting would need the vram_probe persistence that is still null-when-unknown (run_sweep.py:45-49).

### C. Frozen probes + learning curves

#### C1. Frozen probes — suite-native via `head_config.frozen`

- **Freeze is expressible TODAY** [VERIFIED: model.py:101-103, verbatim]:
  ```python
  if self.config.head_config.get("frozen", False):
      for param in self.backbone.parameters():
          param.requires_grad = False
  ```
  and the config field [VERIFIED: configs.py:14-17, verbatim]: `frozen: bool = Field(default=False, description=("Whether to freeze the model except the head during training."))`.
- **The head path is generic, not evo/megaDNA-only**: `_load_model_by_task_type` routes ANY model to `DNALLMforSequenceClassification.from_base_model` when `task_config.head_config` is present (model.py:600-615); head types dispatch on suffix: `mlp`/`cnn`/`lstm`/`unet` (model.py:140-146); `pooling_strategy` configurable (model.py:156-157). Our with_head YAML (finetune_config_with_head.yaml) already carries the full head_config block — a probe variant is that block with `head: mlp`, `frozen: true`, small `hidden_dims`.
- **Applicability boundary (planner must scope)**: the special handlers (evo2/evo1/megadna own head branches; enformer/space/borzoi/flashzoi dedicated loaders, model.py:1169-1220) bypass or specialize the generic head path. The 5 `deeplearning_models` are therefore OUT of the frozen-probe lane scope (they are also out of the VEP lane — see D); scope = generic-path models, disclosed in the lane docs.
- **Implementation shape (recommendation)**: run_finetune gains `--frozen-probe` (or a `--config-variant probe` mechanism generalizing the evo/megaDNA reload at run_finetune.py:630-632): when set, load a `finetune_config_probe.yaml` for ANY model (the with_head reload currently keys on the special_models membership — the variant generalizes the same in-loop reload discipline, respecting the D-11 per-model reload + head_config.task_type per-dataset assignment at run_finetune.py:718-719). Probe runs alias as `{model}+probe` via save_model_name (same as peft aliases). The suite's own `inference/probing.py` (700 lines: embedding extraction/probing) is a REFERENCE for probe methodology but is an inference-time module — our lane stays fine-tune-shaped (frozen backbone + trained head through the normal Trainer), which is what makes metrics comparable to the main leaderboard.
- **CPU-testable**: source-contract tests (variant reload placement, frozen flag in the probe YAML), sweep fake-executor tests for `+probe` cells; GPU smoke = tiny model, 1 epoch, assert backbone grads absent (e.g. all(not p.requires_grad for p in trainer.model.backbone.parameters()) — cheap assertion task).

#### C2. Learning curves — run_sweep `--curve` schedule

- **Data-fraction subsetting**: `--curve "0.25,0.5,1.0"` (or a fractions file) expands each (model, task, seed) cell into per-fraction cells. The subsetting primitive is the SAME one `--subset_file` uses (HF `Dataset.select` on the train split — 05-RESEARCH Pattern 5, applied there to test; here to train): `dataset.dataset["train"] = dataset.dataset["train"].select(range(int(n * f)))` or seed-shuffle-then-select (recommend: shuffle(seed=cell seed).select — fraction variance should be governed by the run seed, documented either way). Dev/test untouched → **eval_subsets.json discipline keeps test rows identical across fractions and models** (the 05-03 unified eval-subset contract is exactly the consistency guarantee a learning curve needs).
- **Output layout (recommendation)**: nest under the seed dir — `{root}/{model}/{task}/seed_{seed}/frac_{f}/` — so the existing `trainer_state.json` resume marker per (model, task, seed) does NOT collide across fractions; the marker check must then be scoped to the frac dir. Alternative (sibling `frac_` cells at task level) breaks the marker scoping — avoid.
- **Probe checkpoints**: `eval_steps`/`save_steps`/`logging_steps` already exist in TrainingConfig (configs.py:282-286); the curve YAML variant tightens them (e.g. eval every N steps) — no suite change needed. Checkpoint harvesting is post-hoc from `trainer_state.json`/log history — machinery can define the curve-extraction reader offline (CPU-testable against synthetic trainer_state fixtures).
- **Dry-run provability**: the matrix expansion is pure enumeration — `--curve` + `--dry-run` writes planned frac cells into `sweep_manifest.json`; fake-executor tests pin argv composition (a `--train_fraction` flag on run_finetune) and record fields (`train_fraction` in run_record). Fail-fast validation of the fraction list (the `_validate_filters` collect-all-problems discipline, run_sweep.py:290-335).

### D. Zero-shot VEP scorer

**Headline: the suite ships the complete, tested scoring core.** `dnallm/inference/vep.py` (997 lines; suite test file `tests/inference/test_vep.py` = 1,515 lines, runs kernels on a real tiny torch module — `TinyDNAModel`/`SimpleDNATokenizer` fixtures in tests/conftest.py:122-176):

- `align_variant(sequence, pos, ref, alt, tokenizer) -> VariantAlignment` — the same-slot evaluability rule: scoreable only when ref/alt tokenizations have equal length and differ at exactly ONE token slot; otherwise a machine-readable skip record (`"length-changing allele"`, `"multi-slot token difference"`, `"no change"`) — skip-as-data, never exceptions (vep.py:57-114, 114-192).
- `clm_log_likelihood(model, tokenizer, sequence)` — full-sequence causal log-likelihood, one forward pass, shifted-logits gather (vep.py:219-258).
- `mlm_slot_log_prob(model, tokenizer, sequence, slot_index, token_id)` — mask-and-predict log-prob at one slot (vep.py:261-304).
- `score_variant(model, tokenizer, sequence, pos, ref, alt, *, paradigm="mlm")` — paradigm dispatch with the **paradigm↔architecture guard** (bidirectional model + clm → ValueError; tokenizer without mask_token + mlm → ValueError; vep.py:622-657). Deltas are alt-minus-ref → deleterious NEGATIVE; AUROC/AUPRC computed over `-delta` (the evo2-clinvar/GPN field convention; vep.py:766-771). These sign/paradigm conventions cross-check against the literature [CITED: openreview.net/pdf?id=2BsTU6MuzC; biorxiv 2025.02.18.638918 (evo2); Benegas et al. GPN].
- `evaluate_vcf(model, tokenizer, vcf_path, reference, *, paradigm, context_window=200, ...)` — ClinVar-style VCF driver via scikit-allel (`allel.read_vcf`, `alt_number>=4` to avoid 4+-allelic truncation); D-17 cohort convention: SNVs only, `Pathogenic/Likely_pathogenic` vs `Benign/Likely_benign` strict whitelist (VUS/conflicting excluded), >=1 review star; reference accepts a FASTA path OR a plain `Mapping[str, str]` chromosome dict (vep.py:451-504) — **the mapping form is the synthetic-fixture door: no FASTA needed for tests**.
- `VepConfig` pydantic scaffold already in load_config's section list (`paradigm: "mlm"` pattern `^(clm|mlm)$`, `context_window: 200`, `output_dir`; configs.py:481-507, 735-737).

**Design for `script/zero_shot_vep.py` (recommendation): registry batch DRIVER, kernels lazily imported.**

1. Module-level code stays torch-free (vep.py imports torch at module top — importing it CPU-side is impossible; CI stays GPU/dnallm-free). The suite kernels are imported INSIDE the GPU run path (`from dnallm.inference.vep import score_variant, align_variant` behind the scorer seam).
2. Owns: iterate `pipeline/models_info.json` (62 models); paradigm selection from the `type` column [VERIFIED this session: MLM 32, CLM 18, DL 5, EMPTY 7]; DL + EMPTY rows emitted as excluded-with-reason rows (the missing-row disclosure discipline); tokenizer-type awareness for context policy (`Tokenizer` values observed: BPE 23, singlebase 31, one-hot 1, 6mer 6, "6-mer" 1 — note the inconsistent 6mer/6-mer spellings, a data-hygiene flag for the adaptation or provenance plan); model loading via `load_model_and_tokenizer` (GPU path) with `Model_path`/`modelscope`/`huggingface` columns.
3. Sanity checks: (a) synthetic synonym-vs-nonsense fixture — a hand-built tiny VCF + reference mapping where nonsense variants must score more deleterious than synonymous under any discriminating model (expectation test on a stub scorer CPU-side; on the REAL scorer it becomes a GB10 smoke assertion); (b) reverse-complement control for causal models (score window + RC window; report both + asymmetry — the PlantCAD2/evo-documented concern [CITED]); (c) skip-fraction disclosure per model (the suite already reports it — surface it in our per-model rows).
4. Output: per-model rows `{model, paradigm, evaluated, skipped, skip_fraction, AUROC, AUPRC, convention, rc_control}` → `dnallm-mark/data/vep_zero_shot.{json,csv}` (dual-artifact convention) + schema bucket + synthetic-fixture tests pinning the shape. AUROC/AUPRC via the suite's metric registry through evaluate_vcf, or our own aggregation of per-variant deltas (recommend: drive `evaluate_vcf` per model — it already does convention + metrics + skip accounting; our script supplies model+tokenizer+VCF+reference and collects `VepResult.to_dict()`).
5. Input fixtures: a ClinVar-shaped synthetic VCF (the suite's own `tests/inference/data/synthetic_variants.vcf` + `synthetic_reference.txt` are committed in the suite repo — read-only reference for fixture SHAPE; we author our own under tests/fixtures to keep DNALLM read-only boundaries clean).
6. GPU boundary: it must RUN at E2' time on GB10 over the 62-registry models (CPU-slow/VRAM-light per model; batch windows; the suite runs one window per variant pair) and be TESTABLE now on synthetic fixtures + (sanctioned) a tiny-model GPU smoke.

### E. Provenance + snapshot + docs (packaging)

#### E1. Provenance columns

- `pipeline/datasets_info.json` today: 50 entries, 11 columns [VERIFIED this session: `Category, Dataset_name, Dataset_path, Dev, Index, Test, Train, labels, length, metric, type`]. Needed additions (CONTEXT): `source`, `citation`, `license`, `preprocessing`, `download_url` (ModelScope default), `download_url_alternates`. Names are planner's discretion; keep the D-10 no-parallel-table rule: the JSON registry is the single source, CSV is the projection.
- **convert_registry extension path** [VERIFIED: convert_registry.py:84-113]: `KIND_PRESETS["datasets"]["columns"]` is a plain list — new columns append to it; `--to-csv` emits them (missing → empty cell), `--to-json`/`--merge-existing` round-trips them. The abort-on-wrong-count ingest discipline: the D-10 continuity means ingest validates expected column presence (extend the existing validation family). Round-trip test extends tests/test_convert_registry.py.
- **Value seeding**: research drafts values from public sources (dataset papers, ModelScope/HF/GUE pages) into a CSV; maintainer reviews before publication (CONTEXT Q2 — binding). Unknown license/citation → literal `Unspecified` + the source link in `source`, never blank — mirroring the 7-missing-GUE rows discipline (DATA.md:43-53).
- **Artifacts**: generated `dnallm-mark/data/provenance.{json,csv}` (dual, n_audit convention) + a generated DATA.md provenance appendix table (50 rows + the generator script header stamp, DATA.md:3-7 pattern). Generator = new `script/build_provenance.py` (or extend audit script family) reading the registry only — deterministic, CPU, CI-testable via synthetic registry slices.

#### E2. Snapshot wiring

- `script/freeze_snapshot.py` is COMPLETE and tested (tar + sorted SHA256 manifest with `# commit <hash>` header; freeze_snapshot.py:51-103). It is explicitly "unwired from any Makefile target this phase — Phase 6 packaging owns the invocation policy" (freeze_snapshot.py:86-87, 12-15).
- Wiring needs [recommendation]: (a) a `snapshot:` Makefile target invoking it over the data-v1.1.0 tree — the derived-data set: the 4 `models_comparison*.json`, `tasks.json`, `task_performance/`, `n_audit.{json,csv}`, `permutation_tests.json`, `manifest.json` (the committed contents of dnallm-mark/data/ minus model_performance/ which is an input, not derived — planner confirms the exact list); (b) output dir `baseline/snapshots/` (gitignored — artifacts are for deposition, not the repo; mirrors how baseline/data-v1.sha256 is committed but tars are not) — or committed manifests only; (c) **commit-hash derivation without live git in the data path**: `manifest.json` already carries `generated_from: "991804613c4874bfa3f32d318340b5d7b4118ffe"` + `data_version: "1.1.0"` + `date` [VERIFIED: dnallm-mark/data/manifest.json] — the snapshot target can read THAT (a constant committed with the data) instead of shelling git, keeping the data path hermetic; `--commit-hash "$(git rev-parse HEAD)"` remains the manual override; (d) re-freeze procedure doc: post-E2' data-v2 → `make data` → verify drift-clean → `make snapshot` → new manifest+tar; the data-v2 gate tooling rehearsal from 05-04 composes here.
- Re-verification from manifest: `sha256sum -c snapshot-<hash>.sha256` (line format is the standard `sha256sum -c` form — two spaces, baseline/data-v1.sha256 convention).

#### E3. README reproduction + docs/

- **README today has NO reproduction section** [VERIFIED: README section map — Quick Start covers only the local server (:100-111); the pipeline section covers GPU pipeline usage (:113-227); nothing walks install→data→aggregate→serve for a fresh clone]. The literal blocks exist as working commands: `uv sync` (pyproject: default-groups=["data"]), `make data` (Makefile:44-49 — summarize → permutation → tasks-index), `make test`, `bash start-server.sh` / `cd dnallm-mark && python3 -m http.server 8080`. Expected outputs per step: quoting the deterministic-emission guarantees (byte-stable `make data` no-op on committed tree — the drift-gate invariant) and the tasks.json row count. Fresh-clone proof in the CI-replay style = the committed `tests/fixtures/e2_replay/` chain (05-01) is the pattern; a docs-side variant can state "CI replays exactly this chain on every PR" with the badge link.
- **docs/ does not exist yet** [VERIFIED: ls]. New `docs/METHODOLOGY.md` documents the four aggregation methods (rank / MinMax / z-score / robust — all in `script/summarize_comparison.py`) + the F6 dual views (rank_score vs weighted_score, tie rule, permutation tests) in ONE place; README links to it. `docs/ONBOARDING.md`: the EXT-01/02 checklists (registry edit → convert_registry round-trip → quirks if needed → audit → `run_sweep --dry-run` validation → post-run export steps at E2'), each step dry-run-validatable with no GPU.
- **DOI swap (SC-7)**: the load-bearing README link + HTML comment (README.md:117-123), the `.gitleaks.toml` rule-level allowlist anchored `^README\.md$` + record-scoped regex `zenodo\.org/records/19135551\?preview=1&token=` (.gitleaks.toml:19-35). The scripted swap = a small script (e.g. `script/doi_swap.py`) that (1) rewrites the README link to the public DOI URL, (2) removes the HTML comment + the allowlist rule block, (3) refuses to run when the target DOI is still 404 (a `--force` for the maintainer), all in ONE commit (WR-01 same-commit rule). Documented in the phase docs; the MAINTAINER executes when record 19135551 goes public. Zenodo 404 status re-verified 2026-10-11 (CONTEXT).

#### E4. Dead logic removal — `recalculateComparison`

- Definition at dnallm-mark/js/data.js:232 [VERIFIED: read this session]. **Zero callers confirmed**: repo-wide grep finds only (a) the definition, (b) a config.js:37 comment citing "the dead recalculateComparison lesson", (c) a tests/js/main-view-toggle.test.js:9 comment. No HTML/JS calls it. [VERIFIED: grep this session]
- Node-test coverage for the removal: `tests/js/data-escape.test.js` already does `require('../../dnallm-mark/js/data.js').default` (data-escape.test.js:16) — the module keeps importing/loading post-removal, and `make test`'s `node --test tests/js/` lane (Makefile:66-69) is the proof. Add/extend a data.js node test asserting the exported surface (or simply that DataAPI loads + memoizes) in the same early dedicated commit, before METHODOLOGY.md lands (CONTEXT sequencing).

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| peft | >=0.14.0 (suite pin; latest ~0.21.x) | LoRA/IA³ adapters | dnallm 1.2.1 core dependency; suite presets + guards built on it [VERIFIED: DNALLM pyproject.toml:52] |
| scikit-allel | >=1.3.13,<2 (suite pin) | VCF parsing in the suite VEP driver | suite's adopted reader (owner decision recorded in suite 92a8106) [VERIFIED: DNALLM pyproject.toml:57] |
| torch / transformers | 2.11.0 / 5.17.0 ([gpu] pins) | GPU path only | inside suite bounds torch>=2.4,<2.12 / transformers>=4.49,<6 [VERIFIED: both pyprojects] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dnallm | 1.2.1 (local clone, tag v1.2.1) | peft trainer surface, VEP kernels, head/frozen plumbing | GPU-side only; never imported CPU-side/CI |
| pydantic (transitive via dnallm) | >=2.10.6 | config validation in suite | suite-internal; our YAML sections validate through it at GPU time |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Suite VEP kernels (lazy import) | Hand-rolled CLM/MLM scoring in our script | Hand-rolling forks tested statistical code + redoes the alignment rule — rejected (tie-rule lesson) |
| `--peft` flag passthrough | Separate peft config-variant YAML only | Flag composes with run_sweep cell expansion; YAML-only cannot enumerate adapter cells in dry-run |
| frac-nested seed dirs for curves | Sibling frac dirs at task level | Sibling layout breaks the trainer_state.json marker scoping (seed-scoped resume) — rejected |

**Installation (GPU env, sanctioned smoke scope):**
```bash
uv sync --group gpu            # torch==2.11.0 (cu130 index), transformers==5.17.0
uv pip install -e /home/forrest/Github/DNALLM   # dnallm 1.2.1 + its core deps (heavy: jax, modelscope, bitsandbytes)
```
(Equivalent pip forms acceptable; the point is: local clone, tag v1.2.1 content.)

## Package Legitimacy Audit

No NEW external packages are introduced by this phase's plans. All GPU-path dependencies (peft, scikit-allel, bitsandbytes, datasets≤3.2.0, ...) arrive transitively through the dnallm 1.2.1 local-clone install, whose pins were read directly from its pyproject.toml this session [VERIFIED: /home/forrest/Github/DNALLM/pyproject.toml:24-67]. CPU-side/CI additions are none (stdlib + existing locked groups). Registry cross-checks: peft and scikit-allel confirmed on PyPI via official HF/scikit-allel documentation surfaces [CITED: huggingface.co/docs/peft, github.com/huggingface/peft/pull/2102]. Disposition: nothing to remove or flag.

## Architecture Patterns

### System Architecture Diagram (phase 6 mechanism flow)

```
                     ┌────────────────────────────────────────────────┐
                     │  PLAN 1: dnallm 1.2.1 adaptation verification  │
                     │  (gates everything below)                      │
                     └───────┬────────────────────────────────────────┘
                             │ verifies
        ┌────────────────────┼─────────────────────────────┐
        ▼                    ▼                             ▼
 [peft surface map]   [quirk re-verification]     [env_smoke update + GB10 install/smoke]
        │                    │                             │
        ▼                    ▼                             ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │ run_finetune: --peft {none,lora,ia3} · --frozen-probe · --train_frac │
 │  (YAML lora:/ia3: sections · use_lora ctor kwarg · use_ia3 field ·   │
 │   head_config.frozen · save_model_name {model}+lora|+ia3|+probe)     │
 └───────┬──────────────────────────────────────────────────────────────┘
         │ argv (LIST)                                  │ seed dirs
         ▼                                              ▼
 ┌──────────────────────────┐              ┌───────────────────────────┐
 │ run_sweep --peft/--curve │──dry-run──▶  │ {root}/{model}/{task}/    │
 │ matrix expansion +       │  manifest    │  seed_{s}[+frac_{f}]/     │
 │ fail-fast validation     │              │  run_record.json (+peft,  │
 └──────────────────────────┘              │  +train_fraction fields)  │
                                           │  final_metrics.json       │
                                           │  seed_result.json (future,│
                                           │   suite-written, tolerant)│
                                           └────────────┬──────────────┘
                                                        │ read
                                                        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │ export_runs (tolerant seed_result reader) ──▶ frontier machinery ──▶ │
 │ dnallm-mark/data/frontier.{json,csv} (schema-pinned, synthetic-      │
 │ fixture tested; real numbers land post-E2')                          │
 └──────────────────────────────────────────────────────────────────────┘

 script/zero_shot_vep.py ──lazy──▶ dnallm.inference.vep kernels
   (62-model registry driver · paradigm by models_info `type` ·
    skip/disclosure rows for DL+EMPTY · synonym/nonsense + RC sanity ·
    vep_zero_shot.{json,csv} · CPU fixtures + GB10 tiny-model smoke)

 Packaging lane (independent of lanes above):
   datasets_info provenance cols ─▶ convert_registry round-trip ─▶
   build_provenance ─▶ data/provenance.{json,csv} + DATA.md appendix ─▶
   make snapshot (freeze_snapshot over data-v1.1.0, hash from manifest.json)
   docs/METHODOLOGY.md + docs/ONBOARDING.md + README reproduction section
   (dead-code removal commit FIRST) + script/doi_swap.py (prepared, maintainer-run)
```

### Pattern 1: Source-contract tests for GPU-importing pipeline files
**What:** `pipeline/*.py` is read as SOURCE TEXT (ast/regex), never imported — the tests/test_run_finetune_contracts.py discipline. The peft/probe/curve passthroughs are pinned this way CPU-side.
**When to use:** every run_finetune/run_sweep behavioral contract that does not need execution.
**Anchor:** [VERIFIED: tests/test_run_finetune_contracts.py:6-10 — "read as SOURCE TEXT and never imported: it does `import torch` / `from dnallm import ...` at module level"].

### Pattern 2: Fake-executor seam for sweep extensions
**What:** `run_matrix(cells, output_root, executor=None)` injects the launcher (run_sweep.py:702-744); tests inject fakes. `--curve`/`--peft` cell expansion is validated purely through enumeration + manifests.
**Anchor:** [VERIFIED: run_sweep.py:702-707, 736-744].

### Pattern 3: Skip-as-data disclosure rows (VEP + provenance + frontier)
**What:** Anything not computable becomes an explicit row with a machine-readable reason (suite VEP skip_reason; 7-missing-GUE rows; DL/EMPTY model exclusion rows; `Unspecified` provenance) — never silently dropped.
**Anchors:** [VERIFIED: vep.py:57-79 (VariantAlignment skip_reason); DATA.md:43-53].

### Pattern 4: Dual CSV+JSON artifacts + schema buckets
**What:** Every new downloadable (provenance, frontier, vep_zero_shot) mirrors n_audit.{json,csv} and gets a `schemas/*.json` + tests/test_schemas.py SCHEMA_FILES bucket in the same commit as first data.
**Anchor:** [VERIFIED: dnallm-mark/data/n_audit.{json,csv} exist; tests/test_schemas.py:24-42].

### Pattern 5: Alias names via save_model_name + suffix-stripping joins
**What:** Adapter/probe runs write under `{model}+lora` etc. using the existing `--save_model_name` (run_finetune.py:794); consumers strip the suffix for the metadata join (D-18 alias-normalization precedent), keep the alias for display.

### Anti-Patterns to Avoid
- **Reimplementing VEP scoring math**: the suite kernels + alignment rule + guard are the reviewed, tested implementation — reuse via lazy import.
- **Importing dnallm (or vep.py) at module level in any script/ or tests/ file**: breaks CI (torch absent). Lazy-import inside GPU paths only; mirror in ty config if a new GPU module appears (`replace-imports-with-any`, pyproject.toml:63-69).
- **Editing goldens by hand** when frontier/provenance/VEP artifacts land: chain-produced, schema-pinned.
- **Putting frac dirs beside seed dirs** in the curve layout: breaks resume-marker scoping (C2).
- **Hand-editing datasets_info.json provenance values as the source of truth**: CSV-edit → `--to-json --merge-existing` ingest with abort-on-wrong-count (D-10) is the path; JSON stays authoritative.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLM/MLM variant scoring | Custom log-likelihood loops | `dnallm.inference.vep` kernels (lazy import) | Same-slot rule, paradigm guard, skip accounting, ClinVar convention all tested in-suite (1,515-line test file) |
| VCF parsing | stdlib VCF reader | suite's `evaluate_vcf` (scikit-allel) | INFO typing, gzip, ALT dimensionality — never a hand-rolled reader (suite's own recorded decision) |
| PEFT target-module selection | Per-model target lists in OUR repo | suite `lora_targets.yaml` presets (30 families) + `peft_dry_run` | Suite presets cite per-family derivation provenance and carry ratio bands; ours would drift |
| Trainable-ratio validation | Our own param-count checks | suite `_guard_trainable_ratio` (runs automatically) | Already enforced-attach against preset bands |
| Statistics for any new aggregate | New CI math | vendored `aggregate_seeds` (export_runs) | One statistical vocabulary (05-RESEARCH Pattern 1) |
| SHA256 manifests | Custom hash format | `freeze_snapshot` / `sha256sum -c` line convention | Tested primitive + standard tooling re-verification |

**Key insight:** v1.2.1 moved almost all lane mechanisms INTO the suite with tests; our code's job is orchestration (registry driving, cell enumeration, config passthrough, artifact schema) — the part that stays CPU-testable.

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| GPU / host | NVIDIA GB10 present (nvidia-smi); this host IS the GB10 | none (smoke tasks may target it directly) |
| Python env (.venv) | Python 3.13.16; numpy 2.5.3, pandas 2.3.3 (data group); jsonschema/pytest/ruff/ty (dev); **torch, transformers, peft, datasets, dnallm ALL absent** | adaptation plan: sanctioned `uv sync --group gpu` + local-clone dnallm install task |
| System python3 | 3.14.7 (homebrew), no numpy/pandas — NOT the project env | none (always use .venv / uv) |
| pipeline/models/ | **does not exist** (never created on this machine) | smoke tasks that need a real model must fetch one small model (sanctioned); decide which tiny model (e.g. a small PlantDNABERT/NT class from ModelScope per models_info rows) |
| pipeline/datasets/ | EXISTS with content (BEND, Deep4mC_datasets, Genomic_Benchmarks, ... — the gitignored local tree) | env_smoke check-4 will enumerate any missing dirs (7 GUE known) |
| Suite repo | /home/forrest/Github/DNALLM on branch `dev` @ 98f7aa5; `dnallm/` + pyproject IDENTICAL to tag v1.2.1 (verified by empty diff); working tree clean for dnallm/ | pin installs/verifications to the v1.2.1 tag; repo is actively moving (branch changed mid-session) |
| Derived data | data-v1.1.0 committed (manifest.json: data_version "1.1.0", generated_from 9918046..., date 2026-10-10); 4 comparisons + tasks.json + task_performance/ + n_audit + permutation_tests.json | snapshot target freezes exactly this set |
| Dead JS logic | `recalculateComparison` at dnallm-mark/js/data.js:232, zero callers | dedicated early removal commit |
| Zenodo record 19135551 | still preview-token-only (public record 404, re-verified 2026-10-11 per CONTEXT) | DOI swap stays prepared-not-executed |
| seed_stats/ | `dnallm-mark/data/seed_stats/` does not exist yet (export_runs default out-dir; E2' product) | no action; exporter tolerant reader must not assume it |

## Common Pitfalls

### Pitfall 1: `use_lora=True` without a `lora:` YAML section
**What goes wrong:** `KeyError: 'lora'` at trainer construction (trainer.py:421 indexes `config["lora"]` directly).
**Why it happens:** IA³ defaults gracefully (`config.get("ia3", Ia3Config())`) so the asymmetry is non-obvious.
**How to avoid:** the peft plan adds the `lora:` section to finetune_config.yaml in the same change as the `--peft` flag; a source-contract test pins the section's presence.
**Warning signs:** GPU smoke dying at DNATrainer init with KeyError.

### Pitfall 2: CI/torch boundary breached by "just one import"
**What goes wrong:** `from dnallm.inference.vep import ...` at module top of zero_shot_vep.py, or a test importing it — CI dies (torch not installed; REL-02).
**Why it happens:** vep.py/configs.py look import-light but transitively pull torch (dnallm/__init__ imports .models/.finetune unconditionally).
**How to avoid:** lazy import inside the run path; injectable scorer seam for tests; ty `replace-imports-with-any` covers the GPU module statically.
**Warning signs:** local .venv tests pass (if torch got installed for smoke!) while CI reds — keep smoke env and CI env mentally separate; run `make ci` locally before commit.

### Pitfall 3: Adapter/probe/frac runs colliding with resume markers or the exporter walk
**What goes wrong:** alias cells written under the base model name (or frac dirs beside seed dirs) make `trainer_state.json` skip logic and `load_run_records`' `{model}/{task}/seed_{n}` walk (export_runs.py:438-450) mis-attribute runs.
**Why it happens:** the layout contract is implicit in three readers (run_finetune resume, run_sweep skip, export walk).
**How to avoid:** aliases via save_model_name (full dir separation); frac dirs nested UNDER seed; extend `_SEED_DIR_PATTERN`-adjacent logic deliberately with contract tests.
**Warning signs:** exporter picking up `frac_0.25` dirs as garbage model rows.

### Pitfall 4: provenance values presented as verified when they are research-drafted
**What goes wrong:** license/citation guesses get committed as fact.
**Why it happens:** 50 datasets × 6 fields is a research-heavy table.
**How to avoid:** the draft CSV lands with `Unspecified` defaults everywhere unresolved; the maintainer-review checkpoint gates publication (CONTEXT Q2); generator stamps "reviewed" state from a manifest field if desired.
**Warning signs:** any non-`Unspecified` value without a source link.

### Pitfall 5: snapshot hash derivation shelling git inside the data path
**What goes wrong:** `make snapshot` run from a tarball-exported tree (the SI/deposition scenario) gets `git: not found` → hash None → wrong artifact names.
**Why it happens:** freeze_snapshot takes `--commit-hash` as a string precisely to avoid this.
**How to avoid:** default hash = `manifest.json`'s `generated_from` (committed constant); `git rev-parse` only as an explicit override.
**Warning signs:** snapshot-None.tar outputs.

### Pitfall 6: goldens/schema/data three-way skew when new artifacts land
**What goes wrong:** frontier/provenance/VEP artifacts added without schema buckets or with hand-adjusted goldens.
**How to avoid:** Phase-2 SC-6 discipline — schema + data + re-chained goldens in one commit; drift-gated via `make data` where the artifact is in the regeneration chain.
**Warning signs:** CI drift job reds on merge.

### Pitfall 7: env_smoke contract drift after the sanction
**What goes wrong:** the docstring still says agents may never execute it while plans now carry execution tasks — a future agent refuses (or worse, treats execution as out-of-contract) .
**How to avoid:** amend the env_smoke docstring + the 0.8.0→1.2.1 labels in the adaptation commit itself.

## Code Examples

### peft enablement (our run_finetune passthrough — verified target surface)
```python
# Source: dnallm/finetune/trainer.py:369-376, 407, 421 (v1.2.1) + configs.py:326-334
# LoRA: constructor kwarg (NOT a config field); lora: YAML section REQUIRED
trainer = DNATrainer(
    model=model,
    config=configs,          # configs["lora"] must exist when use_lora=True
    datasets=dataset,
    extra_args=extra_args or None,
    use_lora=(peft_mode == "lora"),
)
# IA3: TrainingConfig field; ia3: YAML section OPTIONAL (defaults + presets)
if peft_mode == "ia3":
    configs["finetune"].use_ia3 = True
```

### minimal YAML sections (validated field lists)
```yaml
# Source: dnallm/configuration/configs.py:400-423, 436-478 (defaults verbatim)
lora:
    r: 8                 # LoRA attention dimension (rank)
    lora_alpha: 16
    target_modules: null # null => suite preset auto-selection (lora_targets.yaml)
    lora_dropout: 0.1
    bias: "none"         # none|all|lora_only
    task_type: "SEQ_CLS"
ia3:
    target_modules: null # null => suite preset
    feedforward_modules: null  # preset fills; must stay a subset of target_modules
    task_type: "SEQ_CLS"
```

### frozen probe (suite-native)
```yaml
# Source: configs.py:14-17 (frozen field) + model.py:101-103 (freeze loop)
task:
    head_config:
        head: "mlp"
        frozen: true      # freezes self.backbone.parameters() at construction
        hidden_dims: [512]
```

### seed_result.json tolerant reader (exporter extension sketch)
```python
# Source shapes verified: sweep.py:314-324 (suite writer) — fields:
#   {"model_name", "task_name", "seed", "timestamp", "metrics"}
def _read_seed_result(seed_dir: Path) -> dict | None:
    path = seed_dir / "seed_result.json"
    if not path.exists():          # tolerant: absent => not evidence
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("metrics") or None   # merged as per-seed evidence
```

### frontier row derivable fields
```python
# Sources: run_sweep.py:663-682 (record fields), export_runs.py:494-499 (total_flos hard-required)
{
    "model": "plant-dnabert-6mer+lora",     # alias display name
    "base_model": "plant-dnabert-6mer",     # suffix-stripped join key
    "method": "lora",                        # from run_record["peft"]
    "trainable_params_pct": 0.32,            # NEW: persisted by run_finetune post-attach
    "wall_hours": 1.84,                      # finished_at - started_at
    "total_flos": 1.2e17,                    # existing metrics requirement
    "score_delta": -0.004,                   # adapter vs full-run export join
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| IA³ "suite-support-gated last" (roadmap pre-decision) | Suite-native IA³ symmetric to LoRA (use_ia3 + ia3: section + presets) | dnallm v1.2 revision (92a8106, 2026-10-10) | IA³ lane unconditioned; one shared mechanism |
| Lane verification = fake-executor only (D-05) | Smoke sanction incl. GB10 GPU (2026-10-11) | maintainer directive this session | Plans gain bounded real-execution tasks; E2' still gated |
| VEP lane = design our own scorer | Suite ships full VEP core (vep.py + CLI + presets) | v1.2 revision | Our script becomes a driver; reuse kernels |
| Zero-shot VEP per CONTEXT: "no GPU-path integration" | Sanctioned GPU smoke allowed for VEP tiny-model verification | 2026-10-11 directive | Keep the offline-driver architecture; add optional smoke task |

**Deprecated/outdated within our repo:** env_smoke docstring's 0.8.0 labels + agent-prohibition contract (amend in plan 1); run_finetune inline "@ revision 483a35c" citations (refresh to v1.2.1 in plan 1).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | peft resolves to a version whose IA3Config accepts the suite's field set (suite's frozenset filter handles 0.14-0.21 span; latest ~0.21.x per docs banners) | A1/B | Older peft drops exclude_modules silently (suite-filtered by design); acceptable — verify version printed in smoke |
| A2 | The `[gpu]`+dnallm install on GB10 completes cleanly (bounds verified on paper; jax/modelscope/bitsandbytes are heavy but standard) | A4 | Install failures surface in the sanctioned smoke task — that is the task's purpose; no plan dependency blocked |
| A3 | `evaluate_vcf` performance over 62 models is acceptable at E2' time (one window per variant pair, context_window 200) | D | If too slow, batch windows or subset the cohort — a maintainer decision at run time, not a mechanism change |
| A4 | Frozen-probe lane scope excludes the 5 deeplearning_models (special loaders bypass generic head path) | C1 | If a special model turns out head-capable, scope can widen — mechanism unchanged |
| A5 | Curve fractions should shuffle-then-select with the cell seed (rather than first-N) | C2 | First-N is cheaper and deterministic; planner picks — both are defensible; document the choice |
| A6 | Tiny-model choice for GB10 smokes (a small ModelScope/HF model from the registry rows) is resolvable at plan time | Runtime State | If no small model is conveniently fetchable, smoke tasks fall back to peft_dry_run-style checks that still load a real backbone |

**Claims tagged [ASSUMED] elsewhere:** none material — every other claim carries a [VERIFIED: path:lines] or [CITED: url] anchor inline.

## Open Questions

1. **Frontier + VEP artifact publication surface** — do `frontier.*` / `vep_zero_shot.*` / `provenance.*` become leaderboard-downloadable data files (linked from pages like n_audit) or docs-only artifacts until real numbers exist post-E2'?
   - What we know: n_audit precedent is linked from DATA.md and downloadable from the site; frontier/VEP have synthetic-fixture-only content until E2'.
   - Recommendation: commit schema'd EMPTY-or-synthetic-marked artifacts only where CI needs them (fixtures), and gate site links on real data — planner decides per artifact; both fit the CONTEXT envelope.
2. **Snapshot output dir committed vs gitignored** — `baseline/snapshots/` tars are deposition artifacts (gitignore) but the `.sha256` manifest could be committed as tamper-evidence.
   - Recommendation: commit manifests, ignore tars (mirrors baseline/data-v1.sha256 being committed); maintainer taste wins if it surfaces in review.

Neither blocks planning; both are within Claude's-discretion envelopes (exact artifact placement).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| GB10 GPU | smoke tasks | ✓ (this host) | NVIDIA GB10 | — |
| .venv (uv-managed) | all CPU work | ✓ | Python 3.13.16, numpy 2.5.3, pandas 2.3.3 | — |
| torch/transformers/peft/dnallm | GPU-path smoke + lane verification | ✗ (not installed; sanctioned to install) | — | install task in plan 1 (uv sync --group gpu + local-clone dnallm) |
| pipeline/models/ | any smoke needing a real backbone | ✗ (dir absent) | — | fetch one small model (sanctioned); peft_dry_run checks still need a real model |
| pipeline/datasets/ | env_smoke check 4 | ✓ (partial; 7 GUE known-missing) | local tree | none needed — check is informational for the known gate |
| node ≥18 | JS test lane (dead-code removal proof) | ✓ (Makefile check-node guard) | — | — |

**Missing dependencies with no fallback:** none blocking — the GPU stack gap is exactly what the sanctioned plan-1 install task closes.
**Missing dependencies with fallback:** real-model smokes can degrade to peft_dry_run + tiny-fetch decisions at plan time (A6).

## Security Domain

`security_enforcement` is enabled (level 1). Phase-6 surface:

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | static site, no auth |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | provenance CSV ingest = untrusted-data parse-only discipline (abort-on-wrong-count, no eval); VCF/reference fixtures parsed by scikit-allel, never hand-rolled; registry values never reach a shell (argv LIST, T-03-10 continuity for new flags) |
| V6 Cryptography | yes (integrity only) | SHA-256 manifests via hashlib (freeze_snapshot._sha256_file) — never hand-rolled hashing |

| Threat Pattern | STRIDE | Standard Mitigation |
|-----------------|--------|---------------------|
| Provenance CSV formula/CSV-injection into maintainer spreadsheets | Tampering | neutral quoting on export; values are data, documented as never executed |
| Dataset/VEP fixture content treated as code (planted modules) | Tampering/Elevation | fixtures live under tests/fixtures authored by us; downloaded models go to fresh dirs; untrusted-input-boundary discipline (no interpreter run from inside data dirs) |
| DOI-swap script rewriting README out of scope | Tampering | refuse-unless-public check + same-commit allowlist removal (WR-01); maintainer-executed |
| Snapshot manifest forgery | Repudiation | SHA-256 + frozen commit hash; re-verify via `sha256sum -c` |

## Sources

### Primary (HIGH confidence — read this session)
- /home/forrest/Github/DNALLM @ v1.2.1 (= working tree; empty diff verified): `dnallm/finetune/trainer.py`, `dnallm/finetune/sweep.py`, `dnallm/configuration/configs.py`, `dnallm/configuration/presets/lora_targets.yaml`, `dnallm/models/model.py`, `dnallm/models/tokenizer.py`, `dnallm/inference/vep.py`, `dnallm/cli/vep.py`, `dnallm/__init__.py`, `pyproject.toml`, `tests/conftest.py`, `tests/inference/test_vep.py`
- dnallmmark: `pipeline/run_finetune.py`, `pipeline/run_sweep.py`, `pipeline/env_smoke.py`, `pipeline/finetune_config*.yaml`, `pipeline/{models,datasets}_info.json`, `pipeline/eval_subsets.json`, `pipeline/sweep_priorities.json`, `script/export_runs.py`, `script/convert_registry.py`, `script/freeze_snapshot.py`, `dnallm-mark/js/data.js`, `dnallm-mark/data/manifest.json`, `README.md`, `.gitleaks.toml`, `Makefile`, `pyproject.toml`, `DATA.md`, `tests/*`
- git state of both repos (tags, branches, diffs) — verified this session

### Secondary (MEDIUM confidence)
- [peft IA3 docs](https://huggingface.co/docs/peft/package_reference/ia3) + [peft ia3 config source v0.19.0](https://github.com/huggingface/peft/blob/v0.19.0/src/peft/tuners/ia3/config.py) + [peft PR #2102 exclude_modules](https://app.semanticdiff.com/gh/huggingface/peft/pull/2102/overview) — field surface cross-check
- [A Geometric Perspective on Zero-Shot VEP](https://openreview.net/pdf?id=2BsTU6MuzC), [evo2 preprint](https://www.biorxiv.org/content/biorxiv/early/2025/02/21/2025.02.18.638918.full.pdf), [Benegas GPN-MSA](https://www.zoology.ubc.ca/~otto/veg/Readings/Benegas2025.pdf), [PlantCAD2](https://www.cell.com/cell-genomics/fulltext/S2666-979X(26)00191-6) — MLM log-odds vs causal LLR conventions, RC asymmetry

### Tertiary (LOW confidence)
- None used for load-bearing claims.

## Metadata

**Confidence breakdown:**
- peft/VEP/frozen/seed_result surfaces: HIGH — read directly in the v1.2.1-verified tree with verbatim quotes
- Lane integration shapes (B/C/D recommendations): HIGH on anchors, MEDIUM on the recommendation details (planner's discretion envelope)
- Packaging paths (E): HIGH — every named file read this session
- External conventions (peft versions, VEP literature): MEDIUM — official docs/preprints, not registry-verified versions

**Research date:** 2026-10-11
**Valid until:** 2026-11-10 (suite repo is actively moving — re-pin by tag v1.2.1, not branch; 30-day window)
