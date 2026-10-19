---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
plan: 05
subsystem: pipeline
tags: [d-04-deletion, legacy-purge, parity-repin, verbatim-literals, quality-gates]

# Dependency graph
requires:
  - phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
    provides: pipeline/flops_counter.py — the verbatim FlopsCounter port, now the FLOPs reference of record (07-01)
  - phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
    provides: run_finetune.py calibration slot + post-success flops_report write — the legacy file fully superseded (07-04)
provides:
  - pipeline/dnallmmark_pipeline.py deleted (D-04 closed — git history is the reference, final commit 1b74037e)
  - tests/test_run_finetune_contracts.py parity expectations as self-contained sha-documented inline literals (LEGACY_PIPELINE retired)
  - Zero dnallmmark_pipeline references across pipeline/ script/ tests/ Makefile schemas/; docs refreshed (README, AUDIT past-tense banner, TUI-REQUIREMENTS, .claude/CLAUDE.md architecture sections)
  - Full phase surface green in one run: make lint / make typecheck / make test (550 pytest + 18 node tests)
affects: [07-06 GB10 smoke (last plan of the phase), phase-08 tui (CLAUDE.md architecture context now current), phase-11 monitor]

# Actuals (#2632) — same estimateTokens scale as the plan's estimate (chars/4
# over the realized diff). Estimate was 30000 tokens; realized ~24700.
actuals:
  tokens: 24700
  tasks: 3
  commits: 2

tech-stack:
  added: []  # zero external packages (T-07-SC vacuous)
  patterns:
    - "parity-expectation re-pinning: transcribe verbatim literals + per-block one-line provenance comment naming the source commit sha BEFORE deleting the source file — the suite is green at every intermediate commit, making the deletion provably non-breaking (D-04 discipline)"
    - "provenance-by-sha: after deletion, live-code comments cite the legacy source by description + final commit sha, never by live path (git history is the reference)"

key-files:
  created: []
  modified:
    - tests/test_run_finetune_contracts.py
    - pipeline/flops_counter.py
    - pipeline/run_finetune.py
    - script/export_runs.py
    - tests/test_known_defects.py
    - README.md
    - AUDIT.md
    - docs/TUI-REQUIREMENTS.md
    - .claude/CLAUDE.md
  deleted:
    - pipeline/dnallmmark_pipeline.py

key-decisions:
  - "Provenance comments name the legacy source via description + final commit sha (1b74037e14defbe7ed94f798e2f3f91b0d184ce6) rather than the live filename: Task 1's comment template and Task 2's zero-grep gate over tests/ cannot both hold literally, and the sha is the durable pointer D-04 designates (git history is the reference)"
  - "LEGACY_MODELS_WITH_LIMITED_LENGTH carries the legacy file's verbatim int caps (1027/512); the parity test str()-normalizes at the use site because dict_members()'s regex yields string digits — assertion semantics byte-identical"
  - ".claude/CLAUDE.md updated surgically (only the 31 dnallmmark_pipeline mentions, the FLOPs reference of record, and the retained-read-only claims); its other pre-existing staleness (41-vs-62 models, 'no test framework') predates this phase and stays out of scope per fix discipline"

patterns-established:
  - "Deletion close-out order: re-pin expectations -> verify green -> delete + purge references in ONE task -> re-run all gates; archives under .planning/milestones/ never edited by cleanup"
  - "Historical audit records are marked, not falsified: AUDIT.md gains a post-audit banner naming the deletion; finding rows keep their original file/line citations as records"

requirements-completed: [PIPE-01]  # shared with 07-01/07-04/07-06 — completes only when 07-06 finishes (shared-ID gate)

coverage:
  - id: D1
    description: "Five LEGACY_PIPELINE parity expectations re-pinned as inline literals before deletion (D-04): fp32-only, no-char-n (+ deeplearning_models prefix), limited-length caps, safetensors union, determine_batch_size tier table — each with a transcribed-from comment naming the final commit sha; LEGACY_PIPELINE constant retired"
    requirement: PIPE-01
    verification:
      - kind: unit
        ref: "tests/test_run_finetune_contracts.py#test_fp32_only_models_forced_to_full_precision, test_models_no_char_n_parity_with_name_map, test_models_with_limited_length_wired, test_safetensors_list_is_legacy_union, test_length_tier_rounding_parity — 64/64 green with the legacy file still present at commit dd4099a"
        status: pass
      - kind: other
        ref: "grep -v '^\s*#' tests/test_run_finetune_contracts.py | grep -c LEGACY_PIPELINE -> 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "Legacy file deleted with full reference purge: git rm pipeline/dnallmmark_pipeline.py + stale __pycache__ bytecode; provenance comments refreshed in flops_counter.py/run_finetune.py/export_runs.py/test_known_defects.py; README tree, AUDIT.md past-tense banner, TUI-REQUIREMENTS Phase-7 note, .claude/CLAUDE.md architecture sections (FLOPs reference = flops_counter.py, zero retained-read-only claims)"
    requirement: PIPE-01
    verification:
      - kind: other
        ref: "test ! -e pipeline/dnallmmark_pipeline.py -> deleted; grep -rn dnallmmark_pipeline pipeline/ script/ tests/ Makefile schemas/ -> 0 lines; git diff --quiet HEAD -- .planning/milestones/ -> archives-untouched; repo-wide mentions remain only in AUDIT.md (historical banner) + .planning/ archives"
        status: pass
    human_judgment: false
  - id: D3
    description: "Full phase gates green over the complete Phase 7 surface for the first time in one run: lint covers all three new pipeline modules + edited files via PHASE7_MODULES; typecheck zero diagnostics; full pytest (incl. flops_counter/artifact_loader/registry_loader/sweep/contracts suites + slow lane) + node JS lane"
    requirement: PIPE-01
    verification:
      - kind: other
        ref: "make lint -> All checks passed! (exit 0, all PHASE7 modules in expansion)"
        status: pass
      - kind: other
        ref: "make typecheck -> All checks passed! (exit 0)"
        status: pass
      - kind: other
        ref: "make test -> 550 passed (pytest, 9.66s) + node lane 18 pass / 0 fail (exit 0)"
        status: pass
    human_judgment: false

# Metrics
duration: 10 min
completed: 2026-10-11
status: complete
plan_head_before: 4e5fa690c8cf5a5a7d2f9bf86a11fb66be59a892
plan_head_after: 96f20a6ae89e5ff89eb0c166039856c4ffa65546  # last production commit; the docs close-out commit follows this SUMMARY
---

# Phase 7 Plan 05: Legacy Pipeline Deletion (D-04) + Parity Re-pins + Phase Gates Summary

**D-04 closed: pipeline/dnallmmark_pipeline.py deleted (final commit 1b74037e — git history is the reference) after its five parity expectations were re-pinned as sha-documented verbatim literals, every stale reference purged from live code and docs, and the complete Phase 7 surface green in one gate run (make lint / typecheck clean; 550 pytest + 18 node tests pass)**

## Performance

- **Duration:** 10 min (2026-10-11T07:33:38Z → 07:43:36Z)
- **Tasks:** 3/3
- **Files:** 10 (9 modified, 1 deleted; -1422/+176 lines)
- **Commits:** 2 production (measured `git rev-list --count 4e5fa69..HEAD` = 2 at SUMMARY time; the docs close-out follows)

## Accomplishments

- **The five parity expectations are self-contained literals** (Task 1,
  `dd4099a`): `models_only_support_fp32`, `deeplearning_models` +
  `models_no_char_n` (composition form preserved), `models_with_limited_length`
  (verbatim int caps), `model_not_use_safetensors` (10-entry legacy set), and
  the full `determine_batch_size` function source (exec'd through the same
  `extract_fn` as the ACTIVE source) — each block carrying a one-line
  "transcribed from the legacy pipeline script at commit
  1b74037e14defbe7ed94f798e2f3f91b0d184ce6 before deletion (D-04)" comment.
  The suite was green at this commit WITH the legacy file still present —
  the safety property that made the deletion provably non-breaking.
- **The legacy file is gone and nothing points at it** (Task 2, `96f20a6`):
  `git rm pipeline/dnallmmark_pipeline.py` + both stale `.pyc` files
  (cpython-313/314); provenance comments in `pipeline/flops_counter.py`
  (:4/:803/:853), `pipeline/run_finetune.py` (:550/:1444),
  `script/export_runs.py` (:286), and `tests/test_known_defects.py`'s
  docstring now cite the legacy source by description + final commit sha;
  README's directory tree drops the line (and adds flops_counter.py);
  AUDIT.md gains a post-audit banner marking the deletion (findings rows
  untouched — records are not falsified); docs/TUI-REQUIREMENTS.md gains a
  Phase-7-landed note; .claude/CLAUDE.md's 31 mentions rewritten with
  `pipeline/flops_counter.py` as the FLOPs reference of record and
  `pipeline/run_finetune.py` as the pipeline entry — every
  retained-read-only/never-deleted claim corrected.
- **All three phase gates green over the full surface, first time in one
  run** (Task 3, no corrective edits needed): `make lint` exit 0 with
  flops_counter.py + registry_loader.py + artifact_loader.py confirmed in
  the PHASE7_MODULES expansion (existence-guard idiom from 07-01 — no
  Makefile fix required); `make typecheck` exit 0, zero diagnostics; full
  `make test` = 550 pytest passed (slow lane included — up from 07-04's
  549-fast-lane baseline with the re-pinned contracts) + node lane 18/18.

## Task Commits

Each task was committed atomically:

1. **Task 1: Re-pin the five LEGACY_PIPELINE parity expectations as
   literals (before deletion)** — `dd4099a` (test)
2. **Task 2: Delete the legacy file, purge stale references** — `96f20a6`
   (chore)
3. **Task 3: Full phase gates** — no commit (gates green on first run; the
   plan's conditional Makefile lint-list fix was not needed)
4. **Plan metadata close-out** — this SUMMARY + STATE/ROADMAP/REQUIREMENTS

## Files Created/Modified

- `tests/test_run_finetune_contracts.py` — five parity tests read
  LEGACY_* literals instead of the legacy file; LEGACY_PIPELINE constant
  retired; module docstring updated to the transcription mechanism
- `pipeline/dnallmmark_pipeline.py` — DELETED (git history retains it at
  1b74037e)
- `pipeline/flops_counter.py`, `pipeline/run_finetune.py`,
  `script/export_runs.py`, `tests/test_known_defects.py` — provenance
  comments refreshed (sha-cited, no live-path mention)
- `README.md` — tree line replaced (legacy dropped, flops_counter.py added)
- `AUDIT.md` — post-audit deletion banner added
- `docs/TUI-REQUIREMENTS.md` — Phase-7-landed note on the FLOPs gap item
- `.claude/CLAUDE.md` — architecture sections current again (FLOPs
  reference, pipeline entry, conventions, entry points, constraints)

## Decisions Made

- Provenance comments cite the legacy source by description + final commit
  sha instead of the live filename (see Deviation 1 — Task 1's comment
  template and Task 2's zero-grep gate over tests/ conflict literally; the
  sha is the durable pointer D-04 designates).
- `LEGACY_MODELS_WITH_LIMITED_LENGTH` stores verbatim int caps; the test
  str()-normalizes because `dict_members()`'s regex yields string digits —
  the comparison keeps its exact original semantics.
- .claude/CLAUDE.md edited surgically (dnallmmark_pipeline mentions and
  FLOPs/reference claims only); regenerating the whole generated file is a
  separate maintainenance action outside this plan's surgical scope.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Task 1's provenance-comment template conflicts with Task 2's grep gate**
- **Found during:** Task 1 (before writing the comments)
- **Issue:** Task 1 specifies each literal block gets a comment
  "transcribed from pipeline/dnallmmark_pipeline.py at commit {sha}", but
  Task 2's verify requires `grep -rn "dnallmmark_pipeline" ... tests/` to
  return ZERO lines — a comment carrying the filename can never satisfy
  both.
- **Fix:** the comments name the source as "the legacy pipeline script ...
  at commit 1b74037e14defbe7ed94f798e2f3f91b0d184ce6 before deletion
  (D-04)" — description + sha, no live-path token. Git history (the sha)
  is exactly the reference D-04 designates, so provenance is preserved.
- **Files modified:** tests/test_run_finetune_contracts.py (same comments
  also shaped the flops_counter.py/run_finetune.py/export_runs.py rewording
  in Task 2)
- **Verification:** both gates pass — each block carries the sha'd
  transcribed-from comment AND the Task 2 grep returns 0.
- **Committed in:** `dd4099a` / `96f20a6`

**2. [Rule 1 - Bug] Fifth test's legacy file-read line survived the first edit pass**
- **Found during:** Task 1 verification (first pytest run — 1 failed,
  NameError: LEGACY_PIPELINE)
- **Issue:** the determine_batch_size test read the legacy file into a
  local `legacy` variable that the re-pin replaced only at its use site,
  leaving an orphaned `LEGACY_PIPELINE.read_text()` line.
- **Fix:** removed the orphaned read line; re-ran the suite.
- **Files modified:** tests/test_run_finetune_contracts.py
- **Verification:** 64/64 green.
- **Committed in:** `dd4099a`

**3. [Rule 3 - Blocking] Task 2's purge scope had to extend to tests/test_known_defects.py**
- **Found during:** Task 2 (mention census)
- **Issue:** the plan's Task 2 <files> list omits tests/test_known_defects.py,
  but its docstring cites the legacy filename — Task 2's zero-grep gate
  over tests/ cannot pass with it present.
- **Fix:** docstring reworded to "the old monolithic pipeline script
  (itself deleted at Phase 7 per D-04 — git history is the reference)" —
  historical record preserved, grep satisfied.
- **Files modified:** tests/test_known_defects.py
- **Verification:** grep over tests/ returns 0; test_known_defects passes.
- **Committed in:** `96f20a6`

---

**Total deviations:** 3 auto-fixed (2 Rule-3 blocking, 1 Rule-1 bug)
**Impact on plan:** All three are transcription/purge-mechanics
reconciliations inside the plan's own gates; the end state matches the
plan's intent exactly (sha-documented verbatim literals, zero live
references, gates green). No scope creep.

## Prohibition Verification (flagged items)

- **.planning/milestones/ untouched** — `git diff --quiet HEAD --
  .planning/milestones/` prints archives-untouched at the Task 2 gate;
  `.planning/` generally saw zero edits from the deletion cleanup (the
  sanctioned STATE/ROADMAP/REQUIREMENTS updates follow this SUMMARY via
  gsd_run, not the cleanup).
- **Literals transcribed verbatim at the final commit** — every value was
  extracted with the test file's own helpers (`list_members` /
  `composed_members` / `dict_members` / the `determine_batch_size` regex)
  against the working tree identical to 1b74037e BEFORE editing, then
  byte-compared against the transcription; each block carries the
  sha-naming comment. Reviewed at phase verification.

## Flagged Assumption Carried Forward (plan frontmatter)

Reference-cleanup scope: AUDIT.md mentions were handled as "mark deleted,
keep records" (post-audit banner + untouched finding rows) per the plan's
flagged assumption — the audit rows' file/line citations now describe a
file that exists only in git history, which the banner states explicitly.

## Issues Encountered

None beyond the deviations above.

## Authentication Gates

None — no external services.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 07-06 (GB10 smoke, last plan of the phase): runs against a tree with no
  legacy file; the smoke's D-23 magnitude anchor and flops_report emission
  proof are unaffected by this plan (re-pinned contracts prove it — the
  suite is green with the file gone).
- Phase 8 (tui): .claude/CLAUDE.md's pipeline architecture sections are
  current again — future agents read flops_counter.py/run_finetune.py as
  the live surface, not a deleted file.
- PIPE-01 completes when 07-06's SUMMARY lands (shared-ID gate across
  07-01/07-04/07-05/07-06).

---
*Phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re*
*Completed: 2026-10-11*

## Self-Check: PASSED

- All key files exist on disk (9 modified + this SUMMARY); the legacy file is confirmed deleted
- Both production commits are ancestors of HEAD (`dd4099a`, `96f20a6`); measured `git rev-list --count 4e5fa69..HEAD` = 2 (docs close-out follows, = frontmatter's total)
- Plan-level verification re-run green: contracts 64/64, `make lint` exit 0 (all PHASE7 modules in the expansion), `make typecheck` exit 0, full `make test` 550 pytest passed + node lane 18/18, live-code grep 0, archives untouched
