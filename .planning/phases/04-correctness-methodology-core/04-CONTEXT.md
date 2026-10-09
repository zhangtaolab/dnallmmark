# Phase 4: Correctness & Methodology Core - Context

**Gathered:** 2026-10-10 (autonomous smart discuss, maintainer accepted all 4 areas)
**Status:** Ready for planning

<domain>
## Phase Boundary

Every confirmed correctness bug is fixed surgically with test evidence — species grouping via dataset-side metadata (the AUD-01-P0 fix vehicle), a unified exporter with an explicit metric-key mapping layer (REV-03/F3①, key-parity tested, IN-03 mirror resolved), and every page works: full render across all pages, submission flow restored, escaping at touched sites. Phase-3 carryovers land: the 4 quirk-parity ports, 17 card fills, IN-01 comparator label, README/lint hygiene.

</domain>

<decisions>
## Implementation Decisions

### Species metadata table (F3②/AUD-01)
- **Q1:** The human-verified species table IS `pipeline/datasets_info.json`'s `Category` column (merged in during Phase 3's D-10 unification; 50 rows Animals/Plants/Microbe). No second source of truth.
- **Q2:** Verification procedure: the maintainer personally reviews all 50 Category rows against a generated review list; the confirmed list is committed as the human-verified evidence.
- **Q3:** The Phase 2 species xfail lock (D-03 pivoted export-chain contract) is UNMARKED in the SAME commit as the fix lands (fix + unmark + aggregation-diff inventory, three-in-one — SC-1 literal). The findability/uniqueness/species-key companion stays.
- **Q4:** "Multiple"-origin datasets (e.g. iDNA_ABF 5mC/6mA cross-species) classify into their majority-species arena per the Phase 3 research recommendation; the review list annotates their multiple origin.

### Unified exporter (REV-03/F3① + IN-03)
- **Q1:** Aggregation = VENDORED copy of dnallm.finetune.sweep's pure numpy/scipy statistics function (source-annotated revision@483a35c) + a parity test pinning behavior to that revision. No direct import (dnallm/__init__ pulls torch — breaks the CPU-only torch-free dev discipline). Revisit when the suite offers a torch-free import path.
- **Q2:** New script `script/export_runs.py`: reads F2-layout run_record.json → applies the explicit metric-key mapping → emits task_performance-compatible shape (Phase 2 schemas unchanged; frontend untouched). `get_task_performance.py`'s input side retires per SC-2.
- **Q3:** The exporter OWNS the single metric-key mapping table; `summarize_comparison.py`'s METRIC_KEY_MAP mirror is DELETED (IN-03 resolved by removal, not by co-existence); key-parity unit tests enumerate suite-registry ↔ export-enum both directions; new keys join the closed enum with the data≡enum self-check updated in the same commit (SC-6).
- **Q4:** freeze_snapshot (tar + SHA256 + frozen commit hash) lands as a tested function this phase; the actual freeze invocation waits for Phase 6 packaging (data still moves at E2').

### Frontend restoration (FIX-01..04)
- **Q1:** renderNavbar fix covers the 5 REAL pages (index/task/finetuning/models/datasets); mockup/test dev artifacts stay out (project convention).
- **Q2:** submit.html is created as the 6th real page: js/submit.js rewired to the current schema, added to CONFIG.NAV_LINKS, client-side validation + PR-instruction generator per the Phase 1 audit description.
- **Q3:** A shared escapeHTML util (js/data.js) applied ONLY at DOM-build sites this phase touches (navbar/submit/task renderers) — bounded to touched code, no global hardening pass.
- **Q4:** "Every page renders, zero console errors" is verified by LIVE Playwright MCP browser passes per page (console capture as evidence) plus UAT records; static checks alone are insufficient.

### Phase-3 carryovers
- **Q1:** WR-03/WR-04 quirk-parity ports land IN FULL (ACGT alphabet option, models_with_limited_length, safetensors membership fix, length-tier rounding) with a parity contract test against the legacy pipeline's registries.
- **Q2:** All 17 card-less models get full 11-key cards this phase (pure metadata, no GPU; same discipline as PlantHelixSeek; card-absent enumeration goes to zero — contract test asserts 62/62 complete cards).
- **Q3:** IN-01 comparator label fix lands inside the SC-1 aggregation-diff inventory tooling (one tool surface, two items).
- **Q4:** README exporter sentence + IN-08 (convert_registry.py joins make lint scope) bundled as one hygiene commit, ruff-zero self-evidenced.

### Claude's Discretion
None — all sixteen grey-area answers were maintainer-accepted recommendations.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `script/convert_registry.py` (bidirectional, tested) — registry tooling base
- F2 artifacts: `run_record.json` contract, seed-isolated layout, `pipeline/run_sweep.py` determinism discipline
- Phase 2 schema suite (4 schemas + closed enum self-checks) — exporter output must validate
- `tests/test_registry_unification.py` — card-absent enumeration to drive Q2 carryover
- Playwright MCP (live DOM verification) + `baseline/compare.py --summary-json` diff vocabulary

### Established Patterns
- Vendor-with-provenance + parity test (Q1 exporter) mirrors the convert_registry/D-10 discipline
- Same-commit fix+unmark+diff-inventory matches the Phase 1 52-pair gate pattern
- Aggregation diff = pre-documented inventory, zero out-of-inventory changes (Phase 1/3 precedent)

### Integration Points
- Exporter output → `dnallm-mark/data/task_performance/` (schema-validated) → summarize_comparison → frontend
- NAV_LINKS + page-controller pattern for submit.html; DataAPI cache for the 6-page render verification
- `make lint` scope list; `make typecheck`; CI-less gates stay Makefile-bound

</code_context>

<specifics>
## Specific Ideas

- Maintainer preferences (consistent): maximum strictness, fix residuals before accepting, evidence-first, decisive numbered answers.
- SC-1's aggregation diff must show ONLY changes the species fix explains — same pre-documented-inventory discipline as the data-v1 migration gate.

</specifics>

<deferred>
## Deferred Ideas

- Direct import of the suite's aggregation function — until dnallm offers a torch-free import path (vendor now, revisit later).
- Actual freeze_snapshot invocation — Phase 6 packaging.
- Global innerHTML escaping hardening — bounded to touched sites this phase (full pass is out of scope by design).

</deferred>
