---
phase: 05-ci-e2-rerun
verified: 2026-10-10T13:19:02Z
status: passed
score: 24/24 must-haves verified
covered_files: [".github/workflows/ci.yml", ".gitignore", ".htmlvalidate.json", ".planning/phases/05-ci-e2-rerun/05-01-PLAN.md", ".planning/phases/05-ci-e2-rerun/05-01-SUMMARY.md", ".planning/phases/05-ci-e2-rerun/05-02-PLAN.md", ".planning/phases/05-ci-e2-rerun/05-02-SUMMARY.md", ".planning/phases/05-ci-e2-rerun/05-03-PLAN.md", ".planning/phases/05-ci-e2-rerun/05-03-SUMMARY.md", ".planning/phases/05-ci-e2-rerun/05-04-PLAN.md", ".planning/phases/05-ci-e2-rerun/05-04-SUMMARY.md", "CHANGELOG.md", "DATA.md", "Makefile", "README.md", "baseline/d18-alias-inventory.json", "baseline/f6-migration-inventory.json", "dnallm-mark/data/manifest.json", "dnallm-mark/data/model_performance/PlantDNAMamba2-BPE_performance.json", "dnallm-mark/data/models_comparison.json", "dnallm-mark/data/models_comparison_animal.json", "dnallm-mark/data/models_comparison_microbe.json", "dnallm-mark/data/models_comparison_plant.json", "dnallm-mark/data/n_audit.csv", "dnallm-mark/data/n_audit.json", "dnallm-mark/data/permutation_tests.json", "dnallm-mark/js/config.js", "dnallm-mark/js/data.js", "dnallm-mark/js/main.js", "dnallm-mark/js/task.js", "eslint.config.mjs", "pipeline/env_smoke.py", "pipeline/eval_subsets.json", "pipeline/run_finetune.py", "pipeline/run_sweep.py", "pipeline/sweep_priorities.json", "pyproject.toml", "schemas/data_manifest.json", "schemas/models_comparison.json", "schemas/n_audit.json", "schemas/permutation_tests.json", "script/audit_n_frequencies.py", "script/export_runs.py", "script/permutation_tests.py", "script/run_migration_inventory.py", "script/summarize_comparison.py", "tests/fixtures/e2_replay/datasets_info.json", "tests/fixtures/e2_replay/finetune_config.yaml", "tests/fixtures/e2_replay/finetuned/ReplayModel-A/FakeCpG__methylation/seed_42/final_metrics.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-A/FakeCpG__methylation/seed_42/run_record.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-A/FakeCpG__methylation/seed_42/trainer_state.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-A/FakeCpG__methylation/seed_43/final_metrics.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-A/FakeCpG__methylation/seed_43/run_record.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-A/FakeCpG__methylation/seed_43/trainer_state.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-A/FakeCpG__methylation/seed_44/final_metrics.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-A/FakeCpG__methylation/seed_44/run_record.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-A/FakeCpG__methylation/seed_44/trainer_state.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-B/FakeCpG__methylation/seed_7/final_metrics.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-B/FakeCpG__methylation/seed_7/run_record.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-B/FakeCpG__methylation/seed_7/trainer_state.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-B/FakeCpG__methylation/seed_8/final_metrics.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-B/FakeCpG__methylation/seed_8/run_record.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-B/FakeCpG__methylation/seed_8/trainer_state.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-B/FakeCpG__methylation/seed_9/final_metrics.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-B/FakeCpG__methylation/seed_9/run_record.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-B/FakeCpG__methylation/seed_9/trainer_state.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-C/FakeCpG__methylation/seed_123/final_metrics.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-C/FakeCpG__methylation/seed_123/run_record.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-C/FakeCpG__methylation/seed_123/trainer_state.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-C/FakeCpG__methylation/seed_124/final_metrics.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-C/FakeCpG__methylation/seed_124/run_record.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-C/FakeCpG__methylation/seed_124/trainer_state.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-C/FakeCpG__methylation/seed_125/final_metrics.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-C/FakeCpG__methylation/seed_125/run_record.json", "tests/fixtures/e2_replay/finetuned/ReplayModel-C/FakeCpG__methylation/seed_125/trainer_state.json", "tests/fixtures/e2_replay/models_info.json", "tests/fixtures/golden/models_comparison.json", "tests/fixtures/golden/models_comparison_animal.json", "tests/fixtures/golden/models_comparison_microbe.json", "tests/fixtures/golden/models_comparison_plant.json", "tests/js/main-view-toggle.test.js", "tests/test_aggregation.py", "tests/test_audit_n.py", "tests/test_ci_replay.py", "tests/test_export_runs.py", "tests/test_known_defects.py", "tests/test_migration_inventory.py", "tests/test_permutation.py", "tests/test_run_finetune_contracts.py", "tests/test_schemas.py", "tests/test_sweep.py"]
covered_digest: "v3:sha256:53047219266e2d8b7076ef72bc899efc2fa257ea1a7555ac47e5e517c0d037b4"
behavior_unverified: 0
overrides_applied: 0
pending_uat:
  - test: "Live visual check of the weighted-default leaderboard (bash start-server.sh, open http://localhost:8080)"
    expected: "Leaderboard opens on the Weighted view; the Raw Rank toggle re-sorts the table and re-labels the scatter y-axis in one click; the footer shows the stamped date + data v1.1.0 (no today's-date behavior)"
    why_human: "05-02 Task 3 <human-check>, deferred to the phase UAT gate per the execution instruction and recorded in the WINDOWS ledger (entry 11, unrun-verify); behavioral seams are pinned by the 7 node tests in tests/js/main-view-toggle.test.js (15/15 lane green) — the browser-level visual judgment is the human part"
  - test: "First real GitHub-runner execution of ci.yml + branch-protection setup (05-USER-SETUP.md: make the four ci.yml checks required on main; do NOT require the 3.14 probe leg)"
    expected: "Badge goes green on the maintainer's next push; every job completes under 15 minutes; the four checks become required before merging (REV-06 'PR-required' clause)"
    why_human: "Runner-side behavior (action SHAs resolving on the runner, uv sync, badge) cannot be locally proven before the first push — WINDOWS ledger entry 10 (unrun-verify, open); every lane command was proven locally at commit time and re-verified by this verifier"
human_verification:
  - test: "Live visual check of the weighted-default leaderboard (bash start-server.sh, open http://localhost:8080)"
    expected: "Leaderboard opens on the Weighted view; the Raw Rank toggle re-sorts the table and re-labels the scatter y-axis in one click; the footer shows the stamped date + data v1.1.0 (no today's-date behavior)"
    why_human: "05-02 Task 3 <human-check>, deferred to the phase UAT gate (WINDOWS entry 11); node-test lane pins the mechanical seams only"
  - test: "First real GitHub-runner execution of ci.yml + branch-protection setup per 05-USER-SETUP.md"
    expected: "Badge green on next push; every job under 15 minutes; four checks required on main"
    why_human: "Runner-side behavior not locally provable before the first push (WINDOWS entry 10); user-setup item, not a code gap"
---

# Phase 5: CI & Three-Seed Full Re-Run (E2') Verification Report

**Phase Goal:** Aggregation methodology is upgraded BEFORE numbers publish (tie rules, difficulty normalization, permutation tests), CI proves repo health end-to-end, and the leaderboard is recomputed under three seeds with an attributable, changelogged, tagged migration
**Verified:** 2026-10-10T13:19:02Z
**Status:** passed (automated verification; 2 pending-UAT items routed to the phase UAT gate — see Pending UAT)
**Re-verification:** No — initial verification
**Verification scope note:** Per the binding ROADMAP decisions-carried block and the phase CONTEXT, the E2' LAUNCH itself is a maintainer-pulled dual-gate trigger (never agent-executed) and the `data-v2` tag is created only after E2' sign-off. This verification therefore proves the **code-only half and full preparation** — exactly what the phase promised — not E2' execution.

## Goal Achievement

### Observable Truths

Merged from the 4 ROADMAP Success Criteria (the contract) plus the 25 must_haves truths across plans 05-01..05-04. All gate numbers and artifact checks below were re-derived by this verifier at HEAD c1a1546 unless noted.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC-1/05-02: CI-overlap tie rule — overlapping 95% intervals share the component's min rank; CpG top-10 case (span ~0.0021) renders as a tie at n=3 t-intervals (df=2), never bootstrap | ✓ VERIFIED | `script/summarize_comparison.py:182-294` — `calculate_dataset_stats(ci_map=...)` with union-find over closed-interval overlap (`:241-266`), connected components share component-min rank; `_closed_intervals_intersect` (`:165-177`) implements closed-interval touch = tie. CpG proof: `tests/test_aggregation.py:308-334` `test_cpg_replica_top_models_tie_under_n3_t_intervals` — spans the committed anchors (0.0021039 asserted), builds intervals via the vendored `aggregate_seeds` at n=3, asserts `method == "t"`. This verifier ran the named test: PASSED. Boundary/adjacency/vacuous rows: `:263` touch-point, `:275` A~B~C merging, `:290` ci_map=None byte-identical exact-tie. On committed single-run data the rule is vacuous by design (no CI source pre-E2') — documented in CHANGELOG; activates at E2' when the exporter's seed_stats feed ci_map |
| 2 | SC-1/05-02: every CI interval in the chain comes from the vendored `aggregate_seeds` (n<3 → ci95 null/"none"; 3≤n<10 → t-interval; n≥10 → seeded bootstrap) | ✓ VERIFIED | Vendored block `script/export_runs.py:122-231` (banner "VERBATIM vendored copy @483a35c"; `CI_MIN_SEEDS=3` `:142`, `BOOTSTRAP_MIN_SEEDS=10` `:146`, `n_seeds` in every stats block `:195`). This verifier mechanically diffed the vendored block's 74 code lines against `git show 483a35c:dnallm/finetune/sweep.py` from the read-only suite checkout: all verbatim (the single non-matching line is export_runs' own module-level `REPO_ROOT` constant, not part of the vendored function — same finding as the Phase-4 verifier). Phase-5 diff hunks touch only the docstring, the D-16 emitter, and the CLI — never the vendored block. Intervals are CONSUMED by the tie rule (`ci_map`), never computed there; tests import `from export_runs import aggregate_seeds` (`tests/test_aggregation.py:34`) |
| 3 | SC-1/F6 Q4/05-02: leaderboard defaults to the z-score×uniform-difficulty weighted view; one click switches to raw rank; weighted value only READ client-side | ✓ VERIFIED | `dnallm-mark/js/config.js:39-42` VIEW_OPTIONS (weighted = "(default)"); `js/main.js:18-19` `currentView: 'weighted'` + `currentSort: 'weighted_score'`; `switchView` `:123-131`; view-derived scatter y accessor/axis `:239-240`, metric column `:477-479`; `weighted_score` read via `p.weighted_score ?? 0` — never computed (only `zscore` reference in js is the pre-existing dead `recalculateComparison`, `data.js:302`, dated to the initial 2026-03-27 commit, DATA-07/Phase-6 scope). 7 node tests in `tests/js/main-view-toggle.test.js` (default state, switch mapping, unknown-id guard, read-not-recompute, row metric, footer stamp, config default) — 15/15 lane green in this verifier's `make test` run. Browser-level visual confirmation = pending-UAT item 1 |
| 4 | SC-1/F6 Q3/05-02: pairwise permutation tests (10,000 shuffles, rng-seeded, BH over the C(42,2)=861 family) published as a committed artifact with family/semantics disclosed | ✓ VERIFIED | `script/permutation_tests.py`: scipy `permutation_test` `permutation_type="samples"`, `n_resamples=10_000`, `axis=-1`, `rng=42` (`:116-127`), `false_discovery_control(method="bh")` (`:183`). Committed artifact live-checked by this verifier: 861 pairs, `family_size: 861`, `n_resamples: 10000`, `seed: 42`, `fdr_method: bh`, coverage rule disclosed, 657 significant, 0 excluded; `info.axis` carries the WR-01 paired-semantics disclosure ("paired permutation test (scipy permutation_type='samples') — per-task difference signs flipped under the null"). One-reader design: `load_zscore_matrix` reuses summarize's own `load_model_inputs` + `calculate_dataset_stats` — the same zscores whose sums the leaderboard publishes |
| 5 | SC-1/05-02: the full chain (comparisons, permutation artifact, manifest) regenerates byte-identically | ✓ VERIFIED | This verifier ran `make data` (which runs summarize + permutation + index generator) then `git diff --exit-code -- dnallm-mark/data/`: exit 0, zero porcelain lines — the exact CI drift step, green on the committed tree |
| 6 | SC-2/05-01: push/PR runs the full local gate set on a GitHub ubuntu runner (ruff, ty, full pytest incl. slow lane, node:test, node --check, pinned static checks) | ✓ VERIFIED | `.github/workflows/ci.yml`: 4 jobs — lint-typecheck (make lint + make typecheck), test (matrix 3.13-required + 3.14 continue-on-error probe, make test), static-js (node --test, node --check over dnallm-mark/js/ + scripts/, `npx --yes eslint@10.12.0`, `npx --yes html-validate@11.16.2` over the six real shells), drift (make data + git diff --exit-code). Jobs invoke exactly the Makefile entry points (key link). All three action SHAs independently re-resolved by this verifier via `git ls-remote` against the official repos: checkout v7.0.1 = 3d3c42e5…, setup-uv v10.3.0 = 1c37ad07…, setup-node v7.1.0 = 949feb24… — all three match the workflow verbatim. `permissions: contents: read`; `pull_request` trigger only (no `pull_request_target` — appears only in the security-posture comment); zero mutable `@vN` tags (grep). TEST-04's literal "3.12" matrix text superseded by `requires-python >= 3.13` — documented deviation (05-01 SUMMARY #3, D-07) |
| 7 | SC-2/05-01: every CI job aborts at 14 minutes (<15-min budget enforced) | ✓ VERIFIED | `timeout-minutes: 14` on all 4 jobs (lint-typecheck `:36`, test `:50`, static-js `:77`, drift `:105`; grep count 4 job lines + 1 comment) |
| 8 | SC-2/Q1 decision/05-01: canned golden replay proves the chain end-to-end over committed fixtures — export → schema-valid task files with n_seeds=3 t-intervals; aggregate → schema-valid comparison; both byte-stable | ✓ VERIFIED | `tests/test_ci_replay.py` (marked `pytest.mark.ci`): export half asserts task_performance schema validity + seed_stats n_seeds=3/method "t"/two-float ci95 + byte-stability (`:147-222`); aggregate half asserts models_comparison schema validity + byte-stability (`:302+`). Fixture `tests/fixtures/e2_replay/` = 30 committed files (3 models × FakeCpG__methylation × 3 seeds: run_record/trainer_state/final_metrics + config + registry slices; models A/B carry the near-identical AUPRC overlap input — `test_replay_fixture_intervals_a_b_overlap_c_separates` `:175`). CONTEXT Q1 (maintainer-accepted) supersedes SC-2's literal "tiny model × 1k × 1 epoch" smoke wording: real training in CI is prohibited by the CI-feasibility constraint (no GPU, no dnallm); the replay covers export→aggregate→schema including the export step the SC names. First real runner execution = pending-UAT item 2 |
| 9 | SC-2/Q2/05-01: pinned `ci` marker lane selects the replay + the three reused classes and runs via `make ci` | ✓ VERIFIED | Marker registered in `pyproject.toml:85`; module pytestmarks on the three reused classes. This verifier ran `make ci`: **73 passed, 237 deselected**; `pytest -m ci --collect-only` selects exactly tests/test_ci_replay.py, test_aggregation.py, test_export_runs.py, test_known_defects.py — and nothing else |
| 10 | SC-2/TEST-04: README carries the CI badge | ✓ VERIFIED | `README.md:5` — badge + link to zhangtaolab/dnallmmark ci.yml workflow |
| 11 | SC-2/TEST-07/05-01: CI regenerates the derived chain and fails on any byte drift; committed tree is a verified no-op | ✓ VERIFIED | drift job = `make data` + `git diff --exit-code -- dnallm-mark/data/` (ci.yml:116-119). This verifier ran the exact sequence: make data exit 0, zero porcelain lines, `git diff --exit-code` clean |
| 12 | SC-3/F7 Q2/05-03: N-frequency + non-ACGT tables for all benchmark tasks in DATA.md + downloadable CSV/JSON | ✓ VERIFIED | `DATA.md` (generated wholesale by the audit, "do not edit by hand" header) — this verifier counted exactly 50 census rows; `dnallm-mark/data/n_audit.json` + `n_audit.csv` committed and schema-validated (schemas/n_audit.json bucket in the suite). Split columns: Train/Dev/Test N, non-ACGT per split, strict-pass, N-tolerant, unified eval N |
| 13 | SC-3/REV-07 empty/05-03: every registry task appears exactly once; the 7 missing GUE tasks explicit, never silently absent | ✓ VERIFIED | Live-checked: n_audit.json carries 50 tasks — 43 present, 7 missing; the missing names (GUE__EPI_GM12878, fungi_species_20, human_tf_0, mouse_1, mouse_4, virus_covid, virus_species_40) appear BOTH as an explicit prose list under "Missing datasets (pending re-extraction)" AND as visible table rows ("missing (re-extraction pending)") in the census. eval_subsets.json omits the 7 (never an empty list that would select zero rows) |
| 14 | SC-3/F7 Q1/05-03: eval-subset ID lists contain only common-filter survivors; N = min over model classes | ✓ VERIFIED | `pipeline/eval_subsets.json` live-checked: 43 tasks, 582,927 IDs, all lists sorted ascending; **43/43 tasks have len(ids) == the audit's unified_eval_n** (e.g. BEND CpG 106224 — the measured strict-charset drop from 106227). ID-survival + min-over-classes pinned by `tests/test_audit_n.py::test_emitted_ids_survive_common_filter_and_are_first_n` (in the 310-pass suite) |
| 15 | SC-3/F7 Q3/05-03: `run_finetune --subset_file` — fail-fast validation, TEST split only, before validate_sequences, absent flag = unchanged | ✓ VERIFIED | `pipeline/run_finetune.py:188` flag; `:201` `validate_subset_file` (collect-all-problems: unknown key, non-int incl. bool, negative, out-of-range, non-object, unreadable, + WR-03 Dataset_name-divergence cross-check `:253-259`); `:283` `apply_eval_subset` (test-split-only injectable seam); wiring `:496-504` exits non-zero with `[Error]` before any model load. This verifier ran the named tests `test_subset_validator_refuses_dataset_name_divergence` (PASSED) and re-ran the validator over the committed eval_subsets.json + real registry: **zero problems over 43 tasks** (real-registry no-op confirmed). 11 subset contract tests in the 310-pass suite cover every behavior row incl. absent-flag zero-select and seam ordering |
| 16 | SC-3/REV-07 ordering/05-03: the audit is deterministic (sorted iteration, sort_keys, byte-identical re-runs) | ✓ VERIFIED | This verifier re-ran `uv run --group data python script/audit_n_frequencies.py` over the real local dataset tree (43 dirs, ~3.8M rows): exit 0 and **all four outputs byte-identical** (n_audit.json, n_audit.csv, eval_subsets.json, DATA.md — git diff --exit-code clean) |
| 17 | SC-4/D-16/05-04: E2' data chain closed end-to-end on fixtures — export_runs emits BOTH views from run records; CI replay covers export → both views → aggregate → schema | ✓ VERIFIED | `script/export_runs.py:645+` `export_runs_tree(..., model_output_dir=...)`; default = `input_root / "model_performance"` (`:698-699`) — a sibling of the input root, NEVER dnallm-mark/data (committed data provably untouched); per-model emission `:790-795` with filename alias = registry key (key==name contract); `--model-output-dir` CLI `:825`. `tests/test_ci_replay.py:227+` proves the full D-16 chain (fixture records → task view + per-model view, both schema-valid → summarize over the emitted per-model dir via monkeypatched REGISTRY_PATH → schema-valid comparison, byte-stable). summarize's model_performance reader NOT modified (one reader per view — this verifier confirmed the reader is the pre-existing path) |
| 18 | SC-4/D-18/05-04: one key per model — plant-dnamamba2-BPE normalized to the registry key PlantDNAMamba2-BPE in a dedicated, inventoried commit | ✓ VERIFIED | This verifier: exactly ONE mamba2 results file via `git ls-files "*amba2*"` = `PlantDNAMamba2-BPE_performance.json`; all 4 comparisons carry exactly the key `PlantDNAMamba2-BPE` (42 models each); registry key exists (62 keys). `baseline/d18-alias-inventory.json` live-summed by this verifier: 2029 diffs = alias MISSING/EXTRA 4+4 + FLOAT_ULP 296 (69+68+77+82; max rel 5.9e-15) + permutation churn 1724 (BOOL 174 + FLOAT_BIG 730 + VALUE 820) + VALUE 1 (generated_from restamp) — every category attributed in CHANGELOG's D-18 section. Two dedicated commits (bridge 9918046, alias migration dfb9a80) per plan; manifest GENERATED_FROM restamped to 9918046 (the pre-rename HEAD, 05-02 convention) |
| 19 | SC-4/05-04: run_sweep executes in maintainer-declared priority order (tier 1 = E2E pair) and re-runs exactly failed cells from sweep_failures.json — fake-executor proven, no GPU run | ✓ VERIFIED | `pipeline/run_sweep.py`: `load_priority_tiers` `:383`, `apply_priority_order` `:479` (tier rank composed as PRIMARY sort key over the sorted() fallback), `load_failure_pairs` `:523`; WR-02 Train-falsy refusal in both validators (`:468`, `:528+` — mirrors `_validate_filters`). Committed `pipeline/sweep_priorities.json`: tier 1 = the PIPE-03 E2E pair (plant-dnamamba-6mer + PlantHelixSeek on PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation — registry-key form), tier 2 = the three maintainer-curated representatives (GENERanno-eukaryote-0.5b-base / PlantCAD2-Small-l24-d0768 / Omni-DNA-700M). This verifier ran `test_committed_priorities_degradation_order_fake_executor`: PASSED (tier-1 first → all tier-2 cells → sorted fallback, seeds adjacent). Committed-file content + real-registry key cross-check pinned by tests; clean-manifest zero-cell + fail-fast classes covered in the 310-pass suite |
| 20 | SC-4/05-04: PIPE-02 env-smoke gate exists as a checkable exit-code script — written, linted, type-checked, NEVER executed | ✓ VERIFIED | `pipeline/env_smoke.py`: 5 PASS/FAIL surfaces (torch/transformers version pins parsed from pyproject `[gpu]` via `read_gpu_pins` `:73-108` — never duplicated; dnallm import; CUDA device; all 50 dataset dirs with named missing list; small-tensor matmul) + the maintainer-directed numpy>=2 gate + datasets/pyarrow diagnostic. This verifier: `make lint` + `make typecheck` green with the file in scope (both re-run); grep over tests/ for `env_smoke` = **zero references** (never imported or executed by any test); only py_compile was ever run on it |
| 21 | SC-4/05-04: E2' launch stays behind the dual gate + explicit maintainer authorization; tier-2 maintainer-curated, never agent-invented | ✓ VERIFIED | Both blocking-human gates resolved with verbatim maintainer dispositions recorded in commit messages: 05-01 Task 2 (eslint@10.12.0 + html-validate@11.16.2 exact-pin npx form — maintainer reply `approved`, commit d546e30) and 05-04 Task 4 (tier-2 curation — maintainer selected "每 arena 一代表 (Recommended)", the exact three names, commit 6598e45). No sweep launch anywhere: only --dry-run + fake executors (constraint audit below); nothing in the codebase auto-starts a sweep |
| 22 | SC-4/05-04: partial E2' completion honest by construction — n_seeds disclosed per metric; no vacuous CI below 3 seeds (n=3 → t-interval df=2) | ✓ VERIFIED | `aggregate_seeds` emits `n_seeds` in every stats block (`export_runs.py:195`) with `n < CI_MIN_SEEDS → ci95 None / method "none"` (`:199`); tests assert n_seeds==3 and the failed-seed exclusion (`tests/test_export_runs.py:434-440`). The suite statistics contract (n<3 → null CI) is the vendored, parity-pinned semantics (truth 2) |
| 23 | SC-4/DATA-03/05-04: data-v2 gate fully prepared, never executed automatically; tag created only by the maintainer | ✓ VERIFIED | `script/run_migration_inventory.py` (thin orchestrator looping the untouched comparator; `--write-manifest` SHA256 convention) rehearsed on the real D-18 migration — `baseline/d18-alias-inventory.json` is its committed output. This verifier: `git tag` lists **only `data-v1`** — no data-v2 tag exists, no tag was created/moved/pushed by any agent |
| 24 | SC-4/DATA-01/02/06/05-02: recomputed leaderboard with before/after artifact, CHANGELOG with dates, data_version stamped, footer shows generation date/version | ✓ VERIFIED | DATA-01: `baseline/f6-migration-inventory.json` (live-read: 4 changed × 42 EXTRA_IN_REGEN weighted_score keys = 168, 2 new artifacts, tasks.json identical, zero existing values moved) + the D-18 inventory (truth 18) — two full before/after attributions. DATA-02: `CHANGELOG.md` `[1.1.0] - 2026-10-10` section with data_version, category counts, inventory links, methodology notes + the D-18 section. DATA-06: `dnallm-mark/data/manifest.json` = `{data_version: 1.1.0, generated_from: 9918046…, date: 2026-10-10}` (constants, never a live clock/git call — `summarize_comparison.py:536-541`); footer renders the stamps via `DataAPI.loadDataManifest()` with hide-on-failure null-guard (`main.js:409-413`); live clock gone (grep `toLocaleDateString` main.js = 0). Migration atomicity: this verifier confirmed at commit 3c40de3 all five path groups (4 comparisons / summarize code / models_comparison schema / CHANGELOG / golden fixtures) were last-touched by exactly 3c40de3 — the F6 migration was ONE commit. SC-4's literal "data-v2 tag exists" is intentionally post-E2' (truth 23) — the maintainer gate, not a phase gap |

**Score:** 24/24 truths verified (0 present-but-behavior-unverified)

**Deferred/pending by design (not gaps):** the E2' three-seed execution itself, the `data-v2` tag, and the C(62,2)=1891 permutation family are maintainer-gated post-phase actions per the binding ROADMAP decisions-carried block (dual gate + explicit authorization; never auto-tagged). REQUIREMENTS DATA-03 records exactly this: "complete as PREPARATION". The tier-1/tier-2 sweep, env_smoke, --subset_file, and both export views are proven on fixtures/fake executors — launch day runs only code CI has already exercised.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|--------|
| `.github/workflows/ci.yml` | 4 jobs, SHA-pinned, permissions, timeout 14 | ✓ VERIFIED | All verified (truth 6-7); SHAs re-resolved from official repos by this verifier |
| `tests/fixtures/e2_replay/` | 3×1×3 run-record tree + config + registry slices | ✓ VERIFIED | 30 committed files; the A/B overlap input for the tie rule |
| `tests/test_ci_replay.py` | Chain-replay assertions incl. D-16 full chain | ✓ VERIFIED | Export/aggregate/D-16-chain tests all in the 310-pass suite; `make ci` 73 passed |
| `eslint.config.mjs` | ESLint 10 flat config, zero npm imports, inlined globals | ✓ VERIFIED | Inlined browser/CDN globals; correctness-core rules; no imports (read in full) |
| `.htmlvalidate.json` | html-validate 11 structural config over 6 real shells | ✓ VERIFIED | Structural rules only; six shells named in the CI invocation |
| `Makefile` | ci lane + permutation recipe + lint scope | ✓ VERIFIED | `ci:` lane `:76-77`; data target permutation line `:48`; lint scope includes permutation_tests/run_migration_inventory/audit_n_frequencies/env_smoke `:96` |
| `script/summarize_comparison.py` | Tie rule + weighted_score + manifest emission | ✓ VERIFIED | Truths 1, 24; constants in the Configuration block |
| `script/permutation_tests.py` | Pairwise engine, deterministic artifact | ✓ VERIFIED | Truth 4; `--help` clean, REPO_ROOT-relative CLI |
| `script/run_migration_inventory.py` | Inventory orchestrator + --write-manifest | ✓ VERIFIED | Rehearsed on the real D-18 migration (committed output); unit-tested (test_migration_inventory.py) |
| `schemas/models_comparison.json` | 16-key closed performance block | ✓ VERIFIED | Live-parsed: required = 16 keys incl. weighted_score; additionalProperties false |
| `schemas/permutation_tests.json` + `schemas/data_manifest.json` | Strict new contracts | ✓ VERIFIED | Both additionalProperties:false with required info/pairs and data_version/date/generated_from patterns; registered in test_schemas buckets (suite green) |
| `dnallm-mark/data/manifest.json` | data_version 1.1.0 + generated_from + ISO date | ✓ VERIFIED | Live-read: exactly the three stamped fields; validates against the schema |
| `CHANGELOG.md` | Per-version registry | ✓ VERIFIED | Convention header + [1.1.0] + D-18 sections with counts and inventory links |
| `baseline/f6-migration-inventory.json` + `d18-alias-inventory.json` | Machine-readable before/after | ✓ VERIFIED | Both committed and live-read; every category attributed (168 / 2029) |
| `dnallm-mark/data/permutation_tests.json` | 861-pair published artifact | ✓ VERIFIED | Truth 4 |
| `script/audit_n_frequencies.py` + `DATA.md` + `n_audit.json/csv` + `eval_subsets.json` | F7 census + subsets | ✓ VERIFIED | Truths 12-16; audit re-run byte-identical by this verifier |
| `pipeline/run_finetune.py` | --subset_file fail-fast + test-split seam | ✓ VERIFIED | Truth 15 |
| `pipeline/sweep_priorities.json` | Tier-1 pair + tier-2 three representatives | ✓ VERIFIED | Truth 19; content pinned by tests |
| `pipeline/env_smoke.py` | Never-executed checkable gate | ✓ VERIFIED | Truth 20 |
| `dnallm-mark/data/model_performance/PlantDNAMamba2-BPE_performance.json` | Registry-key-aligned results file | ✓ VERIFIED | Truth 18; exactly one mamba2 file |
| `dnallm-mark/js/main.js` + `config.js` + `data.js` | View toggle + stamped footer | ✓ VERIFIED | Truths 3, 24 |
| `tests/js/main-view-toggle.test.js` | 7 view/footer node tests | ✓ VERIFIED | 15/15 node lane green in this verifier's run |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| .github/workflows/ci.yml | Makefile | make lint/typecheck/test/data | ✓ WIRED | All four jobs invoke Makefile entry points (ci.yml:43-44, 74, 117); no duplicated commands |
| tests/test_ci_replay.py | script/export_runs.py | `export_runs_tree()` over the committed fixture | ✓ WIRED | `:112` call; output validated against schemas/task_performance.json (Draft202012Validator) |
| .github/workflows/ci.yml | eslint.config.mjs | `npx --yes eslint@10.12.0 --config eslint.config.mjs` | ✓ WIRED | ci.yml:98 exact pin; config consumed; proven locally at commit time + non-vacuous by negative probes |
| script/summarize_comparison.py | script/export_runs.py | `from export_runs import …` | ✓ WIRED | `:96` (resolve_dataset_metric); intervals flow exporter→seed_stats→ci_map consumer without re-computation; `load_model_inputs` shared with the permutation engine (one reader) |
| script/permutation_tests.py | models_comparison aggregate view | zscore vectors | ✓ WIRED | `load_zscore_matrix` reuses summarize's reader + `calculate_dataset_stats` — the same zscores the leaderboard sums (stronger than reading the JSON: one normalization) |
| Makefile | script/permutation_tests.py | data target recipe line | ✓ WIRED | Makefile:48, after the summarize line; proven by the verifier's drift no-op |
| dnallm-mark/js/main.js | dnallm-mark/data/manifest.json | `DataAPI.loadDataManifest()` cached fetch | ✓ WIRED | data.js:85-104; footer renders date + data_version; hidden when fetch fails |
| script/audit_n_frequencies.py | pipeline/datasets_info.json | registry join, Dataset_path resolution | ✓ WIRED | 50-key enumeration, missing dirs warned and rowed (live-checked) |
| script/audit_n_frequencies.py | pipeline/eval_subsets.json | common-subset emission | ✓ WIRED | The exact --subset_file input shape; 43/43 N-consistency live-checked |
| pipeline/run_finetune.py | pipeline/eval_subsets.json | --subset_file path argument | ✓ WIRED | Validator + apply seam between load_local_data and validate_sequences (seam-ordering test); real-artifact no-op re-verified |
| script/export_runs.py | script/summarize_comparison.py | per-model files = the existing model_performance reader's input | ✓ WIRED | Emitted files validate against schemas/model_performance.json (test-asserted); reader untouched |
| pipeline/run_sweep.py | pipeline/sweep_priorities.json | --priority-file tier ranks | ✓ WIRED | load_priority_tiers/apply_priority_order; committed file drives ordering (fake-executor test PASSED by verifier) |
| pipeline/env_smoke.py | pyproject.toml | [gpu] pins read at runtime | ✓ WIRED | `read_gpu_pins` parses pyproject (torch==2.11.0/transformers==5.17.0 present); never hardcoded twice |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| 4 models_comparison files | per-model aggregates + weighted_score | model_performance/*.json × registry | Yes — 42 models; weighted_score live-verified present 42/42 ×4 | ✓ FLOWING |
| permutation_tests.json | per-pair p-values | zscore matrix over model_performance via the shared reader | Yes — 861 real pairs, 657 significant | ✓ FLOWING |
| manifest.json | version stamps | migration-commit constants | Yes — 1.1.0 / 9918046 / 2026-10-10 (constants by design, drift-safe) | ✓ FLOWING |
| n_audit.json/csv + DATA.md + eval_subsets.json | census + subset IDs | on-disk dataset CSVs (local, gitignored) | Yes — 43 present tasks, 582,927 IDs; re-run byte-identical | ✓ FLOWING (local maintainer step by design — never in make data/CI) |
| leaderboard page | weighted/rank views + footer stamp | fetched comparison + manifest JSON | Yes — weighted_score read from performance block; footer reads manifest | ✓ FLOWING (visual = pending-UAT 1) |
| exporter per-model view | {model}_performance.json | run-record trees | Fixture-proven (D-16 replay); real records arrive at E2' — the designed boundary | ✓ FLOWING at fixture level; real-record path is the E2' gate |

### Behavioral Spot-Checks (all run by this verifier, its own process)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite both lanes | `make test` | **310 passed (Python) + 15 passed (node), 0 failed, exit 0** | ✓ PASS |
| Lint | `make lint` | All checks passed (ruff over full scope incl. all phase-5 scripts) | ✓ PASS |
| Type check | `make typecheck` | All checks passed (ty over script/, baseline/, tests/, scripts/, pipeline/) | ✓ PASS |
| Drift gate (exact CI step) | `make data` + `git status --porcelain -- dnallm-mark/data/` + `git diff --exit-code` | exit 0; zero porcelain lines; diff clean | ✓ PASS |
| Pinned ci lane | `make ci` | 73 passed, 237 deselected; collect-only selects exactly the 4 intended modules | ✓ PASS |
| Known-defect regression | `pytest tests/test_known_defects.py -q` | 10 passed | ✓ PASS |
| CpG tie at n=3 t-intervals | named test `test_cpg_replica_top_models_tie_under_n3_t_intervals` | PASSED | ✓ PASS |
| Tier degradation order (fake executor) | named test `test_committed_priorities_degradation_order_fake_executor` | PASSED | ✓ PASS |
| WR-03 divergence refusal | named test `test_subset_validator_refuses_dataset_name_divergence` | PASSED | ✓ PASS |
| WR-03 real-registry no-op | validator over committed eval_subsets.json × real datasets_info.json | 43 tasks, zero problems | ✓ PASS |
| Audit determinism (real tree) | `uv run --group data python script/audit_n_frequencies.py` + git diff --exit-code | exit 0; all 4 outputs byte-identical | ✓ PASS |
| Action SHA pinning | `git ls-remote` official repos for the 3 tags | all 3 SHAs match ci.yml verbatim | ✓ PASS |
| Vendored stats verbatim @483a35c | mechanical code-line diff vs `git show 483a35c:dnallm/finetune/sweep.py` | 74/74 vendored code lines verbatim (module's own REPO_ROOT constant aside) | ✓ PASS |
| F6 migration atomicity | `git log 3c40de3 -1 --format=%H` over 5 path groups | all = 3c40de3 (data/code/schema/CHANGELOG/goldens in ONE commit) | ✓ PASS |
| Artifact assertions | live python over committed JSON | 861 pairs / 657 sig; manifest 3 fields; 50-row census 43/7; 43 sorted subset lists, 43/43 N-consistent; one mamba2 key ×4 comparisons; 16-key schema block | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` convention exists in this project; the phase's probe surface is the Makefile gates + named tests, all executed by this verifier in its own process (table above). The REVIEW's independent reruns (drift, inventory, artifact statistics) are corroborated, not relied upon.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| REV-04 | 05-02 | F6 aggregation upgrade (tie rule, dual views, permutation tests; CpG tie) | ✓ SATISFIED | Truths 1-5 |
| REV-06 | 05-01 | CI golden tests — canned replay + parity + spot checks + units; CPU, <15 min, PR-required | ✓ SATISFIED | Truths 6-11. Q1 decision (canned replay, no real training) is the maintainer-accepted CONTEXT form under the CI-feasibility constraint; "PR-required" completes with the branch-protection user-setup item (pending-UAT 2) |
| REV-07 | 05-03 | N-frequency audit + unified eval-subset ID lists accepted by the pipeline | ✓ SATISFIED | Truths 12-16 |
| REV-09 | 05-04 | E2' code-only half (REV-09's requirement text "executes only after REV-01/REV-02 gates" — the gating is enforced by design; execution is the maintainer trigger) | ✓ SATISFIED (code-only half, per ROADMAP plan text and phase goal) | Truths 17-23; the launch checklist exists (05-04 SUMMARY) |
| DATA-01 | 05-02, 05-04 | Recomputed leaderboard with before/after artifact | ✓ SATISFIED | Truth 24 + truth 18: two full migration inventories (F6 + D-18) attribute every diff |
| DATA-02 | 05-02 | CHANGELOG records result-affecting changes with date; data_version stamped | ✓ SATISFIED | Truth 24: [1.1.0] section + manifest stamp + D-18 section |
| DATA-03 | 05-04 | Git tags for data versions | ✓ SATISFIED as PREPARATION (REQUIREMENTS' own annotation) | data-v1 exists; data-v2 tooling rehearsed on D-18; tag reserved for the maintainer gate (truth 23) — the "both tags exist" literal completes at the post-E2' sign-off, by the binding pre-decision |
| DATA-06 | 05-02 | Footer shows generation date/version stamp | ✓ SATISFIED | Truth 24 (code-verified; visual = pending-UAT 1) |
| TEST-04 | 05-01 | GitHub Actions CI (SHA-pinned, matrix, badge) | ✓ SATISFIED | Truths 6-7, 10; 3.13+3.14 matrix is the documented D-07 supersession of the literal 3.12 text |
| TEST-05 | 05-01 | Frontend static checks in CI | ✓ SATISFIED | eslint 10.12.0 + html-validate 11.16.2 exact-pin lanes + node --check (truth 6) |
| TEST-07 | 05-01 | CI drift detection | ✓ SATISFIED | Truth 11 (verifier ran the exact step) |

Orphaned requirements: none — every Phase-5-mapped ID in REQUIREMENTS.md traceability (REV-04/06/07/09, TEST-04/05/07, DATA-01/02/03/06) is claimed by at least one plan's `requirements` field, and none claims completion without evidence.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/test_ci_replay.py | REV-06, REV-09 | all | 0 | no | Behavioral (schema validation, byte-stability, n=3 t-interval values) | PASS |
| tests/test_aggregation.py | REV-04 | 21 | 0 | no | Value (exact ranks, spans, method "t", weighted sums) | PASS |
| tests/test_permutation.py | REV-04 | all | 0 | no | Value (hand-computed exact p-values 0.25/BH 0.375, byte-determinism, exclusions) | PASS |
| tests/test_audit_n.py | REV-07 | 12 | 0 | no | Behavioral (census, filters, missing-dir rows, ID survival, CSV header, determinism) | PASS |
| tests/test_run_finetune_contracts.py | REV-07 | 23 | 0 | no | Behavioral (stub .select recording, validator classes, seam ordering, [Error] exit) | PASS |
| tests/test_sweep.py | REV-09 | 33 funcs | 0 | no | Behavioral (frozen order, tier composition, fake-executor degradation, fail-fast) | PASS |
| tests/test_export_runs.py | REV-09, REV-06 | all | 0 | no | Value/behavioral (schema, parity, byte-stability, n_seeds, failed-seed exclusion) | PASS |
| tests/test_migration_inventory.py, test_schemas.py, test_known_defects.py | DATA-01, contracts, defect locks | all | 0 | no | Value/contract | PASS |
| tests/js/main-view-toggle.test.js | REV-04/DATA-06 | 7 | 0 | no | Value/behavioral (default state, mapping, read-not-recompute, footer hide-on-fail) | PASS |

Disabled tests on requirements: 0 (the single `skipif` at test_golden.py:54 is the environmental node-absence guard; node present, tests ran). Zero `xfail` markers anywhere (all comments referencing xfail describe the historical locks, now unmarked). Circular patterns: none — permutation expected values are hand-computed independent oracles; goldens are chain-produced under the never-hand-edited discipline; the vendored stats are diffed against the external suite source. Assertion strength: value-level throughout. Review-fix tests verified real (WR-02 +2 sweep, WR-03 +1 contracts — named tests re-run by this verifier).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none — 83 phase files scanned) | — | Zero TBD/FIXME/XXX, zero TODO/HACK/PLACEHOLDER, zero stub phrases, zero empty implementations | — | Debt-marker gate: clean |

The three `# noqa: BLE001` in pipeline/env_smoke.py:207,232,380 are new-file per-line justified suppressions on diagnostic blocks that must never abort the gate (documented inline) — not scope-widening on pre-existing files; zero new noqa added to any pre-existing file (git diff verified). Blocker-level anti-patterns: zero.

### Decision Coverage

`check.decision-coverage-verify`: 3/3 trackable CONTEXT.md decisions honored (D-16 → per-model emitter + full-chain replay; D-17 → manifest/OQ2, no-tag/OQ3, tier curation/OQ4, 861-family/OQ5, inventory/OQ6, replay depth/OQ7 all landed; D-18 → alias normalized + inventoried). 0 not honored. Gate non-blocking by design.

### Constraint Compliance (phase-specific)

| Constraint | Status | Evidence (verifier-derived) |
|-----------|--------|------------------------------|
| No pipeline execution (run_finetune never run; run_sweep only --dry-run/validators; no GPU) | ✓ HELD | pipeline/ phase diff = exactly the 5 intended code/data files; `git ls-files` scan for finetuned/sweep_manifest/sweep_failures/run_record/trainer_state/final_metrics outside tests/fixtures = NONE; zero untracked pipeline outputs; all execution evidence in history is fixture/fake-executor/--dry-run form |
| env_smoke.py never imported/executed by any test or agent | ✓ HELD | grep `env_smoke` over tests/ = zero references; lint/typecheck cover it statically; only py_compile was ever run |
| /home/forrest/Github/DNALLM strictly read-only | ✓ HELD | DNALLM repo's post-phase-5 commits (32d242a → bf4656f, Oct 10 18:11-21:03) are all authored by the maintainer (Tao Zhang, own GSD quick tasks); its untracked .planning/tmp+graphs files predate phase 5 (Oct 2-7); zero phase-5 commits touch DNALLM paths; the suite source was only read (`git show 483a35c`) |
| No data-v2 tag (or any tag) created/moved/pushed by an agent | ✓ HELD | `git tag` = data-v1 only |
| ruff + ty gating real (memory: lint AND type-check gates) | ✓ HELD | Both re-run green by this verifier; all new scripts in lint scope (Makefile:96) and ty scope; zero new noqa on pre-existing files |
| No new npm/pip installs; npx only via the maintainer-approved exact pins | ✓ HELD | tech-stack added: [] in all four SUMMARYs; the only npm surface = eslint@10.12.0 + html-validate@11.16.2 exact pins (Task 2 gate, `approved`) |
| Weighted view never computed client-side; no live clock/git in the data path; no hand-edited goldens | ✓ HELD | Truths 3, 5, 24; goldens re-chained through the chain only (drift no-op proves it) |
| Drift gate green at every migration commit | ✓ HELD | Verifier's make data no-op over the final tree; the REVIEW independently reran it mid-phase; WR-01 regeneration commit proven no-op post-commit |

### Known-Defect Regression

`tests/test_known_defects.py`: **10 passed** (this verifier's run) — zero xfail markers, all locks permanently green. The defect ledger has not grown: the phase review found 0 critical / 3 warnings (all FIXED: WR-01 axis disclosure regenerated, WR-02 Train-falsy refusal +2 tests, WR-03 Dataset_name cross-check +1 test) / 4 info (IN-04 fixed; IN-01..03 documented-open in 05-REVIEW-DISPOSITION.md with explicit E2'-time routing). WINDOWS phase-5 entries: 3 unrun-verify (by-design never-executed surfaces) + 1 deviation (fixed). No unaddressed defect entries for phase-5 files.

### Pending UAT — Phase UAT Gate Items

UAT-pending items are not failures; they are routed to the phase UAT gate per the project's phase 3/4 pattern and recorded in the WINDOWS ledger:

1. **05-02 Task 3 visual localhost check** (WINDOWS entry 11, unrun-verify)
   **Test:** `bash start-server.sh`, open http://localhost:8080
   **Expected:** Leaderboard opens on the Weighted view; the Raw Rank toggle re-sorts the table and re-labels the scatter y-axis in one click; the footer shows the stamped date + data v1.1.0 (no today's-date behavior)
   **Why human:** Visual judgment; the mechanical seams (default state, view→sort mapping, weighted read-not-recompute, footer stamp + hide-on-fail) are pinned by 7 node tests — the browser-level rendering is the untested layer this phase (no Playwright pass was in scope)

2. **First real GitHub-runner execution of ci.yml + branch protection** (WINDOWS entry 10; 05-USER-SETUP.md)
   **Test:** Maintainer pushes; then Settings → Branches → require the four ci.yml checks on main (NOT the 3.14 probe leg)
   **Expected:** Badge green; every job under 15 minutes; checks required before merging (REV-06 "PR-required" clause completes)
   **Why human:** Runner-side behavior is not locally provable before the first push; all lane commands were proven locally at commit time and re-verified by this verifier

3. *(E2'-launch scope, post-phase by design — WINDOWS entry 12:)* env_smoke on GB10, the sweep launch itself, first real --subset_file consumption, and the data-v2 tag remain behind the maintainer dual gate. Listed for the orchestrator's visibility, not as phase UAT.

### Gaps Summary

None. No truth FAILED, no artifact is MISSING/STUB, no key link is NOT_WIRED, and no blocker anti-pattern was found. All four verification gates re-ran green under this verifier (310+15 tests, lint, typecheck, drift no-op), the pinned ci lane runs 73 green, the N-audit re-ran byte-identical over the real dataset tree, the vendored statistics remain verbatim against the read-only suite source, the F6 migration's one-commit atomicity and both migration inventories' full attribution were mechanically confirmed, and all three action SHAs were independently re-resolved from the official repos. The E2' launch and data-v2 tag are the maintainer's gated actions by binding pre-decision — preparation for both is complete and rehearsal-proven. Two pending-UAT items (the 05-02 visual check and the first runner execution + branch protection) are routed to the phase UAT gate and are not verification failures.

## VERIFICATION PASSED

---

_Verified: 2026-10-10T13:19:02Z_
_Verifier: Claude (gsd-verifier)_
