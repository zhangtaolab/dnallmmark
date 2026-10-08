# Pin Validation — data-chain environment (D-05 / D-06 evidence)

**Validated:** 2026-10-08
**Environment:** repo-local uv venv (`.venv`), CPython 3.13.16 (uv-managed, aarch64)
**Generators:** PRE-FIX state at tag `data-v1` (commit `788e909`) — this validation ran before any FIX-05 determinism edit (plan 01-03 lands after)
**Conclusion:** inventory fully explained — pins are authoritative (see "D-06 conclusion")

## Resolved versions (from uv.lock)

| Package | Resolved | Bound (pyproject `data` group) |
|---------|----------|-------------------------------|
| pandas  | 2.3.3    | `>=2.2,<3.0` (D-05 floor)     |
| numpy   | 2.5.3    | `>=2.0,<3`                    |

Single resolution per package across all dependency groups (`uv.lock` holds exactly one
`numpy` and one `pandas` package block; 60 blocks total including the GPU `pipeline` group,
which `uv sync` never installs by default — `default-groups = ["data"]`).
The interpreter is the uv-managed CPython 3.13.16, strictly isolated from
`/home/forrest/Github/DNALLM/.venv` (D-07).

## Commands (exact, from a clean clone at tag `data-v1` + plan 01-01 task 2 state)

```bash
# Environment build
~/.local/bin/uv venv .venv --python 3.13
~/.local/bin/uv sync                       # installs data group only: pandas 2.3.3, numpy 2.5.3
~/.local/bin/uv export --group data --no-emit-project -o requirements.txt
~/.local/bin/uv lock --check               # exit 0 — stable deterministic resolution

# Scratch regeneration (mirror layout required by generate-tasks-index.js __dirname paths)
rm -rf /tmp/dnallm-pinval
mkdir -p /tmp/dnallm-pinval/scripts /tmp/dnallm-pinval/dnallm-mark/data
cp -r dnallm-mark/data/model_performance /tmp/dnallm-pinval/dnallm-mark/data/
cp scripts/generate-tasks-index.js /tmp/dnallm-pinval/scripts/

cd /tmp/dnallm-pinval/dnallm-mark/data     # both Python scripts are CWD-sensitive
/home/forrest/Github/dnallmmark/.venv/bin/python /home/forrest/Github/dnallmmark/script/summarize_comparison.py
/home/forrest/Github/dnallmmark/.venv/bin/python /home/forrest/Github/dnallmmark/script/get_task_performance.py
node /tmp/dnallm-pinval/scripts/generate-tasks-index.js

# Value comparison (order-insensitive) — per file, from the repo root
python3 baseline/compare.py [--summary-json] dnallm-mark/data/<file> /tmp/dnallm-pinval/dnallm-mark/data/<file>
```

## Per-file diff inventory (complete)

47 of 52 derived files are **VALUES IDENTICAL (order-insensitive)**: every
`task_performance/*.json` file (47/47). The remaining 5:

| File | Total diffs | Diff classes |
|------|-------------|--------------|
| `models_comparison.json`         | 42 | 38 FLOAT_ULP + 4 FLOAT_BIG |
| `models_comparison_animal.json`  | 33 | 33 FLOAT_ULP              |
| `models_comparison_plant.json`   | 41 | 41 FLOAT_ULP              |
| `models_comparison_microbe.json` | 42 | 40 FLOAT_ULP + 2 FLOAT_BIG |
| `tasks.json`                     | 2  | 2 VALUE                   |

### FLOAT_ULP — `sum_zscore` only (152 occurrences, max rel 2.41e-14)

Every ULP-class diff in every comparison file sits on a `sum_zscore` field. Example:
`36.08327926630596` vs `36.08327926630597` (rel ≈ 3.9e-16).

**Root cause:** per-dataset z-scores use `np.mean`/`np.std`
(`script/summarize_comparison.py:143-144`); float summation behavior differs between the
original (unknown, 2026-03-31) generation environment and numpy 2.5.3. Every field computed
without mean/std — raw scores, MinMax, robust, `rank_score`, top-K counts, FLOPs sums,
sample counts — is bit-identical, which is the signature of summation-order noise, not a
pandas semantic change (pandas 3.0 dtype/COW behavior is excluded by the `<3.0` bound).

### FLOAT_BIG — `rank` fields of exact-tie pairs only (6 occurrences, 3 pairs)

Rank swaps occur **only** between models whose `rank_score` is exactly equal; the tie order
is decided by Python's stable `sorted()` falling back to `models_info` insertion order,
which derives from `os.listdir` on the generating machine (the exact class of
nondeterminism FIX-05 eliminates in plan 01-03).

| File | Tie pair | rank_score | Committed ranks | Regenerated ranks |
|------|----------|-----------|-----------------|-------------------|
| `models_comparison.json` | Omni-DNA-700M ↔ plant-dnabert-6mer | 1232.0 | 13 / 14 | 14 / 13 |
| `models_comparison.json` | gena-lm-bigbird-base-t2t ↔ hyenadna-large-1m-seqlen-hf | 749.0 | 29 / 30 | 30 / 29 |
| `models_comparison_microbe.json` | agro-nucleotide-transformer-1b ↔ plant-dnamamba2-BPE | 448.0 | 3 / 2 | 2 / 3 |

The first two pairs were pre-documented in the phase research. The microbe pair is an
**investigated addition** to that literal inventory (see "Inventory investigation" below).

### VALUE — `tasks.json` only (2 occurrences)

- `/generatedAt`: `'2026-03-31'` vs `'2026-10-08'` — the pre-fix generator stamps the live
  date (`scripts/generate-tasks-index.js:50`); the committed index was generated 2026-03-31.
  (Plan 01-03 drops the field per Pitfall 6.)
- `/tasks[0]/metric` (BEND__CpG_methylation): `'auprc'` vs `'AUPRC'` — the committed index
  predates the current `task_performance` casing; the pre-fix JS index generator does not
  apply `summarize_comparison.py`'s `metric_key_map` lowercasing. Known stale-derived-data
  instance (research Pitfall 9), reconciled by plan 01-03's regeneration.

## Inventory investigation (D-06): the third tie pair

The plan's expected inventory named "exactly the two exact-tie pairs" (both in the global
`models_comparison.json`). The validation run surfaced a third pair in the per-species
microbe file. Investigation (2026-10-08):

- Both `agro-nucleotide-transformer-1b` and `plant-dnamamba2-BPE` carry `rank_score = 448.0`
  in the **committed** microbe file and in the **regenerated** one — an exact tie in both.
- The swapped values are only the `rank` ordinals (2/3); `rank_score` itself is identical on
  both sides, and the two models' `sum_zscore` values differ only within the ULP noise band.
- Mechanism is identical to the pre-documented pairs: exact tie → stable sort →
  insertion-order fallback → `os.listdir` order differs across machines. The per-species
  arenas simply re-rank model subsets, exposing tie pairs (here 448.0) that the global file
  does not (global ties: 1232.0, 749.0).

**Verdict:** same root cause, no new failure class, no value outside the explained
taxonomy — documented rather than escalated. (The global tie pairs do not appear in the
per-species files because arena rank_scores differ from the global ones.)

## Determinism check (same machine, run-twice)

The full chain was rerun with the pinned environment; all 52 outputs (5 comparison/index
files + 47 task files) were **byte-identical** across runs (`cmp` per file). Cross-machine
byte stability is NOT claimed for the pre-fix generators — `os.listdir` order and the
`generatedAt` stamp are exactly what FIX-05 (plan 01-03) addresses.

## D-06 conclusion

Every observed diff falls inside the root-caused taxonomy above: numpy mean/std ULP noise
on `sum_zscore` only (≤ 2.41e-14), rank swaps only between exactly-tied models, and the two
pre-documented `tasks.json` VALUE diffs. No unexplained value difference exists in any of
the 52 derived files; 47/47 `task_performance` files are value-identical. Per D-05/D-06 the
floor pins (`pandas>=2.2,<3.0`, `numpy>=2.0,<3`) plus the committed `uv.lock`
(pandas 2.3.3 / numpy 2.5.3) are **authoritative** for the data chain.

Re-validation trigger: any change to the pins, or any future regeneration producing a diff
outside this inventory, re-opens D-06 investigation.
