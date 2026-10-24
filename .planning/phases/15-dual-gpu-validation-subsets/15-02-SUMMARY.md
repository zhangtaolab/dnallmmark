---
phase: 15-dual-gpu-validation-subsets
plan: 2
subsystem: testing
tags: [subset-generator, stratified-sampling, determinism, registry-isolation, stdlib-only]

requires:
  - phase: 15-dual-gpu-validation-subsets
    provides: "dispatch-mode N=2 smoke proven (15-01) + run_record finalize fix (15-04) the subset sweep will ride on"
provides:
  - "script/make_subset_datasets.py — deterministic stratified subset generator (stdlib-only, seed-governed, run-twice byte-identical)"
  - "Subset registry contract: official keys + official Dataset_path verbatim, only Train/Dev/Test replaced by measured counts + per-entry subset provenance (generator/seed/fraction/actual_fraction/source_counts)"
  - "tests/test_subset_datasets.py (21 pins over the nine D15-06/D15-07/D15-08/D15-15 behaviors) + committed 3-class fixture"
  - "pipeline/datasets-smoke/ + pipeline/registry-smoke/ gitignore entries; Makefile lint slot for the generator"
affects: [15-03 (real materialization + real-artifact checks), VAL-03 small real sweep, docs/multi-gpu.md sweep section]

actuals:
  tokens: 12578
  tasks: 2
  commits: 2

tech-stack:
  added: []  # zero installs by design (T-15-SC): stdlib-only generator
  patterns:
    - "Two-layer registry seam honored: subset CSVs at official-relative Dataset_path under --dataset_root override; subset registry steers only the sweep layer"
    - "Largest-remainder allocation in pure integer arithmetic (divmod) with stable-sort tie-break → earliest sorted label gets the extra row"
    - "ONE shared random.Random(seed) consumed in fixed order (tasks in CLI order → splits train/dev/test → classes sorted) — run-level determinism contract"
    - "Third-registry-class isolation: path-based refusal (equals/contains official, equals custom) + test-side sha256 before/after over official AND custom files"

key-files:
  created:
    - script/make_subset_datasets.py
    - tests/test_subset_datasets.py
    - tests/fixtures/subset_fixture/train.csv
    - tests/fixtures/subset_fixture/dev.csv
    - tests/fixtures/subset_fixture/test.csv
  modified:
    - .gitignore
    - Makefile

key-decisions:
  - "D15-06 semantics implemented as pinned: k = max(1, int(n × fraction)) capped at n, actual_fraction = k/n recorded per split; per-split independent stratified sampling"
  - "Tie-break: equal-count classes give the extra row to the EARLIEST sorted label (5mC pins 53/52, 6/5, 59/58) — largest-remainder over integer quotas, stable sort, no float drift"
  - "emp_H3 test split is 37/37, NOT the plan bullet's 36/38 — the research table's allocation column is internally inconsistent with the pinned rule (its own train row 291/307 already follows largest-remainder); quotas 74×742/1497=36.68 and 74×755/1497=37.32 give label 0 the extra row; verified against the real probe CSVs still on disk"
  - "Partial-success registry policy: subset registries are written with the successfully generated tasks only (a missing task fails sweep --tasks validation loudly); zero successes → no registry write; any refusal → non-zero exit"
  - "Generator accepts any header containing sequence+label columns (rows copied verbatim), covering the benchmark's 2- and 3-column layouts while pinning the sequence,label contract"

patterns-established:
  - "Mutation-proven pins (12-05 precedent, 5 mutations: tie-break flip, floor drop, order reversal, Dataset_path rewrite, count falsification — each reddened its matching pin, reverted, never committed) as the RED-equivalent when the tracer task lands the behavior first"
  - "Fresh-root-per-run byte-identity comparison: exact file-set equality across two output trees (stronger than delete-stale-between-runs — a silently-not-written file cannot pass vacuously AND content is proven root-independent)"

requirements-completed: [VAL-02]

coverage:
  - id: D1
    description: "Deterministic stratified subset generator (stdlib-only) with registry + provenance output"
    requirement: VAL-02
    verification:
      - kind: integration
        ref: "Task-1 tracer verify (fabricated official-key tree end-to-end: 105/11/117 rows, 53/52 + 6/5 + 59/58 stratification, registry counts + actual_fraction, official registries hash-unchanged) — re-run green at the tracer feedback gate"
        status: pass
  - id: D2
    description: "Test suite pinning byte-identity, stratification math, multiclass fixture, floor rule, ordering, registry fidelity, isolation, fail-fast, output containment"
    requirement: VAL-02
    verification:
      - kind: unit
        ref: "tests/test_subset_datasets.py — 21 passed (.venv/bin/python -m pytest tests/test_subset_datasets.py -q)"
        status: pass
      - kind: unit
        ref: "make lint (ruff covers script/make_subset_datasets.py via the new Makefile slot) + make typecheck — both green"
        status: pass
      - kind: unit
        ref: "node --test tests/js/*.test.js — 26/26 green (untouched lanes)"
        status: pass
      - kind: unit
        ref: "ci.yml blob hash == 33d2252eb594e0faecece9e8015a332d8d6479ef (byte-identical, D15-15)"
        status: pass

metrics:
  duration: 8 min
  completed: 2026-10-20

commits: 2
plan_head_before: cd447c42c76109368c327473699c3ed45591c694
plan_head_after: 86f44515e78e3d10b67ae9c4a8ca16b64999ccba

status: complete
---

# Phase 15 Plan 2: Subset Generator + Tests Summary

**One-liner:** stdlib-only 5% stratified subset generator (largest-remainder over sorted labels, floor-of-1, one shared RNG, original file order) with a 21-pin test suite and provable official/custom registry isolation.

## What Was Built

### Task 1 — `script/make_subset_datasets.py` (tracer) + .gitignore + Makefile (commit 2371ae5)

- **Generator** (581 lines, argparse/csv/json/os/random/pathlib only — no numpy, CI-safe per D15-15): per-split independent stratified sampling with the pinned D15-06 rule `k = max(1, int(n × fraction))` capped at `n`; integer largest-remainder allocation over sorted labels (stable sort → earliest sorted label wins remainder ties); ONE `random.Random(seed)` consumed in fixed order (tasks in `--tasks` CLI order, splits train/dev/test, classes sorted); rows emitted in original file order; CSVs via `csv.writer(lineterminator="\n")` on `newline=""` handles (byte-stable on every platform).
- **Subset registry contract**: `{registry-dir}/datasets_info.json` keeps official keys + official `Dataset_path` VERBATIM, replaces only `Train`/`Dev`/`Test` with measured subset counts, adds the `subset` provenance object `{generator, seed, fraction, actual_fraction per split, source_counts}`; `{registry-dir}/models_info.json` copies the `--models` entries verbatim. All JSON `indent=4, sort_keys=True, ensure_ascii=False` + trailing newline. This is the two-layer seam: the child resolves the same relative `Dataset_path` under an overridden `--dataset_root` with zero pipeline code changes.
- **Validation (V5 / T-15-04)**: declared-vs-measured count guard (registry Train/Dev/Test must equal on-disk rows — refuse with zero writes), header must carry `sequence`+`label`, per-row field count, integer labels (multilabel `;`/regression abort loudly); header-only/0-row splits refused. All three splits validated before any write (all-or-nothing per task).
- **Isolation (D15-07 / T-15-03)**: refuses a resolved `--registry-dir` that equals or contains `pipeline/` or equals the custom registry dir (read-only reimplementation of `registry_loader.custom_registry_dir`: env > XDG > `~/.config/dnallmmark`); never opens official/custom files for writing.
- **Tracer verify green**: fabricated official-key 5mC tree → 105/11/117 rows as 53/52, 6/5, 59/58; registry + provenance correct; official registries sha256-unchanged. Re-ran end-to-end at the tracer feedback gate — green, and the two runs' trees/registries are byte-identical.
- `.gitignore`: `pipeline/datasets-smoke/` + `pipeline/registry-smoke/` adjacent to the `finetuned-smoke*/` precedent. Makefile lint list gains the script (plain addition; ci.yml byte-identical).

### Task 2 — tests + committed fixture (commit 86f4451)

- **Fixture** `tests/fixtures/subset_fixture/`: 3-class (labels i%3), train 60 (20/20/20), dev 12 (4/4/4), test 30 (10/10/10), deterministic `ACGTACGT%04d` sequences (D15-08).
- **21 pins** over the nine behaviors: (1) run-twice byte-identity across two fresh roots incl. exact output-file-set; (2) measured stratification math for all six real split distributions; (3) fixture k=3 → 1/1/1; (4) floor rule (12/19/20 → 1, never 0, capped at n, fraction 1.0 → n); (5) original-file-order + identical selection across runs; (6) registry fidelity incl. `actual_fraction == k/n` per split and models parsed-equal; (7) autouse official+custom registry sha256 pin across every run + the three registry-dir refusals with zero writes; (8) four fail-fast refusals (header-only, count mismatch, malformed row, non-integer label) each with zero writes + non-zero exit; (9) input tree read-only + nothing outside the explicit roots.
- **Non-vacuity (TDD)**: production behavior landed with the Task-1 tracer per the plan's own ordering — RED-equivalent proven by five throwaway mutations (tie-break flip → 3 red, floor drop → 4 red, order reversal → 1 red, Dataset_path rewrite → 1 red, Train-count falsification → 1 red), each reverted, never committed (12-05 precedent).
- **Gates**: pytest 21/21, `make lint` + `make typecheck` green, node 26/26, ci.yml hash pin intact, D15-06 rule literal present (3 occurrences). dnallm editable install verified intact after the `uv run` lanes (D15-14 posture).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan arithmetic] emp_H3 test split pinned 37/37, not the plan bullet's 36/38**
- **Found during:** Task 2 (Test 2 spec)
- **Issue:** The plan's Test-2 parenthetical "(74 = 36/38)" covers both emp_H3 dev AND test, but 36/38 is only correct for dev (labels 735/762). For test (labels 742/755) the pinned algorithm — largest remainder over sorted labels, earliest-label tie-break (must_haves + the 8988bfd tie-break correction + the Task-1 verify's own tuples) — yields 37/37 (quotas 36.68/37.32; the extra row goes to the larger remainder = label 0). The research table's allocation column is internally inconsistent (its train row 291/307 follows largest-remainder while its dev/test rows follow a different, unstated rule); the 8988bfd correction fixed only the equal-count tie cases.
- **Fix:** Implemented the pinned algorithm unchanged; Test 2 asserts dev 36/38 and test 37/37 with an explanatory comment (module docstring + parametrize case). Verified against the real probe CSVs still on disk at `/root/autodl-tmp/tmp/ms-probe/` (labels 742/755 re-measured this session). Task-1's authoritative verify tuples (53/52, 6/5, 59/58) all pass unchanged.
- **Files modified:** tests/test_subset_datasets.py
- **Commit:** 86f4451

**2. [Rule 1 - Snippet bug] Task-1 verify's inline assertion applied `int()` to the header row**
- **Found during:** Task 1 tracer verify
- **Issue:** The plan's inline python snippet slices AFTER conversion — `[int(r[1]) for r in csv.reader(...)][1:]` runs `int('label')` on the header and raises ValueError before any assertion. The snippet's intent (drop the header, count labels) is unambiguous.
- **Fix:** Re-ran the assertion leg with the slice inside the comprehension (`list(csv.reader(...))[1:]`); all assertions passed unchanged. The generator itself needed no change; the tracer gate re-ran the full verify green.
- **Files modified:** none (verify-command-side fix only)

**3. [Rule 3 - Plan omission] `import os` beyond the plan's enumerated stdlib list**
- **Found during:** Task 1
- **Issue:** The plan enumerates the import allow-list as "argparse, csv, json, random, hashlib, pathlib" but ALSO mandates reimplementing the `custom_registry_dir` env resolution (`DNALLMMARK_CUSTOM_REGISTRY_DIR` > `XDG_CONFIG_HOME` > home), which requires `os.environ`.
- **Fix:** Added `import os` — still stdlib-only, zero installs (the actual T-15-SC/D15-15 prohibition). hashlib was not needed (no hash output is part of the generator's write contract) and is simply unused from the allow-list.
- **Files modified:** script/make_subset_datasets.py
- **Commit:** 2371ae5

**4. [TDD shape - documented] Mutation-proven pins instead of a RED-first cycle**
- The plan orders the tracer (Task 1) before the tests (Task 2, `tdd="true"`), so the behavior predates its tests by design. RED-equivalent non-vacuity proven by five throwaway mutations (see Task 2 above), following the recorded 12-05 proof-suite precedent. No RED evidence JSON exists because no RED state ever existed in the committed tree.

## Auth Gates

None — pure CPU plan, no network/auth surfaces touched.

## Known Stubs

None — no placeholder logic; every output path (subset CSVs, both registries, provenance) is fully wired.

## Threat Flags

None — no security-relevant surface beyond the plan's threat model. All three register threats mitigated and test-pinned: T-15-03 (registry cross-contamination — path refusals + sha256 pins), T-15-04 (malformed CSV input — four fail-fast refusals), T-15-SC (package installs — zero installs, stdlib-only).

## Self-Check: PASSED

All created files exist (script, test file, three fixture CSVs, SUMMARY); both task commits (2371ae5, 86f4451) are ancestors of HEAD; .gitignore and Makefile entries verified present.
