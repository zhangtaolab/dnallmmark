---
phase: 04-correctness-methodology-core
plan: 04
subsystem: pipeline
tags: [quirk-parity, legacy-reference, registry-cards, contract-tests, mutation-testing, model-cards]

# Dependency graph
requires:
  - phase: 03-pipeline-adaptation-registries
    provides: the rewritten pipeline/run_finetune.py with its registry block, VRAM estimators and batch-determination site; the D-10 unified 62-entry models_info.json (name authority)
  - phase: 04-correctness-methodology-core
    provides: 04-01's lint-scope discipline; 04-03's site restoration (no coupling beyond suite health)
provides:
  - All four legacy quirk behaviors ported into run_finetune.py under current registry name forms (ACGT/N charset conditional, models_with_limited_length WIRED, 11-entry safetensors union, length-tier initial batch cap with legacy grad_accum compensation)
  - LEGACY_NAME_MAP parity contract tests (tests/test_run_finetune_contracts.py) that make BOTH divergence and blind-copy drift test failures — mutation-proven non-vacuous (8/8 mutations caught)
  - 62/62 complete 11-key model cards in pipeline/models_info.json (card-absent enumeration retired; zero-absent contract asserted)
  - Per-model upstream source provenance for all 17 fills (table below)
  - A5 resolved by inspection: space and SPACE are the same model under two registry keys — kept distinct (merge surfaced to the maintainer as a blocker, not taken)
affects: [04-02 exporter modelCard join (now total over the registry), E2' quirk-behavior parity, maintainer registry backfill for 7 no-public-page models]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 11428     # 45,713 diff chars / 4 over base c2e014e..HEAD
  tasks: 2
  commits: 2        # MEASURED: git rev-list --count c2e014e..HEAD at SUMMARY time
plan_head_before: c2e014e15602feed13f8a3686c457ae97ea31a68
plan_head_after: 84f56ad758372b62f604dd80b31fc05ea50c5814

# Tech tracking
tech-stack:
  added: []          # no dependencies; the source probes used public HTTP APIs only
  patterns:
    - "Parity modulo a documented name map: LEGACY_NAME_MAP (rename -> new name, drops -> None) compared against the deprecated pipeline read as TEXT — both divergence directions fail"
    - "Statement-anchored source-text contracts (statement_index matches code at a line start, never inside comments) — a commented-out wiring line can never satisfy a contract"
    - "Exec-the-extracted-pure-function for behavioral parity of torch-free functions (determine_batch_size) without importing the torch-pulling module"
    - "Card fills: operational-row-derivable fields + the registry's own absent-value convention \"\" for fields with no traceable upstream — never a fabricated placeholder"

key-files:
  created: []        # no new files; /tmp probe/fill scripts were throwaway
  modified:
    - pipeline/run_finetune.py
    - tests/test_run_finetune_contracts.py
    - pipeline/models_info.json
    - tests/test_registry_unification.py
    - tests/test_model_registry.py

key-decisions:
  - "context_len (bp) on the 7 no-public-page models is \"\" (the registry's missing-value convention), NOT 0: the task_performance schema types it integer, so a fabricated 0 would silently render a wrong number on the public site, while \"\" fails the exporter's schema validation LOUDLY at E2' if one of these models ever gets results — surfacing the gap instead of hiding it"
  - "space's card carries the benchmark's own committed info-block values (space_performance.json == SPACE's card) — the strongest in-repo source for what the benchmark actually ran under that alias"
  - "The tier cap composes as min(bs_new, tier_cap) where the cap is computed from the batch size BEFORE the count-0 VRAM estimator can overwrite it, preserving the legacy 'applied to the configured batch size' semantics"

patterns-established:
  - "Quirk-registry parity tests extract membership from BOTH sources and compare modulo the name map — extend this pattern for any future legacy quirk port"

requirements-completed: [REV-03]

coverage:
  - id: D1
    description: "WR-03 alphabet port: models_no_char_n in current registry name forms (rename applied, 3 drops honored), every member resolving against the unified registry, with the conditional ACGT/N charset at the validate_sequences site"
    verification:
      - kind: unit
        ref: "tests/test_run_finetune_contracts.py#test_models_no_char_n_parity_with_name_map"
        status: pass
      - kind: unit
        ref: "mutation checks M2 (dead name resurrected) and M6 (hardcoded ACGT) both FAIL the test"
        status: pass
    human_judgment: false
  - id: D2
    description: "WR-03 remaining ports: models_with_limited_length wired at the max_length block (AUD-15 dead config made functional, ordering-clamped between the token-len clamp and the estimator) and model_not_use_safetensors as the exact 11-entry union (plant-dnamamba-6mer AND PlantGFM), all members resolving against the registry"
    verification:
      - kind: unit
        ref: "tests/test_run_finetune_contracts.py#test_models_with_limited_length_wired + #test_safetensors_list_is_legacy_union"
        status: pass
      - kind: unit
        ref: "mutation checks M3 (unwired clamp) and M1 (dropped PlantGFM) both FAIL the tests"
        status: pass
    human_judgment: false
  - id: D3
    description: "WR-04 tier rounding: determine_batch_size ports the legacy tier table verbatim (behaviorally proven by exec-ing the extracted pure function from BOTH sources across 15 boundary/floor cases), wired as the initial cap BEFORE the VRAM estimators, composed as min(bs_new, tier_cap), with the legacy grad_accum compensation max(1, batch_size // bs_new) at the adjustment site"
    verification:
      - kind: unit
        ref: "tests/test_run_finetune_contracts.py#test_length_tier_rounding_parity"
        status: pass
      - kind: unit
        ref: "mutation checks M4 (tier drift), M5/M7 (commented-out wiring), M8 (call after estimator) all FAIL the test"
        status: pass
    human_judgment: false
  - id: D4
    description: "Carryover Q2: 62/62 registry entries carry all 11 CARD_KEYS; operational columns and all pre-existing cards byte-identical (verified programmatically: zero operational changes, zero pre-existing card changes); card-absent enumeration retired to a zero-absent contract in both registry suites (count pin 45 -> 62)"
    verification:
      - kind: unit
        ref: "tests/test_registry_unification.py#test_models_registry_single_source + tests/test_model_registry.py#test_every_entry_carries_the_complete_card"
        status: pass
      - kind: integration
        ref: "make test: 206 passed + 0 xfailed (pytest, +4 over the 202 baseline) + node lane 5; make lint + make typecheck clean"
        status: pass
    human_judgment: false
  - id: D5
    description: "Card-value provenance: each of the 17 fills traces to a named upstream source (table below) or to the registry's own operational row + absent-value convention; space/SPACE same-model finding and the 7 no-public-page models surfaced for maintainer backfill"
    verification: []
    human_judgment: true
    rationale: "External card contents (HF/ModelScope pages fetched 2026-10-10) cannot be validated by in-repo automation; the maintainer should spot-check the source table — especially the 7 models whose cards carry \"\" absent-convention values and the space/SPACE duplicate."

# Metrics
duration: 43 min
completed: 2026-10-10
status: complete
---

# Phase 4 Plan 04: Quirk-Parity Ports + 62/62 Card Completeness Summary

**All four legacy model quirks ported into run_finetune.py under current registry names with mutation-proven parity contracts (LEGACY_NAME_MAP makes blind-copy drift a test failure), and the unified registry reaches 62/62 complete 11-key cards with per-model upstream provenance**

## Performance

- **Duration:** 43 min
- **Started:** 2026-10-10T02:28:12Z
- **Completed:** 2026-10-10T03:11:08Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- **Four quirk-parity ports (carryover Q1, WR-03/WR-04):** (1) `models_no_char_n` ported in current registry name forms with the conditional charset at `validate_sequences` (members `"ACGTacgt|"`, all others `"ACGTNacgtn|"` — the exact legacy :1055 strings); (2) `models_with_limited_length` `{prokbert-mini: 1027, plant-dnabert-6mer: 512}` WIRED at the max_length block — the legacy dict was defined but never applied (AUD-15 dead config, now functional, ordering-clamped between the `max_token_len` clamp and the batch sizing); (3) `model_not_use_safetensors` extended to the 11-entry union (`plant-dnamamba-6mer` from legacy + `PlantGFM` from the rewrite); (4) the legacy `determine_batch_size` tier table (`<=512` full, then `//2 //4 //8 //16 //32` at 1024/2048/4096/8192/16384, else 1, each `max(1, ...)`-floored) ported as the initial batch cap computed BEFORE the VRAM estimators, composed as `bs_new = min(bs_new, tier_batch_cap)` (the estimator only ever reduces below the cap), with the legacy grad_accum compensation `max(1, batch_size // bs_new)` at the existing adjustment site (multiplying the D-07-reset YAML default, exactly the legacy `original_grad_accum * scaling_factor`).
- **Name-drift trap handled:** `LEGACY_NAME_MAP` documents the rename (`PlantCAD2-Large-l48-d1536 -> PlantCAD2-Large`) and the three drops (`prokbert-mini-c`, `prokbert-mini-long`, `MutBERT`); the parity tests compare active vs legacy membership MODULO the map, so both divergence (a live quirk lost) and blind-copy drift (a dead name resurrected) fail the suite.
- **Mutation-proven non-vacuous tests:** 8 targeted mutations (drop PlantGFM, resurrect MutBERT, unwire the clamp, tier `//4->//5`, comment-out the composition, comment-out the compensation, hardcode ACGT for all, tier call after the estimator) were applied and each FAILS its test. The M5 mutation exposed a real trap — the composition assertion originally matched the string inside a comment — fixed by anchoring every wiring assertion to real statement starts (`statement_index`: line-start matches only).
- **17 card fills (carryover Q2):** 10 cards from confirmed public pages (cards + configs + measured parameter counts via the HF safetensors/weight-file sizes); `space` from the benchmark's own committed info block; 7 models with no locatable public page carry only the fields derivable from the registry's own operational row, with every other field set to the registry's absent-value convention `""` — never a fabricated value. Operational columns and all 45 pre-existing cards verified byte-identical (zero changes).
- **Contract updates:** `test_registry_unification` now asserts ZERO entries lack any CARD_KEYS member (the TXT_ONLY_MODELS enumeration is retired); `test_model_registry`'s count pin moved 45 -> 62.

## Per-model card source table (all pages read 2026-10-10)

| Model | Source (URL) | Fields sourced | size (M) basis |
|---|---|---|---|
| FungiHelixSeek | huggingface.co/zhangtaolab/FungiHelixSeek + modelscope.cn/models/zhangtaolab/FungiHelixSeek | README property table (263M, MoE hybrid, 8,192 bp, MLM, fungi), config (max_pos 8192, vocab 11) | 263,481,008 (safetensors) |
| GENA-LM-yeast | huggingface.co/AIRI-Institute/gena-lm-bert-base-yeast + modelscope.cn/models/lgq12697/gena-lm-bert-base-yeast | README (MLM, S. cerevisiae, bert-base 512-tok), config (bert, max_pos 512) | 541,130,889 B / 4 = 135.3M (== operational "135M") |
| PlantCAD2-Large | huggingface.co/kuleshov-group/PlantCAD2-Large-l48-d1536 + modelscope.cn/models/lgq12697/PlantCAD2-Large-l48-d1536 | config (caduceus, d1536/l48); family fields from the registry's own Small/Medium cards (PlantCAD series, 8192, plants, MLM) | 5,547,707,406 B / 4 = 1386.9M |
| PlantCaduceus_l24 | huggingface.co/kuleshov-group/PlantCaduceus_l24 + modelscope.cn/models/lgq12697/PlantCaduceus_l24 | HF tags (caduceus), config (d512/l24); family fields from the registry's own PlantCaduceus_l32 card (PlantCAD series, 512, plants, MLM) | 174,648,570 B / 4 = 43.7M |
| PlantGFM | huggingface.co/hu-lab/PlantGFM | README (Hyena, 220M stated, 64K bp, 12 model plants, single-nucleotide, CausalLM) | 220 (card-stated; op "220M") |
| Shorkie_LM | huggingface.co/ZiyanZhuang/shorkie-lm-165-method-rebuild-v1.1 | README (16,384 bp input, 13,651,812 trainable, masked-base = MLM, 165 fungal genomes) | 13,665,828 (safetensors) |
| SpeciesLM-fungi-downstream-k1 | huggingface.co/johahi/specieslm-fungi-downstream-k1 | config (bert, 768x12, max_pos 512, BertForMaskedLM; k=1 = single-nucleotide) | 87,126,144 (safetensors; == op "87.1M") |
| SpeciesLM-fungi-upstream-k1 | huggingface.co/johahi/specieslm-fungi-upstream-k1 | config (bert, max_pos 1024) | 87,519,872 (== op "87.5M") |
| plant-dnamamba-singlebase | huggingface.co/zhangtaolab/plant-dnamamba-singlebase + modelscope.cn/models/zhangtaolab/plant-dnamamba-singlebase | README (Mamba-130m-based, CausalLM, trained at 512 tokens), config (mamba, vocab 11); series/species from the PDLLMs family cards | 90,528,768 (safetensors; op "90M") |
| space | committed dnallm-mark/data/model_performance/space_performance.json info block (== SPACE card), corroborated by huggingface.co/yangyz1230/space (ICML 2025) + modelscope.cn/models/lgq12697/space | all 11 fields verbatim from the benchmark's own committed data | 589 (committed card) |
| Chaoba / Chaoba_all_species / Chaoba_denseMamba | NO public page found (HF search, ModelScope Name-search + org enumerations, web search; only lead: Lin Chaoba, Nanjing Agricultural University — ORCID 0000-0002-9157-9956) | name/size/tokenizer/mean_token_len from the registry operational row; all other fields `""` | 400 / 700 / 400 (operational) |
| denseSSM_plant_genome | NO public page found (same search battery) | operational row; others `""` | 282 (operational) |
| mamba2_370M / mamba2_plant_genome | NO public page found (same search battery; the cartesia/state-spaces mamba2-370m is a natural-language model, not these) | operational row; others `""` | 370 / 370 (operational) |
| prokbert | AMBIGUOUS: neuralbioinfo/prokbert-mini is 20,642,181 params (20.6M) on an overlapped 6-mer — matching this entry's operational row (20M/6mer/mean 6) — but the existing prokbert-mini card already links that repo while ITS operational row (25M) matches prokbert-mini-c (24,975,380, character-level) | operational row; others `""`; ambiguity flagged below | 20 (operational) |

## Task Commits

Each task was committed atomically:

1. **Task 1: Four quirk-parity ports + parity contract tests with the rename map** — `fce5702` (feat)
2. **Task 2: 17 card fills -> 62/62 complete cards + zero-absent contract** — `84f56ad` (feat)

**Plan metadata:** (docs commit follows this SUMMARY)

## Files Created/Modified

- `pipeline/run_finetune.py` — `determine_batch_size` tier function; `models_no_char_n` + `models_with_limited_length` registries; safetensors union (11); the max_length clamp; the tier-cap call + min() composition; the grad_accum compensation; the conditional ACGT/N charset
- `tests/test_run_finetune_contracts.py` — module-level helpers (`list_members`, `composed_members`, `dict_members`, `apply_legacy_name_map`, `registry_keys`, `statement_index`), `LEGACY_NAME_MAP`, 4 new parity tests, docstring extended
- `pipeline/models_info.json` — 17 entries gain complete 11-key cards (byte-stable sort_keys/indent-4 round-trip)
- `tests/test_registry_unification.py` — TXT_ONLY_MODELS enumeration retired; zero-absent 62/62 assertion
- `tests/test_model_registry.py` — count pin 45 -> 62 (test renamed `test_every_entry_carries_the_complete_card`)

## Decisions Made

- `context_len (bp)` on the 7 no-public-page models is `""`, not `0` — the schema types it integer, so a `0` would render as a plausible-but-wrong number on the public site while `""` fails the 04-02 exporter's schema validation loudly if one of these models ever produces results (the repo's "missing = empty string, never 0" convention).
- The tier cap is computed from the batch size BEFORE the count-0 VRAM estimator can overwrite it, preserving the legacy "applied to the configured batch size" semantics; the min() composition then guarantees the estimator never raises past the cap.
- `space`'s card carries the benchmark's own committed info-block values verbatim — the strongest in-repo source for what actually ran under that alias.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Plan-fact mismatch] test_model_registry.py's 45-count pin had to flip with the fill**
- **Found during:** Task 2 (verify step)
- **Issue:** The plan named only `tests/test_registry_unification.py` for the contract update, but `tests/test_model_registry.py` pins `CARD_BEARING_COUNT = 45` — the plan's own verify command (`pytest tests/test_registry_unification.py tests/test_model_registry.py`) fails without updating it.
- **Fix:** Count pin 45 -> 62 with the test renamed to `test_every_entry_carries_the_complete_card`; docstrings updated; the PlantHelixSeek-specific pins untouched.
- **Files modified:** tests/test_model_registry.py
- **Verification:** both suites green (8 passed); full `make test` 206 passed + node 5.
- **Committed in:** 84f56ad

**2. [Rule 1 - Bug] Parity test's wiring assertion matched commented-out code**
- **Found during:** Task 1 (self-imposed mutation check M5)
- **Issue:** `active.find("bs_new = min(bs_new, tier_batch_cap)")` matched the string inside a comment when the real line was commented out — a vacuous contract.
- **Fix:** `statement_index()` helper anchoring every new wiring assertion to a line start; all 8 mutations re-checked FAIL.
- **Files modified:** tests/test_run_finetune_contracts.py
- **Verification:** mutation suite 8/8 caught; 12 tests green.
- **Committed in:** fce5702

---

**Total deviations:** 2 auto-fixed (1 Rule 3 plan-fact mismatch, 1 Rule 1 vacuous-test bug)
**Impact on plan:** None on scope — both are the plan's own gates applied to facts the plan under-specified.

## Flagged Findings for the Maintainer (surfaced, NOT auto-resolved)

1. **space ≡ SPACE (A5, resolved by inspection):** the committed `space_performance.json` info block is identical to the SPACE card (name "SPACE", 589M, yangyz1230/space, lgq12697/space), and no distinct lowercase-space model exists on HF or ModelScope. The two registry entries are the SAME MODEL under two keys (txt-era row vs json-era card) with different operational rows (`models/space` vs `models/SPACE`, `<500M` vs `589M`). Per the plan's acceptance criteria they REMAIN DISTINCT entries; merging them (62 -> 61) is a registry-invariant change (Rule 4) that belongs to the maintainer — the leaderboard's 42-model data runs under the lowercase alias.
2. **7 models with no locatable public page** (Chaoba, Chaoba_all_species, Chaoba_denseMamba, denseSSM_plant_genome, mamba2_370M, mamba2_plant_genome): their cards carry `""` for series/architecture/context_len/species/type/huggingface/modelscope. The maintainer (who ran these models) can backfill from private provenance; the fields will fail the exporter's schema validation loudly if one of these models is ever exported with results.
3. **prokbert mapping ambiguity:** `neuralbioinfo/prokbert-mini` (20.6M, overlapped 6-mer, 1024-token context) matches this entry's operational row (20M/6mer/mean 6), while the existing `prokbert-mini` card links that same repo even though ITS operational row (25M) matches `prokbert-mini-c` (25.0M, character-level). Which HF repo each registry entry actually ran is a maintainer decision; no link was asserted in the fill.

## Known Stubs

| File | Location | Reason |
|---|---|---|
| pipeline/models_info.json | entries Chaoba / Chaoba_all_species / Chaoba_denseMamba / denseSSM_plant_genome / mamba2_370M / mamba2_plant_genome / prokbert | card fields series, architecture, context_len (bp), species, type, huggingface, modelscope are `""` (no locatable upstream source; T-04-10 forbids fabrication) — keys PRESENT (62/62 contract holds) but values await maintainer backfill |

## Issues Encountered

- The initial mutation check (M5) revealed the commented-code matching trap — resolved via statement anchoring (deviation 2).
- ModelScope's search API required the undocumented `Name` body field (the `Target`/`Criterion` variants return the global trending list); the direct repo-detail API worked for mirror probing.

## User Setup Required

None - no external service configuration required.

## Authentication Gates

None.

## Next Phase Readiness

- 04-02's exporter modelCard join is now total over the 62-entry registry; the `""` card fields on the 7 no-public-page models will surface as schema-validation failures at E2' if those models ever produce results (by design).
- Suite baseline after this plan: 206 passed + 0 xfailed (pytest) + 5 node tests; `make lint` and `make typecheck` clean.
- Quirk runtime behavior is provable only at E2' (no GPU this phase) — the parity tests pin list membership and wiring presence, the designed boundary per the plan's flagged assumption.

## Self-Check: PASSED

- Files verified on disk: pipeline/run_finetune.py, tests/test_run_finetune_contracts.py, pipeline/models_info.json, tests/test_registry_unification.py, tests/test_model_registry.py — all FOUND
- Commits verified as ancestors of HEAD: fce5702, 84f56ad — both FOUND
- All plan acceptance criteria re-run post-commit: PASS (per coverage block + verification battery above)
- Legacy reference pipeline/dnallmmark_pipeline.py byte-identical to base (0 diff chars); /home/forrest/Github/DNALLM untouched (read-only source); zero GPU/install activity

---
*Phase: 04-correctness-methodology-core*
*Completed: 2026-10-10*
