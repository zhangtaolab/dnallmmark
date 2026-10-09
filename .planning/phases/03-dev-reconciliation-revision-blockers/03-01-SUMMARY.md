---
phase: 03-dev-reconciliation-revision-blockers
plan: "01"
subsystem: pipeline
tags: [git-merge, conflict-resolution, deprecation, xfail-lock, contract-test, readme]

requires:
  - phase: 02-data-contracts-test-harness
    provides: schema bucket pins (42/47/4/1), enum self-checks, known-defect lock suite (136 passed + 5 xfailed baseline)
  - phase: 01-audit-release-foundations
    provides: AUDIT.md findings contract, data-v1 baseline discipline
provides:
  - dev@c6b3137 merged into autorun; pipeline/run_finetune.py + TSV registries tracked; data tree held at HEAD bytes
  - Deprecated-but-compilable pipeline/dnallmmark_pipeline.py with F10 deprecation header; README names run_finetune.py as benchmark entry point
  - AUD-01 lock pivoted to fixture-injectable export-chain contract (xfail strict, proven non-vacuous) with shape companion
  - D-04 frontend review record for commit 8d99daf (verdict: clean, 4 observations)
affects: [03-02 (registry unification consumes merged .txt/.json registries), 03-03 (F1/F2 edits land on merged run_finetune.py), 03-04, Phase 4 (F3 species fix flips + removes the pivoted lock), Phase 5]

actuals:
  tokens: 18217   # 72870 chars / 4 over plan_head_before..HEAD; incl. ~11011 tokens of merged dev content — authored diff alone ≈ 7206
  tasks: 3
  commits: 5      # 3 authored (41bf49e merge, 1b74037, 00a07a2) + 2 dev-side commits absorbed via the merge (808d61e, c6b3137)
plan_head_before: 360be65607c3799e13c5a6a5135f4da123264420
plan_head_after: 00a07a2182ed54cbb013b2541e90125bbefac176

tech-stack:
  added: []       # nothing new — merge + edits only (ty/[gpu] land in 03-02/03-03)
  patterns:
    - "Per-path merge policy proven by byte-empty staged diff before the merge commit (T-03-01/T-03-02 mitigation)"
    - "Export-chain contract lock: fixture-injectable xfail(strict=True) joining result-JSON species against the datasets_info Category column (stdlib csv, CRLF-tolerant)"

key-files:
  created:
    - tests/fixtures/export_chain/defect_species_performance.json
    - .planning/phases/03-dev-reconciliation-revision-blockers/03-FRONTEND-REVIEW.md
  modified:
    - pipeline/dnallmmark_pipeline.py   # deprecation module docstring (F10); dev 11-line content arrived via merge
    - README.md                          # run_finetune.py usage + structure tree + adjacent truth fixes
    - tests/test_known_defects.py        # D-03 pivot: AST anchor retired, contract lock + companion added
    - pipeline/run_finetune.py           # arrived from origin/dev via merge (unmodified by this plan's tasks)

key-decisions:
  - "Merge resolved mechanically per the verified inventory — checkout --ours for the 51 data conflicts, git rm -f for the 6 clean dev additions (git rm requires -f for staged additions absent from HEAD); zero hand-edited JSON"
  - "README Run Pipeline section updated beyond the two named lines (detailed-args block, models_info.json->txt, --fix_token_len dropped, --auto_batch_size documented) so the renamed entry point is not misdocumented by its own adjacent prose"
  - "D-03 lock applies the research OQ-1 recommendation: species must be in {Animals, Plants, Microbe, Multiple} AND equal the dataset's Category"
  - "D-04 verdict recorded as CLEAN with 4 observations (O1/O2 = AUD-16-interaction edge cases, O3 pre-existing inert drawBorder, O4 aria-pressed) — no new AUD rows; each fails the confirmed-defect bar"

patterns-established:
  - "Merge-acceptance proof chain: byte-empty staged data diff + NO_DEV_DATA_FILES ls-files check + suite-count reproduction BEFORE the merge commit is created"
  - "Contract-lock pivot shape: fixture (defect-bearing) + xfail(strict=True) lock + unmarked shape companion, joined on an external registry column — reusable for future producer-contract locks"

requirements-completed: [REV-10]

coverage:
  - id: D1
    description: "dev@c6b3137 merged into autorun with the leaderboard data tree held at HEAD bytes and the 6 dev-added data files excluded (conflict inventory in merge commit message)"
    requirement: REV-10
    verification:
      - kind: other
        ref: "git diff --cached <pre-merge> --quiet -- dnallm-mark/data -> DATA_TREE_IDENTICAL (pre-commit, re-run post-commit)"
        status: pass
      - kind: other
        ref: "git ls-files check -> NO_DEV_DATA_FILES"
        status: pass
      - kind: unit
        ref: "make test -> 136 passed + 5 xfailed + node lane 2 pass (bucket pins 42/47/4/1 held)"
        status: pass
      - kind: other
        ref: "git diff origin/dev HEAD --quiet -- pipeline/datasets_info.txt -> byte-identical (CRLF preserved)"
        status: pass
    human_judgment: false
  - id: D2
    description: "F10: pipeline/dnallmmark_pipeline.py deprecated via module docstring naming run_finetune.py; README usage command and structure tree name run_finetune.py as the benchmark entry point; file retained and still compiles"
    requirement: REV-10
    verification:
      - kind: other
        ref: "head -n 12 pipeline/dnallmmark_pipeline.py | grep -c run_finetune -> 1; grep -c run_finetune.py README.md -> 2"
        status: pass
      - kind: other
        ref: "uv run --group dev python -m py_compile pipeline/dnallmmark_pipeline.py -> COMPILES"
        status: pass
    human_judgment: false
  - id: D3
    description: "AUD-01 lock pivoted (D-03) from the retired pipeline AST anchor to a fixture-injectable export-chain contract: species == datasets_info Category, xfail(strict=True), proven non-vacuous, with unmarked shape companion; old anchor + companion retired in the same commit"
    verification:
      - kind: unit
        ref: "tests/test_known_defects.py::test_aud01_species_matches_dataset_arena_category XFAIL + test_aud01_contract_fixture_has_expected_shape PASSED (3 locks, 5 xfailed items, zero XPASS)"
        status: pass
      - kind: unit
        ref: "pytest tests/test_known_defects.py -q --runxfail -> exit 1, lock fails on the athaliana defect entry (non-vacuous)"
        status: pass
      - kind: other
        ref: "grep retired names (_find_construction_sites, both old test names) -> 0 matches; WR-02/WR-03 byte-unchanged in diff"
        status: pass
    human_judgment: false
  - id: D4
    description: "D-04 targeted frontend review record for commit 8d99daf: full 9-hunk enumeration, per-hunk AUDIT-ID classification, explicit verdict"
    verification:
      - kind: other
        ref: "git show 8d99daf --name-only scope assert -> SCOPE_EXACT (exactly js/main.js, index.html, css/charts.css)"
        status: pass
      - kind: other
        ref: "grep 8d99daf -> 7 mentions; grep AUD-nn -> 13 mentions in 03-FRONTEND-REVIEW.md; no frontend source modified"
        status: pass
    human_judgment: true
    rationale: "Mechanical checks prove the record exists, is complete (9/9 hunks), and cross-references the audit; the 'clean' verdict itself is a static-review judgment a human may wish to spot-check"

duration: 15 min
completed: 2026-10-10
status: complete
---

# Phase 03 Plan 01: Dev-Branch Reconciliation Merge, F10 Retirement, D-03 Lock Pivot Summary

**origin/dev pipeline rewrite merged into autorun with the leaderboard data tree held byte-identical at HEAD; old pipeline deprecated in code and README; AUD-01 species lock pivoted to a fixture-injectable export-chain contract proven non-vacuous**

## Performance

- **Duration:** ~15 min (execution; excludes planning)
- **Started:** 2026-10-09T16:09:38Z
- **Completed:** 2026-10-10 (UTC boundary crossed during execution)
- **Tasks:** 3/3
- **Files modified:** 7 (4 code/doc + 1 fixture + 1 review record + merge-carriage)

## Accomplishments

- **The D-01/D-02 merge** (`41bf49e`, 2 parents): all 51 both-modified `dnallm-mark/data/` conflicts resolved to HEAD bytes via `git checkout --ours` (zero hand-edited generated JSON); the 6 dev-added data files (3 CrossDNA performance JSONs, `models_comparison_human.json`, 2 gene_exp task files) removed via `git rm -f`; `pipeline/run_finetune.py`, both TSV registries, dev's `models_info.json` (44 models) and `dnallmmark_pipeline.py` (11-line state) arrived cleanly. Proven before commit: `DATA_TREE_IDENTICAL`, `NO_DEV_DATA_FILES`, `make test` = 136 passed + 5 xfailed + node 2, `make lint` green. `datasets_info.txt` verified byte-identical to `origin/dev` (CRLF preserved).
- **F10 retirement + D-03 pivot in one commit** (`1b74037`): `pipeline/dnallmmark_pipeline.py` opens with a deprecation module docstring naming `run_finetune.py` (compiles via `py_compile`; nothing else changed); README's usage command, detailed-args block, and structure tree now document `run_finetune.py`; `tests/test_known_defects.py` retired `_find_construction_sites` + the AST lock + old companion and gained `test_aud01_species_matches_dataset_arena_category` (xfail strict, fails on the fixture's `athaliana` defect — proven via `--runxfail` exit 1) plus the unmarked `test_aud01_contract_fixture_has_expected_shape` companion; WR-02/WR-03 byte-unchanged; suite baseline preserved exactly.
- **D-04 review record** (`00a07a2`): commit `8d99daf` (the only frontend delta between this lineage and dev, per the research correction) reviewed hunk-by-hunk against the Phase 1 audit baseline — verdict CLEAN, 4 observations recorded for Phase 4, no new AUD rows (each observation fails the confirmed-defect bar: deliberate design, AUD-16-contingent with zero committed instances, pre-existing code, or a11y nicety).

## Task Commits

1. **Task 1: D-01 merge — 51 data conflicts to HEAD, 6 dev-added files removed, suite green** — `41bf49e` (feat, merge commit with per-path-group conflict inventory)
2. **Task 2: F10 deprecation + README entry-point rename + D-03 lock pivot** — `1b74037` (feat)
3. **Task 3: D-04 targeted frontend review of 8d99daf** — `00a07a2` (docs)

**Plan metadata:** this SUMMARY + STATE/ROADMAP/REQUIREMENTS commit (see below).

## Files Created/Modified

- `pipeline/run_finetune.py` — merged from origin/dev (737 lines, read-only cargo per D-05; never executed)
- `pipeline/models_info.txt`, `pipeline/datasets_info.txt` — merged TSV registries (CRLF preserved)
- `pipeline/models_info.json` — dev side (44 models incl. CrossDNA)
- `pipeline/dnallmmark_pipeline.py` — dev 11-line state via merge + F10 deprecation docstring
- `README.md` — run_finetune.py as benchmark entry point (usage + args + structure tree + registry/flag prose fixes)
- `tests/test_known_defects.py` — D-03 pivot (AST anchor machinery removed; contract lock + `_load_category_map` + companion added)
- `tests/fixtures/export_chain/defect_species_performance.json` — NEW defect-bearing result-JSON fixture (5 datasets: Microbe/Animals/Multiple/Plants healthy + athaliana defect)
- `.planning/phases/03-dev-reconciliation-revision-blockers/03-FRONTEND-REVIEW.md` — NEW D-04 record

## Decisions Made

- Recorded in frontmatter `key-decisions` (merge mechanics, README truth-scope, OQ-1 contract shape, D-04 observations bar).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Documentation correctness] README Run Pipeline section updated beyond the two named lines**
- **Found during:** Task 2
- **Issue:** The plan named the L154 usage command and the ~L318 structure-tree entry. But renaming the command alone would leave the adjacent detailed-arguments block documenting flags `run_finetune.py` does not accept (`--fix_token_len`), the prose naming `models_info.json` (the new pipeline reads `models_info.txt`, verified at run_finetune.py:319), and a batch-size sentence describing always-on auto-adjustment (the new pipeline makes it opt-in `--auto_batch_size`).
- **Fix:** The args block was replaced with `run_finetune.py`'s verbatim argparse surface; `models_info.json` -> `models_info.txt`; `--fix_token_len` clause dropped; `--auto_batch_size` documented. The L210 exporter sentence (`{model_name}_performance.json` claim) was NOT touched — rewording it front-runs REV-03; logged to `deferred-items.md` instead.
- **Files modified:** README.md
- **Verification:** `grep -c "run_finetune.py" README.md` -> 2; manual read of the section
- **Committed in:** 1b74037

**2. [Rule 3 - Blocking] `git rm` required `-f` for the 6 dev-added data files**
- **Found during:** Task 1
- **Issue:** Plain `git rm` refused ("the following files have changes staged in the index") because the merge staged them as additions absent from HEAD.
- **Fix:** `git rm -f` on exactly the 6 named paths — index + worktree removal, the plan-instructed resolution; content remains recoverable from `origin/dev`.
- **Verification:** `NO_DEV_DATA_FILES` echoed; data-tree diff byte-empty
- **Committed in:** 41bf49e

---

**Total deviations:** 2 auto-fixed (1 documentation correctness, 1 blocking mechanic)
**Impact on plan:** Neither widens review surface beyond the sections the plan already renamed; both were required for the named edits to be truthful. No scope creep.

## Issues Encountered

None.

## Authentication Gates

None — fully offline work.

## User Setup Required

None.

## Known Stubs

None — no stub patterns introduced. (The fixture's `info.huggingface`/`modelscope` are empty strings mirroring the synthetic-fixture convention; test fixture data, not UI-rendering stubs.)

## Next Phase Readiness

- 03-02 (D-10 registry unification) can consume the merged dual registries (`.txt` operational + `.json` card, CRLF endings) exactly as researched; `datasets_info.txt` verified byte-identical to dev.
- 03-03 (F1/F2) edits land on the merged `run_finetune.py` — the G1 outdir site, D-07 grad_accum leak (L584-598), and D-11 head-config leak sites are all present in the merged file per research's verbatim quotes; run_finetune.py was never executed (D-05).
- Phase 4's F3 species fix will XPASS the pivoted AUD-01 lock (`test_aud01_species_matches_dataset_arena_category`) — the marker must be removed in the same commit as the fix (house rule, documented in the module docstring).
- Deferred: README exporter sentence (see `deferred-items.md`); D-04 observations O1-O4 for the Phase 4 frontend pass.

## Self-Check: PASSED

All key created files exist on disk (fixture, review record, SUMMARY, merged pipeline files); all three task commits (41bf49e, 1b74037, 00a07a2) verified as ancestors of HEAD.

---
*Phase: 03-dev-reconciliation-revision-blockers*
*Completed: 2026-10-10*
