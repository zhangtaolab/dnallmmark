# Phase 4: Correctness & Methodology Core - Pattern Map

**Mapped:** 2026-10-10
**Files analyzed:** 22 (new + modified)
**Analogs found:** 22 / 22 (all tracked in-repo or pinned suite-revision sources; no gitignored mirrors)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `script/export_runs.py` (NEW) | utility/script | transform (batch JSON→JSON) | `script/convert_registry.py` (repo-root explicit-path script pattern) | role-match |
| `script/summarize_comparison.py` (EDIT) | utility/script | batch transform | itself (edit sites at :80-96, :295-305, :335-339, :389-412) | exact |
| `script/get_task_performance.py` (DELETE per OQ6) | utility/script | transform | — | n/a (retirement) |
| `tests/test_export_runs.py` (NEW) | test | transform | `tests/test_schemas.py:130-153` (data≡enum self-check) + `tests/test_sweep.py` (fixture-tree harness) | role-match |
| `tests/test_vendored_stats.py` (NEW) | test | transform | `tests/test_determinism.py` (pinned-behavior parity) | role-match |
| `tests/test_known_defects.py` (EDIT) | test | n/a | itself (:69-164 lock + companion) | exact |
| `tests/test_aggregation.py` (EDIT) | test | n/a | itself (:15-18 pin docstring) | exact |
| `tests/test_run_finetune_contracts.py` (EDIT) | test | n/a | itself (:237-255 parity pattern) | exact |
| `tests/test_registry_unification.py` (EDIT) | test | n/a | itself (CARD_KEYS :54, TXT_ONLY_MODELS :59) | exact |
| `tests/test_pivot.py` (retire/fold) | test | n/a | — | n/a |
| `pipeline/run_finetune.py` (EDIT: 4 quirk ports) | config/registry module | n/a | `pipeline/dnallmmark_pipeline.py:1322-1361` (legacy registries) + `pipeline/dnallmmark_pipeline.py:791-811` (`determine_batch_size`) | exact reference |
| `pipeline/dnallmmark_pipeline.py` (read-only reference) | reference | n/a | itself | exact |
| `pipeline/models_info.json` (EDIT: 17 card fills) | config/data | n/a | `tests/test_registry_unification.py` CARD_KEYS + the 03-03 PlantHelixSeek fill precedent | exact |
| `baseline/compare.py` (EDIT: IN-01 + WR-02) | utility | transform | itself (:70-115 `walk()`) | exact |
| `dnallm-mark/{index,task,finetuning,models,datasets}.html` (EDIT ×5) | component (static shell) | n/a | `dnallm-mark/datasets.html` (empty-container shell :24, :27, :34) | exact |
| `dnallm-mark/submit.html` (NEW) | component (static shell) | n/a | `dnallm-mark/datasets.html` full shell | exact |
| `dnallm-mark/js/submit.js` (EDIT: validateJSON rewiring) | component (page controller) | request-response (fetch/FileReader) | itself (:171-206) + `js/finetuning.js` renderNavbar for navbar copy | exact |
| `dnallm-mark/js/data.js` (EDIT: escapeHTML + aggregateSpecies caller level) | utility | n/a | itself (:132-145 helper block, :172 getColorForModel) | exact |
| `dnallm-mark/js/config.js` (EDIT: confirm NAV_LINKS Submit entry) | config | n/a | itself (:50-57) | exact |
| `dnallm-mark/js/{main,task}.js` (EDIT: add navbar render) | component | n/a | `js/finetuning.js:52-65` renderNavbar | exact |
| `dnallm-mark/js/{finetuning,datasets,models}.js` (EDIT: AUD-10 nesting reads) | component | n/a | `js/datasets.js:44-53` loadData join (correct level) vs `js/finetuning.js:129-144` (wrong level) | exact |
| `pyproject.toml` + `Makefile` + `README.md` (EDIT: scipy group, lint scope += convert_registry/export_runs, exporter sentence) | config | n/a | `Makefile:67-68` lint scope line; `pyproject.toml` dep groups | exact |

Vendored source (READ-ONLY, pinned): `/home/forrest/Github/DNALLM` @ `483a35c` — `dnallm/finetune/sweep.py::aggregate_seeds` and `dnallm/tasks/metric_registry.py::_RAW_REGISTRY`. Never imported, never modified; copied into `script/export_runs.py` with source annotation.

## Pattern Assignments

### `script/export_runs.py` (NEW — utility, batch transform)

**Analog A (script skeleton):** `script/convert_registry.py:1-40` — large module docstring (Purpose / Behavior / Direction of truth), repo-root explicit paths (`REPO_ROOT`-relative `Path`s, NOT CWD-relative — this is the deliberate CWD-convention break Pitfall 3 blesses), argparse CLI. Follow this header/docstring structure.

**Analog B (metric mapping precedent):** `pipeline/dnallmmark_pipeline.py:1273-1285` — the legacy hardcoded mapping the new table formalizes:
```python
"auroc": test_results.get("eval_AUROC", ""),
"pearson_r": test_results.get("eval_pearsonr", ""),
"spearman_r": test_results.get("eval_spearmanr", ""),
```

**Vendored function (copy verbatim, annotate `source: dnallm/finetune/sweep.py @483a35c`):**
```python
def aggregate_seeds(values, *, n_bootstrap, bootstrap_seed, small_n_ci):  # "t-interval" | "omit"
    # returns EXACTLY {"n_seeds", "mean", "sd", "ci95", "method"}
    # n<3 -> ci95=None method="none"; 3<=n<10 t-interval via scipy.stats.t.ppf(0.975, n-1);
    # n>=10 seeded percentile bootstrap rng.integers(0, n, (n_bootstrap, n)) -> np.percentile(means,[2.5,97.5])
```
Vendor module constants too: `SMALL_N_CI_CHOICES`, `CI_MIN_SEEDS = 3`, `BOOTSTRAP_MIN_SEEDS = 10`. Only imports: `numpy`, `scipy.stats`.

**Input contract:** `pipeline/run_sweep.py:23-37` run_record.json schema (metrics = final_metrics keys VERBATIM, suite-native `eval_*`). Layout `{output_root}/{model}/{task}/seed_{seed}/run_record.json`.

**Mapping table:** `SUITE_CANONICAL` (28-name frozenset, RESEARCH Pattern 3 skeleton) + `CANONICAL_TO_EXPORT` + `PIPELINE_KEYS`; unmapped canonicals → `""` (A6 default). summarize_comparison imports this table (its local `metric_key_map` at :295-305 is deleted).

**Output:** must validate against `schemas/task_performance.json` (datasetBlock species enum `["Animals","Plants","Microbe"]` — Multiple→majority arena mapping applied BEFORE emission, never leak "Multiple"). parametersBlock sourcing = Open Question 5, maintainer sign-off.

**Error handling:** hard-fail joins (KeyError on unregistered dataset/model), never silent fallback (Anti-Pattern: fallback joins). Filename sanitization `/`→`_` per `script/get_task_performance.py:155`.

---

### `script/summarize_comparison.py` (EDIT — species switch, METRIC_KEY_MAP deletion, get_float isfinite)

**Edit site 1 — species source (:335-339), replace with registry join.** Join pattern to copy: `tests/test_known_defects.py:88-91` `_load_category_map`:
```python
with DATASETS_INFO.open("r", encoding="utf-8") as fh:
    registry = json.load(fh)
return {name: entry["Category"] for name, entry in registry.items()}
```
Replacement in the dataset loop:
```python
arena = arena_map[dataset_name]   # KeyError = unregistered = hard fail
dataset_species_map[dataset_name] = arena
```
with `MAJORITY_ARENA = {"Multiple": "Animals"}` applied at load. Keep :389-412 grouping/filename emission untouched (groups now keyed by arena).

**Edit site 2 — get_float (:80-96):** after `return float(val)` add `if not math.isfinite(result): return default` (WR-03). Same commit: flip pins in `tests/test_aggregation.py` whose docstring (:15-18) documents today's pass-through.

**Edit site 3 — delete `metric_key_map` (:295-305), import exporter's table.**

---

### `pipeline/run_finetune.py` (EDIT — 4 quirk ports)

**Analog:** `pipeline/dnallmmark_pipeline.py:1322-1361` (legacy registries) and `:791-811` (`determine_batch_size` tier table `<=512: full, <=1024: //2, <=2048: //4, <=4096: //8, <=8192: //16, <=16384: //32, else 1`, each `max(1, batch_size // N)` + grad_accum `max(1, batch_size // dynamic_batch_size)`). Port as INITIAL length-tier cap composable with the existing VRAM estimator (:210-307); wire `models_with_limited_length` `{"prokbert-mini": 1027, "plant-dnabert-6mer": 512}` at the max_length block (~:628). ACGT alphabet: conditional at `run_finetune.py:732` — list members `"ACGTacgt|"`, non-members `"ACGTNacgtn|"`. Safetensors: union (11 entries — both `plant-dnamamba-6mer` AND `PlantGFM`). Use CURRENT registry name forms; apply rename map `PlantCAD2-Large-l48-d1536→PlantCAD2-Large`, drop `prokbert-mini-c/-long`, `MutBERT` (name-drift trap).

**Parity test extension:** copy `tests/test_run_finetune_contracts.py:237-255` regex-extract-both-sources pattern (`list_members(src, name)` + membership asserts), extended with `LEGACY_NAME_MAP` per RESEARCH Code Example.

---

### `pipeline/models_info.json` (EDIT — 17 card fills)

**Analog:** the 03-03 PlantHelixSeek fill (D-09, source-annotated ModelScope card). Keys = `tests/test_registry_unification.py:54` `CARD_KEYS` frozenset (11 keys). Update the test's enumeration from 17-absent to 62/62 complete.

---

### `baseline/compare.py` (EDIT — IN-01 INT label, WR-02 bool/int)

**Edit site:** `walk()` :70-115. WR-02: the BOOL branch (:88-92) reports only `if a != b` — add cross-type reporting (`isinstance(a, bool) != isinstance(b, bool)` → report even at equal value). IN-01: pure `int`-vs-`int` unequal pairs currently fall to FLOAT_BIG — add a distinct INT label branch before the float path; update the docstring vocabulary table same commit; check `baseline/PIN-VALIDATION.md` for label dependencies.

---

### Frontend shells — `{index,task,finetuning,models,datasets,submit}.html`

**Analog:** `dnallm-mark/datasets.html` — empty-container pattern (:24 `.hero-container`, :27 `.datasets-container`), `./css/styles.css` link (:11), module script at end of body (:34). Add `<div class="navbar-container"></div>` to all 6. Note: models.html/datasets.html also carry a STATIC `<nav class="navbar">` (:15-19) — the dynamic renderer targeting `.navbar-container` is the locked fix (CONTEXT Q1 keeps the dynamic navbar); the planner decides static-nav removal vs coexistence (Pitfall 8: one shared renderer, config-driven, active-state from pathname — `CONFIG.NAV_LINKS` at `js/config.js:50-57` already includes Submit).

**Shared renderNavbar to copy/adapt:** `js/finetuning.js:52-65` — template literal over `CONFIG.NAV_LINKS`, injected via `document.querySelector('.navbar-container').innerHTML`. Add null-guard (`if (!el) return;`) per CLAUDE.md container convention, and `escapeHTML()` on interpolated names.

---

### `dnallm-mark/js/submit.js` (EDIT — validateJSON rewiring) + `js/data.js` (escapeHTML)

**validateJSON misread site:** `js/submit.js:171-206` — iterates `Object.entries(parsed)` at ROOT so `info`/`performance` keys fail the `dataset`/`performance` sibling check. Rewire: top level must be `{info, performance}`; iterate `Object.entries(parsed.performance)` requiring `dataset`/`parameters`/`performance` sub-dicts (schema contract from `schemas/` Phase 2, structural check only — no JSON-Schema-in-browser). Keep the Promise/FileReader wrapper shape and the existing branch-name sanitizer in `generatePRInstructions()` (`replace(/[^a-zA-Z0-9_-]/g, '-')`).

**escapeHTML placement:** `js/data.js` helper block beside `normalizeToArena` (:149) / `getColorForModel` (:172) — plain module method, per RESEARCH Code Example. Apply ONLY at navbar/submit/task renderers touched this phase (locked bounded scope).

**AUD-10 nesting fixes:** correct level = iterate `performance` dict, not root. Wrong: `js/finetuning.js:129-132` (`Object.entries(this.state.performanceData)` where performanceData is already the performance map — verify the caller level), `js/datasets.js:46-47` (correct-level reference shape: `data.dataset?.species || 'N/A'`), `js/data.js:132-142` `aggregateSpecies` + its caller at :249, `js/submit.js:184-195`. Must land WITH the navbar fix (Pitfall 2: unmasking garbage rows).

## Shared Patterns

### Registry joins (hard-fail)
**Source:** `tests/test_known_defects.py:88-91`
**Apply to:** summarize_comparison species join; export_runs model-card and dataset-block joins. Plain `Source__task`-key lookup; KeyError on miss; never fall back.

### Same-commit fix + fixture + unmark (SC-1 / strict-xfail)
**Source:** `tests/test_known_defects.py:110-164` (companion + xfail(strict=True) lock pair)
**Apply to:** AUD-01 unmark, WR-02, WR-03 lock removals. Companion stays unmarked forever; strict XPASS forces marker removal in the same commit as the fix + fixture edit (`tests/fixtures/export_chain/defect_species_performance.json` poly_a entry → `"Plants"`).

### Vendoring with provenance + parity test
**Source:** suite revision `483a35c` (immutable pin); prior art `script/convert_registry.py` (D-10 discipline)
**Apply to:** `aggregate_seeds` (n-guard boundaries 2/3/9/10, t-values vs scipy recompute, bootstrap seed determinism, ValueError cases) and the 28-name metric registry surface (key-parity both directions; vendored name list is the oracle).

### SC-6 data≡enum self-check
**Source:** `tests/test_schemas.py:130-153` `test_metric_enum_matches_committed_data`
**Apply to:** exporter metricBlock enum extension (only if A6 default is overridden) and `info.metric` casing (do NOT normalize — enum is `["f1","mcc","spearmanr","AUPRC"]`).

### Empty-container + page-controller (frontend)
**Source:** `dnallm-mark/datasets.html` + `js/finetuning.js:52-65`
**Apply to:** all 6 pages; single shared renderNavbar; Playwright pass (start-server.sh :8080) asserts zero console errors + containers non-empty + nav links resolve.

### Lint-scope growth with every touched file (D-08 discipline)
**Source:** `Makefile:67-68` (current scope: `tests/ script/make_dev_splits.py pipeline/run_finetune.py pipeline/run_sweep.py`)
**Apply to:** add `script/convert_registry.py` (IN-08), `script/export_runs.py`, `script/summarize_comparison.py`, `baseline/compare.py` once touched; ruff-zero self-evidenced. `make typecheck` (ty) must stay zero-diagnostics on the new script.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `freeze_snapshot` (function inside export_runs or baseline) | utility | file-I/O | No tar/SHA256 manifest writer exists; nearest convention is `baseline/data-v1.sha256` (manifest format only, no generator). Parameterized paths + fixture-tree pure-function test per OQ7. |
| Playwright verification harness | test | n/a | No browser test exists; Phase 1 headless-chromium DOM dumps are process precedent only — evidence format is console capture + DOM assertions, manual via Playwright MCP/CLI, not a committed test file. |

## Metadata

**Analog search scope:** `script/`, `tests/`, `pipeline/`, `baseline/`, `dnallm-mark/js/`, `dnallm-mark/*.html`, `Makefile`, `pyproject.toml`; suite repo `/home/forrest/Github/DNALLM` @483a35c (read-only). All analog paths verified git-tracked (`git ls-files` non-empty) or pinned suite revisions.
**Files scanned:** ~30
**Pattern extraction date:** 2026-10-10
