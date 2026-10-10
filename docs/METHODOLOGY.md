# Leaderboard Methodology

This document is the single authoritative description of how DNALLM-Mark
turns per-model benchmark results into the numbers on the public
leaderboard. Every section names the script that implements it, so a
reviewer can trace prose to code; the scripts' own docstrings carry the
same statements at the implementation site.

The whole chain is deterministic (sorted iteration, `sort_keys`
serialization, no live clock) and byte-stable: re-running `make data` over
the committed inputs reproduces every artifact bit-for-bit — an invariant
CI enforces on every pull request (the [drift
job](../.github/workflows/ci.yml) fails if regenerating the data tree
produces any diff).

## Inputs

- **Per-model results** — `dnallm-mark/data/model_performance/{model}_performance.json`
  (one file per model; the pipeline's output contract, or the unified
  exporter at E2'). Missing metric values are empty strings, never `null`
  or `0`.
- **The dataset registry** — `pipeline/datasets_info.json` (the single
  source of truth, D-10), including each dataset's primary metric
  (`metric`), arena (`Category`), and provenance columns. Provenance —
  source, citation, license, and download URLs for all 50 datasets — is
  published in [`DATA.md`](../DATA.md) and as the downloadable
  [`data/provenance.json`](../dnallm-mark/data/provenance.json) /
  [`data/provenance.csv`](../dnallm-mark/data/provenance.csv) dual
  artifact (`script/build_provenance.py`).

## Per-task normalization (four methods)

Implemented in `script/summarize_comparison.py`
(`calculate_dataset_stats`). On each individual task, every model that was
evaluated receives four normalized scores:

1. **Rank Score** — competition ranking with `method='min'` (tied raw
   scores share the best rank), converted to points as `N − rank`, where
   `N` is the number of models evaluated on that task. Rank 1 earns `N−1`
   points; last place earns 0.
2. **MinMax** — `(score − min) / (max − min)`, scaled to [0, 1]; all zeros
   when `max == min`.
3. **Z-Score** — `(score − mean) / std` over the task's score
   distribution; all zeros when `std == 0`.
4. **Robust** — `(score − median) / IQR` (quartiles at 25/50/75),
   resistant to outlier scores; all zeros when `IQR == 0`.

**No imputation:** a model not evaluated on a task simply receives no
contribution for that task. Sums never invent zeros for missing runs.

## Aggregation into leaderboard views

Implemented in `script/summarize_comparison.py` (`aggregate_models`,
`main`). The per-task scores are **summed** across the view's tasks into
`rank_score`, `sum_minmax`, `sum_zscore`, and `sum_robust`; the block also
carries `samples` (task coverage), `avg_raw`, `avg_rank`, Top-K placement
counts (K = 1/3/5/8/10, from the true per-task ranks), and efficiency
totals (`sum_PFLOPs`, `avg_PFLOPs` — measured training FLOPs converted to
PetaFLOPs). The overall `rank` orders models by `rank_score` descending.

**Arena grouping** (FIX-02) comes from the human-reviewed `Category`
column of the registry — never from producer strings — producing the four
views: `models_comparison.json` (all tasks) plus the `animal`, `plant`,
and `microbe` files. "Multiple"-origin datasets classify into their
majority arena (`Animals`, confirmed at the category review gate).

### The dual views (F6): rank vs weighted

The leaderboard exposes two ordering views of the same data:

- **Weighted (default public view)** — `performance.weighted_score`: the
  model's summed per-task z-scores divided by `N`, the aggregation view's
  full task count, i.e. a uniform `1/N` difficulty weight per task. Same
  no-imputation convention as the sums: a model missing tasks contributes
  nothing for them (numerator) while the denominator still counts the
  view's tasks.
- **Raw Rank** — `performance.rank_score` (the rank-score sum above), one
  click away in the UI.

Both values are **precomputed offline** and only ever read by the
frontend; nothing is recomputed client-side (the divergent client-side
recompute was dead code, removed in 06-04 — DATA-07).

## Confidence intervals (vendored suite statistics)

Implemented as a verbatim-vendored copy of the dnallm suite's
`aggregate_seeds` in `script/export_runs.py` (pinned to the suite
semantics by `tests/test_vendored_stats.py`; behavioral edits are
forbidden). Thresholds:

| Seeds per cell | CI reported |
| --- | --- |
| `n < 3` | none — `ci95: null`, `method: "none"` (never a vacuous interval) |
| `3 <= n < 10` | Student-t interval (or omitted under the `omit` policy) |
| `n >= 10` | seeded percentile bootstrap (identical data + seed → identical interval) |

## The CI-overlap tie rule (F6 / REV-04)

Implemented in `script/summarize_comparison.py`
(`calculate_dataset_stats` with a `ci_map`). When closed 95% intervals are
available for a task's models, "tie" is widened from exact score equality
to **closed-interval overlap**: two models tie when their intervals
intersect, touching at exactly one point included. Overlapping models form
**connected components** of the overlap graph (A~B and B~C tie all three
even when A and C do not overlap), and every member receives the
component's **minimum** rank under the `method='min'` convention, so
`task_rank_score = N − rank` stays coherent. Intervals are **consumed
here, never computed** — the single sanctioned producer is the vendored
`aggregate_seeds`. Models with no interval entry keep pure score ranking,
so single-run data (which has no CI source) reproduces the exact-tie
output byte-identically.

## Pairwise significance: the permutation family

Implemented in `script/permutation_tests.py`; published as
[`data/permutation_tests.json`](../dnallm-mark/data/permutation_tests.json)
(schema: [`schemas/permutation_tests.json`](../schemas/permutation_tests.json)).
For every model pair in the all-arena aggregate view:

- a two-sided **paired permutation test** on the per-task z-score vectors
  (paired by task; the null distribution flips the sign of each per-task
  difference), **10,000 shuffles**, `rng`-seeded (42, fresh per pair so
  p-values are independent of pair order);
- pairs align on their **common task set**; a pair with zero common tasks
  is excluded and disclosed in `info.excluded_pairs`;
- **Benjamini-Hochberg** correction over the tested family (C(42,2) = 861
  pairs at the current 42-model corpus; C(62,2) = 1,891 post-E2'), with
  the family size disclosed in the artifact's `info` block;
  `significant` flags `p_adj <= 0.05`.

Runs offline at regeneration time (`make data`), never at page render.

## Efficiency metrics

`FLOPs` per (model, task) are measured during fine-tuning by the
pipeline's forward-hook `FlopsCounter`, flow through the performance JSONs
unchanged, and are aggregated as `sum_PFLOPs` / `avg_PFLOPs`
(÷ 10^15 → PetaFLOPs) by `script/summarize_comparison.py`. The main-page
scatter plot plots them against rank score.

## Where the code lives

| Concern | Script |
| --- | --- |
| Per-task normalization, tie rule, aggregation, dual views | `script/summarize_comparison.py` |
| Seed aggregation + confidence intervals (vendored) | `script/export_runs.py` |
| Permutation family | `script/permutation_tests.py` |
| Provenance table | `script/build_provenance.py` |
| Registry (single source of truth) | `pipeline/datasets_info.json` |
| Fine-tuning + FLOPs measurement | `pipeline/run_finetune.py` |
| Artifact schemas | `schemas/*.json` |

For how to reproduce the leaderboard from a fresh clone, see the
[Reproducing the leaderboard](../README.md#reproducing-the-leaderboard)
section of the README. For adding a new model or dataset, see
[Onboarding](ONBOARDING.md).
