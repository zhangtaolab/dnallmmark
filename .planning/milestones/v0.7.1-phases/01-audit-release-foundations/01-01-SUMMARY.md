---
phase: 01-audit-release-foundations
plan: "01"
subsystem: infra
tags: [uv, lockfile, pandas, numpy, sha256, git-tag, baseline, reproducibility, json-comparator]

requires: []
provides:
  - "Annotated git tag data-v1 freezing the pre-fix byte state of all 52 derived leaderboard JSONs (recoverable via git show data-v1:<path>)"
  - "baseline/compare.py — order-insensitive canonical JSON value comparator with 0/1/2 exit contract and --summary-json machine mode"
  - "baseline/data-v1.sha256 — 52-entry SHA256 integrity manifest of the derived outputs at tag time"
  - "Committed dependency substrate: pyproject.toml (PEP 621 + PEP 735 groups), uv.lock, requirements.txt export, .python-version (3.13)"
  - "baseline/PIN-VALIDATION.md — empirical D-05/D-06 pin-validation evidence with complete root-caused diff inventory"
affects: [01-02-audit, 01-03-determinism-fix, phase-2-tests, phase-5-ci]

actuals:
  tokens: 47210
  tasks: 2
  commits: 3

tech-stack:
  added:
    - "uv 0.12.23 + committed uv.lock (PEP 735 dependency groups: data/dev/pipeline)"
    - "pandas 2.3.3 (floor >=2.2,<3.0) + numpy 2.5.3 (floor >=2.0,<3) in the data group"
    - "CPython 3.13.16 uv-managed interpreter pin (.python-version)"
  patterns:
    - "PEP 735 dependency groups with GPU pipeline group excluded from default install (default-groups = [\"data\"])"
    - "tag + SHA256 manifest + comparator baseline freeze (no duplicated golden copies)"
    - "Order-insensitive canonical JSON value comparison with FLOAT_ULP/FLOAT_BIG tolerance bucketing (rel < 1e-12)"

key-files:
  created:
    - baseline/compare.py
    - baseline/data-v1.sha256
    - baseline/PIN-VALIDATION.md
    - pyproject.toml
    - uv.lock
    - requirements.txt
    - .python-version
  modified:
    - .gitignore

key-decisions:
  - "Baseline artifact form: annotated tag + tracked SHA256 manifest + tracked comparator, NO duplicated golden copies — git stores the exact bytes at the tag, the manifest proves integrity, 52 duplicated files would silently rot"
  - "Floor bounds (pandas>=2.2,<3.0, numpy>=2.0,<3) in pyproject with exactness supplied by the committed uv.lock — not exact pins in the manifest, per D-05"
  - "Comparator keeps explicit argv paths (repo-root tooling) unlike the CWD-relative data scripts; --summary-json added as the machine-readable contract plan 01-03's migration gate consumes"
  - "Third exact-tie pair (microbe file, 448.0) accepted into the diff inventory after investigation — same stable-sort listdir-fallback root cause as the two pre-documented pairs (D-06 discharged, not escalated)"

patterns-established:
  - "data-vN tag discipline: derived-data baselines are frozen as annotated tags + checksum manifests before any result-affecting change lands"
  - "Three-comparison taxonomy: byte (determinism) vs canonical value (pin validation) vs tolerant float (triage) — never conflated"
  - "Dependency groups split: data (CPU, CI-safe) / dev (Phase 2) / pipeline (GPU, never CI-installed)"

requirements-completed: [AUDIT-02, REL-02]

coverage:
  - id: D1
    description: "Order-insensitive canonical JSON value comparator (baseline/compare.py) with exit-code contract and complete-untruncated --summary-json diff inventory"
    requirement: AUDIT-02
    verification:
      - kind: other
        ref: "python3 baseline/compare.py dnallm-mark/data/tasks.json dnallm-mark/data/tasks.json → VALUES IDENTICAL, exit 0"
        status: pass
      - kind: other
        ref: "summary-mode contract asserts: identical pair total==0/diffs==[]/counts=={}; different pair exit 1 with total==len(diffs)==sum(counts.values())>8 (untruncated proven)"
        status: pass
      - kind: other
        ref: "missing file → exit 2 with readable message, no traceback; usage error → exit 2"
        status: pass
    human_judgment: false
  - id: D2
    description: "Pre-fix byte state frozen: 52-entry SHA256 manifest + annotated data-v1 tag, recoverability proven end-to-end"
    requirement: AUDIT-02
    verification:
      - kind: other
        ref: "wc -l baseline/data-v1.sha256 = 52; all paths dnallm-mark/data/-prefixed; zero model_performance entries"
        status: pass
      - kind: other
        ref: "sha256sum -c baseline/data-v1.sha256 → exit 0, no FAILED lines"
        status: pass
      - kind: other
        ref: "git cat-file -t data-v1 = tag; sha256(git show data-v1:dnallm-mark/data/tasks.json) = manifest value; tagged tree has 0 changes to script/, scripts/, dnallm-mark/data/ vs parent"
        status: pass
    human_judgment: false
  - id: D3
    description: "Pinned data-chain environment: pyproject groups, committed uv.lock, requirements.txt export, .python-version, .gitignore trap removed"
    requirement: REL-02
    verification:
      - kind: other
        ref: "git check-ignore uv.lock .python-version → empty; git ls-files shows all 4 manifest files"
        status: pass
      - kind: other
        ref: "uv lock --check → exit 0; single numpy/pandas package blocks in uv.lock"
        status: pass
      - kind: other
        ref: "requirements.txt autogenerated header + pandas==2.3.3/numpy==2.5.3 exact pins; uv sync installed only the 6-package data group (torch absent)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Pin-validation evidence recorded (baseline/PIN-VALIDATION.md): resolved versions, complete per-file diff inventory, root causes, D-06 conclusion"
    requirement: REL-02
    verification:
      - kind: other
        ref: "file present, contains FLOAT_ULP + pandas + explicit D-06 conclusion (authoritative pins)"
        status: pass
      - kind: other
        ref: "47/47 task_performance files VALUES IDENTICAL; all FLOAT_ULP on sum_zscore only (max rel 2.41e-14); FLOAT_BIG only on rank fields of exact-tie pairs; tasks.json diffs = metric casing + generatedAt"
        status: pass
    human_judgment: true
    rationale: "Root-cause acceptance of the diff inventory (especially the investigated third tie pair) is correctness judgment the automated file checks cannot prove — a reviewer should confirm the D-06 reasoning stands before the pins are treated as authoritative for external reproduction."

duration: 9min
completed: 2026-10-08
status: complete
commits: 3
plan_head_before: e475d612243ec7635611c732f36ad31895d3ca16
plan_head_after: 53cd7f67fe67f051e1e9dca0228a339b733e59a2
---

# Phase 01 Plan 01: Data Baseline Freeze + Environment Pins Summary

**Pre-fix derived-data baseline frozen (52-file SHA256 manifest + annotated `data-v1` tag + order-insensitive comparator) and the data-chain environment pinned via uv (pandas 2.3.3 / numpy 2.5.3 lockfile, PEP 735 groups) with D-05/D-06 pin validation evidence recorded in-repo.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-10-08T13:59:20Z
- **Completed:** 2026-10-08T14:08:10Z
- **Tasks:** 2
- **Files modified:** 8 (7 created, 1 edited)

## Accomplishments

- **Comparator shipped with the machine contract 01-03 depends on**: `baseline/compare.py` ports the research-validated walker with the required changes — dead-code MISSING_IN_REGEN branch simplified, 0/1/2 exit contract (2 = load/usage error with readable message), preserved diff vocabulary (TYPE/MISSING_IN_REGEN/EXTRA_IN_REGEN/LEN/FLOAT_ULP/FLOAT_BIG/BOOL/VALUE, rel threshold 1e-12 with the `abs(a-b)/max(abs(a),abs(b),1e-300)` formula), stdlib-only, and `--summary-json` mode emitting the complete untruncated inventory (`total == len(diffs) == sum(counts.values())`) while the human mode keeps its 8-line cap.
- **Pre-fix state frozen and proven recoverable**: 52-entry manifest (4 comparison files + tasks.json + 47 task_performance files, zero model_performance inputs), `sha256sum -c` exit 0, annotated `data-v1` tag whose tree contains the manifest and zero changes to `script/`, `scripts/`, or `dnallm-mark/data/`; `git show data-v1:dnallm-mark/data/tasks.json` hashes to the manifest value.
- **Reproducible CPU data chain**: pyproject with data/dev/pipeline groups (pipeline GPU-only, never CI-installed — verified torch absent from `.venv` after `uv sync`), committed `uv.lock` with exactly one numpy/pandas resolution, exported `requirements.txt` with exact pins + hashes, `.python-version` = 3.13, and the `.gitignore` `uv.lock`/`.python-version` trap removed in the same commit (Pitfall 1).
- **D-05/D-06 pin validation executed and recorded**: full 3-script chain regenerated in a scratch mirror with the pinned env; 47/47 task files value-identical; every observed diff root-caused (sum_zscore ULP noise ≤ 2.41e-14, exact-tie rank swaps, tasks.json metric-casing + generatedAt); run-twice byte-identity confirmed.

## Task Commits

Each task was committed atomically:

1. **Task 1: Freeze the pre-fix state — comparator, SHA256 manifest, data-v1 tag** - `788e909` (feat) — plus annotated tag `data-v1` on that commit
2. **Task 2: Pin the data-chain environment** - `60bbe6c` (chore: pyproject/uv.lock/requirements.txt/.python-version/.gitignore) + `53cd7f6` (docs: PIN-VALIDATION.md)

**Plan metadata:** *(final docs commit follows)*

## Files Created/Modified

- `baseline/compare.py` — order-insensitive JSON value comparator; CLI `python3 baseline/compare.py [--summary-json] <committed> <regen>`; exit 0/1/2
- `baseline/data-v1.sha256` — SHA256 manifest of the 52 derived outputs at tag time
- `baseline/PIN-VALIDATION.md` — pin-validation evidence: commands, resolved versions, complete diff inventory, root causes, D-06 conclusion
- `pyproject.toml` — PEP 621 project + PEP 735 groups (data/dev/pipeline) + `[tool.uv]` package=false, default-groups=["data"]
- `uv.lock` — committed lockfile (60 packages across all groups, single numpy/pandas resolution)
- `requirements.txt` — uv export of the data group (exact pins + hashes)
- `.python-version` — single line `3.13`
- `.gitignore` — removed the `uv.lock` and `.python-version` lines only

## Decisions Made

- Baseline artifact form (CONTEXT.md discretion item): tag + tracked manifest + tracked comparator, no duplicated golden copies — per RESEARCH "Don't Hand-Roll" and Alternatives analysis.
- Comparator CLI keeps explicit argv paths (repo-root tooling), deliberately unlike the CWD-relative data scripts.
- The microbe-file tie pair was accepted into the inventory after investigation rather than escalated (see Deviations) — D-06's investigate-and-document path, not a blocking stop.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Investigation] Third exact-tie pair outside the plan's literal diff inventory**
- **Found during:** Task 2 (pin validation)
- **Issue:** The plan's expected inventory named "exactly the two exact-tie pairs" (both in the global `models_comparison.json`). The validation run surfaced a third pair in `models_comparison_microbe.json`: `agro-nucleotide-transformer-1b` ↔ `plant-dnamamba2-BPE` swapping rank 2↔3.
- **Fix:** Investigated per D-06 before declaring pins authoritative: confirmed both models carry `rank_score = 448.0` exactly in BOTH the committed and regenerated microbe files — an exact tie whose order is decided by the same stable-sort → `os.listdir` insertion-order fallback mechanism as the pre-documented pairs (per-species arenas re-rank subsets, exposing ties the global file does not). Root cause identical; no new failure class.
- **Files modified:** `baseline/PIN-VALIDATION.md` (dedicated "Inventory investigation" section)
- **Verification:** Tie values quoted from both file sides; the pair's `sum_zscore` deltas fall inside the ULP noise band; no other diff outside the taxonomy exists in any of the 52 files.
- **Committed in:** `53cd7f6`

---

**Total deviations:** 1 auto-fixed (Rule 1 investigation, documented in-repo)
**Impact on plan:** None on deliverables — the plan's own D-06 procedure prescribed investigate-and-document; the investigation strengthened the evidence rather than changing any artifact decision.

## Issues Encountered

None — uv resolution, export, regeneration, and all verification checks passed on first attempt. (One transient: an initial run-twice check used inconsistent snapshot paths and was redone with absolute paths; no repo state was affected.)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The `data-v1` baseline is frozen and machine-verifiable; plan 01-03 (FIX-05 determinism) can now land its single byte-layout change with before/after attribution against the tag + manifest.
- Plan 01-02 (audit) runs against the same frozen pre-fix state.
- The `--summary-json` comparator contract 01-03's migration gate consumes is committed and proven untruncated on a >8-diff file pair.
- No blockers. The pinned env resolves stably (`uv lock --check` exit 0) and regenerates 47/47 task files value-identically.

## Self-Check: PASSED

All 8 key files exist on disk; all 3 task commits (`788e909`, `60bbe6c`, `53cd7f6`) are ancestors of HEAD; annotated tag `data-v1` present. Measured commits from ledger: `git rev-list --count e475d61..HEAD` = 3, matching frontmatter.

---
*Phase: 01-audit-release-foundations*
*Completed: 2026-10-08*
