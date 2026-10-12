# Phase 10: Code Review Disposition

**Source review:** `10-REVIEW.md` (2026-10-13, depth deep, 15 findings)
**Fix iteration:** 1
**Fix branch:** `gsd-reviewfix/10-*` over `autorun` @ `9aa0bdc` (review base `71b05c4..HEAD`)
**Scope rule:** D-01..D-16 / R-01..R-03 rulings and the six SUMMARYs are design, not defects — nothing was "fixed" out of them.

## Per-finding disposition

| ID | Disposition | Commit |
|----|-------------|--------|
| CR-01 | **fixed** | `356b324` |
| WR-01 | **fixed** | `1d87cc8` |
| WR-02 | **fixed** | `5ac49ea` |
| WR-03 | **fixed** | `a978300` |
| WR-04 | **fixed** | `4d8ced9` |
| WR-05 | **fixed** | `81014aa` |
| WR-06 | **fixed** | `bdbb985` |
| IN-01 | **fixed** | `a5c3bea` |
| IN-02 | kept open (rationale below) | — |
| IN-03 | **fixed (toast half)**; progress-tick half kept open | `5769e2c` |
| IN-04 | **fixed as documentation** (behavior deliberately unchanged) | `3078539` |
| IN-05 | **fixed** | `b9975ab` |
| IN-06 | kept open (rationale below) | — |
| IN-07 | **fixed** | `6f655a1` |
| IN-08 | **fixed** | `8837119` |

## Fixed — what changed

### CR-01 — the D-11 flip reaches the missing pane (`356b324`)

`missing_datasets()` now derives rows from
`merge_presence(registries.load_n_audit(), reconciled_rows(self._state_path))`
— a reconcile-pass key leaves the missing list the moment its queue entry
turns done; mismatched keys never flip (semantic 6). A new
`merged_audit_tasks()` serves the same merged view through the service's
OWN state path, and `DataManagerBackend.missing_snapshot` computes
`present`/`total` over it, so `DL_PRESENCE_SUMMARY` moves with the rows
(rows drop + present counts + total stays the committed denominator —
all three surfaces consistent). The committed `n_audit.json` stays
read-only (the merge is pure; only `g` refreshes the baseline).

**Test discipline (the release-blocking requirement):** the Pilot
`FakeQueueService.missing_datasets` never again masks the gap — it now
delegates its summary lane to the REAL `merge_presence` rule over its
done entries, and the regression lanes pin the REAL service semantics:
(a) tier-1 over a seeded real service + tmp committed n_audit (done+
reconciled key leaves rows; mismatched sibling stays), (b) the same
merged view through an explicit `state_path`, and (c) the REAL
`DataManagerBackend` over the REAL service with seeded done+reconciled
state asserting rows AND `present/total` flip together. Each lane was
RED on the pre-fix code.

### WR-01 — the zenodo bundle lane honors operator cancel (`1d87cc8`)

`_run_zenodo_bundle` polls the cancel-requested flag at every stage
boundary (pre-probe, pre-parse, pre-download, post-download, and
pre-reconcile) and finishes failed `cancelled_by_operator` through a
`_finish_cancelled` helper — the reap-loop contract mirrored for the
handle-less stdlib-HTTP lane. `download_bundle_files` gained a
`should_cancel` seam checked before each file (partial staging retained,
never a per-file failure). `cancel()`'s docstring documents the bundle
path. Regression: cancel-before-stages (probe never fires) and cancel
mid-download driven through the PUBLIC `cancel` API fired from inside
the fetch seam (both RED before).

### WR-02 — drain-side release-and-recheck (`5ac49ea`)

The review's lock alternative, implemented: `kick`'s check-and-set and
the worker's drain-side release-and-recheck run atomically under a new
shared busy lock. An entry enqueued inside the lost window is absorbed
by the SAME worker (no restart, no generation bump — D-04 serial stays
guaranteed); an entry enqueued after the release gets a driver from the
racing kick itself. The `finally` clear is generation-guarded so a
superseded worker can never release a successor's flag. Implementation
note (the phase-9 lesson applied): the first attempt re-kicked
synchronously from the `finally` and textual cancelled the successor
worker (`WorkerCancelled` out of `wait_for_complete`) — starting a
worker from a finishing worker's thread is not a supported pattern, and
the lock design avoids it entirely. Regression: the deterministic
`on_drain` fake hook reproduces the exact race window (RED: the entry
stranded, `run_task_calls == ["k-one"]`).

### WR-03 — forward queue events past open modals (`a978300`)

`on_queue_event_message` / `on_queue_progress_message` iterate the whole
`screen_stack` and forward to every screen defining the handler.
Regression lanes cover all three modal shapes the review named:
`QueueDetailModal` (the row visibly flips under the drill-down),
the x-cancel `ConfirmModal`, and the selection screen's preset modal
(the D-11 live flip reaches `apply_queue_event` under it). Each RED on
the old top-of-stack-only forward.

### WR-04 — persistence failures absorbed at the never-raises boundary (`4d8ced9`)

`_persist_locked` returns an OSError diagnostic instead of raising.
`enqueue` refuses with the new `persist_failed` action and rolls its
in-memory append back (no ghost row); `claim_next` reverts the claim
(state/attempts/started_at — and now `interrupted`, restored with the
IN-01 field) and answers None; `_finish` still emits the event carrying
a `persist_error=<repr>` problem on both the event and the entry so the
row and drill-down surface it — the worker never dies and the entry is
never left persisted-downloading by a failed `_finish`. `retry`,
`cancel`, and `enqueue_zenodo` stop raising by construction (their
persists route through the same absorbed rail). Both toast consumers
render a new `QUEUE_PERSIST_FAILED_TOAST`. Regression: read-only state
dir over all three mutators — each RED with the review's verified
`PermissionError` before the fix.

### WR-05 — `errors="replace"` on the reconcile/reaudit runner legs (`81014aa`)

`_invoke` passes `errors="replace"` alongside `text=True` (matching
`_pump`'s policy) — one seam serves BOTH subprocess legs
(`reconcile_dataset` and `reaudit_baseline`), so a non-UTF-8-locale
decode of the audit script's CJK/emoji output becomes replacement
characters instead of a `UnicodeDecodeError` absorbed as
`subprocess_error` (a healthy audit flipping to a spurious failed
verdict). The recorded-contract tests pin the kwarg on both legs; a
behavioral proof decodes real undecodable stdout bytes through
`_default_runner`.

**Sibling audit (phase-9 lesson):** every decode/encode path in the
phase diff was grepped — `_pump` and `fetch_record_json` already carried
`errors="replace"`; `read_log` reads a service-written UTF-8 file
(symmetric with its writer, OSError-guarded — not the subprocess-decode
class). **Out of diff, observed:** `tui/services/gauntlet.py`'s runner
(Phase 9 code, unchanged in this phase's review base) carries the same
latent missing `errors=`. Per the surgical-fix constraint it was NOT
widened here; recommend a one-line follow-up + kwargs-pin in the
gauntlet suite.

### WR-06 — `unknown` degraded reasons get their own outcome (`bdbb985`)

`enqueue` returns `action="unknown"` (new `ACTION_UNKNOWN`) carrying its
own `reason_code` for every reason outside `_DISABLED_REASONS`
(`no_modelscope_mirror`, `malformed_repo_id`, `malformed_dataset_path`,
`registry_unreadable`); shape-D/unknown-repo keep the R-02 `disabled`
outcome and its `DL_DISABLED_TOAST`. Both screens render a new neutral
`DL_UNKNOWN_TOAST` naming the machine reason — a transient registry-read
failure can no longer claim the dataset's upstream is a mirror layout.
Regression: tier-1 over the synthetic no-mirror entry and a
bare-registry repo (RED: both collapsed to `disabled`), plus both
screens' toast pins.

### IN-01 — `interrupted` clears at claim (`a5c3bea`)

`claim_next` clears the flag: the claim IS the resume the note
announces, so downloading/done/failed/mismatch rows no longer render
"上次中断 — 通道将续传" forever. The WR-04 revert restores the prior
flag with the other reverted fields. (The restart note still renders on
the recovered PENDING row — the 10-06 visible-recovery contract, pinned
by the existing pilot test, untouched.)

### IN-03 — flip toast uses the bundle label (`5769e2c`, toast half)

A done `zenodo_bundle` event formats `QUEUE_FLIP_TOAST` with
`DL_BUNDLE_TASK_NAME` — the z-enqueue toast and the done-flip toast for
the same task now use one operator-facing name. **Kept open (progress
tick):** posting per-file indeterminate ticks would need a per-file
callback seam through `download_bundle_files` AND changes to the
driver's progress throttle for no visible cell change (percent `None`
renders the same indeterminate glyph the claim tick already shows); the
row's state cell already refreshes through the claim tick and stage
transitions. Marginal value, widening seam — reopen if operators ask.

### IN-04 — fixed-target contract documented (`3078539`)

The review offered "gate on focus OR document the contract". Documented
(the review's zero-risk option): `d`/`r`/`x` act on their own table's
cursor by design (the D-15 verb-table pairing); only `enter` routes by
focus. Gating `d` on focus was deliberately not taken — it would turn
the binding into a silent no-op whenever the queue table is focused,
which is its own surprise class.

### IN-05 — `read_log` through the queue's own state root (`b9975ab`)

The service exposes `state_root()` (the parent of its state file — the
seam `_write_log` writes through) and the Backend's `read_log` resolves
`entry.log_path` against it, with a `getattr` fallback to
`settings.state_dir()` so the screen-protocol fakes keep their small
structural surface. A service constructed with an explicit `state_path`
outside the env state dir now reads back the log it wrote. (The seam
mismatch class is now consistent end-to-end: state file, logs, and the
merged presence view all resolve through the service's own path.)

### IN-07 — dropped malformed entries reported (`6f655a1`)

`_load_locked` counts non-dict rows, reports them through the
`last_load_diagnostic` session channel (the status line surfaces it),
and persists the cleaned entries (the D-06 downgrade-persists
precedent) so the drop fires exactly once — the never-silent-loss
contract now covers per-row corruption, not just whole-file corruption.

### IN-08 — empty missing set is the nothing-to-do outcome (`8837119`)

A bundle run whose missing set is empty at start finishes **done** with
a `nothing_to_do` detail and an empty per-key map (which contributes
nothing to the presence overlay) BEFORE any stage runs — zero network
legs — instead of a full download landing zero keys and reading
`✗ 失败 bundle_landed_zero` on a machine where nothing was wrong.

## Kept open — rationale

### IN-02 — `first_real_error_line` dead code

Kept as-is. The two dispositions the review offers are both design
choices with real trade-offs: wiring it onto failed events invents a
new `details` token vocabulary nothing renders yet (the drill-down
already shows the full verbatim log, which the review agrees "carries
everything"), and dropping it with its tests removes a documented
D-03 surface the 10-01 SUMMARY pinned. Minimal-diff discipline says
the maintainer picks; the cost of keeping it is one tested pure
function. Reopen at the next touch of the engine surface.

### IN-06 — bundle extraction overwrite / member-size cap / staging accumulation

Kept open — all three legs are maintainer policy calls, not surgical
fixes:

- **Overwrite:** the extractor truncating same-named files is
  defensible (the bundle is the authoritative source of record; a
  per-key download that raced a bundle extraction is the anomaly) but
  "skip-and-report" changes activation semantics the day the record
  publishes. This wants the maintainer's ruling, ideally before the
  record goes public (the D-12 activation moment).
- **Decompression-bomb cap:** defense-in-depth on a FROZEN, trusted
  record URL (the module's own constant, T-10-03 anti-hardcoding
  notwithstanding); a cap number is a policy choice with a false-
  positive cost on legitimately large splits.
- **Staging prune:** re-downloads already overwrite same-named staging
  files (open `"wb"`), so accumulation is limited to files the record
  later removes; pruning on start is easy but interacts with the
  no-byte-resume design's expectations and is worth doing together
  with the overwrite ruling.

No operator-facing defect exists TODAY on the live 404 record (the
lane refuses before any extraction); the findings become live only at
activation.

## Phase-9 self-audit (mandatory per the fix brief)

- **Sibling instances, same class:** every decode/encode path in the
  phase diff audited (WR-05 above). No other `text=True` subprocess leg
  exists in the diff; the one out-of-diff sibling (gauntlet) is
  documented, not widened.
- **Adjacent contracts:**
  - *Worker groups:* untouched — `dl-snapshot`/`dl-probe`/`dl-reaudit`
    exclusivity and the driver's `run_download_queue` group unchanged;
    the WR-02 fix deliberately adds NO second worker (the textual
    exclusive-cancel hazard found during implementation is designed
    around).
  - *Run-id drops:* the generation discipline is preserved — WR-02's
    re-drive absorbs the racing entry inside the SAME generation (no
    bump), and the busy-guard + boot-resume generation pins re-ran
    green.
  - *Frozen service surface:* the app-level fakes gained only additive
    members (`merged_audit_tasks`, `resolve_channel`, the `on_drain`
    hook); `QueueDriverProtocol` unchanged; the exhaustive
    state-machine transition table, the restart-rehydration chain, and
    the committed-artifact byte-unchanged pins all re-ran green.
  - *Lock ordering:* the new busy lock is always acquired BEFORE the
    service lock (drain recheck) with no inverse path — no deadlock
    cycle; the drain-recheck `entries()` read is exception-guarded so
    the worker exit can never raise.
- **Module suites re-run** after every fix commit (each finding's
  affected modules), then the full gates below.

## Gates

All green, run from the review-fix worktree:

- `make test` — exit 0 (full pytest lane + the node:test JS suite, 18
  JS tests pass)
- `uv run --group dev --group tui pytest -q` — **1193 passed** (the
  1171 baseline + the 22 regression lanes above; zero failures, zero
  skips)
- `make lint` — all checks passed (one `ruff --fix` pass re-sorted the
  import blocks the new toast constants landed in — committed as
  `style(10): import order after the review-fix toast constants`)
- `make typecheck` (`ty`) — all checks passed

---

_Disposition written by the gsd-code-fixer iteration 1, 2026-10-13._
