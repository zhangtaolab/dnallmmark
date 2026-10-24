---
phase: 03-dev-reconciliation-revision-blockers
plan: "03"
subsystem: pipeline
tags: [gpu-group, uv, pytorch-cu130, ty, typecheck, plantHelixSeek, registry-card, D-05, D-09, PIPE-02, PIPE-03]

requires:
  - phase: 03-dev-reconciliation-revision-blockers
    provides: "03-02 unified 62/50 JSON registries (PlantHelixSeek operational four in-place, card absent) + test harness + make lanes"
  - phase: 02-data-contracts-test-harness
    provides: "test harness (conftest sys.path contract, bucket pins 42/47/4/1), uv/pyproject carrier"
provides:
  - pyproject [gpu] group (exact cu130-sourced pins, definition-only per D-05) + [[tool.uv.index]] pytorch-cu130 (explicit, torch-scoped) + synced uv.lock
  - ty 0.0.85 in the dev group with [tool.ty] config + make typecheck (zero-diagnostics gate incl. pipeline/)
  - PlantHelixSeek 11-key card inside the unified registry (45 complete cards of 62) + tests/test_model_registry.py integrity pins
affects: [03-04 (extends contracts tests; ruff census on run_finetune.py unchanged at 16 — untouched here), Phase 4 (17 remaining card fills; card-bearing count now 45), Phase 5 (typecheck joins CI gates), E2E gate when runs resume (uv sync --group gpu + local-clone dnallm)]

actuals:
  tokens: 13130   # 52521 diff chars / 4 over plan_head_before..HEAD; bulk = uv.lock re-resolution churn
  tasks: 2
  commits: 2      # measured: git rev-list --count 05714da..HEAD
plan_head_before: 05714da32e14519045e824b8ae9c141d084c0680
plan_head_after: 4248e54af059fa4ae8b1abe40d426c3e734fe86b

tech-stack:
  added:
    - "ty 0.0.85 (dev group, uv.lock-pinned) — Astral type checker, maintainer directive"
  patterns:
    - "Exact-pinned optional GPU group via [[tool.uv.index]] explicit=true + [tool.uv.sources] marker-gated torch entry — definition-only, never synced (D-05/REL-02)"
    - "replace-imports-with-any for GPU-side imports (incl. empirically-discovered torch_npu) — ty green without lying about types or installing the GPU stack"

key-files:
  created:
    - tests/test_model_registry.py
  modified:
    - pyproject.toml           # [pipeline]->[gpu] + index/sources + ty pin + [tool.ty.*]
    - uv.lock                  # re-resolved same-commit (resolve-only): torch 2.11.0+cu130, transformers 5.17.0, ty 0.0.85
    - Makefile                 # typecheck target + .PHONY + header doc
    - pipeline/models_info.json # PlantHelixSeek card fill (one hunk, 12 insertions)
    - tests/test_registry_unification.py # card-absent 18->17, card-bearing 44->45

key-decisions:
  - "GPU group is definition-only with the comment placed ABOVE `gpu = [` so the plan's literal -A3 pin-grep stays green for future re-runs (in-bracket comment pushed torch==2.11.0 past the window)"
  - "torch_npu.** added to replace-imports-with-any: the research glob list was empirically incomplete — run_finetune.py:44 imports Huawei's NPU adapter inside try/except; same GPU-side-never-installed class as torch/dnallm/transformers"
  - "Complete-card count post-fill is 45, not the plan's 44: 62 total - 17 card-absent = 45; every '44 complete' in the plan was the stale pre-fill count (the plan's own inline verify asserting len(complete)==44 fails after a correct fill)"
  - "PlantHelixSeek entry key set is 16 keys, not the plan's 15: operational four + Model_name (required by the key==Model_name contract the same tests enforce) + 11 card keys"
  - "PIPE-02/PIPE-03 deliberately NOT marked complete in REQUIREMENTS.md: this plan landed their D-05 deferred metadata-only form; the env build and E2E runs remain Pending until the DNALLM suite stabilizes"

patterns-established:
  - "External-metadata ingest with prior cross-check: every card field traces to the D-09 source or the entry's operational four, asserted in test_model_registry (card-vs-prior agreement test)"

requirements-completed: []   # PIPE-02/PIPE-03 remain Pending — deferred form only per D-05 (see Deviations #3)

coverage:
  - id: D1
    description: "pyproject [gpu] group (torch==2.11.0 + transformers==5.17.0 exact, comment per REL-02/D-05/dnallm-absence) replacing [pipeline]; [[tool.uv.index]] pytorch-cu130 explicit=true; [tool.uv.sources] torch marker-gated linux/win32; uv.lock re-resolved in the same commit"
    requirement: PIPE-02
    verification:
      - kind: other
        ref: "grep -A3 '^gpu = \\[' pyproject.toml | grep -c 'torch==2.11.0' -> 1"
        status: pass
      - kind: other
        ref: "grep -cE '^pipeline = \\[' pyproject.toml -> 0 (exactly one GPU group, REL-02)"
        status: pass
      - kind: other
        ref: "uv lock --check -> exit 0 (lock in sync; resolution CPU-safe 1.6s metadata-only)"
        status: pass
      - kind: other
        ref: "uv run --group dev python -c find_spec('torch') is None -> no torch in env (D-05 held mechanically)"
        status: pass
    human_judgment: false
  - id: D2
    description: "ty toolchain wiring: ty>=0.0.85 in dev group, [tool.ty] config (python 3.13, extra-paths script/baseline, replace-imports-with-any incl. torch_npu, src.include script/baseline/tests/scripts/pipeline), Makefile typecheck target + .PHONY + header doc"
    requirement: PIPE-02
    verification:
      - kind: other
        ref: "make typecheck -> 'All checks passed!' zero diagnostics over script/baseline/tests/scripts/pipeline"
        status: pass
      - kind: unit
        ref: "make test -> 163 passed + 5 xfailed + node lane 2 pass at Task-1 commit time (168 passed after Task 2)"
        status: pass
    human_judgment: false
  - id: D3
    description: "PlantHelixSeek 11-key card filled inside the unified 62-entry registry from the D-09 ModelScope card; operational four untouched; every field non-empty, numeric trio numeric; 45 complete cards / 17 card-absent"
    requirement: PIPE-03
    verification:
      - kind: other
        ref: "inline entry check -> 'PlantHelixSeek card complete, 62 total, 45 complete cards' (corrected count; plan asserted 44 — stale pre-fill value)"
        status: pass
      - kind: other
        ref: "git diff pipeline/models_info.json -> exactly one hunk: PlantHelixSeek +11 card keys, sort_keys layout preserved, no re-sort churn"
        status: pass
      - kind: other
        ref: "git status/diff -- dnallm-mark/ -> byte-untouched (no runs; buckets pinned 42/47/4/1 via suite)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Registry integrity tests: NEW tests/test_model_registry.py (62 entries, key==Model_name, exact 16-key PlantHelixSeek shape, non-empty card fields, numeric trio int/float, card-vs-operational-prior agreement, 45 complete cards) + test_registry_unification enumeration 18->17 / card-bearing 44->45"
    requirement: PIPE-03
    verification:
      - kind: unit
        ref: "pytest tests/test_model_registry.py tests/test_registry_unification.py -q -> 8 passed"
        status: pass
      - kind: other
        ref: "make test -> 168 passed + 5 xfailed + node lane 2 pass; make lint green; make typecheck green post-edit"
        status: pass
    human_judgment: false

duration: 10 min
completed: 2026-10-10
status: complete
---

# Phase 03 Plan 03: Deferred PIPE-02/PIPE-03 Metadata + ty Toolchain Summary

**Exact-pinned [gpu] group (cu130-index-sourced, definition-only per D-05) replacing the loose [pipeline] group with a synced uv.lock and a provably torch-free dev env; ty 0.0.85 wired with zero-diagnostics [tool.ty] config and make typecheck; PlantHelixSeek's 11-key card filled from the D-09 ModelScope card inside the unified 62-entry registry (45 complete cards), pinned by new registry-integrity tests**

## Performance

- **Duration:** ~10 min (execution; excludes planning)
- **Started:** 2026-10-09T17:00:47Z
- **Completed:** 2026-10-10 (UTC boundary crossed during execution)
- **Tasks:** 2/2
- **Commits:** 2 (measured `git rev-list --count 05714da..HEAD`)
- **Files:** 6 (1 created, 5 modified)

## Accomplishments

- **Task 1 — `[pipeline]` → `[gpu]` + ty toolchain (`77eb49e`).** The loose-bounds `pipeline` group (torch>=2.0/transformers>=4.0) was replaced by `gpu` with exact pins `torch==2.11.0` + `transformers==5.17.0`, the comment stating GPU-only/never-CI (REL-02), definition-lands-now/BUILD-deferred (D-05), and dnallm's deliberate absence (local dev clone `../DNALLM`, branch `revision`). The `[[tool.uv.index]] pytorch-cu130` block (`explicit = true`, torch-scoped per T-03-07) plus the marker-gated `[tool.uv.sources]` torch entry landed with it. `ty>=0.0.85` joined the dev group; `[tool.ty]` config per RESEARCH Pattern 6 (python 3.13, `extra-paths ["script","baseline"]` mirroring the conftest sys.path contract, replace-imports-with-any for GPU-side imports, `src.include` covering script/baseline/tests/scripts/pipeline). Makefile gained `typecheck` (`$(UV) run --group dev ty check`) + `.PHONY` + header doc. `uv lock` re-resolved in the SAME commit (resolve-only, 1.6s, no install): torch `2.11.0+cu130`, transformers 5.17.0, ty 0.0.85 locked; nvidia/cuda dependency closure locked alongside (never installed). Verified: `uv lock --check` exit 0; `make typecheck` → "All checks passed!" zero diagnostics; dev env provably torch-free (`find_spec('torch') is None`); `make test` 163 passed + 5 xfailed + node 2.
- **Task 2 — PlantHelixSeek card fill + registry tests (`4248e54`).** The D-09 model card was fetched from `modelscope.cn/models/zhangtaolab/PlantHelixSeek` (README via the ModelScope repo API, master revision) and read in full. All 11 card fields were derivable — no halt needed: name/series `PlantHelixSeek`, `size (M)` 470 (card "470M params" == prior `Model_size "470M"`), type `MLM`, tokenizer `singlebase` (== prior), `mean_token_len` 1 (== prior), architecture `HelixSeek (Transformer + KDA + MLA + MoE)` (card Model Details row), `context_len (bp)` 8192 (card "Max context: 8,192 bp"), species `plants`, `huggingface`/`modelscope` `zhangtaolab/PlantHelixSeek` (card usage example / the D-09 page). The fill edited ONLY the existing entry (operational four untouched, 62 total unchanged); the git diff is exactly one hunk of +11 card keys with the sort_keys layout preserved. `tests/test_registry_unification.py` dropped PlantHelixSeek from the card-absent enumeration (18 → 17) and moved the card-bearing pin 44 → 45; NEW `tests/test_model_registry.py` (5 tests) pins parse/62/key==Model_name, the exact 16-key PlantHelixSeek shape, non-empty card fields, int/float numeric trio, card-vs-operational-prior agreement, and the 45-complete-card count. Leaderboard data tree byte-untouched.

## Task Commits

1. **Task 1: [gpu] group + pytorch-cu130 index + ty wiring + make typecheck + uv.lock** — `77eb49e` (feat)
2. **Task 2: PlantHelixSeek 11-key card fill (D-09) + registry integrity tests** — `4248e54` (feat)

**Plan metadata:** this SUMMARY + STATE/ROADMAP commit (see below).

## Files Created/Modified

- `pyproject.toml` — gpu group (comment above declaration), pytorch-cu130 index + torch source, dev-group ty, `[tool.ty.environment|analysis|src]`
- `uv.lock` — locked resolution: torch 2.11.0+cu130 (cu130 index), transformers 5.17.0, ty 0.0.85
- `Makefile` — `typecheck` target, `.PHONY`, header comment
- `pipeline/models_info.json` — PlantHelixSeek +11 card keys (45 complete cards of 62)
- `tests/test_registry_unification.py` — enumeration 18→17, card-bearing 44→45, comments updated
- `tests/test_model_registry.py` — NEW: registry-integrity test module

## Decisions Made

Recorded in frontmatter `key-decisions` (comment placement vs the pin-grep, torch_npu glob addition, 45/16 count corrections, PIPE-02/03 not marked complete).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] torch_npu added to the ty replace-imports-with-any list**
- **Found during:** Task 1 (`make typecheck` first run)
- **Issue:** `pipeline/run_finetune.py:44` imports `torch_npu` (Huawei Ascend NPU adapter, inside `try/except ImportError`) — an unresolved-import diagnostic the research Pattern 6 glob list ("still zero errors" claim) did not cover; `torch.**` matches `torch` + submodules but not the separate top-level `torch_npu`.
- **Fix:** Added `torch_npu.**` to `replace-imports-with-any` (same GPU-side-never-installed class as torch/dnallm/transformers/peft/datasets), with a comment recording the empirical origin.
- **Files modified:** pyproject.toml
- **Verification:** `make typecheck` → "All checks passed!" zero diagnostics
- **Committed in:** 77eb49e

**2. [Rule 1 - Plan arithmetic] Post-fill complete-card count is 45, not the plan's 44**
- **Found during:** Task 2 test reconciliation (before authoring the tests)
- **Issue:** The plan consistently says the fill takes the registry "to 44 complete-card entries" and its inline verify asserts `len(complete)==44` — but 44 is the PRE-fill count (03-02 landed 44 complete + 18 absent of 62). The plan's own "card-absent 18 → 17" change forces 45 (62 − 17); 44 complete + 17 absent sums to 61 ≠ 62. The plan's literal verify fails after a correct fill.
- **Fix:** Fill proceeded (the D-09 card content is unambiguous and is the task's substance); counts landed at 45 complete / 17 absent; `test_registry_unification` card-bearing pin moved 44 → 45; `test_model_registry` asserts 45; the inline verify ran with the corrected `len(complete)==45` and printed the corrected one-liner.
- **Files modified:** tests/test_registry_unification.py, tests/test_model_registry.py
- **Verification:** pytest 8 passed; inline check "62 total, 45 complete cards"
- **Committed in:** 4248e54

**3. [Rule 1 - Plan arithmetic] PlantHelixSeek key set is 16 keys, not the plan's 15**
- **Found during:** Task 2 test authoring
- **Issue:** The plan's test spec says "its key set equals the operational four + the 11-key card set exactly (15 keys, no extra, no missing)" — omitting `Model_name`, which the key==Model_name contract (enforced by the same test and by the run_finetune.py dict read site) requires on every entry. 4 + 11 + 1 = 16 (matches the CrossDNA shape reference).
- **Fix:** The exact-set assertion uses operational four ∪ card ∪ {Model_name} = 16 keys; the test comment records the arithmetic.
- **Files modified:** tests/test_model_registry.py
- **Verification:** `test_planthelixseek_entry_shape_is_exactly_ops_plus_card` passed
- **Committed in:** 4248e54

**4. [Rule 3 - Plan-command probe] gpu-group comment moved above the declaration**
- **Found during:** Task 1 verify (V1 grep returned 0)
- **Issue:** The plan's literal probe `grep -A3 '^gpu = \[' | grep -c 'torch==2.11.0'` only looks 3 lines past the group opener; the research Pattern 5 comment (3 lines, inside the brackets) pushes the pin to line +4, so the probe fails against a correctly-pinned group (off-by-one in the plan's own reference pattern too).
- **Fix:** Moved the comment ABOVE `gpu = [` (wording verbatim from research); the pin now lands at +1 and the plan's literal grep passes for every future re-run.
- **Files modified:** pyproject.toml
- **Verification:** V1 grep → 1
- **Committed in:** 77eb49e

**5. [Rule 2 - Truthfulness] PIPE-02/PIPE-03 not marked complete in REQUIREMENTS.md**
- **Found during:** Task 2 close-out (requirements step)
- **Issue:** The plan frontmatter declares `requirements: [PIPE-02, PIPE-03]` and the mechanical workflow would mark both Complete — but REQUIREMENTS.md defines PIPE-02 as the env "reproducibly buildable... with documented setup commands" and PIPE-03 as the two-model E2E producing valid performance JSON. Both are D-05 DEFERRED; this plan landed only their metadata-only forms. Marking complete would falsely green the ship gate.
- **Fix:** Both stay Pending (roadmap already annotates Phase 3 criteria #6/#7 deferred per D-05); `requirements-completed: []` in this SUMMARY; decision recorded in STATE.
- **Files modified:** none (deliberate no-op of the mark step)
- **Verification:** REQUIREMENTS.md unchecked for PIPE-02/PIPE-03, traceability rows stay Pending
- **Committed in:** (documentation only)

---

**Total deviations:** 5 auto-fixed (1 blocking toolchain glob, 2 plan-arithmetic corrections, 1 plan-command probe alignment, 1 deliberate requirements no-op)
**Impact on plan:** No review surface widened: run_finetune.py untouched (03-04's ruff census baseline of 16 findings unchanged), leaderboard data byte-untouched, no installs beyond the plan's own verification path (ty synced into the dev env by `uv run --group dev` exactly as `make typecheck`/`make test` require; the gpu group never synced — dev env provably torch-free).

## Issues Encountered

None beyond the deviations above (all resolved in-flight).

## Authentication Gates

None — fully offline except the single D-09 card fetch (public ModelScope API, read-only). No model runs, no GPU work, no venv builds for the GPU stack, no installs of the gpu group, no writes under /home/forrest/Github/DNALLM (strictly read-only).

## User Setup Required

None.

## Known Stubs

None — no stub patterns introduced. The `[gpu]` group is definition-only BY DESIGN (D-05 deferred form, documented in the group comment and the plan; rebuilding later requires only `uv sync --group gpu` plus the documented local-clone dnallm install). The PlantHelixSeek card is complete (no empty/placeholder values; test-enforced).

## Next Phase Readiness

- 03-04 (F2/D-07/D-08/D-11) extends `tests/test_run_finetune_contracts.py` and lands its edits on `run_finetune.py`, untouched here — its ruff census baseline (16 findings) and the two contract tests are unchanged.
- The 17 remaining card-absent names stay enumerated in `test_registry_unification.py` for Phase 4 fills (each fill must move the card-bearing pin the same way this plan did: 44→45 here, next fill →46).
- ty is wired and green over pipeline/ — 03-04's run_finetune.py edits must keep `make typecheck` at zero diagnostics, and its ruff fixes will land in a tree where typecheck already gates.
- When runs resume (post suite stabilization): `uv sync --group gpu` + dnallm from the local clone (`../DNALLM`, branch `revision`); torch 2.11.0+cu130 and transformers 5.17.0 are already locked.

## Self-Check: PASSED

tests/test_model_registry.py exists on disk; both task commits (77eb49e, 4248e54) verified as ancestors of HEAD; uv.lock in-sync check and the zero-diagnostics typecheck re-run post-commit.

---
*Phase: 03-dev-reconciliation-revision-blockers*
*Completed: 2026-10-10*
