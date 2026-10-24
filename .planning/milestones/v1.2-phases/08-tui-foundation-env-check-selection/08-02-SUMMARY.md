---
phase: 08-tui-foundation-env-check-selection
plan: 02
subsystem: tui (console package + dependency/tooling spine)
tags: [tui, dependency-groups, textual, platformdirs, pytest-asyncio, d-01, i18n-01, foundation-spine]
requires:
  phase: []
provides: []
provides:
  - "[tui] uv dependency group (textual>=8.2,<9 + platformdirs>=3.6,<5, exactly two packages) locked in uv.lock — the substrate every Phase 8-12 plan installs against"
  - "make tui entry (uv run --group tui --group gpu python -m tui) + PHASE8_TUI wildcard lint guard — later tui/ files join lint coverage with zero further Makefile edits"
  - "tui/ package skeleton: __main__ REPO_ROOT+pipeline sys.path bootstrap (from __file__, never CWD), DnallmMarkTui(App) composition root, screens/ + services/ contract docstrings declaring the one-directional import boundary"
  - "tui/strings.py — the I18N-01 single home for operator copy (APP_TITLE + ENV_KERNEL_LABELS, UI-SPEC Copywriting Contract verbatim)"
  - "tests/tui/conftest.py repo-root sys.path insert — the Pitfall 4 fix that makes import tui resolve under plain pytest in CI"
  - "pytest-asyncio>=1.4,<2 in dev + asyncio_mode=auto — the tier-2 Pilot test lane, proven sync-suite-neutral (A3)"
affects:
  - pyproject.toml
  - uv.lock
  - Makefile
  - tui/
  - tests/tui/
actuals:
  tokens: 7618      # chars/4 over the realized diff (30472 chars) — vs estimate 13000
  tasks: 2          # Task 1 = blocking-human legitimacy gate (maintainer-resolved); Task 2 = the spine
  commits: 1        # measured: git rev-list --count 99c1559..HEAD (Task 1 was verification-only, no commit by design)
plan_head_before: 99c15590e5021efccb3e3525b1d5f6b126a22d0e
plan_head_after: ef56567c24206fdd5af0275a990e961a5efd4092
tech-stack:
  added:
    - "textual 8.2.8 (>=8.2,<9, [tui] group) — TUI framework; pure-Python, py.typed, CPU-lane-safe"
    - "platformdirs 4.13.0 (>=3.6,<5, [tui] group) — XDG user_state_dir/user_config_dir resolution (D-04); fresh lock resolution (the venv's transitive 4.12.4 was never a lock member)"
    - "pytest-asyncio 1.4.0 (>=1.4,<2, dev group) — tier-2 Pilot test runner under pytest 9.1.1"
    - "textual transitives: linkify-it-py 2.2.0, mdit-py-plugins 0.6.1 (rich/pygments/markdown-it-py already locked)"
  patterns:
    - "wildcard existence-guard lint coverage (PHASE8_TUI := $(wildcard tui/*.py tui/screens/*.py tui/services/*.py)) — the glob IS the guard; later plans add files without Makefile edits"
    - "D-01 CI ratification via Makefile recipe only: make test gains --group tui so the EXISTING CI test job installs textual-the-library with zero workflow edits (sha256-proven)"
    - "__file__-derived REPO_ROOT bootstrap mirrored from tests/conftest.py:41-44 (repo root + pipeline/ inserts before any tui.app/pipeline-seam import)"
    - "package-qualified tui imports require the repo root as an import root — declared once in [tool.ty.environment] extra-paths and once in tests/tui/conftest.py"
key-files:
  created:
    - tui/__init__.py
    - tui/__main__.py
    - tui/app.py
    - tui/strings.py
    - tui/styles.tcss
    - tui/screens/__init__.py
    - tui/services/__init__.py
    - tests/tui/conftest.py
  modified:
    - pyproject.toml
    - uv.lock
    - Makefile
key-decisions:
  - "Package legitimacy verdicts (maintainer-delegated, 2026-10-11): textual 8.2.8 / platformdirs 4.13.0 / pytest-asyncio 1.4.0 all APPROVED — full verdict lines in the Package Legitimacy Gate section"
  - "typecheck recipe gains --group tui (Rule 3): ty cannot resolve textual's py.typed types without the library installed — proven by a fresh-env unresolved-import failure in exactly CI's lint-typecheck state; textual-the-library in the existing CPU static lane, data/gpu lanes still never see textual (constraint 2/10 intact)"
  - "uv sync --group tui executed with --inexact: plain uv sync is EXACT and would have stripped the GB10 venv's GPU stack AND the manually-installed dnallm (not restorable by uv — local-clone install); --inexact matches the inexact-sync behavior every uv run lane already relies on (Pitfall 10/A4)"
  - "PHASE8_TUI uses the direct wildcard glob over the PHASE7 explicit-list form: the tui tree gains ~10 files across 08-03..08-07 — the glob auto-covers them, the explicit list would need per-plan Makefile edits"
  - "strings.py kernel map lands as ENV_KERNEL_LABELS (kernel-id → operator label, main() kernel order) — keys are env_smoke CheckResult.name data, never translated; values are UI-SPEC Copywriting Contract verbatim"
  - "platformdirs locked at 4.13.0 (same-day release, maintainer-accepted via signed provenance per the gate verdict; the venv's prior transitive 4.12.4 was never in uv.lock, so this was a fresh resolution, not an upgrade)"
patterns-established:
  - "[tui]-group lane discipline: data/gpu lanes never install textual; the display runtime is make tui (--group tui --group gpu, GB10-local); CI knows textual only as a library (make test / make typecheck recipes)"
  - "services-textual-free contract declared in tui/services/__init__.py docstring (the tripwire test lands in 08-03 per plan — Phase 7 absence-lock discipline)"
  - "tui/__main__ + tests/tui/conftest.py sys.path bootstrap pair: identical REPO_ROOT-from-__file__ idiom at runtime and test time (the conftest.py:41-44 mirror)"
  - "I18N-01 single-home rule: tui/strings.py is the only module that may define operator-facing copy; screens reference constants, never inline copy"
requirements-completed: [I18N-01]
coverage:
  - id: D1
    description: "Dependency + tooling spine — [tui] group (exactly textual>=8.2,<9 + platformdirs>=3.6,<5) with locked uv.lock, dev-group pytest-asyncio, asyncio_mode=auto, ty coverage (src 'tui', extra-paths '.'), PHASE8_TUI lint guard, test recipe --group tui (D-01), make tui target, CI workflow byte-identical"
    requirement: I18N-01
    verification:
      - kind: unit
        ref: "uv run --group dev --group tui python -c ... import tui.app, tui.strings, tui.services -> tui-import-ok"
        status: pass
      - kind: unit
        ref: "uv run --group tui python -c ... -> textual 8.2.8, platformdirs 4.13.0 (majors 8 and 4)"
        status: pass
      - kind: other
        ref: "make lint exit 0; PHASE8_TUI coverage proven by break-test (injected F401 in tui/strings.py flagged by the lane, then reverted)"
        status: pass
      - kind: other
        ref: "make typecheck exit 0 ('All checks passed!')"
        status: pass
      - kind: unit
        ref: "make test-fast: 560 passed, 1 deselected — A3 (asyncio_mode=auto leaves the sync suite green)"
        status: pass
      - kind: other
        ref: "full make test (exact CI test-job command): 561 passed + JS lane 18 pass, exit 0"
        status: pass
      - kind: other
        ref: "grep textual .github/workflows/ci.yml exits 1; sha256 84cc615c5ea46ced0c29857188f32e65856f5c17bfe2f06840db8c2cc7bf5549 byte-identical pre/post"
        status: pass
      - kind: other
        ref: "uv.lock [package.metadata.requires-dev] tui = [platformdirs >=3.6,<5, textual >=8.2,<9] — exactly two packages; lock diff purely additive (74 insertions, 0 deletions)"
        status: pass
    human_judgment: false
    rationale: "Every criterion is mechanically checked (imports, versions, lint/type/test exits, byte identity, lock contents) — no visual or judgment-based criterion exists for this deliverable."
  - id: D2
    description: "tui/ package skeleton — __main__ bootstrap (REPO_ROOT + pipeline/ from __file__, never CWD), DnallmMarkTui(App) minimal composition root (TITLE from strings, CSS_PATH), strings.py first constants (APP_TITLE + ENV_KERNEL_LABELS per UI-SPEC), screens/+services/ contract docstrings, styles.tcss, tests/tui/conftest.py repo-root insert"
    requirement: I18N-01
    verification:
      - kind: unit
        ref: "tui-import-ok (verify 1) — tui.app/strings/services import package-qualified"
        status: pass
      - kind: unit
        ref: "uv run --group tui --group gpu python -c 'import tui.__main__' -> entry-import-ok, REPO_ROOT resolves to the repo from __file__; DnallmMarkTui.TITLE prints 'DNALLM-Mark 控制台'"
        status: pass
      - kind: other
        ref: "make -n tui -> 'uv run --group tui --group gpu python -m tui'; .PHONY lists tui"
        status: pass
      - kind: other
        ref: "acceptance grep: no CWD-relative path resolution in tui/__main__.py (REPO_ROOT from __file__ only; acceptance criterion 5)"
        status: pass
      - kind: other
        ref: "ENV_KERNEL_LABELS values match the UI-SPEC Copywriting Contract row verbatim (seven kernel ids in main() order)"
        status: pass
    human_judgment: false
    rationale: "All checks are mechanical (imports, command expansion, source greps, value comparison against the spec)."
  - id: D3
    description: "Task 1 package-legitimacy blocking gate — textual / platformdirs / pytest-asyncio verified on PyPI before any install or commit (the T-08-SC mitigation)"
    requirement: I18N-01
    verification:
      - kind: human
        ref: "Maintainer verdict 2026-10-11 (delegation on record: '你来检查') — three-way evidence via PyPI project page + JSON API; verdict lines recorded verbatim in the Package Legitimacy Gate section and in the Task 2 commit message"
        status: pass
      - kind: other
        ref: "Task 2 did not run before the verdict was recorded (resume-order enforced by the continuation protocol); no 08-02 production commits existed pre-verdict (verified at resume: HEAD 99c1559, no tui/ tree, no pyproject tui entries)"
        status: pass
    human_judgment: true
    rationale: "The gate exists precisely because registry metadata alone cannot distinguish a legitimate canonical package from a namespaced impersonation — a human (or a human-delegated, evidence-backed verification) is the designed discriminator; the maintainer approved all three with the delegation recorded."
duration: 84 min
completed: 2026-10-11T11:36:00Z
status: complete
---

# Phase 08 Plan 02: TUI Dependency/Tooling Spine + Package Skeleton Summary

Landed the non-retrofittable console foundation: the [tui] group (textual 8.2.8 + platformdirs 4.13.0, maintainer-legitimacy-gated), pytest-asyncio Pilot lane, make tui entry, PHASE8_TUI lint guard, and the tui/ skeleton whose contract docstrings declare the one-directional import boundary (services textual-free) — with CI's workflow file byte-identical throughout (sha256-proven) because D-01's ratification lives entirely in Makefile recipes.

## Performance

- **Duration:** 84 min wall-clock (2026-10-11T10:08:18Z – ~11:33Z, from the plan-start epoch recorded by the checkpoint agent — includes the Task 1 maintainer round-trip pause; the continuation execution itself was ~85 min of that window's tail)
- **Tasks completed:** 2 / 2 (Task 1 = blocking-human package-legitimacy gate, resolved by maintainer verdict; Task 2 = the dependency/tooling spine + skeleton)
- **Files changed:** 11 (8 created, 3 modified; +398/−8 lines; uv.lock diff purely additive)
- **Commits:** 1 production commit (measured from the persisted plan ledger; Task 1 was verification-only by design)
- **Estimate calibration:** 7618 actual tokens vs 13000 estimated (58% — the skeleton's docstring-heavy files were cheaper than the low-confidence estimate assumed)

## Accomplishments

- **Task 1 — package legitimacy gate (blocking-human, resolved):** the three packages were verified on PyPI (project page + JSON API, three-way evidence) and approved by the maintainer with the delegation on record; the full verdict lines are in the Package Legitimacy Gate section below and in the Task 2 commit message. No install or commit happened before the verdict (verified at resume: HEAD was 99c1559 with no tui/ tree and no pyproject tui entries).
- **Task 2 — the spine:** pyproject gained the [tui] group (exactly `textual>=8.2,<9` + `platformdirs>=3.6,<5`, dated comments citing D-01/constraint 10 and the textual-dev/textual-serve exclusion), dev gained `pytest-asyncio>=1.4,<2`, `[tool.pytest.ini_options]` gained `asyncio_mode = "auto"`, ty's src include gained `"tui"` and its environment extra-paths gained `"."` (tui imports are package-qualified, so the repo root must be an import root). The Makefile gained PHASE8_TUI (wildcard existence-guard), the D-01 test-recipe change (`--group dev --group tui pytest`), and the `tui` target (`--group tui --group gpu python -m tui`, Pitfall 10). `uv lock` resolved textual 8.2.8 / platformdirs 4.13.0 / pytest-asyncio 1.4.0 + two textual transitives — 74 lock insertions, zero deletions. The 11-file tui/ skeleton landed with contract docstrings; tests/tui/conftest.py inserts the repo root so `import tui` resolves under plain pytest.
- **Proof, not inspection:** all six plan verify commands green — tui-import-ok; textual 8.2.8/platformdirs 4.13.0; make lint (with PHASE8_TUI coverage PROVEN by an injected-F401 break-test that the lane caught); make typecheck; make test-fast (560 passed — A3 proven); CI workflow grep-empty + sha256 byte-identical. Beyond the plan's list, the full `make test` (the exact CI test-job command) also ran green: 561 passed + JS lane 18 pass. Entry-point smoke: `tui.__main__` imports with REPO_ROOT resolving from `__file__`, `DnallmMarkTui.TITLE` renders the strings constant, `make -n tui` expands to the Pitfall-10 command.

## Package Legitimacy Gate

Task 1's blocking-human checkpoint, resolved by the maintainer on 2026-10-11 (delegation on record: verification performed with three-way PyPI evidence at the maintainer's request). Verdict lines recorded verbatim as instructed:

- textual — APPROVED: v8.2.8, exact pure-ASCII name, maintained by Textualize/Will McGugan (github.com/Textualize/textual), 254 releases with continuous lineage since 2021-06-03, latest upload 2026-06-30, not yanked. Verified via PyPI project page + JSON API (2026-10-11).
- platformdirs — APPROVED: v4.13.0, exact pure-ASCII name, maintained by the tox organization / tox-dev (github.com/tox-dev/platformdirs) with GitHub-Actions release attestation, 86 releases since 2021-05-13, latest upload 2026-10-11 (same-day routine release; attestation present; no takeover signals), not yanked. Verified via PyPI project page + JSON API (2026-10-11). Note for the SUMMARY: uv.lock will pin 4.13.0 (same-day release accepted due to signed provenance; the prior transitive 4.12.4 remains a fallback if the maintainer later prefers).
- pytest-asyncio — APPROVED: v1.4.0, exact pure-ASCII name, maintained under pytest-dev (github.com/pytest-dev/pytest-asyncio) via Trusted Publishing, 76 releases since 2015-04-11, latest upload 2026-05-26, not yanked. Verified via PyPI project page + JSON API (2026-10-11).

Outcome: uv.lock pinned exactly the approved versions (textual 8.2.8, platformdirs 4.13.0, pytest-asyncio 1.4.0). The gate is also recorded in the Task 2 commit message (the commit that introduced the install).

## Task Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 — package-legitimacy gate (verification only, no files by design) | — | maintainer verdict 2026-10-11, recorded above + in commit ef56567's message |
| 2 — dependency/tooling spine + skeleton (feat) | `ef56567` | feat(08-02): land [tui] dependency/tooling spine + tui/ package skeleton |
| plan metadata (docs) | (this commit) | docs(08-02): complete TUI dependency/tooling spine plan |

## Files Created/Modified

- **Created:** `tui/__init__.py` (package contract docstring — layout, one-directional import boundary), `tui/__main__.py` (REPO_ROOT + pipeline/ sys.path bootstrap from `__file__`, never CWD), `tui/app.py` (`DnallmMarkTui(App)` minimal composition root — TITLE from strings, CSS_PATH wired), `tui/strings.py` (APP_TITLE + ENV_KERNEL_LABELS, UI-SPEC Copywriting verbatim), `tui/styles.tcss` (comment-only minimal; theme-token contract), `tui/screens/__init__.py` (presentation-tier contract), `tui/services/__init__.py` (textual-free invariant + allowed-imports contract), `tests/tui/conftest.py` (repo-root sys.path insert)
- **Modified:** `pyproject.toml` (+[tui] group, +pytest-asyncio in dev, +asyncio_mode, ty src/extra-paths), `uv.lock` (+5 packages, 74 insertions 0 deletions), `Makefile` (+PHASE8_TUI, test recipe --group tui, +tui target, typecheck recipe --group tui, .PHONY, header doc)

## Decisions Made

- **Typecheck lane installs the [t]ui group (Rule 3):** the plan's listed verifies include `make typecheck` green + tui/ ty-covered + CI byte-identical — empirically incompatible as-is: in a fresh env (exactly CI's lint-typecheck job state) ty fails `tui/app.py` with `error[unresolved-import]: Cannot resolve imported module 'textual.app'`. Fix: `typecheck: uv run --group dev --group tui ty check` — real types (textual ships py.typed; NO replace-imports-with-any entry, per RESEARCH), zero workflow edits, data/gpu lanes untouched.
- **`uv sync --group tui` run with `--inexact`:** plain `uv sync` is exact and would have stripped the GB10 venv's GPU stack (torch/transformers) and the manually-installed dnallm — not restorable by uv. `--inexact` installs the [tui] group while preserving them (verified post-sync: torch 2.11.0+cu130, dnallm 1.2.1, peft 0.21.2 all intact).
- **PHASE8_TUI as a direct wildcard glob** (vs the PHASE7 explicit-file-list form): the tui tree grows ~10 files across 08-03..08-07; the glob auto-covers every present .py file, so no later plan edits the Makefile for lint coverage.
- **ENV_KERNEL_LABELS naming and data/copy split:** keys are env_smoke's CheckResult.name ids (data, never translated); values are the UI-SPEC Chinese labels. APP_TITLE + the kernel map are the two constant groups landing now; the copy set grows with each screen.
- **platformdirs 4.13.0 locked** (fresh resolution — the venv's transitive 4.12.4 was never a uv.lock member): same-day release accepted per the maintainer-approved verdict (signed provenance); 4.12.4 remains the documented fallback.

## Deviations from Plan

**1. [Rule 3 - blocking issue] typecheck recipe gains `--group tui`**
- **Found during:** Task 2 (verify command 4)
- **Issue:** The plan specifies ty coverage for tui/ and a byte-identical CI workflow, but `make typecheck` (`uv run --group dev ty check`) fails in any fresh environment — CI's lint-typecheck job — with `error[unresolved-import]: Cannot resolve imported module 'textual.app'` on tui/app.py:12, because textual (py.typed) is not installed in the dev+data lane.
- **Fix:** `typecheck: $(UV) run --group dev --group tui ty check`, with a dated comment recording the empirical proof and the constraint reasoning. textual-the-library in the existing CPU static lane is consistent with D-01 (library yes; data/gpu lanes still never see textual; zero workflow edits; zero new jobs). The alternative (replace-imports-with-any for textual.**) was rejected — RESEARCH explicitly rules it out and it would gut real type checking of the App subclass.
- **Files modified:** Makefile
- **Verification:** make typecheck exit 0 ("All checks passed!"); CI sha256 unchanged; the failure was reproduced before the fix and is quoted in the Makefile comment.
- **Commit:** `ef56567`

**2. [Rule 1 - lint finding] RUF100 unused noqa in tui/__main__.py**
- **Found during:** Task 2 (verify command 3, first run)
- **Issue:** The `# noqa: E402` on the post-bootstrap import referenced a rule this ruff version's default set does not enable — RUF100 (unused noqa) fired instead.
- **Fix:** Replaced the noqa with a plain justification comment (the import-after-bootstrap placement is intentional and unflagged).
- **Files modified:** tui/__main__.py
- **Verification:** make lint exit 0; the finding itself proved PHASE8_TUI coverage before the explicit break-test did.
- **Commit:** `ef56567`

**3. [Rule 3 - execution-safety] `uv sync --group tui` run with `--inexact`**
- **Found during:** Task 2 (lock/sync step)
- **Issue:** The plan's literal command, plain `uv sync --group tui`, performs an EXACT sync: it would uninstall the GB10 venv's GPU stack and the manually-installed dnallm package (from the local clone — not in any group, not restorable by uv).
- **Fix:** `uv sync --group tui --inexact` — same group installation, preserves the environment every make lane (and Phase 7's smoke practice) relies on; post-sync spot-check confirmed torch 2.11.0+cu130 / dnallm 1.2.1 / peft 0.21.2 intact.
- **Files modified:** none (execution detail; the venv is gitignored)
- **Commit:** `ef56567` (documented in the commit body)

**Total deviations:** 3 auto-fixed (1 Rule 1, 2 Rule 3).
**Impact:** None on the plan's contract — all six verify commands green after each fix; the CI workflow stayed byte-identical throughout (sha256 verified pre-task, post-commit).

## Issues Encountered

- A duplicate 6-line comment block briefly appeared in the Makefile typecheck section (edit old_string matched the recipe only, leaving the original comment above the replacement) — caught in diff review and fixed before the commit; nothing landed.
- The break-test revert needed a manual Edit instead of `git checkout --` (tui/strings.py was untracked at that point) — restored byte-identical, lint re-verified green.
- Pre-existing, out of scope (logged in the phase `deferred-items.md`): every `uv run` invocation that includes the gpu group uninstalls+reinstalls `nvidia-cusparselt-cu13 0.8.0` (~2ms churn, reproduced with `--group gpu` alone, no tui involved; the 08-02 lock diff touched no torch/nvidia entries).

## Authentication Gates

None — no auth surfaces in this plan.

## User Setup Required

None. (`make tui` on the GB10 host opens the skeleton console — title bar only, no screens yet by design; the first screen lands with 08-03.)

## Known Stubs

None — the skeleton's minimal surfaces (comment-only styles.tcss, docstring-only __init__ files, no screens/services yet) are the designed Phase 8 foundation shape per the plan, not stubs: every element the 08-03 tracer wires (group, entry point, bootstrap, strings home, conftest) exists and is gate-covered.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: supply-chain-surface | Makefile | CI lint-typecheck lane now installs the [tui] group (Rule 3 deviation) — the same three maintainer-approved packages at the same locked versions via uv.lock; no new registry, package, or network endpoint beyond the T-08-SC-audited set |

## Next Phase Readiness

- **08-03 (tracer) can land immediately:** `import tui.app` / `import tui.services` resolve package-qualified under pytest (tests/tui/conftest.py); new screens/services files join lint (wildcard glob) and ty (src include) coverage with zero config edits; the Pilot lane is live (pytest-asyncio installed, asyncio_mode=auto, sync suite proven neutral); `tests/tui/test_import_lock.py` locks the services-textual-free invariant declared in `tui/services/__init__.py`.
- **The D-01 CI posture is proven end-to-end:** the existing CI test job will install textual-the-library through `make test`'s recipe (no workflow bytes changed), the lint-typecheck job through `make typecheck`'s; the drift/static-js jobs and every data/gpu lane never see textual.
- **Env services (08-04) inherit the seam:** kernel ids for ENV_KERNEL_LABELS match env_smoke's CheckResult names landed in 08-01 — the strings map is the render vocabulary for the panel rows.

## Self-Check: PASSED

- All 8 created files — FOUND (committed in `ef56567`): tui/{__init__,__main__,app,strings}.py, tui/styles.tcss, tui/screens/__init__.py, tui/services/__init__.py, tests/tui/conftest.py
- All 3 modified files — FOUND in `ef56567`: pyproject.toml, uv.lock, Makefile
- Task commit verified as ancestor of HEAD: `ef56567` (git merge-base --is-ancestor)
- Commit count measured from the persisted ledger: 1 production commit (`git rev-list --count 99c1559..ef56567`)
- CI workflow sha256 `84cc615c...` byte-identical pre-task and post-commit
