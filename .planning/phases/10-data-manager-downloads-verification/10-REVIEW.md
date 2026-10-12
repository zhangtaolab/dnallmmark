---
phase: 10-data-manager-downloads-verification
reviewed: 2026-10-13T00:00:00Z
depth: deep
files_reviewed: 17
files_reviewed_list:
  - tui/services/download_queue.py
  - tui/services/zenodo_bundle.py
  - tui/screens/data_manager.py
  - tui/screens/selection.py
  - tui/app.py
  - tui/__main__.py
  - tui/screens/nav.py
  - tui/strings.py
  - tui/styles.tcss
  - tests/tui/test_services_download_queue.py
  - tests/tui/test_services_zenodo_bundle.py
  - tests/tui/test_pilot_data_manager.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/fixtures/modelscope_stderr_success.txt
  - tests/tui/fixtures/modelscope_stderr_interrupted.txt
findings:
  critical: 1
  warning: 6
  info: 8
  total: 15
status: issues_found
review_base: 71b05c4..HEAD
review_classes: CR/WR/IN
---

# Phase 10: Code Review Report

**Reviewed:** 2026-10-13
**Depth:** deep (per-file + cross-module trace: service -> app driver -> screens -> tests)
**Diff:** `git diff 71b05c4..HEAD -- . ':(exclude).planning'` (32 code commits)
**Files Reviewed:** 17
**Status:** issues_found

Intended behaviors per 10-CONTEXT (D-01..D-16, R-01..R-03) and the six
SUMMARYs were treated as design, not defects: mismatch never auto-deletes
(D-07); 4 shape-D keys disabled-with-explanation (R-02); no artificial
download timeout (T-10-06-01); artifact-based verdicts, never exit codes;
services zero-textual; boot resume only via `__main__`; Zenodo GET-only;
bundle lane no byte-resume.

## Summary

The phase is unusually well-disciplined: LIST argv everywhere with a
repo-id allowlist, owned `Popen` handles with `start_new_session` +
killpg cancel, zip-slip guards that survive absolute/traversal/symlink
members, an exhaustive 20-row transition table, per-worker `@work`
groups, generation-tagged messages, empty-overlay env isolation, and a
committed-artifact sha256 anti-clobber pin. The subprocess decode policy
is correct on the modelscope stderr pump (`errors="replace"`). All
claimed gates re-verified green at HEAD
(`tests/tui/test_services_download_queue.py` +
`test_services_zenodo_bundle.py`: 169 passed;
`test_pilot_data_manager.py` + `test_pilot_selection_custom.py`:
61 passed).

One release-blocking defect and six should-fix defects remain, all
verified against the code (CR-01, WR-04 also verified by executing the
real service against seeded state):

- The data-manager missing pane's D-11 flip is **fake drift**: the
  Pilot e2e proves the drop against a `FakeQueueService` whose
  `missing_datasets` filters done entries, while the real service
  derives the pane from the committed `n_audit.json` only — on a real
  host a reconciled dataset never leaves the missing list, the presence
  summary never moves, and the happy-zero state is unreachable without
  a maintainer `g`-reaudit commit.
- The Zenodo bundle lane cannot be cancelled at all (`cancel()` answers
  `"signalled"` and the branch ignores the flag).
- A narrow lost-wakeup race in the driver busy-guard can strand a
  pending entry with no driver running.
- Queue-event forwarding targets `self.screen` (the top of the stack),
  so any open modal swallows row refreshes and the selection flip.
- `enqueue`/`claim_next`/`_finish` propagate `OSError` from
  `atomic_write`, breaking the pinned "never raises" contracts
  (verified: `PermissionError` crosses `enqueue`).
- The reconcile/reaudit legs decode subprocess output with `text=True`
  and no `errors=` policy — the recurring non-UTF8-locale failure class
  converts a healthy audit into a spurious failed verdict.
- `enqueue` collapses every degraded reason into the `disabled`
  outcome, so a registry-read failure renders the factually wrong
  "mirror layout" toast.

## Critical Issues

### CR-01: The D-11 flip never reaches the data-manager missing pane — the e2e proof is fake drift over semantics the real service does not have

**File:** `tui/services/download_queue.py:2073-2108` (`missing_datasets`),
`tui/screens/data_manager.py:322-358` (`DataManagerBackend.missing_snapshot`),
`tests/tui/test_pilot_data_manager.py:159-165` (`FakeQueueService.missing_datasets`)
**Issue:** The real `missing_datasets()` derives rows exclusively from
`registries.load_n_audit()` (the committed `dnallm-mark/data/n_audit.json`)
via `presence_for` — it never consults the reconcile overlay
(`reconciled_rows`/`merge_presence`, the substrate 10-02 built for exactly
this flip). `DataManagerBackend.missing_snapshot` additionally computes
`present`/`total` from the same committed view. The Pilot "proof" that a
done entry drops from the missing list
(`test_driver_e2e_rows_toast_and_missing_refresh`,
`tests/tui/test_pilot_data_manager.py:1288-1290`) passes only because
`FakeQueueService.missing_datasets` implements `state != "done"`
filtering — semantics the real service does not share.
**Failure scenario (verified by executing the real service against a
seeded done+reconciled entry and a committed-view n_audit):** operator
downloads `GUE__emp_H3` on the GB10 host; the run lands, reconciles
pass, the row turns ✓ 完成, `QUEUE_FLIP_TOAST` fires ("在场已更新"), and
the selection screen flips the cell to present — but the data-manager
missing pane still lists the key with a ✗ glyph and
`DL_PRESENCE_SUMMARY` still counts it missing. Pressing `d` on it
answers 已在队列中 forever (a done entry is `already_queued`), `r` is a
no-op, so the stale ✗ row is unactionable and permanent until the
maintainer runs `g` and commits a new baseline. The screen contradicts
itself (done row + missing row for the same key), contradicts slot 2,
and the `✓ 无缺失数据集` happy zero is unreachable. The GB10 live-smoke
procedure (10-06 §step 4: "the key leaves the missing list") will fail
at exactly this step.
**Fix:** derive both surfaces from the merged view the selection screen
already uses — in `missing_datasets()` (or at minimum in
`DataManagerBackend.missing_snapshot`):
`tasks = merge_presence(registries.load_n_audit(), reconciled_rows(self._state_path))`
then compute rows/present over `tasks`. Keep the committed file
read-only (the merge is pure). Update `FakeQueueService` to delegate to
the same rule (or drive the e2e through `merge_presence`) so the Pilot
lane can no longer mask the gap.

## Warnings

### WR-01: The Zenodo bundle lane cannot be cancelled — `cancel()` reports "signalled" while the branch ignores it

**File:** `tui/services/download_queue.py:1295-1303` (`cancel`),
`1590-1713` (`_run_zenodo_bundle`)
**Issue:** `cancel()` on a `downloading` entry adds the key to
`_cancel_requested` and signals `self._active.get(key)` — but
`_run_zenodo_bundle` never registers `_active` (only the modelscope
lane does, line 1395) and never checks `_cancel_requested` at any stage
(probe / parse / download / extract / reconcile). `_finish` (line 2040)
then discards the flag.
**Failure scenario:** after the record publishes (activation is the
probe answer flipping, zero code change), the operator presses `x` on
the bundle row and confirms — the confirm copy promises
"已下载部分将由通道续传保留 — Enter 取消", `cancel()` returns
`"signalled"`, and the multi-GB HTTP download continues to completion.
With no artificial timeout by design (accepted T-10-06-01 names the
operator cancel as THE bounded escape), a trickling/hung bundle
transfer leaves the operator no escape short of quitting the TUI; the
per-read 15s socket timeout does not bound a slow-but-steady stream.
**Fix:** check `key in self._cancel_requested` at each stage boundary
in `_run_zenodo_bundle` (before parse, inside the per-file download
loop via a callback, before extract, before reconcile) and finish as
`failed` with `cancelled_by_operator`; mirror the reap-loop contract.

### WR-02: Driver lost-wakeup — a kick landing between the final `claim_next()` and the `finally` busy-clear strands a pending entry

**File:** `tui/app.py:368-382` (`kick_download_queue`),
`385-431` (`run_download_queue`, esp. 414 + 431)
**Issue:** the busy flag is the only restart guard. The worker's drain
sequence is `claim_next() → None` (line 414) … `finally:
_queue_busy = False` (line 431). Any enqueue+kick that lands inside
that window (including while the worker's `claim_next` holds the
service lock and the enqueue is serialized behind it) sees
`_queue_busy is still True`, returns, and no driver ever starts for the
newly appended pending entry.
**Failure scenario:** worker W finishes task N, `claim_next` scans the
entries (empty at that instant); the operator presses `d` on the
missing pane — `enqueue` appends+persists, `kick_download_queue` hits
the still-set busy flag and returns; W's `finally` clears the flag. The
queue now holds a pending row with no driver: the row shows ◌ 待下载
indefinitely, the download never starts. Recovery is only incidental
(a later enqueue/retry/boot resumes both).
**Fix:** in the worker `finally`, after clearing `_queue_busy`, re-check
`any(e.state == "pending" for e in self._download_queue.entries())` and
re-kick when non-empty (the flag now being False makes the re-kick
safe); alternatively perform check-and-set of the busy flag under a
`threading.Lock` shared with the finally.

### WR-03: Queue-event forwarding targets `self.screen` (the modal), so an open ConfirmModal/QueueDetailModal swallows row refreshes and the selection flip

**File:** `tui/app.py:447-477` (`on_queue_event_message` /
`on_queue_progress_message`, `getattr(self.screen, ...)` at 462, 471)
**Issue:** while any `ModalScreen` is pushed (the cancel confirms, the
drill-down, the selection screen's `ConfirmModal`/`PresetMenu`),
`self.screen` is the modal, which defines neither
`apply_queue_event` nor `apply_queue_progress` — the forward is a
silent no-op. Neither the data-manager nor the selection screen has a
self-healing reload: the rows stay stale after the modal closes.
**Failure scenario:** the operator opens the drill-down on a
downloading row; the task completes (done, reconcile pass); the flip
toast fires but `apply_queue_event` never runs; the operator dismisses
the modal and the row still reads ⠋ 下载中 with a frozen percent until
some unrelated action triggers `_reload_snapshot`. Worse on the
selection screen: a done event arriving while a confirm/preset modal is
open never re-runs `_load_data`, so the presence cell stays ✗ until the
next mount/filter/view action — the D-11 "live flip" is lost, not
delayed.
**Fix:** forward to every screen in the stack that defines the handler:
`for screen in self.screen_stack: apply = getattr(screen,
"apply_queue_event", None); if apply is not None: apply(event)` (same
for progress).

### WR-04: Persistence failures cross the "never raises" service boundary — verified `PermissionError` out of `enqueue`/`claim_next`; a failing `_finish` leaves the entry downloading and drops the event

**File:** `tui/services/download_queue.py:1106-1115` (`_persist_locked`),
`1138-1187` (`enqueue` — docstring: "never an exception"),
`1307-1328` (`claim_next`), `2014-2044` (`_finish`)
**Issue:** `_persist_locked` calls `settings.atomic_write` unguarded;
`OSError` (read-only state dir, full disk, quota) propagates out of
every mutator. Verified by execution: with the state dir read-only,
`enqueue(...)` raises `PermissionError` and `claim_next()` raises
`PermissionError` — both violate their pinned contracts, and the
screen actions call them directly on the event loop (unhandled
exception in an action handler).
**Failure scenario:** disk fills mid-download; the task's CLI exits;
`run_task` reaches `_finish` → `_persist_locked` raises inside the
driver worker — the QueueEvent is never posted (the row never
refreshes), the entry stays persisted as `downloading`, and the worker
dies with textual's generic worker error. On the next boot the entry
downgrades and re-runs (recoverable), but during the session the queue
appears wedged with no diagnostic surfaced.
**Fix:** absorb `OSError` in `_persist_locked` into a returned
diagnostic (or catch at the three mutator boundaries): `enqueue`
returns a failed outcome, `claim_next` returns None, `_finish` still
returns the event carrying a `persist_error=<repr>` problem so the row
and drill-down surface it.

### WR-05: Reconcile/reaudit legs decode subprocess output `text=True` with no `errors=` policy — the recurring non-UTF8-locale class turns a healthy audit into a spurious failed verdict

**File:** `tui/services/download_queue.py:1954` (`_invoke` runner call),
`1999-2012` (`reaudit_baseline` via the same `_invoke`)
**Issue:** `subprocess.run(..., capture_output=True, text=True)`
decodes with the locale encoding and strict errors. The audit script
emits CJK/emoji markers (e.g. `✅`), so on a host whose `LC_CTYPE` is a
non-UTF-8 codepage (the GBK class that was phase-8 CR-01 and phase-9
WR-02/WR-06), `communicate()` raises `UnicodeDecodeError` inside
`subprocess.run`; `_invoke`'s `except Exception` absorbs it as
`subprocess_error`.
**Failure scenario:** GBK-locale host, dataset lands, audit subprocess
runs to completion and writes a passing temp `n_audit.json` — the
decode of its stdout raises before the artifact is ever read;
`reconcile_dataset` returns verdict `failed` (`subprocess_error`), the
entry lands `failed` instead of `done`, presence never flips, and the
drill-down shows a launch diagnostic for a run that succeeded. Wrong
result, no crash, operator-misleading. (The modelscope stderr pump at
line 845 already uses `errors="replace"` — this is the one new leg
without the policy.)
**Fix:** pass `errors="replace"` alongside `text=True` in the
`_invoke` runner kwargs (the seam fakes record kwargs; add the kwarg to
the recorded-contract tests), matching `_pump`'s policy.

### WR-06: `enqueue` collapses every degraded reason into `disabled`, rendering the factually wrong "mirror layout" toast for registry failures

**File:** `tui/services/download_queue.py:1161-1171` (enqueue →
`action="disabled"` for ANY `reason_code`),
`tui/screens/data_manager.py:958-973` (`_toast_enqueue_outcome` →
`DL_DISABLED_TOAST` only), same mapping in
`tui/screens/selection.py:1673-1712`
**Issue:** `channel_state()` already distinguishes `disabled`
(shape-D / unknown-repo) from `unknown` (no mirror, malformed values,
`registry_unreadable`), but `enqueue` returns `action="disabled"` for
all six reason codes, and both screens render that action with
`DL_DISABLED_TOAST` = "⚠ {key} 上游为镜像布局，不支持一键下载 —
download_url 见详情" — copy that is true only for `shape_d_layout` /
`unknown_repo_shape`.
**Failure scenario:** `pipeline/datasets_info.json` read fails
transiently (NFS blip, permissions); the operator presses `d` on a
missing row; `resolve_channel` degrades with `registry_unreadable`;
the operator is told the dataset's upstream is a non-downloadable
mirror layout — a false statement that sends the diagnosis in exactly
the wrong direction (the drill-down would show
`channel: unknown (registry_unreadable)`, contradicting the toast).
Same false copy for `no_modelscope_mirror` and the malformed-value
reasons under registry drift.
**Fix:** return a distinct outcome (e.g. `action="unknown"` carrying
`reason_code`) for reason codes outside `_DISABLED_REASONS`, render it
with a neutral "channel unavailable: {reason}" toast; or gate
`DL_DISABLED_TOAST`'s copy on the reason code.

## Info

### IN-01: `interrupted` is never cleared — the restart note renders on done/failed rows forever

**File:** `tui/services/download_queue.py:1059-1060` (set on downgrade;
no clear in `claim_next` 1307-1328 / `retry` 1246-1267 / `_finish`
2014-2044), `tui/screens/data_manager.py:864-866`
**Issue:** once a restart downgrade sets `interrupted=true`, every
later state keeps it; the task cell appends "上次中断 — 通道将续传"
(dim) to downloading/done/failed/mismatch rows and the drill-down. A
completed download showing "last interrupted — the channel will
resume" is stale/misleading (verified: still `True` after
`retry`→pending→claim).
**Fix:** clear `interrupted` in `claim_next` (the resume it announces
has begun) or in `_finish` on the done transition.

### IN-02: `first_real_error_line` is dead code — the D-03 failure-summary deliverable was never wired

**File:** `tui/services/download_queue.py:377-398`
**Issue:** defined and unit-tested (tests at
`test_services_download_queue.py:1012-1024`) but no production caller;
the 10-01 SUMMARY lists it as part of the engine surface. The verbatim
log carries everything, so impact is nil, but the function and its
tests pin behavior nothing consumes.
**Fix:** either surface it as a `first_error=` detail token on failed
events (the intended drill-down summary) or drop it with its tests.

### IN-03: `run_task` drops `progress_cb` on the zenodo branch; the bundle flip toast formats the raw queue key

**File:** `tui/services/download_queue.py:1362-1363`,
`tui/app.py:455-458`, `tui/screens/data_manager.py:1047-1057`
**Issue:** the bundle dispatch passes no `progress_cb`, so a bundle row
renders the indeterminate `⠋ …` for the entire (potentially
hours-long) download — the claim tick is its only progress signal. And
the app's done toast formats `event.key` ("zenodo-19135551") while the
z-toast uses `DL_BUNDLE_TASK_NAME` ("zenodo-19135551（整包）"), so the
two toasts for the same task use different names.
**Fix:** post an occasional indeterminate/stage tick from the bundle
branch (e.g. per downloaded file), and format the flip toast with the
bundle label for `kind == zenodo_bundle`.

### IN-04: `d`/`r`/`x` act on their fixed table's cursor regardless of focus while `enter` routes by focus

**File:** `tui/screens/data_manager.py:975-983` (`d` always reads the
missing table), `1070-1080` (`enter` checks `self.focused`)
**Issue:** with the queue table focused, pressing `d` silently enqueues
whatever the (unfocused) missing list's cursor sits on — a surprising
action on a table the operator is not looking at; `enter` on the same
keypress routes correctly.
**Fix:** gate `d` on the missing table being focused (mirroring
`_open_detail_for_focused`), or document the fixed-target contract in
the binding comment.

### IN-05: `read_log` and `_write_log` resolve the log root through different seams

**File:** `tui/screens/data_manager.py:420-430` (`settings.state_dir() /
entry.log_path`) vs `tui/services/download_queue.py:2064-2069`
(`self._state_path.parent / LOG_DIR_NAME`)
**Issue:** correct today only because the default `state_path` lives
under `settings.state_dir()`; a service constructed with an explicit
`state_path` elsewhere writes logs the screen can never read (empty
drill-down, no error).
**Fix:** expose the log root from the service (e.g.
`log_path_abs(entry)`) or have `read_log` derive from the queue's own
state path.

### IN-06: Bundle extraction overwrites existing files under `pipeline/datasets` and has no member-size cap; staging accumulates

**File:** `tui/services/zenodo_bundle.py:289-294` (`open(target, "wb")`
truncates), `1651` (staging dir never cleaned)
**Issue:** the shape-C rename enforces "operator data is NEVER
overwritten" (`rename_target_exists`), but the bundle extractor
truncates any same-named existing file (e.g. per-key-downloaded CSVs)
without a check; archive members are copied with no size bound
(decompression-bomb defense-in-depth); the staging dir under the state
root grows across runs.
**Fix:** skip-and-report members whose target exists with a different
size (or accept-and-document the overwrite); optionally cap per-member
bytes; prune staging on run start.

### IN-07: A single malformed entry in an otherwise valid file is dropped silently

**File:** `tui/services/download_queue.py:1046-1047`
**Issue:** `_load_locked` keeps only `isinstance(raw, dict)` entries —
a hand-edited file with one non-dict entry loses that row with no
diagnostic, while the module contract claims "never silent loss" for
corrupt state (only whole-file corruption is quarantined).
**Fix:** count and report dropped entries through the
`last_load_diagnostic` session channel.

### IN-08: A bundle run with zero missing keys ends `failed bundle_landed_zero` even when everything is already present

**File:** `tui/services/download_queue.py:1675-1683`
**Issue:** `landed` is computed over the (committed-view) missing set;
on a machine where nothing is missing, a successful multi-GB bundle
download+extract lands zero keys and the entry reads ✗ 失败 with
`bundle_landed_zero` — a misleading terminal state (nothing was wrong).
**Fix:** treat `missing_keys == 0` at run start as an explicit
nothing-to-do outcome (done with a note, or refuse at enqueue with a
toast).

---

## Counts

| Class | Count |
|-------|-------|
| CR | 1 |
| WR | 6 |
| IN | 8 |
| **Total** | **15** |

_Generated: 2026-10-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_

## Re-review iteration 2 (HEAD 0b3e1c9)

**Fix diff audited:** `9aa0bdc..0b3e1c9` (16 commits: 12 fix, 1 style, 3 docs)
**Method:** every CR/WR failure scenario re-executed against HEAD; every new
regression lane re-run against the PRE-FIX commit in a throwaway worktree
(`9aa0bdc` + the fix-commit test files; 18 lanes confirmed RED there);
introduced-findings sweep of the fix diff itself (busy-lock ordering,
screen-stack iteration, rollback paths, drain-recheck, string tripwire).
Full gates re-verified at HEAD: `tests/tui` 623 passed, `make lint`,
`make typecheck` all green.

### Per-finding verdicts

| ID | Verdict | Basis |
|----|---------|-------|
| CR-01 | **CONFIRMED-FIXED** | Original scenario re-executed at HEAD: seeded done+reconciled entry + committed-view n_audit → `missing_datasets()` now returns `[]` (was `['GUE__emp_H3']`). The regression lanes are real-service lanes, not fakes: tier-1 over a seeded real service + monkeypatched `registries.N_AUDIT_PATH` (mismatch sibling stays), the explicit-`state_path` lane, and the REAL `DataManagerBackend` over the REAL service asserting rows AND `present/total` flip together. All three verified RED on `9aa0bdc` (assertion failures: `['Demo__task', 'DemoM__mm'] == ['DemoM__mm']`, `['GUE__emp_H3'] == []`). `FakeQueueService` no longer masks the gap — its summary lane delegates to the production `merge_presence` rule, and `missing_snapshot`'s `present` counts over the merged view (denominator stays the committed count). |
| WR-01 | **CONFIRMED-FIXED** (residual noted, IN-10) | Stage-boundary polls at every leg + the `should_cancel` seam inside `download_bundle_files` + `_finish_cancelled` (`cancelled_by_operator`, flag consumed by `_finish` so retry is never poisoned — regression asserts the retry claim). Both regressions (cancel-before-stages with `router.calls == []`; cancel fired from INSIDE the fetch seam mid-download) verified RED pre-fix. Residual: the seam is per-FILE — during a single-file transfer (a one-archive bundle) the cancel takes effect only after the current file completes (IN-10). |
| WR-02 | **CONFIRMED-FIXED** | The deterministic `on_drain` hook reproduces the exact window and was RED pre-fix (entry stranded, `run_task_calls == ["k-one"]`). Lock audit: `kick`'s check-and-set and the worker's release-and-recheck are atomic under `_queue_busy_lock`; `run_download_queue()` is started OUTSIDE the lock; the only nested acquisition is busy-lock → service-lock (drain recheck's `entries()`), with no inverse path — no deadlock. No busy-strand path: the `finally` clear is generation-guarded and a generation bump requires a successful check-and-set (busy already False). No double-claim: the re-drive continues the SAME single worker, no second driver can start. **But the recheck pattern combined with WR-04 introduces CR-02 below.** |
| WR-03 | **CONFIRMED-FIXED** | Forward iterates `screen_stack` to every screen defining the handler; both modal lanes (drill-down over the queue row; selection preset modal with the live flip) verified RED pre-fix. No double-apply: at most one non-modal screen exists in a textual stack (`switch_screen` replaces); modals define no queue handlers; each screen's apply is persisted-state-as-truth and idempotent regardless. |
| WR-04 | **CONFIRMED-FIXED at the boundary* | Original scenario re-executed at HEAD: read-only state root → `enqueue` returns `persist_failed` with the in-memory append rolled back (no ghost row), `claim_next` returns None with the claim reverted to its exact prior shape (incl. `interrupted`), `_finish` still emits the event carrying `persist_error=<repr>` on both the event and the entry (worker survives, row surfaces it). All three mutator regressions verified RED pre-fix (the review's own `PermissionError`). *The absorbed claim-failure interacts with the WR-02 recheck → INTRODUCED CR-02. |
| WR-05 | **CONFIRMED-FIXED** | `errors="replace"` rides the ONE shared seam (`_invoke`) serving both legs; both kwargs-pin regressions (reconcile + reaudit) verified RED pre-fix; the behavioral proof decodes real undecodable stdout bytes through `_default_runner` to replacement chars. Sibling sweep confirmed no other `text=True` leg in the phase diff. |
| WR-06 | **CONFIRMED-FIXED** | `ACTION_UNKNOWN` carries its own reason for every non-`_DISABLED_REASONS` degradation; both screens render the neutral `DL_UNKNOWN_TOAST` naming the machine reason; the shape-D `disabled` keeps the mirror-layout copy. Tier-1 (no-mirror + bare-registry) and both screens' toast pins verified RED pre-fix (the bare-registry case previously collapsed to `disabled`). |
| IN-01 | **CONFIRMED-FIXED** | `interrupted` clears at claim (the resume begins), restored on the WR-04 revert; regression RED pre-fix. The recovered PENDING row still carries the note (the 10-06 visible-recovery contract) — intended. |
| IN-02 | kept open — **ACCEPTED** | Both dispositions are genuine trade-offs (new unrendered vocabulary vs deleting a SUMMARY-pinned surface); a tested pure function has no runtime risk. Reopen at the next engine touch. |
| IN-03 | toast half **CONFIRMED-FIXED** (RED-verified: bundle done formats `DL_BUNDLE_TASK_NAME`, raw key never appears); progress half kept open — **ACCEPTED** (percent `None` renders the same indeterminate glyph the claim tick already shows; a per-file callback widens the seam with no visible cell change). |
| IN-04 | fixed-as-documentation — **ACCEPTED** (the review's own zero-risk option; focus-gating `d` would create its own silent-noop class). |
| IN-05 | **CONFIRMED-FIXED** | `state_root()` seam + `read_log` through it (getattr fallback keeps the fakes' surface); regression over a real service with a state_path OUTSIDE the env state root verified RED pre-fix (empty drill-down). |
| IN-06 | kept open — **ACCEPTED with a condition** | The rationale holds (policy calls; lane inert while the record 404s; zip-slip already guarded; post-landing reconcile re-verifies content), and nothing CR/WR hides behind it — but the disposition's own "maintainer rules before the record goes public" must be tracked as an activation gate, not left implicit. |
| IN-07 | **CONFIRMED-FIXED** (residual noted, IN-11) | Non-dict rows counted + reported through the `last_load_diagnostic` session channel; cleaned entries persist so the drop fires once; healthy siblings survive; regression RED pre-fix. The early return skips the downgrade pass — see INTRODUCED IN-11. |
| IN-08 | **CONFIRMED-FIXED** | Empty missing set → done with `nothing_to_do` detail and an empty per-key map BEFORE any stage (zero network legs, nothing extracted); regression RED pre-fix. |

### Introduced findings (iteration-2 sweep of the fix diff)

### CR-02: WR-02's drain recheck × WR-04's claim-refusal = an unbounded driver livelock under a persistent persist failure

**File:** `tui/app.py:426-452` (the drain-side release-and-recheck),
`tui/services/download_queue.py:1400-1431` (`claim_next` returns None on
persist failure with the entry still pending)
**Issue:** when `claim_next` answers None because the claim could NOT
PERSIST (read-only state root, full disk) while the entry is still pending
in memory, the drain recheck's `any(state == "pending")` is true forever →
`continue` → claim → persist fails → revert → None → recheck → … The loop
has no sleep, no attempt cap, and no exit for this case; the busy flag
never clears, so every later kick is a no-op and the worker never exits.
**Failure scenario (verified by execution at HEAD 0b3e1c9: a real
`DownloadQueueService` over a read-only state root seeded with two pending
entries, driven by the real app driver):** 47,546 `claim_next` calls in one
second, `_queue_busy` stays True, `run_download_queue` still running, one
core pegged at 100%, the write path hammered continuously. Realistic
trigger: the disk fills mid-session while a second entry is queued (task 1
finishes with an absorbed `persist_error`, the driver claims task 2, and
spins); with the condition persistent, a restart boots straight back into
the spin (boot resume loads pending → kicks). The UI stays alive but the
queue is permanently wedged with CPU burn — a hang-class regression in the
exact degradation class WR-04 targeted (pre-fix, the same scenario raised
once and the worker died quietly).
**Fix:** distinguish "None because drained" from "None because the claim
was refused" — e.g. `claim_next` records the refusal diagnostic
(`last_claim_refusal()`), and the drain recheck exits the worker
(generation-guarded busy clear, matching the WR-04 toast vocabulary for
the surfaced failure) instead of `continue` when the last None was a
refusal; alternatively bound the re-drive (backoff sleep + attempt cap).

### IN-09: The two new toast constants are not registered in the string-inventory tripwire

**File:** `tests/tui/test_services_download_queue.py:3134-3163`
(`EXPECTED_DL_CONSTANTS` / `EXPECTED_QUEUE_CONSTANTS`)
**Issue:** `DL_UNKNOWN_TOAST` and `QUEUE_PERSIST_FAILED_TOAST` landed in
`tui/strings.py` and are imported directly by consumers (an ImportError
would still catch absence), but the inventory tripwire — whose stated
purpose is the complete DL_/QUEUE_ single-home lock — does not list them,
so the tripwire no longer covers the full inventory.
**Fix:** add both names to the expected tuples.

### IN-10: WR-01 residual — a cancel during a single-file bundle transfer only takes effect after that file completes

**File:** `tui/services/zenodo_bundle.py:238-240` (the `should_cancel`
check sits before each FILE, not inside the chunk loop)
**Issue:** a one-archive record (the likely publication shape) transfers
as one large file; the operator's cancel is observed at the next
stage boundary — after the whole file streams.
**Fix (when the lane activates):** check `should_cancel` every N chunks
inside the copy loop (e.g. per 64 KiB block or per second) and break.

### IN-11: IN-07's dropped-entries early return skips the downloading→pending downgrade pass

**File:** `tui/services/download_queue.py:1067-1086`
**Issue:** when a file carries BOTH a non-dict row and a
`downloading`-state entry, the dropped-rows branch returns before the
D-06 downgrade loop — on that load the entry stays `downloading` in
memory, so `boot_resume_queue` sees no pending entry and never kicks.
**Failure scenario:** hand-edited/partially corrupted file with both
shapes: boot skips the auto-resume; the entry sits unclaimed until the
next `load()` (the screen snapshot) downgrades it and some user action
kicks. Recoverable, silent, narrow.
**Fix:** run the downgrade pass before the dropped-rows early return (or
fall through instead of returning).

### The gauntlet.py sibling (coordinator question 4)

**Verified: YES — the same class.** `tui/services/gauntlet.py:550`
(`_invoke`: `self._runner(argv, capture_output=True, text=True,
timeout=..., env=...)`, no `errors=` policy) launches the same
CJK/emoji-emitting scripts; on a non-UTF-8 `LC_CTYPE` host,
`subprocess.run` raises `UnicodeDecodeError` inside `communicate()`,
absorbed by `except Exception` as `("subprocess_error", repr(exc))` — a
FAILED gauntlet item for a kernel that ran fine. Identical to WR-05 in
mechanism and consequence; had `gauntlet.py` been in this phase's diff it
would have been a WR.
**Recommendation: fix now** — one line (`errors="replace"` in the same
runner call) plus one kwargs-pin assertion in
`tests/tui/test_services_gauntlet.py`. It is surgical (zero widening),
the fixer already touched the deliberately-twinned seam in
`download_queue._invoke` this iteration, and shipping with the two
documented twins inconsistent re-opens the exact recurring decode class
this review cycle exists to close. If the maintainer prefers strict scope
purity, it must be the first commit of the next iteration — before
release.

### Iteration-2 counts

| Class | Count | Detail |
|-------|-------|--------|
| CR (introduced) | 1 | CR-02 livelock |
| WR (introduced) | 0 | — |
| IN (introduced/residual) | 3 | IN-09, IN-10, IN-11 |
| Original findings fixed | 12 of 15 | CR-01, WR-01..06, IN-01, IN-05, IN-07, IN-08 (+ IN-03 toast half) |
| Original findings accepted-as-kept-open | 3 | IN-02, IN-06 (with the pre-activation ruling condition), IN-03 progress half; IN-04 accepted as documentation |

**Release verdict: NOT clean** — CR-02 (the driver livelock) must be
fixed before ship; IN-09/IN-11 are one-line fixes recommended in the same
commit; IN-10 tracks activation.

_Re-review: 2026-10-13, Claude (gsd-code-reviewer), HEAD 0b3e1c9_

## Re-review iteration 3 (HEAD ed34b87)

**Fix diff audited:** `4079860..ed34b87` (0b31267 CR-02 / b01e523 IN-09 /
63f18e6 IN-11 / 46ddd37 gauntlet twin / c781a8a style / ed34b87 disposition)
**Method:** the CR-02 livelock scenario re-executed independently at HEAD
(read-only root + two pending entries + real service + real driver), with
boot-resume and rail-recovery variants; all four new regression lanes
re-run against the pre-fix commit `4079860` in a throwaway worktree (RED
verified); the whole fix diff re-audited as a fresh surface; full gates at
HEAD: `tests/tui` 627 passed, `make lint`, `make typecheck` all green.

### Per-item verdicts

**CR-02 — CONFIRMED-FIXED.** Independent re-execution at HEAD: kick over
the read-only rail → the driver EXITS after a bounded attempt count, busy
flag released, no `run_download_queue` worker remains, and the new
`QUEUE_PERSIST_DRIVER_TOAST` fires naming the refused key. Boot-resume
over the still-broken rail: one bounded attempt, exit, no spin. Rail
recovery + kick: claims succeed (both entries run to terminal states),
driver exits, busy False, `last_claim_refusal()` reads None after the
healthy claims. The regression lane is RED on `4079860` via the real
livelock (`wait_for_complete` timeout). Exit-path edge audit:
(a) **false refusal** — impossible by construction: only `claim_next`
writes the flag (service-locked), it is cleared at the START of every
attempt, and the single-driver guarantee (busy check-and-set) means no
other claim can interleave between the worker's None-return and its read;
a refusal therefore always describes THIS worker's just-failed claim over
a memory-pending-but-not-persistable entry (the queue is wedged by
definition — exit + toast is the honest state). (b) **refusal vs exit
race** — busy is released under the shared lock BEFORE the return; a kick
landing after the release succeeds at check-and-set and starts the next
generation (over a still-broken rail: exactly one more bounded attempt
and exit — proven by the re-kick execution, not just the test). The
stalled message is generation-dropped when a successor exists, so a
recovered rail suppresses the stale stall-toast correctly. (c) **boot
resume** — spin-free (execution-verified). Fakes without the
`last_claim_refusal` seam keep drained-only semantics via the getattr
guard.

**IN-09 — CONFIRMED-FIXED.** All three toast constants
(`DL_UNKNOWN_TOAST`, `QUEUE_PERSIST_FAILED_TOAST`, and the new
`QUEUE_PERSIST_DRIVER_TOAST`) are registered in the EXPECTED_ tuples, and
the new reverse sweep makes the lock bidirectional (defined set ==
registered set). The pre-fix RED replicated exactly: the reverse sweep at
`4079860` semantics reports `unregistered: ['DL_UNKNOWN_TOAST',
'QUEUE_PERSIST_FAILED_TOAST']` (the third name did not exist yet).
Over-constraining check: a legitimate future constant fails with a
two-direction message naming exactly what to register — that is the
tripwire's documented contract working, one tuple line to satisfy; scope
stays DL_/QUEUE_-prefixed constants in the constants-only module. Not
over-constraining.

**IN-11 — CONFIRMED-FIXED.** The D-06 downgrade pass now runs before the
dropped-rows early return, with one persist covering drop + downgrade.
Regression (compound file: non-dict row + downloading survivor) is RED on
`4079860` (survivor stayed downloading); at HEAD the survivor downgrades
to pending + interrupted, persists, and the diagnostic still rides the
session channel — boot resume sees pending and kicks.

**Gauntlet twin — CONFIRMED-FIXED.** `gauntlet.py:_invoke` now passes
`errors="replace"` alongside `text=True` — kwargs-identical to the
`download_queue._invoke` twin. The RED claim is credible and verified:
the kwargs pin fails on `4079860` with `KeyError: 'errors'` (the runner
call carried no errors kwarg). Committed separately as phase-9 follow-up,
keeping the phase-10 diff pure — the recurring decode class is now closed
repo-wide.

**Iteration-3 introduced-findings sweep — none.** The CR-02 exit path
reuses the audited busy-lock discipline (release under the lock, start
outside it, generation-guarded finally — no new ordering); the
`last_claim_refusal` read sits before the lock block but is stable
(single-writer, same thread); `QueueStalledMessage` is generation-tagged
and its toast is app-level (renders above modals); the bidirectional
tripwire's failure mode is a precise assertion, not a confusing error;
the CR-02 lane's monkeypatch claim seam wraps the instance attribute the
driver actually calls (no interposition gap); the style commit touches
test formatting only.

**Kept-open set — fully dispositioned, no hidden CR/WR.**
- IN-02 (`first_real_error_line` dead code): maintainer choice, tested
  pure function, no runtime risk. Accepted (iteration 2).
- IN-06 (bundle overwrite / member-size cap / staging prune): policy
  calls, lane inert while record 19135551 404s; zip-slip guarded;
  post-landing reconcile re-verifies content. Bound to the explicit
  PRE-ACTIVATION GATE: the maintainer must rule overwrite/cap/staging
  before the record publishes.
- IN-10 (per-file cancel seam): same activation gate as IN-06 — the
  per-chunk cancel check lands with the lane's activation work.
- IN-03 progress half: accepted (indeterminate glyph renders regardless;
  seam widening has no visible effect).

### FINAL RELEASE VERDICT: **CLEAN**

All 8 CR/WR-class findings from iterations 1-2 are fixed and
fix-verified (each against its original failure scenario, each with a
RED-on-pre-fix regression lane). Zero CR/WR/IN findings introduced by
this iteration. The four kept-open items are IN-class, explicitly
dispositioned, and either inert pending the documented Zenodo
activation gate (IN-06, IN-10) or maintainer polish choices (IN-02,
IN-03 progress half). The GB10 live smoke (10-06 §procedure) remains the
maintainer's manual confirmation step, now with the missing-pane flip
actually true of the real stack.

_Cumulative ledger: iteration 1 — CR 1 / WR 6 / IN 8; iteration 2 —
CR 1 / WR 0 / IN 3 introduced (all fixed this iteration); iteration 3 —
0 introduced; open: IN-02, IN-03(progress), IN-06*, IN-10* (* =
pre-activation gate)._

_Re-review: 2026-10-13, Claude (gsd-code-reviewer), HEAD ed34b87_
