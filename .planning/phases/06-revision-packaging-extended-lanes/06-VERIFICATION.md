---
phase: 06-revision-packaging-extended-lanes
verified: 2026-10-11T01:35:29Z
status: gaps_found
score: 6/7 must-haves verified
covered_files: [".gitignore", ".planning/phases/06-revision-packaging-extended-lanes/06-01-PLAN.md", ".planning/phases/06-revision-packaging-extended-lanes/06-01-SUMMARY.md", ".planning/phases/06-revision-packaging-extended-lanes/06-02-PLAN.md", ".planning/phases/06-revision-packaging-extended-lanes/06-02-SUMMARY.md", ".planning/phases/06-revision-packaging-extended-lanes/06-03-PLAN.md", ".planning/phases/06-revision-packaging-extended-lanes/06-03-SUMMARY.md", ".planning/phases/06-revision-packaging-extended-lanes/06-04-PLAN.md", ".planning/phases/06-revision-packaging-extended-lanes/06-04-SUMMARY.md", ".planning/phases/06-revision-packaging-extended-lanes/06-05-PLAN.md", ".planning/phases/06-revision-packaging-extended-lanes/06-05-SUMMARY.md", "DATA.md", "Makefile", "README.md", "baseline/snapshots/snapshot-991804613c4874bfa3f32d318340b5d7b4118ffe.sha256", "dnallm-mark/data/provenance.csv", "dnallm-mark/data/provenance.json", "dnallm-mark/js/config.js", "dnallm-mark/js/data.js", "docs/METHODOLOGY.md", "docs/ONBOARDING.md", "docs/TUI-REQUIREMENTS.md", "pipeline/datasets_info.json", "pipeline/env_smoke.py", "pipeline/finetune_config.yaml", "pipeline/finetune_config_curve.yaml", "pipeline/finetune_config_probe.yaml", "pipeline/finetune_config_with_head.yaml", "pipeline/run_finetune.py", "pipeline/run_sweep.py", "schemas/frontier.json", "schemas/provenance.json", "schemas/vep_zero_shot.json", "script/build_frontier.py", "script/build_provenance.py", "script/convert_registry.py", "script/doi_swap.py", "script/export_runs.py", "script/freeze_snapshot.py", "script/zero_shot_vep.py", "tests/fixtures/frontier/frontier_sample.json", "tests/fixtures/vep_zero_shot/cohort.vcf", "tests/fixtures/vep_zero_shot/expected_stub_rows.json", "tests/fixtures/vep_zero_shot/reference.json", "tests/js/data-api.test.js", "tests/js/main-view-toggle.test.js", "tests/test_build_provenance.py", "tests/test_convert_registry.py", "tests/test_doi_swap.py", "tests/test_export_runs.py", "tests/test_frontier.py", "tests/test_run_finetune_contracts.py", "tests/test_schemas.py", "tests/test_sweep.py", "tests/test_zero_shot_vep.py"]
covered_digest: "v3:sha256:83fb8936936ddf8b18563644cb12000750fb978bda6be9b525f6e56ec4944f81"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "A results snapshot (tar + SHA-256 manifest + frozen commit hash) supports SI/Zenodo deposition and can be re-verified from its manifest (SC-3, REV-03 tail)"
    status: partial
    reason: >-
      The committed tamper-evidence manifest no longer verifies against the
      working tree at HEAD: the maintainer-directed in-window provenance fill
      (47d057f, 'fill ModelScope download URLs') changed
      dnallm-mark/data/provenance.csv and provenance.json — both inside the
      frozen SNAPSHOT_FILES set — without re-running the README's documented
      re-freeze procedure (make data -> drift-clean -> make snapshot -> commit
      the refreshed .sha256). The README's own re-verification one-liner
      (README.md:219, 'cd baseline/snapshots && sha256sum -c
      snapshot-*.sha256  # re-verify: every line OK') now exits 1 with 2 of 58
      mismatched lines. The deposition artifact itself is NOT corrupt: all 58
      tar members match the committed manifest byte-for-byte (verified
      independently), and the pre-fill provenance content is preserved inside
      the tar. The gap is between the committed .sha256 and the live tree.
    artifacts:
      - path: "baseline/snapshots/snapshot-991804613c4874bfa3f32d318340b5d7b4118ffe.sha256"
        issue: "manifest hashes for dnallm-mark/data/provenance.{csv,json} pin the pre-47d057f state; live tree differs (2/58 lines fail sha256sum -c)"
    missing:
      - "Re-run the documented re-freeze procedure after the 47d057f provenance fill: make data (verify porcelain empty), make snapshot, commit the refreshed snapshot-991804613c4874bfa3f32d318340b5d7b4118ffe.sha256 — OR, if the maintainer intends the snapshot to stay pinned at the pre-fill 9918046 state until data-v2, document that scoping in the README snapshot section (the one-liner is valid at the frozen commit / against the extracted tar) via an override"
---

# Phase 6: Revision Packaging & Extended Lanes — Verification Report

**Phase Goal:** External reviewers can understand, trust, reproduce, and extend the platform — provenance, methodology docs, validated onboarding, result snapshots for SI/Zenodo — with the revision-window extension lanes (PEFT, zero-shot VEP, learning curves) delivered as far as the window allows and the remainder explicitly deferred to the response letter
**Verified:** 2026-10-11T01:35:29Z
**Status:** gaps_found
**Re-verification:** No — initial verification
**Covered set:** commits `83bdbaf..HEAD` (HEAD `47d057f`; 50 commits — 32 execution + review + 14 review-fix + records + 2 maintainer-directed in-window additions), fingerprinted above

## Goal Achievement

### Observable Truths (per ROADMAP Success Criteria)

| # | Truth (SC) | Status | Evidence |
|---|------------|--------|----------|
| 1 | SC-1: Reviewer can reproduce the leaderboard from a fresh clone using literal copy-pasteable README commands (install → data → aggregate → serve) | ✓ VERIFIED | `README.md:113-209` — "Reproducing the Leaderboard" section: literal blocks `uv sync` / `make data` + drift porcelain check / `make test` (both lanes) / `bash start-server.sh`, expected output per step, fresh-clone CI-replay proof (:201-209), links to METHODOLOGY + ONBOARDING. Drift gate re-run by verifier: `make data` exit 0, `git status --porcelain` EMPTY (byte-stable no-op holds at HEAD) |
| 2 | SC-2: Each dataset has a provenance row in DATA.md (source, citation, license, preprocessing, ModelScope-default URL + alternates); downloadable manifest (CSV/JSON) with full metadata and direct links | ✓ VERIFIED | Registry `pipeline/datasets_info.json`: 50 entries, **0 blank cells** across the six provenance columns; `Unspecified` = license 35 / citation 7 / **download_url 0** (50/50 filled — the in-window 47d057f advancement, verified independently). ModelScope org split: zhangtaolab 9 + lgq12697 34 + forrestzhang 7 = 50; primary 18 / alternates-only 32; zero Unspecified-primary. Committed `dnallm-mark/data/provenance.{json,csv}` (50 rows, 7 keys, schema `schemas/provenance.json` with minLength:1); DATA.md appendix under GENERATED PROVENANCE markers (:110-192) with correction path; maintainer review recorded in `c59f5f8` ("reviewed 接受现状"); drift-gated via `make data` (no-op at HEAD). Note: the DATA.md human table renders Dataset/Source/License/Citation with preprocessing as a uniform block + download-policy paragraph; per-row download URLs live in the linked CSV/JSON manifest — the manifest is the SC's direct-links carrier |
| 3 | SC-3: Results snapshot (tar + SHA-256 manifest + frozen commit hash) supports SI/Zenodo deposition and re-verifies from its manifest | ✗ FAILED | `baseline/snapshots/snapshot-9918046...sha256` committed, `.tar` gitignored (on disk), manifest paths relative to baseline/snapshots, frozen hash 9918046 read from manifest.json `generated_from` (hermetic). **All 58 tar members match the committed manifest** (deposition artifact internally consistent — verifier-recomputed). BUT the README's documented re-verification (`cd baseline/snapshots && sha256sum -c snapshot-*.sha256`, README.md:219) **exits 1: 2/58 lines differ** — `dnallm-mark/data/provenance.csv` + `.json` were changed by in-window 47d057f (inside SNAPSHOT_FILES) without the documented re-freeze (README.md:228-236). See Gaps Summary |
| 4 | SC-4: Four aggregation methods (+F6 dual views) documented in ONE place; `js/data.js:recalculateComparison()` dead logic gone | ✓ VERIFIED | `docs/METHODOLOGY.md` (156 lines): "Per-task normalization (four methods)" (:31 — rank/MinMax/z-score/robust with formulas), "The dual views (F6): rank vs weighted" (:67), CI semantics (:84), CI-overlap tie rule (:97), permutation family (:113), "Where the code lives" (:141). `grep -rn recalculateComparison dnallm-mark/` → one past-tense lesson comment only (`js/config.js:38` "since removed — DATA-07"); function + all call sites deleted in dedicated first commit `a9e3dd6`; node suite pins absence (`tests/js/data-api.test.js`) — 18/18 green |
| 5 | SC-5: Maintainer can onboard a new model/dataset end-to-end via the documented process (mechanism validated, no GPU runs) | ✓ VERIFIED | `docs/ONBOARDING.md` (217 lines): new-model checklist (6 steps, :9-92) and new-dataset checklist (7 steps incl. provenance ingestion, :94-209); every step CPU/dry-run (`convert_registry` round-trip, `run_sweep --dry-run`, `make data`); LOW-01 r2 enum fix landed (`5020553`); underlying commands all exist and are test-covered (converter 21 tests, sweep 59 incl. dry-run family) |
| 6 | SC-6: Revision-window lanes in priority order — LoRA/IA³/frozen probes + cost-accuracy frontier table; zero-shot VEP with CLM/MLM scoring + sanity; learning curves; remainder deferred with mechanism documented | ✓ VERIFIED | LoRA/IA³: `--peft {none,lora,ia3}` + `lora:`/`ia3:` YAML sections in BOTH configs + `use_lora` ctor kwarg (`run_finetune.py`, 3872fea); adapter aliases `+lora/+ia3` + `--num_train_epochs` + trainable-params persistence into final_metrics (6748b92, 8c8e55c); `run_sweep --peft` alias cells + LIST argv + record field (c5cad04); frontier machinery `script/build_frontier.py` + `schemas/frontier.json` + generator-produced fixture (8722012) — publication gate held (`dnallm-mark/data/frontier.json` ABSENT). VEP: `script/zero_shot_vep.py` (62-row type-driven enumeration, lazy suite-kernel seam, synonym/nonsense sanity, CLM-only RC control, dual emission) + `schemas/vep_zero_shot.json` + fixtures (ff922c5, 5271675). Frozen probes: `--config-variant {head,probe,curve}` + `finetune_config_probe.yaml` (head "mlp", **frozen: true**, hidden_dims [512] — verified) + `PROBE_INELIGIBLE` (9 entries incl. **both `SPACE` and `space`** — HI-01, d894de4) + argv guard (006c912). Curves: `--train_fraction` (train-only, seed-governed, frac-under-seed nesting, fraction-scaled cadence) + `run_sweep --curve` 4-tuple expansion + `finetune_config_curve.yaml` + `extract_curve_points` (66c1846, 6014e3c, 7d850a5). GPU smokes re-verified from disk: LoRA pct **0.331253**, probe pct **0.441759** (both in (0,5]); VEP honest-FAIL verdicts recorded. IA³ execution + real lane runs remain maintainer-gated post-E2' (ROADMAP's own deferral design) |
| 7 | SC-7: Zenodo preview-token link replaced with published DOI once record 19135551 is public, .gitleaks.toml updated in the same commit — prepared, not executed | ✓ VERIFIED | `script/doi_swap.py` (2d16f13): 404-refusal naming record + `--force` escape, both-files-or-neither in one run, `--dry-run`, WR-01 same-commit rule in docstring; 11 tests green. README tokenized link **INTACT** (`preview=1&token=` count = 1); `.gitleaks.toml` record-19135551 allowlist intact; swap provably NOT executed |

**Score:** 6/7 truths verified (1 failed — SC-3 live-tree re-verification)

### Gates (run independently by the verifier)

| Gate | Command | Result | Status |
|------|---------|--------|--------|
| Full suite | `make test` | pytest **451 passed** in 10.03s; node lane **18/18 pass, 0 fail** | ✓ PASS |
| Lint | `make lint` | All checks passed (ruff over tests/ + fixed-findings list + 4 existence-guarded phase-6 scripts) | ✓ PASS |
| Type-check | `make typecheck` | All checks passed (ty) | ✓ PASS |
| Drift | `make data` + `git status --porcelain` | exit 0; porcelain EMPTY — byte-stable no-op at HEAD incl. the 47d057f provenance state | ✓ PASS |
| Node lane | `node --test tests/js/` (inside make test) | 18 tests, 18 pass, 0 fail | ✓ PASS |
| Snapshot re-verify | `cd baseline/snapshots && sha256sum -c snapshot-*.sha256` | **exit 1 — 2/58 mismatch (provenance.csv, provenance.json)** | ✗ FAIL |
| Tar-vs-manifest | verifier-computed over all 58 tar members | 58/58 match | ✓ PASS (deposition artifact consistent) |

### Behavioral Spot-Checks

| Behavior | Evidence | Status |
|----------|----------|--------|
| LoRA smoke persistence | `pipeline/finetuned/plant-dnabert-6mer+lora/.../final_metrics.json` on disk: trainable_params 296450 / total 89493508 / pct **0.331253** in (0,5] | ✓ PASS |
| Probe smoke frozen backbone | `plant-dnabert-6mer+probe/.../final_metrics.json`: 395778 / 89591298 / pct **0.441759** in (0,5] | ✓ PASS |
| MED-04 probe×peft refusal | `run_finetune.py:749-757` sys.exit; `test_probe_peft_composition_refused_at_argv_boundary` in green suite | ✓ PASS |
| HI-01 SPACE closure | `PROBE_INELIGIBLE` (run_finetune.py:504) lists `SPACE` and `space` with per-line provenance; registry-derived pin test green | ✓ PASS |
| MED-01 base_model in failures | `run_sweep.py:129-144,685-739`; `test_peft_failure_entries_record_base_model_beside_alias`, `test_from_failures_recovers_peft_sweep_alias_cells` green | ✓ PASS |
| MED-02 env_smoke cap label | `env_smoke.py:49,203` — "dnallm 1.2.1 caps datasets<=5.1.0" (v1.2.1 truth) | ✓ PASS |
| MED-03 provenance round-trip | `convert_registry.py` `--kind provenance` 7-column slice + merge-only + refuse-unknown-rows (:124-131,177-183); DATA.md marker text names the same path; `make data` no-op proves registry↔artifact agreement at HEAD | ✓ PASS |
| Publication gates | `dnallm-mark/data/frontier.json` and `vep_zero_shot.json` both ABSENT (post-E2' gated) | ✓ PASS |
| sweep priorities | `pipeline/sweep_priorities.json`: tier1 = 2 (model,task) pairs; tier2 = 3 bare names (GENERanno-eukaryote-0.5b-base, PlantCAD2-Small-l24-d0768, Omni-DNA-700M) | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan(s) | Status | Evidence |
|-------------|----------------|--------|----------|
| REL-03 (README reproducibility) | 06-04 | ✓ SATISFIED | SC-1 evidence |
| DATA-04 (provenance table, ModelScope-default URLs) | 06-04 | ✓ SATISFIED | SC-2 evidence (50/50 coverage incl. 47d057f) |
| DATA-05 (downloadable CSV/JSON manifest) | 06-04 | ✓ SATISFIED | committed provenance.{json,csv} + DATA.md links |
| DATA-07 (methodology docs + dead-logic removal) | 06-04 | ✓ SATISFIED | SC-4 evidence |
| EXT-01 (new-model onboarding) | 06-04 | ✓ SATISFIED | SC-5 evidence |
| EXT-02 (new-dataset onboarding) | 06-04 | ✓ SATISFIED | SC-5 evidence |
| REV-03 (exporter + snapshot; phase-6 tail) | 06-04 | ⚠ SATISFIED-WITH-GAP | snapshot exists + tar-verifiable; committed .sha256 stale vs tree (SC-3 gap) |
| REV-05 (LoRA/IA³/frozen probes + frontier) | 06-01, 06-02, 06-05 | ✓ SATISFIED | SC-6 evidence |
| REV-08 (zero-shot VEP + learning curves) | 06-01, 06-03, 06-05 | ✓ SATISFIED | SC-6 evidence |

All 9 phase-6 REQ IDs are marked `[x]` complete in REQUIREMENTS.md and carry implementation evidence. No orphaned requirements (REQUIREMENTS.md maps exactly these 9 to Phase 6).

### Constraint Audit

| Constraint | Status | Evidence |
|------------|--------|----------|
| No pipeline execution beyond the four evidenced bounded smokes | ✓ HELD | `pipeline/finetuned/` contains exactly 3 dirs (base dry-run shell, +lora, +probe — all plant-dnabert-6mer); no `sweep_failures.json` anywhere; only 2 fetched models (plant-dnabert-6mer, plant-dnagpt-BPE); VEP smoke artifacts in /tmp per SUMMARY |
| Smoke sanction scope (2026-10-11 directive: bounded plan-task smokes) | ✓ HELD | env_smoke all-PASS (13 PASS lines, exit 0); LoRA 1-epoch; VEP two-model; probe 1-epoch — all recorded as plan tasks in SUMMARYs with the amended sanction docstring (1298eef) |
| E2' never launched | ✓ HELD | no sweep execution evidence; maintainer dual-gate documented |
| `/home/forrest/Github/DNALLM` read-only | ✓ HELD | `git -C ... status --porcelain` EMPTY |
| No git tags created | ✓ HELD | `git tag` → `data-v1` only |
| `data_version` stays 1.1.0 | ✓ HELD | manifest.json |
| CI untouched by phase/smoke work | ✓ HELD | zero `.github/` commits in `83bdbaf..HEAD` |
| ruff + ty gates real | ✓ HELD | both executed by verifier, both clean; lint list includes the 4 phase-6 scripts (existence-guarded) |
| No leaderboard number moved | ✓ HELD | `make data` no-op at HEAD; comparisons/tasks.json/manifest untouched in range |

### Anti-Patterns Found

Zero debt markers (TBD/FIXME/XXX), zero TODO/HACK/PLACEHOLDER, zero stub phrases across all 42 covered implementation files. The 35/7 `Unspecified` provenance cells are the maintainer-reviewed honest-unknown state (c59f5f8), not stubs — correction path documented and MED-03-tested.

### Test Quality Audit

- Disabled/skipped tests in phase test files: **0** (one grep hit was the substring `exit(` matching `xit(` — false positive; verified)
- Chain-produced fixtures (`frontier_sample.json`, `expected_stub_rows.json`) pin byte-stability/determinism by design (documented 04-05/06-02/06-03 discipline); value correctness is pinned by separate first-principles tests (hand-derived VEP classification table, hand-computed deltas, hand-computed permutation p-values from Phase 5). No circular sole-oracle found.
- Assertion strength: value-level throughout (hash equality, exact counts, schema validation, refusal-message content)

### Decision Coverage

Gate reported `could-not-parse` (06-CONTEXT.md uses prose Area decisions, not `D-NN:` IDs) — warning-only by design. Manual mapping: all four Area decision groups (extended-lane depth, provenance/snapshot, docs architecture, DOI/1.2.1) are traceable to shipped artifacts verified above.

### In-Window Addition (out of phase-6 scope — noted, not verified as goal)

`docs/TUI-REQUIREMENTS.md` (6c79747) — next-milestone TUI requirements collection draft, maintainer-directed. Excluded from phase-6 goal verification per instructions; included in the covered-set fingerprint for provenance.

### Pending-UAT (deferred to the human gate — not failures)

1. **Docs read-through** — METHODOLOGY.md, ONBOARDING.md, README reproduction section: a human should confirm the prose is clear and accurate for an external reviewer (automated checks prove presence/wiring, not readability).
2. **VEP honest-FAIL interpretation** — maintainer review of the recorded sanity verdicts (both 100M models below the synthetic-cohort bar; RC asymmetry 0.3333 on the CLM) for the response-letter framing.
3. **Snapshot semantics decision** — see gap: re-freeze now vs pin at 9918046 until data-v2 (maintainer call; override available).
4. **GB10 smoke logs** — full logs live in /tmp (`06-01-env-smoke.txt`, `06-02-smoke-lora.log`, `06-05-smoke-probe.log`); maintainer may archive them before /tmp rotation.

### Gaps Summary

**One gap, introduced after plan close, precise and cheap to close.** SC-3's live-tree re-verification fails at HEAD because the maintainer-directed in-window commit 47d057f (ModelScope provenance fill — which correctly advanced SC-2 to 50/50 through the documented MED-03 path and left `make data` a byte-stable no-op) changed two files inside the frozen snapshot set without following the README's own re-freeze procedure (README.md:228-236) for landed data revisions. The deposition artifact is not compromised: all 58 tar members match the committed manifest (verifier-recomputed), so the frozen pre-fill state is fully recoverable and internally consistent. What breaks is the reviewer-facing tamper-evidence story: a fresh-clone reviewer running the README's one-liner sees 2 red lines. Fix options: (a) re-freeze and commit the refreshed `.sha256` (documented two-command procedure), or (b) accept the pinned-at-frozen-commit semantics via a VERIFICATION.md override + a README scoping note. Everything else in the phase — all six other SCs, all gates, all constraints — verified green against the actual codebase.

---

_Verified: 2026-10-11T01:35:29Z_
_Verifier: Claude (gsd-verifier)_
