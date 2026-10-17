---
phase: 06-revision-packaging-extended-lanes
plan: 04
subsystem: packaging
tags: [provenance, dataset-metadata, registry-columns, snapshot, freeze-snapshot, methodology-docs, onboarding, doi-swap, dead-code-removal, maintainer-gate]
requires:
  - "the drift-green post-05-04 tree (make data no-op invariant the provenance chain must join)"
  - "pipeline/datasets_info.json as the D-10 single source (50 entries, unified 03-02)"
  - "script/convert_registry.py round-trip machinery + script/freeze_snapshot.py tested primitive (04-02/04-05)"
  - "phase-6 scripts on disk from 06-02/06-03 (lint-list existence guard ordering)"
provides:
  - "DataAPI without recalculateComparison (dead divergent aggregation removed, dedicated first commit)"
  - "six provenance columns across all 50 datasets_info entries (source, citation, license, preprocessing, download_url, download_url_alternates)"
  - "script/build_provenance.py — deterministic dual provenance.{json,csv} emitter + marker-scoped DATA.md appendix"
  - "schemas/provenance.json + its SCHEMA_FILES bucket (strict 50-row contract)"
  - "make snapshot lane — hermetic freeze (hash from manifest.json generated_from), committed .sha256 / gitignored .tar, sha256sum -c re-verification"
  - "docs/METHODOLOGY.md (four methods + dual views + tie rule + CI semantics + permutation family) and docs/ONBOARDING.md (new-model / new-dataset checklists)"
  - "README literal reproduction section + snapshot/re-freeze procedure + doc links"
  - "script/doi_swap.py — prepared same-commit README + .gitleaks.toml swap (refuses on 404; never executed)"
  - "the recorded maintainer provenance review (Task 4 blocking gate, resolved 2026-10-11)"
affects:
  - "06-05 (last plan; response-letter packaging cites the provenance state, snapshot procedure, and SC-7 prepared swap)"
  - "milestone close / gsd-ship (broken-windows gate lifecycle entry; REL-03/DATA-04/DATA-05/DATA-07/EXT-01/EXT-02/REV-03 marks)"
  - "post-E2' re-freeze (the README-documented make data -> verify drift-clean -> make snapshot -> commit .sha256 procedure)"
tech-stack:
  added: []
  patterns:
    - "marker-scoped generated appendix in a hand-authored doc (BEGIN/END provenance markers; maintainer sections provably byte-identical after regeneration)"
    - "hermetic snapshot lane: frozen commit hash read from the committed manifest.json constant, never live git, so the lane works from tarball exports (Pitfall 5)"
    - "existence-guarded Makefile lint-list extension (a phase-6 script joins the gate only if present on disk)"
    - "prepared-not-executed maintainer tooling with an injectable public-ness check (doi_swap both-or-neither invariant)"
key-files:
  created:
    - script/build_provenance.py
    - script/doi_swap.py
    - schemas/provenance.json
    - tests/test_build_provenance.py
    - tests/test_doi_swap.py
    - tests/js/data-api.test.js
    - docs/METHODOLOGY.md
    - docs/ONBOARDING.md
    - dnallm-mark/data/provenance.json
    - dnallm-mark/data/provenance.csv
    - baseline/snapshots/snapshot-991804613c4874bfa3f32d318340b5d7b4118ffe.sha256
  modified:
    - dnallm-mark/js/data.js
    - dnallm-mark/js/config.js
    - tests/js/main-view-toggle.test.js
    - pipeline/datasets_info.json
    - script/convert_registry.py
    - tests/test_convert_registry.py
    - tests/test_schemas.py
    - script/freeze_snapshot.py
    - Makefile
    - .gitignore
    - README.md
    - DATA.md
decisions:
  - "Unspecified-default state is the publication-safe honest state: every unresolved license/citation/download cell is the literal string Unspecified with the source link in source — never blank (minLength 1 enforced by schema)"
  - "Task 4 gate resolved by maintainer acceptance (verbatim: reviewed 接受现状) — the drafted values stand (15 license / 43 citation verified 2026-10-11); the 35/7/9 Unspecified rows stand as honest unknowns; corrections may come anytime later via provenance.csv + convert_registry --to-json --merge-existing + make data (documented in ONBOARDING/README)"
  - "Snapshot hash is manifest-derived (generated_from), never a live git call in the data path; git rev-parse stays a documented manual override only"
  - "The .sha256 manifest is committed and the .tar gitignored (resolved OQ 2); manifest paths are relative to baseline/snapshots so re-verification is the literal sha256sum -c one-liner"
  - "Lint-list extension is existence-guarded (a cut lane's script must never be referenced by the gate)"
  - "doi_swap is prepared, never executed: the real README tokenized link and .gitleaks.toml allowlist are provably untouched at plan end; the maintainer runs the swap when Zenodo record 19135551 goes public (WR-01 same-commit rule)"
patterns-established:
  - "Generated-doc-section discipline: explicit GENERATED ... BEGIN/END markers + do-not-edit stamp + the maintainer-editable CSV surface as the correction path"
  - "Hermetic-freeze discipline: frozen content keyed by a committed constant, re-verification via the standard sha256sum -c form"
requirements-completed: [REL-03, DATA-04, DATA-05, DATA-07, EXT-01, EXT-02, REV-03]
metrics:
  duration: "~75 min across two sessions (Tasks 1-3 prior session; Task 4 gate resolution + close-out continuation 2026-10-11)"
  completed: "2026-10-11"
estimate_provenance: "plan estimate: 75000 tokens / 4 tasks"
actuals:
  tokens: 65124   # chars/4 over git diff d9aead2..c59f5f8 (260494 chars)
  tasks: 4
  commits: 8       # MEASURED: git rev-list --count d9aead2..c59f5f8
plan_head_before: d9aead2730ecad70b773353f58d871f201115953
plan_head_after: c59f5f84f48bdcfba7728dd62a611d151fc6742d
status: complete
coverage:
  - deliverable: "dead-code removal — recalculateComparison gone in the plan's FIRST dedicated commit, surface proven absent, zero call sites, lessons kept in past tense"
    requirement: DATA-07
    verification:
      - kind: tests
        ref: "tests/js/data-api.test.js#DataAPI default export loads as an object with its cache surface, DataAPI memoizes a fetch: a doubled fetch called twice hits the network once, DataAPI no longer exports recalculateComparison (dead logic removed, DATA-07)"
        status: pass
      - kind: command
        ref: "grep -rn 'recalculateComparison(' dnallm-mark/js/ dnallm-mark/*.html | wc -l == 0; commit-subject verify pinned a9e3dd6 as HEAD at task end"
        status: pass
    human_judgment: false
  - deliverable: "provenance chain — six columns over 50 registry entries, converter round-trip + abort-on-wrong-count, deterministic dual artifact, marker-scoped DATA.md appendix, schema bucket"
    requirement: DATA-04
    verification:
      - kind: tests
        ref: "tests/test_convert_registry.py (16 tests incl. the six-column round-trip + wrong-count aborts); tests/test_build_provenance.py#test_emission_is_deterministic,test_reemission_over_its_own_output_is_a_no_op,test_rows_cover_every_registry_entry_in_sorted_order,test_blank_provenance_cell_aborts,test_missing_provenance_key_aborts,test_unspecified_is_preserved_not_blank,test_marker_section_replaces_only_between_markers,test_append_when_markers_absent,test_unbalanced_marker_aborts,test_emitted_json_validates_against_schema,test_emitted_csv_has_header_and_sorted_rows,test_committed_artifacts_match_emission,test_committed_registry_has_no_blank_provenance_cells; tests/test_schemas.py SCHEMA_FILES provenance bucket"
        status: pass
      - kind: command
        ref: "make data byte-stable no-op (consecutive-run hash equality); provenance-shape check: 50 rows, Unspecified present (35 license / 7 citation / 9 download_url)"
        status: pass
    human_judgment: false
  - deliverable: "downloadable provenance manifest (CSV/JSON) with direct links — ModelScope default, alternates included"
    requirement: DATA-05
    verification:
      - kind: command
        ref: "committed dnallm-mark/data/provenance.{json,csv}; committed-artifact-matches-emission test; DATA.md appendix links both machine-readable forms"
        status: pass
    human_judgment: false
  - deliverable: "results snapshot — hermetic make snapshot lane, committed .sha256 / gitignored .tar, sha256sum -c re-verification from the manifest"
    verification:
      - kind: command
        ref: "make snapshot; cd baseline/snapshots && sha256sum -c snapshot-*.sha256 (exit 0, all files OK); git check-ignore on the .tar; SNAPSHOT_FILES excludes model_performance/"
        status: pass
    human_judgment: false
  - deliverable: "docs trio — METHODOLOGY (four methods + dual views + tie rule + CI semantics + permutation family, each traced to its script), ONBOARDING (dry-run-validatable new-model/new-dataset checklists), README literal reproduction + snapshot/re-freeze procedure"
    requirement: REL-03
    verification:
      - kind: command
        ref: "grep proofs: docs/METHODOLOGY.md + uv sync + make snapshot + sha256sum -c present in README; make lint/typecheck/test green after docs land"
        status: pass
    human_judgment: false
  - deliverable: "maintainer provenance review — the Task 4 blocking-human publication gate, resolved and recorded"
    verification:
      - kind: command
        ref: "commit c59f5f8 (docs(06-04): provenance values post-maintainer-review) carries the verbatim disposition + the reviewed/accepted disclosure-string updates; artifacts byte-identical; full gate battery re-run green"
        status: pass
    human_judgment: true
    rationale: "The gate is by construction a maintainer judgment (CONTEXT Area 2 binding): whether research-drafted provenance values may publish as reviewed. The acceptance is recorded as the maintainer's own selection (reviewed 接受现状); automation can only prove the record landed, not make the editorial call."
  - deliverable: "doi_swap prepared, not executed — refuses on 404, both-files-or-neither, --dry-run; real README/.gitleaks.toml provably untouched"
    verification:
      - kind: tests
        ref: "tests/test_doi_swap.py (11 tests: refusal on 404 + message names DOI, both edits in one run, --force, missing-target writes neither, --dry-run prints/writes nothing + still refuses, real files untouched, real checker not-public for current record, CLI wiring)"
        status: pass
      - kind: command
        ref: "grep -c 'preview=1&token=' README.md >= 1 and porcelain empty on README.md/.gitleaks.toml at plan end"
        status: pass
    human_judgment: false
---

# Phase 06 Plan 04: Packaging (provenance, snapshot, docs, DOI-swap preparation) Summary

**One-liner:** The packaging half of Phase 6 landed as eight commits — the dead `recalculateComparison` removed first in its own provable commit, a registry-driven provenance chain (six columns x 50 datasets -> converter round-trip -> deterministic dual artifact -> marker-scoped DATA.md appendix -> strict schema bucket), a hermetic `make snapshot` lane (manifest-derived hash, committed `.sha256`, `sha256sum -c`-re-verifiable), the METHODOLOGY/ONBOARDING/README-reproduction docs trio, a prepared-but-never-executed `doi_swap.py`, all closed by the maintainer's recorded acceptance of the provenance table.

## What Was Built

### Task 1 — the FIRST dedicated commit: dead-code removal (commit a9e3dd6)

`tests/js/data-api.test.js` written first (node:test, the suite's style): the default export loads, a doubled fetch memoizes to one network hit, and **`recalculateComparison` is absent from the exported object**. Then the full definition (from `dnallm-mark/js/data.js:232`) was deleted, and the two lesson comments (`js/config.js:37`, `tests/js/main-view-toggle.test.js:9`) rewritten in past tense — the lesson stays, the implication of presence goes. Zero `.recalculateComparison(` occurrences survive under `dnallm-mark/` (js or html), proven by grep; the commit-subject verify pinned the removal as HEAD at task end. This landed BEFORE any methodology documentation, per the DATA-07 sequencing truth.

### Task 2 — provenance chain + snapshot wiring + lint-list consolidation (commits 0ac07ef, 65cc195, 7f88746, a03dd61)

- **Columns + round-trip (0ac07ef):** `KIND_PRESETS['datasets']['columns']` extended with `source, citation, license, preprocessing, download_url, download_url_alternates`; ingest aborts on wrong expected-column count (the D-10 family); `tests/test_convert_registry.py` extended first (9 -> 16 tests). Values research-drafted from public sources into a working CSV, ingested `--to-json --merge-existing` into `pipeline/datasets_info.json` (50 entries; unresolved cells the literal `Unspecified`, never blank).
- **Emitter + schema + artifact (65cc195, ONE commit):** `script/build_provenance.py` (audit_n_frequencies conventions; reads the registry ONLY; no clock, no network) emits `dnallm-mark/data/provenance.{json,csv}` and replaces ONLY the content between `GENERATED PROVENANCE BEGIN/END` markers in DATA.md (do-not-edit stamp names the CSV correction path). `schemas/provenance.json` (strict draft-2020-12, `additionalProperties: false`, `minLength: 1` on every cell — no blank can validate; row count pinned 50). `tests/test_build_provenance.py` (13 tests: determinism, re-emission no-op, marker safety over a fixture DATA.md, append-when-absent / abort-when-unbalanced, Unspecified preservation, schema validation, committed-artifact-matches-emission) written BEFORE the emission; SCHEMA_FILES bucket + file-count entry in `tests/test_schemas.py`.
- **Snapshot wiring (7f88746):** `freeze_snapshot.py` docstring notes updated from intentionally-unwired to the Phase-6 wiring + frozen file list; Makefile `snapshot` lane reads the hash from `manifest.json`'s committed `generated_from` (991804613c4874bfa3f32d318340b5d7b4118ffe) — never live git (Pitfall 5; git rev-parse documented as manual override only); `build_provenance` joined the `data` chain; `baseline/snapshots/*.tar` gitignored (OQ 2 resolved: `.sha256` committed); first `make snapshot` run produced the committed `snapshot-991804613c4874bfa3f32d318340b5d7b4118ffe.sha256`.
- **Lint-list consolidation (a03dd61):** the phase-6 scripts joined the Makefile lint list ONLY where present on disk (existence guard) — `build_frontier.py`, `zero_shot_vep.py`, `build_provenance.py` now, `doi_swap.py` joins automatically when it lands in Task 3.

### Task 3 — docs trio + doi_swap preparation (commits b3e8b52, 2d16f13)

- **Docs (b3e8b52):** `docs/METHODOLOGY.md` — the four aggregation methods (rank / MinMax / z-score / robust) with formulas and defaults as implemented, the `rank_score` vs `weighted_score` dual views, the CI-overlap tie rule (closed intervals, connected components, min-rank), the vendored CI semantics (n<3 none, t-interval, seeded bootstrap), and the permutation family disclosure (10,000 shuffles, BH over 861 pairs, seed) — each section naming its implementing script. `docs/ONBOARDING.md` — the EXT-01 new-model and EXT-02 new-dataset checklists, every command CPU/dry-run-validatable. README reproduction section — literal copy-pasteable blocks (`uv sync`, `make data` byte-stable no-op, `make test` both lanes, `bash start-server.sh`), expected outputs per step, the CI-replay fresh-clone proof tied to the badge, the snapshot/re-freeze subsection (`make data` -> verify drift-clean -> `make snapshot` -> commit the new `.sha256`), and links to both docs. Every pre-existing README section (including the load-bearing Zenodo link + its HTML comment) untouched.
- **doi_swap (2d16f13):** `script/doi_swap.py` as a thin REPO_ROOT orchestrator (run_migration_inventory style): `--doi` / `--force` / `--dry-run`; public-ness check via urllib with a short timeout, injectable for tests; edit functions operate on explicit paths so tests run over tmp fixtures; ONE run rewrites the README tokenized link and removes the record-19135551-scoped `.gitleaks.toml` allowlist block — both or neither (tested); refusal messages name the record and the `--force` escape; the docstring records the WR-01 same-commit rule and that the MAINTAINER executes it when record 19135551 is public. `tests/test_doi_swap.py` (11 tests) written first per TDD. The REAL README and `.gitleaks.toml` are untouched — pinned by test AND by the plan-end verify.

### Task 4 — the blocking maintainer review, RESOLVED (commit c59f5f8)

The checkpoint presented the generated provenance table with two options: accept the research-drafted values as-is (reviewed), or review manually first with CSV corrections.

**Gate resolution (verbatim):** Presented: accept the research-drafted provenance table as-is (reviewed) vs. review manually first. **Maintainer selected: "reviewed 接受现状"** — the drafted values stand (15 license / 43 citation verified 2026-10-11); the 35/7/9 Unspecified rows stand as honest unknowns (publication-safe state); corrections may come anytime later via provenance.csv + re-ingest (documented in ONBOARDING/README).

Resolution execution (acceptance path — no corrections): the Unspecified-default state already stood committed from Task 2; the review record is the commit `docs(06-04): provenance values post-maintainer-review` (c59f5f8), carrying the verbatim disposition plus the two disclosure strings that implied a PENDING review, updated to the accepted state:

- `schemas/provenance.json` `$comment`: "and are PENDING THE MAINTAINER REVIEW that gates publication" -> "and were REVIEWED AND ACCEPTED BY THE MAINTAINER on 2026-10-11 (the Task 4 blocking gate resolved - the Unspecified rows stand as accepted honest unknowns)"
- `script/build_provenance.py` appendix template + regenerated DATA.md: "and are **pending the maintainer review that gates publication**" -> "and **reviewed and accepted by the maintainer (2026-10-11)**"

The emitted artifacts `provenance.{json,csv}` are byte-identical across the resolution (the review state lives in the schema $comment and the DATA.md prose, not in the data rows); the snapshot manifest was unaffected (DATA.md and schemas/ are outside the frozen `dnallm-mark/data/` set) and re-verified. Full gate battery re-run after the edit: 400 passed + JS 18, lint clean, typecheck clean, `make data` idempotent, `sha256sum -c` exit 0.

## Commits

| Task | Commit | Subject |
| --- | ------ | ------- |
| 1 | a9e3dd6 | refactor(06-04): remove dead recalculateComparison (DATA-07) |
| 2 | 0ac07ef | feat(06-04): provenance columns + converter round-trip |
| 2 | 65cc195 | feat(06-04): build_provenance emitter + schema + artifact + DATA.md appendix |
| 2 | 7f88746 | feat(06-04): snapshot wiring |
| 2 | a03dd61 | chore(06-04): lint-list consolidation |
| 3 | b3e8b52 | docs(06-04): METHODOLOGY + ONBOARDING + README reproduction |
| 3 | 2d16f13 | feat(06-04): doi_swap preparation |
| 4 | c59f5f8 | docs(06-04): provenance values post-maintainer-review |

**Plan metadata:** the close-out commit (SUMMARY + state) follows this file.

## Deviations from Plan

### Auto-fixed Issues (prior executor, Tasks 1-3)

**1. [Rule 1 - Bug] CSV delimiter sniffing hardened**
- **Found during:** Task 2 (converter round-trip work)
- **Issue:** delimiter sniffing over the full file could mis-detect on data-only content.
- **Fix:** header-line-only delimiter sniff + standard excel quoting.
- **Files modified:** script/convert_registry.py
- **Commit:** 0ac07ef

**2. [Rule 3 - Blocker] snapshot manifest paths relative to baseline/snapshots**
- **Found during:** Task 2 (snapshot wiring)
- **Issue:** the manifest's recorded paths did not resolve for the literal `sha256sum -c` re-verification command documented in README/Makefile.
- **Fix:** manifest paths emitted relative to baseline/snapshots so `cd baseline/snapshots && sha256sum -c snapshot-*.sha256` passes literally.
- **Files modified:** script/freeze_snapshot.py (Makefile lane passes relative paths)
- **Commit:** 7f88746

### Interpretations (no plan contract changed)

**3. [Design] build_provenance appends when markers absent / replaces when present / aborts unbalanced.** The plan specified marker-scoped replacement; the emitter's complete contract (fresh DATA.md without markers gains the appendix; markers present -> scoped replace; one marker alone -> loud abort rather than silent clobber) — tested all three ways. Commit 65cc195.

**4. [Design] schema fixture test relaxes minItems/maxItems.** The generic schema-fixture family would emit fixture rows below the provenance schema's pinned 50; the fixture test relaxes the count bounds for the fixture case while the 50-row pin binds via the SCHEMA_FILES bucket over the committed artifact. Commit 65cc195.

**5. iDNA-ABF citation uses the exact Crossref title — verified, not a deviation.** Recorded for the review trail: the citation string was confirmed against Crossref's exact rendered title rather than the paper's header form.

**Continuation (Task 4):** no new deviations — the acceptance path matched the plan's gate text exactly (review-record commit + disclosure-string consistency + full re-verification).

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocker) + 3 recorded interpretations.
**Impact on plan:** All were correctness/verifiability requirements of the shipped surface (round-trip robustness, the literal re-verification command). No scope creep; no leaderboard number moved.

## Verification Results

Final plan-end state (re-run in the continuation session after the review-record commit):

- `make test`: **pytest 400 passed** (was 368 at 06-03 close; +32: 13 `test_build_provenance`, 11 `test_doi_swap`, 8 converter/schema incl. parametrized expansion) + **node lane 18 passed** (was 15; +3 `data-api.test.js`)
- `make lint`: All checks passed (ruff over tests/ + the fixed-findings list + the existence-guarded phase-6 scripts)
- `make typecheck`: All checks passed (ty, no widened suppressions)
- `make data`: byte-stable no-op (consecutive-run hash equality over DATA.md + provenance pair + comparisons + tasks.json + manifest); drift proxy green with the provenance chain in it
- `make snapshot` + `cd baseline/snapshots && sha256sum -c snapshot-*.sha256`: exit 0, every listed file OK; the `.tar` is gitignored, the `.sha256` committed
- Provenance shape: 50 rows; Unspecified counts re-measured at close-out — license 35, citation 7, download_url 9 (download_url_alternates 38) — matching the gate-resolution record
- `data_version` stays **1.1.0** in manifest.json; **no git tag created**
- The real README still carries `preview=1&token=` (>= 1 occurrence) and `.gitleaks.toml` the allowlist block — the swap is provably NOT executed; porcelain clean on both files
- Task 1 invariants hold at plan end: zero `recalculateComparison(` occurrences under `dnallm-mark/`

## Success-Criteria / must_haves Coverage

| Truth / SC | Evidence |
| --- | --- |
| Dead logic gone (SC-4 second half, DATA-07) | a9e3dd6 (first commit of the plan); `tests/js/data-api.test.js` surface + memoization assertions; grep-zero call sites; lessons kept past-tense |
| 50 provenance rows, six columns, dual artifact, never blank (SC-2, DATA-04, DATA-05) | datasets_info 50x6; round-trip + wrong-count aborts (16 converter tests); `test_rows_cover_every_registry_entry_in_sorted_order`, `test_committed_registry_has_no_blank_provenance_cells`, `test_committed_artifacts_match_emission`; schema `minLength: 1` |
| Maintainer-reviewed before publication (CONTEXT Area 2) | Task 4 blocking gate -> c59f5f8 with the verbatim disposition; schema $comment + DATA.md appendix now disclose reviewed/accepted 2026-10-11; corrections path documented (CSV -> convert_registry -> make data) |
| Snapshot exists and re-verifies (SC-3, REV-03 tail; OQ 2) | `make snapshot` hermetic (manifest-derived hash); committed `snapshot-991804613c4874bfa3f32d318340b5d7b4118ffe.sha256`; `sha256sum -c` exit 0; tar gitignored; model_performance/ excluded |
| Methodology in ONE place + fresh-clone reproduction (SC-1, SC-4 first half, REL-03) | docs/METHODOLOGY.md (four methods + dual views + tie rule + CI semantics + permutation family, script-traced); README literal blocks + expected outputs + CI-replay proof; METHODOLOGY/ONBOARDING links present |
| Onboarding validated end-to-end, no GPU (SC-5, EXT-01, EXT-02) | docs/ONBOARDING.md two checklists, every step dry-run-validatable (registry edit -> round-trip -> quirks -> audit -> run_sweep --dry-run) |
| DOI swap prepared, not executed (SC-7) | script/doi_swap.py + 11 tests (404 refusal, both-or-neither, --dry-run, --force); real files provably untouched; WR-01 recorded in docstring + README |
| No leaderboard number moved | data_version 1.1.0; no tag; drift proxy green; provenance pair byte-identical across the Task 4 resolution |
| SC-6 (revision-window lanes) | NOT this plan — owned by 06-01/02/03/05; 06-05 remains |

## Test Coverage

New/extended tests shipped by this plan: `tests/js/data-api.test.js` (3), `tests/test_build_provenance.py` (13), `tests/test_doi_swap.py` (11), `tests/test_convert_registry.py` (+7 incl. parametrized cases), `tests/test_schemas.py` (provenance bucket added inside the existing 5). Suite totals: **400 pytest + 18 JS**, all green; lint and typecheck clean.

## Known Stubs

None. The 35 license / 7 citation / 9 download_url `Unspecified` cells are not stubs — they are the reviewed, publication-safe honest-unknown state (maintainer-accepted 2026-10-11), with the correction path (provenance.csv -> convert_registry --to-json --merge-existing -> make data) documented in ONBOARDING, README, the DATA.md appendix, and the schema $comment.

## Self-Check: PASSED

All 11 created files exist on disk (verified via `[ -f ]` probes); all 8 commits (a9e3dd6, 0ac07ef, 65cc195, 7f88746, a03dd61, b3e8b52, 2d16f13, c59f5f8) verified as ancestors of HEAD; commits measured at 8 via `git rev-list --count d9aead2..c59f5f8` (matches frontmatter `actuals.commits`); the committed snapshot manifest re-verifies (`sha256sum -c` exit 0) and the tar stays ignored.
