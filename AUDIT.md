# DNALLM-Mark Code Audit — 2026-10

**Scope:** pipeline / data scripts / frontend at commit `788e909` (tag `data-v1`, pre-fix state). The working tree equals the tagged state for all three audited subsystems — plan 01-01 of this milestone added only root-level substrate files (`baseline/`, `pyproject.toml`, `uv.lock`, `requirements.txt`, `.python-version`) and touched no audited code or data.

**Method:** parallel systematic review with one reviewer per subsystem (pipeline / data scripts / frontend); every finding independently reproduced before grading. An internal seed inventory (CONCERNS.md, mapped 2026-10-08) was used as input hypotheses to re-verify — never as conclusions.

## Executive summary

Interim state (skeleton + verified seed findings; full merge pending): 0 P0, 2 P1, 1 P2, all in the data subsystem so far.

Top risks identified to date: the committed derived-data index (`tasks.json`) is stale relative to its own inputs (metric-casing drift for `BEND__CpG_methylation`), and all three derived-data generators are nondeterministic across machines and days. Both are reproducibility findings (P1); neither changes an already-published aggregation value by itself, but the second makes byte-level reproduction of the leaderboard data impossible outside the original machine.

## Findings table

| ID | Sev | Subsystem | Location | Finding | Reproduction | Recommended fix | Disposition |
| AUD-01-P1 | P1 | data | dnallm-mark/data/tasks.json (BEND__CpG_methylation entry); scripts/generate-tasks-index.js | Stale derived index: committed tasks.json carries metric value "auprc" for task id BEND__CpG_methylation while the source task_performance file and the model_performance inputs carry the cased form "AUPRC". The index (generated 2026-03-31) is not a faithful projection of the current tree; its generator does not apply the metric_key_map casing map used by the aggregation script (script/summarize_comparison.py:299 maps "AUPRC" to "auprc"). | jq over dnallm-mark/data/tasks.json selecting the task with id "BEND__CpG_methylation" returns metric "auprc"; grep over dnallm-mark/data/task_performance/BEND__CpG_methylation_task_performance.json shows "metric": "AUPRC" at line 10; the casing map at script/summarize_comparison.py:298-308 is not referenced anywhere in scripts/generate-tasks-index.js | Regenerate tasks.json from the current task_performance tree (plan 01-03 regeneration) and make the index generator casing-consistent with the aggregation script so the drift class cannot recur | fixed in-phase by FIX-05 (plan 01-03) — regeneration reconciles the value; any page-level effect of the mismatch is audited under frontend review |
| AUD-02-P1 | P1 | data | script/summarize_comparison.py:309,380-381,407-408; script/get_task_performance.py:100,158-159; scripts/generate-tasks-index.js:50 | Derived-data generators are nondeterministic: directory iteration uses unsorted os.listdir (summarize_comparison.py:309 and get_task_performance.py:100), json.dump writes without sort_keys (summarize_comparison.py:380-381 and 407-408; get_task_performance.py:158-159), and the task-index generator stamps a live-clock date (generate-tasks-index.js:50, generatedAt). Output bytes therefore depend on the generating machine's filesystem order and the run date; exact-tie rank order and float summation order are machine-dependent. | Quoted source at each site: `for filename in os.listdir(input_dir):` (both Python scripts); `json.dump(..., indent=4, ensure_ascii=False)` with no sort_keys (four sites); `generatedAt: new Date().toISOString().split('T')[0]`. Empirical: plan 01-01 pin-validation regenerated the full chain on a second machine and observed exact-tie rank swaps (Omni-DNA-700M vs plant-dnabert-6mer at rank_score 1232.0; gena-lm-bigbird-base-t2t vs hyenadna-large-1m-seqlen-hf at 749.0; agro-nucleotide-transformer-1b vs plant-dnamamba2-BPE at 448.0) driven by os.listdir insertion order (baseline/PIN-VALIDATION.md) | Wrap both Python directory loops in sorted(); add sort_keys=True to all four json.dump calls; remove the generatedAt live-clock stamp (plan 01-03 decision: drop the field) | fixed in-phase by FIX-05 in plan 01-03 |
| AUD-03-P2 | P2 | data | README.md:241-242; script/summarize_comparison.py:34-35 | Documentation names the per-species outputs models_comparison_animals.json and models_comparison_plants.json (plural species) while the tracked outputs are models_comparison_animal.json and models_comparison_plant.json (singular, produced via to_singular_species at script/summarize_comparison.py:164-184). Users following the docs hit file-not-found. | README.md lines 241-242 list the plural filenames; ls dnallm-mark/data shows only singular variants (models_comparison_animal.json, models_comparison_plant.json); the module docstring at script/summarize_comparison.py:34-35 repeats the plural names | Correct the filenames in README and the module docstring | milestone backlog (doc drift) |

## Severity definitions

- **P0 — leaderboard integrity:** anything that makes a published number wrong, risks data corruption, or exposes an unintended live secret. Aggregation math errors, pipeline data-integrity regressions, silent model dropping from rankings.
- **P1 — user-facing breakage or reproducibility:** dead pages, broken flows, nondeterminism, unreproducible environment, missing license — anything that breaks external trust or blocks the release.
- **P2 — hygiene and debt:** dead code, doc drift, console or log noise, performance — recorded and routed to the milestone backlog per D-03.

Grading rule: a finding is severity-graded only after independent reproduction (D-01). Candidates that could not be reproduced are listed under Unverified observations without a grade. Maintainability observations are recorded in the separate non-graded list (D-04) and never receive P0/P1/P2 grades.

## Methodology and limitations

Interim. The methodology section is completed when the merged report publishes (plan 01-02 task 3). Constraints already established for this audit:

- No GPU and no `dnallm` environment exists this phase — the pipeline subsystem is reviewed by static code-path tracing with quoted lines, cross-checked against the 42 committed model_performance JSONs. The pipeline module is not imported (its module globals live under the `if __name__ == "__main__":` guard; importing and calling `main()` raises NameError).
- Data-script claims are reproduced against actual committed JSON values (jq / python) and, where applicable, scratch regeneration of the chain per the procedure in `baseline/PIN-VALIDATION.md`.
- Frontend rendering claims are verified in a browser over a local static server where tooling permits; claims verified only by static evidence (grep with quoted lines, `node --check`) are marked static-verified-only.
- The intentional Zenodo dataset-sharing link at README.md:116 is a recorded maintainer decision (kept as-is); it is excluded from findings and is never quoted here — the full-history secret scan in plan 01-03 provides the evidence that no other secrets exist.

## Maintainability findings (non-graded, D-04)

Interim — populated in full at merge time. Seeded from re-verified observations; these carry no severity grade by design:

- Dead template configuration in `dnallm-mark/js/config.js:19-47` (arena-template leftovers: SORT_OPTIONS, RANKING_DISPLAY, TABLE_CONFIG, API, DEV_MODE) — unreferenced.
- Duplicated `renderNavbar()` copy-pasted across five page modules (finetuning.js, models.js, datasets.js, submit.js, plus a dead variant in main.js) — the duplication is the breeding ground of the navbar crash class.
- Unused SheetJS CDN include on three production pages (~900 KB) and three committed dev mockup pages (test.html, verify-chart.html, task-mockup.html).

## Secret-scan evidence

<!-- pending: filled by plan 01-03 task 3 -->
