---
phase: 01-audit-release-foundations
reviewed: 2026-10-08T16:49:42Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - .gitignore
  - .gitleaks.toml
  - README.md
  - baseline/compare.py
  - dnallm-mark/data/tasks.json
  - script/summarize_comparison.py
  - scripts/generate-tasks-index.js
findings:
  critical: 0
  warning: 3
  info: 4
  total: 7
status: issues_found
---

# Phase 01: Code Review Report (incremental re-review of WR-07..09 / IN-01..06 fix commits)

**Reviewed:** 2026-10-08T16:49:42Z
**Depth:** standard
**Files Reviewed:** 7 (exactly the files changed since the prior full-phase review at commit 6087657)
**Status:** issues_found (0 critical, 3 warnings, 4 info)

## Summary

This re-review covers only the delta since the prior full-phase review: the seven files touched by the WR-07..09 and IN-01..06 fix commits. Every fix was re-verified adversarially, with empirical execution where possible rather than code reading alone. Prior-review findings whose disposition is tracked in `01-REVIEW-DISPOSITION.md` (e.g., the Zenodo token's documented acceptance, the fungi/human species mislabels deferred to Phase 4, the `sum_PFLOPs` task-set divergence) are not re-raised here.

**Verified clean (evidence-backed):**

- `script/summarize_comparison.py` (IN-02 fix): regenerated all four comparison files from the real `model_performance/` inputs with the project venv — **value-identical** to the committed files per `baseline/compare.py` (`total: 0` diffs each). Also regenerated with the pre-fix code (at 6087657): **identical output** — all 8,193 missing-metric values in the real data are plain `""`, which both versions exclude, so the stricter `raw_score is not None` gate is purely defensive and changed no shipped numbers (no before/after documentation obligation triggered). Metric `0`/`0.0` values remain correctly included.
- `scripts/generate-tasks-index.js` (IN-03/IN-04 fixes): simulated generator output against `task_performance/` is **byte-identical** to the committed `tasks.json` (47/47 files, `count` correct, every entry's `species`/`type`/`labels`/`length`/`metric` matches its source file, display names match the collapsed-underscore regex). The per-file `[Skip]` handler is correct (`return null` + filter).
- `.gitleaks.toml` (WR-08 fix): empirically verified with gitleaks 8.30.1 — `git` scan of recent commits reports no leaks (relative path `README.md` matches `^README\.md$`); `detect --no-git --source <abs>` surfaces the intentional link (fail-loud, as documented); the same link in `docs/README.md` is detected (anchor works); a token on a different record ID is detected; the built-in `jwt` rule indeed misses `)`-closed link tokens, confirming the custom rule is load-bearing.
- `baseline/compare.py` (WR-04/WR-05 fixes): diff output is byte-identical across `PYTHONHASHSEED=1` and `PYTHONHASHSEED=4242`; equal-value int/float asymmetry (`5` vs `5.0`) now reports `TYPE`; `NaN` vs `NaN` compares identical; `len(diffs) == total == sum(counts.values())` invariant holds.
- `.gitignore` (IN-06 fix): every removed rule targets a path absent from the tree (`dnallm/`, `example/`, `Arena/`, `instruct/`, `tests/`, `site/`, `test/inference/`); no previously-ignored real file became untracked; `datasets/`, `models/`, `finetuned/`, `logs/` still cover all four `pipeline/` output paths (verified with `git check-ignore`).
- `README.md` (WR-07/WR-09/IN-05 + Python-badge fixes): singular filenames match `to_singular_species()` output and the files on disk; the documented regeneration chain is accurate and ordered; `top8_count` now documented; Python 3.13 badge/prereq matches `pyproject.toml` (`requires-python >= 3.13`), `.python-version` (`3.13`), and the documented dependency groups (`data`/`dev`/`pipeline` all exist in `pyproject.toml`). All files referenced in the project-structure section exist.

The remaining findings are hardening gaps in or adjacent to the just-fixed code paths — none contradict a prior disposition, and none change shipped numbers.

## Warnings

### WR-01: gitleaks allowlist is record-scoped, not token-scoped — any swapped JWT in the known link position is silently suppressed

**File:** `.gitleaks.toml:24-35`
**Issue:** The rule-level allowlist suppresses findings where the path is `^README\.md$` AND the match contains `zenodo.org/records/19135551?preview=1&token=`. The token *value* is not pinned, so suppression covers **any** JWT placed in that exact URL shape in top-level README.md — not just the D-08 token. Empirically verified with gitleaks 8.30.1: substituting a different (valid-shaped) HS256 JWT into the record-19135551 link in a top-level `README.md` produced **zero findings** under the repo config; combined with the empirically confirmed fact that the built-in `jwt` rule misses `)`-closed link tokens, the scanner is completely blind to a token swap in that position. The only guard is the README's "any change here must update that allowlist in the same commit" comment — process, not enforcement. (Context: no CI workflow exists yet, so the config is currently manual-only; Phase 2 is planned to wire it in.)
**Fix:** Pin the known token in the allowlist regex so a rotated or replaced token stops matching and surfaces, e.g. extend `regexes` to:

```toml
regexes = ['''zenodo\.org/records/19135551\?preview=1&token=eyJhbGciOiJIUzUxMiJ9\.eyJpZCI6ImVhYzE2MTJmLWQzZDMtNDMxZC04ZTc3LTkyNzk1MTQzMmIxOCI\.''']
```

(header + payload prefix of the exact D-08 token). Any future token fails the AND-condition, is reported, and forces the deliberate allowlist update the README comment already promises.

### WR-02: `compare.py` treats equal-value bool/int cross-type pairs as identical — silent false-negative against live pinned data

**File:** `baseline/compare.py:90-98`
**Issue:** When exactly one side is a `bool`, the diff is emitted only if `a != b`. Because Python's `True == 1` and `False == 0` (and `True == 1.0`), a committed `true` regenerating as `1` (or `1.0`) — a real JSON type change — passes silently. Empirically verified: comparing `{"flag": true, "n": 5}` vs `{"flag": 1, "n": 7}` reports only the `/n` diff. This is inconsistent with the file's own contract: the docstring's `BOOL` class is defined as "bool/int cross-type value mismatch" and the just-added `TYPE` semantics explicitly cover *equal-value* int/float asymmetry for the numeric case. The gap is live, not hypothetical: **all 47 pinned `task_performance` files carry boolean `parameters.bf16` / `parameters.fp16` fields** (89 data files contain booleans overall), so a producer change that serializes those flags as ints would pass the pin-validation gate this tool exists to enforce (decision D-06).
**Fix:** Report `BOOL` whenever bool-ness differs, regardless of value equality:

```python
if isinstance(a, bool) or isinstance(b, bool):
    if a != b or isinstance(a, bool) != isinstance(b, bool):
        diffs.append(("BOOL", path, f"{type(a).__name__} vs {type(b).__name__}: {a} vs {b}"))
    return
```

### WR-03: Non-finite metric values (`"nan"`, `NaN`, `"inf"`) pass the presence gate and poison an entire task's normalization

**File:** `script/summarize_comparison.py:352-364` (with `get_float` at lines 80-96)
**Issue:** The IN-02 fix derives presence from `get_float(..., default=None)` — but `float("nan")` and `float("inf")` succeed, so a metric value of `"nan"` (a string ML eval harnesses do emit on failed runs) or a JSON `NaN` literal returns a non-`None` non-finite float, passes `if raw_score is not None`, and enters `calculate_dataset_stats`. There, NaN propagates through `np.percentile`/`minmax`/`zscore`/`robust` to **every** model on that task (verified semantics of the numpy calls at lines 139-149), and `json.dump` then writes bare `NaN` literals — invalid strict JSON that breaks the frontend's `JSON.parse` and other strict consumers. Verified there are currently **0** non-finite metric values in the 42 input files, so nothing shipped is affected today; this is a latent single-value corruption vector in exactly the presence-gating code this fix hardened.
**Fix:** Treat non-finite conversions as missing:

```python
raw = get_float(...)  # after conversion, before inclusion
if raw_score is not None and not math.isfinite(raw_score):
    raw_score = None  # or log a [Skip]-style warning naming the file/dataset/metric
```

## Info

### IN-01: Pure-integer differences are classified as `FLOAT_BIG`

**File:** `baseline/compare.py:107-111`
**Issue:** An int-vs-int difference (committed `5` vs regen `7`, verified: reported as `[FLOAT_BIG] /n: 5 vs 7 rel=2.86e-01`) falls through to the relative-delta branch, whose classes the docstring defines as *float* diffs. Exit code and totals are still correct, so this is misclassification, not a missed diff — but a machine-mode consumer filtering on `FLOAT_*` to mean "numeric noise vs real change" gets float semantics for an int-type change.
**Fix:** Branch on `isinstance(a, float) or isinstance(b, float)` and emit a distinct class (e.g. `INT`/`VALUE`) for non-float numerics, or redefine the docstring's `FLOAT_ULP`/`FLOAT_BIG` as "numeric" classes.

### IN-02: Index generator crashes with a raw stack trace when `task_performance/` is missing

**File:** `scripts/generate-tasks-index.js:18`
**Issue:** `fs.readdirSync(TASK_PERFORMANCE_DIR)` sits outside the per-file try/catch this fix added. A missing/renamed directory (plausible right after a fresh clone without generated data) aborts with an unhandled `ENOENT` stack trace — inconsistent with the `[Skip]` convention the same fix established and with `summarize_comparison.py`'s friendly `Error: Could not find input directory` path.
**Fix:** Guard the directory up front:

```js
if (!fs.existsSync(TASK_PERFORMANCE_DIR)) {
  console.error(`Error: Could not find task performance directory '${TASK_PERFORMANCE_DIR}'`);
  process.exit(1);
}
```

### IN-03: README "Output fields" still omits `avg_PFLOPs`

**File:** `README.md:252-261`
**Issue:** The IN-05 fix added `top8_count` to the documented output fields, but `avg_PFLOPs` — emitted by `script/summarize_comparison.py:253` and present in all 42 entries of the shipped `models_comparison.json` — is still undocumented, while its sibling `sum_PFLOPs` is listed.
**Fix:** Add `- avg_PFLOPs - Average computational cost in PetaFLOPs (tasks with FLOPs > 0)` to the Output fields list.

### IN-04: `.planning/tmp/` GSD scratch is untracked noise in `git status`

**File:** `.gitignore` (end of file)
**Issue:** `.planning/tmp/` (GSD workflow scratch, e.g. `01-failing-directions.json`, `01-verify-paths.json`) shows as untracked in `git status` alongside real changes, creating accidental-commit risk under `git add -A` flows — the same class of noise the IN-06 trim aimed to eliminate. The rest of `.planning/` is deliberately tracked, so a targeted entry is needed rather than ignoring the directory.
**Fix:** Append `.planning/tmp/` to `.gitignore` (or whichever scratch location GSD is configured to use).

---

_Reviewed: 2026-10-08T16:49:42Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (incremental re-review; scope = 7 files changed since 6087657; empirical verification: gitleaks 8.30.1 sandbox tests, compare.py edge-case runs across PYTHONHASHSEED values, full data regeneration old-vs-new with the project venv, generator simulation against `task_performance/`)_
