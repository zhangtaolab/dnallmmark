# Deferred Items — quick task 261017-mad

Out-of-scope discoveries made during execution (recorded per the scope
boundary; NOT fixed by this task).

## 1. Load-timing flake in `test_monitor_running_golden` (pre-existing, observed once at the pre-task baseline)

- **Found during:** Task 3 pre-work — the FIRST full-suite baseline run
  (before any task edit), `uv run --group dev --group tui pytest -q`.
- **Observation:** that one run failed
  `tests/tui/test_snapshots.py::test_monitor_running_golden` with a
  `.terminal-<id>-matrix` mismatch — the SECOND full-suite run (same
  command, zero changes between) passed at exactly the expected baseline
  membership `1 failed / 1867 passed`, and the snapshots module passed
  11/11 in isolation twice. Not caused by this task's changes (it
  predates them); not reproducible on demand.
- **Mechanism (diagnosed, not fixed):** the `terminal-<id>` in rich's
  `export_svg` is `zlib.adler32` over the REPR OF EVERY RENDERED
  SEGMENT (`rich/console.py:2475-2479`) — a content hash, not a random
  id. So under full-suite load some segment (attribute or text)
  differed from the committed golden once. All golden-fixture data in
  `_running_monitor_service` is frozen (elapsed/ETA/done/total/
  cells/resume counts), and the 2s `set_interval` frontier tick
  re-renders idempotently over that frozen data — the residual suspect
  is a load-dependent refresh/animation artifact captured mid-flight at
  export time.
- **Scope ruling:** pre-existing, unrelated files, no task change
  touches the monitor screen or the snapshots — out of scope per the
  fix discipline. Recorded to `.planning/WINDOWS.md` (kind deviation)
  so it is visible at ship time.
- **This task's final gate:** the full suite and the snapshots module
  both green; membership exactly 1F/1869P + node 26/26.
