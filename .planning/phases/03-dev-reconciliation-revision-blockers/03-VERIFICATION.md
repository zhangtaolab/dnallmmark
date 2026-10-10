---
phase: 03-dev-reconciliation-revision-blockers
verified: 2026-10-10T07:19:08Z
status: passed
score: 29/29 must-haves verified
covered_files: [".planning/phases/03-dev-reconciliation-revision-blockers/03-01-PLAN.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-01-SUMMARY.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-02-PLAN.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-02-SUMMARY.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-03-PLAN.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-03-SUMMARY.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-04-PLAN.md", ".planning/phases/03-dev-reconciliation-revision-blockers/03-04-SUMMARY.md", "Makefile", "README.md", "pipeline/datasets_info.json", "pipeline/dnallmmark_pipeline.py", "pipeline/models_info.json", "pipeline/run_finetune.py", "pipeline/run_sweep.py", "pyproject.toml", "script/convert_registry.py", "script/make_dev_splits.py", "tests/conftest.py", "tests/fixtures/export_chain/defect_species_performance.json", "tests/test_convert_registry.py", "tests/test_dev_splits.py", "tests/test_known_defects.py", "tests/test_model_registry.py", "tests/test_registry_unification.py", "tests/test_run_finetune_contracts.py", "tests/test_sweep.py", "uv.lock"]
covered_digest: "v3:sha256:277c35e4c0f4c786e4fea542a9c5fa935105d0b6ce10c22455dc4f3a092c4fde"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 29/29
  gaps_closed: []
  gaps_remaining: []
  regressions: []
  mode: stale-refresh (Phase 4 changed 12 files in this phase's covered set; every must-have re-verified against the CURRENT tree at HEAD 015a0cf)
  prior_human_items_resolved: "2/2 via 03-UAT.md (2026-10-10, status: passed) — DNALLM no-writes attribution confirmed by maintainer; D-04 frontend-review verdict human-read confirmed"
deferred:
  - truth: "PIPE-02 full form — GPU env reproducibly BUILT (uv sync --group gpu + dnallm from local clone) and PIPE-03 full form — two-model E2E producing schema-valid performance JSON"
    addressed_in: "Phase 5 (E2E gate, when model runs resume on a stabilized DNALLM suite)"
    evidence: "ROADMAP SC-6/SC-7 '[DEFERRED 2026-10-09]'; binding D-05 CODE-ONLY scope. This phase's owed forms ([gpu] group definition, PlantHelixSeek entry) verified present at HEAD."
  - truth: "7 unlocatable GUE dataset dirs (partial extraction) and dataset double-nesting normalization"
    addressed_in: "Phase 5 E2E gate"
    evidence: "D-05 deferral; re-proven at HEAD: make_dev_splits --check WARNING-excludes them (7 dirs, 'OK: registry/disk agreement for 43 task(s)', exit 0)."
---

# Phase 3: Dev-Branch Reconciliation & P0 Revision Blockers Verification Report

**Phase Goal:** The dev-branch pipeline rewrite (run_finetune.py @ dev c6b3137) is reconciled with the audited main lineage — Phase 1/2 contracts and tests survive the merge — and the manuscript-revision P0 blockers (dev splits, seed-isolated sweep, old-pipeline retirement) land. **Verified against the binding 2026-10-09 D-05 CODE-ONLY scope** (PIPE-02 = [gpu] group definition as code only, no install; PIPE-03 = PlantHelixSeek models_info entry as metadata only, no model runs).
**Verified:** 2026-10-10T07:19:08Z
**Status:** passed
**Re-verification:** Yes — STALE-REFRESH. The prior verification (2026-10-09T18:45:17Z, 29/29) went fingerprint-stale after Phase 4 changed 12 files in this phase's covered set. Every must-have was re-verified against the CURRENT tree at HEAD `015a0cf`; nothing was taken from the prior report or from SUMMARY claims. Phase-4-designed changes are handled by **supersession-by-record** (see the Supersession Ledger) — each is a pre-declared deferral from this phase's own `deferred:` ledger that landed and was independently verified in 04-VERIFICATION.md.

## Goal Achievement

Gate battery reproduced by this verifier at HEAD `015a0cf` on `autorun`: `make test` = **232 passed (pytest lane) + 8 passed (node lane), 0 failed**; `make lint` clean (Phase-4-widened superset scope); `make typecheck` clean; `uv lock --check` exit 0 (88 packages, metadata-only); dev env provably torch-free; `make_dev_splits.py --check` exit 0. The suite count evolved 193 (Phase-3 close) → 232 (Phase 4 added 39 tests) and the 5 xfail locks became unmarked green contracts (Phase 4 D-13 same-commit rule) — expected designed evolution, documented below, not regression.

### Observable Truths

**Plan 03-01 (merge + F10 + D-03 pivot + D-04) — 6 truths**

| # | Truth | Status | Evidence (current tree unless noted) |
|---|-------|--------|----------|
| 1 | SC-1/D-02: dev@c6b3137 merged; data tree held at HEAD bytes; 6 dev-added files absent; bucket pins + enum self-checks hold; suite green | ✓ VERIFIED | Merge commit `41bf49e` (parents `360be65` + `c6b3137`, conflict inventory in message); `c6b3137` ancestor of HEAD; `NO_DEV_DATA_FILES` (ls-files of all 6 paths empty, re-run); bucket pins live at HEAD: model_performance=42, task_performance=47, comparison files=4, tasks.json=1; suite green (232). **Superseded-by-record:** `git diff 360be65 HEAD -- dnallm-mark/data` is no longer empty — it is exactly Phase 4's documented FIX-02 regeneration inventory (models_comparison_animal/microbe.json, GUE__EPI_GM12878 + GUE__fungi_species_20 task files, tasks.json) plus `baseline/compare.py` (Phase-4 WR-02/D-13), all committed post-merge on autorun and verified in 04-VERIFICATION.md. Phase 3 held the tree byte-identical through its close; numbers moved only through the documented fix path, never via a merge — the prohibition's substance holds. |
| 2 | SC-2/D-03: AUD-01-P0 lock pivoted to export-chain contract (fixture-injectable, non-vacuous, unmarked shape companion) | ✓ VERIFIED (Phase-4 supersession: lock now unmarked-green) | Pivot landed at `1b74037`; at Phase-3 close (`7c7dfaf`) the file carried 9 `xfail` occurrences (lock xfail-strict, non-vacuity proven then). Phase 4 fixed the defect the lock pinned (FIX-02, commit `6bb9364`: fixture corrected to `"Plants"` + marker removed in the SAME commit per the D-13 house rule). At HEAD the contract stands as the permanent unmarked green guard `test_aud01_species_matches_dataset_arena_category` (species == Category from unified json) with the unmarked shape companion — both PASSED in the 232; fixture present. The D-03 pivot mechanism is intact; only the marker state evolved, exactly as the lock's own reason string predicted ("the Phase 4 fix"). |
| 3 | SC-2/D-03: old AST anchor lock, companion, `_find_construction_sites` retired in the same commit; pivot documented in module docstring | ✓ VERIFIED | grep of `tests/test_known_defects.py` at HEAD: `_find_construction_sites`, `test_producer_writes_dataset_species_not_model_organism`, `test_aud01_construction_site_anchor` → 0 matches. Module docstring documents the D-03 pivot, the F10 same-commit retirement, AND the Phase-4 unmark history. |
| 4 | SC-3/REV-10/F10: deprecation docstring names run_finetune.py; README usage + structure tree name it as benchmark entry point | ✓ VERIFIED | `pipeline/dnallmmark_pipeline.py` opens with the DEPRECATED module docstring naming `pipeline/run_finetune.py` — banner byte-unchanged by Phase 4 (confirmed: the file is absent from Phase 4's 67-file diff). README carries 4 `run_finetune.py` mentions; usage command, structure tree, and (Phase-4-added) exporter docs all reference the current entry points. |
| 5 | PROBE[REV-10/empty]: deprecated file retained, compiles, deprecation notice surfaced | ✓ VERIFIED | File tracked; `py_compile` → COMPILES. Info note carried forward: the deprecation is a module docstring (surfaced via pydoc/`__doc__`), not a runtime print — direct execution ImportErrors on torch/dnallm, which itself blocks accidental legacy runs. Operative acceptance checks all pass. |
| 6 | PROBE[REV-10/encoding]: datasets_info.txt arrived CRLF byte-identical, then retired | ✓ VERIFIED | Blob-hash probe re-run: `git show 41bf49e:pipeline/datasets_info.txt` == `git show origin/dev:pipeline/datasets_info.txt` (both `9fd645a1…`); both .txt registries absent from tree and index at HEAD. |

**Plan 03-02 (D-10 unification + F1 dev splits + refusal guard) — 7 truths**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 7 | SC-D10a/D-10 single source: models 62 entries (ops four complete, key==Model_name), datasets 50 entries (all operational columns, key==Dataset_name), zero pipeline/*.txt\|*.csv tracked | ✓ VERIFIED | Direct JSON inspection at HEAD: 62/50 entries, ops-four complete on all models, all 10 dataset columns complete, key==name-field everywhere; `git ls-files 'pipeline/*.txt' 'pipeline/*.csv'` empty (NO_TABULAR_REGISTRIES). |
| 8 | SC-D10b/D-10 read site: json.load only, dict iteration, field keys unchanged, pandas import removed, argparse help updated | ✓ VERIFIED | `grep read_table` → 0; no pandas import; `json.load` over `base_dir + datasets_info.json` / `models_info.json` at L347/L351; argparse help strings name the .json registries (L112, L183); compiles (in suite); lint clean. Survived Phase 4's quirk-port edits unchanged in substance. |
| 9 | SC-D10c contract test: registry-unification test green, pins 62/50, card-absent enumeration, key==name | ✓ VERIFIED (Phase-4 supersession: enumeration → zero-absent contract) | `tests/test_registry_unification.py` green in the 232: 62/50 pins, no-tabular-registry assertion, operational completeness, key==name, zero bare gene_exp keys — all hold. The card-absent enumeration was retired by Phase 4 (04-04 carryover Q2) and replaced by the STRONGER zero-absent contract (62/62 complete cards, "must stay EMPTY") — this phase's own deferred-ledger row ("17 remaining card-absent entries → Phase 4", pre-authorized by D-10) landing as designed; docstring records the full history. |
| 10 | D-03/D-10 retarget: `_load_category_map` reads Category from datasets_info.json in the same commit as .txt deletion; lock still non-vacuous | ✓ VERIFIED (Phase-4 supersession: contract now fixed-green) | `_load_category_map()` at HEAD reads Category from `pipeline/datasets_info.json` via json.load (L85-97), keys in Source__task form, join is plain lookup; companion still guards shape/name-resolution (green). The "still fails under --runxfail" clause is superseded: Phase 4's FIX-02 fixed the defect the lock existed to catch, so the contract now passes as an unmarked permanent guard — non-vacuity was proven at Phase-3 close and is preserved in git history (the fixture still carries the formerly-defect entry, now corrected). |
| 11 | SC-4/REV-01/F1: 18 Dev-empty tasks get stratified 10% dev splits (seed=42, reproducible); registry Train/Dev updated; two-layer test-as-eval enforcement | ✓ VERIFIED | Registry at HEAD: 50/50 entries with truthy Dev; 57 dev.csv on disk (18 registry-driven + documented extras); `make_dev_splits.py --check` exits 0 ("OK: registry/disk agreement for 43 task(s)", 7 unlocatable GUE dirs WARNING-excluded per the documented Phase-5 deferral); determinism/stratification/rare-class/count-guard/idempotency pinned by 13 green tests; EVAL-01 suite-side gate re-confirmed at dnallm 483a35c (`allow_test_as_eval` opt-in guard present in trainer.py L568+). |
| 12 | REV-01 part 2: refusal guard (REFUSED SystemExit naming task + EVAL-01 contract + remediation) before model load; config purity | ✓ VERIFIED | Guard at L550 (`REFUSED: dataset '{dataset_name}' has no dev split …` naming the EVAL-01 contract and remediation); `test_dev_refusal_guard_precedes_data_dict` green (precedes `load_model_and_tokenizer(` at the call site and `data_dict = {}`); `allow_test_as_eval` in neither finetune YAML (purity test green). Line numbers shifted by Phase 4's additive edits — the index-precedence contract is what is pinned, and it holds. |
| 13 | PROBE[REV-01/ordering]: dev.csv and rewritten train.csv preserve original row order | ✓ VERIFIED | Order-preservation remains an explicit test target in `tests/test_dev_splits.py` (13 tests green, incl. byte-identical re-carve determinism). |

**Plan 03-03 (deferred PIPE-02/PIPE-03 metadata + ty) — 8 truths**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 14 | SC-6 deferred form/PIPE-02: [gpu] group as code only — exact pins, torch-scoped explicit index, replacing [pipeline], dnallm absent, never installed | ✓ VERIFIED | pyproject at HEAD: `gpu = ["torch==2.11.0", "transformers==5.17.0"]` with the D-05/REL-02/dnallm-absence comment above the declaration; zero `pipeline =` group; `[[tool.uv.index]] pytorch-cu130` with `explicit = true` (torch-scoped, transformers on PyPI); `[tool.uv.sources]` torch marker-gated linux/win32; `default-groups = ["data"]`; `find_spec('torch') is None` in the dev env (re-proven). Unchanged by Phase 4's [data]-group additions. |
| 15 | PROBE[PIPE-02/ordering]: uv.lock in sync, CPU-safe metadata-only resolution | ✓ VERIFIED | `uv lock --check` exits 0 (88 packages resolved in 0.56ms — no download, no build). |
| 16 | PROBE[PIPE-02/empty]: [gpu] definition complete standalone; rebuild recipe documented | ✓ VERIFIED | The group's comment documents the rebuild recipe verbatim (local dev clone `../DNALLM`, branch `revision`); the lock carries the full resolution. |
| 17 | Maintainer ty toolchain directive: ty>=0.0.85 in dev, [tool.ty] config, make typecheck zero diagnostics | ✓ VERIFIED | `ty>=0.0.85` in dev group; `[tool.ty]` at HEAD: python-version 3.13, `extra-paths ["script","baseline","pipeline"]`, replace-imports-with-any (torch/dnallm/transformers/peft/datasets/torch_npu + Phase-4-added `evaluate.**` — additive, documented in-file), `src.include` covering script/baseline/tests/scripts/pipeline; `make typecheck` → "All checks passed!". |
| 18 | SC-7 deferred form/PIPE-03/D-09/D-10: PlantHelixSeek gains complete 11-key card in the unified registry | ✓ VERIFIED (Phase-4 supersession: 45-complete → 62/62) | Entry at HEAD carries exactly 16 keys (ops four + Model_name + 11 card keys), every card field non-empty after str-strip, numeric trio int/int/int (470 / 1 / 8192), prior-agreement test green. The "45 complete cards / 17 card-absent" state is superseded by Phase 4's 62/62 zero-absent registry (pre-declared deferral, landed and verified in 04-VERIFICATION). |
| 19 | PROBE[PIPE-03/adjacency]: exactly 62 entries; leaderboard data tree NOT regenerated in Phase 3 (model_performance bucket stays 42) | ✓ VERIFIED | 62 entries at HEAD; model_performance bucket still 42; the only data-tree drift vs pre-merge is Phase 4's documented regeneration inventory — Phase 3 itself added no data bytes. |
| 20 | PROBE[PIPE-03/empty]: no empty/null/placeholder field in the PlantHelixSeek entry; registry test rejects empties | ✓ VERIFIED | Live check: PlantHelixSeek empty card fields = [] (all 11 non-empty); `test_planthelixseek_card_fields_complete_and_numeric_trio_numeric` green. Note: 7 OTHER entries carry `""` card values under Phase 4's documented absent-value convention (maintainer-backfill item in 04-VERIFICATION) — PlantHelixSeek is not among them; Phase-4 scope, not a Phase-3 gap. |
| 21 | PROBE[PIPE-03/ordering]: fill preserves sort_keys serialization; diff is exactly the PlantHelixSeek entry | ✓ VERIFIED | Historical commit re-checked: `git show 4248e54 --stat -- pipeline/models_info.json` = 12 insertions / 1 deletion (one-entry hunk); registry loads with consistent sort_keys layout at HEAD. |

**Plan 03-04 (F2/G1 + D-07 + D-11 + D-08 + sweep runner) — 8 truths**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 22 | SC-5/REV-02/G1: outdir = {root}/{model}/{task}/seed_{seed}/; resume marker seed-scoped | ✓ VERIFIED | `outdir = f"{save_root}/{model_save_name}/{dataset_name}/seed_{seed}/"` at L659; untouched resume check `os.path.exists(outdir + "trainer_state.json")` at L663 reads the seed-scoped path; `test_seed_isolated_output_layout` green (both substrings + ordering). Survived Phase 4's additive quirk ports. |
| 23 | D-11 cross-MODEL head-config leak fixed: base config reloaded at model-loop top, exactly once, before the custom-head override | ✓ VERIFIED | Exactly ONE `load_config("./finetune_config.yaml")` (count re-verified), inside the model loop, before the `evo2_1b_base`/`megaDNA_updated` override; `test_base_config_reload_is_per_model` green. Static chain re-closed end-to-end at the suite revision: dnallm's `load_config` @ 483a35c (read-only) constructs fresh `TaskConfig`/`TrainingConfig` instances from a fresh `yaml.safe_load` per call — no caching — so residue cannot cross models. |
| 24 | D-07 cross-DATASET grad_accum leak fixed: YAML default snapshotted per model, reset at dataset-loop top before the adjustment read | ✓ VERIFIED | Snapshot `default_grad_accum` at L505 (deliberately AFTER the with_head reload — the WR-01 fix-loop refinement, justification in the test docstring); reset at L517 as the first statement of the dataset-loop body; word-boundary adjustment-read precedence pinned by `test_grad_accum_reset_per_dataset` green. |
| 25 | SC-5/REV-02 sweep runner: run_sweep.py drives model x task x seed; argv-list subprocess cwd=pipeline/; run_record contract; skip on trainer_state; failures manifest; sorted+sort_keys manifest | ✓ VERIFIED | `pipeline/run_sweep.py` at HEAD: `enumerate_matrix` (L197), `build_argv` (L288), `launch_subprocess` (L312), `run_matrix` (L395, injectable executor), `main`; run_record carries status/metrics-verbatim/vram_probe/git_commit/started_at/finished_at/error (schema L27-36 + `_new_record` L356); WR-12 no-overwrite, WR-13 final-metrics-before-marker (run_finetune side, contract test green), WR-11 corrupt-metrics isolation, CR-02 exit-0-no-metrics=failed, WR-14 empty-flag fail-fast (re-proven empirically below) — 19 sweep tests collected, all green. |
| 26 | REV-02 dry-run: enumerates matrix, writes ONLY the manifest — CPU-testable, no subprocess | ✓ VERIFIED | Verifier CLI smoke re-run over the real registries: exit 0, `sweep_manifest.json` created with both seed_42 and seed_43 cells (grep count 2), output root contains ONLY the manifest. |
| 27 | D-08: ruff findings resolved (3 justified BLE001 noqa); make lint widened; zero config suppression; fp32 handling (CR-01) holds | ✓ VERIFIED | `make lint` green at HEAD over the Phase-4-widened superset scope (this phase's four paths all included); `grep tool.ruff pyproject.toml` → 0; exactly 3 noqa lines in run_finetune.py; `test_fp32_only_models_forced_to_full_precision` green (membership parity vs the deprecated reference + fp16/bf16=False before DNATrainer). |
| 28 | PROBE[REV-02/ordering] determinism: sorted iteration + sort_keys serialization → byte-identical manifests | ✓ VERIFIED | `test_dry_run_manifest_is_byte_deterministic` green (19 collected sweep tests include it); manifest holds only matrix+statuses (timestamps/git_commit live in run_record only). |
| 29 | D-06/E2' gating preserved: no model runs of any kind; real mode never invoked | ✓ VERIFIED | No `finetuned/` dir; zero `run_record.json` / `sweep_manifest.json` / `final_metrics.json` anywhere outside test fixtures (find re-run); tests use fake executors + --dry-run only; verifier probes used --dry-run; torch/dnallm absent from every env this repo manages. |

**Score:** 29/29 truths verified (0 present-behavior-unverified; 0 overrides)

The G1/D-07/D-11 leak-fix truths (22-24) remain classified VERIFIED rather than behavior-unverified for the same reason the prior verification recorded: the loop-ordering invariants are pinned by green source-contract tests in our tree, and the one runtime property source tests cannot see (dnallm's `load_config` returning fresh objects per call) was re-verified read-only at the cited suite revision this pass. First live execution remains, by binding directive D-05, deferred to the E2E gate (see Deferred).

### Supersession Ledger (Phase-4-designed changes to this phase's covered set)

Each row is a change Phase 4 made to files this phase's fingerprint covers, pre-authorized by this phase's own deferred ledger / decisions, landed, and independently verified in 04-VERIFICATION.md. None reverts a Phase-3 must-have; each either strengthens the contract or was the declared deferral landing.

| # | Phase-3 contract surface | Phase-4 change | Disposition |
|---|--------------------------|----------------|-------------|
| 1 | AUD-01 lock xfail(strict) + --runxfail non-vacuity (truths 2, 10) | Defect FIXED (FIX-02); marker removed same-commit (D-13); contract now unmarked-green | Superseded-by-record — the lock's designed end state; pivot mechanism + fixture + companion intact |
| 2 | Card-absent enumeration of 17 txt-only models (truths 9, 18) | All 17 cards filled (04-04 carryover Q2); enumeration retired for a zero-absent 62/62 contract | Superseded-by-record — this phase's deferred-ledger row landing; stronger contract, same pins for 62/50/key==name |
| 3 | Data tree byte-identical vs pre-merge (truth 1) | Phase-4 regeneration of exactly 5 documented data files + baseline/compare.py (WR-02/D-13) | Superseded-by-record — movement only through the documented fix path, never via merge; 6 dev-added files still absent; buckets 42/47/4/1 intact |
| 4 | run_finetune.py (truths 8, 12, 22-24, 27) | Additive quirk-parity ports (models_no_char_n ACGT/N charset, limited-length wiring, safetensors 11-union, tier rounding) + LEGACY_NAME_MAP parity tests | Additive-by-design — every Phase-3 site re-verified in place (guard L550, outdir L659, one base reload, snapshot L505/reset L517, 3 noqa, 0 read_table); all contract tests green |
| 5 | Suite 193 passed + 5 xfailed | 232 passed + 0 xfailed | Expected evolution — Phase 4 added 39 tests and unmarked 5 locks per its own one-commit rule |
| 6 | Lint scope = this phase's 4 paths | Phase 4 widened to a superset (adds summarize_comparison, export_runs, freeze_snapshot, convert_registry, compare.py) | Additive — the Phase-3 paths all still inside the gate, still clean |
| 7 | README exporter sentence pending (prior deferred row) | Phase 4 landed "Export Runs to the Leaderboard" (README:216-221) | Deferred item CLOSED by Phase 4 |
| 8 | get_task_performance.py pivot script (not in this phase's covered set; ecosystem context) | Deleted by Phase 4 (IN-03) with coverage folded into test_export_runs.py | Superseded-by-record — outside this phase's truths; noted because the make-data chain changed shape |

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | PIPE-02 full env build + PIPE-03 two-model E2E | Phase 5 / E2E gate | ROADMAP SC-6/SC-7 "[DEFERRED 2026-10-09]"; metadata-only forms verified present at HEAD (this report) |
| 2 | 7 unlocatable GUE dirs + dataset double-nesting flattening | Phase 5 E2E gate | D-05; --check WARNING-exclusion re-proven active at HEAD (7 dirs, 43 agree, exit 0) |

Prior-ledger rows now landed by Phase 4 (no longer deferred): WR-03/WR-04 quirk ports; README exporter sentence; 17 card fills.

### Advisory (New Scope, Unevidenced)

None. Re-verification ran; no new-scope Step-7 findings arose (debt-marker scan over all 20 covered implementation files: clean; anti-pattern scan below).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| Merge commit w/ conflict inventory | 41bf49e on autorun | ✓ VERIFIED | 2 parents `360be65`+`c6b3137`, inventory in message; ancestor of HEAD |
| tests/fixtures/export_chain/defect_species_performance.json | defect-bearing result-JSON fixture | ✓ VERIFIED | Present; species values corrected by Phase 4's same-commit fix; shape companion green |
| 03-FRONTEND-REVIEW.md | D-04 review record | ✓ VERIFIED | Present; verdict CLEAN, 4 observations (UAT-confirmed by human read) |
| convert_registry.py D-10 extensions + tests | --rename-name, --derive-operational, stock pins | ✓ VERIFIED | 12 converter tests green in suite (in lint scope) |
| tests/test_registry_unification.py | single-source contract | ✓ VERIFIED | Green; 62/50 pins hold; enumeration superseded by zero-absent contract |
| Unified models/datasets_info.json; .txt retired | 62/50 single-source JSON | ✓ VERIFIED | Verified directly at HEAD; zero tabular registries tracked |
| run_finetune.py json read site + REFUSED guard | registry load + fail-fast | ✓ VERIFIED | L347/351 json.load; L550 guard before model load; contract tests green |
| script/make_dev_splits.py + tests | split generator + --check | ✓ VERIFIED | 13 tests green; --check exit 0 (43 tasks agree) |
| tests/test_run_finetune_contracts.py | guard + purity + leak contracts | ✓ VERIFIED | Green at HEAD — now 12 tests (5 Phase-3 + fp32/presence/WR-13 fix-loop + 4 Phase-4 quirk-parity) |
| pipeline/run_sweep.py + tests | matrix driver + dry-run + fake-executor proof | ✓ VERIFIED | 19 tests green; CLI dry-run smoke re-proven by this verifier |
| pyproject [gpu] + [tool.ty] + Makefile typecheck/lint | deferred-form code + toolchain | ✓ VERIFIED | All blocks present at HEAD; both gates clean |
| tests/test_model_registry.py | PlantHelixSeek integrity pins | ✓ VERIFIED | Green (16-key shape, non-empty, prior agreement); card-bearing pin updated 45→62 by Phase 4 |
| Deprecated dnallmmark_pipeline.py + README rename | F10 | ✓ VERIFIED | Banner unchanged; COMPILES; README 4 mentions |

All artifacts exist, are substantive, and are wired into the suite/Makefile gates at HEAD.

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| README pipeline usage | pipeline/run_finetune.py | usage command + structure tree + exporter docs | ✓ WIRED | 4 mentions; exporter section (Phase 4) references run_finetune's F2 layout |
| AUD-01 contract lock | fixture + datasets_info Category | `_load_category_map` over unified json | ✓ WIRED | Join live at HEAD; contract green (defect fixed, guard permanent) |
| run_finetune registry reads | unified json registries | json.load at L347/351, .items() loops | ✓ WIRED | Zero read_table; field keys unchanged |
| run_finetune refusal guard | registry Dev value, pre-model-load | L550 before the load call site | ✓ WIRED | Index-precedence test green |
| registry Train counts | num_train_data math | --check registry/disk agreement | ✓ WIRED | 43 tasks agree at HEAD; 7 WARNING-excluded (documented) |
| run_sweep subprocess argv | run_finetune CLI | build_argv list, cwd=pipeline/ | ✓ WIRED | argv-capture test green; never shell |
| run_sweep expected layout | run_finetune outdir construction | seed_{seed}/ convention both sides | ✓ WIRED | Two-sided fake-executor test green |
| run_record metrics | final_metrics.json verbatim | no translation layer | ✓ WIRED | Key-set identity test green; exporter (Phase 4) consumes them with its own mapping layer |
| make lint/typecheck | widened scope incl. pipeline/ | Makefile targets + [tool.ty] | ✓ WIRED | Both exit clean at HEAD (scope now Phase-4 superset) |
| sweep layout | dnallm run_seeds protocol | {out_root}/{model}/{task}/seed_{s}/ | ✓ WIRED | Layout contract matches suite protocol; exporter (Phase 4) is the in-repo consumer |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| models_info.json | 62 entries | converter unification (Phase 3) + 17 card fills (Phase 4) | ✓ | FLOWING (unified, test-pinned 62/62) |
| datasets_info.json | 50 entries | unified registry; Train/Dev from on-disk CSV counts | ✓ | FLOWING (--check agreement 43/43 locatable) |
| dev splits | 57 dev.csv | carve_stratified_dev over real train.csv | ✓ | FLOWING (deterministic seed=42) |
| sweep manifest | planned cells | unified registry keys x truthy-Train datasets | ✓ | FLOWING (CLI smoke over real registries) |
| run_finetune registries | models/datasets dicts | json.load of the unified files | ✓ | FLOWING (module-level read proven) |

No static returns, no hardcoded data, no mocks in any data path.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite (both lanes) | `make test` | 232 passed (pytest) + 8 passed (node), 0 failed | ✓ PASS |
| Lint gate (Phase-4 superset scope) | `make lint` | All checks passed (rc=0) | ✓ PASS |
| Type gate | `make typecheck` | All checks passed (rc=0) | ✓ PASS |
| Contract files by name | `pytest tests/test_run_finetune_contracts.py tests/test_sweep.py tests/test_registry_unification.py tests/test_model_registry.py tests/test_dev_splits.py tests/test_known_defects.py -q` | 62 passed | ✓ PASS |
| Sweep dry-run CLI | `run_sweep.py --dry-run` over real registries | exit 0; manifest w/ 2 seed cells; only manifest written | ✓ PASS |
| WR-14 empty-flag fail-fast | `run_sweep.py --models , --dry-run` | exit 1; flag + raw value in message; no output root | ✓ PASS |
| Registry/disk agreement | `make_dev_splits.py --check` | exit 0; OK 43 tasks; 7 WARNING-excluded | ✓ PASS |
| Lock sync | `uv lock --check` | exit 0 (88 packages) | ✓ PASS |
| D-05 env purity | `find_spec('torch')` in dev env | None | ✓ PASS |
| Bucket pins | file counts under dnallm-mark/data | 42 / 47 / 4 / 1 | ✓ PASS |
| Registries | live JSON inspection | 62/50, ops-complete, key==name, Dev 50/50, 62/62 cards | ✓ PASS |
| EVAL-01 suite contract | `git -C ../DNALLM show 483a35c:dnallm/finetune/trainer.py` | allow_test_as_eval opt-in guard present | ✓ PASS |
| D-11 runtime prerequisite | `git show 483a35c:dnallm/configuration/configs.py` | `load_config` builds fresh dataclass instances per call | ✓ PASS |

### Probe Execution

All PROBE[...] must-have truths were re-executed by this verifier in its own process at HEAD: encoding probe via blob-hash comparison (hashes equal, `9fd645a1…`), merge-inventory probe via `git show 41bf49e`, ordering probes via line-index verification (L347/351, L550, L659/663, L505/517), empty-adjacency probes via direct content checks, WR-14 fail-fast empirically (exit 1, no output root), sweep dry-run empirically (exit 0, manifest-only). No probe claimed in any SUMMARY was taken on trust.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| REV-01 | 03-02 | F1 dev splits + refusal of silent test fallback | ✓ SATISFIED (Complete in REQUIREMENTS.md) | 50/50 Dev truthy; 57 dev.csv; --check green; guard + purity + suite-side EVAL-01 verified at HEAD |
| REV-02 | 03-04 | F2 seed-isolated sweep + per-run records + failure manifest | ✓ SATISFIED (Complete) | seed_{seed}/ layout, resume seed-scoped, runner + records verified at HEAD |
| REV-10 | 03-01 | F10 old-pipeline deprecation + README entry point | ✓ SATISFIED (Complete) | Banner unchanged + compiles + README 4 mentions |
| PIPE-02 | 03-03 | GPU env reproducibly buildable | ✓ DEFERRED-FORM SATISFIED (REQUIREMENTS.md traceability now reads Complete — checkbox evolved post-Phase-4; the full build remains Phase 5 E2E-gate scope per ROADMAP SC-6 deferral annotation) | [gpu] group definition verified present as code (no install) |
| PIPE-03 | 03-03 | Two-model E2E validation | ✓ DEFERRED-FORM SATISFIED (same note as PIPE-02) | PlantHelixSeek entry verified complete at HEAD (62/62 cards); runs remain Phase 5 scope |

Orphaned requirements: NONE — REQUIREMENTS.md maps exactly PIPE-02/03/REV-01/02/10 to Phase 3, all five claimed by plans. Info note: the PIPE-02/PIPE-03 checkboxes (left Pending at Phase-3 close per the 03-03 deviation-5 discipline) were flipped to Complete at some later point (Phase-4-era REQUIREMENTS edit); the ROADMAP still carries the SC-6/SC-7 "[DEFERRED 2026-10-09]" annotations and Phase 5 owns the actual build/E2E — the checkbox state is a post-Phase-3 bookkeeping evolution, not a Phase-3 claim.

### Decision Coverage

Decision-coverage gate re-run: **11/11 CONTEXT.md decisions (D-01..D-11) honored** by shipped artifacts at HEAD (query: check.decision-coverage-verify; skipped: false, blocking: false).

### Test Quality Audit

| Test File | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|--------|---------|----------|-----------------|---------|
| tests/test_sweep.py | 19 | 0 | 0 | Value/Behavioral (exit codes, file contents, byte-determinism, argv/cwd) | OK |
| tests/test_run_finetune_contracts.py | 12 | 0 | 0 | Value (source-index ordering, exact-once counts, exec-based tier-table parity) | OK |
| tests/test_dev_splits.py | 13 | 0 | 0 | Behavioral (byte-identical outputs, formula counts) | OK |
| tests/test_registry_unification.py + test_model_registry.py + test_convert_registry.py | 3+5+12 | 0 | 0 | Value (counts, key sets, non-emptiness) | OK |
| tests/test_known_defects.py | 7 (incl. 3 parametrized) | 0 | 0 | Value (contract equality, KeyError end-to-end) | OK — former xfail locks are now unmarked green contracts (Phase 4 D-13); each lock's non-vacuity was proven at Phase-3 close and the unmark landed same-commit-as-fix per house rule |

No disabled tests on requirements; no circular fixtures (fixtures are hand-authored synthetic data); expected-value provenance for the species contract is the maintainer datasets registry (external oracle).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| pipeline/dnallmmark_pipeline.py | 1-16 | Deprecation is a module docstring, not a runtime print (carried forward from initial verification) | ℹ️ Info | Cosmetic wording gap in one probe sub-clause; operative checks pass; direct execution ImportErrors on torch/dnallm, blocking accidental legacy runs |
| pipeline/models_info.json | 7 entries | `""` card values under Phase 4's documented absent-value convention | ℹ️ Info | Phase-4 scope (04-VERIFICATION human item 3); keys present, 62/62 contract holds; not a Phase-3 concern — PlantHelixSeek (this phase's entry) is fully populated |
| pipeline/datasets/ (untracked) | — | 14 extra dev.csv in non-registry dirs (documented; gitignored, no consumer) | ℹ️ Info | None |

Debt markers (TBD/FIXME/XXX): zero across all 20 covered implementation files (grep re-run this pass). No blockers, no warnings.

### Human Verification

None outstanding. The two items from the prior verification were resolved via UAT (`.planning/phases/03-dev-reconciliation-revision-blockers/03-UAT.md`, 2026-10-10, status: passed, 2/2):
1. DNALLM no-writes attribution — maintainer confirmed the parallel fix(11)/docs(11)/docs(12) commits are their own session; the prohibition stands fully attributed.
2. D-04 frontend-review verdict (commit 8d99daf) — human read confirmed CLEAN, 4 observations.

No new behavior-unverified truths arose this pass (see Score note).

### Gaps Summary

**No gaps.** All 29 must-have truths across the four plans are VERIFIED against the current tree at HEAD `015a0cf` with direct evidence re-derived by this verifier — none rests on SUMMARY claims. Phase 4's changes to this phase's covered set are uniformly additive or pre-declared deferrals landing: the AUD-01 contract graduated from xfail lock to permanent green guard with its defect actually fixed; the registry graduated from 45 to 62/62 complete cards under a stronger zero-absent contract; run_finetune.py gained quirk-parity ports without disturbing a single Phase-3 site (guard, seed-isolated outdir, exactly-one base reload, grad_accum snapshot/reset, 3 sanctioned noqa, json read site — all re-verified in place with contract tests green); the lint/typecheck gates widened to supersets and stay clean; and the data tree moved only through Phase 4's documented regeneration inventory, never via a merge, with bucket pins 42/47/4/1 intact. The full gate battery reproduces green at HEAD, the sweep dry-run and WR-14 fail-fast probes re-passed empirically, D-05/D-06 remain held (no runs, no GPU installs, torch-free env, zero run artifacts), and both prior human items are UAT-closed. The covered fingerprint is refreshed to the current tree.

---

_Verified: 2026-10-10T07:19:08Z_
_Verifier: Claude (gsd-verifier)_
