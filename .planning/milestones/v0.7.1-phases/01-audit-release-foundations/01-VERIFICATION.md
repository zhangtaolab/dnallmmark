---
phase: 01-audit-release-foundations
verified: 2026-10-10T07:34:34Z
status: passed
score: 23/23 must-haves verified
covered_files: [".gitignore", ".gitleaks.toml", ".planning/phases/01-audit-release-foundations/01-01-PLAN.md", ".planning/phases/01-audit-release-foundations/01-01-SUMMARY.md", ".planning/phases/01-audit-release-foundations/01-02-PLAN.md", ".planning/phases/01-audit-release-foundations/01-02-SUMMARY.md", ".planning/phases/01-audit-release-foundations/01-03-PLAN.md", ".planning/phases/01-audit-release-foundations/01-03-SUMMARY.md", ".python-version", "AUDIT.md", "LICENSE", "Makefile", "README.md", "baseline/PIN-VALIDATION.md", "baseline/compare.py", "baseline/data-v1.sha256", "dnallm-mark/data/models_comparison.json", "dnallm-mark/data/models_comparison_animal.json", "dnallm-mark/data/models_comparison_microbe.json", "dnallm-mark/data/models_comparison_plant.json", "dnallm-mark/data/task_performance/BEND__CpG_methylation_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__C.elegans_4mC_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__D.melanogaster_4mC_task_performance.json", "dnallm-mark/data/task_performance/Deep4mC_datasets__E.coli_4mC_task_performance.json", "dnallm-mark/data/task_performance/GUE__EPI_GM12878_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K14ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K36me3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K4me1_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K79me3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3K9ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H3_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H4_task_performance.json", "dnallm-mark/data/task_performance/GUE__emp_H4ac_task_performance.json", "dnallm-mark/data/task_performance/GUE__fungi_species_20_task_performance.json", "dnallm-mark/data/task_performance/GUE__human_tf_0_task_performance.json", "dnallm-mark/data/task_performance/GUE__mouse_1_task_performance.json", "dnallm-mark/data/task_performance/GUE__mouse_4_task_performance.json", "dnallm-mark/data/task_performance/GUE__prom_300_all_task_performance.json", "dnallm-mark/data/task_performance/GUE__prom_core_all_task_performance.json", "dnallm-mark/data/task_performance/GUE__virus_covid_task_performance.json", "dnallm-mark/data/task_performance/GUE__virus_species_40_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__coding_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__human_vs_worm_task_performance.json", "dnallm-mark/data/task_performance/Genomic_Benchmarks__regulatory_region_type_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K27ac_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K27me3_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K4me2_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__H3K9me3_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__enhancers_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_acceptors_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_all_task_performance.json", "dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_donors_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K27ac_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K27me3_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K4me3_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-core-promoters_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-lncRNAs_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-open-chromatin_task_performance.json", "dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-sequence-conservation_task_performance.json", "dnallm-mark/data/task_performance/PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation_task_performance.json", "dnallm-mark/data/task_performance/PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation_task_performance.json", "dnallm-mark/data/task_performance/iDNA_ABF_datasets__5mC_task_performance.json", "dnallm-mark/data/task_performance/iDNA_ABF_datasets__6mA_task_performance.json", "dnallm-mark/data/task_performance/iPro-WAEL_datasets__Promoter_R_capsulatus_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__poly_a.arabidopsis_thaliana_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__promoter_strength.leaf_task_performance.json", "dnallm-mark/data/task_performance/plant-genomic-benchmark__terminator_strength.leaf_task_performance.json", "dnallm-mark/data/tasks.json", "pyproject.toml", "requirements.txt", "script/export_runs.py", "script/summarize_comparison.py", "scripts/generate-tasks-index.js", "uv.lock"]
covered_digest: "v3:sha256:c23f3a180dea1e8f6c63946908295c0a119a6dc6d6e4a36f38fe7d67a23a793b"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 23/23
  gaps_closed:
    - "STALE-REFRESH #3 (minimal delta): the prior pass (2026-10-10T07:24:56Z, passed 23/23 at 015a0cf) went stale because its W-1 remediation re-exported requirements.txt (commit 414ac9d, +975/-1) — requirements.txt is in the covered set, so the fingerprint invalidated by design. git diff 015a0cf..HEAD over the covered set shows exactly ONE changed implementation file: requirements.txt; the only other changes are three VERIFICATION.md planning docs (phases 01/02/03, inert, not covered inputs). This pass re-derived the named key evidence afresh at HEAD 73bd2b4 (tag manifest 52/52, make-data determinism x2, gitleaks production scan AND rules-only probe over the now-226-commit history, full substrate check on the NEW requirements.txt incl. export-currency) and carries every other truth on git-proven byte-identity with the prior pass, which ran those live at the same tree state."
    - "W-1 CLOSED by 414ac9d: committed requirements.txt is now the full 40-package D-15 data-group export — header names `uv export --group data --no-emit-project -o requirements.txt`, fresh export body byte-identical (only the header's output-path token differs, as expected), pandas==2.3.3/numpy==2.5.3/scipy==1.18.1/evaluate==0.4.6 all == lock resolutions, 954 --hash lines (pip --require-hashes shape), zero torch/transformers entries, README:361 'pip export of the data group' now accurate."
    - "Fresh fingerprint over the identical 74-file covered set: v3:sha256:c23f3a180d..."
  gaps_remaining: []
  regressions: []
---

# Phase 1: Audit & Release Foundations Verification Report (Stale-Refresh #3, post-W-1)

**Phase Goal:** The repo is safe for public visibility and every future number change is attributable — all three subsystems audited with evidence, the pre-fix state frozen, and the reproducibility substrate (license, pinned dependencies, deterministic generators) in place
**Verified:** 2026-10-10T07:34:34Z
**Status:** passed
**Re-verification:** Yes — STALE-REFRESH #3, minimal delta. The prior pass (2026-10-10T07:24:56Z, passed 23/23 at HEAD 015a0cf) had its fingerprint invalidated when its own recorded warning W-1 was remediated: requirements.txt was re-exported via `uv export --group data --no-emit-project -o requirements.txt` (commit 414ac9d), and requirements.txt is a covered input. This pass verifies the CURRENT tree at HEAD `73bd2b4`.

## Goal Achievement

### Evidence policy for this pass (stale-refresh #3, delta = one covered file)

- **The delta is git-proven minimal:** `git diff 015a0cf..HEAD` over the 74-file covered set shows exactly one changed implementation file — requirements.txt. The only other changes in the range are three VERIFICATION.md planning docs (phases 01/02/03), which are inert and not covered inputs.
- **Re-derived afresh this session (at HEAD 73bd2b4):** data-v1 tag extraction + 52/52 manifest checksums; `make data` determinism (run twice, 0 dirty files each); gitleaks production scan over the full history (now 226 commits) AND the rules-only no-suppression probe (exactly the one intentional finding); the complete dependency substrate on the CHANGED surface — `uv lock --check`, single numpy/pandas/scipy/evaluate resolutions, default-groups isolation, venv torch-absence, and the new requirements.txt (header command match, exact pins == lock, scipy+evaluate presence, pip `--require-hashes` shape, export-currency via fresh-export diff); gsd-tools artifact/key-link queries; ignore-negative link; LICENSE/README consistency.
- **Carried on byte-identity:** every other truth rests on a covered file that is git-proven byte-identical since 015a0cf, where the prior pass (minutes earlier, same tree state for those files) executed it live. The fresh covered_digest is the audit trail for that identity claim.

### Observable Truths

**Roadmap success criteria:**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Findings report covers pipeline, data scripts, frontend; every finding severity-graded with file:line evidence + recommended fix | ✓ VERIFIED (carried: AUDIT.md byte-identical since 015a0cf) | 24 `AUD-` rows, P0×2 → P1×12 → P2×10 ladder, all three subsystems, per-row file:line + fix + disposition — verified live by the prior pass on the identical bytes |
| 2 | Pre-fix state recoverable and diffable (data-v1 tag + golden baseline) before result-affecting fixes | ✓ VERIFIED (FRESH) | `git cat-file -t data-v1` = tag (423f5ce); tag tree extracted via `git archive` this session: **52/52 manifest checksums OK (LC_ALL=C), 0 failures**; manifest = 52 lines, 0 model_performance entries |
| 3 | Data-regeneration chain run twice from a clean state produces byte-identical derived JSON | ✓ VERIFIED (FRESH) | `make data` (= summarize_comparison.py + generate-tasks-index.js, Makefile `data:` target) run TWICE this session at HEAD: both exit 0, `git status --porcelain dnallm-mark/data/` = **0 dirty files after each run** |
| 4 | Fresh contributor installs CPU-only data chain from pinned manifests (pandas>=2.2,<3.0); GPU group never in default install | ✓ VERIFIED (FRESH, on the changed substrate incl. the new requirements.txt) | pyproject: `pandas>=2.2,<3.0` floor intact, `default-groups = ["data"]`, GPU deps in `[gpu]` behind the explicit cu130 index; `uv lock --check` exit 0 (88 packages); single resolutions numpy 2.5.3 / pandas 2.3.3 / scipy 1.18.1 / evaluate 0.4.6; venv check: pandas 2.3.3 / numpy 2.5.3 / scipy 1.18.1 present, `find_spec('torch') is None`; **requirements.txt now the full 40-package export with exact pins == lock and zero torch/transformers entries — the pip path is no longer stale (W-1 closed)** |
| 5 | Repo publishable: LICENSE + separate data terms; secret-hygiene decision applied (Zenodo link stays, full-history scan confirms no other secrets) | ✓ VERIFIED (scan FRESH over 226 commits; LICENSE/README carried byte-identical) | LICENSE: MIT, holder "zhangtaolab and DNALLM-Mark contributors" (D-09); README badge line 3 + License section: MIT code + CC BY 4.0 derived aggregates + upstream not-redistributed disclaimer; Zenodo record-19135551 link unchanged (README byte-identical in range); **gitleaks 8.30.1 production scan re-run live: 226 commits (--all), "no leaks found"** |

**Plan-specific truths (01-01 / 01-02 / 01-03):**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 6 | Comparator buckets float diffs at rel 1e-12 into FLOAT_ULP vs FLOAT_BIG; exit 0 only when no diffs | ✓ VERIFIED (carried: compare.py byte-identical; prior pass executed the full exit contract 0/1/2/2 live) | Phase-4 D-13 additive INT/BOOL_CROSS labels; formula/threshold untouched (compare.py:124-128) |
| 7 | --summary-json emits complete untruncated inventory (len(diffs) == total == sum(counts)) | ✓ VERIFIED (carried) | Prior pass asserted reconciliation on self-pair, 45-diff pair, and all 52 migration-gate summaries on these exact bytes |
| 8 | Manifest covers exactly the 52 derived files, none of the 42 inputs | ✓ VERIFIED (FRESH) | 52 lines, 0 model_performance entries, 52/52 OK vs extracted tag tree |
| 9 | Fresh uv sync installs only the data group | ✓ VERIFIED (FRESH) | default-groups=["data"]; data-group venv carries pandas/numpy/scipy, torch absent |
| 10 | uv.lock holds a single numpy resolution across all groups | ✓ VERIFIED (FRESH) | Exactly one block each: numpy 2.5.3, pandas 2.3.3, scipy 1.18.1, evaluate 0.4.6 — versions match requirements.txt pins exactly |
| 11 | Empty dev group keeps resolution working | ✓ VERIFIED (wording SUPERSEDED by design — carried forward) | dev = [jsonschema, pytest, ruff, ty] since Phases 2/3; invariant re-proven live: `uv lock --check` exit 0 |
| 12 | Re-running uv lock produces no change | ✓ VERIFIED (FRESH) | `uv lock --check` exit 0, "Resolved 88 packages in 0.61ms" |
| 13 | Pin validation ran on pre-fix generators; only the root-caused inventory observed (backstop) | ✓ VERIFIED (carried: PIN-VALIDATION.md byte-identical) | 5 FLOAT_ULP refs, D-06 conclusion; bounding claim re-confirmed by the prior pass's fresh 52-pair gate on identical inputs |
| 14 | Same-root-cause findings merged into single rows citing every site | ✓ VERIFIED (carried) | AUDIT.md AUD-10/12/14 multi-site single rows stand |
| 15 | Zero-findings subsystem would be explicitly reported | ✓ VERIFIED (carried) | Vacuous — all three subsystems carry findings; contract in the unchanged methodology section |
| 16 | Findings table ordered P0→P1→P2, then subsystem, then AUD-nn | ✓ VERIFIED (carried) | Prior pass's fresh awk scan on the identical bytes: P0 P0 → P1×12 → P2×10 contiguous |
| 17 | Maintainability findings in separate non-graded list (D-04) | ✓ VERIFIED (carried) | "## Maintainability findings (non-graded, D-04)" present |
| 18 | Report pre-documents expected post-fix migration inventory | ✓ VERIFIED (carried) | "Expected post-fix migration inventory" + "Post-fix migration record" sections present; re-confirmed empirically by the prior pass's 52-pair gate on identical inputs |
| 19 | Partial review-agent run detected at merge time (backstop) | ✓ VERIFIED (carried) | Process truth; 24 rows traceable; machinery untouched |
| 20 | Exact-tie pairs resolve to deterministic alphabetical order | ✓ VERIFIED (carried; reinforced FRESH) | All 4 comparison files byte-identical since the prior pass's full tie-group scan (every exact rank_score tie alphabetical); this session's `make data` ×2 no-op re-proves the chain reproduces exactly those bytes |
| 21 | One-time migration diff vs data-v1 contains only the documented inventory | ✓ VERIFIED (carried on immutable inputs) | The gate's two sides are fixed: the data-v1 tag tree (immutable object, re-verified 52/52 this session) and the HEAD data files (byte-identical since the prior pass ran the full 52-pair gate: 45 IDENTICAL + 2 species-corrected task files + ULP/tie-swap/re-aggregation classes, zero out-of-set). Nothing that feeds the gate changed in this delta |
| 22 | Full-history scan clean + no-allowlist probe surfaces exactly the one known finding | ✓ VERIFIED (BOTH HALVES FRESH, 226 commits) | Production (committed config, --all): 226 commits, "no leaks found". Probe (rules-only config — detection rule retained, allowlist stripped — full history): exactly **1 finding: README.md, RuleID zenodo-preview-token, commit 09fb0ae, the intentional record-19135551 link**; no other secret anywhere in history, including the 4 commits added since the prior pass |
| 23 | Generators' empty-input behavior unchanged by the fix (backstop) | ✓ VERIFIED (superseded in part by record, carried) | Pivot retired Phase 4 (OQ6, IN-03) with assertions folded into tests/test_export_runs.py; surviving generators exercised by the Phase-2+ harness and this session's `make data` ×2 no-op |

**Score:** 23/23 truths verified (0 present-but-behavior-unverified; 0 overrides; each truth carries either fresh behavioral evidence from this session or git-proven byte-identity with the prior pass's live evidence at the same tree state — the covered_digest seals that identity claim)

### Superseded by Design (Phase-4 semantic shifts — carried forward from the prior pass; all deciding records unchanged)

Phase 4 deliberately changed the meaning of several Phase-1 wordings. Each supersession cites the deciding Phase-4 record; the underlying invariants were re-proven live (this session or the byte-identical prior pass).

| Phase-1 wording | Current reality | Deciding record | Invariant re-verified |
|---|---|---|---|
| Data chain = summarize_comparison.py + **get_task_performance.py** + generate-tasks-index.js | Pivot script DELETED; chain is `make data` = summarize + generate-tasks-index (task_performance files are committed static data until E2' regenerates them via export_runs.py) | Phase-4 OQ6/D-decisions, IN-03 (04-05); README documents the honest static-data status | Run-twice byte-identity re-proven FRESH this session: `make data` ×2, 0 dirty files (truth 3) |
| Comparator diff vocabulary = 8 classes incl. FLOAT_BIG for int rank pairs | Vocabulary widened with INT and BOOL_CROSS labels; formula/threshold/exit contract untouched | Phase-4 D-13, IN-01, WR-02 (b34f43e/a0d254d) | Exit contract + summary-json reconciliation executed live by the prior pass on identical bytes (truths 6, 7) |
| `[data]` group = pandas + numpy floors | Group widened: scipy>=1.15.2 + evaluate>=0.4.6 (D-15) — scipy is a module-level import of the chain via export_runs | Phase-4 D-15 maintainer Option C (0189d4c) | Lock stability + single resolutions + default-groups isolation + torch-absent venv all FRESH this session (truths 4, 9-12); **the D-15 export-currency drift is now CLOSED — requirements.txt is the current full export (414ac9d)** |
| Derived data tree = post-migration state gated at Phase 1 | animal/microbe re-aggregated + 2 task-file species values + tasks.json 2 entries changed by the species-grouping fix | Phase-4 FIX-02/AUD-01 (6bb9364), maintainer-approved 50-row Category review (04-CATEGORY-REVIEW.md), OQ4 (aa27ea3) | Prior pass's 52-pair gate on identical inputs bounds all diffs to Phase-1 inventory + exactly these documented corrections (truth 21); `make data` no-op re-proven FRESH |
| Tie-pair population = the 4 Phase-1 pairs | Population changed with the regroup (microbe 448.0 pair subsumed; new ties in animal/microbe) | Same FIX-02 record | Every exact tie alphabetical (prior pass, identical bytes); byte-reproduction re-proven FRESH |
| README data-chain section named the 3-script chain | README rewritten by Phase 4: exporter section added, pivot instructions removed, `make data` chain documented | Phase-4 04-05 README docs (2a26a66) | License section, badge, disclaimer, Zenodo link all survive (truth 5; README byte-identical in this delta, consistency re-checked live) |
| (Carried forward) pipeline deprecation, [pipeline]→[gpu] rename, dev-group tooling, README line drift | Stand as recorded at the prior refresh | Phase-3 REV-10 / D-05 / maintainer ty directive / af12068 | Invariants re-proven here: lock isolation, resolution stability, link byte-identity |

### Prohibition Disposition (ADR-550 D4 — judgment tier, human-resolved at the Phase-1 UAT; no new judgment surface)

All six prohibitions were confirmed by the maintainer in 01-UAT.md test 4 (2026-10-09, pass) — that resolution stands. Nothing in this one-file delta produced a new judgment surface; the secret-hygiene prohibitions were additionally re-proven live over the enlarged 226-commit history (both scan directions).

| Prohibition | Maintainer | Fresh/Carried verifier evidence |
|-------------|-----------|---------------------------------|
| AUDIT-01: no unreproducible graded findings | Confirmed (UAT 4) | AUDIT.md byte-identical; Unverified-observations section carries the demotion list |
| AUDIT-01: no secret material in AUDIT.md | Confirmed (UAT 4) | AUDIT.md byte-identical; prior pass's sweep (zenodo.org/records=0, eyJ=0, token==0) on identical bytes |
| FIX-05: no value changes beyond inventory | Confirmed (UAT 4) | Prior pass's full-strength 52-pair gate on immutable inputs (truth 21) |
| REL-01: no license claims over upstream data | Confirmed (UAT 4) | README License section re-read live: upstream "not redistributed ... remain under their original terms"; CC BY covers only repo-produced aggregates |
| REL-05: allowlist not widened | Confirmed (UAT 4) | .gitleaks.toml byte-identical since d14c9bd: exactly one rule-scoped AND allowlist, anchored `^README\.md$` + record-19135551 regex; production scan clean over 226 commits (FRESH) |
| REL-05: no secret values in committed evidence | Confirmed (UAT 4) | AUDIT.md location-only references; .gitleaks.toml carries regex patterns, not values; requirements.txt hashes are package integrity hashes, not credentials |

### Required Artifacts

gsd-tools `verify.artifacts` re-run this session: **7/7 (01-01), 1/1 (01-02), 4/4 (01-03) — 12/12 passed**.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `baseline/compare.py` | Comparator, exit contract, --summary-json | ✓ VERIFIED (carried, byte-identical; prior live exec) | Phase-4 D-13 additive labels only; exit contract executed live by prior pass |
| `baseline/data-v1.sha256` | 52-entry manifest | ✓ VERIFIED (FRESH) | 52 lines; 52/52 OK vs extracted tag tree this session |
| `baseline/PIN-VALIDATION.md` | Pin-validation evidence | ✓ VERIFIED (carried) | Present, byte-identical, 5 FLOAT_ULP refs, D-06 conclusion |
| `pyproject.toml` | PEP 621 + groups | ✓ VERIFIED (re-read) | data/dev/gpu groups; default-groups=["data"]; pandas floor intact; D-15 scipy/evaluate in [data] |
| `uv.lock` | Exact-resolution lockfile | ✓ VERIFIED (FRESH) | 88 packages; single numpy/pandas/scipy/evaluate; `uv lock --check` exit 0 |
| `requirements.txt` | Exact pins, current export | ✓ VERIFIED (FRESH — W-1 closed) | 40 packages; header names the export command verbatim; pandas==2.3.3, numpy==2.5.3, scipy==1.18.1, evaluate==0.4.6 == lock; fresh `uv export --group data --no-emit-project` body byte-identical; pip `--require-hashes` shape (954 hash lines); no GPU deps |
| `.python-version` | 3.13 pin | ✓ VERIFIED (FRESH) | `git check-ignore .python-version` exit 1 (tracked, not ignored) |
| `AUDIT.md` | Public findings report | ✓ VERIFIED (carried) | Byte-identical; 24 findings; ladder verified live by prior pass |
| `LICENSE` | MIT text | ✓ VERIFIED (re-read) | Canonical MIT; holder "zhangtaolab and DNALLM-Mark contributors" per D-09 |
| `.gitleaks.toml` | Default rules + narrow AND allowlist | ✓ VERIFIED (FRESH scans) | Byte-identical config; both scan directions re-run live over 226 commits |
| `script/summarize_comparison.py` | sorted + sort_keys | ✓ VERIFIED (FRESH execution) | Re-executed twice green via `make data` on the current tree |
| `scripts/generate-tasks-index.js` | No live-clock stamp | ✓ VERIFIED (FRESH execution) | Re-executed twice green via `make data`; no `new Date` |

### Key Link Verification

gsd-tools `verify.key-links`: 4/10 pattern-verified across the three plans; the negatives are the same non-file/negative/conceptual links the pattern matcher cannot express (a git tag as source, a REMOVED ignore line, a code-construct source, a config-to-scan-process link). Every link was behaviorally proven live this session or rests on byte-identity with the prior pass's live proof:

| From | To | Via | Status | Fresh evidence |
|------|----|----|--------|----------------|
| pyproject.toml | uv.lock | floor bounds → exact pins | ✓ WIRED (pattern + live) | pandas floor → pandas 2.3.3 in lock; `uv lock --check` exit 0 (FRESH) |
| uv.lock | requirements.txt | uv export of data group | ✓ WIRED (pattern + live, currency RESTORED) | fresh export body byte-identical to committed file (FRESH — the W-1 drift is gone) |
| .gitignore | uv.lock | ignore line REMOVED (negative link) | ✓ WIRED (behavioral) | `git check-ignore uv.lock .python-version` exit 1 (FRESH) |
| git tag data-v1 | baseline/data-v1.sha256 | recover-and-checksum | ✓ WIRED (behavioral) | 52/52 OK from extracted tag tree (FRESH) |
| sorted(os.listdir) in the generators | byte-identical outputs | pinned iteration + sort_keys | ✓ WIRED (behavioral) | `make data` ×2 at HEAD: 0 dirty files (FRESH) |
| .gitleaks.toml allowlist | full-history scan | AND-condition suppression | ✓ WIRED (behavioral) | Production 226-commit scan clean; rules-only probe surfaces exactly the one intentional finding (BOTH FRESH) |
| LICENSE | README badge + License section | consistency | ✓ WIRED (pattern + live) | Badge line 3 MIT; License section consistent (FRESH read) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| dnallm-mark/data/ (52 derived files) | all values | 42 model_performance inputs via the current chain (+ registry Category join since Phase 4) | Yes — `make data` ×2 reproduces the committed tree byte-for-byte (0 dirty), FRESH this session | ✓ FLOWING |
| requirements.txt | 40 package pins + 954 hashes | uv.lock via `uv export --group data` | Yes — fresh export byte-identical (FRESH this session) | ✓ FLOWING |
| AUDIT.md findings | reproduction evidence | actual code + committed JSONs | Yes — byte-identical; anchors the later-phase locks | ✓ FLOWING |

### Behavioral Spot-Checks (this session, all fresh at HEAD 73bd2b4)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Tag recoverability + manifest integrity | `git archive data-v1` + `LC_ALL=C sha256sum -c` | 52/52 OK, 0 failures | ✓ PASS |
| Manifest shape | line count + model_performance grep | 52 lines, 0 input entries | ✓ PASS |
| Determinism (current chain, run-twice) | `make data` ×2 + porcelain check | both runs exit 0, 0 dirty files | ✓ PASS |
| Lock stability | `uv lock --check` | exit 0, 88 packages | ✓ PASS |
| Single resolutions | grep uv.lock blocks | numpy 2.5.3 / pandas 2.3.3 / scipy 1.18.1 / evaluate 0.4.6, one block each | ✓ PASS |
| requirements.txt export currency (W-1 closure) | fresh `uv export --group data --no-emit-project` vs committed body | byte-identical (only header output-path token differs, as expected) | ✓ PASS |
| requirements.txt pip shape | header + pins + hash coverage + GPU-leak grep | header command matches; 40 pkgs; 954 `--hash=sha256:` lines; 0 torch/transformers | ✓ PASS |
| venv isolation | find_spec + imports under `uv run --group data` | torch None; pandas 2.3.3 / numpy 2.5.3 / scipy 1.18.1 | ✓ PASS |
| gitleaks production scan | `gitleaks git --config .gitleaks.toml --log-opts=--all .` | 226 commits, no leaks found, exit 0 | ✓ PASS |
| gitleaks probe (no suppression) | `gitleaks git --config <rules-only> --log-opts=--all .` | exactly 1 finding: README.md zenodo-preview-token @09fb0ae | ✓ PASS |
| MIT body + holder | LICENSE read | MIT, one holder line, "zhangtaolab and DNALLM-Mark contributors" | ✓ PASS |
| Ignore-negative link | `git check-ignore uv.lock .python-version` | exit 1 — both tracked, not ignored | ✓ PASS |
| Covered-set existence | stat all 68 implementation covered files | 0 missing | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes exist or are declared by this phase. The gitleaks two-scan proof (truth 22) was executed directly by the verifier in its own process this session (both directions, table above); the make-data determinism gates likewise ran in-process.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| AUDIT-01 | 01-02 | Severity-graded findings report, all three subsystems | ✓ SATISFIED | AUDIT.md byte-identical, prior live verification (truths 1, 14-18) |
| AUDIT-02 | 01-01 | Pre-fix baseline (golden outputs + data-v1 tag) before fixes | ✓ SATISFIED | Tag + 52-entry manifest; 52/52 recoverability FRESH (truths 2, 8) |
| REL-01 | 01-03 | LICENSE present, data licensing declared separately | ✓ SATISFIED | MIT LICENSE + README CC BY 4.0 + upstream disclaimer re-read live (truth 5) |
| REL-02 | 01-01 | Pinned offline/data-chain manifests; GPU deps isolated from CI | ✓ SATISFIED | Groups + uv.lock (88 pkgs) + requirements.txt (now CURRENT export) + .python-version; default-groups=["data"]; [gpu] never installed (truths 4, 9-12) |
| REL-05 | 01-03 | Secret hygiene settled; full-history scan confirms no other secrets | ✓ SATISFIED | Live 226-commit production scan clean + rules-only probe exactly-one-finding, both FRESH (truth 22) |
| FIX-05 | 01-03 | Deterministic generators (sorted + sort_keys) | ✓ SATISFIED | Run-twice byte-identity FRESH at HEAD (truths 3, 20, 23) |

Orphaned requirements: none — REQUIREMENTS.md maps exactly AUDIT-01, AUDIT-02, REL-01, REL-02, REL-05, FIX-05 to Phase 1 (all Complete), matching the plan frontmatter union.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| ~~requirements.txt~~ | ~~whole file~~ | ~~Stale uv export (prior W-1)~~ | ✅ CLOSED by 414ac9d | The file is now the full 40-package D-15 data-group export; fresh export byte-identical; README:361 claim accurate; pip path complete for the current chain (scipy present). Verified fresh this session — no follow-up remains |
| baseline/compare.py | 55 | Stale docstring See-also naming the deleted script/get_task_performance.py | ℹ️ Info | Cosmetic; carried (byte-identical file); recorded as Phase-4 deferred-items.md #1; no functional impact |
| (none) | - | TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER debt markers | - | 0 in requirements.txt (the only changed covered file; fresh grep) |

### Decision Coverage

Carried from the prior pass (no decision-relevant file changed except requirements.txt, whose change EXECUTES the prior pass's W-1 recommendation): D-05 floor pins + lock exactness re-proven FRESH (truth 4), D-06 stop-gate honored via the immutable-inputs migration gate (truth 21), D-07 `.python-version`=3.13 (tracked, FRESH check), D-08 Zenodo link byte-identical (README unchanged in range; probe re-confirms the link is the sole intentional finding), D-09 holder retitle present, D-10 MIT intact. Phase-3/4 decisions superseding Phase-1 wordings are recorded in the Superseded-by-Design table with their deciding records.

### Human Verification Required

None. The four judgment-tier items from the original phase remain resolved with recorded maintainer confirmations in 01-UAT.md (status complete, 4/4 pass, 2026-10-09); that resolution is untouched. This one-file delta produced no new behavior-unverified truth and no new judgment surface — every truth carries fresh behavioral evidence from this session or git-proven byte-identity with the prior pass, which ran the remaining evidence live at the same tree state. (Phase 4's own three human items belong to Phase 4's UAT, not this phase.)

### Gaps Summary

No gaps. This stale-refresh was triggered by exactly one covered-input change — the requirements.txt re-export (414ac9d) that remediated the prior pass's sole Warning (W-1) and thereby invalidated the fingerprint by design. The fix itself was verified at full depth this session: the committed file is now the current, complete 40-package export of the D-15-widened data group (header command verbatim, exact pandas/numpy/scipy/evaluate pins == lock, full hash coverage, pip `--require-hashes` shape, no GPU leakage, README claim accurate, fresh-export byte-identity). The named key evidence was re-derived afresh at HEAD 73bd2b4 — data-v1 tag manifest 52/52, `make data` determinism no-op twice, gitleaks production scan AND rules-only probe over the enlarged 226-commit history (exactly the one intentional Zenodo finding) — and every other truth rests on git-proven byte-identity with the prior pass's live evidence, sealed by the fresh covered_digest (v3:sha256:c23f3a18..., identical 74-file covered set). The sole prior Warning is closed with nothing replacing it; the one carried Info item (compare.py:55 stale See-also) remains recorded as Phase-4 deferred-items #1. Phase 1's goal — repo safe for public visibility, every future number change attributable — remains achieved at HEAD 73bd2b4.

---

_Verified: 2026-10-10T07:34:34Z_
_Verifier: Claude (gsd-verifier)_
