---
phase: quick-261014-l6h
plan: 01
subsystem: dnallm-channel adaptation (registry alignment + download queue + machine env)
tags: [dnallm, modelscope, registry, download-queue, environment]
requires:
  - "DNALLM sibling clone at ../DNALLM branch dev @ cd4be43 (read-only)"
  - "261014-c2l/dcl/f4w quick tasks (directories_config, run-config threading)"
  - "261014-ir9 (59-entry official registry)"
provides:
  - "pipeline/dnallm_compat.json — the dnllm_adapted verdict map the next quick task's slot-2 model-download screen + default-list filter consumes"
  - "script/audit_dnallm_compat.py — the offline regen path for the compat map + modelscope/huggingface ID alignment"
  - "DownloadQueueService dataset_root param + _datasets_base() chain (param > tolerant file > repo default) at all six landing sites"
  - ".venv carrying torch 2.11.0+cu130 + modelscope 1.40.2 + dnallm 1.2.1 editable (machine-local, pyproject/uv.lock untouched)"
  - "pipeline/models/plant-dnamamba-6mer landed through dnallm.models.model.download_model (gitignored)"
affects:
  - "pipeline/models_info.json (5 ID value lines corrected to dnallm authority)"
  - "Makefile lint explicit list"
  - "the maintainer's 2x2 training smoke (TUI slot 4 / CLI) — presence + dry-run proven here, launch is the maintainer's"
tech-stack:
  added: []
  patterns:
    - "functools.partial-bound modelscope snapshot_download as the dnallm download_model downloader (cache_dir not threaded by the wrapper — bind via partial)"
    - "importlib.util file-path load of the sibling clone's MODEL_INFO (no dnallm install needed for the audit)"
    - "tolerant directories_config seam at the service tier (run_config.py precedent), strict lane stays pipeline-only"
key-files:
  created:
    - script/audit_dnallm_compat.py
    - pipeline/dnallm_compat.json
    - tests/test_dnallm_compat.py
  modified:
    - pipeline/models_info.json
    - tui/services/download_queue.py
    - tests/tui/test_services_download_queue.py
    - Makefile
decisions:
  - "Compat map verdicts: 36 adapted / 23 unadapted over exactly the 59 registry keys; the executor's re-derived counts matched the planning-time expectation exactly (incl. gena-lm-bert-large-t2t staying unadapted — its family lists gena-lm-bert-base-large-t2t, a different basename)"
  - "The 5 authority fixes: modelscope slots ZhejiangLab-LifeScience/{DNABERT-2-117M, agro-nucleotide-transformer-1b, hyenadna-large-1m-seqlen-hf}; huggingface orgs pGenomeOcean/GenomeOcean-500M + JadenLong/MutBERT-Multi — surgical 5-line git diff, recipe roundtrip guarded inside the script"
  - "Channel vocabulary: modelscope-slot (MODEL_INFO slot non-None) vs modelscope-mirror (slot None, kept lgq12697/<basename> — dnallm's own load_preset_model default channel, source=modelscope)"
  - "Queue reroute is ADD-ALONGSIDE at the consumer: the pipeline/datasets default literal stays at _datasets_base(); registry reads + self._pipeline_dir stay repo-anchored"
  - "The plant-dnamamba-6mer card's custom remote code is transformers-5.17-incompatible (MambaCache import) — the NATIVE no-trust_remote_code MambaForCausalLM path loads cleanly (93.7M params); intel filed in deferred-items.md for the maintainer's smoke decision, no pipeline change in this task"
metrics:
  duration: 35 min
  completed: 2026-10-14
status: complete
actuals:
  tokens: 14077   # chars/4 over the realized c96a7e2..HEAD diff (56,310 chars); the plan's 70k estimate also covered the machine-local env/download work that produces no diff
  tasks: 3
  commits: 2      # MEASURED: git rev-list --count c96a7e2..HEAD
plan_head_before: c96a7e21cef55713b50147c9d97fe5137090c038
plan_head_after: acb50a4eb0a7e13069de2c3f5398f2ed74289ee4
---

# Phase quick-261014-l6h Plan 01: DNALLM channel adaptation (env + alignment audit + dataset-root reroute + 2x2 presence) Summary

**One-liner:** dnallm-authoritative ModelScope channel wired end-to-end — venv (torch cu130 + modelscope + dnallm editable), the 59-key dnallm_compat verdict map (36/23) with 5 surgical registry ID fixes, the download queue's dataset landing rerouted through param > tolerant-file > repo-default, and plant-dnamamba-6mer landed via download_model with the 4-cell dry-run manifest proven.

## Task 1 — Environment (L6H-01): machine-local, no commit

- `uv sync --group data --group dev --group tui --group gpu --inexact` → landed `torch==2.11.0+cu130` + `transformers==5.17.0` from the pinned cu130 index (GB10/ARM aarch64 wheels).
- Torch gate BEFORE any dnallm work: `2.11.0+cu130 True` (CUDA available on the GB10).
- `uv pip install modelscope` → modelscope 1.40.2 (+modelscope-hub 0.4.6, cffi/cryptography/pycparser) — plain uv pip, lockfile untouched.
- `uv pip install -e /home/forrest/Github/DNALLM` → dnallm 1.2.1, **Editable project location: /home/forrest/Github/DNALLM** (T-l6h-01: editable from the read-only sibling @ cd4be43, never a registry fetch). Torch stayed 2.11.0+cu130 through the install (pip resolved against the satisfied pin).
- Import-surface proofs, verbatim from the verify run:
  - `from dnallm import DNADataset, DNATrainer, load_config, load_model_and_tokenizer` — OK (the run_finetune.py:74 contract)
  - `from dnallm.models.model import download_model` — OK (retry wrapper, model.py:323)
  - `from modelscope.hub.snapshot_download import snapshot_download` — OK (the exact path dnallm's modelscope branch uses, model.py:462)
- `git diff --quiet pyproject.toml uv.lock` clean; `git -C ../DNALLM status --porcelain` empty at handoff.

**[Rule 1 - Bug] Plan verify literal vs the pinned wheel's version string:** the plan's gate asserted `torch.__version__ == '2.11.0'`, but the cu130-index wheel reports `2.11.0+cu130` (PEP 440 local suffix). uv.lock pins exactly `torch==2.11.0+cu130` from `https://download.pytorch.org/whl/cu130` for linux — the installed artifact IS the locked one. Corrected the gate to `startswith('2.11.0')` + `'+cu130' in version`. No code changed; gate-command fix only.

## Task 2 — Alignment audit + compat map + queue reroute (L6H-02/L6H-03): TDD, 2 commits

### TDD record

**RED (4b14ce5):** `uv run --group dev --group tui pytest tests/test_dnallm_compat.py -q` → **10 failed** (FileNotFoundError on the not-yet-generated pipeline/dnallm_compat.json; AssertionError on the four alignment locks) — every failure on the planned artifact/behavior, zero collection/fixture faults. Queue reroute: targeted run → **2 failed** (`test_file_dataset_root_redirects_spec_local_dir_and_gate_naming` failing on the local_dir assertion — config not yet read; `test_constructor_dataset_root_beats_file_key` failing with TypeError on the missing `dataset_root` kwarg) + 2 guard pins passing by design (byte-identity + corrupt-degrade are regression guards for GREEN, not new-behavior REDs).

**GREEN (acb50a4):** implementation below; `pytest tests/test_dnallm_compat.py tests/tui/test_services_download_queue.py` → **179 passed** (10 + 169; the queue file's true pytest count was 165 pre-task + 4 new — the plan's "144" was a grep-based count, the actual collected count is 169).

**REFACTOR:** none needed — the helper is single-purpose; the script's mirror-form check was already implemented with string ops over regex during GREEN.

### What landed

- **script/audit_dnallm_compat.py** (new): stdlib-only audit; loads MODEL_INFO from `../DNALLM/dnallm/models/modeling_auto.py` via `importlib.util` file-path import (the module imports only `collections`); `--dnallm-root` defaults to `../DNALLM` resolved from `__file__` (never CWD); encodes the five authority rules; refuses to write when the serialization recipe (`json.dumps(doc, indent=4, ensure_ascii=False, sort_keys=True)` + trailing newline) does not roundtrip the CURRENT models_info.json byte-identically; records `dnallm_commit` via `git -C <root> rev-parse HEAD`.
- **pipeline/dnallm_compat.json** (new): schema 1, `dnallm_commit cd4be4399367cbc324eb9c8ac3e9d62d4ed2469a`, exactly the 59 registry keys — **36 adapted / 23 unadapted**, matching the planning-time expectation member-for-member (unadapted set: CrossDNA x3, FungiHelixSeek, PlantBiMoE, PlantDNAMamba2-BPE, PlantGFM, PlantHelixSeek, SPACE + space, Shorkie_LM, SpeciesLM x2, borzoi/flashzoi-replicate-0, denseSSM/mamba2 x3, enformer, evo2_1b_base (no MODEL_INFO entry at dev HEAD), plant-genomic-jamba (family commented out at dev HEAD), prokbert (bare entry), gena-lm-bert-large-t2t (different basename from its family's gena-lm-bert-base-large-t2t)).
- **pipeline/models_info.json**: the 5 authority fixes — surgical `git diff`: exactly 5 changed value lines, zero reflow:

  | entry | field | before -> after |
  |---|---|---|
  | DNABERT-2-117M | modelscope | lgq12697/DNABERT-2-117M -> **ZhejiangLab-LifeScience/DNABERT-2-117M** (slot) |
  | agro-nucleotide-transformer-1b | modelscope | lgq12697/... -> **ZhejiangLab-LifeScience/agro-nucleotide-transformer-1b** (slot) |
  | hyenadna-large-1m-seqlen-hf | modelscope | lgq12697/... -> **ZhejiangLab-LifeScience/hyenadna-large-1m-seqlen-hf** (slot) |
  | GenomeOcean-500M | huggingface | DOEJJI/GenomeOcean-500M -> **pGenomeOcean/GenomeOcean-500M** (org) |
  | MutBERT-Multi | huggingface | CompBioDSA/MutBERT-Multi -> **JadenLong/MutBERT-Multi** (org) |

  Audit idempotency proven: second run reports `0 field fix(es)`, files byte-stable.
- **tui/services/download_queue.py**: constructor gains `dataset_root=None` (resolved Path, the flag tier); ONE `_datasets_base()` helper (param > `directories_config.load_directories_tolerant().get("dataset_root")` > `self._pipeline_dir` — tolerant, the run_config.py service-tier seam; a corrupt file degrades, never SystemExit); all SIX landing sites rerouted (ChannelSpec local_dir ~2473, landing gate ~1679, shape-C rename ~1708, zenodo extract ~1884, landed-keys scan ~1955, reconcile staged absolute Dataset_path ~2023). Deliberately NOT rerouted: `self._pipeline_dir` itself and the datasets_info.json registry read (~2580) — registry is repo state.
- **tests**: tests/test_dnallm_compat.py (10 CI-safe pins — no dnallm import, no ../DNALLM access) + 4 queue reroute tests + the module autouse config-root pin (tmp_path_FACTORY idiom — the byte-identity proof lane).
- **Makefile**: `script/audit_dnallm_compat.py` joins the lint explicit list via the `QUICK_L6H_SCRIPTS` existence-guard group.

### Gates

- `make lint` green; `make typecheck` green (ty covers the new script + the queue reroute).
- Targeted suites: `tests/test_dnallm_compat.py tests/tui/test_services_download_queue.py tests/test_model_registry.py tests/test_registry_unification.py` → **187 passed**.
- Full `make test`: **1697 passed / 7 failed / node lane 26/26**. Failure accounting vs the documented baseline: 6 documented baseline failures present (5 test_schemas + 1 test_determinism, the post-9bc68e1 stale pins); the 4 root-user chmod persist-failure sims are GREEN on this non-root machine (environmentally green, exactly as c2l's deferred-items predicts); **1 failure beyond the documented set — proven pre-existing machine state, see Deviations**. The known snapshot flake did not strike this run.

## Task 3 — Download + presence + dry-run (L6H-04/L6H-05): machine-local, no commit

Precondition re-asserted: `import dnallm, modelscope` OK (survived the Task-2 uv-run lanes — uv run's inexact sync, the Phase-7 A4 practice); compat map lists plant-dnamamba-6mer adapted / zhangtaolab slot / modelscope-slot channel.

- **The download invocation** (throwaway script under /tmp, `python -I`, never committed — reuse this exact shape in the slot-2 feature):

  ```python
  from functools import partial
  from modelscope.hub.snapshot_download import snapshot_download
  from dnallm.models.model import download_model

  landing = "/home/forrest/Github/dnallmmark/pipeline/models/plant-dnamamba-6mer"
  downloader = partial(snapshot_download, cache_dir=landing)  # cache_dir rides the partial
  download_model("zhangtaolab/plant-dnamamba-6mer", downloader=downloader)
  ```

- **Landing normalization** (the anticipated modelscope 1.40.2 nesting): files landed under `models/zhangtaolab--plant-dnamamba-6mer/snapshots/master/` + a `.lock/` dir; hoisted the snapshot contents (real files, no symlinks) with mv to the dir root and removed the scaffolding. Final: `pipeline/models/plant-dnamamba-6mer/config.json` DIRECT (the run_finetune model_base "pipeline/" + Model_path "models/plant-dnamamba-6mer" resolution target) + tokenizer_config.json/special_tokens_map.json/vocab.txt + model.safetensors (375M) + pytorch_model.bin. No org-level sibling dirs under pipeline/models/ (only plant-dnabert-6mer, plant-dnagpt-BPE, plant-dnamamba-6mer).
- **CPU probes** (mamba-ssm NOT installed — import fails as expected):
  - `AutoConfig.from_pretrained(local, trust_remote_code=True)` → **MambaConfig, model_type=mamba** OK
  - `AutoTokenizer.from_pretrained(local, trust_remote_code=True)` → **EsmTokenizer, vocab 4107**, encode probe OK
  - Optional full-load (safetensors 375M < ~1GB bar): with trust_remote_code=True the CARD's custom `modeling_mamba.py` FAILS on transformers 5.17 (`ImportError: cannot import name 'MambaCache' from 'transformers.cache_utils'`); the NATIVE pure-PyTorch path — `AutoModelForCausalLM.from_pretrained(local)` WITHOUT trust_remote_code — loads cleanly: **MambaForCausalLM, 93.7M params** (registry says 94M). Filed as maintainer smoke intel in deferred-items.md (dnallm's own loader is trust_remote_code throughout — model.py:1050/1074).
- **2x2 presence**: all four targets verified — pipeline/models/plant-dnabert-6mer (config.json), pipeline/models/plant-dnamamba-6mer (config.json), pipeline/datasets/PDLLMs_datasets/plant-multi-species-open-chromatin/{train,dev,test}.csv, pipeline/datasets/plant-genomic-benchmark/gene_exp.arabidopsis_thaliana/{train,dev,test}.csv.
- **Dry-run**: `run_sweep.py --dry-run --models plant-dnabert-6mer,plant-dnamamba-6mer --tasks PDLLMs_datasets__plant-multi-species-open-chromatin,plant-genomic-benchmark__gene_exp.arabidopsis_thaliana --seeds 42 --output-root pipeline/finetuned/l6h-dryrun` → manifest at pipeline/finetuned/l6h-dryrun/sweep_manifest.json (gitignored, D-26) holding exactly the 4 planned cells (each model x each task, seed 42). Full verify block rerun verbatim: `L6H-05 OK: 4-cell manifest`.
- Working tree at handoff: zero tracked changes beyond `.planning/`; DNALLM sibling clean.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] torch version literal in the Task-1 verify gate**
- **Found during:** Task 1 verify
- **Issue:** the gate asserted `torch.__version__ == '2.11.0'` but the locked cu130 wheel reports `2.11.0+cu130`; uv.lock itself pins `2.11.0+cu130` from the pytorch-cu130 index — the gate literal was a planning slip, not an environment problem.
- **Fix:** corrected the assertion (startswith + cu130 suffix check); no files changed, gate command only.

**2. [Rule 3 - Blocking] lint/ty findings in the new audit script**
- **Found during:** Task 2 gates
- **Issue:** F401 (unused `re` after implementing the mirror-form check with string ops), PLW1510 (subprocess.run without explicit check=False), and three ty Optionals on `importlib.util` spec/loader.
- **Fix:** removed the import, added `check=False`, added an explicit `spec is None or spec.loader is None` guard. Both gates green after.

### Out-of-scope discovery (documented, NOT fixed — the scope boundary)

**3. [Environmental] `test_storage_overview_defaults_mirror_real_consumers` fails on this machine**
- **Found during:** Task 2 full `make test`
- **Issue:** the f4w-authored test asserts `pipeline/logs` does not exist ("fresh checkout"); this GB10 machine carries gitignored run-log leftovers from the Phase-7 smoke (Oct 11) and a later local run (Oct 13). Proven mechanical: with `pipeline/logs` moved aside the test passes (1 passed, 0.04s); the directory was restored byte-for-byte immediately. The f4w full-suite evidence ran on the PREVIOUS machine (root user — hence its 4 chmod-sim failures), which lacked this state.
- **Fix:** none (would touch an unrelated f4w test file). Filed in deferred-items.md with a candidate hermetic-fix note for a future quick task.

## Auth Gates

None.

## Known Stubs

None — no stub patterns introduced; the compat map and reroute are fully wired.

## Next-step routing (per the plan's success criteria)

- **The maintainer launches the 2x2 training smoke** from TUI slot 4 (`p` preview -> `enter` gate) or CLI `run_sweep.py --models plant-dnabert-6mer,plant-dnamamba-6mer --tasks PDLLPs...` — READ deferred-items.md FIRST: the dnamamba card's remote code vs transformers 5.17 (MambaCache) likely ImportErrors inside dnallm's trust_remote_code load path; the native no-trust path is proven working, stripping the landed config's auto_map is the cheapest mitigation if the maintainer wants it.
- **The next quick task is the slot-2/3 split** consuming pipeline/dnallm_compat.json (slot 2 = models only: per-model download status + `d`-style download via the partial-bound dnallm channel shown above; slot 3 = datasets only, ModelScope default); the registry default list filter = dnllm_adapted models only.

## Self-Check: PASSED

- Files: script/audit_dnallm_compat.py FOUND; pipeline/dnallm_compat.json FOUND; tests/test_dnallm_compat.py FOUND; tui/services/download_queue.py FOUND (modified); pipeline/models_info.json FOUND (modified); Makefile FOUND (modified); tests/tui/test_services_download_queue.py FOUND (modified)
- Commits: 4b14ce5 and acb50a4 are ancestors of HEAD (verified via git merge-base --is-ancestor)
- SUMMARY written by the executor; docs commit handled by the orchestrator per the dispatch constraints
