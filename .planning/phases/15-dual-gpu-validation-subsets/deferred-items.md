# Phase 15 Deferred Items

Out-of-scope discoveries logged during plan execution (never fixed
in-phase; each routes to its owning flow).

## 15-04 (2026-10-20): test_export_runs D-15 test hangs when
huggingface.co is unreachable

- **Found during:** 15-04 Task 2 verify lane
  (`pytest tests/test_export_runs.py`).
- **Item:** `test_d15_evaluate_cross_validates_suite_mapped_metric_conventions`
  (tests/test_export_runs.py:779, pre-existing from the D-15 era) calls
  `evaluate.load("pearsonr"/"spearmanr")`, which HEADs huggingface.co
  for an etag BEFORE falling back to the local module cache. On this
  AutoDL box huggingface.co TCP connects are DROPPED (no RST), so each
  HEAD blocks to the OS TCP timeout with no fast ConnectionError — the
  suite hangs >9 min instead of falling back to the cached metric
  modules (both are fully cached under HF_HOME).
- **Not fixed (out of scope):** the file is untouched by 15-04; a code
  fix (explicit local_files_only / an offline marker / a skip-if-no-
  network guard) is the test owner's decision.
- **Workaround used by the 15-04 verify lane (environment, not code):**
  `HF_ENDPOINT=https://hf-mirror.com` (reachable on this box) — the D-15
  test then passes in ~17 s. Later executors running the export suite on
  this box should export `HF_HOME=/root/autodl-tmp/.cache/hf
  HF_ENDPOINT=https://hf-mirror.com` for the lane.
