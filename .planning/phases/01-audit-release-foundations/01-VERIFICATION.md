---
phase: 01-audit-release-foundations
verified: 2026-10-09T21:00:00Z
status: passed
score: 23/23 must-haves verified
covered_files: [".gitignore", ".gitleaks.toml", ".planning/phases/01-audit-release-foundations/01-01-PLAN.md", ".planning/phases/01-audit-release-foundations/01-01-SUMMARY.md", ".planning/phases/01-audit-release-foundations/01-02-PLAN.md", ".planning/phases/01-audit-release-foundations/01-02-SUMMARY.md", ".planning/phases/01-audit-release-foundations/01-03-PLAN.md", ".planning/phases/01-audit-release-foundations/01-03-SUMMARY.md", ".python-version", "AUDIT.md", "LICENSE", "README.md", "baseline/PIN-VALIDATION.md", "baseline/compare.py", "baseline/data-v1.sha256", "dnallm-mark/data/models_comparison.json", "dnallm-mark/data/models_comparison_animal.json", "dnallm-mark/data/models_comparison_microbe.json", "dnallm-mark/data/models_comparison_plant.json", "dnallm-mark/data/task_performance/BEND__CpG_methylation_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__C.elegans_4mC_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__D.melanogaster_4mC_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__E.coli_4mC_task_performance.json", "dnallm-mark/data/task_performance/GUE__EPI_GM12878_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K14ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K36me3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K4me1_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K79me3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K9ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H4_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H4ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__fungi_species_20_task_performance.json", "dnallm-mark/data/task_performance/GUE__human_tf_0_task_performance.json", "dnallm-mark/data/task_performance/GUE__mouse_1_task_performance.json", "dnallm-mark/data/task_performance/GUE__mouse_4_task_performance.json", "dnallm-mark/data/task_performance/GUE__prom_300_all_task_performance.json", "dnallm-mark/data/task_performance/GUE__prom_core_all_task_performance.json", "dnallm-mark/data/task_performance/GUE__virus_covid_task_performance.json", "dnallm-mark/data/task_performance/GUE__virus_species_40_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__coding_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__human_vs_worm_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__regulatory_region_type_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K27ac_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K27me3_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K4me2_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K9me3_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__enhancers_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_acceptors_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_all_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_donors_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K27ac_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K27me3_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K4me3_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-core-promoters_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-lncRNAs_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-open-chromatin_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-sequence-conservation_task_performance.json", "dnallm-mark/data/task_performance/PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation_task_performance.json", "dnallm-mark/data/task_performance/PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation_task_performance.json", "dnallm-mark/data/task_performance/iDNA_ABF_datasets__5mC_task_performance.json", "dnallm-mark/data/task_performance/iDNA_ABF_datasets__6mA_task_performance.json", "dnallm-mark/data/task_performance/iPro-WAEL_datasets__Promoter_R_capsulatus_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__poly_a.arabidopsis_thaliana_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__promoter_strength.leaf_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__terminator_strength.leaf_task_performance.json", "dnallm-mark/data/tasks.json", "pyproject.toml", "requirements.txt", "script/get_task_performance.py", "script/summarize_comparison.py", "scripts/generate-tasks-index.js", "uv.lock"]
covered_digest: "v3:sha256:c0e4792226a2e21dcd203b1aa4a42d2995ca2d88b1d79c2a5f70101f38c80e5f"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 23/23
  gaps_closed:
    - "STALE-REFRESH: prior report (2026-10-09T00:48:10Z) passed but its fingerprint went stale — Phases 2/3 modified 4 files in the covered set (.gitignore, README.md, pyproject.toml, uv.lock; proven by git diff name-status against the prior-verification commit 38f4f31). This pass re-verified EVERY must-have with fresh evidence at HEAD cce36c6 (post Phase-3 merge 41bf49e, registries unified to JSON, dnallmmark_pipeline.py deprecated with banner naming run_finetune.py per REV-10)"
    - "Re-anchored changed surfaces: README License section + MIT badge + CC BY 4.0 + upstream disclaimer (now lines 370-374); Zenodo link byte-identical 293-byte URL (moved README:116 -> README:123 by the Phase-3 rewrite — D-08 invariant is over the link, which is unchanged, byte-compared against data-v1 and pre-merge 360be65); pyproject group surface ([pipeline] renamed [gpu] per Phase-3 D-05 with exact pins torch==2.11.0/transformers==5.17.0, default-groups=[\"data\"] retained, dev group gained Phase-2/3 tools); uv.lock re-resolved (71 packages, still single numpy/pandas resolutions matching requirements.txt exact pins)"
    - "Re-confirmed baseline/ discipline on the current tree: git diff 360be65 HEAD -- baseline/ is EMPTY and -- dnallm-mark/data/ is EMPTY (leaderboard data tree byte-identical to pre-merge)"
  gaps_remaining: []
  regressions: []
---

# Phase 1: Audit & Release Foundations Verification Report (Stale-Refresh)

**Phase Goal:** The repo is safe for public visibility and every future number change is attributable — all three subsystems audited with evidence, the pre-fix state frozen, and the reproducibility substrate (license, pinned dependencies, deterministic generators) in place
**Verified:** 2026-10-09T21:00:00Z
**Status:** passed
**Re-verification:** Yes — STALE-REFRESH. The prior report (2026-10-09T00:48:10Z, passed 23/23) went stale because later phases changed covered files: `git diff --name-status <prior-verification commit 38f4f31> HEAD` over the implementation covered set shows exactly four modified files — `.gitignore`, `README.md`, `pyproject.toml`, `uv.lock` — all from Phase 2/3 work (test harness, toolchain, README rewrite around `run_finetune.py`, lock re-resolution). Every other covered file (LICENSE, AUDIT.md, .gitleaks.toml, baseline/ trio, requirements.txt, .python-version, both Python generators, the JS generator, all 52 derived data files) is git-proven unchanged. This pass re-verified every must-have against the CURRENT tree at HEAD `cce36c6` with fresh behavioral evidence — not a delta of the old report.

## Goal Achievement

### Evidence policy for this pass (stale-refresh)

- **Changed surfaces** (README.md, pyproject.toml, uv.lock, .gitignore) — verified directly, full depth, this session.
- **Unchanged surfaces** — non-change proven by git diff against the prior-verification commit, then RE-EXECUTED live anyway wherever cheap (tag-manifest 52/52, run-twice determinism in a clean HEAD worktree, the full 52-pair migration gate, gitleaks production + probe scans, comparator smoke, uv lock --check, tie-pair ordering). Prior behavioral executions are leveraged only where re-execution adds nothing beyond byte-identical inputs (comparator fixture edge suite, empty-input pre/post comparison) or is impossible by nature (process truths).
- **Phase-3 semantic shifts** — recorded as SUPERSEDED BY DESIGN where a Phase-1 wording references the pre-Phase-3 world (pipeline active status, [pipeline] group name, empty dev group, README line number). None of these are violations; each supersession cites the Phase-3 decision (REV-10 / D-05 / maintainer ty directive).

### Observable Truths

**Roadmap success criteria:**

| # | Truth | Status | Evidence (fresh at HEAD unless noted) |
|---|-------|--------|----------|
| 1 | Findings report covers pipeline, data scripts, frontend; every finding severity-graded with file:line evidence + recommended fix | ✓ VERIFIED | AUDIT.md unchanged since prior pass (git: 0 commits since 38f4f31); re-checked live: 177 lines, 24 `AUD-` rows (8-column table), severity ladder P0(2)→P1(12)→P2(10) contiguous, all three subsystems present (pipeline 56 refs, data-script, frontend), per-row file:line + reproduction + fix + disposition columns, secret-grep 0 matches (zenodo.org/records, eyJ, token=). AUD-01-P0 and AUD-05-P1 rows still anchor the later lock/registry work (see Decision Coverage note below) |
| 2 | Pre-fix state recoverable and diffable (data-v1 tag + golden baseline) before result-affecting fixes | ✓ VERIFIED (re-executed) | `git cat-file -t data-v1` = tag; tag tree extracted via `git archive` this session: **52/52 manifest checksums OK (LC_ALL=C), 0 failures**; manifest = 52 lines, 0 model_performance entries |
| 3 | Data-regeneration chain run twice from clean checkout produces byte-identical derived JSON | ✓ VERIFIED (re-executed — stronger than prior pass) | Fresh git worktree at HEAD; full chain (get_task_performance.py → summarize_comparison.py → generate-tasks-index.js) run TWICE, all six generator invocations exit 0, worktree `git status --porcelain` = **0 dirty files after both runs** — both runs reproduce the committed tree byte-for-byte |
| 4 | Fresh contributor installs CPU-only data chain from pinned manifests (pandas>=2.2,<3.0); GPU group never in default install | ✓ VERIFIED (re-executed) | pyproject (current): `pandas>=2.2,<3.0` data-group floor, `default-groups = ["data"]`; GPU deps in a separate `[gpu]` group (name superseded: was `[pipeline]`, renamed by Phase-3 D-05, exact pins torch==2.11.0/transformers==5.17.0, explicit pytorch-cu130 index — isolation invariant unchanged and strengthened); `uv lock --check` exit 0 (71 packages); repo venv: pandas 2.3.3 / numpy 2.5.3, `find_spec('torch') is None`; no CI config exists yet (`.github` absent) so nothing can install the GPU group; requirements.txt pins pandas==2.3.3/numpy==2.5.3 == lock resolutions |
| 5 | Repo publishable: LICENSE + separate data terms; secret-hygiene decision applied (README Zenodo link stays, full-history scan confirms no other secrets) | ✓ VERIFIED (re-executed on the changed surface) | LICENSE unchanged (git): canonical MIT body sha256 `f9c4c77baa38...`, exactly one copyright line "Copyright (c) 2026 zhangtaolab and DNALLM-Mark contributors", pure ASCII; README (rewritten by Phase 3): MIT badge line 3, License section at 370-374 — MIT code + CC BY 4.0 derived aggregates + "Upstream datasets are not redistributed ... remain under their original terms"; **Zenodo record-19135551 link byte-for-byte identical** (293-byte URL incl. token, diff-verified against both data-v1 and pre-merge 360be65 README — line moved 116→123 with the rewrite; the D-08 invariant is over the link, which is unchanged); **gitleaks 8.30.1 production scan re-run live: `git --log-opts=--all` over 171 commits (up from 69 — covers all Phase-2/3 additions) → "no leaks found", exit 0** |

**Plan-specific truths (01-01 / 01-02 / 01-03):**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 6 | Comparator buckets float diffs at rel 1e-12 (abs(a-b)/max(abs(a),abs(b),1e-300)) into FLOAT_ULP vs FLOAT_BIG; exit 0 only when no diffs | ✓ VERIFIED (re-executed at scale) | baseline/ tree unchanged (git diff vs pre-merge 360be65 empty); identical-pair smoke "VALUES IDENTICAL" exit 0; the fresh 52-pair gate (below) exercised the comparator over 104 real files with correct FLOAT_ULP / FLOAT_BIG / VALUE / MISSING_IN_REGEN classification; prior fixture suite (ULP 1.85e-16, BIG 4e-01, TYPE cross-type) leveraged — compare.py byte-identical since |
| 7 | --summary-json emits complete untruncated inventory (len(diffs) == total == sum(counts)) | ✓ VERIFIED (re-executed) | Every one of the 52 fresh summary-json outputs parsed and classified this session; totals reconcile (e.g. tasks.json total 49 = 1 MISSING_IN_REGEN + 48 VALUE; comparison files 40-44 diffs each fully enumerated); untruncated output observed directly (49-diff tasks.json inventory printed in full) |
| 8 | Manifest covers exactly the 52 derived files, none of the 42 inputs | ✓ VERIFIED (re-executed) | 52 lines, 0 model_performance entries, 52/52 OK vs extracted tag tree |
| 9 | Fresh uv sync installs only the data group | ✓ VERIFIED (re-executed) | default-groups=["data"] in current pyproject; venv carries pandas/numpy only from the data chain; torch absent (find_spec None) |
| 10 | uv.lock holds a single numpy resolution across all groups | ✓ VERIFIED (re-executed on the CHANGED lock) | Exactly one `name = "numpy"` and one `name = "pandas"` block in the current (71-package, Phase-3 re-resolved) lock; versions 2.5.3 / 2.3.3 match requirements.txt exactly |
| 11 | Empty dev group keeps resolution working | ✓ VERIFIED (wording SUPERSEDED by design) | The dev group is no longer empty: Phase 2 added pytest/ruff/jsonschema (the Phase-1 plan's own comment anticipated this — "Phase 2 adds pytest/ruff"), Phase 3 added ty>=0.0.85 per maintainer directive. The invariant the truth protects — dependency-group resolution keeps working — re-proven live: `uv lock --check` exit 0 |
| 12 | Re-running uv lock produces no change | ✓ VERIFIED (re-executed) | `uv lock --check` exit 0, "Resolved 71 packages in 1ms" |
| 13 | Pin validation ran on pre-fix generators; only the root-caused inventory observed (backstop) | ✓ VERIFIED | baseline/PIN-VALIDATION.md present and unchanged (5 FLOAT_ULP references); its documented inventory is exactly what the fresh 52-pair migration gate reproduced against the current tree (truth 21) — the bounding claim re-confirmed on live evidence |
| 14 | Same-root-cause findings merged into single rows citing every site | ✓ VERIFIED | AUDIT.md unchanged; AUD-10/12/14 multi-site single rows stand from the verified prior pass |
| 15 | Zero-findings subsystem would be explicitly reported | ✓ VERIFIED | Vacuous — all three subsystems carry findings; explicit no-findings contract stands in the unchanged methodology section |
| 16 | Findings table ordered P0→P1→P2, then subsystem, then AUD-nn | ✓ VERIFIED (severity ladder re-checked live) | Fresh awk check: P0×2, P1×12, P2×10 — contiguous, correctly ordered; within-severity subsystem/ID ordering stands from the prior programmatic check on the unchanged file |
| 17 | Maintainability findings in separate non-graded list (D-04) | ✓ VERIFIED | "## Maintainability findings (non-graded, D-04)" section present at line 142 in the unchanged file |
| 18 | Report pre-documents expected post-fix migration inventory | ✓ VERIFIED | "### Expected post-fix migration inventory" (line 103) + "### Post-fix migration record" (line 115) sections present; the inventory was RE-CONFIRMED empirically by the fresh 52-pair gate |
| 19 | Partial review-agent run detected at merge time (backstop) | ✓ VERIFIED | Process truth; /tmp candidate files ephemeral by design; AUDIT.md's 24 rows remain traceable; machinery untouched since the verified pass |
| 20 | Exact-tie pairs resolve to deterministic alphabetical order | ✓ VERIFIED (re-executed) | All four exact-tie pairs checked live in the committed data: all-file 1232.0 [Omni-DNA-700M, plant-dnabert-6mer], all-file 749.0 [gena-lm-bigbird-base-t2t, hyenadna-large-1m-seqlen-hf], plant 116.0 [caduceus-ph..., space], microbe 448.0 [agro-nucleotide-transformer-1b, plant-dnamamba2-BPE] — every pair in ascending alphabetical order; run-twice byte-identity (truth 3) proves machine-independence |
| 21 | One-time migration diff vs data-v1 contains only the documented inventory | ✓ VERIFIED (re-executed in full) | Fresh 52-pair gate, tag tree vs HEAD tree, comparator --summary-json per file: **47 task_performance files IDENTICAL**; 4 comparison files: FLOAT_ULP diffs exclusively on `sum_zscore` fields (40/41/41/42 per file), FLOAT_BIG exactly 4 total = the two documented tie-rank swaps (plant caduceus/space 36↔37, microbe agro/plant-dnamamba2 2↔3), nothing else; tasks.json: 1 MISSING_IN_REGEN (/generatedAt) + 48 VALUE (47 IN-04 displayName whitespace collapses + 1 BEND auprc→AUPRC casing). Matches the pre-documented inventory + the documented IN-04 extension exactly; zero out-of-inventory diffs |
| 22 | Full-history scan clean + no-allowlist probe surfaces exactly the one known finding | ✓ VERIFIED (both halves re-executed live) | Production: 171 commits, "no leaks found", exit 0. Probe (detect --no-git, 3.30 GB incl. untracked files): exactly **1 finding** — README.md:123, RuleID zenodo-preview-token, the intentional link (surfaces because absolute-path scan misses the `^README\.md$` anchor — the fail-loud behavior the config comment documents); no other secret anywhere scanned |
| 23 | Generators' empty-input behavior unchanged by the fix (backstop) | ✓ VERIFIED | All three generators: 0 commits since the prior verification (git-proven), so the prior pre-fix-vs-post-fix empty-input behavioral comparison transfers byte-for-byte; Phase-2's test harness additionally exercises the generators on the current tree (suite green, truth below) |

**Score:** 23/23 truths verified (0 present-but-behavior-unverified; 0 overrides; 4 wording-level supersessions recorded in the Superseded-by-Design table — each protects an invariant that was re-proven live)

### Superseded by Design (Phase-3 semantic shifts — not violations)

The Phase-3 merge (41bf49e) changed the meaning of several Phase-1 wordings. Each supersession cites the deciding record; the underlying invariant was re-verified live in this pass.

| Phase-1 wording | Current reality | Deciding record | Invariant re-verified |
|---|---|---|---|
| AUDIT.md findings describe `pipeline/dnallmmark_pipeline.py` as the active benchmark producer | File retained read-only under a DEPRECATED module banner naming `pipeline/run_finetune.py` as the entry point (banner verified live, lines 1-16) | Phase-3 REV-10/F10; D-03 lock pivot | AUDIT.md is a point-in-time PRE-FIX report — its findings are historical records, not current-state claims; the findings contract (graded, evidenced, ordered, dispositioned) is intact; AUD-01's lock pivoted to the export-chain contract (Phase-3 D-03), AUD-05's registry work landed as D-10 unification |
| "GPU pipeline dependencies" in a `[pipeline]` group | Group renamed `[gpu]` with exact pins (torch==2.11.0, transformers==5.17.0) + explicit cu130 index | Phase-3 D-05 code-only scope | REL-02 isolation invariant: not in default-groups, not installed in any repo-managed env (torch findable: False), no CI exists to install it |
| "dev declared as an empty list" | dev = [jsonschema, pytest, ruff, ty] | Phase-2 harness; Phase-3 maintainer ty directive (anticipated by Phase-1's own plan comment "Phase 2 adds pytest/ruff") | Resolution stability: uv lock --check exit 0 |
| "the Zenodo preview link at README.md:116" | Link now at README.md:123 after the Phase-3 README rewrite | Phase-3 af12068 README restructure | Link URL byte-identical (293 bytes, diffed against data-v1 and 360be65); allowlist path-anchored `^README\.md$` — line-number independent |

### Prohibition Disposition (ADR-550 D4 — judgment tier, human-resolved at the prior UAT; evidence re-confirmed on the current tree)

All six prohibitions were confirmed by the maintainer in 01-UAT.md test 4 (2026-10-09, pass) — that resolution stands. Verifier evidence re-checked fresh:

| Prohibition | Maintainer | Fresh verifier evidence |
|-------------|-----------|-------------------------|
| AUDIT-01: no unreproducible graded findings | Confirmed (UAT 4) | AUDIT.md unchanged; "Unverified observations" section (line 53) carries the demotion list |
| AUDIT-01: no secret material in AUDIT.md | Confirmed (UAT 4) | Re-grepped: zenodo.org/records = 0, eyJ = 0, token= = 0 |
| FIX-05: no value changes beyond inventory | Confirmed (UAT 4) | **Re-proven at full strength**: the fresh 52-pair gate bounds every diff to the documented inventory (truth 21) |
| REL-01: no license claims over upstream data | Confirmed (UAT 4) | README License section (current rewrite) re-read: upstream datasets "not redistributed ... remain under their original terms"; CC BY covers only repo-produced aggregates |
| REL-05: allowlist not widened | Confirmed (UAT 4) | .gitleaks.toml unchanged (git): exactly one rule-scoped `[[rules.allowlists]]`, condition AND, anchored `^README\.md$` + record-19135551 regex; live production scan clean over 171 commits |
| REL-05: no secret values in committed evidence | Confirmed (UAT 4) | AUDIT.md location-only references (sweep clean); .gitleaks.toml contains regex patterns, not values |

### Required Artifacts

gsd-tools `verify.artifacts` re-run this session on the current tree: **7/7 (01-01), 1/1 (01-02), 4/4 (01-03) — 12/12 passed**.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `baseline/compare.py` | Comparator, exit contract, --summary-json | ✓ VERIFIED | baseline/ byte-identical to pre-merge (git diff empty); re-executed over 104 files this session |
| `baseline/data-v1.sha256` | 52-entry manifest | ✓ VERIFIED | 52 lines; 52/52 OK vs extracted tag tree (fresh) |
| `baseline/PIN-VALIDATION.md` | Pin-validation evidence | ✓ VERIFIED | Present, unchanged, 5 FLOAT_ULP refs |
| `pyproject.toml` | PEP 621 + groups | ✓ VERIFIED (changed surface re-read) | data/dev/gpu groups; default-groups=["data"]; pandas floor intact; [tool.ty]/[tool.uv.index] additions are Phase-2/3 scope |
| `uv.lock` | Exact-resolution lockfile | ✓ VERIFIED (changed surface re-read) | 71 packages; single numpy/pandas; `uv lock --check` exit 0 |
| `requirements.txt` | Exact pins | ✓ VERIFIED | pandas==2.3.3, numpy==2.5.3 (== lock) |
| `.python-version` | 3.13 pin | ✓ VERIFIED | Tracked, not ignored (check-ignore exit 1) |
| `AUDIT.md` | Public findings report | ✓ VERIFIED | 177 lines; 24 findings; no credential text |
| `LICENSE` | MIT text | ✓ VERIFIED | Unchanged; canonical body; holder "zhangtaolab" per D-09 |
| `.gitleaks.toml` | Default rules + narrow AND allowlist | ✓ VERIFIED | Unchanged; single anchored entry; live scans in both directions |
| `script/summarize_comparison.py` | sorted + sort_keys | ✓ VERIFIED | 0 commits since prior verification; sorted(os.listdir + sort_keys=True present; re-executed twice green |
| `scripts/generate-tasks-index.js` | No live-clock stamp | ✓ VERIFIED | 0 commits since prior verification; re-executed twice green |

### Key Link Verification

gsd-tools `verify.key-links`: 4/10 pattern-verified; the 6 negatives are non-file/conceptual links the matcher cannot express (git tag as source, /tmp ephemeral files, code constructs, .planning process docs, a negative ignore-line claim). Each was behaviorally re-proven live this session:

| From | To | Via | Status | Fresh evidence |
|------|----|----|--------|----------------|
| pyproject.toml | uv.lock | floor bounds → exact pins | ✓ WIRED (pattern + live) | pandas>=2.2,<3.0 → pandas 2.3.3 in lock; uv lock --check exit 0 |
| uv.lock | requirements.txt | uv export of data group | ✓ WIRED (pattern) | pins identical across both (live read) |
| .gitignore | uv.lock | ignore line REMOVED (negative link) | ✓ WIRED (behavioral) | `git check-ignore uv.lock` exit 1; lock tracked; Phase-3 .gitignore edit added only `.planning/tmp/` |
| git tag data-v1 | baseline/data-v1.sha256 | recover-and-checksum | ✓ WIRED (behavioral) | 52/52 OK from extracted tag tree (fresh) |
| CONCERNS.md seeds | review agents | D-01 re-verification input | ✓ WIRED (process; prior pass) | CONCERNS.md exists; process link, evidenced in AUDIT.md methodology |
| /tmp audit candidates | AUDIT.md table | executor verify pass | ✓ WIRED (process; prior pass) | Ephemeral by design; 24 rows traceable |
| PIN-VALIDATION.md | AUDIT.md methodology | pre-documented inventory | ✓ WIRED (behavioral) | Inventory re-confirmed empirically by fresh 52-pair gate |
| sorted(os.listdir) in generators | byte-identical outputs | pinned iteration + sort_keys | ✓ WIRED (behavioral) | Run-twice in clean HEAD worktree: 0 dirty files (fresh) |
| .gitleaks.toml allowlist | full-history scan | AND-condition suppression | ✓ WIRED (behavioral) | Production 171-commit scan clean; probe surfaces exactly the one intentional finding (fresh) |
| LICENSE | README badge + License section | consistency | ✓ WIRED (pattern + live) | Badge line 3 MIT; section 370-374 consistent post-rewrite (fresh read) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| dnallm-mark/data/ (52 derived files) | all values | 42 model_performance inputs via the three generators | Yes — the full chain re-run twice from a clean HEAD checkout reproduced the committed tree byte-for-byte (0 dirty) | ✓ FLOWING |
| tasks.json displayNames | displayName strings | IN-04 collapse transform | Yes — 47 documented collapses present in committed data (re-observed in the migration gate diffs) | ✓ FLOWING |
| AUDIT.md findings | reproduction evidence | actual code + committed JSONs | Yes — unchanged since the verified pass; AUD-01/AUD-05 anchor later-phase locks | ✓ FLOWING |

### Behavioral Spot-Checks (this session, all fresh)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Tag recoverability + manifest integrity | `git archive data-v1` + `LC_ALL=C sha256sum -c` | 52/52 OK, 0 failures | ✓ PASS |
| Manifest shape | line count + model_performance grep | 52 lines, 0 input entries | ✓ PASS |
| Determinism (run-twice, clean checkout) | full chain x2 in git worktree at HEAD | 6/6 generator exits 0; 0 dirty files after both runs | ✓ PASS |
| Migration gate (52-pair, tag vs HEAD) | compare.py --summary-json per file | 47 IDENTICAL; ULP=sum_zscore only; BIG=4 tie ranks only; tasks.json = generatedAt + 47 displayName + 1 metric casing — exactly the documented inventory | ✓ PASS |
| Tie-pair ordering | python rank_score scan over 4 comparison files | all 4 exact-tie pairs alphabetical | ✓ PASS |
| Lock stability | `uv lock --check` | exit 0, 71 packages | ✓ PASS |
| Comparator smoke | compare.py tasks.json vs itself | VALUES IDENTICAL, exit 0 | ✓ PASS |
| gitleaks production scan | `gitleaks git --log-opts=--all --config .gitleaks.toml` | 171 commits, no leaks found, exit 0 | ✓ PASS |
| gitleaks probe (no suppression) | `gitleaks detect --no-git --source <repo>` | exactly 1 finding: README.md:123 zenodo-preview-token (the intentional link); 3.30 GB scanned incl. untracked | ✓ PASS |
| MIT body integrity | sha256 vs canonical | identical (f9c4c77b...) | ✓ PASS |
| Zenodo link byte-integrity | URL diff vs data-v1 + 360be65 README | 293-byte URL byte-identical | ✓ PASS |
| baseline/ + data-tree discipline | `git diff 360be65 HEAD -- baseline/ -- dnallm-mark/data/` | both empty | ✓ PASS |
| Full workspace suite (once) | `make test` | 193 passed + 5 xfailed + node lane 2 pass | ✓ PASS |

Prior-pass behavioral executions leveraged only for: comparator fixture edge suite (compare.py byte-identical), empty-input pre/post comparison (generators byte-identical, 0 commits since).

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes declared by this phase. The gitleaks probe-scan behavior (truth 22) was executed directly by the verifier in its own process (table above).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| AUDIT-01 | 01-02 | Severity-graded findings report, all three subsystems | ✓ SATISFIED | AUDIT.md 24 findings re-checked live (truth 1, 14-18) |
| AUDIT-02 | 01-01 | Pre-fix baseline (golden outputs + data-v1 tag) before fixes | ✓ SATISFIED | Tag + 52-entry manifest; 52/52 recoverability re-proven fresh (truth 2, 8) |
| REL-01 | 01-03 | LICENSE present, data licensing declared separately | ✓ SATISFIED | MIT LICENSE + README CC BY 4.0 section + upstream disclaimer, re-read on the Phase-3-rewritten README (truth 5) |
| REL-02 | 01-01 | Pinned offline/data-chain manifests; GPU deps isolated from CI | ✓ SATISFIED | Groups + uv.lock + requirements.txt + .python-version; default-groups=["data"]; [gpu] group never installed (truth 4, 9-12) |
| REL-05 | 01-03 | Secret hygiene settled; full-history scan confirms no other secrets | ✓ SATISFIED | Live 171-commit production scan clean + probe exactly-one-finding (truth 22); Zenodo link byte-identical |
| FIX-05 | 01-03 | Deterministic generators (sorted + sort_keys) | ✓ SATISFIED | Run-twice byte-identity re-proven fresh at HEAD (truth 3, 20, 23) |

Orphaned requirements: none. REQUIREMENTS.md maps exactly AUDIT-01, AUDIT-02, REL-01, REL-02, REL-05, FIX-05 to Phase 1 (all marked Complete) — the plan frontmatter union equals the same six. (The verification task brief additionally listed REL-03, REL-04, DATA-01, DATA-02; per REQUIREMENTS.md those belong to Phases 6, 2, 5, 5 respectively — REL-04 Complete via Phase 2, the others Pending in their own phases — so they are not Phase-1 scope and not orphans of it.)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | TBD/FIXME/XXX debt markers | - | 0 across all implementation covered files (fresh grep) |
| (none) | - | TODO/HACK/PLACEHOLDER/stub patterns | - | 0 in the four changed covered files (fresh grep) |

### Decision Coverage

Gate re-run this session: **10/10 CONTEXT.md decisions (D-01..D-10) honored** (`check.decision-coverage-verify`: skipped false, blocking false, not_honored []). D-09 (holder retitle) and D-08 (Zenodo link kept) verified directly on the current tree; the Phase-3 decisions that superseded Phase-1 wordings (REV-10 deprecation, D-05 [gpu] rename) are recorded in the Superseded-by-Design table with their deciding records.

### Human Verification Required

None. The four judgment-tier items from the original phase were resolved with recorded maintainer confirmations in 01-UAT.md (status: complete; 4/4 pass, 2026-10-09T00:38:08Z) — that resolution is unchanged and nothing in this refresh produced a new behavior-unverified truth or a new judgment surface: every truth carries fresh behavioral evidence from this session or git-proven byte-identity with the prior behavioral pass.

### Gaps Summary

No gaps. The stale fingerprint was caused by exactly four covered files modified by Phases 2/3 (git-proven: .gitignore, README.md, pyproject.toml, uv.lock); each changed surface was re-verified directly and each is consistent with the Phase-1 contracts — the README rewrite preserved the License section, badge, upstream disclaimer, and the byte-identical Zenodo link; the pyproject/lock evolution (group rename, dev tooling, exact GPU pins) preserved and strengthened the REL-02 isolation contract; the .gitignore edit did not re-ignore the lockfile. Every unchanged surface was proven unchanged and then re-executed live anyway: the data-v1 tag still verifies 52/52, the regeneration chain run twice from a clean HEAD checkout reproduces the committed tree byte-for-byte, the 52-pair migration gate still bounds every diff to the pre-documented inventory, all four exact-tie pairs still resolve alphabetically, the comparator still holds its exit contract, the lock still resolves stably with single numpy/pandas resolutions, and the full-history secret scan is clean over 171 commits with the probe surfacing exactly the one intentional link. Phase-3's deliberate semantic shifts (pipeline deprecation per REV-10, [pipeline]→[gpu] rename per D-05, dev-group tooling) are recorded as superseded-by-design with their invariants re-proven — none is a violation. Phase 1's goal — repo safe for public visibility, every future number change attributable — remains achieved at HEAD.

---

_Verified: 2026-10-09T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
