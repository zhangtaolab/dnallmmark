# Changelog

Per-version registry for the leaderboard's derived data, following the
lm-evaluation-harness changelog convention (DATA-02). Every
result-affecting change to `dnallm-mark/data/` lands with a section here
recording the date, the `data_version` stamp carried in
`dnallm-mark/data/manifest.json`, the change-category counts from the
migration inventory, and a link to the machine-readable inventory artifact.

## Version convention

- **data-v1** — the pre-fix byte baseline, frozen at git tag `data-v1`
  (SHA256 manifest: `baseline/data-v1.sha256`). Numbers from the original
  single-run aggregation.
- **1.1.0** — F6 methodology fields: the z-score × uniform-difficulty
  weighted view (`weighted_score`), the CI-overlap tie rule, and the
  pairwise permutation-test artifact. **No existing number moved** (the
  inventory below shows additions only); the public default view switches
  to the weighted view. No intermediate git tag — `data_version` 1.1.0 is
  stamped in `manifest.json` only.
- **2.0.0 (data-v2, after E2')** — the three-seed full re-run numbers:
  seeded statistics, CI-backed tie groups, and the C(62,2)=1891 permutation
  family. Tagged `data-v2` at the maintainer sign-off gate (categorized
  inventory → sign-off → tag + SHA256 manifest; never auto-tagged).

## [1.1.0] - 2026-10-10

**data_version:** 1.1.0 · **generated_from:** `73006a0464c6dcdf0c28a29a48cdfb829b0fba6c`
(stamped in [`dnallm-mark/data/manifest.json`](dnallm-mark/data/manifest.json))

### Changes

| Category | Count | Files |
|----------|-------|-------|
| `EXTRA_IN_REGEN` (new `weighted_score` key per model entry) | 168 | 4 × `models_comparison{,_animal,_plant,_microbe}.json` (42 models each) |
| New artifact | 2 | `dnallm-mark/data/permutation_tests.json`, `dnallm-mark/data/manifest.json` |
| Existing values moved | **0** | — `tasks.json` byte-identical; no FLOAT/INT/VALUE diffs anywhere |

Machine-readable inventory: [`baseline/f6-migration-inventory.json`](baseline/f6-migration-inventory.json)
(7 derived files: 4 changed, 2 new, 1 identical; 168 diffs, all
attributable to the `weighted_score` field addition).

### Methodology (REV-04 / F6)

- **Weighted dual view (F6 Q2, Q4):** every model's performance block gains
  `weighted_score` = Σ per-task z-score ÷ (task count of the aggregation
  view) — uniform difficulty weight, no imputation. The public leaderboard
  DEFAULT VIEW switches to Weighted; the raw Rank view stays one click away.
  The weighted value is precomputed offline and only selected client-side.
- **CI-overlap tie rule (F6 Q1):** per-task ranking now supports tie groups
  from overlapping 95% confidence intervals (closed intervals; connected
  components share the component's minimum rank). Interval semantics come
  from the single vendored statistical source (`aggregate_seeds`: n<3 → no
  interval, 3≤n<10 → t-interval, n≥10 → seeded bootstrap), so E2' three-seed
  data gets t-intervals (df=2), never bootstrap. On the current single-run
  data there is no CI source and the rule is vacuous by design — its
  behavior is pinned by fixture tests, including the CpG top-10 case
  (AUPRC span 0.0021039 renders as a tie at n=3).
- **Permutation family (F6 Q3, D-17/OQ5):** pairwise model comparisons on
  the aggregate view — per-task z-score vectors, paired permutation test
  (`permutation_type="samples"`), 10,000 shuffles, rng=42, BH-corrected at
  FDR 0.05 over the disclosed C(42,2)=**861**-pair family (0 pairs excluded
  for insufficient task overlap; 657 significant). Published as a committed
  offline artifact; the family grows to C(62,2)=1891 at data-v2.
- **Stamped footer (DATA-06):** the leaderboard footer now shows the
  generation date and data version from `manifest.json` — the live clock is
  gone.
- **No intermediate tag (D-17/OQ3):** `data_version` 1.1.0 exists only as
  the manifest stamp + this section; the next git tag is `data-v2` at the
  maintainer gate after E2'.

### Alias normalization (D-18, 2026-10-10)

`plant-dnamamba2-BPE` → `PlantDNAMamba2-BPE`: the committed results file
was renamed to the unified-registry key (`git mv`, one key per model — the
key==name contract). Only the file name and the leaderboard alias (derived
from it) change; scores are untouched.

| Category | Count | Files |
|----------|-------|-------|
| `MISSING_IN_REGEN` / `EXTRA_IN_REGEN` (the one alias key, per file) | 4 + 4 | 4 × `models_comparison{,_animal,_plant,_microbe}.json` |
| `FLOAT_ULP` (zscore-sum fields only; max rel. 5.9e-15) | 296 | 4 × `models_comparison*.json` |
| Pair churn in `permutation_tests.json` (the renamed model's 41 pairs; array-positional) | 1724 | `permutation_tests.json` |
| `VALUE` (`generated_from` restamp) | 1 | `manifest.json` |
| Byte-identical | 0 diffs | `tasks.json` |

Attribution (verified at migration time): exactly one model's key churns
in every comparison file; `rank`, `rank_score`, `samples`, and all Top-K
counts are unchanged for all 41 shared models; the only comparison-value
movement is `sum_zscore`/`weighted_score` at ULP scale (≤5.9e-15 relative)
— the documented float summation-order class (the alias sorts at a
different position, reordering iteration), same phenomenon as the Phase-1
PIN-VALIDATION `sum_zscore` ULP finding. In `permutation_tests.json` every
pair whose identity is unchanged (820/861) has a byte-identical p-value
and significance flag — zero p-value movement anywhere; the 1724 diffs are
the 41 renamed pairs changing identity plus the array-positional index
shifts those moves cause (the artifact is a sorted list, so compare.py
matches moved entries cross-wise). `manifest.json` carries the pre-rename
commit restamp per the 05-02 convention; `DATA_VERSION` stays 1.1.0.

Machine-readable inventory: [`baseline/d18-alias-inventory.json`](baseline/d18-alias-inventory.json)
(7 derived files: 6 changed, 1 identical; 2029 diffs, all attributed above).
