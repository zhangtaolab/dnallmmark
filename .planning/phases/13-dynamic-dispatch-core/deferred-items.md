# Phase 13 deferred items

Out-of-scope discoveries logged during execution (scope boundary: only
issues directly caused by the current task's changes are auto-fixed).

## 2026-10-20 (13-02 full-gate run, `make test`)

- **`tests/tui/test_services_about.py::test_derive_about_data_default_root_is_the_repo_pyproject` fails (pre-existing).**
  The test pins `software_version == "1.2.0"` while `pyproject.toml` is
  `1.3.0` — stale since the v1.3 milestone bump (commit `9a39bde`,
  verified an ancestor of the 13-02 plan base `fea5d8d`, i.e. it fails
  with or without this plan's changes). Fix is maintainer-side: follow
  the `3961d2c` precedent and re-pin, or derive the expected version
  from `pyproject.toml`. Not touched by 13-02 (out of blast radius).
- **Baseline-count drift on this box: recorded 2F/1919P (261018-kvj) vs observed 7F/2030P/3S.**
  Six of the seven observed failures are the documented environmental
  chmod artifacts (persist-failure simulations via `state.chmod(0o500)`
  are ineffective when pytest runs as root — user memory: "6 chmod-based
  test failures are environmental"); the seventh is the version pin
  above. None import or exercise any file 13-02 changed
  (`pipeline/dispatch_core.py`, `pipeline/run_sweep_shard.py`,
  `Makefile`, `tests/test_dispatch_core.py`). Re-baselining is a
  maintainer decision, deliberately not done here (the 261018-kvj
  precedent: baseline members are recorded, not re-baselined, by
  executors).
