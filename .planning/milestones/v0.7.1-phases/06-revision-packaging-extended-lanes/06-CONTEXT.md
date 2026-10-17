# Phase 6: Revision Packaging & Extended Lanes - Context

**Gathered:** 2026-10-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Packaging, provenance, documentation, and revision-window extension-lane MECHANISMS — everything a reviewer needs to understand, trust, reproduce, and extend the platform, plus the dnallm-1.2.1 adaptation verification that gates the lane plans. All deliverables are code/docs/artifact-machinery only: lane RUNS, E2', data-v2 tag, and the DOI swap execution remain maintainer-gated actions outside this phase's agent scope.

</domain>

<decisions>
## Implementation Decisions

### Extended-Lane Depth (Area 1 — accepted 2026-10-11)
- All five lanes (LoRA, IA³, frozen probes, zero-shot VEP, learning curves) deliver full CODE MECHANISMS + fake-executor/synthetic-fixture tests, each independently cuttable (incomplete lane → response-letter future work with mechanism documented)
- LoRA + IA³ share one peft mechanism — suite-native since dnallm 1.2.1 (trainer.py imports get_peft_model/LoraConfig/IA3Config); IA³'s former "suite-support-gated last" condition is lifted
- Cost-accuracy frontier table: generation MACHINERY now (synthetic-fixture driven, schema'd, tests pin the shape), real numbers land automatically post-E2'
- Zero-shot VEP lane: offline scorer `script/zero_shot_vep.py` (CLM/MLM dual scoring + sanity checks + synthetic-fixture tests) — no GPU-path integration
- Learning curves: `run_sweep` extension (`--curve` schedule + probe checkpoint hooks), provable via --dry-run with fake executors

### Provenance & Snapshot (Area 2 — accepted 2026-10-11)
- Provenance is REGISTRY-DRIVEN: datasets_info.json gains provenance columns (source, citation, license, preprocessing, ModelScope-default download URL + alternates); convert_registry.py extended to round-trip them; abort-on-wrong-count ingest discipline (D-10 continuity — no hand-curated parallel table)
- Unknown license/citation → explicit `Unspecified` + source link row, never blank (same discipline as the 7 missing-GUE rows); the generated provenance table is reviewed by the maintainer before publication
- Snapshot wired NOW: script/freeze_snapshot.py (tested, unwired since Phase 4) runs over the committed data-v1.1.0 tree → tar + SHA-256 manifest + frozen commit hash, supporting SI/Zenodo deposition; a documented re-freeze procedure covers the post-E2' data-v2 snapshot
- Provenance manifest downloads as CSV+JSON dual artifacts (mirrors the n_audit convention)

### Documentation Architecture (Area 3 — accepted 2026-10-11)
- `docs/METHODOLOGY.md` (new docs/ dir): the four aggregation methods + F6 dual views documented in ONE place; README links to it
- README reproduction section: literal copy-pasteable command blocks (install → data → aggregate → serve) with expected outputs per step + a fresh-clone proof in the CI-replay style
- `docs/ONBOARDING.md`: new-model/new-dataset process as a dry-run-validated checklist (registry edit → convert_registry → audit → sweep --dry-run — mechanism validated with no GPU runs)
- Dead logic `recalculateComparison` (dnallm-mark/js/data.js:232) removed in a dedicated early commit BEFORE the methodology doc lands (docs never reference dead code; node tests prove no callers)

### Zenodo DOI & 1.2.1 Adaptation Mechanics (Area 4 — accepted 2026-10-11)
- DOI swap (SC-7): a scripted one-click swap (README link + .gitleaks.toml allowlist rule removed in the SAME commit — WR-01 rule) is prepared and documented; the MAINTAINER executes it when Zenodo record 19135551 goes public (currently 404/not public — verified 2026-10-11). No agent polling/auto-swap
- `seed_result.json` (new suite per-seed file, shape {split, timestamp, metrics}): TOLERANT ADOPTION — the exporter gains a lenient reader that merges it as per-seed evidence when present and is non-fatal when absent; coexists with our run_record.json
- 1.2.1 adaptation verification is the FIRST plan of Phase 6 (quirk-list re-verification vs 1.2.1, peft config-surface mapping for the lane plans, env_smoke version expectations, seed_result.json decision landing); the lane plans depend on it

### Claude's Discretion
Implementation details within these envelopes (exact column names, script structure, doc section order, test placement) — following established repo patterns.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `script/convert_registry.py` — bidirectional JSON↔CSV registry converter (KIND_PRESETS, delimiter sniffing) to extend for provenance columns
- `script/freeze_snapshot.py` — tested but unwired snapshot tool (SHA-256 manifest convention); `script/run_migration_inventory.py --write-manifest` shares the line convention
- `pipeline/run_sweep.py` — injectable fake-executor discipline, `--priority-file`/`--from-failures` collect-all-problems validation (the pattern for `--curve`)
- `script/export_runs.py` — dual-view emitter, registry joins, tolerant-reader precedents (LEGACY_DATASET_METRIC)
- `script/audit_n_frequencies.py` — registry-join enumeration + missing-row disclosure discipline
- Schema bucket registry in `tests/test_schemas.py`; dual CSV+JSON artifact convention (n_audit)
- CHANGELOG + migration-inventory discipline (05-02/05-04) for any data-touching change

### Established Patterns
- Fail-fast collect-all-problems validation (_validate_filters family)
- Deterministic emission: sorted iteration + sort_keys, byte-stable regeneration, drift-gated via make data
- Untrusted-data parse-only discipline for dataset CSVs
- TDD with fake executors / synthetic fixtures; dry-run as the only permitted sweep execution form

### Integration Points
- `pipeline/datasets_info.json` (+ converter) — provenance columns
- `pipeline/run_sweep.py` — `--curve` extension; `pipeline/run_finetune.py` — peft config passthrough (adapter verification first)
- `script/zero_shot_vep.py` (new), `docs/` (new dir: METHODOLOGY.md, ONBOARDING.md)
- `README.md` (reproduction section + DOI), `.gitleaks.toml` (swap script target)
- `dnallm` 1.2.1 read-only references: trainer peft surface, sweep.py SEED_RESULT_FILENAME, metric_registry (verified 0 drift vs our 28-name mapping)

</code_context>

<specifics>
## Specific Ideas

- dnallm 1.2.1 alignment facts (verified read-only 2026-10-11): `aggregate_seeds` byte-identical to our vendored copy (F6 holds); sweep protocol unchanged + additive `seed_result.json`; metric registry 28 canonicals with zero drift; `load_local_data`/`validate_sequences`/`sampling` and the import surface intact; `allow_test_as_eval` preserved; peft native
- Zenodo record 19135551: 404 (not public) as of 2026-10-11 — swap is prepared, not executed
- `recalculateComparison` dead logic confirmed still present at dnallm-mark/js/data.js:232

</specifics>

<deferred>
## Deferred Ideas

- Lane RUNS (LoRA/IA³/probes/VEP-execution/curves-execution) — post-E2', maintainer dual-gate GPU actions
- E2' launch itself (env_smoke on GB10 + explicit go) and the data-v2 tag — maintainer-only
- Reviewer-response report (F1-F10/G1-G7) — milestone close, gitignored, per standing maintainer directive (NOT a phase-6 plan deliverable)
- First real GitHub-runner CI execution + branch protection — maintainer setup (05-USER-SETUP.md)

</deferred>
