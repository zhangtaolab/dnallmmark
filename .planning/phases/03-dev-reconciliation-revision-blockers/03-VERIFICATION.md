---
phase: 03-dev-reconciliation-revision-blockers
verified: 2026-10-09T18:45:17Z
status: human_needed
score: 29/29 must-haves verified
covered_files: [".planning/phases/03-dev-reconciliation-revision-blockers/03-01-PLAN.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-01-SUMMARY.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-02-PLAN.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-02-SUMMARY.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-03-PLAN.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-03-SUMMARY.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-04-PLAN.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-04-SUMMARY.md", "Makefile", "README.md", "pipeline/datasets_info.json", "pipeline/dnallmmark_pipeline.py", "pipeline/models_info.json", "pipeline/run_finetune.py", "pipeline/run_sweep.py", "pyproject.toml", "script/convert_registry.py", "script/make_dev_splits.py", "tests/conftest.py", "tests/fixtures/export_chain/defect_species_performance.json", "tests/test_convert_registry.py", "tests/test_dev_splits.py", "tests/test_known_defects.py", "tests/test_model_registry.py", "tests/test_registry_unification.py", "tests/test_run_finetune_contracts.py", "tests/test_sweep.py", "uv.lock"]
covered_digest: "v3:sha256:20a472a6ce4721878e69f850adb54ceb424ac7d1d2cdea0510db7d209dbd52c5"
behavior_unverified: 0
overrides_applied: 0
gaps: []
deferred:
  - truth: "PIPE-02 full form — GPU env reproducibly BUILT (uv sync --group gpu + dnallm from local clone) and PIPE-03 full form — two-model E2E producing schema-valid performance JSON"
    addressed_in: "Phase 5 (E2E gate, when model runs resume on a stabilized DNALLM suite)"
    evidence: "ROADMAP SC-6/SC-7 '[DEFERRED 2026-10-09 — no model runs until the DNALLM suite stabilizes]'; CONTEXT D-05/D-06; REQUIREMENTS.md keeps both Pending. This phase owes and landed ONLY the deferred metadata forms (verified: [gpu] group definition, PlantHelixSeek entry)."
  - truth: "WR-03 ACGT-only alphabet divergence and WR-04 unported quirk registries (limited_length, safetensors membership, tier rounding)"
    addressed_in: "Phase 4 (quirk-parity surface)"
    evidence: "03-REVIEW-DISPOSITION.md: 'skipped: deferred Phase 4 (maintainer-sanctioned)'; ROADMAP Phase 4 goal covers the correctness core."
  - truth: "README.md Run Pipeline exporter sentence ({model_name}_performance.json claim) still describes the deprecated pipeline"
    addressed_in: "Phase 4 (REV-03 exporter)"
    evidence: "deferred-items.md row routed to Phase 4; ROADMAP Phase 4 requirements include REV-03."
  - truth: "17 remaining card-absent model entries in models_info.json lack card fields"
    addressed_in: "Phase 4"
    evidence: "D-10 ('card fields may be temporarily absent for txt-only models (Phase 4 fills)'); enumeration pinned by tests/test_registry_unification.py."
  - truth: "7 unlocatable GUE dataset dirs (partial extraction) and dataset double-nesting normalization"
    addressed_in: "Phase 5 E2E gate"
    evidence: "D-05 ('Dataset double-nesting normalization defers with the E2E'); make_dev_splits --check WARNING-excludes them; run_sweep.py docstring documents flattening as not-executed."
human_verification:
  - test: "Confirm the parallel activity in /home/forrest/Github/DNALLM (commits 483a35c..d6350b6, docs(11)/fix(11)/docs(12), 2026-10-09/10) is the maintainer's own parallel suite-stabilization session, not writes made by this phase"
    expected: "Maintainer affirms those DNALLM commits are theirs (the documented parallel workstream per D-05); the no-writes-under-DNALLM prohibition then stands fully attributed"
    why_human: "Descriptor-less prohibition disposed flagged-unverified: our repo's commits provably touch zero DNALLM paths and the env provably lacks torch/dnallm, but both repos share the git identity 'Tao Zhang', so authorship of the DNALLM-side commits is not programmatically attributable. Verifier's non-authoritative verdict: NO violation found (commit subjects are the DNALLM project's own phase 11/12 numbering, matching the documented parallel workstream)."
  - test: "Spot-check the D-04 frontend review verdict ('CLEAN, 4 observations') for commit 8d99daf in 03-FRONTEND-REVIEW.md"
    expected: "A human read of git show 8d99daf agrees the log10/linear toggle introduces no new confirmed frontend defect beyond the 4 recorded observations"
    why_human: "The executor's coverage record declared human_judgment: true on this verdict (a static-review judgment). The verifier independently corroborated the mechanical claims (scope exactly 3 files; null-guarded scaleSwitch; optional-chaining data reads; no innerHTML in the scatter-chart hunks; delegation binding on static markup) and found nothing contradicting CLEAN — that corroboration is a non-authoritative second review, not a substitute for the declared human spot-check."
---

# Phase 3: Dev-Branch Reconciliation & P0 Revision Blockers Verification Report

**Phase Goal:** The dev-branch pipeline rewrite (run_finetune.py @ dev c6b3137) is reconciled with the audited main lineage — Phase 1/2 contracts and tests survive the merge — and the manuscript-revision P0 blockers (dev splits, seed-isolated sweep, old-pipeline retirement) land. **Verified against the binding 2026-10-09 D-05 CODE-ONLY scope** (PIPE-02 = [gpu] group definition as code only, no install; PIPE-03 = PlantHelixSeek models_info entry as metadata only, no model runs), not the full original goal sentence.
**Verified:** 2026-10-09T18:45:17Z
**Status:** human_needed (all 29 must-have truths VERIFIED; 2 human items — 1 unverified-prohibition attribution, 1 declared review-verdict judgment)
**Re-verification:** No — initial verification (no prior VERIFICATION.md existed)

## Goal Achievement

Verification performed at HEAD `7c7dfaf` on `autorun`. Suite state at verification time, reproduced by the verifier: `make test` = **193 passed + 5 xfailed + node lane 2 pass**; `make lint` clean; `make typecheck` clean; `uv lock --check` exit 0; dev env provably torch-free.

### Observable Truths

**Plan 03-01 (merge + F10 + D-03 pivot + D-04) — 6 truths**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC-1/D-02: dev@c6b3137 merged; data tree byte-identical to pre-merge; 6 dev-added files absent; bucket pins + enum self-checks hold; suite green | ✓ VERIFIED | Merge commit `41bf49e` (parents `360be65` + `c6b3137`) with the full per-path-group conflict inventory in its message; `git diff 360be65 HEAD -- dnallm-mark/data` and `-- baseline/` both **empty**; `NO_DEV_DATA_FILES` (ls-files of all 6 paths empty); `c6b3137` is an ancestor of HEAD; `make test` green with bucket pins/enum self-checks live in `tests/test_schemas.py` (passing within 193). Suite count grew from the 136 baseline as plans 02-04 added 57 tests — expected evolution, not a regression; the baseline-reproduction requirement was scoped to the merge commit and recorded in its message. |
| 2 | SC-2/D-03: AUD-01-P0 lock pivoted to export-chain contract (fixture-injectable, xfail strict, non-vacuous, unmarked shape companion) | ✓ VERIFIED | `test_aud01_species_matches_dataset_arena_category` is xfail(strict) in the suite (5 xfailed); `pytest --runxfail` exits 1 with this test **first** in the FAILED list (fails on the `athaliana` defect — non-vacuous); companion `test_aud01_contract_fixture_has_expected_shape` passes (the 1 passed); fixture `tests/fixtures/export_chain/defect_species_performance.json` exists. |
| 3 | SC-2/D-03: old AST anchor lock, companion, `_find_construction_sites` retired in the same commit; pivot documented in module docstring | ✓ VERIFIED | grep for `_find_construction_sites`, `test_producer_writes_dataset_species_not_model_organism`, `test_aud01_construction_site_anchor` → 0 matches in `tests/test_known_defects.py`; module docstring documents the D-03 pivot and same-commit F10 retirement (confirmed in deprecation banner cross-reference). |
| 4 | SC-3/REV-10/F10: deprecation docstring names run_finetune.py; README usage + structure tree name it as benchmark entry point | ✓ VERIFIED | `pipeline/dnallmmark_pipeline.py` opens with the DEPRECATED module docstring naming `pipeline/run_finetune.py` (retained read-only for attribution + FLOPs reference); README carries 4 `run_finetune.py` mentions (usage command, args, structure tree, sweep docs). |
| 5 | PROBE[REV-10/empty]: deprecated file retained, compiles, deprecation notice surfaced | ✓ VERIFIED | File tracked, `py_compile` → COMPILES. **Info note:** the deprecation is a module docstring (surfaced via `pydoc`/`__doc__`/import), not a runtime `print` — direct execution raises ModuleNotFoundError at the module-level `torch`/`dnallm` imports (L35-37) in any env without the GPU stack, which itself prevents accidental legacy runs. The plan's operative acceptance checks (head-12 grep, py_compile, README grep) all pass. |
| 6 | PROBE[REV-10/encoding]: datasets_info.txt arrived from dev CRLF byte-identical, then retired by 03-02 | ✓ VERIFIED | `git show 41bf49e:pipeline/datasets_info.txt` hash == `git show origin/dev:pipeline/datasets_info.txt` hash (byte-identical at the merge commit); file since deleted by D-10 retirement (never rewritten — no write-preservation concern). |

**Plan 03-02 (D-10 unification + F1 dev splits + refusal guard) — 7 truths**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 7 | SC-D10a/D-10 single source: models_info.json 62 entries (ops four complete, key==Model_name), datasets_info.json 50 entries (all operational columns, key==Dataset_name), zero pipeline/*.txt\|*.csv tracked | ✓ VERIFIED | Direct JSON inspection: 62/50 entries, ops-four complete on all models, `Index/Dataset_path/Train/Test/Dev/type/labels/length/metric/Category` complete on all datasets, key==name-field everywhere; `git ls-files 'pipeline/*.txt' 'pipeline/*.csv'` empty (NO_TABULAR_REGISTRIES). |
| 8 | SC-D10b/D-10 read site: json.load only, dict iteration, field keys unchanged, pandas import removed, argparse help updated | ✓ VERIFIED | `grep read_table` → 0; no pandas import; `json.load` over `base_dir + datasets_info.json` / `models_info.json` at L316/L320; loops iterate `.items()` (L411 models, L447 datasets) reading all field names as dict keys; argparse help strings name the .json registries (L112, L183). |
| 9 | SC-D10c contract test: registry-unification test green, pins 62/50, card-absent enumeration, key==name | ✓ VERIFIED | `tests/test_registry_unification.py` present and green within the 193-test suite; docstring documents CSV as on-demand projection only. |
| 10 | D-03/D-10 retarget: `_load_category_map` reads Category from datasets_info.json in the same commit as .txt deletion; lock still non-vacuous | ✓ VERIFIED | Retargeted helper green in suite; `--runxfail` still exits 1 with the species lock failing; companion green. |
| 11 | SC-4/REV-01/F1: 18 Dev-empty tasks get stratified 10% dev splits (seed=42, reproducible); registry Train/Dev updated; two-layer test-as-eval enforcement | ✓ VERIFIED | Registry: 50/50 entries with truthy Dev; 57 dev.csv on disk (18 registry-driven + documented extras in non-registry dirs); `make_dev_splits.py --check` exits 0 ("OK: registry/disk agreement for 43 task(s)", 7 unlocatable GUE dirs WARNING-excluded per documented deferral); determinism/stratification/rare-class/count-guard/idempotency pinned by 13 green tests; **suite-side EVAL-01 verified read-only**: `git show 483a35c:dnallm/finetune/trainer.py` L568+ carries the `allow_test_as_eval` gate (test split serves as eval only when explicitly true, else eval disabled/hard-error path). |
| 12 | REV-01 part 2: refusal guard (REFUSED SystemExit naming task + EVAL-01 contract + remediation) before model load; config purity | ✓ VERIFIED | Guard at L486-495 raises `SystemExit` with REFUSED-prefixed message naming the dataset, the EVAL-01 contract, and make_dev_splits.py; source index precedes the `load_model_and_tokenizer(` call site (L527) and `data_dict = {}` (L605) — pinned by green `test_dev_refusal_guard_precedes_data_dict`; `allow_test_as_eval` appears in neither finetune YAML (grep 0; `test_configs_never_enable_test_as_eval` green). |
| 13 | PROBE[REV-01/ordering]: dev.csv and rewritten train.csv preserve original row order (byte-stability auditable) | ✓ VERIFIED | Order-preservation is an explicit test target in `tests/test_dev_splits.py` (green, 13 tests incl. byte-identical re-carve determinism); docstring documents row-order-preserving selection. |

**Plan 03-03 (deferred PIPE-02/PIPE-03 metadata + ty) — 8 truths**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 14 | SC-6 deferred form/PIPE-02: [gpu] group as code only — torch==2.11.0 + transformers==5.17.0 exact, pytorch-cu130 index (explicit=true, torch-scoped), replacing [pipeline], dnallm absent, never installed | ✓ VERIFIED | pyproject: `gpu = ["torch==2.11.0", "transformers==5.17.0"]` with D-05/REL-02/dnallm-absence comment above the declaration; zero `pipeline =` group; `[[tool.uv.index]] pytorch-cu130` with `explicit = true`; `[tool.uv.sources]` torch marker-gated; `default-groups = ["data"]`; `find_spec('torch') is None` in the dev env (no-torch-in-env). |
| 15 | PROBE[PIPE-02/ordering]: uv.lock in sync, CPU-safe metadata-only resolution | ✓ VERIFIED | `uv lock --check` exits 0 (71 packages resolved in 1ms — no download, no build). |
| 16 | PROBE[PIPE-02/empty]: [gpu] definition complete standalone; rebuild later = uv sync --group gpu + documented local-clone dnallm install | ✓ VERIFIED | The group's comment documents exactly the rebuild recipe (local dev clone `../DNALLM`, branch `revision`); lock carries the full resolution (torch 2.11.0+cu130, transformers 5.17.0, ty 0.0.85). |
| 17 | Maintainer ty toolchain directive: ty>=0.0.85 in dev, [tool.ty] config, make typecheck zero diagnostics | ✓ VERIFIED | `ty>=0.0.85` in dev group; `[tool.ty]` with python 3.13, `extra-paths ["script","baseline","pipeline"]`, replace-imports-with-any (incl. torch_npu, empirically added), `src.include` covering script/baseline/tests/scripts/pipeline; `make typecheck` → "All checks passed!". |
| 18 | SC-7 deferred form/PIPE-03/D-09/D-10: PlantHelixSeek gains complete 11-key card in the unified registry (62 total; 45 complete cards; 17 card-absent) | ✓ VERIFIED | Entry carries exactly 16 keys (ops four + Model_name + 11 card keys), every card field non-empty after str-strip, numeric trio int/int/int (470 / 1 / 8192); 45 complete cards of 62; `test_registry_unification` enumeration 18→17. **External-source check (verifier-fetched live):** the ModelScope card confirms 470M params, HelixSeek (Transformer+KDA+MLA+MoE), 8,192 bp context, plants, MLM, zhangtaolab/PlantHelixSeek links literally; `tokenizer: singlebase` / `mean_token_len: 1` are the semantic encoding of the card's "single-nucleotide" vocabulary and agree with the maintainer operational priors. |
| 19 | PROBE[PIPE-03/adjacency]: exactly 62 entries after the fill; leaderboard data tree NOT regenerated (model_performance bucket stays 42) | ✓ VERIFIED | 62 entries counted; `git diff 360be65 HEAD -- dnallm-mark/data` empty; bucket pins 42/47/4/1 green in the suite. |
| 20 | PROBE[PIPE-03/empty]: no empty/null/placeholder field; registry test rejects empties; halt-not-land rule | ✓ VERIFIED | All 11 card values non-empty (verified directly + `test_model_registry` non-empty assertion green); values trace to the fetched card or operational priors. |
| 21 | PROBE[PIPE-03/ordering]: fill preserves sort_keys serialization; diff is exactly the PlantHelixSeek entry | ✓ VERIFIED | Fill commit `4248e54` touches models_info.json with 12 insertions / 1 deletion (one-entry hunk); registry loads with consistent sort_keys layout. |

**Plan 03-04 (F2/G1 + D-07 + D-11 + D-08 + sweep runner) — 8 truths**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 22 | SC-5/REV-02/G1: outdir = {root}/{model}/{task}/seed_{seed}/; resume marker seed-scoped (seed 43 runs after seed 42's marker) | ✓ VERIFIED | `outdir = f"{save_root}/{model_save_name}/{dataset_name}/seed_{seed}/"` at L597; the untouched resume check `os.path.exists(outdir + "trainer_state.json")` at L601 reads the seed-scoped path — seed isolation follows from the path arithmetic (no hidden state); `test_seed_isolated_output_layout` green (asserts both substrings + ordering). |
| 23 | D-11 cross-MODEL head-config leak fixed: base config reloaded at model-loop top, exactly once, before the custom-head override; no head_config residue | ✓ VERIFIED | Exactly ONE `load_config("./finetune_config.yaml")` at L421, inside the model loop (header L411), before the `evo2_1b_base`/`megaDNA_updated` override (L432-433); **end-to-end static chain closed**: dnallm's `load_config` (suite source, read-only) constructs fresh `TaskConfig`/`TrainingConfig` dataclass instances from a fresh `yaml.safe_load` on every call — no caching — so each model's config object graph is new and residue cannot cross models; `test_base_config_reload_is_per_model` green. |
| 24 | D-07 cross-DATASET grad_accum leak fixed: YAML default snapshotted per model, reset at dataset-loop top before the adjustment read | ✓ VERIFIED | Snapshot `default_grad_accum` at L443 (deliberately AFTER the with_head reload — the WR-01 fix-loop refinement, justification comment in code: head models must reset to their with_head default); reset at L455 as the first statement of the dataset-loop body; word-boundary adjustment read at L672 (reset precedes it); `test_grad_accum_reset_per_dataset` green. |
| 25 | SC-5/REV-02 sweep runner: run_sweep.py drives model x task x seed; argv-list subprocess cwd=pipeline/; run_record (status/metrics verbatim/vram_probe nulls/git_commit/timestamps); skip on trainer_state; failures manifest; sorted+sort_keys manifest | ✓ VERIFIED | `pipeline/run_sweep.py` (637 lines): `enumerate_matrix` (L197), `build_argv` (L288), `launch_subprocess` (L312), `run_matrix` (L395, injectable executor), `main` (L542); WR-12 no-overwrite, WR-13 final_metrics-before-marker (contract test L308), WR-11 corrupt-metrics isolation, CR-02 exit-0-no-metrics=failed, WR-06 failures-manifest hygiene all landed with tests (19 sweep tests green in suite). |
| 26 | REV-02 dry-run: enumerates matrix, writes ONLY the manifest — CPU-testable, no subprocess | ✓ VERIFIED | Verifier CLI smoke over the real registries: exit 0, `sweep_manifest.json` created with both seed_42 and seed_43 cells, and the output root contains ONLY the manifest (no cell dirs, no records). |
| 27 | D-08: all ruff findings resolved (genuine fixes except 3 justified BLE001 noqa); make lint widened; zero config suppression | ✓ VERIFIED | `make lint` (widened scope: tests/ + make_dev_splits.py + run_finetune.py + run_sweep.py) → "All checks passed!"; `grep tool.ruff pyproject.toml` → 0; exactly 3 noqa lines at the three designed isolation sites (L537 model-load `break`, L744 encode `continue`, L810 train `continue` — control flow verified preserved); CR-01 fp32-only quirk registry + forced-precision code present with contract test. |
| 28 | PROBE[REV-02/ordering] determinism: sorted iteration + sort_keys serialization → byte-identical manifests | ✓ VERIFIED | Byte-determinism is a pinned test target in `tests/test_sweep.py` (green); manifest holds only matrix+statuses (timestamps/git_commit live in run_record only). |
| 29 | D-06/E2' gating preserved: no model runs of any kind; real mode never invoked | ✓ VERIFIED | No `finetuned/` dir, no `run_record.json` / `final_metrics.json` / `sweep_manifest.json` anywhere on disk; tests use fake executors + --dry-run only; verifier probes used --dry-run; torch/dnallm absent from every env this repo manages. |

**Score:** 29/29 truths verified (0 present-behavior-unverified)

The G1/D-07/D-11 leak-fix truths (22-24) were classified VERIFIED rather than behavior-unverified because the complete static chain was closed end-to-end: the loop-ordering invariants are pinned by green source-contract tests in our tree, AND the one runtime property source tests cannot see (whether dnallm's `load_config` returns fresh objects per call) was verified by reading the suite's constructor at the cited revision — it builds new dataclass instances from a fresh `yaml.safe_load` every call. First live execution remains, by binding directive D-05, deferred to the E2E gate (see Deferred).

### Deferred Items

Pre-declared deferred scope (binding D-05 directive and maintainer-sanctioned review dispositions — NOT gaps):

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | PIPE-02 full env build + PIPE-03 two-model E2E | Phase 5 / E2E gate | ROADMAP SC-6/SC-7 "[DEFERRED 2026-10-09]"; REQUIREMENTS.md correctly keeps both Pending; this phase owed and landed the metadata-only forms |
| 2 | WR-03 ACGT-only alphabet; WR-04 unported quirk registries | Phase 4 | 03-REVIEW-DISPOSITION.md maintainer-sanctioned deferrals |
| 3 | README exporter sentence (pre-REV-03 wording) | Phase 4 (REV-03) | deferred-items.md routed row; ROADMAP Phase 4 requirements |
| 4 | 17 remaining card-absent model entries | Phase 4 | D-10 decision; enumeration pinned by test_registry_unification.py |
| 5 | 7 unlocatable GUE dirs + dataset double-nesting flattening | Phase 5 E2E gate | D-05; --check WARNING-exclusion documented; run_sweep docstring documents non-execution |

### Flagged Assumptions (surfaced per plan frontmatter — not failures)

1. **[REV-01/unclassified]** Split-generator edge semantics beyond tested ones (empty train.csv, label/registry count disagreement, mid-write interruption) — cannot occur on the 18 vetted tasks; re-review if reused on unvetted datasets.
2. **[D-10/derived Model_path]** The 6 json-only entries' `Model_path = models/{key}` is convention-derived, not verified against on-disk model dirs (gitignored, absent until runs resume) — verify at the E2E gate before first real run (plant-dnamamba-6mer is one).
3. **[D-10/card-absent 18→17]** Card fields deliberately absent for 17 txt-only models; exact enumeration pinned by test so the gap is explicit.
4. **[D-10/name normalization]** The 3 gene_exp bare names normalized to Source__task form via converter `--rename-name`; Dataset_path joins both sides (verified equal at unification).
5. **[REV-02/unclassified]** Sweep edge semantics (two concurrent sweeps over one root; killed subprocess leaving partial seed dir — accepted default: re-run; empty filter lists — now hard-failed by WR-14) — flagged for the Phase 5 E2E gate review.
6. **[Suite aggregator adoption]** Whether Phase 4/5 adopts dnallm's `run_seeds`/statistics.json aggregator is deferred to REV-03/E2' planning; this phase guarantees only the layout/record contract.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| Merge commit w/ conflict inventory | 41bf49e on autorun | ✓ VERIFIED | 2 parents, full per-path-group table in message |
| tests/fixtures/export_chain/defect_species_performance.json | defect-bearing result-JSON fixture | ✓ VERIFIED | 1,687 bytes; lock fails on its athaliana defect |
| 03-FRONTEND-REVIEW.md | D-04 review record | ✓ VERIFIED | 9-hunk enumeration, 13 AUD-ID cross-refs, explicit clean verdict |
| convert_registry.py D-10 extensions + tests | --rename-name, --derive-operational, stock pins | ✓ VERIFIED | 12 converter tests green in suite |
| tests/test_registry_unification.py | single-source contract | ✓ VERIFIED | green; pins 62/50, enumeration, key==name |
| Unified models/datasets_info.json; .txt retired | 62/50 single-source JSON | ✓ VERIFIED | verified directly; zero tabular registries tracked |
| run_finetune.py json read site + REFUSED guard | registry load + fail-fast | ✓ VERIFIED | L316/320 json.load; L486-495 guard before model load |
| script/make_dev_splits.py + tests | split generator + --check | ✓ VERIFIED | 472 lines; 13 tests green; --check exit 0 |
| tests/test_run_finetune_contracts.py | guard + purity + 3 leak contracts | ✓ VERIFIED | 8 tests (guard, purity, seed layout, reload, grad_accum, fp32, presence, WR-13 ordering) |
| pipeline/run_sweep.py + tests | matrix driver + dry-run + fake-executor proof | ✓ VERIFIED | 637 lines; 19 tests green; CLI smoke passed |
| pyproject [gpu] + [tool.ty] + Makefile typecheck/lint | deferred-form code + toolchain | ✓ VERIFIED | all blocks present; both targets clean |
| tests/test_model_registry.py | PlantHelixSeek integrity pins | ✓ VERIFIED | green (16-key shape, non-empty, prior agreement, 45 cards) |
| Deprecated dnallmmark_pipeline.py + README rename | F10 | ✓ VERIFIED | banner + compiles + README 4 mentions |

All artifacts exist, are substantive (no stubs — every writer is exercised by green tests or direct CLI probes), and are wired into the suite/Makefile gates.

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| README pipeline usage | pipeline/run_finetune.py | usage command + structure tree | ✓ WIRED | 4 mentions incl. run_sweep dry-run/real invocations (WR-08 cd-pipeline documented) |
| AUD-01 contract lock | fixture + datasets_info Category | _load_category_map over unified json | ✓ WIRED | --runxfail proves the join fails on the defect entry |
| run_finetune registry reads | unified json registries | json.load at L316/320, .items() loops | ✓ WIRED | zero read_table; field keys unchanged |
| run_finetune refusal guard | registry Dev value, pre-model-load | L486-495 before L527 call | ✓ WIRED | index-precedence test green |
| registry Train counts | num_train_data math | --check registry/disk agreement | ✓ WIRED | 43 tasks agree; 5 pre-existing count defects corrected (disk-authoritative) |
| run_sweep subprocess argv | run_finetune CLI | build_argv list, cwd=pipeline/ | ✓ WIRED | argv-capture test; never shell |
| run_sweep expected layout | run_finetune outdir construction | seed_{seed}/ convention both sides | ✓ WIRED | two-sided fake-executor test |
| run_record metrics | final_metrics.json verbatim | no translation layer | ✓ WIRED | key-set identity test |
| make lint/typecheck | widened scope incl. pipeline/ | Makefile targets + [tool.ty] | ✓ WIRED | both exit clean |
| sweep layout | dnallm run_seeds protocol | {out_root}/{model}/{task}/seed_{s}/ | ✓ WIRED | layout contract matches suite protocol (aggregation adoption deferred, flagged) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| models_info.json | 62 entries | dev json (44 cards) + dev txt (56 rows) via converter | ✓ | FLOWING (unified, test-pinned) |
| datasets_info.json | 50 entries | dev txt+json merged; Train/Dev from on-disk CSV counts | ✓ | FLOWING (--check agreement 43/43 locatable) |
| dev splits | 57 dev.csv | carve_stratified_dev over real train.csv | ✓ | FLOWING (deterministic seed=42) |
| sweep manifest | planned cells | unified registry keys x truthy-Train datasets | ✓ | FLOWING (CLI smoke over real registries) |
| run_finetune registries | models/datasets dicts | json.load of the unified files | ✓ | FLOWING (module-level read proven) |

No static returns, no hardcoded data, no mocks in any data path.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite | make test | 193 passed + 5 xfailed + node 2 pass | ✓ PASS |
| Lint gate (widened) | make lint | All checks passed (rc=0) | ✓ PASS |
| Type gate | make typecheck | All checks passed (rc=0) | ✓ PASS |
| Lock non-vacuity | pytest tests/test_known_defects.py --runxfail | exit 1; species lock first FAILED; 5 locks fail, companion passes | ✓ PASS |
| Sweep dry-run CLI | run_sweep.py --dry-run over real registries | exit 0; manifest w/ 2 seed cells; only manifest written | ✓ PASS |
| WR-14 empty-flag fail-fast | run_sweep.py --models , --dry-run | exit 1; flag+raw value in message; no output root | ✓ PASS |
| Registry/disk agreement | make_dev_splits.py --check | exit 0; OK 43 tasks; 7 WARNING-excluded | ✓ PASS |
| Lock sync | uv lock --check | exit 0 | ✓ PASS |
| D-05 env purity | find_spec('torch') in dev env | None (no torch in env) | ✓ PASS |
| Card external fidelity | live fetch of modelscope.cn PlantHelixSeek README | 9/11 literal + 2 semantic matches | ✓ PASS |
| EVAL-01 suite contract | git show 483a35c:dnallm/finetune/trainer.py | allow_test_as_eval gate present at cited range | ✓ PASS |

### Probe Execution

All PROBE[...] must-have truths were re-executed by the verifier in its own process (commands and outputs in the tables above — merge-inventory probe via `git show 41bf49e`, encoding probe via blob-hash comparison, ordering probes via line-index verification, empty-adjacency probes via direct content checks). No probe claimed in SUMMARY.md was taken on trust.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| REV-01 | 03-02 | F1 dev splits + refusal of silent test fallback | ✓ SATISFIED (Complete in REQUIREMENTS.md) | 50/50 Dev truthy; 18 splits on disk; guard + purity + suite-side EVAL-01 verified |
| REV-02 | 03-04 | F2 seed-isolated sweep + per-run records + failure manifest | ✓ SATISFIED (Complete) | seed_{seed}/ layout, resume seed-scoped, runner + records verified |
| REV-10 | 03-01 | F10 old-pipeline deprecation + README entry point | ✓ SATISFIED (Complete) | banner + compiles + README |
| PIPE-02 | 03-03 | GPU env reproducibly buildable | ✓ DEFERRED-FORM SATISFIED — requirement correctly **Pending** | [gpu] group definition landed as code (no install); full build deferred per D-05 to E2E gate |
| PIPE-03 | 03-03 | Two-model E2E validation | ✓ DEFERRED-FORM SATISFIED — requirement correctly **Pending** | PlantHelixSeek entry landed as metadata (16-key, sourced from D-09 card); runs deferred per D-05 |

Orphaned requirements: NONE — REQUIREMENTS.md maps exactly PIPE-02/03/REV-01/02/10 to Phase 3, all five claimed by plans. The REQUIREMENTS.md checkbox discipline is exactly right: REV-01/02/10 checked Complete; PIPE-02/03 left unchecked (Pending) with the deferred form landed — neither falsely greened nor lost.

### Decision Coverage

Decision-coverage gate result: **11/11 CONTEXT.md decisions (D-01..D-11) honored** by shipped artifacts (query: check.decision-coverage-verify; blocking: false, by design).

### Test Quality Audit

| Test File | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|--------|---------|----------|-----------------|---------|
| tests/test_sweep.py | 19 | 0 | 0 | Value/Behavioral (exit codes, file contents, byte-determinism) | OK |
| tests/test_run_finetune_contracts.py | 8 | 0 | 0 | Value (source-index ordering, exact-once counts) | OK |
| tests/test_dev_splits.py | 13 | 0 | 0 | Behavioral (byte-identical outputs, formula counts) | OK |
| tests/test_registry_unification.py + test_model_registry.py + test_convert_registry.py | 12+5 | 0 | 0 | Value (counts, key sets, non-emptiness) | OK |
| tests/test_known_defects.py | 1 companion + 5 strict xfail locks | 0 deceptive skips | 0 | Value (contract equality) | OK — the xfails are the designed known-defect locks (AUD-01, comparator bool/int, non-finite get_float), each proven non-vacuous via --runxfail and guarded by unmarked companions |

No disabled tests on requirements; no circular fixtures (fixtures are hand-authored synthetic data); the expected-value provenance for the species contract is the maintainer datasets registry (external oracle), not system output.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| pipeline/dnallmmark_pipeline.py | 1-16 | Deprecation is a module docstring, not a runtime print — the PROBE[REV-10/empty] "running it prints" sub-clause holds only in the pydoc/__doc__/source sense; direct execution ImportErrors on torch/dnallm (which usefully blocks accidental legacy runs) | ℹ️ Info | Cosmetic wording gap in one probe sub-clause; operative acceptance checks all pass |
| pipeline/datasets/ (untracked) | — | 14 extra dev.csv files in non-registry dirs (documented by executor; gitignored, inert — no consumer reads them) | ℹ️ Info | None |

Debt markers: zero TBD/FIXME/XXX in all 20 phase-modified files. No 🛑 blockers, no ⚠️ warnings.

### Human Verification Required

1. **Unverified-prohibition attribution (unverified-prohibition — human review recommended).** Prohibition: "no writes of any kind under /home/forrest/Github/DNALLM." **Test:** Confirm the parallel DNALLM-repo activity (commits `483a35c..d6350b6`, subjects `fix(11)`/`docs(11)`/`docs(12)`, dated 2026-10-09/10) is the maintainer's own parallel suite-stabilization session. **Expected:** Maintainer affirms those commits are theirs — the prohibition then stands fully attributed. **Why human:** our phase's commits provably touch zero DNALLM paths and no env here can even import dnallm, but both repositories share the git identity "Tao Zhang", so authorship of the DNALLM-side commits is not programmatically attributable. Verifier's non-authoritative verdict: **no violation found** (the DNALLM commits carry that project's own phase-11/12 numbering, exactly matching the parallel workstream D-05 documents).

2. **D-04 review verdict spot-check.** **Test:** Human-read `git show 8d99daf` against `.planning/phases/03-dev-reconciliation-revision-blockers/03-FRONTEND-REVIEW.md`. **Expected:** Agreement that the log10/linear toggle introduces no new confirmed frontend defect beyond the 4 recorded observations (all routed to Phase 4). **Why human:** the executor declared human_judgment: true on this static-review verdict. The verifier independently corroborated every mechanical claim (scope exactly js/main.js + index.html + css/charts.css; null-guarded `scaleSwitch`; optional-chaining reads; no innerHTML built in the scatter hunks; listener on static markup that no re-render replaces) and found nothing contradicting CLEAN — corroboration, not substitution.

### Gaps Summary

**No gaps.** All 29 must-have truths across the four plans are VERIFIED against the codebase at HEAD `7c7dfaf` with explicit evidence — not one rests on SUMMARY.md claims alone. The merge held the leaderboard data tree byte-identical to pre-merge; the registries are single-source JSON with the .txt duals retired; the 18 dev splits exist on disk with registry/disk agreement; the two config leaks and the seed-agnostic resume defect are fixed with contract-test pins and the suite-side constructor chain verified read-only; the sweep runner exists with dry-run/fake-executor proof and the fix-loop's 14 findings demonstrably landed (WR-14's empty-flag fail-fast re-proven empirically by this verifier); the deferred PIPE-02/PIPE-03 metadata forms landed exactly per the binding D-05 code-only scope with REQUIREMENTS.md honestly left Pending; and the full gate battery (test/lint/typecheck/lock/env-purity) reproduces green.

Status is **human_needed** solely for the two items above — one descriptor-less prohibition whose compliance is evidenced but whose cross-repo attribution requires the maintainer, and one declared review-verdict judgment. Neither blocks readiness; both are lightweight confirmations at the end-of-phase human checkpoint.

---

_Verified: 2026-10-09T18:45:17Z_
_Verifier: Claude (gsd-verifier)_
