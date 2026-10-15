---
phase: quick-261015-h8i
plan: 01
subsystem: dependencies
tags: [dependencies, uv, modelscope, data-group, pyproject, lock, docs]
requires:
  - "2026-10-14 ModelScope-first ruling (modelscope as default download channel)"
  - "01-01 (the pyproject/uv.lock/requirements.txt pin chain + PIN-VALIDATION evidence discipline)"
  - "10-06 (resolve_modelscope_cli venv-sibling-then-PATH contract in tui/services/download_queue.py)"
provides:
  - H8I-1 `uv sync` on a fresh clone installs a working `modelscope` console script (>=1.40,<2 in the data group; resolved 1.40.2 + modelscope-hub 0.4.6) — zero manual install steps remain anywhere
  - H8I-2 re-lock changes zero existing resolutions (pandas 2.3.3 / numpy 2.5.3 byte-unchanged, D-05 bounds untouched); requirements.txt is the exact `uv export --group data --no-emit-project` artifact of the new lock (hashes + via-tree)
  - doc sync: GETTING-STARTED prereq + cli_unavailable remedy, DEVELOPMENT import-seam parenthetical, PIN-VALIDATION dated addendum (new 98-block count)
affects:
  - pyproject.toml, uv.lock, requirements.txt
  - docs/GETTING-STARTED.md, docs/DEVELOPMENT.md, baseline/PIN-VALIDATION.md
tech-stack:
  added:
    - "modelscope>=1.40,<2 (data group; resolved 1.40.2) + modelscope-hub 0.4.6 + cffi 2.1.1 / cryptography 50.0.2 / pycparser 3.11 transitives"
  patterns:
    - "bounded pin per D-05 convention, floor = box-validated 1.40.2 (the pandas/numpy precedent)"
    - "CLI-only dependency: installed by the group, never imported in-process (the AST import guard in tests/tui/test_services_download_queue.py still holds)"
key-files:
  created: []
  modified:
    - pyproject.toml
    - uv.lock
    - requirements.txt
    - docs/GETTING-STARTED.md
    - docs/DEVELOPMENT.md
    - baseline/PIN-VALIDATION.md
decisions:
  - "modelscope bound >=1.40,<2 (D-05-style bounded pin, 1.40.2 box-validated floor) rather than exact == pin — house convention for the data group floors with the lock freezing exact versions"
  - "uv sync --inexact used for the box venv (deviation below): plain exact sync would strip the GB10 GPU stack + manual dnallm per the recorded 08-02 decision; a fresh clone's plain `uv sync` still installs modelscope identically"
metrics:
  duration: 8 min
  completed: 2026-10-15
status: complete
actuals:
  tokens: 16700   # 66,891 diff chars / 4 over the two code commits (6dbefd2..HEAD)
  tasks: 3
  commits: 2
---

# Quick Task 261015-h8i: modelscope into the core data group — Summary

**One-liner:** `modelscope>=1.40,<2` joined the pyproject `data` group (resolved 1.40.2 + modelscope-hub 0.4.6, lock 93→98 blocks, pandas 2.3.3 / numpy 2.5.3 byte-unchanged), requirements.txt re-exported with hashes, and every doc that taught manual acquisition now points at `uv sync`.

## What was done

### Task 1 — pyproject + lock + export + sync (commit e36439f)

- Added `"modelscope>=1.40,<2",` to `[dependency-groups] data` after the evaluate line, with a house-style comment block recording the maintainer 2026-10-15 directive, the venv-sibling-then-PATH console-script resolution in `tui/services/download_queue.py`, the pure-Python/no-GPU-weight CI acceptance, the deliberate dnallm-stays-manual boundary, and the D-05 bounded-pin convention with the 1.40.2 floor.
- `uv lock`: resolved cleanly, no conflict — Added modelscope 1.40.2, modelscope-hub 0.4.6, cffi 2.1.1, cryptography 50.0.2, pycparser 3.11 (93 → 98 `[[package]]` blocks). Nothing else moved.
- `uv export --group data --no-emit-project -o requirements.txt`: both packages present with sha256 hashes and via-annotations.
- `uv sync --inexact` (see deviation): modelscope 1.40.2 was already present at exactly the locked version, so the manual install formally became the group install; `.venv/bin/modelscope` stayed linked.
- `uv lock --check` exits 0. Full Task 1 verify chain printed `TASK1-OK`.

### Task 2 — acquisition-doc sync (commit 3ebb2ca)

1. GETTING-STARTED "Download prerequisites" bullet: now states the console script ships in the data group — `uv sync` installs it (venv-sibling resolution, then PATH fallback) — while model downloads still need the external `dnallm` (manual, sibling clone).
2. GETTING-STARTED `cli_unavailable` troubleshooting entry: remedy is now "Re-run `uv sync` — modelscope ships in the pyproject data group…" (the `python -m modelscope` has-no-`__main__` explanation kept verbatim).
3. DEVELOPMENT download-subprocess-seam bullet: parenthetical now states modelscope has shipped in the `data` group since 2026-10-15 (`uv sync` installs it) while the service-module never-imports-in-process invariant, the AST guard `test_service_module_never_imports_modelscope`, and the manual-GPU-side dnallm statement are unchanged. No other sentence in the bullet touched.
4. PIN-VALIDATION: appended `## Addendum (2026-10-15): modelscope joins the data group` — directive, resolved versions, `uv lock --check` pass, unchanged pandas/numpy verdicts (grepped from the new lock), the console-script consequence, and the new 98-block count (supersedes the 2026-10-08 count of 60; the intervening 60→93 growth is the Phase 2-12 dev/tui/gpu group additions). The 2026-10-08 evidence body is untouched (historical record). D-06 re-validation trigger not tripped.

Stale-phrase verify: `uv pip install modelscope` gone from GETTING-STARTED, `modelscope is in no uv group` gone from DEVELOPMENT, `data group` present, addendum found at PIN-VALIDATION.md:134 — `DOCS-OK`.

### Task 3 — full gates (no files changed; evidence only)

| Gate | Result |
|------|--------|
| `make lint` (ruff) | All checks passed |
| `make typecheck` (ty) | All checks passed |
| `node --test tests/js/*.test.js` | 26 pass / 0 fail |
| `uv run --group dev --group tui pytest --tb=no -q` | **7 failed, 1786 passed, 9 xfailed in 279.48s** — the exact documented box baseline (planning observation: same counts in 279.53s); zero errors, zero xpassed (tokenized per the plan's grep chain → `ALL-GATES-GREEN`) |

The pytest lane ran through `uv run`, so it consumed the new lock (auto-sync; the post-change environment). The failing 7 are the documented set (determinism chain, five schema pins, the machine-state storage-overview pin); the 9 xfailed are the strict-xfail SVG goldens.

**CI needs zero workflow edits:** every ci.yml lane reaches packages only through `uv run` auto-sync of the data group, so modelscope installs automatically; the drift lane (`make data` + `git diff --exit-code`) is unaffected because the derived-data chain does not import modelscope.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `uv sync --inexact` instead of plain `uv sync` (Task 1)**
- **Found during:** Task 1 sync step
- **Issue:** The plan's literal `uv sync` performs an *exact* sync of the data group only — on the maintainer's GB10 venv it would strip the GPU stack (torch/transformers) and the deliberately manual `dnallm` sibling-clone install, which no make lane can restore. This exact hazard is a recorded decision (08-02, STATE.md: "uv sync for the tui group must use --inexact (plain sync is exact and strips the GB10 GPU stack + dnallm)").
- **Fix:** Ran `uv sync --inexact`. Same end-state for the plan's purpose — the venv formally carries modelscope via the group at the locked version (already present at 1.40.2, console script linked) — without the collateral removal. A fresh clone's plain `uv sync` (the doc-facing instruction) installs modelscope identically; H8I-1 is unaffected.
- **Files modified:** none (command-level deviation)
- **Commit:** n/a (within Task 1)

**2. [Rule 1 - Bug] Task 2 verify initially failed the `data group` grep**
- **Found during:** Task 2 verification
- **Issue:** First wording used backticks around `data` ("the pyproject `data` group"), which breaks the contiguous `data group` phrase the plan's verify greps for.
- **Fix:** Reworded the troubleshooting bullet to "ships in the pyproject data group" (plain). Re-verify: `DOCS-OK`.
- **Files modified:** docs/GETTING-STARTED.md
- **Commit:** 3ebb2ca (folded into Task 2's commit)

## Verification Results

- Task 1: `TASK1-OK` — `uv lock --check` exit 0; `modelscope==1.40.2` + `modelscope-hub==0.4.6` in requirements.txt (sha256 hashes present); uv.lock modelscope 1.40.x / pandas 2.3.3 / numpy 2.5.3; `.venv/bin/modelscope --help` exit 0 within 30 s.
- Task 2: `DOCS-OK` — stale phrases gone, addendum present.
- Task 3: `ALL-GATES-GREEN` — lint/typecheck/JS green; pytest summary tokenizes to exactly 7 failed / 1786 passed / 9 xfailed with no errors/xpassed tokens.

## Threat Mitigations Applied

- **T-h8i-SC (supply-chain ingress):** bounded pin `>=1.40,<2`, exact 1.40.2 + 0.4.6 frozen in the committed uv.lock, sha256 hashes in the exported requirements.txt; legitimacy evidenced by the maintainer directive naming the package + floor, live dist-info verification at plan time, and CI never importing it (installed only — the suite passed unchanged at baseline).
- **T-h8i-01 (lock/export drift):** `uv lock --check` exit 0 + the pandas/numpy version greps prove the re-lock changed no existing resolution.
- **T-h8i-02 (CI budget):** accepted per plan — five small pure-Python additions; gates unaffected.

## Commits

| Commit | Type | Content |
|--------|------|---------|
| e36439f | feat | pyproject data-group entry + uv.lock (98 blocks) + requirements.txt export |
| 3ebb2ca | docs | GETTING-STARTED x2, DEVELOPMENT x1, PIN-VALIDATION addendum |

## Self-Check: PASSED

- pyproject.toml, uv.lock, requirements.txt, docs/GETTING-STARTED.md, docs/DEVELOPMENT.md, baseline/PIN-VALIDATION.md — all present on disk (verified via git show of both commits).
- Commits e36439f and 3ebb2ca — both ancestors of HEAD on `autorun` (git log).
