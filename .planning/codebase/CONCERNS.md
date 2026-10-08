---
last_mapped_commit: a44d3104b8ab1e04ddbebed75446772fc0ca3f1b
last_mapped_at: 2026-10-08
---
# Codebase Concerns

**Analysis Date:** 2026-10-08

## Tech Debt

**Dead template configuration ("arena" leftovers):**
- Issue: `CONFIG` in `dnallm-mark/js/config.js:19-47` contains `SORT_OPTIONS` (score/win-rate/battles), `RANKING_DISPLAY` (SHOW_ELO/SHOW_WIN_RATE/SHOW_BATTLES), and `TABLE_CONFIG` (`DEFAULT_SORT: 'elo'`) from the "Design Arena" LLM-arena template this UI was cloned from. None are referenced anywhere else. `CONFIG.API` (`js/config.js:67-74`) points to a nonexistent `https://api.dnallm-mark.com`; `DEV_MODE: true` and `SOCIAL_LINKS` are also unreferenced.
- Files: `dnallm-mark/js/config.js`
- Impact: Misleads future contributors into wiring up ELO/win-rate features that have no data source.
- Fix approach: Delete unused CONFIG blocks, or move genuinely planned items to a comment/roadmap.

**Duplicated navbar rendering across 4 pages (one variant broken):**
- Issue: `renderNavbar()` is copy-pasted into `finetuning.js:52-66`, `models.js:62-76`, `datasets.js:66-80`, and `submit.js:39-53`. All use `link.active` which is never set in `CONFIG.NAV_LINKS`. `main.js:72-90` has a smarter `renderNavbar()` (computes active state) that is never called — dead method.
- Files: `dnallm-mark/js/main.js`, `dnallm-mark/js/finetuning.js`, `dnallm-mark/js/models.js`, `dnallm-mark/js/datasets.js`, `dnallm-mark/js/submit.js`
- Impact: Any nav change must be repeated 4-5 times; the duplication is why the crash bug below exists.
- Fix approach: Extract one shared `renderNavbar(activeUrl)` into `data.js` or a new `js/navbar.js`; remove the dead `main.js` version or make it the shared one.

**Half-implemented frontend aggregation stub:**
- Issue: `DataAPI.recalculateComparison()` in `dnallm-mark/js/data.js:187-273` is a fake reimplementation of `script/summarize_comparison.py` with hardcoded thresholds (`top1Count = avgRaw >= 0.9 ? 1 : 0`) and always-zero `sumRank`/`sum_minmax`/`sum_zscore`. It is never called.
- Files: `dnallm-mark/js/data.js`
- Impact: If anyone wires it up, the leaderboard silently shows fabricated numbers.
- Fix approach: Delete the function; ranking math must only live in the Python script.

**Committed dev artifacts and unused CDN payload:**
- Issue: `dnallm-mark/test.html` ("Design Arena - 测试页面", links to `localhost:8000`), `dnallm-mark/verify-chart.html`, and `dnallm-mark/task-mockup.html` are development mockups committed to the repo. SheetJS (`xlsx@0.18.5`, ~900 KB) is loaded from CDN on `index.html:21`, `task.html:23`, and `finetuning.html:13` but no JS references `XLSX` anywhere.
- Files: `dnallm-mark/test.html`, `dnallm-mark/task-mockup.html`, `dnallm-mark/verify-chart.html`, `dnallm-mark/index.html`, `dnallm-mark/task.html`, `dnallm-mark/finetuning.html`
- Impact: Slower page loads, larger attack surface, confusion about which pages are real.
- Fix approach: Delete the three mockup HTML files and the xlsx script tags.

**Console logging left in production code:**
- Issue: 39 `console.log` calls across the page modules (26 in `task-loader.js` alone, including a styled banner announcing debug APIs at `js/task-loader.js:407-413`).
- Files: `dnallm-mark/js/*.js`
- Impact: Noise in production console; minor.
- Fix approach: Strip or gate behind `CONFIG.DEBUG`.

**Mixed-language comments:**
- Issue: Chinese and English comments interleaved (`js/config.js:101`, `js/submit.js:3`, `js/datasets.js:3`, `js/models.js:3`, `css/styles.css:2-4`).
- Impact: Minor readability friction for the (English) public open-source audience.
- Fix approach: Standardize on English comments.

**No dependency specification at all:**
- Issue: No `requirements.txt`, `pyproject.toml`, `environment.yml`, or `package.json` anywhere. The pipeline imports `dnallm`, `torch`, `transformers`, `numpy`, `pandas` with zero version pinning; `README.md:84-97` (Installation) never mentions installing the `dnallm` framework or any Python dependencies.
- Files: `pipeline/dnallmmark_pipeline.py:16-18`, `README.md`
- Impact: Pipeline is not reproducible; `dnallm` API drift breaks it silently.
- Fix approach: Add `pipeline/requirements.txt` (or pyproject) pinning `dnallm`, `torch`, `transformers`, `numpy`, `pandas`; document install in README.

**README documentation drift:**
- Issue: `README.md:241-243` and the docstring of `script/summarize_comparison.py:34-35` document output files as `models_comparison_animals.json`/`models_comparison_plants.json` (plural) but the code produces singular names (`models_comparison_animal.json`, `models_comparison_plant.json`) — see `to_singular_species()` at `script/summarize_comparison.py:164-184`. README project-structure section (`README.md:271-304`) omits `task.html`, `models.html`, `datasets.html`, and `scripts/generate-tasks-index.js`. README badge (`README.md:3`) declares MIT licensing but no `LICENSE` file exists in the repo.
- Files: `README.md`, `script/summarize_comparison.py`
- Impact: Users following docs hit file-not-found; license status legally ambiguous.
- Fix approach: Correct filenames in docs, add LICENSE file, refresh the structure tree.

## Known Bugs

**Three pages crash on load — navbar container missing:**
- Symptoms: `finetuning.html`, `models.html`, and `datasets.html` render only the static hero placeholder and no table/model selector. Console shows `TypeError: Cannot set properties of null (setting 'innerHTML')`.
- Files: `dnallm-mark/js/finetuning.js:52-66`, `dnallm-mark/js/models.js:62-76`, `dnallm-mark/js/datasets.js:66-80`
- Trigger: Each page's `setup()` calls `renderNavbar()` first, which does `document.querySelector('.navbar-container').innerHTML = ...`. No `.navbar-container` element exists in any HTML file (verified by grep) — pages have a static `<nav class="navbar">` instead. The TypeError is swallowed by `setup()`'s try/catch, aborting all subsequent rendering (`renderHero`, table render, `bindEvents`).
- Workaround: None for users; pages are effectively dead.

**Fine-tuning leaderboard iterates wrong data nesting:**
- Symptoms: Even with the navbar bug fixed, the dataset table would show two garbage rows per model (`datasetName` = "info" and "performance") with all metric cells `N/A`.
- Files: `dnallm-mark/js/finetuning.js:126-153` (`prepareLeaderboardRows`)
- Trigger: `Object.entries(perfData)` is iterated directly, but each `model_performance/*.json` has shape `{ info, performance: { <dataset>: {...} } }` (verified in `data/model_performance/`). The loop must iterate `perfData.performance`.
- Workaround: None.

**Datasets page aggregates fake datasets "info" and "performance":**
- Symptoms: Same wrong-level iteration in `dnallm-mark/js/datasets.js:43-64` — the datasets Map would end up with exactly two entries named "info" and "performance", both showing `N/A` metadata, instead of the 47 real datasets.
- Files: `dnallm-mark/js/datasets.js`
- Trigger: Loading the datasets page (currently masked by the navbar crash).
- Workaround: None.

**Species aggregation always returns empty:**
- Symptoms: Models page species column always shows `N/A`.
- Files: `dnallm-mark/js/data.js:132-142` (`aggregateSpecies`), consumed by `js/models.js:56`
- Trigger: `aggregateSpecies` iterates `Object.values(performanceData)` (yields the `info` object and the `performance` dict) and probes `dataset.dataset?.species` — never present at that level. Should iterate `performanceData.performance`.
- Workaround: None.

**Leaderboard sorting breaks after first interaction:**
- Symptoms: On `index.html`, clicking a table header sorts once (or appears to); after switching arena or filter buttons, header clicks do nothing.
- Files: `dnallm-mark/js/main.js:488-500` (`bindEvents` attaches listeners to `th.sortable`), `dnallm-mark/js/main.js:363-408` (`renderLeaderboard` replaces the table via innerHTML)
- Trigger: `bindEvents()` runs once at setup; every `renderLeaderboard()` call destroys the `th` elements and their listeners. New rows/headers are never re-bound.
- Workaround: Reload the page.
- Fix approach: Use event delegation on the table container (the file already does this correctly for filter buttons at `js/main.js:477-486`).

**Sort state tracked but never applied:**
- Symptoms: `state.currentSort` and `state.sortAscending` toggle on header clicks, but the sort never changes.
- Files: `dnallm-mark/js/main.js:119-141` (`filterAndSortModels` unconditionally sorts by `rank_score` descending, ignoring `this.state.currentSort`/`sortAscending`)
- Trigger: Clicking any sortable header other than re-clicking Rank Score.
- Fix approach: Read `currentSort` in the comparator and honor `sortAscending`.

**Row click handlers lost after model filter change (fine-tuning page):**
- Files: `dnallm-mark/js/finetuning.js:241-253` — `.clickable-row` listeners bound once in `bindEvents()`; `renderLeaderboard()` re-render on select change replaces rows without re-binding (same pattern as the sorting bug).
- Fix approach: Delegate clicks on `.leaderboard-container`.

**Debug API calls a nonexistent method:**
- Symptoms: `DNALLMDebug.tasks()` throws `TypeError: ...getTaskList is not a function`.
- Files: `dnallm-mark/js/task-loader.js:393-394` (calls `window.taskLoader.getTaskList()`; class defines `initialize()` but no `getTaskList`).
- Fix approach: Return `this.taskList` via an added `getTaskList()` or call `initialize()`.

**Submit-page JSON validation rejects the documented format:**
- Symptoms: Uploading a real pipeline-generated `{model}_performance.json` fails with `Dataset "info" missing required fields`.
- Files: `dnallm-mark/js/submit.js:171-206` (expects top-level `{datasetName: {dataset, performance}}`), contradicting `README.md:188-226` and actual files (`{info, performance}`).
- Trigger: Any submission attempt using the documented format. Page itself is unreachable — `submit.html` does not exist even though `CONFIG.NAV_LINKS` links to it (`js/config.js:56`).
- Fix approach: Validate the `{info, performance}` schema and extract dataset entries from `parsed.performance`; create `submit.html` or remove the nav entry.

**Pipeline writes model species as dataset species (data-integrity regression risk):**
- Symptoms: Re-running the current pipeline and regenerating summaries would corrupt the Animal/Plant/Microbe arena split.
- Files: `pipeline/dnallmmark_pipeline.py:1229` (`"species": model_row.get("species", "unknown")` — `model_row` is the MODEL info; `pipeline/datasets_info.json` has no `species` field per dataset)
- Trigger: `script/summarize_comparison.py:336-341` builds `dataset_species_map` from this value; with model species values like `human`/`athaliana`/`multi-species`, species grouping breaks. The committed `data/model_performance/*.json` files contain correct per-dataset species (`Animals`/`Plants`/`Microbe` — verified consistent across all 42 files), proving they were produced by different code than what is currently committed.
- Workaround: Post-edit species fields by hand after each pipeline run.
- Fix approach: Add `species` to each entry in `pipeline/datasets_info.json` and use `row.get("species")` at pipeline line 1229.

**Config leaks across models in single-process batch runs:**
- Symptoms: When running all models without `--target_model`, every model processed after `evo2_1b_base` (index 6 in `models_info.json`) or `megaDNA_updated` (index 17) inherits `finetune_config_with_head.yaml` (MLP head, bf16 False, batch 48, save_total_limit 20) because `configs` is never restored to the base YAML. Likewise `Jamba-DNA-v1-114M-hg38` (index 16) sets `fp16/bf16 = False` permanently for all subsequent models.
- Files: `pipeline/dnallmmark_pipeline.py:835-838` (special-model config switch, no restore), `pipeline/dnallmmark_pipeline.py:862-864` (fp32-only switch, no restore)
- Impact: Benchmark fairness — mixed head configs/precision across models in one run; committed data appears to come from per-model runs (`--target_model`), which masks the bug.
- Fix approach: Reload `configs = load_config("./finetune_config.yaml")` at the top of each model iteration; apply per-model overrides on a fresh copy.

**Dead length-limit config:**
- Issue: `models_with_limited_length` (`pipeline/dnallmmark_pipeline.py:1332-1335`, caps for `prokbert-mini` and `plant-dnabert-6mer`) is defined but never referenced anywhere in the file.
- Impact: Those models run without their intended context-length caps; results may OOM or diverge from prior benchmarks.
- Fix approach: Wire it into the max_length determination block (`pipeline/dnallmmark_pipeline.py:956-980`) or delete it.

**Model metadata and data files out of sync:**
- Symptoms: `PlantHelixSeek` has committed performance data (`data/model_performance/PlantHelixSeek_performance.json`) but no entry in `pipeline/models_info.json`; `SPACE` vs `space` and `PlantDNAMamba2-BPE` vs `plant-dnamamba2-BPE` filename casing mismatches mean the pipeline cannot re-run these models on case-sensitive filesystems.
- Files: `pipeline/models_info.json`, `dnallm-mark/data/model_performance/`
- Impact: 3 of 42 leaderboard models are unreproducible via the pipeline; silent `continue` at `pipeline/dnallmmark_pipeline.py:828-829` skips missing models without logging.
- Fix approach: Align keys/filenames exactly; log skipped models.

## Security Considerations

**Leaked access token in README:**
- Risk: `README.md:116` contains a Zenodo record URL with an embedded `?token=...` preview/access token committed to git and public on GitHub.
- Files: `README.md`
- Current mitigation: None.
- Recommendations: Remove the token from the URL (publish the Zenodo record and link plainly), and treat the leaked token as compromised — revoke/regenerate it. Purge from git history if feasible.

**CDN scripts without Subresource Integrity:**
- Risk: Chart.js and SheetJS are loaded from jsdelivr with no `integrity`/`crossorigin` attributes (0 occurrences across all HTML files). A CDN compromise injects script into a scientific leaderboard page.
- Files: `dnallm-mark/index.html:18,21`, `dnallm-mark/task.html:20,23`, `dnallm-mark/finetuning.html:13`, `dnallm-mark/task-mockup.html:13`
- Current mitigation: `rel="noopener"` on external links only.
- Recommendations: Add SRI hashes, vendor the libraries into the repo, or use a lockfile-backed local copy; drop the unused SheetJS include entirely.

**Unescaped innerHTML interpolation of user/external input:**
- Risk: All rendering uses template literals injected via `innerHTML` without escaping. `js/submit.js:144-168,213-260` interpolates user-entered model name, submitter name, and email directly (self-XSS / phishing vector on shared machines). More importantly, model/dataset names come from `data/model_performance/*.json`, so a malicious submission PR with a crafted model name (e.g. containing `<img onerror=...>`) would execute in every visitor's browser on the leaderboard, models, datasets, and task pages.
- Files: `dnallm-mark/js/main.js:399,414-448`, `dnallm-mark/js/finetuning.js:136-148`, `dnallm-mark/js/models.js:125-140`, `dnallm-mark/js/datasets.js:129-141`, `dnallm-mark/js/task.js:429-461`, `dnallm-mark/js/submit.js`
- Current mitigation: None.
- Recommendations: Add an `escapeHtml()` helper in `js/data.js` and apply it to every string interpolated into innerHTML; PR review should still eyeball added JSON for payload-looking names.

**`trust_remote_code=True` model loading:**
- Risk: The pipeline fallback loader executes arbitrary Python from model repos/directories (`pipeline/dnallmmark_pipeline.py:880-898`).
- Files: `pipeline/dnallmmark_pipeline.py`
- Current mitigation: Models are local files the operator placed in `pipeline/models/` — acceptable for a research pipeline.
- Recommendations: Document that model directories are trusted input; avoid extending this path to network downloads.

**No secrets in code:** `.env` files absent; static site has no backend. Reserved API base URL in `js/config.js:68` is inert.

## Performance Bottlenecks

**Serial fetch waterfall on three pages:**
- Problem: `DataAPI.loadAllModelPerformance()` (`dnallm-mark/js/data.js:105-124`) awaits 42 JSON fetches sequentially in a for-loop; used by the Models, Datasets, and (formerly working) Fine-tuning pages.
- Files: `dnallm-mark/js/data.js`
- Cause: Sequential `await` inside loop.
- Improvement path: `Promise.allSettled(modelNames.map(...))`, or generate a single aggregated JSON at data-build time (the comparison files already exist for this purpose).

**One Chart.js dataset per model point:**
- Problem: The scatter chart creates 42 datasets of one point each (`dnallm-mark/js/main.js:232-249`) instead of a single dataset with 42 points — heavier tooltip/interaction/legend handling, and the custom legend plus this scales linearly with model count.
- Files: `dnallm-mark/js/main.js`
- Improvement path: Single dataset with per-point backgroundColor; re-assess at 100+ models.

**Row-by-row Python iteration for token counting:**
- Problem: `count_split_tokens()` (`pipeline/dnallmmark_pipeline.py:692-701`) iterates an HF dataset per-row in Python to sum token lengths — slow on datasets with hundreds of thousands of rows.
- Files: `pipeline/dnallmmark_pipeline.py`
- Improvement path: Use column access (`dataset['input_ids']`) and vectorized length sum, or `Dataset.map` batching.

**Full-file caching of task JSONs in localStorage:**
- Problem: `TaskLoader.cacheTask()` (`dnallm-mark/js/task-loader.js:121-157`) stores each complete `task_performance` JSON (all models, all metrics) in localStorage with a 24 h TTL; quota pressure triggers full expired-sweep + retry.
- Files: `dnallm-mark/js/task-loader.js`
- Improvement path: Acceptable at 47 tasks; if tasks grow, cache trimmed projections only.

## Fragile Areas

**Implicit, undocumented data-shape contract:**
- Files: `dnallm-mark/data/model_performance/*.json`, `dnallm-mark/data/task_performance/*.json`, `dnallm-mark/data/tasks.json`
- Why fragile: The `{info, performance: {dataset: {dataset, parameters, performance}}}` nesting is load-bearing across the Python scripts and every JS page, yet exists only as convention — three independent frontend bugs (finetuning.js, datasets.js, aggregateSpecies) already stem from misreading it. No schema validation anywhere on either producer or consumer side.
- Safe modification: When touching producers (`pipeline/dnallmmark_pipeline.py`, `script/get_task_performance.py`), re-run the full chain (summarize → pivot → index) and eyeball one file of each type; add a tiny JSON-schema check script.
- Test coverage: None.

**Three-step manual data-build chain with no freshness guard:**
- Files: `script/summarize_comparison.py`, `script/get_task_performance.py`, `scripts/generate-tasks-index.js`
- Why fragile: Regenerating data requires running all three, in that order, each from `dnallm-mark/data/` (except the Node script, run from anywhere). `get_task_performance.py` does NOT regenerate `tasks.json`; forgetting `generate-tasks-index.js` leaves `tasks.json` stale (task-loader fetches files by name from the index — currently in sync at 47/47, `generatedAt` 2026-03-31). `summarize_comparison.py` derives dataset species via last-writer-wins across files (`script/summarize_comparison.py:338-341`), which only works because all committed files happen to agree.
- Safe modification: Add a make/just target or single orchestrator script that runs all three and verifies `tasks.json.count == len(task_performance/*.json)`.
- Test coverage: None.

**FLOPs hook registry pinned to specific transformers class names:**
- Files: `pipeline/dnallmmark_pipeline.py:47-168`
- Why fragile: `FlopsCounter` matches on hard-coded class-name strings (`BertSelfAttention`, `MistralSdpaAttention`, `ModernBertAttention`, `MambaMixer`, ...) and `name_or_path` substrings. Any transformers upgrade that renames attention modules silently zeroes FLOPs for affected models (no error — hooks just never fire), corrupting the headline `sum_PFLOPs` efficiency metric. FLOPs are also extrapolated from a single-sample forward pass (`pipeline/dnallmmark_pipeline.py:1056-1135`, scaled ×3 ×epochs at `1209-1218`).
- Safe modification: After any dependency change, verify `flops_report.json` layer_details is non-empty for a canary model.
- Test coverage: None.

**Pipeline must run from `pipeline/` with relative paths:**
- Files: `pipeline/dnallmmark_pipeline.py:814,832,1009,1198` (`./finetune_config.yaml`, `./logs/`, `./finetuned/`)
- Why fragile: Running from repo root silently finds nothing (`load_config` failure) or writes outputs to unintended dirs. Module-level globals (`base_dir`, `datasets_info`, `models_info`, model lists) are defined under `if __name__ == "__main__":` (`pipeline/dnallmmark_pipeline.py:1294-1341`) and consumed by `main()` — importing the module and calling `main()` raises NameError; the 1,341-line file cannot be unit-tested or reused.
- Safe modification: Keep cwd discipline or refactor to pass paths explicitly.
- Test coverage: None.

**Error swallowing produces silently-partial results:**
- Files: `pipeline/dnallmmark_pipeline.py:899-909,1042-1051,1270-1279` (broad `except Exception` + `continue`), `pipeline/dnallmmark_pipeline.py:833` (error log opened `"w"` — truncated every run)
- Why fragile: A model or dataset that fails mid-run simply vanishes from the leaderboard with only a console/print and a per-model log file that the next run erases. `README.md` sells the platform as a standardized benchmark, so missing entries directly skew `rank_score`/top-K counts (models are only ranked on tasks they completed — no imputation, per `script/summarize_comparison.py:232-235`).
- Safe modification: Check `logs/*_error_log.txt` after every run; append (`"a"`) instead of truncate.
- Test coverage: None.

**Page-load order dependency in task page:**
- Files: `dnallm-mark/js/task.js:11-27` (`LoadingController` dereferences `#loading-retry` at module-eval time), `dnallm-mark/task.html:150-161`
- Why fragile: Works only because module scripts are deferred (DOM ready). If the script were ever loaded non-module or the element renamed, the whole task page crashes before setup.
- Safe modification: Null-guard the element lookups.

## Scaling Limits

**Frontend at scale:**
- Current capacity: 42 models, 47 tasks, ~40 KB comparison JSONs; pages render synchronously into single tables with no pagination (`CONFIG.TABLE_CONFIG.ROWS_PER_PAGE: 20` exists but is unused).
- Limit: At 100+ models — color collisions guaranteed (15-color palette, `js/data.js:172-179`), 42+ serial fetches per page visit, unwieldy legend/table. At 100+ tasks, localStorage caching of full task JSONs approaches the ~5 MB quota.
- Scaling path: Aggregate-build a single per-page JSON at data-build time; paginate tables; generate stable per-model colors (hash-based) or categorical grouping.

**Pipeline throughput:**
- Current capacity: Single GPU, strictly sequential model×dataset loops; no multi-GPU, no job scheduling, no checkpoint parallelism.
- Limit: Wall-clock scales with 41 models × 50 datasets; disk fills with checkpoints (`--remove_pt`/`--remove_checkpoints` flags exist as manual mitigations, `pipeline/dnallmmark_pipeline.py:732-743`).
- Scaling path: External orchestration (Slurm/Snakemake) wrapping per-model invocations — the `--target_model` flag already supports this.

## Dependencies at Risk

**`dnallm` framework (unpinned, external repo):**
- Risk: The entire pipeline's core (`DNADataset`, `load_config`, `load_model_and_tokenizer`, `DNATrainer`) comes from `github.com/zhangtaolab/DNALLM` with no version constraint or install documentation.
- Impact: Any upstream API change breaks `pipeline/dnallmmark_pipeline.py` at runtime; no lockfile to bisect against.
- Migration plan: Pin a commit/version in a `requirements.txt`; vendor as submodule if stability is needed.

**CDN-hosted Chart.js 4.4.0 (pinned exact, no SRI):**
- Risk: Offline development impossible; CDN outage or compromise takes down every page.
- Impact: All visualizations on `index.html` and `task.html`.
- Migration plan: Vendor `chart.umd.min.js` into `dnallm-mark/vendor/`.

**SheetJS xlsx 0.18.5:**
- Risk: Loaded but entirely unused — pure attack surface and page weight (see Tech Debt).
- Impact: None functional.
- Migration plan: Remove the script tags.

## Missing Critical Features

**No LICENSE file:**
- Problem: `README.md:3` shows an MIT badge and the citation block implies open use, but the repository contains no LICENSE file.
- Blocks: Legal reuse by the research community the benchmark targets.

**No submit.html page:**
- Problem: Navigation (`js/config.js:56`) and `js/submit.js` (complete implementation) reference `/submit.html`, which does not exist. External contributors — the stated growth mechanism ("After your PR is merged, the models_comparison.json will be recalculated") — have no intake path.
- Blocks: Community submissions.

**No test suite / CI / linting:**
- Problem: Zero test files, no CI config, no eslint/prettier/ruff configs anywhere.
- Blocks: Safe refactoring of any of the fragile areas above; regression detection for the ranking math in `script/summarize_comparison.py` (the scientific core).

**No automated data pipeline:**
- Problem: Data regeneration is three manual scripts (see Fragile Areas); nothing validates that `models_comparison*.json`, `task_performance/`, and `tasks.json` are mutually consistent after a run.
- Blocks: Reliable published-data updates.

## Test Coverage Gaps

**Everything — the repository has no tests of any kind:**
- What's not tested: All Python logic (`script/summarize_comparison.py` ranking/normalization math — the numbers the leaderboard publishes; `script/get_task_performance.py` pivot correctness; `pipeline/dnallmmark_pipeline.py` batch-size/config mutation logic) and all JS pages (data loading, table rendering, the exact nesting-level bugs documented above would have been caught by a single fixture-based test).
- Files: `script/`, `scripts/`, `pipeline/`, `dnallm-mark/js/`
- Risk: Any refactor or dependency bump can silently corrupt published benchmark rankings.
- Priority: High — start with unit tests for `calculate_dataset_stats`/`aggregate_models` (pure functions, easy fixtures) and a smoke test that loads each `data/*.json` and asserts the expected top-level shape.

---

*Concerns audit: 2026-10-08*
