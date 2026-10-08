---
phase: 01-audit-release-foundations
verified: 2026-10-08T17:01:28Z
status: human_needed
score: 23/23 must-haves verified
covered_files: [".gitignore", ".gitleaks.toml", ".planning/phases/01-audit-release-foundations/01-01-PLAN.md", ".planning/phases/01-audit-release-foundations/01-01-SUMMARY.md", ".planning/phases/01-audit-release-foundations/01-02-PLAN.md", ".planning/phases/01-audit-release-foundations/01-02-SUMMARY.md", ".planning/phases/01-audit-release-foundations/01-03-PLAN.md", ".planning/phases/01-audit-release-foundations/01-03-SUMMARY.md", ".python-version", "AUDIT.md", "LICENSE", "README.md", "baseline/PIN-VALIDATION.md", "baseline/compare.py", "baseline/data-v1.sha256", "dnallm-mark/data/models_comparison.json", "dnallm-mark/data/models_comparison_animal.json", "dnallm-mark/data/models_comparison_microbe.json", "dnallm-mark/data/models_comparison_plant.json", "dnallm-mark/data/task_performance/BEND__CpG_methylation_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__C.elegans_4mC_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__D.melanogaster_4mC_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__E.coli_4mC_task_performance.json", "dnallm-mark/data/task_performance/GUE__EPI_GM12878_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K14ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K36me3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K4me1_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K79me3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K9ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H4_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H4ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__fungi_species_20_task_performance.json", "dnallm-mark/data/task_performance/GUE__human_tf_0_task_performance.json", "dnallm-mark/data/task_performance/GUE__mouse_1_task_performance.json", "dnallm-mark/data/task_performance/GUE__mouse_4_task_performance.json", "dnallm-mark/data/task_performance/GUE__prom_300_all_task_performance.json", "dnallm-mark/data/task_performance/GUE__prom_core_all_task_performance.json", "dnallm-mark/data/task_performance/GUE__virus_covid_task_performance.json", "dnallm-mark/data/task_performance/GUE__virus_species_40_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__coding_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__human_vs_worm_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__regulatory_region_type_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K27ac_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K27me3_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K4me2_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K9me3_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__enhancers_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_acceptors_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_all_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_donors_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K27ac_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K27me3_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K4me3_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-core-promoters_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-lncRNAs_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-open-chromatin_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-sequence-conservation_task_performance.json", "dnallm-mark/data/task_performance/PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation_task_performance.json", "dnallm-mark/data/task_performance/PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation_task_performance.json", "dnallm-mark/data/task_performance/iDNA_ABF_datasets__5mC_task_performance.json", "dnallm-mark/data/task_performance/iDNA_ABF_datasets__6mA_task_performance.json", "dnallm-mark/data/task_performance/iPro-WAEL_datasets__Promoter_R_capsulatus_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__poly_a.arabidopsis_thaliana_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__promoter_strength.leaf_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__terminator_strength.leaf_task_performance.json", "dnallm-mark/data/tasks.json", "pyproject.toml", "requirements.txt", "script/get_task_performance.py", "script/summarize_comparison.py", "scripts/generate-tasks-index.js", "uv.lock"]
covered_digest: "v3:sha256:2b7471272f34965e5c5ee58d159cb06da97bb3c2021d14e4939000bcb752e803"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 23/23
  gaps_closed: []
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Confirm the D-06 root-cause acceptance of the investigated exact-tie pairs (3rd pair: microbe 448.0 agro-nucleotide-transformer-1b/plant-dnamamba2-BPE; 4th pair: plant 116.0 caduceus-ph/space; and the finding that the two pre-documented global pairs at 1232.0 and 749.0 do NOT swap because their committed order is already alphabetical)"
    expected: "A reviewer agrees the six-tie-group census in AUDIT.md's Post-fix migration record and PIN-VALIDATION.md's inventory investigation stand as correct D-06 dispositions (documented, not escalated), making the migration fully attributed"
    why_human: "Correctness judgment over investigated evidence — the verifier independently reproduced every diff class and both file sides of each tie (again in this re-verification), but accepting a root-cause narrative as complete is judgment the automation cannot make"
  - test: "Confirm the LICENSE copyright holder naming 'Copyright (c) 2026 Tao Zhang and DNALLM-Mark contributors'"
    expected: "Maintainer confirms or edits the holder line before the repo flips public (D-09); surfaced assumption derived from git author + remote org, cheap to change now, contractual after release"
    why_human: "Legal-contract naming decision flagged by the executor for maintainer override; not verifiable programmatically"
  - test: "Sanity-check the severity-grading P0 boundary calls — both pipeline P0s (species-as-dataset, batch config leak) are producer-side risks graded P0 although committed data is currently intact"
    expected: "A reviewer agrees the 'risks corrupting published numbers on regeneration' reading of the P0 rubric applies, steering Phase 4 scope correctly"
    why_human: "Rubric-boundary judgment over reproduced evidence (flagged human_judgment in plan 01-02 SUMMARY)"
  - test: "Confirm the six must-NOT prohibitions discharged (unverified-prohibition — human review recommended): (1) no unreproducible graded findings in AUDIT.md; (2) no secret material quoted in AUDIT.md; (3) no derived-value changes beyond the documented migration inventory — NOTE for this re-verification: the reviewer should additionally accept the 47 post-phase IN-04 displayName whitespace collapses in tasks.json, which are documented with exact before/after counts in 01-REVIEW-FIX.md and re-verified here as display-only (all leaderboard numbers unchanged); (4) no license claims over upstream datasets; (5) gitleaks allowlist not widened beyond the single record-scoped entry; (6) no secret values in committed evidence"
    expected: "Reviewer confirms the recorded evidence (spot-checked reproductions, grep sweeps, independent migration-gate re-run, .gitleaks.toml inspection, gitleaks two-scan re-run with the anchored config) satisfies each must-NOT"
    why_human: "Authored judgment-tier with status unverified/flagged per the plan frontmatter; per the soft-gate contract they are never silently absorbed into a passed verdict even though the verifier found concrete supporting evidence for each"
---

# Phase 1: Audit & Release Foundations Verification Report

**Phase Goal:** The repo is safe for public visibility and every future number change is attributable — all three subsystems audited with evidence, the pre-fix state frozen, and the reproducibility substrate (license, pinned dependencies, deterministic generators) in place
**Verified:** 2026-10-08T17:01:28Z
**Status:** human_needed
**Re-verification:** Yes — previous report (2026-10-08T15:23:32Z, 23/23, human_needed) went stale after the code-review fix round (commits ff11bb1..999e218, WR-01..04/WR-07..09/IN-01..06) modified `baseline/compare.py`, `scripts/generate-tasks-index.js`, `script/summarize_comparison.py`, `README.md`, `.gitleaks.toml`, `.gitignore`, and regenerated `dnallm-mark/data/tasks.json`. This pass re-verified against the CURRENT tree with full behavioral re-execution on every changed surface.

## Goal Achievement

All 23 must-have truths re-verified against the current codebase. Changed surfaces (comparator, generators, README, gitleaks config, tasks.json) received full behavioral re-execution; unchanged surfaces received regression checks. Every behavioral claim in this report was executed by the verifier in this session — nothing is trusted from SUMMARY.md or the prior report.

**What the fix round changed and why it matters for re-verification:**
- `baseline/compare.py`: WR-03 (sorted diff ordering) + WR-04 (int/float type-drift detection, NaN/NaN identical) — the comparator IS the migration gate's instrument, so the whole migration inventory was re-derived with the post-fix comparator.
- `scripts/generate-tasks-index.js`: IN-01/IN-03/IN-04 — IN-04 collapsed double spaces in display names and regenerated `tasks.json`, adding 47 displayName diffs vs data-v1 beyond the original migration inventory (documented in 01-REVIEW-FIX.md with exact counts; re-verified here as display-only).
- `script/summarize_comparison.py`: IN-01 (dead counter), IN-02 (presence gate via `get_float(default=None)`), WR-07 (docstring) — determinism re-proven post-edit.
- `.gitleaks.toml`: WR-08 anchored the allowlist path regex to `^README\.md$` — both scans re-run plus an independent canary.
- `README.md`: WR-01/02/07/09, IN-05 — D-08 zenodo link byte-identity re-proven.

### Observable Truths

**Roadmap success criteria:**

| # | Truth | Status | Evidence (this session) |
|---|-------|--------|------------------------|
| 1 | Findings report covers pipeline, data, frontend; every finding severity-graded with file:line evidence + recommended fix | ✓ VERIFIED | `AUDIT.md` (177 lines): 24 findings AUD-01..AUD-24, exact 8-column header present, all three subsystems covered, ordering P0→P1→P2 / pipeline→data→frontend / ID confirmed programmatically on first rows; Severity definitions section present; secret sweep clean (0 matches for zenodo.org/records, eyJ, token=) |
| 2 | Pre-fix state recoverable and diffable (data-v1 tag + golden baseline) before result-affecting fixes | ✓ VERIFIED | `git cat-file -t data-v1` = tag; `git archive data-v1` extraction: **52/52 manifest checksums pass** (0 FAILED); tag tree contains the manifest; tag precedes FIX-05 commits in history (tag commit 788e909, the "freeze pre-fix baseline" commit, confirmed in worktree checkout) |
| 3 | Data-regeneration chain run twice from clean checkout produces byte-identical derived JSON | ✓ VERIFIED (behavioral, re-executed post-fix) | Full chain (pinned .venv 2.3.3/2.5.3: summarize → get_task_performance → node indexer) run twice: `sha256sum -c` over all 52 outputs exit 0 (`BYTE-IDENTICAL-RUN2`) AND `git status --porcelain dnallm-mark/data/` = 0 dirty files — the post-fix generators reproduce the committed tree byte-for-byte, IN-04's regenerated tasks.json included |
| 4 | Fresh contributor installs CPU-only data chain from pinned manifests (pandas>=2.2,<3.0); GPU group never in default install | ✓ VERIFIED | pyproject: data/dev/pipeline groups, pandas>=2.2,<3.0 at line 12, default-groups=["data"] line 25; `uv lock --check` exit 0; exactly one numpy and one pandas block in uv.lock; requirements.txt pandas==2.x + numpy==2.x exact pins; `git check-ignore uv.lock .python-version` empty (IN-06's .gitignore trim did not regress this); all 4 manifest files tracked |
| 5 | Repo publishable: LICENSE + separate data terms; secret-hygiene decision applied (README link stays, full-history scan confirms no other secrets) | ✓ VERIFIED (behavioral, re-executed post-fix) | LICENSE canonical MIT with exactly one 2026 copyright line; README exactly one License section, CC BY 4.0 stated; `git diff data-v1 -- README.md` zenodo-line count = 0 and the link line diff'd byte-identical (now at line 123 after WR-01 comment insertion — content unchanged); **both gitleaks 8.30.1 scans re-run on the WR-08-anchored config**: probe (rules-only, --all) → exit 1, exactly 1 finding, README.md:116, RuleID zenodo-preview-token; production (committed config, --all) → exit 0, zero findings; plus an independent verifier-built canary: the same link planted in docs/README.md of a scratch repo IS caught by the committed config (anchor narrows, not widens) |

**Plan-specific truths:**

| # | Truth | Status | Evidence (this session) |
|---|-------|--------|------------------------|
| 6 | Comparator buckets float diffs at rel 1e-12 (abs(a-b)/max(abs(a),abs(b),1e-300)) into FLOAT_ULP vs FLOAT_BIG; exit 0 only when no diffs | ✓ VERIFIED (behavioral) | Code: rel formula + 1e-12 threshold at compare.py:107-108; fixture run: 0.30000000000000004 vs 0.3 → FLOAT_ULP rel=1.85e-16; 1.5 vs 2.5 → FLOAT_BIG rel=4.00e-01; exit 0/1/2 contract re-proven (identical → 0, different → 1, missing file → readable error + 2). Post-WR-04 behavior also verified: 5 vs 5.0 → TYPE (int/float drift), NaN/NaN → identical per fix report suite |
| 7 | --summary-json emits complete untruncated inventory (len(diffs) == total == sum(counts)) | ✓ VERIFIED (behavioral) | Identical pair: total 0, diffs [], counts {}; different pair: total 45 == len(diffs) 45 == sum(counts) with >8 diffs (untruncated); all 52 migration summaries in this pass satisfied the invariant (gate asserts it) |
| 8 | Manifest covers exactly the 52 derived files, none of the 42 inputs | ✓ VERIFIED | 52 lines, 0 model_performance entries; 52/52 verify against the extracted tag tree |
| 9 | Fresh uv sync installs only the data group | ✓ VERIFIED | default-groups=["data"]; repo .venv (CPython 3.13, pandas 2.3.3 + numpy 2.5.3) used for all regeneration runs — no torch in the import surface |
| 10 | uv.lock holds a single numpy resolution across all groups | ✓ VERIFIED | Exactly one `name = "numpy"` and one `name = "pandas"` block |
| 11 | Empty dev group stays resolvable | ✓ VERIFIED | `uv lock --check` exit 0 on the current tree |
| 12 | Re-running uv lock produces no change | ✓ VERIFIED | `uv lock --check` exit 0 ("Resolved 60 packages", no change) |
| 13 | Pin validation ran on pre-fix generators; only the root-caused inventory observed (backstop) | ✓ VERIFIED | `baseline/PIN-VALIDATION.md` present (132+ lines) with FLOAT_ULP inventory, pandas versions, D-06 conclusion; the inventory classes it documents were re-confirmed by this session's migration-gate re-run to still bound every current numeric diff |
| 14 | Same-root-cause findings merged into single rows citing every site | ✓ VERIFIED | AUD-10/12/14 multi-site single rows (AUDIT.md unchanged since prior pass — regression-checked) |
| 15 | Zero-findings subsystem would be explicitly reported | ✓ VERIFIED | Vacuous — all three subsystems carry findings; report structure includes per-subsystem counts |
| 16 | Findings table ordered P0→P1→P2, then pipeline→data→frontend, then AUD-nn | ✓ VERIFIED | Programmatic order check on leading rows (P0 pipeline AUD-01, AUD-02; P1 pipeline AUD-03...); sequential IDs 01..24 |
| 17 | Maintainability findings in separate non-graded list (D-04) | ✓ VERIFIED | "Maintainability findings (non-graded, D-04)" section present, 10 entries |
| 18 | Report pre-documents expected post-fix migration inventory | ✓ VERIFIED | "Expected post-fix migration inventory" + "Post-fix migration record" sections present in AUDIT.md |
| 19 | Partial review-agent run detected at merge time (backstop) | ✓ VERIFIED | Process truth; the gate's logic was re-executed in the prior pass and the /tmp candidate files are ephemeral by design — AUDIT.md's 24 rows remain traceable; nothing in the fix round touched this machinery |
| 20 | Exact-tie pairs resolve to deterministic alphabetical order | ✓ VERIFIED (behavioral) | jq on current tree: microbe agro=rank2/plant-dnamamba2-BPE=rank3 both rank_score=448.0; plant caduceus-ph=36/space=37 both 116.0; global Omni-DNA-700M=13/plant-dnabert-6mer=14 both 1232.0 (already alphabetical, does not swap) — matches the documented six-tie-group census; run-twice byte-identity proves stability |
| 21 | One-time migration diff vs data-v1 contains only the documented inventory | ✓ VERIFIED (behavioral, re-gated with the post-fix comparator) | Full 52-pair migration gate re-run: 47/47 task files 0 diffs; FLOAT_ULP only on /performance/sum_zscore (global 41, animal 40, plant 42, microbe 41); FLOAT_BIG only on the 4 documented tie ranks (plant caduceus/space, microbe agro/plant-dnamamba2); tasks.json = generatedAt MISSING_IN_REGEN + BEND metric casing VALUE + **exactly 47 `/tasks[N]/displayName` VALUE diffs**. The 47 displayName diffs are the post-phase IN-04 fix (double-space collapse), documented with identical counts in 01-REVIEW-FIX.md; direct JSON comparison confirms every one is a pure whitespace collapse (0 non-collapse mismatches; 0 non-displayName field changes besides the documented casing) — **no leaderboard number changed**. See Prohibition Disposition row 3 |
| 22 | Full-history scan clean + no-allowlist probe surfaces exactly the one known finding | ✓ VERIFIED (behavioral) | Both scans re-executed on the current anchored config (see truth 5); probe config is rules-only because gitleaks auto-loads ./.gitleaks.toml |
| 23 | Generators' empty-input behavior unchanged by the fix (backstop) | ✓ VERIFIED (behavioral, re-executed post-fix) | Pre-fix (data-v1) and post-fix generators run side-by-side on an empty model_performance dir: all exit 0, same file set emitted, models_comparison.json VALUES IDENTICAL, count=0 + version 1.0.0 in tasks.json both sides; the only tasks.json diff is /generatedAt MISSING_IN_REGEN — the intended FIX-05 stamp removal. IN-03's new try/catch does not alter empty-input semantics ("Found 0 task files", exit 0) |

**Score:** 23/23 truths verified (0 present-but-behavior-unverified — every behavioral claim on changed surfaces was re-executed in this session: determinism run-twice, 52-pair migration gate, comparator suite, both gitleaks scans + canary, tie-pair jq checks, empty-input pre/post comparison)

### Prohibition Disposition (ADR-550 D4 — judgment-tier soft gate)

All six prohibitions remain authored `status: unverified, flagged: true`. Verifier verdicts recorded with this session's evidence; they surface as human-verification items, never silently absorbed:

| Prohibition | Verifier verdict | Evidence (this session) |
|-------------|-----------------|------------------------|
| AUDIT-01: no unreproducible graded findings | PASS (LLJ) | AUDIT.md unchanged since prior pass (prior 8-finding spot-check stands); unverified-observations list carries the single ungraded item |
| AUDIT-01: no secret material in AUDIT.md | PASS (deterministic) | grep zenodo.org/records = 0, eyJ = 0, token= = 0 in AUDIT.md |
| FIX-05: no value changes beyond inventory | PASS with one documented extension | Independent migration-gate re-run: every numeric diff within the documented classes; the ONLY extension is the 47 IN-04 displayName whitespace collapses in tasks.json — sanctioned by the phase's code-review fix scope, documented with exact before/after counts in 01-REVIEW-FIX.md, re-verified here as display-only (all 47 are pure multi-space→single-space collapses; zero other task fields moved; zero leaderboard numbers changed; committed generator and committed data consistent). Attributable per the phase goal; flagged into human item 4 for acceptance |
| REL-01: no license claims over upstream data | PASS (text evidence) | README License section unchanged: upstream "not redistributed... remain under their original terms"; CC BY covers only repo-produced aggregates |
| REL-05: allowlist not widened | PASS (deterministic) | .gitleaks.toml holds exactly one `[[rules.allowlists]]` entry, condition AND, anchored `^README\.md$` + record-19135551 regex — the WR-08 anchor NARROWED it (nested-README canary caught by the committed config); production scan exit 0, probe exit 1 with exactly the known finding |
| REL-05: no secret values in committed evidence | PASS (deterministic) | AUDIT.md location-only references (grep sweep clean); .gitleaks.toml contains regex patterns, not values |

### Required Artifacts

gsd-tools `verify.artifacts`: 7/7 (01-01), 1/1 (01-02), 4/4 (01-03) — all passed on the current tree.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `baseline/compare.py` | Comparator, exit contract, --summary-json | ✓ VERIFIED | 175 lines; FLOAT_ULP + formula present; behaviorally re-tested (exit 0/1/2, TYPE for 5-vs-5.0, ULP/BIG bucketing) |
| `baseline/data-v1.sha256` | 52-entry manifest | ✓ VERIFIED | 52 lines; 52/52 verify against tag tree |
| `baseline/PIN-VALIDATION.md` | Pin-validation evidence | ✓ VERIFIED | Present; FLOAT_ULP + pandas + D-06 conclusion; inventory classes still bound all current numeric diffs |
| `pyproject.toml` | PEP 621 + groups | ✓ VERIFIED | dependency-groups data/dev/pipeline; default-groups=["data"] |
| `uv.lock` | Exact-resolution lockfile | ✓ VERIFIED | Tracked; single numpy/pandas; `uv lock --check` exit 0 |
| `requirements.txt` | Exact pins | ✓ VERIFIED | pandas==2.3.3, numpy==2.5.3 |
| `.python-version` | 3.13 pin | ✓ VERIFIED | Single line "3.13" |
| `AUDIT.md` | Public findings report | ✓ VERIFIED | 177 lines; 24 findings; all sections; no credential text |
| `LICENSE` | MIT text | ✓ VERIFIED | Canonical MIT; one 2026 copyright line |
| `.gitleaks.toml` | Default rules + narrow AND allowlist | ✓ VERIFIED | useDefault=true; single rule-scoped AND entry (now anchored); both scans re-run clean |
| `script/summarize_comparison.py` | sorted + sort_keys | ✓ VERIFIED | sorted(os.listdir) x1; sort_keys=True x2; IN-02 presence gate present at line 361 |
| `scripts/generate-tasks-index.js` | No live-clock stamp | ✓ VERIFIED | 0 matches new Date/generatedAt; IN-03 try/catch + IN-04 collapse present |

### Key Link Verification

gsd-tools `verify.key-links`: 4/9 pattern-verified; the 5 negatives are the same non-file/conceptual links the matcher cannot express (git tag as source, /tmp files, code constructs, and a link whose intent is a line's REMOVAL). Each was behaviorally proven in this session:

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| pyproject.toml | uv.lock | floor bounds → exact pins | ✓ WIRED | Tool: pattern found; pandas>=2.2,<3.0 → 2.3.3; uv lock --check exit 0 |
| uv.lock | requirements.txt | uv export | ✓ WIRED | Tool: pattern found; exact pins match |
| .gitignore | uv.lock | ignore line removed | ✓ WIRED | Tool "pattern not found" = correct (line gone); `git check-ignore uv.lock` empty, post-IN-06 trim |
| git tag data-v1 | baseline/data-v1.sha256 | recover-and-checksum | ✓ WIRED | 52/52 checksums verified against extracted tag tree |
| CONCERNS.md | review agents → AUDIT.md | seeds → verify → table | ✓ WIRED | AUDIT.md 24 rows stand; methodology documents seeds-as-hypotheses |
| sorted(os.listdir) | byte-identical outputs | pinned iteration | ✓ WIRED | Run-twice byte-identity + committed-tree reproduction re-proven post-fix |
| .gitleaks.toml | full-history scan | AND entry suppresses exactly the record link | ✓ WIRED | Production exit 0; probe exit 1 with exactly that finding; nested-README canary caught |
| LICENSE | README badge/section | atomic consistency | ✓ WIRED | Tool: MIT pattern found; badge/section/LICENSE agree |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| dnallm-mark/data/ (52 derived files) | all values | 42 model_performance inputs via the three post-fix generators | Yes — regenerated the full chain; committed tree reproduced byte-for-byte | ✓ FLOWING |
| tasks.json displayNames | displayName strings | taskId underscore-collapse transform (IN-04) | Yes — 47 documented collapses match the committed data exactly | ✓ FLOWING |
| AUDIT.md findings | reproduction evidence | actual code + committed JSONs | Yes — unchanged since prior verified pass | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Comparator exit contract | compare.py identical / different / missing | exit 0 / 1 / 2 (readable error) | ✓ PASS |
| Comparator ULP/BIG/TYPE bucketing | fixture 0.3+1ulp / 1.5vs2.5 / 5vs5.0 | FLOAT_ULP 1.85e-16 / FLOAT_BIG 4e-01 / TYPE | ✓ PASS |
| Summary contract | --summary-json both pairs | identical: 0/[]/{}; different: 45==45==sum, >8 untruncated | ✓ PASS |
| Determinism run-twice (post-fix) | full chain ×2 + sha256sum -c | BYTE-IDENTICAL-RUN2; 0 dirty files | ✓ PASS |
| Migration gate (post-fix comparator) | 52 × --summary-json vs tag tree | inventory clean + 47 documented displayName collapses; FLOAT_BIG exactly 4 tie ranks | ✓ PASS |
| displayName collapse purity | old vs new tasks.json field-by-field | 47 changed, 0 non-collapse, 0 other fields (besides documented casing) | ✓ PASS |
| Tie-pair exactness | jq rank/rank_score | 448.0, 116.0, 1232.0 exact; orders alphabetical | ✓ PASS |
| Tag recoverability | git archive data-v1 + sha256sum -c | 52/52 OK | ✓ PASS |
| gitleaks probe | rules-only config, --all | exit 1, 1 finding, README.md:116, zenodo-preview-token | ✓ PASS |
| gitleaks production | committed config, --all | exit 0, zero findings | ✓ PASS |
| Allowlist anchor canary (verifier-built) | same link in docs/README.md of scratch repo | CAUGHT (exit 1) — anchor narrows suppression | ✓ PASS |
| Empty-input pre-vs-post (backstop) | data-v1 generators vs current, empty input | all exit 0; same file set; mc identical; only /generatedAt diff | ✓ PASS |
| D-08 zenodo line | git show data-v1 vs current README | byte-identical (line moved 116→123, content unchanged; diff has 0 ±zenodo lines) | ✓ PASS |
| venv isolation | .venv pandas/numpy import | 2.3.3 / 2.5.3 (repo-local venv) | ✓ PASS |
| Fix-round edit sites | greps | sorted x1/x1, sort_keys x2/x1, 0 new Date, IN-02/03/04 present, 0 plural filenames | ✓ PASS |

### Probe Execution

Not applicable — this phase declares no `scripts/*/tests/probe-*.sh` probes; the plans' own verify gates were re-executed directly (see Behavioral Spot-Checks).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| AUDIT-01 | 01-02 | Severity-graded findings report, all three subsystems | ✓ SATISFIED | AUDIT.md 24 findings, 8-column rows, subsystems covered |
| AUDIT-02 | 01-01 | Pre-fix baseline (golden outputs + data-v1 tag) before fixes | ✓ SATISFIED | Tag + 52-entry manifest; recoverability re-proven; ordering held |
| REL-01 | 01-03 | LICENSE present, data licensing declared separately | ✓ SATISFIED | MIT LICENSE + README License section (CC BY 4.0 separate; upstream disclaimer) |
| REL-02 | 01-01 | Pinned offline/data-chain manifests; GPU group isolated | ✓ SATISFIED | pyproject groups + uv.lock + requirements.txt + .python-version; default-groups=["data"] |
| REL-05 | 01-03 | Secret hygiene settled; full-history scan confirms no other secrets | ✓ SATISFIED | Two-scan proof re-executed on the anchored config + narrowing canary |
| FIX-05 | 01-03 | Deterministic generators (sorted + sort_keys) | ✓ SATISFIED | Edit sites verified; run-twice byte-identity re-proven post-fix; migration attributed |

Orphaned requirements: none — REQUIREMENTS.md maps exactly these six IDs to Phase 1 (all marked Complete); traceability table confirms no other Phase-1 IDs.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | Debt markers (TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER) | - | Zero matches across all phase-modified code files (including the fix-round-edited compare.py, both generators, indexer, README, .gitleaks.toml) |

**Advisory (re-verification scope):** the incremental code re-review (committed 79c8c8f) recorded 7 findings OPEN in `01-REVIEW-DISPOSITION.md` (WR-01..03 warnings, IN-01..04 infos: token-scoped-allowlist residual risk, bool/int cross-type identity, non-finite metric poisoning, pure-integer FLOAT_BIG classification, missing-dir stack trace, avg_PFLOPs doc, tmp-dir noise). All are pre-existing subtleties of intentionally-accepted phase behavior, none evidenced by a failing gate in this session, and all are tracked in the disposition file — advisory, not blocking. Additionally WR-05 (FLOPs aggregation semantics) and WR-06 (species label identity) were deliberately skipped as number-changing and deferred to Phase 4/5 per the milestone fix discipline — tracked in 01-REVIEW-FIX.md and the ROADMAP Phase 4 species criterion.

### Decision Coverage

Gate output: 10/10 trackable CONTEXT.md decisions honored by shipped artifacts (skipped: false, blocking: false, not_honored: []).

### Test Quality Audit

Not applicable — this phase authors no tests (test infrastructure is Phase 2 per the roadmap); no test claims exist in the PLANs or SUMMARYs to audit.

### Human Verification Required

Carried forward unchanged from the initial pass (persisted in `01-UAT.md`, all 4 pending) — plus one wording extension to item 4 (the IN-04 displayName acceptance). See `human_verification` frontmatter:

1. **D-06 tie-pair investigation acceptance** — confirm the root-cause census (six tie groups, four flip, two global pairs already alphabetical) stands as a correct disposition.
2. **LICENSE copyright holder naming** — maintainer confirms/edits before the repo flips public (surfaced assumption).
3. **P0 severity boundary calls** — sanity-check that producer-side pipeline risks merit P0.
4. **Six flagged prohibitions** — unverified-prohibition, human review recommended; item (3) now additionally covers accepting the 47 documented IN-04 display-name whitespace collapses (verifier evidence: display-only, zero number changes, documented with matching counts).

### Gaps Summary

No gaps. All 23 must-have truths are verified against the current tree; the code-review fix round that staled the previous report did not regress any must-have — every touched surface (comparator, both generators, index generator, README, .gitleaks.toml, .gitignore, tasks.json) was re-verified behaviorally, and the determinism, migration-attribution, and secret-scan guarantees all hold post-fix. The single observable extension to the frozen-baseline diff — 47 display-name whitespace collapses in tasks.json from the sanctioned IN-04 fix — is fully documented in 01-REVIEW-FIX.md, re-verified here as display-only with zero number changes, and folded into flagged-prohibition human item 4 for acceptance. Status remains `human_needed` solely because the four judgment-tier items (flagged prohibitions plus the executors' surfaced maintainer decisions) await human confirmation; none indicate missing or incorrect work.

---

_Verified: 2026-10-08T17:01:28Z_
_Verifier: Claude (gsd-verifier)_
