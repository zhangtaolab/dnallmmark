# Deferred Items — quick task 261014-dcl

Out-of-scope discoveries logged during execution. None are caused by
this task's changes (verified against the base commit 6df795d where
noted) and deliberately not fixed here — the scope boundary forbids
touching unrelated failures.

## Pre-existing full-suite failures (10 — unchanged by this task)

The full `make test` gate at the plan's close shows EXACTLY the ten
failures already documented in
`.planning/quick/261014-c2l-add-custom-model-dataset-storage-directo/deferred-items.md`
(stale schema/determinism pins after the helixgen data commit 9bc68e1,
plus the root-user chmod persist-failure simulations — three of the
latter live in tests/tui/test_services_download_queue.py and one in
tests/tui/test_pilot_data_manager.py, files this task touched; they
fail identically before and after).

## Pre-existing flake: the snapshot golden lane under load

`tests/tui/test_snapshots.py::test_golden_export_is_deterministic_across_instances`
(and, in loaded multi-file runs, occasionally a
`test_*_golden` compare such as `test_monitor_running_golden`)
intermittently fails with a byte mismatch. NOT introduced by this task:
probed at the TRUE base commit 6df795d in a scratch worktree, the
determinism test flaked ~2/17 isolated module runs (e.g. run 3 of 3 and
run 9 of 17), before any 261014-dcl change. The flake strikes randomly
under load; single-test reruns pass consistently. Root cause not
investigated (out of scope) — suspected wall-clock-sensitive render
state escaping the fixture freezes (cursor blink phase / spinner frame)
inside textual 8.2.8's `export_screenshot`. A fix would live in
`tests/tui/test_snapshots.py`'s freeze seams, not in this task's files.
