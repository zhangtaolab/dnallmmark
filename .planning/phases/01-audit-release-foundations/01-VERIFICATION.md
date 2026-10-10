---
phase: 01-audit-release-foundations
verified: 2026-10-10T07:24:56Z
status: passed
score: 23/23 must-haves verified
covered_files: [".gitignore", ".gitleaks.toml", ".planning/phases/01-audit-release-foundations/01-01-PLAN.md", ".planning/phases/01-audit-release-foundations/01-01-SUMMARY.md", ".planning/phases/01-audit-release-foundations/01-02-PLAN.md", ".planning/phases/01-audit-release-foundations/01-02-SUMMARY.md", ".planning/phases/01-audit-release-foundations/01-03-PLAN.md", ".planning/phases/01-audit-release-foundations/01-03-SUMMARY.md", ".python-version", "AUDIT.md", "LICENSE", "Makefile", "README.md", "baseline/PIN-VALIDATION.md", "baseline/compare.py", "baseline/data-v1.sha256", "dnallm-mark/data/models_comparison.json", "dnallm-mark/data/models_comparison_animal.json", "dnallm-mark/data/models_comparison_microbe.json", "dnallm-mark/data/models_comparison_plant.json", "dnallm-mark/data/task_performance/BEND__CpG_methylation_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__C.elegans_4mC_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__D.melanogaster_4mC_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__E.coli_4mC_task_performance.json", "dnallm-mark/data/task_performance/GUE__EPI_GM12878_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K14ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K36me3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K4me1_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K79me3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K9ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H4_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H4ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__fungi_species_20_task_performance.json", "dnallm-mark/data/task_performance/GUE__human_tf_0_task_performance.json", "dnallm-mark/data/task_performance/GUE__mouse_1_task_performance.json", "dnallm-mark/data/task_performance/GUE__mouse_4_task_performance.json", "dnallm-mark/data/task_performance/GUE__prom_300_all_task_performance.json", "dnallm-mark/data/task_performance/GUE__prom_core_all_task_performance.json", "dnallm-mark/data/task_performance/GUE__virus_covid_task_performance.json", "dnallm-mark/data/task_performance/GUE__virus_species_40_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__coding_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__human_vs_worm_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__regulatory_region_type_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K27ac_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K27me3_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K4me2_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K9me3_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__enhancers_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_acceptors_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_all_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_donors_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K27ac_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K27me3_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K4me3_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-core-promoters_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-lncRNAs_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-open-chromatin_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-sequence-conservation_task_performance.json", "dnallm-mark/data/task_performance/PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation_task_performance.json", "dnallm-mark/data/task_performance/PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation_task_performance.json", "dnallm-mark/data/task_performance/iDNA_ABF_datasets__5mC_task_performance.json", "dnallm-mark/data/task_performance/iDNA_ABF_datasets__6mA_task_performance.json", "dnallm-mark/data/task_performance/iPro-WAEL_datasets__Promoter_R_capsulatus_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__poly_a.arabidopsis_thaliana_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__promoter_strength.leaf_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__terminator_strength.leaf_task_performance.json", "dnallm-mark/data/tasks.json", "pyproject.toml", "requirements.txt", "script/export_runs.py", "script/summarize_comparison.py", "scripts/generate-tasks-index.js", "uv.lock"]
covered_digest: "v3:sha256:6ebda8df63018039ef426188fa71817bd412eae310dd15e128a12b327bc4b8a7"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 23/23
  gaps_closed:
    - "STALE-REFRESH #2: the prior report (2026-10-09T21:00:00Z, passed 23/23 at cce36c6) went stale because Phase 4 modified 11 files in its covered set — git diff cce36c6..015a0cf over the implementation set shows exactly: baseline/compare.py (D-13 INT/BOOL_CROSS labels), models_comparison_animal.json + models_comparison_microbe.json (species regroup), GUE__EPI_GM12878 + GUE__fungi_species_20 task files + tasks.json (OQ4 species corrections), pyproject.toml + uv.lock (D-15 scipy/evaluate), README.md (exporter docs + pivot-retirement rewrite of the data-chain section), script/get_task_performance.py (DELETED — retired per Phase-4 OQ6/D-decisions), script/summarize_comparison.py (registry-Category grouping + isfinite + metric-mirror deletion). This pass re-verified EVERY must-have with fresh evidence at HEAD 015a0cf."
    - "Covered set updated for the current tree: script/get_task_performance.py dropped (deleted); Makefile and script/export_runs.py added (the current `make data` chain and its module-level import are the evidence surface for the determinism truths); all 52 data files, the baseline trio, manifests, LICENSE/AUDIT/.gitleaks.toml, README, pyproject/uv.lock/requirements retained."
    - "Fresh fingerprint computed over the updated set (74 files): v3:sha256:6ebda8df..."
  gaps_remaining: []
  regressions: []
---

# Phase 1: Audit & Release Foundations Verification Report (Stale-Refresh #2, post-Phase-4)

**Phase Goal:** The repo is safe for public visibility and every future number change is attributable — all three subsystems audited with evidence, the pre-fix state frozen, and the reproducibility substrate (license, pinned dependencies, deterministic generators) in place
**Verified:** 2026-10-10T07:24:56Z
**Status:** passed
**Re-verification:** Yes — STALE-REFRESH. The prior report (2026-10-09T21:00:00Z, passed 23/23 at cce36c6) went stale after Phase 4 modified 11 files in the covered set. Every must-have was re-verified against the CURRENT tree at HEAD `015a0cf` with fresh behavioral evidence; nothing was leveraged from the prior report except surfaces git-proven byte-identical since (AUDIT.md, LICENSE, .gitleaks.toml, baseline/data-v1.sha256, baseline/PIN-VALIDATION.md, requirements.txt, .python-version, .gitignore, scripts/generate-tasks-index.js, models_comparison.json, models_comparison_plant.json, 45 task_performance files — all absent from `git diff cce36c6..HEAD`), and even those were re-executed live wherever cheap.

## Goal Achievement

### Evidence policy for this pass (stale-refresh #2)

- **Phase-4-changed surfaces** (summarize_comparison.py, compare.py, README.md, pyproject.toml, uv.lock, 5 data files, deleted pivot) — verified directly at full depth this session.
- **Phase-4-designed changes supersede by record, never fail**: the pivot retirement (OQ6/D-decisions, IN-03), the species-grouping switch (FIX-02/AUD-01, maintainer-approved in `04-CATEGORY-REVIEW.md`), the D-15 dependency additions, and the D-13 comparator label additions are recorded in the Superseded-by-Design table with their invariants re-proven live. Each supersession cites the deciding Phase-4 record.
- **Unchanged surfaces** — non-change proven by git, then re-executed live anyway (tag 52/52, make-data determinism ×2, 52-pair migration gate, gitleaks both directions, comparator contract, uv lock check, tie-pair scan).

### Observable Truths

**Roadmap success criteria:**

| # | Truth | Status | Evidence (fresh at HEAD 015a0cf unless noted) |
|---|-------|--------|----------|
| 1 | Findings report covers pipeline, data scripts, frontend; every finding severity-graded with file:line evidence + recommended fix | ✓ VERIFIED | AUDIT.md unchanged since Phase 1 (git log: last touch 511a100); re-checked live: 24 `AUD-` rows (8-column table), severity ladder re-scanned fresh: P0×2 → P1×12 → P2×10 contiguous and correctly ordered, all three subsystems present, per-row file:line + reproduction + fix + disposition; secret sweep re-grepped: zenodo.org/records=0, eyJ=0, token==0; Unverified-observations, Post-fix-migration-record, and filled Secret-scan-evidence sections all present |
| 2 | Pre-fix state recoverable and diffable (data-v1 tag + golden baseline) before result-affecting fixes | ✓ VERIFIED (re-executed) | `git cat-file -t data-v1` = tag; tag tree freshly extracted via `git archive`: **52/52 manifest checksums OK (LC_ALL=C), 0 failures**; manifest = 52 lines, 0 model_performance entries |
| 3 | Data-regeneration chain run twice from a clean state produces byte-identical derived JSON | ✓ VERIFIED (re-executed on the CURRENT chain) | Chain superseded by record (see Superseded table): `make data` = summarize_comparison.py + generate-tasks-index.js (Makefile:38-40; pivot retired Phase 4). Run TWICE this session at HEAD: both runs exit 0 and `git status --porcelain dnallm-mark/data/` = **0 dirty files after each run** — the current chain reproduces the committed tree byte-for-byte, twice |
| 4 | Fresh contributor installs CPU-only data chain from pinned manifests (pandas>=2.2,<3.0); GPU group never in default install | ✓ VERIFIED (re-executed on the changed substrate) | pyproject (current): `pandas>=2.2,<3.0` floor intact, `default-groups = ["data"]`, GPU deps isolated in `[gpu]` (torch==2.11.0/transformers==5.17.0, explicit cu130 index); `uv lock --check` exit 0 (**88 packages** — grew with D-15 scipy/evaluate); repo venv: pandas 2.3.3 / numpy 2.5.3 / scipy 1.18.1, `find_spec('torch') is None`; requirements.txt pins pandas==2.3.3/numpy==2.5.3 == lock resolutions (see Warning W-1 on export currency) |
| 5 | Repo publishable: LICENSE + separate data terms; secret-hygiene decision applied (Zenodo link stays, full-history scan confirms no other secrets) | ✓ VERIFIED (re-executed) | LICENSE unchanged since Phase 1 (git log: 33b80ca D-09 retitle): MIT text, exactly one line "Copyright (c) 2026 zhangtaolab and DNALLM-Mark contributors"; README (Phase-4-rewritten data sections only): MIT badge line 3, License section at 373-377 — MIT code + CC BY 4.0 derived aggregates + upstream not-redistributed disclaimer; **Zenodo record-19135551 link byte-for-byte identical to data-v1's** (293-byte URL diff-compared fresh; now README:123); **gitleaks 8.30.1 production scan re-run live: 222 commits (--all), "no leaks found", exit 0** |

**Plan-specific truths (01-01 / 01-02 / 01-03):**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 6 | Comparator buckets float diffs at rel 1e-12 (abs(a-b)/max(abs(a),abs(b),1e-300)) into FLOAT_ULP vs FLOAT_BIG; exit 0 only when no diffs | ✓ VERIFIED (re-executed) | compare.py modified by Phase 4 (D-13): diff reviewed — only ADDITIVE INT + BOOL_CROSS labels; the rel formula and 1e-12 threshold lines untouched (compare.py:124-128); identical pair → "VALUES IDENTICAL" exit 0; diff pair → exit 1; missing file → readable message exit 2; usage → exit 2 (all fresh) |
| 7 | --summary-json emits complete untruncated inventory (len(diffs) == total == sum(counts)) | ✓ VERIFIED (re-executed) | Self-pair: total=0, diffs=[], counts={} asserted; tasks.json vs models_comparison.json: exit 1 with **total=45 == len(diffs) == sum(counts)**, >8 diffs (untruncated); all 52 fresh migration-gate summaries parsed with the same reconciliation check — zero INCOMPLETE-INVENTORY |
| 8 | Manifest covers exactly the 52 derived files, none of the 42 inputs | ✓ VERIFIED (re-executed) | 52 lines, 0 model_performance entries, 52/52 OK vs extracted tag tree |
| 9 | Fresh uv sync installs only the data group | ✓ VERIFIED (re-executed) | default-groups=["data"] (current pyproject); repo venv carries pandas/numpy/scipy from the data chain, torch absent (find_spec None) |
| 10 | uv.lock holds a single numpy resolution across all groups | ✓ VERIFIED (re-executed on the CHANGED lock) | Exactly one `name = "numpy"` (2.5.3) and one `name = "pandas"` (2.3.3) block in the current 88-package D-15 lock; scipy and evaluate each exactly one block; versions match requirements.txt exactly |
| 11 | Empty dev group keeps resolution working | ✓ VERIFIED (wording SUPERSEDED by design — carried forward) | dev = [jsonschema, pytest, ruff, ty] since Phases 2/3; the invariant (group resolution stays working) re-proven live: `uv lock --check` exit 0 |
| 12 | Re-running uv lock produces no change | ✓ VERIFIED (re-executed) | `uv lock --check` exit 0, "Resolved 88 packages in 0.98ms" |
| 13 | Pin validation ran on pre-fix generators; only the root-caused inventory observed (backstop) | ✓ VERIFIED | PIN-VALIDATION.md present and unchanged (git; 5 FLOAT_ULP refs, pandas documented); its bounding claim re-confirmed empirically — the fresh 52-pair gate (truth 21) reproduces exactly the documented inventory classes on the unchanged files and bounds every changed file to the Phase-4 documented corrections |
| 14 | Same-root-cause findings merged into single rows citing every site | ✓ VERIFIED | AUDIT.md unchanged; AUD-10/12/14 multi-site single rows stand from the verified pass |
| 15 | Zero-findings subsystem would be explicitly reported | ✓ VERIFIED | Vacuous — all three subsystems carry findings; contract stands in the unchanged methodology section |
| 16 | Findings table ordered P0→P1→P2, then subsystem, then AUD-nn | ✓ VERIFIED (severity ladder re-checked live) | Fresh awk scan: P0 P0 → P1×12 → P2×10, contiguous and correctly ordered; within-severity ordering stands on the unchanged file |
| 17 | Maintainability findings in separate non-graded list (D-04) | ✓ VERIFIED | "## Maintainability findings (non-graded, D-04)" section present in the unchanged file |
| 18 | Report pre-documents expected post-fix migration inventory | ✓ VERIFIED | "Expected post-fix migration inventory" + "Post-fix migration record" sections present (unchanged); inventory re-confirmed empirically by the fresh gate (truth 21), extended by the Phase-4 documented species corrections |
| 19 | Partial review-agent run detected at merge time (backstop) | ✓ VERIFIED | Process truth; /tmp candidates ephemeral by design; 24 rows remain traceable; machinery untouched since the verified pass |
| 20 | Exact-tie pairs resolve to deterministic alphabetical order | ✓ VERIFIED (re-executed on the CURRENT data) | Fresh python scan of all 4 committed comparison files: every exact rank_score tie group is in ascending alphabetical order — all-file 749.0 [gena-lm-bigbird-base-t2t, hyenadna-large-1m-seqlen-hf] and 1232.0 [Omni-DNA-700M, plant-dnabert-6mer]; plant 116.0 [caduceus-ph..., space] and 54.0; the Phase-4 species regroup created NEW tie groups in animal (587.0) and the re-ranked microbe (155.0/175.0/198.0/349.0) — all alphabetical; make-data ×2 byte-identity proves machine-independence |
| 21 | One-time migration diff vs data-v1 contains only the documented inventory | ✓ VERIFIED (re-executed in full, with Phase-4 supersession recorded) | Fresh 52-pair gate, tag tree vs HEAD tree, --summary-json per file, every summary reconciled (total==len==sum): **45 task files IDENTICAL; 2 task files exactly 1 VALUE each on /info/species (EPI_GM12878 Microbe→Animals, fungi Animals→Microbe — the Phase-4 OQ4 corrections)**; all-file comparison: FLOAT_ULP only, all on /performance/sum_zscore; plant: 42 ULP (all sum_zscore) + **2 INT = exactly the documented caduceus/space 36↔37 tie swap** (relabeled FLOAT_BIG→INT by Phase 4's honest-label change — same underlying diff); animal/microbe: large re-aggregation diffs **confined entirely to /performance/(avg_*/sum_*/rank/rank_score) fields** (the expected consequence of the Phase-4 registry-Category regroup — FLOAT_BIG 321/321, INT 55/60, ULP 2/2, nothing structural); tasks.json: 50 VALUE = 47 displayName collapses + 1 BEND auprc→AUPRC + 2 species entries, plus /generatedAt MISSING_IN_REGEN. **Zero out-of-set diffs; every diff attributable to Phase-1's documented inventory or Phase-4's maintainer-approved, recorded species corrections** |
| 22 | Full-history scan clean + no-allowlist probe surfaces exactly the one known finding | ✓ VERIFIED (both halves re-executed live) | Production (committed config, --all): 222 commits, "no leaks found", exit 0. Probe (rules-only config — detection rule retained, allowlist stripped — over full git history): exactly **1 finding: README.md, RuleID zenodo-preview-token, commit 09fb0ae, the intentional link**; no other secret anywhere in history. First probe attempt accidentally retained the allowlist (0 findings); rerun with verified-stripped config to get the true positive — detection not trusted, re-proven |
| 23 | Generators' empty-input behavior unchanged by the fix (backstop) | ✓ VERIFIED (superseded in part by record) | Pivot's portion superseded: get_task_performance.py retired Phase 4 (OQ6/D-decisions IN-03) with its assertions folded into tests/test_export_runs.py (Phase-4 fold-mapping verified there); the surviving generators (summarize_comparison.py, generate-tasks-index.js) are exercised by the Phase-2+ harness on the current tree (Phase-4 verification: 232-test suite green; make-data no-op re-proven here); summarize's only Phase-4 semantic edits (registry join, isfinite, mirror deletion) are Phase-4-verified number-neutral via the same make-data byte-identity gate re-run here |

**Score:** 23/23 truths verified (0 present-but-behavior-unverified; 0 overrides; Phase-4 semantic shifts recorded in the Superseded-by-Design table — each protects an invariant that was re-proven live this session)

### Superseded by Design (Phase-4 semantic shifts — not violations)

Phase 4 deliberately changed the meaning of several Phase-1 wordings. Each supersession cites the deciding Phase-4 record; the underlying invariant was re-verified live in this pass.

| Phase-1 wording | Current reality | Deciding record | Invariant re-verified |
|---|---|---|---|
| Data chain = summarize_comparison.py + **get_task_performance.py** + generate-tasks-index.js | Pivot script DELETED; chain is `make data` = summarize + generate-tasks-index (task_performance files are committed static data until E2' regenerates them via export_runs.py) | Phase-4 OQ6/D-decisions, IN-03 (04-05); README documents the honest static-data status | Run-twice byte-identity on the current chain: `make data` ×2, 0 dirty files (truth 3) |
| Comparator diff vocabulary = 8 classes incl. FLOAT_BIG for int rank pairs | Vocabulary widened with INT (int-vs-int) and BOOL_CROSS (bool/int cross-type) labels; formula/threshold/exit contract untouched | Phase-4 D-13, IN-01, WR-02 (commits b34f43e/a0d254d) | Exit contract 0/1/2 + summary-json reconciliation re-proven live; plant tie-swap diffs now honestly labeled INT — same diffs, verified by path (truth 6, 21) |
| `[data]` group = pandas + numpy floors | Group widened: scipy>=1.15.2 + evaluate>=0.4.6 (D-15) — scipy is a module-level import of the chain via export_runs | Phase-4 D-15 maintainer Option C (commit 0189d4c) | Lock stability + single resolutions + default-groups isolation + torch-absent venv (truths 4, 9-12); export-currency drift flagged as Warning W-1 |
| Derived data tree = post-migration state gated at Phase 1 | animal/microbe re-aggregated + 2 task-file species values + tasks.json 2 entries changed by the species-grouping fix | Phase-4 FIX-02/AUD-01 (6bb9364), maintainer-approved 50-row Category review (04-CATEGORY-REVIEW.md), OQ4 (aa27ea3) | Every diff vs data-v1 still attributable: fresh 52-pair gate bounds all diffs to Phase-1 inventory + exactly these documented corrections (truth 21); `make data` no-op proves the current tree is exactly what the current chain produces |
| Tie-pair population = the 4 Phase-1 pairs | Population changed with the regroup (microbe 448.0 pair subsumed; new ties in animal/microbe) | Same FIX-02 record | Every exact tie in all 4 current files resolves alphabetically (truth 20) |
| README data-chain section named the 3-script chain | README rewritten by Phase 4: exporter section added, pivot instructions removed, `make data` chain documented | Phase-4 04-05 README docs (2a26a66) | License section, badge, disclaimer, and the byte-identical Zenodo link all survive the rewrite (truth 5, fresh diff-verified) |
| (Carried forward) pipeline deprecation, [pipeline]→[gpu] rename, dev-group tooling, README line drift | Stand as recorded at the prior refresh | Phase-3 REV-10 / D-05 / maintainer ty directive / af12068 | Invariants re-proven here: lock isolation, resolution stability, link byte-identity |

### Prohibition Disposition (ADR-550 D4 — judgment tier, human-resolved at the Phase-1 UAT; evidence re-confirmed on the current tree)

All six prohibitions were confirmed by the maintainer in 01-UAT.md test 4 (2026-10-09, pass) — that resolution stands; nothing in this refresh produced a new judgment surface. Fresh verifier evidence:

| Prohibition | Maintainer | Fresh verifier evidence |
|-------------|-----------|-------------------------|
| AUDIT-01: no unreproducible graded findings | Confirmed (UAT 4) | AUDIT.md unchanged; Unverified-observations section carries the demotion list |
| AUDIT-01: no secret material in AUDIT.md | Confirmed (UAT 4) | Re-grepped: zenodo.org/records=0, eyJ=0, token==0 |
| FIX-05: no value changes beyond inventory | Confirmed (UAT 4) | **Re-proven at full strength with the Phase-4 extension recorded**: the fresh 52-pair gate bounds every diff to the Phase-1 inventory + the maintainer-approved Phase-4 species corrections, nothing else |
| REL-01: no license claims over upstream data | Confirmed (UAT 4) | README License section re-read on the current tree: upstream "not redistributed ... remain under their original terms"; CC BY covers only repo-produced aggregates |
| REL-05: allowlist not widened | Confirmed (UAT 4) | .gitleaks.toml unchanged since Phase 1 (git log: d14c9bd): exactly one rule-scoped `[[rules.allowlists]]`, condition AND, anchored `^README\.md$` + record-19135551 regex; production scan clean over 222 commits |
| REL-05: no secret values in committed evidence | Confirmed (UAT 4) | AUDIT.md location-only references (sweep clean); .gitleaks.toml carries regex patterns, not values |

### Required Artifacts

gsd-tools `verify.artifacts` re-run this session: **7/7 (01-01), 1/1 (01-02), 4/4 (01-03) — 12/12 passed**.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `baseline/compare.py` | Comparator, exit contract, --summary-json | ✓ VERIFIED (changed surface re-read + re-executed) | Phase-4 delta reviewed: additive labels only; executed over 104 files this session with contract asserted |
| `baseline/data-v1.sha256` | 52-entry manifest | ✓ VERIFIED | 52 lines; 52/52 OK vs extracted tag tree (fresh) |
| `baseline/PIN-VALIDATION.md` | Pin-validation evidence | ✓ VERIFIED | Present, unchanged, 5 FLOAT_ULP refs, D-06 conclusion |
| `pyproject.toml` | PEP 621 + groups | ✓ VERIFIED (changed surface re-read) | data/dev/gpu groups; default-groups=["data"]; pandas floor intact; D-15 scipy/evaluate and [tool.ty]/[tool.uv.index] are Phase-3/4 scope |
| `uv.lock` | Exact-resolution lockfile | ✓ VERIFIED (changed surface re-read) | 88 packages; single numpy/pandas/scipy/evaluate; `uv lock --check` exit 0 |
| `requirements.txt` | Exact pins | ✓ VERIFIED (with Warning W-1) | pandas==2.3.3, numpy==2.5.3 (== lock); header intact; export is stale w.r.t. the D-15-widened data group — see Anti-Patterns |
| `.python-version` | 3.13 pin | ✓ VERIFIED | Content `3.13`; not gitignored (check-ignore exit 1) |
| `AUDIT.md` | Public findings report | ✓ VERIFIED | Unchanged; 24 findings; ladder re-scanned; no credential text |
| `LICENSE` | MIT text | ✓ VERIFIED | Unchanged since 33b80ca; canonical MIT; holder "zhangtaolab" per D-09 |
| `.gitleaks.toml` | Default rules + narrow AND allowlist | ✓ VERIFIED | Unchanged; single anchored entry; both scan directions re-run live |
| `script/summarize_comparison.py` | sorted + sort_keys | ✓ VERIFIED (changed surface re-read) | sorted(os.listdir + sort_keys=True still present under the Phase-4 edits; re-executed twice green via `make data` |
| `scripts/generate-tasks-index.js` | No live-clock stamp | ✓ VERIFIED | Unchanged since prior verification; no `new Date`; re-executed twice green |

### Key Link Verification

gsd-tools `verify.key-links`: 3/7 pattern-verified; the 4 negatives are non-file/negative/conceptual links the pattern matcher cannot express (a git tag as source, a REMOVED ignore line, a code-construct source, a config-to-scan-process link). Each was behaviorally re-proven live this session:

| From | To | Via | Status | Fresh evidence |
|------|----|----|--------|----------------|
| pyproject.toml | uv.lock | floor bounds → exact pins | ✓ WIRED (pattern + live) | pandas floor → pandas 2.3.3 in lock; `uv lock --check` exit 0 |
| uv.lock | requirements.txt | uv export of data group | ✓ WIRED (pattern; currency drift flagged W-1) | pins identical across both (live read); fresh export differs in group coverage (see W-1) |
| .gitignore | uv.lock | ignore line REMOVED (negative link) | ✓ WIRED (behavioral) | `git check-ignore uv.lock .python-version` exit 1; both tracked |
| git tag data-v1 | baseline/data-v1.sha256 | recover-and-checksum | ✓ WIRED (behavioral) | 52/52 OK from extracted tag tree (fresh) |
| sorted(os.listdir) in the generators | byte-identical outputs | pinned iteration + sort_keys | ✓ WIRED (behavioral) | `make data` ×2 at HEAD: 0 dirty files (fresh) |
| .gitleaks.toml allowlist | full-history scan | AND-condition suppression | ✓ WIRED (behavioral) | Production 222-commit scan clean; rules-only probe surfaces exactly the one intentional finding (fresh, both directions) |
| LICENSE | README badge + License section | consistency | ✓ WIRED (pattern + live) | Badge line 3 MIT; section 373-377 consistent post-Phase-4-rewrite (fresh read) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| dnallm-mark/data/ (52 derived files) | all values | 42 model_performance inputs via the current chain (+ registry Category join since Phase 4) | Yes — `make data` ×2 reproduces the committed tree byte-for-byte (0 dirty) | ✓ FLOWING |
| models_comparison_animal/microbe.json | per-arena aggregates | model_performance × registry Category (hard-fail join) | Yes — 42 models, join-derived membership; re-aggregation attributed and gated (truth 21) | ✓ FLOWING |
| tasks.json displayNames + species | displayName / species strings | IN-04 collapse transform + registry-corrected species | Yes — 47 collapses + 2 Phase-4 corrections present in committed data (re-observed in the gate) | ✓ FLOWING |
| AUDIT.md findings | reproduction evidence | actual code + committed JSONs | Yes — unchanged; findings anchor the later-phase locks (AUD-01 → Phase-4 FIX-02; AUD-05 → registry unification) | ✓ FLOWING |

### Behavioral Spot-Checks (this session, all fresh)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Tag recoverability + manifest integrity | `git archive data-v1` + `LC_ALL=C sha256sum -c` | 52/52 OK, 0 failures | ✓ PASS |
| Manifest shape | line count + model_performance grep | 52 lines, 0 input entries | ✓ PASS |
| Determinism (current chain, run-twice) | `make data` ×2 + porcelain check | both runs 0 dirty files | ✓ PASS |
| Migration gate (52-pair, tag vs HEAD) | compare.py --summary-json per file + class classifier | 45 IDENTICAL + 2 species-corrected task files; all/plant ULP on sum_zscore only; plant 2 INT = tie swap; animal/microbe re-aggregation fields only; tasks.json = generatedAt + casing + 47 displayName + 2 species; zero out-of-set | ✓ PASS |
| Tie-pair ordering | python rank_score scan over 4 comparison files | every exact-tie group alphabetical (incl. the new Phase-4-regroup ties) | ✓ PASS |
| Comparator contract | self-pair / diff-pair / missing-file / usage | 0 / 1 / 2 / 2 exits; summary reconciliation total==len==sum; 45-diff untruncated inventory | ✓ PASS |
| Lock stability | `uv lock --check` | exit 0, 88 packages | ✓ PASS |
| gitleaks production scan | `gitleaks git --config .gitleaks.toml --log-opts=--all .` | 222 commits, no leaks found, exit 0 | ✓ PASS |
| gitleaks probe (no suppression) | `gitleaks git --config <rules-only> --log-opts=--all .` | exactly 1 finding: README.md zenodo-preview-token @09fb0ae | ✓ PASS |
| Zenodo link byte-integrity | URL extract diff: data-v1 README vs HEAD README | 293-byte URL byte-identical (now line 123) | ✓ PASS |
| MIT body + holder | LICENSE read + git log | MIT, one line, holder zhangtaolab (D-09), unchanged since 33b80ca | ✓ PASS |
| venv isolation | find_spec + imports | torch absent; pandas 2.3.3 / numpy 2.5.3 / scipy 1.18.1 | ✓ PASS |
| Data export currency | `uv export --group data --no-emit-project` vs committed file | fresh export = 40 packages vs committed 6 → **Warning W-1** (not a gate failure; see Anti-Patterns) |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes exist or are declared by this phase. The gitleaks two-scan proof (truth 22) was executed directly by the verifier in its own process (table above); the make-data determinism gates likewise ran in-process.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| AUDIT-01 | 01-02 | Severity-graded findings report, all three subsystems | ✓ SATISFIED | AUDIT.md 24 findings re-checked live (truths 1, 14-18) |
| AUDIT-02 | 01-01 | Pre-fix baseline (golden outputs + data-v1 tag) before fixes | ✓ SATISFIED | Tag + 52-entry manifest; 52/52 recoverability re-proven fresh (truths 2, 8) |
| REL-01 | 01-03 | LICENSE present, data licensing declared separately | ✓ SATISFIED | MIT LICENSE + README CC BY 4.0 + upstream disclaimer re-read on the Phase-4-rewritten README (truth 5) |
| REL-02 | 01-01 | Pinned offline/data-chain manifests; GPU deps isolated from CI | ✓ SATISFIED | Groups + uv.lock (88 pkgs) + requirements.txt + .python-version; default-groups=["data"]; [gpu] never installed (truths 4, 9-12); W-1 notes the pip-export currency drift |
| REL-05 | 01-03 | Secret hygiene settled; full-history scan confirms no other secrets | ✓ SATISFIED | Live 222-commit production scan clean + rules-only probe exactly-one-finding (truth 22); Zenodo link byte-identical |
| FIX-05 | 01-03 | Deterministic generators (sorted + sort_keys) | ✓ SATISFIED | Run-twice byte-identity re-proven fresh at HEAD on the current chain (truths 3, 20, 23) |

Orphaned requirements: none — REQUIREMENTS.md maps exactly AUDIT-01, AUDIT-02, REL-01, REL-02, REL-05, FIX-05 to Phase 1 (all Complete), matching the plan frontmatter union.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| requirements.txt | whole file | Stale uv export: committed file (6 packages) no longer equals `uv export --group data` output (40 packages) — Phase 4's D-15 widened [data] with scipy/evaluate without re-exporting; the pip path cannot run the current chain (scipy is a module-level import via export_runs), and README:361 still calls the file "pip export of the data group" | ⚠️ Warning (W-1) | Primary uv path unaffected (uv sync + lock complete and green; README install section routes via prerequisites, not pip). Recommended one-command fix: `uv export --group data --no-emit-project -o requirements.txt` (+ commit). Not a Phase-1 must-have failure — the artifact's contracted truths (exact pandas/numpy pins == lock, header, pip-compatible) still hold — but recorded here as required follow-up, not silently absorbed |
| baseline/compare.py | 55 | Stale docstring See-also naming the deleted script/get_task_performance.py | ℹ️ Info | Cosmetic; already recorded as Phase-4 deferred-items.md #1; no functional impact |
| (none) | - | TBD/FIXME/XXX debt markers | - | 0 across all implementation covered files (fresh grep, incl. the Phase-4-changed ones) |
| (none) | - | TODO/HACK/PLACEHOLDER/stub patterns | - | 0 in the changed covered files (fresh grep) |

### Decision Coverage

The `check.decision-coverage-verify` gate is non-blocking and its honoring detection does not resolve against a completed phase state (invocation semantics); the load-bearing decisions were instead verified directly on the current tree: D-05 floor pins + lock exactness (truth 4), D-06 stop-gate honored via the fresh migration gate (truth 21), D-07 `.python-version`=3.13, D-08 Zenodo link byte-identical (truth 5), D-09 holder retitle present, D-10 MIT intact. Phase-3/4 decisions superseding Phase-1 wordings are recorded in the Superseded-by-Design table with their deciding records.

### Human Verification Required

None. The four judgment-tier items from the original phase remain resolved with recorded maintainer confirmations in 01-UAT.md (status complete, 4/4 pass, 2026-10-09T00:38:08Z); that resolution is untouched, and this refresh produced no new behavior-unverified truth and no new judgment surface — every truth carries fresh behavioral evidence from this session or git-proven byte-identity with a prior behavioral pass. (Phase 4's own three human items — exporter concurrency, live visual spot-check, card provenance — belong to Phase 4's UAT, not this phase.)

### Gaps Summary

No blocking gaps. The stale fingerprint was caused by exactly 11 covered files modified/deleted by Phase 4 (git-proven against the prior-verification commit cce36c6); every changed surface was re-verified directly and every Phase-4-designed semantic shift is recorded as superseded-by-design with its invariant re-proven live: the retired pivot's determinism discipline now lives in `make data` (run twice, 0 dirty, twice), the species regroup's data changes are bounded by the fresh 52-pair gate to exactly the maintainer-approved corrections on top of the Phase-1 inventory, the widened dependency substrate still isolates GPU deps and resolves stably, the comparator's Phase-4 label additions leave the Phase-1 contract intact (re-executed), and the full-history secret scan is clean over 222 commits with the probe surfacing exactly the one intentional Zenodo link — itself byte-identical since data-v1 through two README rewrites. One Warning (W-1) is recorded for follow-up: requirements.txt is a stale export of the D-15-widened data group (pip path incomplete for the current chain; fix is a single uv export command); it does not fail any Phase-1 must-have — the artifact's contracted truths hold and the primary uv substrate is complete and green — but it should be re-exported before public release. Phase 1's goal — repo safe for public visibility, every future number change attributable — remains achieved at HEAD 015a0cf.

---

_Verified: 2026-10-10T07:24:56Z_
_Verifier: Claude (gsd-verifier)_
