---
last_mapped_commit: a44d3104b8ab1e04ddbebed75446772fc0ca3f1b
last_mapped_at: 2026-10-08
---
# External Integrations

**Analysis Date:** 2026-10-08

## APIs & External Services

**Pretrained model registries:**
- Hugging Face Hub - source of truth for model IDs; every entry in `pipeline/models_info.json` has a `"huggingface"` field (e.g. `InstaDeepAI/agro-nucleotide-transformer-1b`, `zhihan1996/DNABERT-2-117M`). Referenced only as metadata/links — models are loaded from local `pipeline/models/` paths, not streamed from the Hub
  - SDK/Client: `transformers` `AutoModelForSequenceClassification.from_pretrained(..., trust_remote_code=True)` fallback at `pipeline/dnallmmark_pipeline.py:880-898`
  - Auth: none required (local loading)
- ModelScope - mirror registry; every `models_info.json` entry also carries a `"modelscope"` field (e.g. `lgq12697/agro-nucleotide-transformer-1b`). Displayed as outbound links in `dnallm-mark/models.html` via `dnallm-mark/js/models.js:136-137`; optional cache env `MS_CACHE_HOME` mentioned (commented) at `pipeline/dnallmmark_pipeline.py:5`
  - SDK/Client: none in this repo (handled inside the `dnallm` framework)

**Frontend CDN dependencies (jsDelivr):**
- Chart.js 4.4.0 - `<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js">` in `dnallm-mark/index.html:18`, `dnallm-mark/task.html:20`, `dnallm-mark/task-mockup.html:13`
- SheetJS xlsx 0.18.5 - `<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js">` in `dnallm-mark/index.html:21`, `dnallm-mark/task.html:23`, `dnallm-mark/finetuning.html:13`
- Note: pages are non-functional without internet access to the CDN

**Reserved / not yet implemented:**
- `CONFIG.API.BASE_URL: 'https://api.dnallm-mark.com'` with endpoints `/models`, `/rankings`, `/arenas` is defined in `dnallm-mark/js/config.js:66-74` and marked "reserved" — no code calls it. All leaderboard data is fetched from local static JSON

**Community/social (outbound links only):**
- Discord invite, Twitter, LinkedIn in `dnallm-mark/js/config.js:60-64`; GitHub Issues/Discussions links in `README.md:308-310`

## Data Storage

**Databases:**
- None. Everything is flat JSON files on the local filesystem

**File Storage:**
- Local filesystem only, structured as a one-way data pipeline:
  - `pipeline/datasets/` - raw datasets (gitignored, downloaded from Zenodo)
  - `pipeline/models/` - pretrained model weights (gitignored)
  - `pipeline/finetuned/{model}/{dataset}/` - checkpoints, `trainer_state.json`, `final_metrics.json`, `test_metrics.json`, `flops_report.json` (gitignored)
  - `pipeline/finetuned/{model}/{model}_performance.json` - master per-model performance file written by the pipeline (`pipeline/dnallmmark_pipeline.py:1198-1268`)
  - `dnallm-mark/data/model_performance/` - 42 committed per-model JSON inputs for the web UI
  - `dnallm-mark/data/task_performance/` - 47 generated per-task JSON files (pivot of the above)
  - `dnallm-mark/data/models_comparison*.json` - 4 generated leaderboard summaries (all/animal/plant/microbe)
  - `dnallm-mark/data/tasks.json` - generated task index (by `scripts/generate-tasks-index.js`)
- Web UI reads these via relative `fetch('./data/...')` calls (`dnallm-mark/js/data.js:40,63,88`, `dnallm-mark/js/task-loader.js:27,91`) — a static HTTP server is required (fetch fails on `file://`)

**Caching:**
- In-memory only (`DataAPI.cache` in `dnallm-mark/js/data.js:6-15`, with retry wrapper in `dnallm-mark/js/task-loader.js:81`)
- Optional model-hub disk caches `HF_HOME` / `MS_CACHE_HOME` referenced (commented out) at `pipeline/dnallmmark_pipeline.py:3-5`

## Authentication & Identity

**Auth Provider:**
- None. The static site has no authentication, no user accounts, no backend. The submit form (`dnallm-mark/js/submit.js`) collects name/email client-side only and never sends them anywhere

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry or similar)

**Logs:**
- Pipeline writes plain-text error logs to `pipeline/logs/{model_name}_error_log.txt` (`pipeline/dnallmmark_pipeline.py:831-833`) and prints timestamped progress to stdout
- TensorBoard event files via `report_to: "tensorboard"` in `pipeline/finetune_config.yaml:57` and `pipeline/finetune_config_with_head.yaml:72`
- Frontend uses `console.log`/`console.warn`/`console.error` only

## CI/CD & Deployment

**Hosting:**
- None configured. Local static serving via `start-server.sh` (port 8080) or `python3 -m http.server 8000` per `dnallm-mark/README.md`

**CI Pipeline:**
- None detected (no `.github/workflows/`, no CI config files)

## Environment Configuration

**Required env vars:**
- None. The system runs entirely on local files and CLI arguments

**Optional env vars:**
- `HF_HOME`, `MS_CACHE_HOME` - hub cache redirection (commented out at `pipeline/dnallmmark_pipeline.py:3-5`)

**Secrets location:**
- Not applicable — no secrets are used anywhere in this repo

**External data acquisition (manual steps):**
- Benchmark datasets: downloaded from Zenodo record 19135551 (link in `README.md:116` — note the link carries a preview token; use the clean record URL) and extracted into `pipeline/datasets/`
- Pretrained models: manually placed in `pipeline/models/` and registered in `pipeline/models_info.json`

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None. Community submissions follow a manual flow: `dnallm-mark/js/submit.js` validates a user-uploaded performance JSON client-side (`validateJSON`, requiring `dataset` + `performance` keys per entry) and renders copy-paste git/PR instructions (`generatePRInstructions`) — no network submission occurs

## Data Processing Chain (how the pieces connect)

1. `python pipeline/dnallmmark_pipeline.py --target_model X` fine-tunes models → writes `pipeline/finetuned/{model}/{model}_performance.json`
2. Performance files are copied into `dnallm-mark/data/model_performance/{model}_performance.json`
3. `python script/get_task_performance.py` (run from `dnallm-mark/data/`) pivots them into `task_performance/{dataset}_task_performance.json`
4. `node scripts/generate-tasks-index.js` builds `dnallm-mark/data/tasks.json` from that directory
5. `python script/summarize_comparison.py` (run from `dnallm-mark/data/`) computes rank/minmax/zscore/robust aggregates → `models_comparison.json` + per-species variants
6. Static site (`index.html`, `task.html`, `finetuning.html`, `models.html`, `datasets.html`) fetches those JSON files at runtime

---

*Integration audit: 2026-10-08*
