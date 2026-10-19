---
phase: 10-data-manager-downloads-verification
plan: 01
subsystem: tui-services
tags: [download-queue, modelscope-cli, subprocess, xdg-state, state-machine, killpg]

requires:
  - phase: 08-tui-foundation
    provides: settings.state_dir/atomic_write (the D-04 XDG state seam), the services-tier import lock
  - phase: 09-gauntlet
    provides: the LIST-argv subprocess discipline, injectable-runner seam idiom, run-id item tagging
provides:
  - DownloadQueueService — the persistent five-state download queue (D-05/D-06/D-08) with restart downgrade, corrupt quarantine, retry, cancel
  - Channel resolution (R-01 primary-else-alternate URL rule + the R-02 46/4 shape table) with repo-id allowlist
  - resolve_modelscope_cli probe (console script only; python -m modelscope probed dead)
  - compose_download_argv per shape (LIST argv, absolute local_dir, exact live-probed flag order)
  - The Popen engine: claim_next/run_task, daemon stderr reader with integer-percent throttling, cancel-aware reap, killpg SIGTERM/SIGKILL cancel, Pitfall-3 landing gate, shape-C rename, verbatim logs/<key>.log + first_real_error_line
  - The two recorded modelscope stderr fixtures (success / interrupted) for the parser lane
affects: [10-02 reconcile+overlay, 10-03 zenodo, 10-04 data-manager screen, 10-05 selection/env integration, 10-06 e2e]

actuals:
  tokens: 28248        # chars/4 over the realized diff (tui/services/download_queue.py + tests + fixtures)
  tasks: 3
  commits: 6           # MEASURED: git rev-list --count 71b05c4..HEAD (3 RED test commits + 3 GREEN feat commits, TDD)
plan_head_before: 71b05c468b18cd764a135f16d42c07192c57fb7c
plan_head_after: 93c4466287fe964e2c619276ec09285732826302

tech-stack:
  added: []            # zero new dependencies (modelscope stays an external probed CLI in no uv group)
  patterns:
    - "Popen-shaped injectable spawner seam (spawner(argv, **kwargs) -> Popen-like) — extends the gauntlet runner idiom to the cancellable process shape"
    - "cancel = flag + os.killpg on the owned process group (start_new_session spawn; SIGTERM, grace wait, SIGKILL escalation)"
    - "best-effort stderr progress parsing over recorded fixtures (ANSI strip + CR split + two live-probed regexes; None = indeterminate is first class)"

key-files:
  created:
    - tui/services/download_queue.py
    - tests/tui/test_services_download_queue.py
    - tests/tui/fixtures/modelscope_stderr_success.txt
    - tests/tui/fixtures/modelscope_stderr_interrupted.txt
  modified: []

key-decisions:
  - "Task 1 landed the channel resolver + CLI probe early (the plan's own ordering resolution: missing_datasets()/enqueue need resolve_channel; both land in this plan)"
  - "claim_next landed in Task 1 (the must_haves D-04 truth places it in the service surface; Task 3's run_task builds on it)"
  - "parse_progress returns INTEGER percents (the research snippet's dict values were strings; the plan's contract is integer-percent change throttling)"
  - "Enqueue precedence: existing-entry check first (D-08's unconditional already_queued truth) ahead of the unknown/disabled/cli gates"
  - "Behavior tests chosen over the source-level AST threading.Lock check (the plan-checker advisory; the Lock is documented + exercised, not AST-pinned)"

patterns-established:
  - "Quarantine-on-corrupt state recovery: os.replace to <name>.corrupt + diagnostic string return, never an exception, never silent loss"
  - "Engine event contract: QueueEvent(run_id, key, kind, state, last_percent, problems, details, log_path) — machine codes + data tokens, never copy"

requirements-completed: [DATA-01, DATA-02]

coverage:
  - id: D1
    description: "Persistent five-state download queue with XDG persistence, restart downgrade, corrupt quarantine, retry/cancel, and idempotent enqueue"
    requirement: DATA-02
    verification:
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py (Lane 1: 22 state-machine tests)"
        status: pass
  - id: D2
    description: "Channel resolution over the official registry (R-01 primary-else-alternate, R-02 46/4 census) + CLI probe + per-shape argv composition"
    requirement: DATA-01
    verification:
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py (Lane 2: census/R-01/argv/probe tests)"
        status: pass
  - id: D3
    description: "Popen execution engine: spawn/stream/reap/cancel with killpg, Pitfall-3 landing gate, shape-C rename, verbatim log capture, recorded-fixture parser"
    requirement: DATA-01
    verification:
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py (Lane 3: engine/parser tests incl. real-subprocess killpg cancel)"
        status: pass
  - id: D4
    description: "Full-suite + lint + typecheck gates green with the new module"
    requirement: DATA-01
    verification:
      - kind: integration
        ref: "make test (1010 collected = 954 baseline + 56 new, pytest + node 18/18, exit 0); make lint; make typecheck"
        status: pass
---

# Phase 10 Plan 01: Download Queue Service Core Summary

**One-liner:** The DATA-01/DATA-02 substrate — a persistent five-state download queue over the XDG state root, R-01/R-02 channel resolution over the official registry (46 downloadable / 4 disabled, census-pinned), and a killpg-cancellable Popen engine with live-probed progress parsing, a Pitfall-3 landing gate, shape-C rename, and verbatim per-key logs — zero textual, zero modelscope imports, 56 tier-1 tests across fake-spawner/fixture/real-subprocess lanes.

## What Was Built

### Task 1 — Queue state machine + XDG persistence + restart/corrupt recovery

`QUEUE_STATES` (D-02 verbatim five) / `SCHEMA_VERSION 1` / `download_queue.json` under `settings.state_dir()`; the canonical 12-field entry set (pinned by exact-set tests — zero credential surface, SC5/T-10-01-02); `load()` with downloading→pending downgrade (persisted per D-05, `interrupted=true`), failed-entries survive, corrupt/forward-schema quarantine to `.corrupt` sidecar with a diagnostic string; `enqueue` (idempotent per key, D-08) with `already_queued`/`unknown_key`/`disabled(reason+source_url)`/`cli_unavailable`/`enqueued` outcomes; `enqueue_all_missing()`; `retry` gating on failed/mismatch; `cancel` (pending→removed, downloading→flag+killpg SIGTERM, else noop); `claim_next` (D-04); `missing_datasets()` computed over the official registry + `registries.load_n_audit()` presence (7 missing GUE keys on the committed data). Per the plan's ordering instruction, the R-01/R-02 resolver + CLI probe landed inside this task (missing-set derivation needs them).

### Task 2 — R-01/R-02 channel resolution + CLI probe + argv composition

The 15-repo shape table at module top (the gauntlet `_AUDIT_SPLIT_ORDER` idiom): 7 shape-A repos / 5 shape-B repos / the shape-C repo with its 3-key subtree map / 2 shape-D repos. `resolve_channel` applies the R-01 primary-else-alternate host test, derives the repo id via urlparse path parsing, validates it against `^[\w.-]+/[\w.-]+$` before anything reaches argv (T-10-01-01), and degrades on unknown repos (`unknown_repo_shape`), no mirror (`no_modelscope_mirror`), malformed ids/paths. `compose_download_argv` emits the LIST argv with absolute `--local_dir` and the exact live-probed flag order; shape-D composes nothing. `resolve_modelscope_cli` probes explicit→venv-sibling→`shutil.which`→None. The 46/4 census is pinned COMPUTED over the committed registry (38 A + 5 B + 3 C; the exact 4 disabled keys with `shape_d_layout`).

### Task 3 — Popen execution engine + fixtures

`run_task` (never raises): re-probe CLI → resolve channel → compose → spawn via the injectable spawner (`start_new_session=True`, PIPEs, env exactly `dict(os.environ)`) → daemon reader threads (stderr through `clean_chunk`/`parse_progress`, `progress_cb` fired at most once per integer-percent change, None = indeterminate) → cancel-aware reap (5s chunks; SIGTERM grace 10s; SIGKILL escalation on the whole group) → classification (nonzero: `cancelled_by_operator` when flagged, else `exit_<code>`; zero: the Pitfall-3 landing gate). The landing gate runs the shape-C rename four cases first, then requires all three split CSVs under `pipeline/datasets/<Group>/<final_task_dir>` — exit 0 + success marker + empty landing lands `landing_incomplete` naming the missing relative paths. Verbatim `[argv]/[exit]/[stdout]/[stderr]` capture at `logs/<sanitized-key>.log` under the state root; `first_real_error_line` skips the two pkg_resources noise lines. Two recorded stderr fixtures seeded from the research's verbatim captures. The real-subprocess cancel lane proves killpg group death (`os.killpg(pgid, 0)` raises `ProcessLookupError`), the failed/cancelled transition, and partials-retained — with zero modelscope dependency.

## Verification Evidence

- `uv run --group dev --group tui pytest tests/tui/test_services_download_queue.py -q` — **56 passed** (all three lanes).
- `uv run --group dev --group tui pytest tests/tui -q` — **440 passed** (import lock, settings seam, about CJK scan included; no existing test modified).
- `make lint` — ruff **All checks passed** (the new module joins the PHASE8_TUI glob automatically).
- `make typecheck` — ty **All checks passed**.
- `make test` — **exit 0**; pytest 1010 collected (954 baseline + 56 new), node lane 18/18.
- modelscope-import prohibition: `grep -n "import modelscope\|from modelscope" tui/services/download_queue.py; test $? -eq 1` — clean (D-01).
- R-02 census gate: the 46/4 assertion computed over the committed registry — the plan's loud-drift tripwire.

## Deviations from Plan

**1. [Task attribution] claim_next landed in Task 1, not Task 3**
- **Found during:** Task 1 GREEN (the no-credential-fields test exercises the downloading transition)
- **Resolution:** The must_haves D-04 truth already places `claim_next()` in the service surface ("the service exposes claim_next()"), so it landed with the state machine; Task 3's run_task builds on it. No behavior difference.

**2. [Plan-directed ordering] Channel resolver + CLI probe landed in Task 1**
- The plan self-acknowledges the wrinkle ("land the resolver first inside this task if ordering requires; both land in this plan") — executed exactly as instructed. Task 2's RED surface was therefore argv composition (6 failing tests) while the census/R-01/probe pins went green against the Task-1 implementation.

**3. [Rule 1 - Bug] parse_progress returns integer percents**
- The research Code Examples snippet returns string dict values (`dict(files)`); the plan's contract is "fires at most once per integer-percent change". Coerced to int at the parser boundary so the whole flow (callback, last_percent, QueueEvent) carries integers.

No other deviations — scope stayed surgical (only the four planned files; no pipeline/ edits, no registry writes, no uv/pyproject changes).

## TDD Discipline

Each task ran RED → GREEN with separate commits: `9bb8107`/`25714cb` (Task 1: 19 target tests failing on missing behavior), `49569bc`/`129b093` (Task 2: 6 argv tests failing on the missing composer), `1f093dd`/`93c4466` (Task 3: 19 engine/parser/cancel tests failing). No REFACTOR commits needed beyond inline cleanup before each GREEN commit (dead-parameter removal; landing-gate return-shape cleanup).

## Known Stubs

None. The `reconcile` persisted field is `null` by design this plan (10-02 inserts the reconcile gate before done — the plan's own truth, not a stub); the `runner` constructor seam is stored unused for 10-02's audit leg, exactly as the plan's constructor spec prescribes.

## Self-Check: PASSED

All four created files exist on disk; all six commits are ancestors of HEAD (`9bb8107`, `25714cb`, `49569bc`, `129b093`, `1f093dd`, `93c4466`).
