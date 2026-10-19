---
phase: 10-data-manager-downloads-verification
reviewed: 2026-10-14T15:19:08Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - tests/tui/test_pilot_data_manager.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/test_services_download_queue.py
  - tui/app.py
  - tui/screens/data_manager.py
  - tui/screens/nav.py
  - tui/screens/selection.py
  - tui/services/download_queue.py
  - tui/strings.py
  - tui/styles.tcss
findings:
  critical: 1
  warning: 2
  info: 2
  total: 5
status: issues_found
review_base: bfe65e1005..HEAD
review_classes: CR/WR/IN
review_kind: incremental (delta since the converged prior review at bfe65e1)
---

# Phase 10: Code Review Report (Incremental — post-convergence delta)

**Reviewed:** 2026-10-14T15:19:08Z
**Depth:** standard (per-file + targeted cross-module trace of the delta's landing/presence chains)
**Diff base:** `bfe65e1005` (the prior review's convergence point)
**Files Reviewed:** 11
**Status:** issues_found

## Summary

This is the incremental review of the phase-10 deliverable surface that changed since the
prior review converged at `bfe65e1`: the l6h reroute of every dataset landing site through
`_datasets_base()` (constructor param > `directories.json` `dataset_root` > repo default),
the mlc `KIND_MODEL` lane (`enqueue_model` / `resolve_model_channel` / `_models_base` /
the `-I` dnallm child with `_normalize_model_landing`), and mlc's slot-3 datasets-primary
rework of `data_manager.py` (full official list primary, `v` toggle, `w` wizard, Zenodo
demoted to the queue title row).

The delta's queue-integrity and cancel/retry machinery is sound: the model lane rides the
existing claim/`_finish`/killpg/`_reap` protocol unchanged, boot-resume downgrades
`KIND_MODEL` entries correctly, argv for the `-I` child is a fixed-program LIST with the
repo id allowlist-validated on both lanes, env is exactly `dict(os.environ)`, and the
`-c` program is a frozen module constant (no operator-controlled code). All 192
service tests and 91 Pilot tests pass; ruff is clean on all eleven files.

One landing-correctness defect is release-blocking: the dataset landing base resolves
through a *different* chain than the one the sweep launcher and the env-check
`dataset_dirs` kernel consume, so downloads can land where the configured run does not
read. Two further warnings cover a presence-reconciliation gap on failed model downloads
and the drill-down misrepresenting `KIND_MODEL` rows on the shared queue table.

Out-of-delta notes (checked, excluded per the incremental mandate): the zenodo bundle
staging dir resolving through `settings.state_dir()` rather than the service's own
`state_root()` (present verbatim at `bfe65e1:1830`), the pre-spawn window of the
`load()`-vs-driver downgrade race, and the driver's cross-retry percent throttle are all
pre-existing behaviors untouched by this delta.

## Critical Issues

### CR-01: Dataset landing base resolves through a different chain than the sweep/env-check root — downloads can land where the configured run does not read

**File:** `tui/services/download_queue.py:1207-1213` (`_datasets_base`, the file tier)
**Cross-module evidence:** `tui/services/env_check.py:212` (`env_smoke.check_dataset_dirs(root=dirs.dataset_root_abs)`),
`tui/services/run_config.py:768-772` (`resolve_dirs` → `dataset_root_abs`, REPO_ROOT-anchored) and
`tui/services/run_config.py:1159` (`compose_argv` threads `--dataset_root` whenever the spec carries one),
`tui/app.py:388` (production construction: `DownloadQueueService()` — the flag tier is never threaded).

**Issue:** The l6h delta gives the queue's dataset landing base the chain
`constructor param > directories.json dataset_root > repo pipeline/`, resolving the file
value with `Path(file_root).resolve()`. But every *consumption* side of the datasets —
the env-check `dataset_dirs` kernel and the sweep launcher's `--dataset_root` flag —
resolves through `run_config.load_state()` (the persisted/live spec, seeded from the same
file only when the spec's own value is unset) anchored at `REPO_ROOT`. Two concrete
divergence modes:

1. **Spec-without-file (the primary UI flow):** the operator sets 数据集根 in slot 4 and
   launches without pressing `[s]` 保存默认. The live spec threads
   `--dataset_root X` into every launch and the env kernel checks `X/datasets`, but the
   queue reads only `directories.json` (absent) and lands every download under the repo
   `pipeline/datasets`. The `ENV_ROUTE_MISSING_DATASETS` loop (env fail → `[3]` download →
   env still fail) never closes: downloads land where the sweep does not read, while the
   queue's reconcile (which reads its own landing base) flips the TUI presence to
   present — the console then claims datasets are in place for a run that cannot see them.
2. **Relative file values:** a relative `dataset_root` in `directories.json` resolves
   against the *process CWD* in `_datasets_base()` (`Path(v).resolve()`) but against
   `REPO_ROOT` in the launch/env chain (`_abs_against_repo_root`), so the two surfaces
   disagree about the location even when both read the same file entry.

The model lane added in the same delta explicitly avoids this hazard
(`_models_base()` walks the run-config chain "so download landing and presence checking
can never disagree about the root"); the dataset lane did not get the same treatment even
though its consumer is the sweep's `--dataset_root`.

**Fix:**
```python
def _datasets_base(self):
    if self._dataset_root is not None:
        return self._dataset_root
    # the SAME chain the env kernels and compose_argv consume (the
    # _models_base precedent): the run-config spec, seeded from
    # directories.json, resolved REPO_ROOT-anchored — never CWD.
    dirs = run_config.resolve_dirs(run_config.load_state())
    if dirs.dataset_root_abs:
        return Path(dirs.dataset_root_abs)
    return self._pipeline_dir
```
(`run_config.load_state()` already seeds the spec from `load_directories_tolerant()`, so
the existing L6H-03 tests — file-tier redirect, param-beats-file, corrupt-file degrade,
byte-identity-when-absent — keep their semantics; only the CWD anchoring and the
spec-blindness disappear.)

## Warnings

### WR-01: A failed KIND_MODEL download flips the selection 下载 column to 已下载 — presence is dir-existence while the done gate requires config.json

**File:** `tui/services/download_queue.py:1988-2009` (the exit-0 failure paths of
`_run_model_download` — nothing removes the partial tree) and
`tui/services/download_queue.py:2011-2086` (`_normalize_model_landing` returns failure
codes while leaving the hoisted/scaffolding tree in place);
`tui/services/selection.py:543-546` (`model_presence`: `MODEL_PRESENCE_PRESENT if
is_dir(base + value)`).

**Issue:** The model lane's done gate requires `config.json` DIRECTLY in the landing dir
(`MODEL_DONE_MARKER`), but the presence decision the 下载 column renders gates only on
`os.path.isdir(landing)`. The `-I` child (`snapshot_download(cache_dir=landing)`)
creates the landing dir early, and every post-spawn failure mode — nonzero exit
mid-download, `model_nesting_ambiguous`, `model_hoist_error`, and
`landing_incomplete` (no `config.json`) — leaves the landing dir on disk (nothing is
cleaned up, per the never-delete discipline). At the next snapshot reload (mounting slot
2, any `e`/`w`/done event) the column therefore reads ✓ 已下载 for a model whose
download FAILED and has no `config.json`; `d` on that row then toasts 该模型已下载,
and `enqueue_model` would answer `already_present` if the queue state were ever lost.
The two surfaces (queue row: failed; download column: downloaded) disagree, and the
column is the surface operators use to decide what is sweepable.

**Fix:** Align the presence decision with the done gate — in
`tui/services/selection.py::model_presence`, treat a landing dir as PRESENT only when
the run_finetune resolution target exists (`os.path.isfile(base + value + "/config.json")`,
the `MODEL_DONE_MARKER` twin), keeping MISSING otherwise; or, if DCL-02's dir-existence
semantics must stand, have the model lane surface a per-key "landing incomplete"
presence override the same way `merge_presence` overlays reconcile-pass datasets.

### WR-02: The slot-3 drill-down renders "channel: unknown (unknown_key)" for healthy KIND_MODEL queue rows — channel_detail only resolves the dataset registry

**File:** `tui/screens/data_manager.py:465-485` (`DataManagerBackend.channel_detail`)

**Issue:** The slot-3 queue table renders ALL shared-queue entries — including
`kind=KIND_MODEL` rows, which share the one queue and driver with datasets. `enter` on a
model row routes to `channel_detail(key)`, which calls only
`self._queue.resolve_channel(key)` (the DATASET registry read); a model key is absent
there, so the drill-down — whose contract is "data, never translated, never elided"
(D-03) — shows `channel: unknown (unknown_key)`, `download_url: -`, and `argv: -` for a
row that is downloading or done through a perfectly healthy dnallm channel. The
verbatim-drill-down surface states a factually wrong channel disposition for every model
row on the shared queue.

**Fix:** In `channel_detail`, route model keys through the model lane (e.g. check the
entry kind via `entries()`, or fall back to `resolve_model_channel(key)` when
`resolve_channel` returns None for a queued key) and render its `source_url`
(`https://www.modelscope.cn/models/<repo_id>`) plus the `-I` argv shape; only keys that
resolve through neither registry should read `unknown (unknown_key)`.

## Info

### IN-01: `z` during the probe-in-flight window renders the "not yet public" toast as fact

**File:** `tui/screens/data_manager.py:1276-1281` (`action_zenodo_bundle`)

**Issue:** `_zenodo_state` is `None` until the mount probe answers; `z` pressed in that
window satisfies `!= PROBE_PUBLIC` and fires `DL_ZENODO_DISABLED_TOAST`
("尚未公开 — 公开后此入口自动激活") — an unproven claim about a record that may well be
public (the run-time leg re-probes regardless, so only the copy is wrong). A
probing-specific dismissal (or deferring the gate to the run-time probe the bundle lane
already performs) would keep the never-silent rule without asserting the unproven state.

### IN-02: `ABOUT_MILESTONE_STAGE` is stale — names phase 9 as the current phase on the About screen

**File:** `tui/strings.py:605`

**Issue:** The About screen's milestone row reads "已交付: Phase 7-8 · 本相位: 9 自定义接入"
while this delta itself lands phase 10 and the nav shell's own annotations record slots
4/5 real since phases 11-06/11-07. The constant is documented as "updated per milestone"
— it has not been. Update at the phase boundary.

---

_Reviewed: 2026-10-14T15:19:08Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (incremental over bfe65e1005)_
