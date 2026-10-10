---
phase: 06-revision-packaging-extended-lanes
plan: 01
subsystem: pipeline-adapter
tags: [dnallm-1.2.1, peft, lora, ia3, env-smoke, gb10, seed-result, exporter]
requires:
  - "dnallm suite repo at tag v1.2.1 (30dfd6d), read-only"
  - "[gpu] group pins (torch 2.11.0 cu130, transformers 5.17.0)"
provides:
  - "run_finetune --peft {none,lora,ia3} + --peft_dry_run (the SC-6 lane tracer surface 06-02/06-03/06-05 build on)"
  - "lora:/ia3: YAML sections in BOTH finetune configs (KeyError 'lora' impossible)"
  - "v1.2.1-refreshed suite citations + the attn_implementation='eager' pin note"
  - "env_smoke with gating peft check, 1.2.1 labels, amended smoke-sanction contract"
  - "export_runs._read_seed_result tolerant reader (absent=skip, present=merge under run_record precedence, malformed=loud abort)"
  - "proven GPU environment on this GB10 host: dnallm 1.2.1 (tag-archive install) + peft 0.21.2 + executed all-PASS env_smoke + both peft dry-runs"
affects:
  - "06-02 (peft lanes: alias/sweep/frontier depend on the tracer + installed env)"
  - "06-03 (VEP/curve lanes depend on the verified adaptation + env)"
  - "06-05 (response-letter packaging cites this plan's evidence)"
tech-stack:
  added:
    - "peft 0.21.2 (suite transitive, resolved by the dnallm 1.2.1 install; GPU-only)"
    - "dnallm 1.2.1 installed into .venv from git-archive v1.2.1 content (non-editable; NOT a repo/CI dependency)"
  patterns:
    - "source-contract tests extended to the peft wiring + env_smoke surface (read-source-never-import)"
    - "tolerant-reader trio (absent/present/malformed) mirroring the run_record abort discipline"
key-files:
  created: []
  modified:
    - pipeline/run_finetune.py
    - pipeline/env_smoke.py
    - pipeline/finetune_config.yaml
    - pipeline/finetune_config_with_head.yaml
    - script/export_runs.py
    - tests/test_run_finetune_contracts.py
    - tests/test_export_runs.py
decisions:
  - "peft=none default path kept byte-identical (mode-guarded mutations + pure-comparison ctor kwarg), contract-pinned so the tracer cannot alter non-lane behavior"
  - "malformed seed_result aborts split into ValueError (parse/shape) and TypeError (isinstance checks) per ruff TRY004 — no suppression widened"
  - "dnallm installed from git-archive v1.2.1 content in /tmp scratch (never editable, never the suite tree); maintainer may switch to editable post-milestone"
  - "REV-05/REV-08 NOT marked complete: they span 06-01/02/03/05; the final carrier (06-05) owns the mark"
metrics:
  duration: "~33 minutes"
  completed: "2026-10-11"
estimate_provenance: "plan estimate: 60000 tokens / 3 tasks"
actuals:
  tokens: 12800     # chars/4 over git diff 83bdbaf..HEAD (51317 chars)
  tasks: 3
  commits: 5        # MEASURED: git rev-list --count 83bdbaf..HEAD
plan_head_before: 83bdbaf6445825c860e7554f28b141ec56fd2623
plan_head_after: 07aacf0f5f9caa82555689bc52b1d590248525b0
status: complete
---

# Phase 06 Plan 01: dnallm 1.2.1 adaptation verification + peft tracer + sanctioned GB10 smoke Summary

**One-liner:** Re-pinned every suite citation to tag v1.2.1, wired the `--peft/--peft_dry_run` tracer through argparse → YAML `lora:`/`ia3:` → `use_ia3` mutation → `use_lora` ctor kwarg under source-contract proof, added the exporter's tolerant `seed_result.json` reader, and EXECUTED the sanctioned GB10 smoke to an all-PASS env_smoke plus both peft dry-runs on a real plant-dnabert-6mer backbone.

## What Was Built

### Task 1 — 1.2.1 alignment + peft tracer (3 commits)

**Commit 7719889 (chore):** the six quirk registries re-verified against tag v1.2.1 (read-only: save_safetensors flows via `training_args.pop` at trainer.py:534 into both save sites :798-876; `trust_remote_code` unconditional in every model.py load path; `allow_test_as_eval` semantics intact at configs.py:317-325; the transformers-v5 tokenizer fallback present at tokenizer.py:256-270). The stale EVAL-01 citation re-anchored to `trainer.py L571-605 @ v1.2.1 (30dfd6d)`; zero `483a35c` strings remain in run_finetune.py; the model-loading region now documents the v1.2.1 `attn_implementation="eager"` hard pin (suite model.py:590-594) so no attention quirk list is ever added on our side.

**Commit 3872fea (feat):** `--peft {none,lora,ia3}` (argparse choices, default none) + `--peft_dry_run` (store_true) mirroring the `--subset_file` seam shape; composition fail-fast (`[Error]` naming both flags) when dry-run arrives without an adapter mode, before the model loop; `configs["finetune"].use_ia3 = True` and `configs["finetune"].peft_dry_run = True` in the per-dataset quirk-mutation block BEFORE the ctor; `use_lora=(peft_mode == "lora")` at the DNATrainer ctor site; `lora:` (REQUIRED under use_lora — suite trainer.py:421 indexes `config["lora"]` directly) + `ia3:` (optional) sections with suite-validated fields only in BOTH YAMLs. No output naming/aliasing touched (adapter aliases are 06-02).

**Commit 1298eef (fix):** all six stale `dnallm 0.8.0` labels relabeled to 1.2.1 with facts re-checked against the v1.2.1 pyproject (datasets<=3.2.0 and numpy>=2 hold; the pyarrow cap claim DROPPED — v1.2.1 declares no pyarrow constraint); new gating check 7 (`import peft` + version, greppable PASS/FAIL, wired into main()'s results); the binding docstring contract amended with the 2026-10-11 smoke sanction boundary (executed smoke as explicit bounded plan TASKS on this GB10 host; py_compile no longer the only sanctioned proof; E2' still maintainer dual-gate; CI still GPU-free).

### Task 2 — seed_result.json tolerant reader (commit 286c56c)

`_read_seed_result(seed_dir)`: absent → silent skip (our run_sweep subprocesses never write the file — forward-compatible adoption); present → validates the ACTUAL suite writer shape (sweep.py:314-324 @ v1.2.1: `{model_name, task_name, seed, timestamp, metrics}`, metrics a dict) and returns the metrics block; malformed → loud abort naming the path (ValueError for parse/shape, TypeError for the isinstance checks — ruff TRY004). Hooked into `load_run_records`' seed loop merging under run_record precedence (our record stays the authority, the suite file supplements missing keys). `make data` verified no-op on the committed tree.

### Task 3 — the sanctioned GB10 smoke (commit 07aacf0 + environment)

- **(a) Tag pin:** `git -C /home/forrest/Github/DNALLM diff --stat v1.2.1..HEAD -- dnallm/ pyproject.toml` EMPTY (tag-exact); tag `v1.2.1` = `30dfd6d`.
- **(b) Install:** `uv sync --group gpu --group dev` → torch 2.11.0+cu130, transformers 5.17.0; dnallm installed with `uv pip install /tmp/dnallm-v1.2.1` where the tag content was extracted via `git archive v1.2.1` (non-editable; zero writes to the suite repo). Resolved: **dnallm 1.2.1, peft 0.21.2, numpy 2.5.3**.
- **(c) env_smoke EXECUTED:** all-PASS, exit 0 — verbatim output below.
- **(d) Model fetch (bounded):** plant-dnabert-6mer from huggingface `zhangtaolab/plant-dnabert-6mer` into `pipeline/models/plant-dnabert-6mer` (gitignored; one model only).
- **(e) peft dry-runs:** `--peft lora --peft_dry_run` and `--peft ia3 --peft_dry_run` on BEND__CpG_methylation (the verify picker's first locally-present task) — both validate-and-exit: preset resolved, matched-module report printed, NO training, NO checkpoints, exit 0. Verbatim outputs below.
- **(f) Read-only assertion:** `git -C /home/forrest/Github/DNALLM status --porcelain` empty at every checkpoint.

## Verbatim Evidence

### env_smoke (uv run --group gpu python pipeline/env_smoke.py) — exit 0

```text
=== PIPE-02 env smoke (dnallmmark @ /home/forrest/Github/dnallmmark) ===
PASS: import torch resolves (/home/forrest/Github/dnallmmark/.venv/lib/python3.13/site-packages/torch/__init__.py)
PASS: torch 2.11.0 == pyproject [gpu] pin
PASS: import transformers resolves (/home/forrest/Github/dnallmmark/.venv/lib/python3.13/site-packages/transformers/__init__.py)
PASS: transformers 5.17.0 == pyproject [gpu] pin
PASS: import dnallm resolves (/home/forrest/Github/dnallmmark/.venv/lib/python3.13/site-packages/dnallm/__init__.py)
PASS: peft 0.21.2 importable (SC-6 LoRA/IA3 lanes; suite floor peft>=0.14.0)
PASS: CUDA available, 1 device(s)
PASS: device 0: NVIDIA GB10, 121.6 GiB total memory
PASS: small-tensor matmul executed (sum == 512.0)
PASS: import numpy resolves (/home/forrest/Github/dnallmmark/.venv/lib/python3.13/site-packages/numpy/__init__.py)
PASS: numpy 2.5.3 >= pyproject floor (major >= 2; dnallm 1.2.1 requires numpy>=2)
INFO (not gated): datasets 5.1.0, pyarrow 26.0.0 (dnallm 1.2.1 caps datasets<=3.2.0, no pyarrow pin — dnallm's own constraints govern resolution)
PASS: all 50 registry dataset dir(s) present on disk
=== SMOKE RESULT: PASS (all checks green) ===
```

13 PASS lines, zero FAIL, exit 0. Full output: `/tmp/06-01-env-smoke.txt`.

### peft lora dry-run (from pipeline/) — exit 0, key lines verbatim

```text
[2026-10-11 02:18:26] Loading model: plant-dnabert-6mer
[2026-10-11 02:18:54] Index: BEND__CpG_methylation, Dataset: BEND__CpG_methylation
Tokenizer type: 6mer. Infer max token length: 87
[Info] LoRA preset 'Plant DNABERT' selected (matched by name marker 'plant-dnabert'): target_modules=['query', 'value']
[Info] PEFT dry run: 24 modules matched target_modules ['query', 'value']: bert.encoder.layer.0.attention.self.query, bert.encoder.layer.0.attention.self.value, bert.encoder.layer.1.attention.self.query, bert.encoder.layer.1.attention.self.value, bert.encoder.layer.2.attention.self.query, bert.encoder.layer.2.attention.self.value, bert.encoder.layer.3.attention.self.query, bert.encoder.layer.3.attention.self.value, bert.encoder.layer.4.attention.self.query, bert.encoder.layer.4.attention.self.value ... and 14 more
[Info] PEFT dry run complete — no training performed.
[Info] Skipping the training loop: finetune.peft_dry_run=true.
[2026-10-11 02:22:25] Error finetuning dataset BEND__CpG_methylation with model plant-dnabert-6mer: max() iterable argument is empty
```

### peft ia3 dry-run (from pipeline/) — exit 0, key lines verbatim

```text
[2026-10-11 02:23:24] Loading model: plant-dnabert-6mer
[2026-10-11 02:23:31] Index: BEND__CpG_methylation, Dataset: BEND__CpG_methylation
[Info] IA³ preset 'Plant DNABERT' selected (matched by name marker 'plant-dnabert'): target_modules=['key', 'value', 'intermediate.dense']
[Info] PEFT dry run: 36 modules matched target_modules ['key', 'value', 'intermediate.dense']: bert.encoder.layer.0.attention.self.key, bert.encoder.layer.0.attention.self.value, bert.encoder.layer.0.intermediate.dense, bert.encoder.layer.1.attention.self.key, bert.encoder.layer.1.attention.self.value, bert.encoder.layer.1.intermediate.dense, bert.encoder.layer.2.attention.self.key, bert.encoder.layer.2.attention.self.value, bert.encoder.layer.2.intermediate.dense, bert.encoder.layer.3.attention.self.key ... and 26 more
[Info] PEFT dry run complete — no training performed.
[Info] Skipping the training loop: finetune.peft_dry_run=true.
[2026-10-11 02:24:34] Error finetuning dataset BEND__CpG_methylation with model plant-dnabert-6mer: max() iterable argument is empty
```

Both runs: exit 0, zero `checkpoint-*` directories anywhere under `pipeline/finetuned/` (only the empty `seed_9527` outdir shell created by the pre-check `os.makedirs`). The trailing "Error finetuning ... max() iterable argument is empty" line is run_finetune's own completion-glob finding no checkpoints after the suite's validate-and-exit — caught by the designed blind-except isolation, logged, and continued; exit stays 0. Observation for 06-02: the dry-run path could skip the completion-glob block for cosmetics, but behavior is correct as-is.

### Resolved versions (the acceptance-criteria record)

| Package | Resolved | Bound |
|---|---|---|
| torch | 2.11.0+cu130 | == [gpu] pin; in suite [2.4.0, 2.12) |
| transformers | 5.17.0 | == [gpu] pin; in suite [4.49.0, 6) |
| dnallm | 1.2.1 | tag-archive v1.2.1 (30dfd6d) content |
| peft | 0.21.2 | >= suite floor 0.14.0 |
| numpy | 2.5.3 | >= repo floor 2, == suite floor family |
| datasets | 5.1.0 | INFO-only (see Deviation 4) |

## Commits

| Task | Commit | Subject |
|---|---|---|
| 1 | 7719889 | chore(06-01): refresh suite citations to v1.2.1 + eager-pin note |
| 1 | 3872fea | feat(06-01): peft tracer wiring — flags, YAML sections, ctor kwarg, use_ia3 |
| 1 | 1298eef | fix(06-01): env_smoke 1.2.1 relabel + gating peft check + sanction amendment |
| 2 | 286c56c | feat(06-01): tolerant seed_result.json reader in the exporter |
| 3 | 07aacf0 | fix(06-01): env_smoke matmul constant — 512.0, not 64.0 (Rule 1) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] env_smoke matmul expected constant was wrong**
- **Found during:** Task 3(c), the first-ever EXECUTED env_smoke run
- **Issue:** `check_matmul` expected `(ones(8,8) @ ones(8,8)).sum() == 64.0`; the correct value is 512.0 (64 entries x 8 each). A latent defect py_compile could never catch — exactly what the sanctioned execution surfaced.
- **Fix:** constant corrected to 512.0 with the derivation documented in the docstring; contract-test surface unaffected.
- **Files modified:** pipeline/env_smoke.py
- **Commit:** 07aacf0

**2. [Rule 3 - Blocking env] 7 GUE dataset dirs missing on disk**
- **Found during:** Task 3(c) first run (check 4 FAIL: GUE__EPI_GM12878, fungi_species_20, human_tf_0, mouse_1, mouse_4, virus_covid, virus_species_40)
- **Issue:** the plan requires env_smoke ALL-PASS, but the documented 7-GUE re-extraction gate left those registry dirs absent.
- **Fix:** extracted the 7 task dirs from the LOCAL `pipeline/datasets/GUE.zip` (already on disk — no download, respecting the no-dataset-download boundary) into `pipeline/datasets/GUE/`. Gitignored local tree; committed data untouched. env_smoke then reported "all 50 registry dataset dir(s) present".
- **Files modified:** none in git (gitignored runtime tree)
- **Commit:** n/a (environment only)

### Interpretations (no plan contract changed)

**3. Tests distributed per-commit (TDD), not all-at-end.** The plan's action prose places the contract-test extension "finally"; each commit instead carried its own RED→GREEN tests (citation tests in 7719889, peft wiring tests in 3872fea, env_smoke tests in 1298eef) — the atomic-commit + TDD discipline taken literally. Same test surface at the end.

**4. datasets resolves to 5.1.0, above the suite cap <=3.2.0.** The project lock's `evaluate` dependency (data group) pins datasets 5.1.0, and every `uv run` implicit sync re-asserts it over the dnallm install's resolution. env_smoke's ecosystem line is NON-GATING by its own contract ("dnallm's own constraints govern resolution; this gate does NOT enforce them"), and both peft dry-runs + full data loading worked under 5.1.0. Flagged for the lane plans / E2' env work: if a suite path ever needs datasets<=3.2.0 semantics, the lock (evaluate's resolution) must be revisited — a maintainer-level decision, not silently changeable here.

**5. `uv sync --group gpu --group dev` (dev group added).** The plan's literal `uv sync --group gpu` would have removed the dev tools (uv sync is exact), breaking the quality gates mid-plan. Adding `--group dev` changes nothing about the GPU resolution; both plan-literal `uv run --group gpu ...` commands then worked verbatim (uv run's implicit sync is inexact — dnallm survives it; verified empirically).

**6. test_run_finetune_contracts.py's own stale EVAL-01 citation refreshed** (same shifted L568-605 range as run_finetune.py:677) for coherence with the file this task extends. `script/make_dev_splits.py:10` carries the same-form historical anchor but is outside the task's file list and self-consistent ("@ revision 483a35c" names the revision the range is valid FOR) — left untouched per the surgical-fix discipline. The vendored-stats provenance banners in export_runs.py are accurate historical records — untouched.

**7. REV-05/REV-08 NOT marked complete in REQUIREMENTS.md.** Both requirements span 06-01/06-02/06-03/06-05 (checked in each plan's frontmatter); this plan discharges only the adaptation-verification gate (SC-6's gating half). Marking them complete at plan 1 of 5 would falsify traceability — the final carrier plan (06-05) owns the mark.

## Verification Results

- `pytest tests/test_run_finetune_contracts.py -v`: 34 passed (was 25 at baseline; +9 new contract tests)
- `pytest tests/test_export_runs.py -v`: 26 passed (+4 seed_result tests)
- grep gates: zero `483a35c` in run_finetune.py; zero `0.8.0` in env_smoke.py
- `py_compile` both GPU-side files: OK
- `make lint` / `make typecheck`: clean (no widened suppressions)
- `make test`: 324 passed (+ node lane green)
- `make data` + porcelain on dnallm-mark/data/: no-op (drift gate green)
- Task 3 verify blocks 1-3 (env_smoke all-PASS >=7 PASS lines; literal lora dry-run command with dry-run report line; suite porcelain empty): ALL PASS
- Final suite-repo state: `git -C /home/forrest/Github/DNALLM status --porcelain` EMPTY

## Test Coverage

- New source-contract tests (tests/test_run_finetune_contracts.py): v1.2.1 citation pin (anchor + eager note placement), peft flag shapes, dry-run composition error before the model loop, ctor use_lora kwarg, guarded use_ia3/peft_dry_run mutation ordering (quirk-block placement, before ctor), peft=none no-op (alias construction untouched + every peft mutation mode-guarded), YAML section key surfaces in BOTH files with suite-default values, env_smoke zero-stale-labels + dropped pyarrow claim, sanction docstring phrases, gating peft check wiring.
- New exporter tests (tests/test_export_runs.py): absent-equivalence (deep-equal walk over on-disk records), merge + run_record precedence + downstream visibility (emitted performance block carries merged mcc; FLOPs keeps the run_record value), five malformed abort cases each naming the path (unparseable / non-object top level / missing metrics / metrics-not-dict / missing identity key), byte determinism with seed_result present.
- GPU-side proof is the executed smoke itself (env_smoke + both dry-runs) — by design never in `make test`/CI.

## Known Stubs

None. (The `--peft` tracer is a complete thin slice by design — alias/output-naming and sweep integration deliberately belong to 06-02, per the plan's specless-probe rows.)

## Self-Check: PASSED

All five commits verified as ancestors of HEAD (7719889, 3872fea, 1298eef, 286c56c, 07aacf0); all seven modified files exist on disk; commits measured at 5 via `git rev-list --count 83bdbaf..HEAD`.
