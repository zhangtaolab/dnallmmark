---
phase: 10-data-manager-downloads-verification
plan: 03
subsystem: tui-services
tags: [zenodo, bundle-download, zip-slip, probe, queue-integration, i18n, strings, data-manager]

requires:
  - phase: 10-data-manager-downloads-verification
    provides: "10-01's DownloadQueueService legs (claim_next, missing_datasets, _missing_splits landing checker) and 10-02's reconcile_dataset leg + done-gate vocabulary the zenodo branch dispatches into"
  - phase: 10-data-manager-downloads-verification
    provides: "10-UI-SPEC Copywriting Contract — the verbatim copy table + the DL_/QUEUE_ prefix split + the ENV_ROUTE [3] amendment this plan lands"
provides:
  - probe_zenodo_public — the D-12 four-state GET probe (frozen URL, ~15s timeout, session-memory only); the activation flip needs zero code change
  - The bundle driver — parse_record_files (dual-spelling defensive), download_bundle_files (streamed 64 KiB, per-file failure collection, traversal-name refusal), extract_bundle_archives (zip-slip guarded)
  - The zenodo-kind queue integration — KIND_ZENODO_BUNDLE + ZENODO_BUNDLE_KEY + CLI-free enqueue_zenodo + the run_task dispatch branch (probe -> parse -> staging download -> guarded extract -> per-key landing check -> per-key reconcile; entry.reconcile carries the per-key verdict map)
  - The complete DL_/QUEUE_ string block (47 constants, exactly the names 10-04/10-05 reference) + the SEL_ d-enqueue amendments + the ENV_ROUTE [3] amendment — the I18N-01 single home for both remaining screens
affects: [10-04 data-manager screen (pure consumer of the strings + the queue surface), 10-05 selection/env amendments (SEL_/ENV_ROUTE consumers), 10-06 e2e]

actuals:
  tokens: 17893     # chars/4 over the realized diff (91bb4fb..8b9b063)
  tasks: 3
  commits: 6        # MEASURED: git rev-list --count 91bb4fb..8b9b063 (3 RED test + 3 GREEN feat, TDD)
plan_head_before: 91bb4fb9b2aa8334db82143fe24420526dd17080
plan_head_after: 8b9b063d54111cf72c769859bacb82a0fefb71da

tech-stack:
  added: []          # stdlib urllib + zipfile only (the prohibition held; requests/httpx never touched)
  patterns:
    - "Kind-dispatch at the run_task head: the entry's persisted kind routes zenodo_bundle entries to a wholly separate branch — the 10-01/10-02 dataset legs are byte-untouched"
    - "Derive-never-hardcode over an untrusted API document: dual-spelling per-field fallbacks, zero-conforming -> explicit empty -> failed record_file_list_unreadable"
    - "Resolve+is_relative_to zip-slip guard on every extracted member plus the download-side staging-name refusal — both traversal classes pinned by fixtures"
    - "One urlopen-shaped constructor seam (zenodo_fetch) serving probe, record fetch, and file downloads — the whole bundle lane is offline-testable"

key-files:
  created:
    - tui/services/zenodo_bundle.py
    - tests/tui/test_services_zenodo_bundle.py
  modified:
    - tui/services/download_queue.py
    - tui/strings.py
    - tests/tui/test_services_download_queue.py

key-decisions:
  - "The bundle run's missing-set source is missing_datasets() (the 10-01 Task-1 checker the plan names): the committed n_audit view, not a disk scan — the landing check then proves each key on disk per key"
  - "Final-state precedence: failed(nothing landed / stage failure) beats nothing; mismatch beats reconcile-failed; done requires >=1 landed AND zero mismatches AND zero failed reconciles (the plan's rule read strictly — a swallowed failed reconcile could never be 'done')"
  - "The bundle entry's reconcile payload is {per_key: {key: verdict}} — reconciled_rows() (the D-11 overlay source) deliberately contributes nothing for it: the bundle lane flips env-check's disk-scan kernel naturally, while selection presence follows the g re-audit (documented for 10-05)"
  - "Queue-lane tests monkeypatch registries.N_AUDIT_PATH at a tmp artifact (the module-path seam) — the committed n_audit.json is never rewritten by any test"
  - "The bundle zip fixture layout pins zip-root == datasets-root (group dirs at the archive root); a differently-prefixed real layout at activation lands zero keys -> explicit failed with landed=0 diagnostics, never silent corruption (the A4 verify-at-activation note)"

patterns-established:
  - "RecordingOpener/UrlRouter: urlopen-shaped fakes as classes (ty-clean attribute access) — the function-with-attributes idiom trips ty and the repo carries zero ty:ignore"
  - "The string-inventory tripwire: every consumer-referenced constant NAME asserted to exist in tui/strings.py — downstream plans fail HERE on drift, not in their own lanes"

requirements-completed: [DATA-04]

coverage:
  - id: D1
    description: "The D-12 four-state probe: one GET against the frozen URL, 404=not_public (live today), 200=public, everything else failed; HEAD never used; zero persistence"
    requirement: DATA-04
    verification:
      - kind: unit
        ref: "tests/tui/test_services_zenodo_bundle.py (Task 1 lane: 200/404/403/500/URLError/timeout/unexpected rows + seam-kwarg, no-URL-param, no-HEAD, zero-CJK pins)"
        status: pass
  - id: D2
    description: "The derive-never-hardcode bundle driver: dual-spelling parse, streamed download through the fetch seam, zip-slip-guarded extraction"
    requirement: DATA-04
    verification:
      - kind: unit
        ref: "tests/tui/test_services_zenodo_bundle.py (Task 2 driver lane: parse both spellings + zero-conforming, 64 KiB chunk pin, per-file failure collection, traversal-name refusal, extract land/skip/corrupt)"
        status: pass
  - id: D3
    description: "The zenodo-kind queue integration: CLI-free enqueue, claim parity, run_task dispatch with the full stage chain and the done/mismatch/failed rule"
    requirement: DATA-04
    verification:
      - kind: integration
        ref: "tests/tui/test_services_download_queue.py (zenodo queue lane: offline E2E done through the REAL extract + REAL reconcile subprocess over a tmp repo; not-public live-today; zero-files; mid-download no-presence-effect; zip-slip-through-queue; mismatch no-deletion; nothing-landed)"
        status: pass
  - id: D4
    description: "The I18N-01 single-home string block: every Copywriting Contract row verbatim under DL_/QUEUE_ with the W1 exact names, the SEL_ amendments, and the ENV_ROUTE [3] amendment"
    requirement: DATA-04
    verification:
      - kind: unit
        ref: "tests/tui/test_services_download_queue.py (47-name inventory tripwire, five-glyph pin, ENV_ROUTE segments, bundle-name/queue-key anchor) + tests/tui/test_pilot_env_check.py (constant-derived route line stays green, zero test edits)"
        status: pass
  - id: D5
    description: "Full-suite + lint + typecheck gates green with zero out-of-scope tree changes"
    requirement: DATA-04
    verification:
      - kind: integration
        ref: "make test (pytest 1094 = 1057 baseline + 37 new; node 18/18, exit 0); make lint; make typecheck; git diff 91bb4fb..HEAD over pipeline/ script/ dnallm-mark/ pyproject.toml uv.lock = EMPTY"
        status: pass

duration: 25min
completed: 2026-10-12
status: complete
---

# Phase 10 Plan 03: DATA-04 Zenodo Bundle + DL_/QUEUE_ Strings Summary

**One-liner:** The DATA-04 alternate whole-package entry — a four-state stdlib GET probe over the frozen record 19135551 (404 = not public, live today; activation is the answer flipping), a derive-never-hardcode bundle driver (dual-spelling record parse, streamed staging downloads, zip-slip-guarded extraction), the zenodo-kind queue branch chaining into the 10-02 per-key reconcile with the per-key verdict map, and the complete 47-constant DL_/QUEUE_ string block + ENV_ROUTE [3] amendment so 10-04/10-05 are pure consumers.

## What Was Built

### Task 1 — The Zenodo probe service (D-12, 4-state)

`tui/services/zenodo_bundle.py` with `ZENODO_RECORD_ID`/`ZENODO_API_URL` frozen constants and `probe_zenodo_public(timeout=15.0, opener=None)`: one stdlib GET — 200 -> `public`; HTTPError 404 -> `not_public` (the live-today not-registered state); any other HTTPError (403/500 pinned), URLError, timeout, or unexpected exception -> `failed`. Pure I/O, session-memory only, zero retries, zero persistence; HEAD never used (the records CDN hangs on it — research Pitfall 7); no URL or shape parameter exists, so no caller input can retarget the probe. 11 offline tests over a recording opener fake, including the timeout-contract row (a fake sleeping past a tiny injected budget then raising, with the kwarg pass-through asserted) and module hygiene (zero CJK, greppable frozen URL, no HEAD patterns).

### Task 2 — The bundle driver + zenodo-kind queue integration

Driver in `zenodo_bundle.py`: `fetch_record_json` (defensive GET+parse, `(None, diagnostic)` on every edge), `BundleFile` + `parse_record_files` (name from `key` OR `filename`, url from `links.self` OR `links.download`; non-conforming skipped; zero conforming -> empty tuple -> the caller's `record_file_list_unreadable` failure), `download_bundle_files` (64 KiB streamed copies through the fetch seam into the state-root staging dir, per-file failures collected, traversal staging names refused), `extract_bundle_archives` (every member resolved under `datasets_root.resolve()` with `is_relative_to` or skipped with a `zip_slip_skipped=` problem; non-zip ignored; corrupt archives reported; plain per-member copy so a member can never become a symlink).

Queue integration in `download_queue.py` (existing legs byte-untouched): `KIND_ZENODO_BUNDLE` + `ZENODO_BUNDLE_KEY = "zenodo-19135551"`, a `zenodo_fetch` constructor seam, CLI-free idempotent `enqueue_zenodo()` (the bundle lane is stdlib HTTP — no modelscope probe), and a kind dispatch at the `run_task` head routing to `_run_zenodo_bundle`: fresh probe (not public -> failed `record_not_public` with `probe=` in details — the live-today 404 state) -> defensive parse -> staging download (any per-file failure -> failed `bundle_download_failed` with verbatim diagnostics; no byte-resume by design) -> guarded extract into `pipeline/datasets` -> per-key landing check over the `missing_datasets()` set (the 10-01 checker per key) -> per-key `reconcile_dataset` (the 10-02 leg) for every landed key -> `entry.reconcile = {"per_key": {key: verdict}}`. Final state: done iff >=1 landed AND zero mismatches; mismatch if any landed key mismatched (problems carry `key:Train_mismatch_declared=N_measured=M` shapes); failed if nothing landed or any stage failed. The branch writes nothing outside staging + `pipeline/datasets`; the drill-down log carries the `[reconcile]` section. The offline E2E runs the REAL extraction and the REAL audit subprocess over a tmp repo to done.

### Task 3 — The DL_/QUEUE_ string block + ENV_ROUTE amendment (I18N-01)

47 constants in `tui/strings.py` (the single home), every 10-UI-SPEC Copywriting Contract row verbatim: DL_ screen chrome (title, missing-list title/columns/empty), the Zenodo four probe states + the never-silent disabled toast + `DL_BUNDLE_TASK_NAME`/`DL_ZENODO_KEY_LABEL`, the four keycap labels, the documented gap-fillers (`DL_PRESENCE_SUMMARY`, `DL_DISABLED_TOAST`); QUEUE_ title/columns/empty, the five glyph-first states (◌ ⠋ ✓ ✗ ⚠), reconcile cells, restart note, the 不自动删除 banner, all toasts (`QUEUE_TOAST_ENQUEUED`/`_ENQUEUED_ALL`/`_ALREADY_QUEUED`/`QUEUE_FLIP_TOAST`/`QUEUE_RETRY_NOOP`/`QUEUE_CLI_UNAVAILABLE`), `QUEUE_PROGRESS_INDETERMINATE`, both cancel confirms, `QUEUE_CANCEL_NOOP`, `QUEUE_REAUDIT_LABEL`; plus the SEL_ d-enqueue amendments. `ENV_ROUTE_MISSING_DATASETS` amended in place: `[3] 前往数据管理` replaces the retired Phase-10-panel note with the `{n}` field and CLI command preserved — the constant-derived env-check Pilot test stays green with zero edits. The names mirror exactly what 10-04/10-05 reference (the plan-checker W1 set), pinned by a 47-name inventory tripwire.

## Performance

- **Duration:** ~25 min (2026-10-12T15:07Z -> 15:34Z)
- **Tasks:** 3/3
- **Files:** 5 (2 created, 3 modified — all planned)

## Task Commits

Each task ran RED -> GREEN with separate commits:

1. **Task 1: Zenodo probe service** — `36c12a3` (test, 11 RED) / `39b1899` (feat)
2. **Task 2: Bundle driver + queue integration** — `92053bf` (test, 22 RED) / `23357ee` (feat)
3. **Task 3: DL_/QUEUE_ strings + ENV_ROUTE** — `303d58f` (test, 4 RED) / `8b9b063` (feat)

No REFACTOR commits needed (cleanup landed inside each GREEN).

## Verification Evidence

- `uv run --group dev --group tui pytest tests/tui/test_services_zenodo_bundle.py tests/tui/test_services_download_queue.py -q` — **140 passed** (22 probe/driver + 118 queue incl. the string lane).
- `uv run --group dev --group tui pytest tests/tui/test_import_lock.py tests/tui/test_services_about.py -q` — green (the auto-locks cover the new module: zero textual, zero services CJK).
- `uv run --group dev --group tui pytest tests/tui/test_pilot_env_check.py -q` — green (the amended ENV_ROUTE is consumption-compatible with zero env_check.py changes).
- `make test` — **exit 0**: pytest **1094 passed** (1057 wave-2 baseline + 37 new), node lane **18/18**.
- `make lint` — ruff **All checks passed**. `make typecheck` — ty **All checks passed** (zero ty:ignore in the repo, unchanged).
- Scope: `git diff 91bb4fb..HEAD -- pipeline/ script/ dnallm-mark/ pyproject.toml uv.lock` — **EMPTY** (no pipeline/ edits, no registry writes, no dependency changes; download_queue.py touched only per the integration spec).
- CI network-free: every Zenodo touch is a mocked opener/URL-router or a local zip fixture; no test lane reaches zenodo.org.

## Deviations from Plan

**1. [Task-boundary discipline, self-corrected] the first module draft carried Task 2's driver**
- **Found during:** Task 1 GREEN — the initial `zenodo_bundle.py` write included the whole Task 2 surface.
- **Resolution:** trimmed to the probe-only module for Task 1's atomic commit (imports included); the driver functions landed in Task 2's GREEN exactly as planned. No behavior impact.

**2. [Rule 1 - Bug] the corrupt-zip fixture was a valid EMPTY zip**
- **Found during:** Task 2 GREEN — `garbage + bare EOCD` parses as a legitimate zero-entry archive (extracts 0, problems 0): the corrupt-archive edge passed vacuously.
- **Fix:** a lying EOCD (nonzero entry count at a bogus central-directory offset) — `is_zipfile` says yes, `ZipFile` raises BadZipFile. `tests/tui/test_services_zenodo_bundle.py`, inside the Task 2 GREEN commit `23357ee`.

**3. [Lint/typecheck constraints, fixed in-lane] three tool findings on the first GREEN draft**
- ruff F811 (duplicate mid-file `io` import) — dropped, the earlier section import covers it; ruff SIM117 (nested `with`) — merged; ty (function-attribute access on the opener fake + `HTTPError` hdrs=None against the stub) — converted the fake to a `RecordingOpener` class and passed `email.message.Message()`. No ty:ignore introduced (repo baseline zero). All inside `23357ee`.

**4. [CJK lock catch, working as designed] a Chinese word in my own new docstring**
- The word 任务 in the new `enqueue_zenodo` docstring tripped the module CJK lock; replaced with "task". The lock's first catch on genuinely new code — no plan impact.

---

**Total deviations:** 4 documented (1 task-boundary self-correction, 1 Rule 1 fixture bug, 1 batched lint/ty adjustment, 1 lock catch)
**Impact on plan:** No scope creep — every change inside the five planned files; all gates green.

## Issues Encountered

`gsd_run` CLI unavailable in this environment (same as 10-02) — state/roadmap/requirements updates applied manually following the documented handler behaviors.

## Known Stubs

None. The not-public state is not a stub — it is the live truth (the record is unregistered); activation is the probe answer flipping with zero code change, per D-12's design.

## Activation-Time Verification Notes (A4, for the record)

- **Bundle zip layout:** the fixture pins zip-root == datasets-root (group dirs at the archive root, matching the registry `Dataset_path` convention). If the real record publishes a differently-prefixed layout, the run fails explicitly (`landed=0` + the not-landed key diagnostics in details) — diagnosable, never silent.
- **Record shape:** the parser accepts both documented spellings per field; a novel shape yields `record_file_list_unreadable` with the parsed count in details.
- **A restricted-published 403:** maps to probe-failed (disabled + explanation) — pinned; safe degradation.

## Threat Flags

None — no security-relevant surface beyond the plan's threat model. All five mitigations test-pinned: T-10-03-01 (resolve+is_relative_to guard + the traversal fixture through the queue branch AND the download-side staging-name refusal), T-10-03-02 (dual-spelling defensive parse + zero-conforming explicit failure), T-10-03-03 (timeout seam pin + per-file streamed bounded copies), T-10-03-04 (zero persisted probe state by construction), T-10-03-05 (extraction lands only under pipeline/datasets; the 10-02 reconcile gate applies per landed key before any done).

## Next Phase Readiness

- **10-04 (data-manager screen):** can assume `enqueue_zenodo()` + the queue surface exactly as landed (kind dispatch is internal — the screen only calls enqueue/kick and renders `entry.reconcile["per_key"]` for bundle rows), and every DL_/QUEUE_/ENV_ROUTE constant by the pinned names — the 47-name inventory is the contract. `DL_BUNDLE_TASK_NAME.startswith(ZENODO_BUNDLE_KEY)` is anchored by test.
- **10-05 (selection/env):** `SEL_ENQUEUE_LABEL`/`SEL_ENQUEUE_PRESENT_TOAST`/`DL_DISABLED_TOAST` exist verbatim; the amended `ENV_ROUTE_MISSING_DATASETS` renders through the existing constant-format call site with zero env_check.py changes (proven by the unmodified Pilot suite). The presence-overlay seam (`merge_presence(load_n_audit(), reconciled_rows())`) is untouched by this plan; bundle-landed keys flip the env disk-scan naturally, and selection presence follows the `g` re-audit.

## Self-Check: PASSED

All five touched files exist on disk; all six plan commits are ancestors of HEAD (`36c12a3`, `39b1899`, `92053bf`, `23357ee`, `303d58f`, `8b9b063`); `commits: 6` measured from the persisted ledger (`91bb4fb..8b9b063`).

---
*Phase: 10-data-manager-downloads-verification*
*Completed: 2026-10-12*
