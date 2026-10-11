---
phase: 01-audit-release-foundations
fixed_at: 2026-10-08T16:02:13Z
review_path: .planning/phases/01-audit-release-foundations/01-REVIEW.md
iteration: 1
findings_in_scope: 15
fixed: 13
skipped: 2
status: partial
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-10-08T16:02:13Z
**Source review:** .planning/phases/01-audit-release-foundations/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 15 (0 Critical, 9 Warning, 6 Info; fix_scope = all)
- Fixed: 13
- Skipped: 2 (both number-changing by design — deferred to their roadmap phases per the milestone's fix discipline)

**Execution environment:** all edits, commits, and verification gates ran inside the isolated
worktree `.claude/worktrees/rf-01-607078-1791474559` (branch `gsd-reviewfix/01-607078`, created
from `autorun` at `c96dd92`), fast-forwarded back to `autorun` on completion. The regeneration
gates used the main checkout's pinned `.venv` interpreter (CPython 3.13.16, numpy 2.5.3,
pandas 2.3.3) over scratch mirrors in `/tmp`, following the exact procedure documented in
`baseline/PIN-VALIDATION.md`. After worktree teardown the results are reproducible from the
merged commits on `autorun`.

## Fixed Issues

### WR-01: Live Zenodo preview JWT committed in public README — residual risk untracked

**Files modified:** `README.md`, `.planning/ROADMAP.md`
**Commit:** ff11bb1
**Applied fix:** Kept the D-08 decision untouched. Added an HTML comment directly above the
`README.md` Zenodo link marking it load-bearing (points at AUDIT.md D-08, states that any
change must update the `.gitleaks.toml` allowlist in the same commit). Added a tracked
follow-up as Phase 6 success criterion 6 in `.planning/ROADMAP.md`: replace the link with the
published record DOI/URL once record 19135551 is public and remove/update the allowlist rule in
the same commit.

### WR-02: README says Python 3.11+ while the repo pins >=3.13

**Files modified:** `README.md`
**Commit:** 1dbe5ee
**Applied fix:** Badge now reads `Python 3.13+`; the Prerequisites entry reads
"Python 3.13+ (data toolchain — see `.python-version`; the GPU pipeline has its own
requirements)" — matching `pyproject.toml:7` (`>=3.13`) and `.python-version` (3.13).

### WR-03: `baseline/compare.py` diff ordering is nondeterministic across processes

**Files modified:** `baseline/compare.py`
**Commit:** bc531e6
**Applied fix:** All three set iterations in `walk()` (`set(a) - set(b)`, `set(b) - set(a)`,
`set(a) & set(b)`) now iterate in `sorted()` order; docstrings updated to state the diff
sequence is process-independent. Verified: `--summary-json` output is byte-identical across
`PYTHONHASHSEED` 1/2/3/4 on a fixture with MISSING/EXTRA/FLOAT/VALUE/LEN diffs; counts, total,
and exit codes unchanged; diff vocabulary and exit contract untouched.

### WR-04: `baseline/compare.py` cannot detect int↔float type drift and false-positives on NaN

**Files modified:** `baseline/compare.py`
**Commit:** f3425a6
**Applied fix:** Numeric branch now (a) reports equal-value int/float asymmetry (committed `5`
vs regen `5.0`) as an existing-vocabulary `TYPE` diff instead of silence, and (b) treats `NaN`
on both sides as identical (early return) instead of a spurious `FLOAT_BIG`. `import math`
added; module docstring updated (TYPE bullet + NaN note). Behavior suite: 5 vs 5.0 → TYPE;
5 vs 5.5 → FLOAT_BIG (unchanged); NaN/NaN → exit 0; NaN vs 1.0 → FLOAT_BIG; bool cross-type
→ BOOL (unchanged); real-data self-compare → exit 0. No new diffs appear on real data — the
post-fix full-chain regeneration (below) is byte-identical, so no int/float asymmetry exists
between committed and regenerated values.

### WR-07: Documented output filenames are plural; the generator writes singular (AUD-19)

**Files modified:** `README.md`, `script/summarize_comparison.py`
**Commit:** a8854b7
**Applied fix:** `models_comparison_animals.json`/`models_comparison_plants.json` →
`models_comparison_animal.json`/`models_comparison_plant.json` in the README "This will
generate" list and the module docstring output-files list. `grep` confirms no plural
references remain in README or any generator.

### WR-08: gitleaks allowlist path regex is unanchored — broader than the documented intent

**Files modified:** `.gitleaks.toml`
**Commit:** d14c9bd
**Applied fix:** `paths = ['''^README\.md$''']` (anchored), with a config comment explaining
why. Canary pair re-run with gitleaks 8.30.1: (A) a 19135551-shaped preview link in
`docs/README.md` is now CAUGHT (was silently suppressible before the anchor); (B) a
different-record link in top-level `README.md` is CAUGHT; (C) the real top-level README is
still SUPPRESSED (exit 0) in relative-path modes — `detect --no-git --source .` and the
production `gitleaks git --log-opts="--all"` full-history scan (exit 0). One documented
residual: `detect --no-git --source /absolute/path` reports absolute file paths, which the
anchor deliberately does not match — the intentional link surfaces visibly there (fail-loud
toward AUDIT.md D-08, never a silent over-suppression). Noted in the config comment.

### WR-09: README's data-regeneration docs omit the third generator entirely

**Files modified:** `README.md`
**Commit:** 51500a9
**Applied fix:** Added a "Generate Task Index" subsection (`node scripts/generate-tasks-index.js`
from repo root, why/when to regenerate, plus a note spelling out the full 3-step chain and the
CWD requirement of the two Python scripts); added `scripts/` to the Project Structure tree and
`tasks.json` to the data subtree; corrected the Node prerequisite to "only for the task-index
generator and the optional `npx http-server` fallback — the web interface itself is static".

### IN-01: Dead counter variable

**Files modified:** `script/summarize_comparison.py`
**Commit:** 0a8fb63
**Applied fix:** Deleted `cnt = 0` and `cnt += 1` (never read).

### IN-02: Metric-presence check is narrower than `get_float`'s missing-value semantics

**Files modified:** `script/summarize_comparison.py`
**Commit:** d5901ef
**Applied fix:** `raw_score = get_float(..., default=None)` and the ranking gate is now
`if raw_score is not None` — presence is derived from the same helper that defines
missing-value semantics (`None`, `""`, whitespace-only), so a null or whitespace metric can no
longer enter ranking as a real `0.0`. **No derived number changed:** full-chain regeneration
with the edited script reproduces all 4 comparison files and all 47 task files plus `tasks.json`
byte-identically (52/52 `cmp`-identical). Behavioral proof: a synthetic 3-model fixture with
`null` and `"   "` metric values ranks only the model with a real metric (previously all three
were ranked, the missing ones at 0.0).

### IN-03: No per-file error handling in the index generator

**Files modified:** `scripts/generate-tasks-index.js`
**Commit:** ffeb247
**Applied fix:** Per-file `readFileSync`/`JSON.parse` wrapped in try/catch; malformed files log
`` [Skip] Failed to read file <name>: <message> `` (matching the Python generators' convention)
and are filtered out of the index instead of aborting the build. Verified with a fixture
containing one malformed + one valid task file: build completes, index contains exactly the
valid task.

### IN-04: Double spaces in generated task display names

**Files modified:** `scripts/generate-tasks-index.js`, `dnallm-mark/data/tasks.json`
**Commit:** 9fcf200
**Applied fix:** `taskId.replace(/_+/g, ' ').trim()` collapses underscore runs, then
`tasks.json` was **regenerated through the fixed generator in-place** (committed generator and
committed data stay consistent — the property the Phase 5 drift gate will enforce).
`baseline/compare.py` between the previous and regenerated `tasks.json`: exactly 47 `VALUE`
diffs, every one on a `/tasks/N/displayName` path; no other field moved. Note for the record:
relative to the frozen pre-fix baseline (`data-v1` / PIN-VALIDATION.md's 2 documented VALUE
diffs), `tasks.json` now carries 47 additional intentional displayName diffs — a display-only
change sanctioned by the phase's fix scope; all 47 display names are now single-spaced.

### IN-05: `top8_count` missing from README's documented output fields

**Files modified:** `README.md`
**Commit:** b09d70e
**Applied fix:** `top8_count` added to the output-fields list (now top1/3/5/8/10).

### IN-06: `.gitignore` carries upstream-dnallm rules for paths that do not exist here

**Files modified:** `.gitignore`
**Commit:** 999e218
**Applied fix:** Removed the upstream blocks for absent paths (`dnallm/models/downloads/`,
`dnallm/data/cache/`, `dnallm/ui/tmp/`, `example/notebooks/`, `example/marimo/`, Mkdocs `site`,
`test|tests/inference/pdf/` PDF list, `Arena/`, `instruct/`, `*.output.txt`) and the duplicate
`.DS_Store`, `.ipynb_checkpoints/`, `.marimo-cache/`, `.marimo-env/` entries; the real
project-specific entries (`datasets/`, `models/`, `finetuned/`) now sit under a
`# Project specific` header. 131 → 99 lines. Verified with `git check-ignore` against real
temp directories: `datasets/`, `models/`, `finetuned/`, `pipeline/logs/`, `__pycache__/`,
`.pytest_cache/`, `.ruff_cache/`, `.venv`, `.DS_Store` all still ignored; `git status` shows
nothing newly tracked.

## Skipped Issues

### WR-05: `sum_PFLOPs`/`avg_PFLOPs` include FLOPs from tasks the model is not ranked on

**File:** `script/summarize_comparison.py:221-225`, `script/summarize_comparison.py:363-365`
**Reason:** skipped: number-changing aggregation semantics — deferred to a later roadmap phase
per this phase's fix discipline. Gating FLOPs accumulation on metric presence changes
`sum_PFLOPs`/`avg_PFLOPs` for at least GENERanno-eukaryote-0.5b-base, GENERanno-prokaryote-0.5b-base,
and PlantCaduceus_l32 in the shipped public files; such a change requires a documented
before/after recomputation (Phase 5's DATA-01..03 migration machinery), not a review drive-by.
The alternative fix branch (documenting the "compute spent including failed evaluations"
semantics) is also a semantics decision that should be made together with the gate change.
**Original issue:** FLOPs are accumulated whenever the model appears in the FLOPs map while
ranking inclusion requires a non-empty primary metric; the two rules diverge on 9 real
model×dataset pairs, so efficiency metrics and rank scores use different task sets for 3 of 42
models on the public scatter chart.

### WR-06: Dataset species labels contradict the datasets' own identity (fungi → Animals, human cell line → Microbe)

**File:** `dnallm-mark/data/tasks.json:50-58`, `dnallm-mark/data/tasks.json:149`, and the same values in all 42 `model_performance` inputs and the arena files
**Reason:** skipped: number-changing species relabeling — belongs to the Phase 4 species work
(AUD-01/FIX-02), which this review itself says should cover label correctness, not just the
pipeline's species source. Moving `GUE__fungi_species_20` out of the animal arena or
`GUE__EPI_GM12878` out of the microbe arena re-ranks every model inside those arena files;
that must go through the test-first fix and the documented before/after recomputation, not a
review drive-by. Recorded here so Phase 4's species audit includes it (the ROADMAP Phase 4
species criterion is the tracking home).
**Original issue:** the species label is identical across all 42 input files (derived data is a
faithful projection), but the input labels contradict dataset identity: a 20-way fungi species
task grouped into Animals, a human lymphoblastoid cell line (GM12878) grouped into Microbe;
`GUE__emp_*` → Microbe warrants the same verification.

## Verification Summary

All gates ran in the isolated worktree (branch `gsd-reviewfix/01-607078`); the regeneration
chain used scratch mirrors in `/tmp` with the main checkout's pinned `.venv` (CPython 3.13.16,
numpy 2.5.3, pandas 2.3.3) per the PIN-VALIDATION.md procedure.

- **Syntax/parse:** `ast.parse` on both edited Python files; `node --check` on the edited JS;
  `tomllib.load` on `.gitleaks.toml`; all pass.
- **Full-chain byte-determinism (post IN-01/IN-02 and again on the final state):**
  `summarize_comparison.py` → `get_task_performance.py` → `generate-tasks-index.js` over the 42
  committed `model_performance` inputs reproduces all 52 derived files byte-identically
  (IN-04's regenerated `tasks.json` included) — no derived number changed in this fix round
  except the sanctioned displayName strings.
- **Comparator behavior:** 4-seed PYTHONHASHSEED determinism check plus a 6-case behavior
  suite on `baseline/compare.py` (see WR-03/WR-04).
- **Secret scan:** gitleaks 8.30.1 canary pair re-run in both directions + production
  full-history scan exit 0 on the final tree (see WR-08).
- **Worktree clean:** `git status` empty after the last commit; 13 atomic `fix(01):` commits
  from `ff11bb1` to `999e218`.

---

_Fixed: 2026-10-08T16:02:13Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
