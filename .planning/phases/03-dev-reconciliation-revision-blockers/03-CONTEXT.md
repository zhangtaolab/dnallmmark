---
context: phase
phase: 03-dev-reconciliation-revision-blockers
---

# Phase 3: Dev-Branch Reconciliation & P0 Revision Blockers - Context

**Gathered:** 2026-10-09 (resumed session; directive-adjusted)
**Status:** Ready for planning

<domain>
## Phase Boundary

Reconcile the dev-branch pipeline rewrite (dev@c6b3137, `run_finetune.py`, 44-model metadata) into the audited autorun lineage with Phase 1/2 assets intact, then land the manuscript-revision P0 CODE blockers: F1 dev splits, F2 seed-isolated sweep, F10 old-pipeline retirement. **Per the 2026-10-09 maintainer directive: code revision FIRST, NO MODEL RUNS this phase** — PIPE-02 GPU-env build and PIPE-03 two-model E2E are deferred until the DNALLM suite stabilizes (it is being updated in parallel); PlantHelixSeek's models_info entry still lands (metadata only). E2' (Phase 5) remains gated behind F1/F2 as recorded.

</domain>

<decisions>
## Implementation Decisions

### Reconciliation strategy
- **D-01:** `git merge origin/dev` into autorun with per-path conflict policy: `dnallm-mark/data/**` and `baseline/` resolve to HEAD (our contract-validated deterministic data + data-v1 baseline discipline); `pipeline/**`, `dnallm-mark/js/**`, `dnallm-mark/index.html`, README take the dev side (new pipeline + new frontend); `script/**`/`scripts/**`/`pyproject.toml`/`.gitignore` reviewed file-by-file (our determinism fixes vs dev state). — **Reversibility:** costly — the merge commit is the fork's convergence point; redoing it means rewriting history after planning artifacts reference it.
- **D-02:** Merge acceptance = `make test` green on the merged tree with ZERO changes to Phase 2 assets beyond documented necessity (schema bucket counts 42/47/4/1 and the enum≡data self-checks must hold unchanged; if dev's script-side state conflicts with our determinism fixes, OUR fixes win — they are the tested behavior).

### Species-defect lock migration
- **D-03:** The AUD-01-P0 xfail lock PIVOTS from the pipeline-source AST anchor to an EXPORT-CHAIN CONTRACT assertion: every dataset entry's `species` in a result/performance JSON must equal the dataset's arena category (Animals/Plants/Microbe from datasets_info), never a model organism. Fixture-injectable (no pipeline import, no model run); stays xfail(strict=True) until Phase 4's F3② dataset-side species table lands; the unmarked companion (findable/unique/species-key) is replaced by a companion asserting the contract shape exists in the fixture. The old pipeline anchor test is retired with the deprecation (F10), documented in the same commit.

### Dev frontend diff
- **D-04:** Merge takes dev's `js/main.js` (79-line diff) + `index.html`, THEN a targeted review of exactly that diff runs in-phase (against our Phase 1 frontend-audit file:line baseline for the same file) before Phase 4 frontend work begins — findings route to Phase 4's list.

### No-model-runs directive (2026-10-09)
- **D-05:** PIPE-02 (GPU env build) and PIPE-03 (two-model E2E) are DEFERRED until the DNALLM suite stabilizes. What still lands as code: the `pyproject [gpu]` dependency-group definition (versions per the verified combo torch 2.11.0+cu130 / transformers 5.17.0 / dnallm from local clone — NOT installed), and PlantHelixSeek's models_info entry (metadata from its model card — serves AUD-05 groundwork). Dataset double-nesting normalization defers with the E2E (only needed before runs). — **Reversibility:** reversible.
- **D-06:** E2' (Phase 5 three-seed re-run) stays gated: F1 → F2 → E2'; with model runs deferred, Phase 5's F6/F9/F7 code work may proceed independently of E2' timing.

### Carried from the pre-restructure discussion (still binding when runs resume)
- Dedicated NEW uv venv for the pipeline env (never DNALLM/.venv reuse — its dnallm install is 0.6.0/stale); lock carrier = pyproject `[gpu]` + uv.lock; E2E pair = plant-dnamamba-6mer + PlantHelixSeek × PlantCAD2__cross_species_leaf_on_off_translation.

### Planning-time decisions (2026-10-09, maintainer answers during /gsd-plan-phase 3)
- **D-07:** The newly-found grad_accum cross-dataset leak (`run_finetune.py` L584/L593/L598 — `configs["finetune"].gradient_accumulation_steps` mutated in place and re-read next dataset; same class as old-pipeline P0 AUD-02) is fixed IN Phase 3 F2 scope (2-3 line fix + test), not deferred to Phase 4.
- **D-08:** Lint scope: ALL 16 ruff findings arriving with `run_finetune.py` via the merge are fixed in Phase 3 (full strictness — no baseline carry-over, no suppression backlog).
- **D-09:** PlantHelixSeek models_info entry (11 metadata fields) is sourced from the maintainer-provided model card: https://modelscope.cn/models/zhangtaolab/PlantHelixSeek

### Claude's Discretion
- Merge mechanics (single merge commit vs. path-checkout steps) and conflict resolution order; a merge-conflict inventory table lands in the plan's acceptance evidence.
- run_finetune.py reading pass during reconciliation: no behavioral edits (that is F1/F2's job), but a correctness read of the G1/G2 claims at L516/L584-598 vs actual code is cheap and de-risks F2's fix.
- Datasets double-nesting: normalization command documented (not executed) for the future E2E gate.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` — Phase 3 section (7 success criteria; #6/#7 annotated deferred per D-05) + the F→E mapping + critical path note
- `.planning/REQUIREMENTS.md` — REV-01 (F1), REV-02 (F2), REV-10 (F10), PIPE-02/03 (deferred), REV-03..09 (later phases)
- `.planning/quick/20261009-revision-plan-integration/PLAN.md` — the F1-F10 revision plan summary (the full external doc's digest; G1-G7 gap analysis)

### Reconciliation inputs
- `origin/dev` @ `c6b3137` — `git diff --stat a44d310..origin/dev` is the conflict-surface map (51 shared derived-data files, pipeline/ +892 lines, js/main.js ±79)
- `pipeline/run_finetune.py` (on dev) — the G1 site at L516, grad_accum at L584-598, resume semantics
- `pipeline/models_info.json` (on dev) — 44 models incl. CrossDNA_8.1M/71.6M/519M

### Phase 1/2 assets that must survive
- `AUDIT.md` — findings contract (AUD-01-P0 species; AUD-05 missing PlantHelixSeek entry)
- `schemas/` + `tests/` + `Makefile` + `baseline/` — the contract set (bucket counts, enum self-checks, determinism suite)
- `.planning/phases/02-data-contracts-test-harness/02-LEARNINGS.md` — 26 learnings (fingerprint discipline is a blocking constraint; fix-round convergence pattern)
- `.planning/phases/01-audit-release-foundations/01-CONTEXT.md` — D-05/D-06/D-07/D-08 pinning decisions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 2 test suite (136 passed + 5 xfailed) is the merge-acceptance instrument; `make test` from repo root is the gate
- `tests/test_known_defects.py` — the lock being pivoted (D-03) already carries the unmarked-companion pattern to adapt
- `baseline/compare.py --summary-json` — the per-diff vocabulary for any data-tree reconciliation evidence

### Established Patterns
- Fix-round convergence loop + contrast verification (Phase 2 learnings) applies to F1/F2 code changes
- Deterministic generators: `sorted()` + `sort_keys` discipline — F2's sweep outputs (run_record.json etc.) should follow it from day one
- xfail(strict=True) with finding-ID reasons — F2's G1 fix gets its own pre-fix xfail lock pattern optional (planner decides; G1 is a straight bug fix, not a deferred-behavior lock)

### Integration Points
- F1 writes dev.csv files + updates datasets_info Dev columns — the Phase 2 schema's dataset contract must not break (datasets_info is not schema-validated today; note for planner)
- F2's seed-isolated dirs change the output layout REV-03's exporter will consume — coordinate the run_record schema shape now (Phase 4 consumes it)

</code_context>

<specifics>
## Specific Ideas

- Maintainer's consistent preferences: maximum strictness; fix residuals before accepting; decisive numbered answers; verification delegated to the agent with evidence-first presentation.
- The revision timeline (10-22 freeze) motivates F1/F2/F10 landing fast; code-only scope this phase fits it.

</specifics>

<deferred>
## Deferred Ideas

- PIPE-02 GPU env BUILD + PIPE-03 two-model E2E — until DNALLM suite stabilizes (D-05); models do not run this phase
- Dataset double-nesting normalization — with the E2E gate (command documented, not executed)
- E2' three-seed full re-run — Phase 5, gated on F1/F2 (+ suite stability)
- WR-01(P1) gitleaks token-pinning, IN-01(P1) comparator label — Phases 4/5 as recorded
- Suite-side work (IA³, from_scratch) — lives in the DNALLM repo, not here

</deferred>

---

*Phase: 3-Dev-Branch Reconciliation & P0 Revision Blockers*
*Context gathered: 2026-10-09*
