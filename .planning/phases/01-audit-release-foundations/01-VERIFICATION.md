---
phase: 01-audit-release-foundations
verified: 2026-10-08T15:23:32Z
status: human_needed
score: 23/23 must-haves verified
covered_files: [".gitignore", ".gitleaks.toml", ".planning/phases/01-audit-release-foundations/01-01-PLAN.md", ".planning/phases/01-audit-release-foundations/01-01-SUMMARY.md", ".planning/phases/01-audit-release-foundations/01-02-PLAN.md", ".planning/phases/01-audit-release-foundations/01-02-SUMMARY.md", ".planning/phases/01-audit-release-foundations/01-03-PLAN.md", ".planning/phases/01-audit-release-foundations/01-03-SUMMARY.md", ".python-version", "AUDIT.md", "LICENSE", "README.md", "baseline/PIN-VALIDATION.md", "baseline/compare.py", "baseline/data-v1.sha256", "dnallm-mark/data/models_comparison.json", "dnallm-mark/data/models_comparison_animal.json", "dnallm-mark/data/models_comparison_microbe.json", "dnallm-mark/data/models_comparison_plant.json", "dnallm-mark/data/task_performance/BEND__CpG_methylation_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__C.elegans_4mC_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__D.melanogaster_4mC_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__E.coli_4mC_task_performance.json", "dnallm-mark/data/task_performance/GUE__EPI_GM12878_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K14ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K36me3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K4me1_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K79me3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K9ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H4_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H4ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__fungi_species_20_task_performance.json", "dnallm-mark/data/task_performance/GUE__human_tf_0_task_performance.json", "dnallm-mark/data/task_performance/GUE__mouse_1_task_performance.json", "dnallm-mark/data/task_performance/GUE__mouse_4_task_performance.json", "dnallm-mark/data/task_performance/GUE__prom_300_all_task_performance.json", "dnallm-mark/data/task_performance/GUE__prom_core_all_task_performance.json", "dnallm-mark/data/task_performance/GUE__virus_covid_task_performance.json", "dnallm-mark/data/task_performance/GUE__virus_species_40_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__coding_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__human_vs_worm_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__regulatory_region_type_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K27ac_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K27me3_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K4me2_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K9me3_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__enhancers_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_acceptors_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_all_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_donors_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K27ac_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K27me3_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K4me3_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-core-promoters_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-lncRNAs_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-open-chromatin_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-sequence-conservation_task_performance.json", "dnallm-mark/data/task_performance/PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation_task_performance.json", "dnallm-mark/data/task_performance/PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation_task_performance.json", "dnallm-mark/data/task_performance/iDNA_ABF_datasets__5mC_task_performance.json", "dnallm-mark/data/task_performance/iDNA_ABF_datasets__6mA_task_performance.json", "dnallm-mark/data/task_performance/iPro-WAEL_datasets__Promoter_R_capsulatus_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__poly_a.arabidopsis_thaliana_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__promoter_strength.leaf_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__terminator_strength.leaf_task_performance.json", "dnallm-mark/data/tasks.json", "pyproject.toml", "requirements.txt", "script/get_task_performance.py", "script/summarize_comparison.py", "scripts/generate-tasks-index.js", "uv.lock"]
covered_digest: "v3:sha256:d6ab49b3d0ed7ccd4dce9c883765f29f670b44948bcc7d418ab2fa596f733a49"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Confirm the D-06 root-cause acceptance of the investigated exact-tie pairs (3rd pair: microbe 448.0 agro-nucleotide-transformer-1b/plant-dnamamba2-BPE; 4th pair: plant 116.0 caduceus-ph/space; and the finding that the two pre-documented global pairs at 1232.0 and 749.0 do NOT swap because their committed order is already alphabetical)"
    expected: "A reviewer agrees the six-tie-group census in AUDIT.md's Post-fix migration record and PIN-VALIDATION.md's inventory investigation stand as correct D-06 dispositions (documented, not escalated), making the migration fully attributed"
    why_human: "Correctness judgment over investigated evidence — the verifier independently reproduced every diff class and both file sides of each tie, but accepting a root-cause narrative as complete is judgment the automation cannot make"
  - test: "Confirm the LICENSE copyright holder naming 'Copyright (c) 2026 Tao Zhang and DNALLM-Mark contributors'"
    expected: "Maintainer confirms or edits the holder line before the repo flips public (D-09); surfaced assumption derived from git author + remote org, cheap to change now, contractual after release"
    why_human: "Legal-contract naming decision flagged by the executor for maintainer override; not verifiable programmatically"
  - test: "Sanity-check the severity-grading P0 boundary calls — both pipeline P0s (species-as-dataset, batch config leak) are producer-side risks graded P0 although committed data is currently intact"
    expected: "A reviewer agrees the 'risks corrupting published numbers on regeneration' reading of the P0 rubric applies, steering Phase 4 scope correctly"
    why_human: "Rubric-boundary judgment over reproduced evidence (flagged human_judgment in plan 01-02 SUMMARY)"
  - test: "Confirm the six must-NOT prohibitions discharged (unverified-prohibition — human review recommended): (1) no unreproducible graded findings in AUDIT.md; (2) no secret material quoted in AUDIT.md; (3) no derived-value changes beyond the documented migration inventory; (4) no license claims over upstream datasets; (5) gitleaks allowlist not widened beyond the single record-scoped entry; (6) no secret values in committed evidence"
    expected: "Reviewer confirms the recorded evidence (spot-checked reproductions, grep sweeps, independent migration-gate re-run, .gitleaks.toml inspection) satisfies each must-NOT"
    why_human: "Authored judgment-tier with status unverified/flagged per the plan frontmatter; per the soft-gate contract they are never silently absorbed into a passed verdict even though the verifier found concrete supporting evidence for each"
---

# Phase 1: Audit & Release Foundations Verification Report

**Phase Goal:** The repo is safe for public visibility and every future number change is attributable — all three subsystems audited with evidence, the pre-fix state frozen, and the reproducibility substrate (license, pinned dependencies, deterministic generators) in place
**Verified:** 2026-10-08T15:23:32Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

All must-have truths were verified against the actual codebase with independent behavioral re-execution (not SUMMARY trust). This is an infrastructure/foundation phase; per the infra-phase scoping rule no artificial user-facing UAT items were invented — the human items below are flagged prohibitions, maintainer-judgment calls the executors themselves surfaced, and D-06 acceptance judgments.

### Observable Truths

Merged from the 5 ROADMAP success criteria (contract wording) plus the plan-specific truths that add detail; deduplicated.

**Roadmap success criteria:**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A findings report covers pipeline, data scripts, and frontend, with every finding severity-graded and backed by file:line evidence plus a recommended fix | ✓ VERIFIED | `AUDIT.md` (177 lines): 24 findings AUD-01..AUD-24, all 8-column rows (awk NF check passed), subsystems pipeline(8)/data(5)/frontend(11) all covered, every row carries Location + Reproduction + Recommended fix + D-03 Disposition. Anti-fabrication spot-checks of 8 findings against real code all confirmed (pipeline:1229 species-from-model-row quoted verbatim; submit.html truly absent; README:241-242 plural filenames present; main.js:129-134 comparator ignores currentSort; task-loader has no getTaskList definition; pre-fix tasks.json carried "auprc" per data-v1 tag) |
| 2 | The pre-fix state is recoverable and diffable — a data-v1 git tag and golden baseline outputs exist — before any result-affecting fix lands | ✓ VERIFIED | Annotated tag `data-v1` (git cat-file -t = tag) at commit 788e909; `git archive data-v1` extraction: **52/52 manifest checksums pass** (sha256sum -c exit 0); tagged tree contains zero changes to script/, scripts/, dnallm-mark/data/ vs parent; manifest is inside the tagged tree and byte-identical to the working-tree copy; ordering held (tag precedes the FIX-05 commits 5620988/6a8495a in history) |
| 3 | Running the data-regeneration chain twice from a clean checkout produces byte-identical derived JSON | ✓ VERIFIED (behavioral) | Verifier re-ran the full chain (both Python scripts with the pinned .venv + node indexer) twice: run-2 `sha256sum -c` over all 52 outputs exit 0, and `git status --porcelain dnallm-mark/data/` dirty-count = 0 (regeneration reproduces the committed tree byte-for-byte). Edit sites confirmed: sorted(os.listdir) exactly once in each Python script, sort_keys=True 2x/1x, zero `new Date`/`generatedAt` in the JS generator |
| 4 | A fresh contributor can install the CPU-only data-chain dependencies from version-pinned manifests (pandas>=2.2,<3.0), with GPU pipeline deps isolated in a group CI never installs | ✓ VERIFIED | pyproject: data/dev/pipeline groups with pandas>=2.2,<3.0 + numpy>=2.0,<3, default-groups=["data"], package=false; `uv lock --check` exit 0; uv.lock has exactly one numpy and one pandas block; repo .venv (CPython 3.13.16) contains pandas 2.3.3 + numpy 2.5.3 and **no torch**; requirements.txt uv-exported with exact pins + hashes; `git check-ignore uv.lock .python-version` exit 1 (not ignored), all manifest files git-tracked |
| 5 | The repo is publishable: LICENSE with data licensing declared separately, and the secret-hygiene decision applied — README.md:116 link stays as-is while a full-history scan confirms no OTHER secrets | ✓ VERIFIED (behavioral) | LICENSE = canonical MIT with exactly one 2026 copyright line; README has exactly one License section (MIT / CC BY 4.0 for derived aggregates / upstream-terms disclaimer); LICENSE+README landed in one atomic commit 8a78c4a; `git diff data-v1 -- README.md` has **zero** added/removed zenodo lines (D-08). Verifier re-ran both gitleaks 8.30.1 scans over --all refs: no-allowlist probe → exit 1, exactly 1 finding, README.md:116, RuleID zenodo-preview-token; committed-config production scan → exit 0, zero findings |

**Plan-specific truths (detail beyond the SC wording), all verified:**

| # | Truth (plan) | Status | Evidence |
|---|--------------|--------|----------|
| 6 | Comparator buckets float diffs at rel 1e-12 (abs(a-b)/max(abs(a),abs(b),1e-300)) into FLOAT_ULP vs FLOAT_BIG; exit 0 only when no diffs | ✓ VERIFIED | Code inspected (baseline/compare.py:90-94, 154); behavior observed: identical pair → "VALUES IDENTICAL" exit 0; different pair → exit 1; missing file → readable error exit 2, no traceback |
| 7 | --summary-json emits the complete untruncated inventory (len(diffs) == total == sum(counts)) | ✓ VERIFIED | tasks.json vs models_comparison.json pair: total 45 == len(diffs) 45 == sum(counts) with >8 diffs (untruncated); identical pair: total 0, diffs [], counts {} |
| 8 | Manifest covers exactly the 52 derived files and none of the 42 model_performance inputs | ✓ VERIFIED | 52 lines, all dnallm-mark/data/-prefixed, 0 model_performance entries (42 inputs on disk unlisted) |
| 9 | Fresh uv sync installs only the data group (GPU pipeline never in the default set) | ✓ VERIFIED | default-groups=["data"] enforces it; .venv site-packages: numpy/pandas/dateutil/pytz/six/tzdata only, torch absent |
| 10 | uv.lock holds a single numpy resolution across all groups | ✓ VERIFIED | Exactly one `name = "numpy"` and one `name = "pandas"` block |
| 11 | Empty dev group stays resolvable (uv lock --check exit 0 with dev = []) | ✓ VERIFIED | uv lock --check exit 0; dev = [] in pyproject |
| 12 | Re-running uv lock produces no change (stable deterministic resolution) | ✓ VERIFIED | `uv lock --check` exit 0 (the exact no-change assertion) |
| 13 | Pin validation ran on the pre-fix generators; only the root-caused inventory was observed (backstop) | ✓ VERIFIED (behavioral, independently re-derived) | Verifier re-ran the PRE-FIX generators (from the data-v1 tag) in a scratch mirror with the pinned venv against the full model_performance input and compared to the committed data-v1 files: **exact count match with PIN-VALIDATION.md** — models_comparison 42 (38 ULP + 4 BIG), animal 33 ULP, plant 41 ULP, microbe 42 (40 ULP + 2 BIG), tasks.json 2 VALUE (generatedAt + metric casing), 47/47 task files 0 diffs; ULP confined to sum_zscore, BIG confined to exact-tie ranks |
| 14 | Same-root-cause findings merged into single rows citing every site | ✓ VERIFIED | AUD-10 (4 nesting sites), AUD-12 (4 listener sites), AUD-14 (6 XSS sites) each one row with all file:line sites; method section documents the merge discipline |
| 15 | A zero-findings subsystem would be explicitly reported, never silently omitted | ✓ VERIFIED | Condition vacuous (all three subsystems have findings) but all three are covered — no silent omission; report structure includes per-subsystem counts |
| 16 | Findings table ordered P0→P1→P2, then pipeline→data→frontend, then AUD-nn ID | ✓ VERIFIED | Programmatic order check over all 24 rows: deterministic-order = True, IDs sequential AUD-01..AUD-24 |
| 17 | Maintainability findings in a separate non-graded list (D-04) | ✓ VERIFIED | "## Maintainability findings (non-graded, D-04)" section, 10 entries, zero P0/P1/P2 grades |
| 18 | Report pre-documents the expected post-fix migration inventory | ✓ VERIFIED | "### Expected post-fix migration inventory" section with ULP noise, 3 tie pairs, BEND casing, generatedAt removal + D-06 halt rule |
| 19 | Partial review-agent run detected at merge time (backstop) | ✓ VERIFIED (behavioral) | Verifier re-executed the findings-file gate in both directions: passes on the three real non-empty /tmp/audit-findings-{pipeline,data,frontend}.md (8.5K/5.2K/9.6K, schema-valid 6-field candidates) and fires ("DETECTED") on a synthetic empty file; AUDIT.md's 24 rows trace to those candidates |
| 20 | Exact-tie pairs resolve to a deterministic order pinned by sorted filename iteration | ✓ VERIFIED (behavioral) | Microbe pair rank_score 448.0 exact tie on both file sides (ranks 2/3 swap), plant pair 116.0 exact tie (ranks 36/37 swap) — now alphabetical and stable across the verifier's two runs; the two global pairs (13/14, 29/30) unchanged, matching the documented "already alphabetical, do not swap" census |
| 21 | One-time migration diff vs data-v1 contains only the documented inventory | ✓ VERIFIED (behavioral, independently re-gated) | Verifier re-ran the full migration gate over all 52 pairs (tag tree vs current): **MIGRATION-INVENTORY-OK** — FLOAT_ULP only on /performance/sum_zscore, FLOAT_BIG only on the two investigated tie pairs' /performance/rank, tasks.json limited to generatedAt MISSING_IN_REGEN + metric-casing VALUE (both required present), 47/47 task files 0 diffs, no out-of-inventory classes |
| 22 | Full-history scan clean + no-allowlist probe surfaces exactly the one known finding | ✓ VERIFIED (behavioral) | Both scans re-executed by the verifier (see truth 5); probe config documented as rules-only because gitleaks auto-loads ./.gitleaks.toml |
| 23 | Generators' empty-input behavior unchanged (backstop) | ✓ VERIFIED (behavioral) | Verifier ran PRE-FIX and POST-FIX generators side-by-side on an empty model_performance dir: all scripts exit 0, same file set emitted, models_comparison.json VALUES IDENTICAL, count=0 tasks both sides; the single tasks.json diff is /generatedAt MISSING_IN_REGEN — the intended global FIX-05 stamp removal, not an emptiness-semantics change |

**Score:** 23/23 truths verified (0 present-but-behavior-unverified — every behavioral claim was re-executed by the verifier, including all three backstop truths)

### Prohibition Disposition (ADR-550 D4 — judgment-tier soft gate)

All six prohibitions were authored with `status: unverified, flagged: true` in the PLAN frontmatter. The verifier recorded non-authoritative verdicts with the following evidence; per the soft-gate contract they surface as human-verification items rather than being silently absorbed into a pass:

| Prohibition | Verifier verdict | Evidence |
|-------------|-----------------|----------|
| AUDIT-01: no unreproducible graded findings | PASS (LLJ + spot-checks) | Unverified-observations list exists with exactly 1 ungraded item; 8/24 findings independently re-checked against real code, all real |
| AUDIT-01: no secret material in AUDIT.md | PASS (deterministic) | grep zenodo.org/records = 0, eyJ = 0, token= = 0 in AUDIT.md |
| FIX-05: no value changes beyond inventory | PASS (deterministic) | Independent migration-gate re-run: MIGRATION-INVENTORY-OK (truth 21) |
| REL-01: no license claims over upstream data | PASS (text evidence) | README License section explicitly: upstream "not redistributed... remain under their original terms"; CC BY covers only repo-produced aggregates |
| REL-05: allowlist not widened | PASS (deterministic) | .gitleaks.toml holds exactly one [[rules.allowlists]] entry, condition AND, path README.md + record-19135551 regex; rule-scoped (not global); canary evidence documented in AUDIT.md |
| REL-05: no secret values in committed evidence | PASS (deterministic) | AUDIT.md location-only references; .gitleaks.toml contains regex patterns, not values |

### Required Artifacts

gsd-tools `verify.artifacts`: 7/7 (01-01), 1/1 (01-02), 4/4 (01-03) — all passed.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `baseline/compare.py` | Order-insensitive comparator, exit contract, --summary-json | ✓ VERIFIED | 158 lines; FLOAT_ULP present; behaviorally tested (exit 0/1/2 + contract) |
| `baseline/data-v1.sha256` | 52-entry SHA256 manifest | ✓ VERIFIED | 52 lines, 0 input entries; 52/52 verify against the extracted tag tree |
| `baseline/PIN-VALIDATION.md` | Pin-validation evidence | ✓ VERIFIED | 132 lines: commands, resolved versions, per-file inventory, D-06 conclusion; inventory independently reproduced by the verifier |
| `pyproject.toml` | PEP 621 + PEP 735 groups | ✓ VERIFIED | dependency-groups present; data/dev/pipeline; default-groups=["data"] |
| `uv.lock` | Committed exact-resolution lockfile | ✓ VERIFIED | Tracked; pandas present; single numpy/pandas blocks; uv lock --check exit 0 |
| `requirements.txt` | pip export with exact pins | ✓ VERIFIED | pandas==2.3.3, numpy==2.5.3 + hashes; uv autogenerated header |
| `.python-version` | 3.13 pin | ✓ VERIFIED | Single line "3.13" |
| `AUDIT.md` | Public severity-graded findings report | ✓ VERIFIED | 177 lines (≥120); "Severity definitions" present; 24 graded findings; all sections; placeholder replaced |
| `LICENSE` | MIT text | ✓ VERIFIED | Canonical MIT; one 2026 copyright line |
| `.gitleaks.toml` | Default rules + narrow AND allowlist | ✓ VERIFIED | useDefault=true; "condition" AND; rule-scoped single entry; both scans re-run clean |
| `script/summarize_comparison.py` | sorted + sort_keys | ✓ VERIFIED | sorted(os.listdir) at 309; sort_keys=True at 381, 408 |
| `scripts/generate-tasks-index.js` | No live-clock stamp | ✓ VERIFIED | Zero new Date / generatedAt; tasks.json carries count/tasks/version only |

### Key Link Verification

gsd-tools `verify.key-links` reported 5 links NOT-WIRED — all are non-file or negative links the pattern matcher cannot express (git tag as source, /tmp files, conceptual targets, and a link whose intent is a line's REMOVAL). Each was verified behaviorally by hand:

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| pyproject.toml | uv.lock | floor bounds → exact pins | ✓ WIRED | pandas>=2.2,<3.0 resolves to pandas 2.3.3 in lock; uv lock --check exit 0 |
| uv.lock | requirements.txt | uv export --group data | ✓ WIRED | Autogenerated header names the exact export command; pins match lock |
| .gitignore | uv.lock | ignore line removed (Pitfall 1) | ✓ WIRED | Tool marked "pattern not found" — correct: the line is gone; git check-ignore exit 1, uv.lock tracked |
| git tag data-v1 | baseline/data-v1.sha256 | recover-and-checksum | ✓ WIRED | Tool cannot read a tag as source; verifier extracted the tag tree and verified 52/52 checksums + manifest-in-tag |
| CONCERNS.md | review agents → AUDIT.md | seed hypotheses → verify → table | ✓ WIRED | Three candidate files exist non-empty with 6-field schema; AUDIT.md rows trace to them; Method documents seeds-as-hypotheses |
| sorted(os.listdir) | byte-identical outputs | pinned iteration | ✓ WIRED | Run-twice byte-identity + committed-tree match prove the causal link |
| .gitleaks.toml | full-history scan | AND-condition suppresses exactly the record link | ✓ WIRED | Production scan exit 0; probe (no allowlist) exit 1 with exactly that finding |
| LICENSE | README badge/section | atomic consistency | ✓ WIRED | Single commit 8a78c4a contains both; badge/section/LICENSE agree on MIT |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| dnallm-mark/data/ (52 derived files) | all values | 42 model_performance inputs via the three generators | Yes — verifier regenerated the full chain and got a byte-identical committed tree | ✓ FLOWING |
| AUDIT.md findings | reproduction evidence | actual code + committed JSONs | Yes — 8 findings spot-checked against real code, all confirmed | ✓ FLOWING |
| PIN-VALIDATION.md inventory | diff counts | real regeneration runs | Yes — verifier re-derived the exact counts independently | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Comparator exit 0 on identical pair | `python3 baseline/compare.py tasks.json tasks.json` | VALUES IDENTICAL, exit 0 | ✓ PASS |
| Comparator exit 2 on missing file | compare.py on nonexistent path | readable error, exit 2 | ✓ PASS |
| Comparator summary contract | --summary-json on different pair | total 45 == len(diffs) == sum(counts), >8 untruncated, exit 1 | ✓ PASS |
| Tag recoverability | `git archive data-v1` + `sha256sum -c` | 52/52 OK (locale: 成功), exit 0 | ✓ PASS |
| Tagged-tree purity | `git diff data-v1^..data-v1 -- script/ scripts/ dnallm-mark/data/` | empty | ✓ PASS |
| Determinism run-twice | full chain ×2 + `sha256sum -c` | exit 0; working tree still clean (0 dirty files) | ✓ PASS |
| Migration gate (independent re-run) | compare.py --summary-json × 52 vs tag tree | MIGRATION-INVENTORY-OK | ✓ PASS |
| Tie-pair exactness | jq rank_score/rank both sides | 448.0 and 116.0 exact ties, ranks swap as documented; global pairs unchanged | ✓ PASS |
| Pin-validation re-derivation | pre-fix generators + pinned venv vs data-v1 | exact inventory match (42/33/41/42/2) | ✓ PASS |
| Empty-input equivalence (backstop) | pre vs post generators, empty input | same outputs; only intended generatedAt drop | ✓ PASS |
| gitleaks probe | rules-only config, --all | exit 1, exactly 1 finding, README.md:116 | ✓ PASS |
| gitleaks production | committed config, --all | exit 0, zero findings | ✓ PASS |
| venv isolation | site-packages listing | pandas/numpy only, no torch; Python 3.13.16 | ✓ PASS |
| AUDIT.md ordering | programmatic check | deterministic P0→P1→P2/subsystem/ID; IDs sequential | ✓ PASS |

### Probe Execution

Not applicable — this phase declares no `scripts/*/tests/probe-*.sh` probes and is not a migration/tooling phase in the probe sense; the plan's verify gates were re-executed directly (see Behavioral Spot-Checks).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| AUDIT-01 | 01-02 | Severity-graded findings report, all three subsystems, file:line + fix | ✓ SATISFIED | AUDIT.md 24 findings, all columns, subsystems covered |
| AUDIT-02 | 01-01 | Pre-fix baseline captured (golden outputs + data-v1 tag) before fixes | ✓ SATISFIED | Tag + 52-entry manifest + comparator; recoverability proven end-to-end; tag precedes FIX-05 commits |
| REL-01 | 01-03 | LICENSE present, data licensing declared separately | ✓ SATISFIED | MIT LICENSE + README License section (CC BY 4.0 separate) |
| REL-02 | 01-01 | Pinned offline/data-chain manifests; GPU group isolated | ✓ SATISFIED | pyproject groups + uv.lock + requirements.txt + .python-version; torch absent from default install |
| REL-05 | 01-03 | Secret hygiene settled; full-history scan confirms no other secrets | ✓ SATISFIED | Two-scan proof re-executed by verifier; narrow rule-scoped allowlist |
| FIX-05 | 01-03 | Deterministic generators (sorted iteration + sort_keys) | ✓ SATISFIED | Edit sites verified; run-twice byte-identity re-executed; migration attributed |

Orphaned requirements: none — REQUIREMENTS.md traceability maps exactly these six IDs to Phase 1 (all marked Complete); every other requirement maps to Phases 2-6.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | Debt markers (TBD/FIXME/XXX/TODO/HACK) in phase-modified code files | - | Zero matches in baseline/compare.py, both Python generators, JS generator, AUDIT.md |
| AUDIT.md | 148 | "placeholder values" text | ℹ️ Info | The audit's own maintainability finding describing pre-existing js/data.js dead code (routed to backlog) — not a phase stub |

### Decision Coverage

Gate output: 10/10 trackable CONTEXT.md decisions honored by shipped artifacts (skipped: false, blocking: false, not_honored: []).

### Test Quality Audit

Not applicable — this phase authors no tests (test infrastructure is Phase 2 per the roadmap); no test claims exist in the PLANs or SUMMARYs to audit.

### Human Verification Required

See `human_verification` frontmatter — 4 items (each fully specified with test/expected/why_human):

1. **D-06 tie-pair investigation acceptance** — confirm the root-cause census (six tie groups, four flip, two pre-documented global pairs do not swap) stands as a correct disposition.
2. **LICENSE copyright holder naming** — maintainer confirms/edits before the repo flips public (surfaced assumption).
3. **P0 severity boundary calls** — sanity-check that producer-side pipeline risks merit P0.
4. **Six flagged prohibitions** — unverified-prohibition, human review recommended (verifier evidence recorded above; per the soft-gate contract these never silently pass).

### Gaps Summary

No gaps. Every must-have truth is verified with direct codebase evidence; every behavioral claim (determinism, migration inventory, pin validation, empty-input semantics, secret scans, tag recoverability, gate behavior) was independently re-executed by the verifier rather than trusted from SUMMARY.md — including an exact-count reproduction of the pin-validation inventory and a clean independent re-run of the migration gate. Artifacts, wiring, data flow, and requirements coverage are all complete. Status is `human_needed` solely because judgment-tier items (flagged prohibitions plus the executors' own surfaced maintainer decisions) require human confirmation before the phase can be considered fully closed; none indicate missing or incorrect work.

---

_Verified: 2026-10-08T15:23:32Z_
_Verifier: Claude (gsd-verifier)_
