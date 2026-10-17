---
phase: quick-261017-eea
plan: 01
subsystem: build+data-chain
tags: [ci-fix, lockfile, pexpect, data-chain, helixgen, schema, baseline-reset]
status: complete
requirements: [EEA-1, EEA-2, EEA-3, EEA-4, EEA-5, EEA-6]
key-files:
  created: []
  modified:
    - pyproject.toml
    - uv.lock
    - scripts/demo/record_tui_demo.py
    - schemas/model_performance.json
    - dnallm-mark/data/model_performance/helixgen-2stage_performance.json
    - dnallm-mark/data/model_performance/helixgen-2stage-w015625_performance.json
    - dnallm-mark/data/model_performance/helixgen-mlm_performance.json
    - dnallm-mark/data/models_comparison.json
    - dnallm-mark/data/models_comparison_animal.json
    - dnallm-mark/data/models_comparison_plant.json
    - dnallm-mark/data/models_comparison_microbe.json
    - dnallm-mark/data/permutation_tests.json
    - tests/test_schemas.py
    - tests/test_determinism.py
  deleted:
    - dnallm-mark/data/models_comparison_multi-species.json
decisions:
  - "pexpect joins [dependency-groups] dev as a real member (no ty masking); lock diff confined to pexpect 4.9.0 + ptyprocess 0.7.0"
  - "info.path stripped from the three helixgen files (leaked AutoDL server paths, zero consumers) — schema NOT extended for path"
  - "[Rule 2 deviation] schema FLOPs relaxed to the anyOf [number, const ''] shape its 13 sibling metrics already use (see Deviations)"
  - "models_comparison_multi-species.json deleted — the 9e803ca stray (forensic below); recoverable at 9e803ca"
  - "New local baseline: 1F / 1859P pytest (test_services_run_config only, machine-local) + node 26/26"
metrics:
  duration: 14 min
  tasks: 4
actuals:
  tokens: 31000
  tasks: 4
  commits: 3
plan_head_before: f044b0e
plan_head_after: c6b510f
---

# Quick Task 261017-eea: CI Fix Batch — pexpect into dev lockfile + data-chain re-sync Summary

Closed all four red PR #7 CI lanes at their root causes: pexpect joined the dev group (lint+typecheck lane), the data chain re-synced with helixgen integrated canonically and the non-regenerable multi-species stray deleted (drift lane + both test lanes), the three helixgen performance files made schema-valid (test lanes), and the stale bucket pin re-based 42→45 — with every moved public number documented before/after below and the new local test baseline pinned.

## Commits

| Commit | Task | Content |
|--------|------|---------|
| 9a225ed | 1 | fix(261017-eea): pexpect into the dev group — CI ty unresolved-import root cause |
| 9a83066 | 2 | fix(261017-eea): helixgen performance files schema-valid — info.path stripped, dataset.species canonical |
| c6b510f | 3 | fix(261017-eea): data chain re-synced — multi-species stray removed, helixgen integrated, drift gate green |

Task 4 (baseline reset + SUMMARY) lands as the docs commit that carries this file.

## Four-Lane Root-Cause Table

| PR #7 lane | Root cause | Fix (commit) |
|------------|-----------|--------------|
| lint+typecheck | `scripts/demo/record_tui_demo.py` imports pexpect lazily at :1102/:1120; ty resolves imports statically; pexpect was in NO dependency group — CI's lock-built env failed unresolved-import x2 while the local venv passed environmentally | pexpect>=4.9 declared in `[dependency-groups]` dev; lock gains exactly pexpect 4.9.0 + ptyprocess 0.7.0 (9a225ed) |
| drift | The four arena files were last regenerated at dfb9a80 (pre-helixgen); 9e803ca committed three helixgen inputs + a `models_comparison_multi-species.json` that no code path regenerates | Stray deleted; four arena files + permutation_tests.json regenerated from the 45-model corpus; two-run `make data` byte-identical no-op proven (c6b510f) |
| test 3.13/3.14 (determinism) | Same data drift — file-set 4 vs committed 5, byte drift of the four | Same regeneration; `tests/test_determinism.py` docstring 42→45 (c6b510f) |
| test 3.13/3.14 (schemas) | helixgen `info.path` (closed 11-key info schema, `additionalProperties: false`) + `dataset.species: 'multi-species'` (enum violation, AUD-01 species-from-model-row defect) + `FLOPs: ''` (strict `type: number`) | info.path stripped, species rewritten to canonical arena (9a83066); FLOPs schema conformed to the missing-metric convention (9a83066, Rule 2 deviation below) |

## pexpect Legitimacy Verdict (per the 08-02 maintainer delegation)

- PyPI project: **pexpect** — https://pypi.org/project/pexpect/
- Authors: Noah Spurrier / Thomas Kluyver / Jeff Quast
- Source: https://github.com/pexpect/pexpect
- License: ISC
- Version pinned: **4.9.0** — PyPI current latest AND the exact version the repo's own `record_tui_demo.py` docstring already cited
- Sole dependency: **ptyprocess 0.7.0** (locked alongside; no further transitive deps)
- Verdict: APPROVED (verified at planning time per the delegation; this batch locked it so CI never resolves freely)

## Lockfile Discipline Proof

- `uv.lock` diff = **23 insertions, 0 deletions**: two `dev`-group membership lines (`{name="pexpect"}` / `{name="pexpect", specifier=">=4.9"}`) + the two new `[[package]]` blocks (pexpect 4.9.0, ptyprocess 0.7.0). Every pre-existing pin untouched — **pandas 2.3.3 and numpy 2.5.3 (D-05 anchors) byte-unchanged**.
- `requirements.txt` re-exported via `uv export --group data --no-emit-project`: **byte-identical** (the export is data-group-only; a dev-group addition never rides it — confirmed empty diff).
- CI-parity proof: `uv run --isolated --group dev --group tui ty check` failed with exactly the 2 unresolved-import diagnostics before the pyproject edit and passes after (and again at final state).

## Multi-Species Stray Forensic (deletion justification)

`dnallm-mark/data/models_comparison_multi-species.json` (added 9e803ca, deleted c6b510f — recoverable at 9e803ca):

- Content = the ALL view (45 models × all 47 datasets; per-model task participation identical to the all view, samples 47) regenerated on the AutoDL training server with `include_weighted=False` — NOT a species-grouped subset (no grouping rule exists in its content).
- Carries the stale pre-D-18 alias `plant-dnamamba2-BPE` (renamed `PlantDNAMamba2-BPE` at dfb9a80) and ULP-level float deltas vs local regeneration (foreign-machine numpy).
- Zero consumers: `js/data.js` arenaMap and `CONFIG.ARENAS` are exactly all/animal/plant/microbe; `schemas/models_comparison.json` $comment scopes itself to ALL FOUR committed files and requires `weighted_score` (the stray has none); `tests/test_schemas.py` enumerates exactly four comparison files and pins the bucket at 4; no test or script references the filename.
- Byte-non-reproducible on this machine in principle — its presence broke the CI drift lane's `git diff --exit-code` unconditionally.
- Knowledge preserved: this SUMMARY records its semantics (above) and its helixgen rows matched our regeneration exactly (`sum_PFLOPs: 0`, rank_scores 1033/980/486 identical to the regenerated all view).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing accommodation] schema FLOPs relaxed to the missing-metric anyOf shape**
- **Found during:** Task 2 — after stripping `info.path` and rewriting `dataset.species`, path29-31 STILL failed. The plan's planning-time diagnosis encoded only the info.path violation, but the schema validator is a collect-all: all 141 helixgen entries (3 × 47) also carry `FLOPs: ""` where the schema demanded `type: number`.
- **Facts assembled before deciding:** (a) the schema's own `$comment` documents the convention as "Missing metric values are exactly '' or a number (Pitfall 7)" — FLOPs was encoded strict only because the Phase-2 survey's 42 files all had measured FLOPs; (b) all 13 sibling metrics already use `anyOf: [{type: number}, {const: ""}]`; (c) `script/summarize_comparison.py:505` reads FLOPs via `get_float(..., default)` and the aggregation's `f_val > 0` guard keeps absent FLOPs out of PFLOPs sums (the server-generated stray itself shows `sum_PFLOPs: 0` for helixgen — identical to local regeneration); (d) no test pins FLOPs strictness; (e) fabricating numbers is forbidden by the repo's core mandate and dropping the helixgen corpus contradicts the batch's purpose.
- **Fix:** `schemas/model_performance.json` FLOPs property changed from `{ "type": "number" }` to `{ "anyOf": [{ "type": "number" }, { "const": "" }] }` — conforming one property to the schema's own documented convention; no other schema change.
- **Files modified:** schemas/model_performance.json (1 line)
- **Commit:** 9a83066
- **Ledger note:** the `gsd-tools windows append` for this deviation failed on a PRE-EXISTING table/JSON disagreement in `.planning/WINDOWS.md` (rows 20, 23, 24, 25, 29 — unrelated to this batch; not repaired, out of scope). This SUMMARY row is the durable record; orchestrator may re-run the append after repairing the ledger.

**2. [Rule 2 - Consistency] two additional stale "42" prose references in tests/test_schemas.py**
- The plan named the EXPECTED_BUCKET_SIZES pin and the determinism docstring; two comments in test_schemas.py ("the 42-file and 47-file validation", "the dataset blocks of the 42 producer files") described the same corpus. Updated to 45 alongside the pin so the file stays internally consistent. Commit c6b510f.

## Before/After Number Ledger (every moved public number)

### helixgen info.path (stripped — T-eea-01 disclosure)

| File | Before (verbatim) | After |
|------|-------------------|-------|
| helixgen-2stage_performance.json | `/root/autodl-tmp/labshare/zt/scratch/helixgen-28-gue/staged` | key deleted |
| helixgen-2stage-w015625_performance.json | `/root/autodl-tmp/labshare/zt/scratch/helixgen-34-canary/helixgen-2stage-w015625` | key deleted |
| helixgen-mlm_performance.json | `/root/autodl-tmp/labshare/zt/scratch/helixgen-43-staged` | key deleted |

### helixgen dataset.species (47 entries per file, rewritten to canonical)

| File | Before | After |
|------|--------|-------|
| all three | `multi-species` × 47 | Animals 22 / Plants 12 / Microbe 13 (the canonical per-dataset map, asserted unanimous across the 42-file corpus) |

Card-level `info.species: 'multi-species'` stays in all three (open string in the schema — valid, and factually what the models are).

### Derived comparison files (42 → 45 models each)

| File | Models | helixgen rank positions (after) | Top-6 order |
|------|--------|-------------------------------|-------------|
| models_comparison.json (all) | 42 → 45 | w015625 #24 (1033), 2stage #26 (980), mlm #40 (486) | unchanged |
| models_comparison_animal.json | 42 → 45 | w015625 #22 (520), 2stage #25 (502), mlm #40 (229) | unchanged |
| models_comparison_plant.json | 42 → 45 | w015625 #24 (232), 2stage #25 (213), mlm #40 (102) | unchanged |
| models_comparison_microbe.json | 42 → 45 | w015625 #22 (281), 2stage #25 (265), mlm #39 (155) | unchanged |

Top-6 BEFORE (all view): PlantHelixSeek 1683, nucleotide-transformer-v2-500m 1644, agro-nucleotide-transformer-1b 1556, GENERanno-eukaryote 1509, PlantCAD2-Medium 1444, PlantCAD2-Small 1438.
Top-6 AFTER (all view): PlantHelixSeek 1821, nucleotide-transformer-v2-500m 1784, agro-nucleotide-transformer-1b 1686, GENERanno-eukaryote 1634, PlantCAD2-Medium 1570, PlantCAD2-Small 1559.
**Order is stable in all four views; the rank_score values legitimately shift** — `task_rank_score = N − rank` per task, and N grows by 1 for each helixgen joining below a model (a top model above all three helixgens on all 47 tasks gains up to +141; PlantHelixSeek +138 = below a helixgen on exactly one task). The same shift applies in the three arena views.

Alias integrity: `PlantDNAMamba2-BPE` present (the D-18 canonical form), stale `plant-dnamamba2-BPE` absent, in all four regenerated files.

### permutation_tests.json

| Field | Before | After |
|-------|--------|-------|
| info.n_models | 42 | 45 |
| info.family_size | 861 | 990 |
| pairs total | 861 | 990 (861 shared + 129 helixgen-involving) |
| significant pairs | 657/861 | 761/990 |
| verdict flips among the 861 shared pairs | — | **0** (all 104 new significant pairs are helixgen-involving) |
| p_adj movement among shared pairs | — | all 861 shifted microscopically (BH scaling over the larger family; e.g. evo2_1b_base vs plant-dnabert-6mer 0.000350 → 0.000353) |

### Unmoved by regeneration (verified)

`manifest.json`, `provenance.json`, `provenance.csv`, `tasks.json`, `DATA.md`, and all 45 `model_performance/` inputs showed zero changes from `make data` — constants / registry-driven / task_performance-driven, as planned. (DATA.md mtime may change; git reports it unchanged.)

## New Test Baseline (pinned for all subsequent quick tasks)

Full `make test` (pytest + node lanes), run as non-root `forrest` on the GB10 box, 2026-10-17 at c6b510f:

- **pytest: 1858 passed, 1 failed** in 296.94s
- **The single failure: `tests/tui/test_services_run_config.py::test_storage_overview_defaults_mirror_real_consumers`** — machine-local: it asserts `pipeline/logs` does not exist "on a fresh checkout", but this box ran real training so the directory exists here. Pre-existing (the 7F baseline's machine-local member), NOT introduced by this batch.
- **node --test tests/js/*.test.js: 26/26 green.**
- The old 7F baseline collapsed from 7 to 1: path29, path30, path31, dataset_enums, bucket_counts, and chain_deterministic are all green; the 5 root-user chmod sims referenced by WINDOWS #22 pass in this non-root context (they are the ledger item's other half, out of scope here).
- **Gate number going forward: 1F / 1859P pytest + 26/26 node.** Zero new failures vs the 7F baseline minus the six this batch collapses.

## Gate Evidence (Task 4 verify block, all at final state)

- `make lint` — All checks passed
- `make typecheck` — All checks passed
- `uv run --isolated --group dev --group tui ty check` — All checks passed (CI parity)
- `node --test tests/js/*.test.js` — 26/26
- `make data` (second consecutive run) + `git diff --exit-code -- dnallm-mark/data/` — empty diff, the CI drift lane's exact check
- Untouched guarantees: `git status --porcelain` over `tests/fixtures/golden/`, `tests/tui/__snapshots__/`, `tui/` = empty; DNALLM sibling repo = 0 dirty entries; no push performed (orchestrator pushes to re-trigger PR #7's four lanes)

## WINDOWS #22 Note

WINDOWS #22 ("Full make-test gate blocked by 10 PRE-EXISTING base failures — 5 schema/determinism pins stale after data commit 9e803ca, 5 root-user chmod persist-failure sims") is **half-closed by this batch**: the schema/determinism half is resolved (all six drift-manifestation failures green; corpus re-synced and drift-gated). The chmod-sims half remains out of scope. Ledger status/disposition is the orchestrator's call — this SUMMARY is the record. (Note: the ledger's rendered table currently disagrees with its fenced JSON for rows 20/23/24/25/29 — pre-existing, unrelated; any ledger update should repair that first per gsd-tools' guidance.)

## Requirements Closed

- EEA-1 pexpect dev-group fix with lock discipline — done (9a225ed)
- EEA-2 helixgen info.path stripped — done (9a83066)
- EEA-3 helixgen dataset.species canonical — done (9a83066)
- EEA-4 data-chain re-sync + multi-species removal — done (c6b510f)
- EEA-5 new baseline pinned, all gates green — done (this file)
- EEA-6 process discipline — plain commits, no push, tui/DNALLM/goldens untouched, no new committed scripts

## Self-Check: PASSED

- Commits 9a225ed, 9a83066, c6b510f are ancestors of HEAD (verified via git log f044b0e..HEAD)
- All modified files committed; tracked working tree clean (`git status --porcelain` non-?? count = 0)
- Regenerated artifacts byte-identical to regeneration output (second `make data` no-op proven)
- Goldens/snapshots/tui/DNALLM untouched (verified)
