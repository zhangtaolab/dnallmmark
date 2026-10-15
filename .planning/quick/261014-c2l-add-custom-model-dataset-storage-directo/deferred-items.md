# Deferred Items — quick task 261014-c2l

Out-of-scope discoveries logged during execution (pre-existing at the
base commit 8f3af3c, verified in a temporary worktree; NOT caused by
this task's changes and deliberately not fixed here — the scope
boundary forbids touching unrelated failures):

## Pre-existing full-suite failures (10, all failing identically at 8f3af3c)

1. **tests/test_schemas.py::test_committed_file_matches_schema[model_performance-path29/30/31]**
   and **test_schema_bucket_counts_are_pinned** and
   **test_dataset_enums_match_committed_data_across_all_schemas** —
   the committed schema pins/bucket counts/enums are stale relative to
   the helixgen model-performance data landed in commit 9e803ca
   ("data: helixgen model performance (2stage, 2stage-w015625, mlm) +
   multi-species comparison"): the three new `*_performance.json`
   files (paths 29-31) do not satisfy the committed schema and the
   pinned aggregate counts drifted. Needs a data-side reconciliation
   (schema pin refresh or data fix) by the data owner.

2. **tests/test_determinism.py::test_chain_is_deterministic_and_matches_committed**
   — the derived data chain no longer matches the committed derived
   files after the same 9e803ca data commit (stale
   `models_comparison*` / `tasks.json` regeneration needed:
   `make data`).

3. **tests/tui/test_services_download_queue.py::test_enqueue_persist_failure_refused_no_ghost_row /
   test_claim_next_persist_failure_reverts_returns_none /
   test_run_task_persist_failure_still_returns_event** and
   **tests/tui/test_pilot_data_manager.py::test_driver_exits_bounded_when_claim_cannot_persist_cr02**
   — the persist-FAILURE simulations (chmod read-only style) are
   ineffective when the suite runs as root (root bypasses the
   read-only permission, so `enqueue` succeeds and returns
   'enqueued' instead of 'persist_failed'). Environmental: green under
   a non-root runner, red as root. Consider a monkeypatched
   `settings.atomic_write` raising side effect instead of
   filesystem permissions, or a root-detecting skip.
