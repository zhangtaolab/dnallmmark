---
phase: 06-revision-packaging-extended-lanes
verified: 2026-10-11T01:44:46Z
status: passed
score: 7/7 must-haves verified
covered_files: [".gitignore", ".planning/phases/06-revision-packaging-extended-lanes/06-01-PLAN.md", ".planning/phases/06-revision-packaging-extended-lanes/06-01-SUMMARY.md", ".planning/phases/06-revision-packaging-extended-lanes/06-02-PLAN.md", ".planning/phases/06-revision-packaging-extended-lanes/06-02-SUMMARY.md", ".planning/phases/06-revision-packaging-extended-lanes/06-03-PLAN.md", ".planning/phases/06-revision-packaging-extended-lanes/06-03-SUMMARY.md", ".planning/phases/06-revision-packaging-extended-lanes/06-04-PLAN.md", ".planning/phases/06-revision-packaging-extended-lanes/06-04-SUMMARY.md", ".planning/phases/06-revision-packaging-extended-lanes/06-05-PLAN.md", ".planning/phases/06-revision-packaging-extended-lanes/06-05-SUMMARY.md", "DATA.md", "Makefile", "README.md", "baseline/snapshots/snapshot-3921fdb5b0227f67bcfca7a56de15d2f6aa77ba3.sha256", "dnallm-mark/data/provenance.csv", "dnallm-mark/data/provenance.json", "dnallm-mark/js/config.js", "dnallm-mark/js/data.js", "docs/METHODOLOGY.md", "docs/ONBOARDING.md", "docs/TUI-REQUIREMENTS.md", "pipeline/datasets_info.json", "pipeline/env_smoke.py", "pipeline/finetune_config.yaml", "pipeline/finetune_config_curve.yaml", "pipeline/finetune_config_probe.yaml", "pipeline/finetune_config_with_head.yaml", "pipeline/run_finetune.py", "pipeline/run_sweep.py", "schemas/frontier.json", "schemas/provenance.json", "schemas/vep_zero_shot.json", "script/build_frontier.py", "script/build_provenance.py", "script/convert_registry.py", "script/doi_swap.py", "script/export_runs.py", "script/freeze_snapshot.py", "script/zero_shot_vep.py", "tests/fixtures/frontier/frontier_sample.json", "tests/fixtures/vep_zero_shot/cohort.vcf", "tests/fixtures/vep_zero_shot/expected_stub_rows.json", "tests/fixtures/vep_zero_shot/reference.json", "tests/js/data-api.test.js", "tests/js/main-view-toggle.test.js", "tests/test_build_provenance.py", "tests/test_convert_registry.py", "tests/test_doi_swap.py", "tests/test_export_runs.py", "tests/test_frontier.py", "tests/test_run_finetune_contracts.py", "tests/test_schemas.py", "tests/test_sweep.py", "tests/test_zero_shot_vep.py"]
covered_digest: "v3:sha256:65e46935a1faee07009c83f508d8bf6ef96c2742cf0e8e24112aaf1d84c73bf1"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 6/7
  gaps_closed:
    - "SC-3 live-tree snapshot re-verification: committed manifest now verifies against the working tree (58/58, exit 0) after the 9d1ec27 re-freeze"
  gaps_remaining: []
  regressions: []
---

# Phase 6: Revision Packaging & Extended Lanes — Verification Report

**Phase Goal:** External reviewers can understand, trust, reproduce, and extend the platform — provenance, methodology docs, validated onboarding, result snapshots for SI/Zenodo — with the revision-window extension lanes (PEFT, zero-shot VEP, learning curves) delivered as far as the window allows and the remainder explicitly deferred to the response letter
**Verified:** 2026-10-11T01:44:46Z
**Status:** passed
**Re-verification:** Yes — after gap closure (prior report 3921fdb, status gaps_found 6/7; single gap closed by 9d1ec27)
**Covered set:** commits `83bdbaf..HEAD` (HEAD `9d1ec27`; 52 commits — the prior 50 + the verification-report commit + the snapshot re-freeze), fingerprinted above

## Re-verification Note (gap → fix → re-run)

The prior run verified 6/7 SCs and FAILED exactly one check: SC-3's documented re-verification one-liner (`cd baseline/snapshots && sha256sum -c snapshot-*.sha256`, README.md:219) exited 1 with 2/58 mismatched lines, because the in-window ModelScope provenance fill (47d057f) changed `provenance.csv`/`provenance.json` — both inside the frozen set — without a re-freeze. The fix landed as 9d1ec27: the stale `snapshot-9918046...sha256` pair was removed and the snapshot re-frozen over the then-current tree using `freeze_snapshot.py`'s **documented manual override** (`--commit-hash "$(git rev-parse HEAD)"`, script docstring: "records the CURRENT tree instead of the stamped data revision — use only when re-freezing outside the data chain"). The diff is exactly 3 lines: header commit `9918046→3921fdb` plus the two refreshed provenance hashes. Note this is the freeze *script's* documented CLI override — NOT a VERIFICATION.md must-have override; the gap was closed for real (prior option (a): re-freeze and commit), so `overrides_applied: 0`. This pass re-ran **every gate independently at HEAD 9d1ec27**, fully re-verified the failed SC-3, and spot-checked the six previously-green SCs (warranted despite 9d1ec27 touching only the manifest, per re-verification discipline).

## Goal Achievement

### Observable Truths (per ROADMAP Success Criteria)

| # | Truth (SC) | Status | Evidence (re-run at 9d1ec27 unless noted) |
|---|------------|--------|----------|
| 1 | SC-1: Reviewer can reproduce the leaderboard from a fresh clone using literal copy-pasteable README commands (install → data → aggregate → serve) | ✓ VERIFIED (regression spot-check) | README.md:113+ "Reproducing the Leaderboard" intact with literal `uv sync` / `make data` + porcelain check / `make test` / `bash start-server.sh` blocks and per-step expected output; drift gate re-run green (below) proves the data step is byte-stable at HEAD |
| 2 | SC-2: Each dataset has a provenance row (source, citation, license, preprocessing, ModelScope-default URL + alternates); downloadable CSV/JSON manifest with direct links | ✓ VERIFIED (regression spot-check) | Registry spot-check: `pipeline/datasets_info.json` = 50 entries, **0 blank `download_url`** (50/50, incl. the 47d057f fill); `make data` no-op (porcelain empty) proves registry ↔ committed `provenance.{csv,json}` ↔ DATA.md agreement at HEAD |
| 3 | SC-3: Results snapshot (tar + SHA-256 manifest + frozen commit hash) supports SI/Zenodo deposition and can be re-verified from its manifest | ✓ VERIFIED (full re-verification — gap closed) | The README one-liner now passes: `cd baseline/snapshots && sha256sum -c snapshot-*.sha256` → **58/58 OK, exit 0** (verifier-executed). Tar-vs-manifest: verifier-recomputed SHA-256 over all tar members → **58/58 match, 0 missing, 0 extra** (deposition artifact internally consistent). Fresh-clone path works: `.sha256` + all hashed data files are committed; paths in the manifest are relative to `baseline/snapshots/` (`../../dnallm-mark/data/...`). **Frozen-hash semantics (honest):** the manifest is named/headered `3921fdb` — the tree whose data files were hashed (HEAD at freeze time); the committing HEAD `9d1ec27` differs from `3921fdb` **only by the manifest itself** (verified: `git diff --stat 3921fdb 9d1ec27` → 1 file, the manifest rename+3 lines; data tree identical). `manifest.json`'s `generated_from` deliberately remains `9918046` — the declared data-revision stamp (pinned via `summarize_comparison.py:540` `GENERATED_FROM`, "pre-D-18-rename HEAD"); restamping is a data-v2 event, so the override name is the correct record of where the re-freeze actually happened. Observation (not a gap): the wired `make snapshot` lane still derives its name from `generated_from` (9918046), so a future wired re-freeze would emit a `snapshot-9918046.*` pair alongside this one; both would verify against the same tree, and the seam resolves at the data-v2 restamp |
| 4 | SC-4: Four aggregation methods (+F6 dual views) documented in ONE place; `js/data.js:recalculateComparison()` dead logic gone | ✓ VERIFIED (regression spot-check) | `grep -rn recalculateComparison dnallm-mark/` → zero live hits (lesson-comment mentions only); `docs/METHODOLOGY.md` intact (156 lines; "Per-task normalization (four methods)" :31, "The dual views (F6)" :67); node suite pins the absence (18/18 green) |
| 5 | SC-5: Maintainer can onboard a new model/dataset end-to-end via the documented process (mechanism validated, no GPU runs) | ✓ VERIFIED (regression spot-check) | `docs/ONBOARDING.md` intact (217 lines, new-model + new-dataset checklists); underlying commands test-covered in the green suite (451 pytest) |
| 6 | SC-6: Revision-window lanes in priority order — LoRA/IA³/frozen probes + frontier; zero-shot VEP; learning curves; remainder deferred with mechanism documented | ✓ VERIFIED (regression spot-check) | Anchors re-confirmed: `--peft` flag (`run_finetune.py:198`); `PROBE_INELIGIBLE` (`run_finetune.py:504`) contains **both `SPACE` and `space`** with per-line provenance (HI-01); `zero_shot_vep.py`, `build_frontier.py`, `schemas/{frontier,vep_zero_shot}.json` present; **publication gates held** — `dnallm-mark/data/frontier.json` and `vep_zero_shot.json` both ABSENT; GPU smokes on disk: LoRA pct **0.331253** (296450/89493508), probe pct **0.441759** (395778/89591298), both in (0,5%] |
| 7 | SC-7: Zenodo preview-token link replaced with published DOI once record 19135551 is public, .gitleaks.toml updated in same commit — prepared, not executed | ✓ VERIFIED (regression spot-check) | README tokenized-link count = **1** (INTACT); `.gitleaks.toml` record-19135551 allowlist rule intact (:25,:35); `doi_swap.py` 404-refusal naming record + `--force` escape present; swap provably still NOT executed |

**Score:** 7/7 truths verified (0 present-but-behavior-unverified)

### Gates (all re-run independently by the verifier at 9d1ec27)

| Gate | Command | Result | Status |
|------|---------|--------|--------|
| Full suite | `make test` | pytest **451 passed** in 9.68s; exit 0 | ✓ PASS |
| Node lane | `node --test tests/js/` (inside make test) | **18 tests, 18 pass, 0 fail** | ✓ PASS |
| Lint | `make lint` | All checks passed (ruff; includes the 4 phase-6 scripts) | ✓ PASS |
| Type-check | `make typecheck` | All checks passed (ty) | ✓ PASS |
| Drift | `make data` + `git status --porcelain` | exit 0; porcelain **EMPTY** — byte-stable no-op at HEAD incl. the re-frozen provenance state | ✓ PASS |
| Snapshot re-verify (SC-3, the prior gap) | `cd baseline/snapshots && sha256sum -c snapshot-*.sha256` | **58/58 OK, exit 0** (was 2/58 FAIL at 47d057f..3921fdb) | ✓ PASS — gap closed |
| Tar-vs-manifest | verifier-computed SHA-256 over all tar members of `snapshot-3921fdb...tar` | 58/58 match, 0 missing, 0 extra | ✓ PASS |

### Behavioral Spot-Checks

| Behavior | Evidence | Status |
|----------|----------|--------|
| LoRA smoke persistence | `pipeline/finetuned/plant-dnabert-6mer+lora/.../final_metrics.json`: 296450 / 89493508 / pct **0.331253** in (0,5] | ✓ PASS |
| Probe smoke frozen backbone | `plant-dnabert-6mer+probe/.../final_metrics.json`: 395778 / 89591298 / pct **0.441759** in (0,5] | ✓ PASS |
| Publication gates (post-E2') | `dnallm-mark/data/frontier.json`, `vep_zero_shot.json` ABSENT | ✓ PASS |
| HI-01 probe-scope closure | `PROBE_INELIGIBLE` lists `SPACE` and `space` (run_finetune.py:504-507, per-line provenance); pin test in green suite | ✓ PASS |
| Snapshot reproducibility from a fresh clone | committed `.sha256` + all 58 hashed files are git-tracked; manifest paths relative to `baseline/snapshots/` | ✓ PASS |
| Stale-name residue | repo-wide `9918046` references: `manifest.json` + `summarize_comparison.py:540` (deliberate data-revision stamp) + `baseline/d18-alias-inventory.json` (historical record) — none reference the removed snapshot filename; `tests/test_freeze_snapshot.py` uses its own fixture hash (`deadbeef1234`) | ✓ PASS |

### Regression Scope (evidence gate, #3304)

Files modified since the prior `verified:` stamp (2026-10-11T01:35:29Z): exactly two — the snapshot manifest (9d1ec27) and the prior VERIFICATION.md itself (3921fdb). No implementation file other than the manifest changed, and the manifest carries zero debt markers (TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER — grep clean). The prior six green SCs therefore could not regress through 9d1ec27; they were spot-checked anyway (evidence above). No new-scope findings; no advisories.

### Requirements Coverage

| Requirement | Source Plan(s) | Status | Evidence |
|-------------|----------------|--------|----------|
| REL-03 (README reproducibility) | 06-04 | ✓ SATISFIED | SC-1 |
| DATA-04 (provenance table, ModelScope-default URLs) | 06-04 | ✓ SATISFIED | SC-2 (50/50) |
| DATA-05 (downloadable CSV/JSON manifest) | 06-04 | ✓ SATISFIED | committed provenance.{json,csv} + DATA.md links |
| DATA-07 (methodology docs + dead-logic removal) | 06-04 | ✓ SATISFIED | SC-4 |
| EXT-01 / EXT-02 (onboarding) | 06-04 | ✓ SATISFIED | SC-5 |
| REV-03 (exporter + snapshot) | 06-04 | ✓ SATISFIED | SC-3 — now fully green (was SATISFIED-WITH-GAP) |
| REV-05 (LoRA/IA³/frozen probes + frontier) | 06-01, 06-02, 06-05 | ✓ SATISFIED | SC-6 |
| REV-08 (zero-shot VEP + learning curves) | 06-01, 06-03, 06-05 | ✓ SATISFIED | SC-6 |

All 9 phase-6 REQ IDs remain `[x]` in REQUIREMENTS.md; no orphaned requirements (unchanged since the prior pass — verified then, no planning-file changes since).

### Constraint Audit

| Constraint | Status | Evidence (re-checked) |
|------------|--------|--------|
| No pipeline execution beyond the four evidenced bounded smokes | ✓ HELD | `pipeline/finetuned/` = exactly 3 dirs (base, +lora, +probe); no `sweep_failures.json` anywhere (find → 0) |
| E2' never launched | ✓ HELD | no sweep execution evidence; publication gates still hold |
| `/home/forrest/Github/DNALLM` read-only | ✓ HELD | `git -C` porcelain = 0 lines |
| No git tags created | ✓ HELD | `git tag` → `data-v1` only |
| `data_version` stays 1.1.0 | ✓ HELD | manifest.json |
| CI untouched by phase/smoke work | ✓ HELD | both post-prior commits touch no `.github/` path |
| ruff + ty gates real | ✓ HELD | both re-executed by verifier, both clean |
| No leaderboard number moved | ✓ HELD | `make data` no-op; porcelain empty |

### Anti-Patterns / Test Quality

Zero debt markers in the changed file; full-suite green (451 + 18). Test-quality findings from the prior pass carry over unchanged (no test file touched since): zero disabled tests, value-level assertions throughout, chain-produced fixtures backed by separate first-principles tests.

### Decision Coverage

Gate re-run: `could-not-parse` (06-CONTEXT.md uses prose Area decisions, not `D-NN:` IDs) — warning-only by design, same as the prior pass. Manual mapping (prior report): all four Area decision groups traceable to the shipped artifacts verified above.

### Pending-UAT (deferred to the human gate — not failures)

1. **Docs read-through** — METHODOLOGY.md, ONBOARDING.md, README reproduction section: a human should confirm the prose is clear and accurate for an external reviewer (automated checks prove presence/wiring, not readability).
2. **VEP honest-FAIL interpretation** — maintainer review of the recorded sanity verdicts (both 100M models below the synthetic-cohort bar; RC asymmetry 0.3333 on the CLM) for the response-letter framing.
3. **~~Snapshot semantics decision~~ — RESOLVED** by the 9d1ec27 re-freeze: the manifest now verifies against the live tree (58/58, exit 0) and the deposition tar is consistent; the pinned-at-9918046 alternative was not taken. Residual semantics (manifest named 3921fdb vs committing HEAD 9d1ec27 differing only by the manifest; `generated_from` stamp intentionally still 9918046 until data-v2) documented under SC-3 above — no maintainer decision outstanding.
4. **GB10 smoke logs** — full logs live in /tmp (`06-01-env-smoke.txt`, `06-02-smoke-lora.log`, `06-05-smoke-probe.log`); maintainer may archive them before /tmp rotation.

### Gaps Summary

None. The single prior gap (SC-3 committed-manifest vs live-tree mismatch) is closed with deterministic evidence re-produced by this verifier at HEAD 9d1ec27: the documented re-verification one-liner passes 58/58 with exit 0, and all 58 tar members match the committed manifest. All seven SCs, all gates, and all constraints verified green against the actual codebase.

## VERIFICATION PASSED

---

_Verified: 2026-10-11T01:44:46Z_
_Verifier: Claude (gsd-verifier)_
