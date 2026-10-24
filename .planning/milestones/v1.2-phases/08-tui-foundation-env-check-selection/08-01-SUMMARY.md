---
phase: 08-tui-foundation-env-check-selection
plan: 01
subsystem: pipeline/env_smoke
tags: [env-smoke, d-02, characterization-tests, tui-substrate, env-01]
requires:
  phase: []
  provides: []
provides:
  - "CheckResult frozen dataclass (name/ok/lines) importable from pipeline/env_smoke — the D-02 structured seam 08-04 env services and 08-06 screen drill-down consume"
  - "Seven kernels returning CheckResult with stable ids in main() order (version_pins, dnallm, peft, cuda, matmul, numpy, dataset_dirs) — the row order and CRITICAL/ROUTING classification basis for 08-04"
  - "tests/test_env_smoke_bytes.py golden byte-characterization suite (S1/S2/S3) — the drift tripwire every future env_smoke edit must keep green"
affects:
  - pipeline/env_smoke.py
  - tests/test_env_smoke_bytes.py
actuals:
  tokens: 7478       # chars/4 over the realized diff (29912 chars)
  tasks: 2
  commits: 2         # measured: git rev-list --count f7d516a..HEAD
plan_head_before: f7d516a84f668fdc0ca5c31a8258eb13286f3edc
plan_head_after: 32144600b4a3427f7e165695cce6f5a3939c3864
tech-stack:
  added: []          # stdlib-only changes (dataclasses); no new dependencies
  patterns:
    - "kernels-return-lines / renderer-main (RESEARCH Pattern 1): kernels build CheckResult and never print; main() owns every stdout byte via _emit + segment loops"
    - "golden byte characterization recorded by RUNNING (sentinel-expectation RED first, then paste the actual bytes — never from memory)"
    - "sys.modules whole-module injection as the deterministic import seam (covers importlib.import_module AND literal `import torch`; None value = documented halt sentinel for the missing-torch path)"
    - "REPO_ROOT sentinel pinning for host-independent golden bytes over path-embedding output"
key-files:
  created:
    - tests/test_env_smoke_bytes.py
  modified:
    - pipeline/env_smoke.py
key-decisions:
  - "check_peft keeps its byte-exact `def check_peft():` signature (no return annotation) — pinned by test_env_smoke_peft_check_is_gating's ^def check_peft\(\): regex; the return type is documented in its docstring while the six sibling kernels carry explicit -> CheckResult annotations"
  - "torch-unavailable cuda/matmul placeholders are CheckResult(name=..., ok=False, lines=()) values — preserves today's two-False append semantics (two failed results, zero output of their own) with type-clean list[CheckResult]"
  - "print_ecosystem_diagnostics stays a printing helper called by main() — explicitly permitted by the plan's acceptance criterion (module-level rendering helper); zero-diff to that function minimizes byte risk"
  - "main() renders in two segment loops (import-surface segment before the torch gate, cuda/matmul/numpy segment after) mirroring today's exact print interleaving — the only structure that keeps the literal results.append(check_peft()) wiring AND the INFO-line/gate-line positions"
  - "golden test fakes carry hardcoded __version__ values matching the current [gpu] pins (torch 2.11.0+cu130 exercising the release-segment path); a future pin bump legitimately fails the golden — updating the literals is the intended maintenance act"
patterns-established:
  - "characterization-first refactor discipline: pin bytes with a golden suite that must pass against the UNMODIFIED module before touching it (this is the template for any future byte-contracted refactor)"
  - "sys.modules + None halt-sentinel injection for deterministic import-failure scenarios on hosts that DO have the package installed"
requirements-completed: [ENV-01]
coverage:
  - id: D1
    description: "D-02 structured-return refactor — frozen CheckResult(name, ok, lines); seven kernels return it with zero printing; main() sole renderer; byte-identical CLI stdout and 0/1 exit"
    requirement: ENV-01
    verification:
      - kind: unit
        ref: "uv run --group dev pytest tests/test_env_smoke_bytes.py -q (3 passed post-refactor, byte-equal S1/S2/S3 + exit ints)"
        status: pass
      - kind: unit
        ref: "uv run --group dev pytest tests/test_run_finetune_contracts.py -q (65 passed, file untouched — git diff empty)"
        status: pass
      - kind: integration
        ref: "live CLI: uv run --group dev python pipeline/env_smoke.py exit 0, trailer present, diff vs /tmp/env_smoke_live_before.txt empty"
        status: pass
      - kind: unit
        ref: "AST audit: zero print() calls inside the seven kernels + import_or_fail; literal results.append(check_peft()) inside main() at pipeline/env_smoke.py:504"
        status: pass
      - kind: other
        ref: "make lint + make typecheck exit 0"
        status: pass
    human_judgment: false
    rationale: "Every criterion is mechanically checked (byte equality, source-grep locks, live diff, lint/type gates) — no visual or judgment-based criterion exists for this deliverable."
  - id: D2
    description: "Golden byte-characterization suite tests/test_env_smoke_bytes.py — S1 all-pass / S2 torch-missing / S3 dataset-missing (double-nested note), full-stdout byte equality + integer exit values"
    requirement: ENV-01
    verification:
      - kind: unit
        ref: "suite green against the UNMODIFIED pipeline/env_smoke.py before the refactor (characterization property; Task 1 commit b109b64, env_smoke.py untouched at that commit)"
        status: pass
      - kind: unit
        ref: "suite green after the refactor (Task 2 commit 3214460)"
        status: pass
      - kind: integration
        ref: "live CLI run before refactor: exit 0, === SMOKE RESULT: trailer present, captured at /tmp/env_smoke_live_before.txt"
        status: pass
    human_judgment: false
    rationale: "Characterization correctness is machine-verifiable by construction — expectations were recorded from executed runs, not authored."
duration: 17 min
completed: 2026-10-11T10:02:19Z
status: complete
---

# Phase 08 Plan 01: Env Smoke Structured-Return Refactor (Golden Bytes) Summary

Refactored the seven env_smoke check kernels to frozen CheckResult returns with main() as the sole renderer, while a golden byte-characterization suite (recorded from live runs, never memory) proves the CLI stdout and exit codes stayed byte-identical — the D-02 substrate the Phase 8 TUI imports and the E2' gate greps.

## Performance

- **Duration:** 17 min (09:45:15Z – 10:02:19Z, 2026-10-11)
- **Tasks completed:** 2 / 2
- **Files changed:** 2 (1 created, 1 modified; +481/−68 lines)
- **Commits:** 2 (measured from the persisted plan ledger)

## Accomplishments

- **Task 1 — golden byte suite (TDD):** `tests/test_env_smoke_bytes.py` pins full-stdout byte equality plus the integer exit value for three scenarios: S1 all-pass (fake modules with `__version__` matching the current `[gpu]` pins — torch deliberately carries `+cu130` so the release-segment comparison path is exercised; fake CUDA torch with 1 device; synthetic all-present registry), S2 torch-missing (torch-unavailable FAIL line in its exact slot between peft and numpy; cuda/matmul failed with no own output; exit 1, 3-group FAIL trailer), S3 dataset-missing (verbatim indented block with the double-nested note continuation line; exit 1). Seams are all monkeypatch-level: `sys.modules` injection (the None halt-sentinel covers both the `import_module` seam and main()'s literal `import torch`), `REPO_ROOT` pinned to a sentinel path for checkout-independent bytes, synthetic tmp dataset registry — CPU-only and CI-safe. RED ran first with sentinel expectations (3 failed on the planned byte-equality assertion; JUnit evidence validated `RED_EVIDENCE_OK`), then the literals were recorded by RUNNING the scenarios — which caught a line a from-memory transcription would have missed (`PASS: import numpy resolves (...)` precedes the floor line).
- **Task 2 — D-02 refactor:** frozen `CheckResult(name: str, ok: bool, lines: tuple[str, ...])` with the seven stable kernel ids in main() order; all seven kernels build and return it (import_or_fail now returns `(module, line)`); `main()` is the only renderer (`_emit` helper + two segment loops reproducing today's exact print interleaving, including the torch-gate FAIL lines' position and the non-gating INFO line between numpy and dataset dirs). The grep-locked surfaces survived verbatim: `def check_peft():` signature, the literal `results.append(check_peft())` wiring inside main(), the module docstring sanction block, every pinned version label — `tests/test_run_finetune_contracts.py` untouched and green.
- **Proof, not inspection:** golden suite green pre- and post-refactor; live CLI output on this GB10 host diff-empty before vs after (exit 0, fully green run — real NVIDIA GB10, all 50 dataset dirs); make lint + make typecheck green; full fast suite 560 passed with zero regressions.

## Task Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 — golden byte suite (test) | `b109b64` | test(08-01): pin env_smoke CLI bytes in golden characterization suite |
| 2 — D-02 structured-return refactor (feat) | `3214460` | feat(08-01): D-02 structured-return refactor — kernels build CheckResult, main renders |
| plan metadata (docs) | (this commit) | docs(08-01): complete env-smoke structured-return refactor plan |

## Files Created/Modified

- **Created:** `tests/test_env_smoke_bytes.py` (322 lines — golden characterization suite, module docstring citing D-02 and the E2' dual-gate contract)
- **Modified:** `pipeline/env_smoke.py` (+159/−68 — CheckResult dataclass, seven kernel refactors, renderer main(); module docstring byte-untouched)

## Decisions Made

- **check_peft stays un-annotated:** the grep-lock test pins `^def check_peft\(\):` byte-exact, so no `-> CheckResult` return annotation is possible on it; the six sibling kernels carry the annotation and check_peft documents the constraint in its docstring (the plan's artifacts-listing of annotated signatures yields to its own prohibition on altering grep-locked wiring).
- **Placeholder CheckResults instead of raw `False` appends:** the torch-unavailable path appends `CheckResult(name="cuda"/"matmul", ok=False, lines=())` — same observable semantics (two failed groups, no output, exit-1 counting) with a type-clean `list[CheckResult]` for the TUI to consume.
- **`print_ecosystem_diagnostics` unchanged:** it remains a printing helper main() calls for rendering (explicitly permitted by the plan's acceptance criterion) — lowest-drift choice for the INFO line.
- **Hardcoded pin-matching fakes in the golden suite:** fake versions match today's `[gpu]` pins as literals; a future pin bump legitimately reddens the suite and updating the literals is the intended maintenance act (characterization semantics).
- **ty/ruff dunder conflict resolved via `setattr` + justified `noqa: B010`:** ty rejects a literal `module.__version__ = ...` write on ModuleType while ruff B010 rejects constant-attr `setattr` — the repo's justified-per-line-noqa precedent (env_smoke's own BLE001 sites) applies.

## Deviations from Plan

**1. [Rule 1 - lint finding] ISC004 parenthesization in refactored line literals**
- **Found during:** Task 2 (make lint gate)
- **Issue:** Moving the original `print(f"..." "...")` argument-list concatenations into tuple/list literals (CheckResult lines) triggered ruff ISC004 (unparenthesized implicit concatenation in a collection) at three sites — the original passed only because print() arguments are not collections.
- **Fix:** Wrapped each concatenated fragment group in its own parentheses inside the collection literal — string values byte-identical, golden suite and live diff re-verified green after the change.
- **Files modified:** `pipeline/env_smoke.py` (check_peft / check_dataset_dirs / check_matmul line literals)
- **Verification:** make lint exit 0; golden suite 3 passed; live diff still empty.
- **Commit:** `3214460`

**2. [Rule 3 - tool conflict] ty unresolved-attribute on fake-module `__version__` write**
- **Found during:** Task 1 (hygiene run of make typecheck beyond the plan's listed verifies)
- **Issue:** `module.__version__ = version` on `types.ModuleType` is an unresolved dunder attribute for ty (regular attribute writes like `cuda`/`ones` resolve fine).
- **Fix:** `setattr(module, "__version__", version)` with a trailing `# noqa: B010` and a justification comment (ruff B010 flags constant-attr setattr — the exact inverse of the ty constraint).
- **Files modified:** `tests/test_env_smoke_bytes.py`
- **Verification:** make typecheck exit 0; make lint exit 0; suite green.
- **Commit:** `b109b64`

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 3).
**Impact:** None on the byte contract — both fixes are formatting/tooling-level; all byte-equality, grep-lock, live-diff, and quality gates were re-run green after each.

## TDD Gate Compliance

Task 1 carried `tdd="true"`; the plan-level `test(08-01):` (`b109b64`) and `feat(08-01):` (`3214460`) commits both exist (validated via git log grep). RED evidence: sentinel-expectation run failed the planned byte-equality assertion (3 failed, exit 1; JUnit report; `check tdd-red-evidence` verdict `RED_EVIDENCE_OK`); semantic assessment: the target test executed `env_smoke.main()` under the pinned seams and failed for the intended reason — expectations not yet recorded — with no syntax, discovery, or unrelated failures. GREEN: literals recorded by executing the scenarios. Note on scope: this is a characterization task — the suite is born-green against the unmodified module by design (the plan's own acceptance criterion), so the RED step demonstrates the recording harness rather than a missing feature.

## Issues Encountered

None beyond the two deviations above. The live dev-venv run happens to be fully green on this GB10 host (uv's inexact sync retains the GPU stack: real GB10 CUDA, dnallm, peft 0.21.2, all 50 dataset dirs) — which made the before/after live diff an all-PASS comparison rather than a FAIL-comparison; the golden suite covers the failure shapes deterministically regardless of host.

## Authentication Gates

None — no auth surfaces in this plan.

## User Setup Required

None.

## Known Stubs

None — no stub patterns in the delivered files; the designed empty-`lines` placeholder CheckResults (torch-unavailable cuda/matmul) are documented behavior, not stubs.

## Next Phase Readiness

- **08-04 (env services) and 08-06 (env screen)** can now `import env_smoke` (pipeline/ on sys.path per the conftest/`__main__` bootstrap pattern) and consume `CheckResult` values directly — kernel ids `version_pins/dnallm/peft/cuda/matmul/numpy/dataset_dirs` are the stable row vocabulary, with per-kernel detail lines available for drill-down rendering without subprocess parsing (D-02 satisfied).
- **The E2' greppable contract is locked from both sides:** rendered bytes (golden suite) and source strings/wiring (the three untouched grep-lock tests). Any future env_smoke edit that drifts either fails CI.
- No `tui/` files, pyproject groups, or Makefile targets were touched — those belong to 08-02/08-03 onward per the wave plan.

## Self-Check: PASSED

- `tests/test_env_smoke_bytes.py` — FOUND (created, committed in `b109b64`)
- `.planning/phases/08-tui-foundation-env-check-selection/08-01-SUMMARY.md` — FOUND (committed in `48e53f8`)
- Task commits verified as ancestors of HEAD: `b109b64` (Task 1), `3214460` (Task 2)
- Commit count measured from the persisted ledger: 2 production commits (`git rev-list --count f7d516a..3214460`)
- TDD gate: both `test(08-01):` and `feat(08-01):` commits present (git log -E grep validated)
