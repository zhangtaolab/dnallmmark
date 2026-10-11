# Pre-Revision Data Baseline (immutable comparison copy)

- **Source:** git commit `a44d310` (`dnallm-mark/data/` tree, 94 files) — the state
  serving https://dnallmmark.org/ before the revision merge; the numbers the
  manuscript revision is measured against.
- **Purpose:** old-vs-new comparison for the E2' re-run (before/after evidence per
  reviewer DATA-01). This copy is NEVER regenerated, overwritten, or deleted —
  `make data` operates only on `dnallm-mark/data/`; comparison artifacts diff
  against THIS directory.
- **Integrity:** `baseline/pre-revision-data.sha256` (sha256sum -c form); also
  recoverable from git tag `data-v1` (788e909) and history.
- **Frozen:** 2026-10-11 by maintainer directive ("之前的数据需要用来与新跑的做对比，不能删除或者覆盖").
