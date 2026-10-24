# Deferred items — quick task 261018-kvj

Out-of-scope discoveries logged during execution (the scope boundary:
only auto-fix issues directly caused by the current task's changes).

## 1. Baseline membership drift: 2F at execution (plan named 1F)

- `tests/tui/test_services_about.py::test_derive_about_data_default_root_is_the_repo_pyproject`
  asserts the repo pyproject version is `0.7.1`; the tree carries
  `1.2.0` since the post-08g version-bump commits (`0adac7a`, `effb5bf`).
  Fails identically on clean HEAD (verified via `git stash`); it will
  also fail in CI (not machine-local). Whichever task owns the next
  version bookkeeping should rebase this pin (or the version test
  should read `pyproject.toml` dynamically).
- `tests/tui/test_services_run_config.py::test_storage_overview_defaults_mirror_real_consumers`
  expects `pipeline/logs` absent ("fresh checkout" assumption); this
  dev box has a live `pipeline/logs` from real runs. Machine-local,
  fails identically on clean HEAD.

Both are PRE-EXISTING (zero new failures from this task; the full
suite is 2F/1919P with both members verified at base). The standing
rule's "1F baseline" is stale by one member — the version-pin failure
post-dates 261018-08g.

## 2. (none further)
