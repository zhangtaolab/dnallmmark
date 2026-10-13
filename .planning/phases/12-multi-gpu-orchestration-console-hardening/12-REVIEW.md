---
phase: 12-multi-gpu-orchestration-console-hardening
reviewed: 2026-10-13T14:19:48Z
depth: standard
files_reviewed: 27
files_reviewed_list:
  - Makefile
  - README.md
  - dnallm-mark/css/progress.css
  - dnallm-mark/css/styles.css
  - dnallm-mark/data/progress/.gitkeep
  - dnallm-mark/js/config.js
  - dnallm-mark/js/data.js
  - dnallm-mark/js/progress.js
  - dnallm-mark/progress.html
  - docs/multi-gpu.md
  - pipeline/run_sweep_shard.py
  - script/gen_progress.py
  - tests/js/progress-page.test.js
  - tests/test_sweep_shard.py
  - tests/tui/__snapshots__/data_manager.svg
  - tests/tui/__snapshots__/env_check.svg
  - tests/tui/__snapshots__/monitor_empty.svg
  - tests/tui/__snapshots__/monitor_running.svg
  - tests/tui/__snapshots__/run_config.svg
  - tests/tui/__snapshots__/selection_datasets.svg
  - tests/tui/__snapshots__/selection_models.svg
  - tests/tui/__snapshots__/wizard.svg
  - tests/tui/test_gen_progress.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_snapshots.py
  - tui/screens/run_config.py
findings:
  critical: 0
  warning: 8
  info: 3
  total: 11
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-10-13T14:19:48Z
**Depth:** standard
**Files Reviewed:** 27
**Status:** issues_found

## Summary

Reviewed the Phase 12 multi-GPU orchestration surface at standard depth:
`pipeline/run_sweep_shard.py` (LPT shard + per-worker Popen + merge mode with
SHA256 verification) was traced end-to-end including its merge-mode validation,
copy/verify passes, and manifest-union loops; `script/gen_progress.py` and the
static web mirror (`progress.html` / `js/progress.js` / `css/progress.css` /
`js/data.js` / `js/config.js`) were reviewed for XSS escaping, state handling,
and data-contract consistency; `tui/screens/run_config.py` was reviewed around
the slot-4 focus-trap base (`_PickerReturnModal`) and the `compact=True`
rendering fix; all five test modules were read in full; the 8 committed SVG
goldens were inspected for corruption/emptiness (all are well-formed Rich
terminal SVGs, 223-235 lines each, non-empty, consistent shape — no findings).

The core mechanisms are sound: the LPT partition is provably disjoint and
covering, the merge validates collect-all before any copy, refuses on any
SHA256 mismatch before manifests land, and the lane-equality guard correctly
mirrors `run_sweep._manifest_payload`'s identity projection (verified against
the real projection). No BLOCKER-severity defects were found. Eight WARNINGs
were identified, concentrated in `run_sweep_shard.py` (doc/behavior mismatch
on `--gpus` validation, worker-log truncation on the documented resume path,
stale-file accumulation on re-merge over a changed worker set, unhandled
`OSError` in the verified-copy step, hash-order-fragile lane-value
canonicalization, silently-ignored `--models` in merge mode) and in
`tui/screens/run_config.py` (a marked-then-disabled custom model is stuck in
the run spec and cannot be unmarked from the UI; operator-facing CJK
punctuation composed in the screen module, invisible to the i18n grep lock).

## Warnings

### WR-01: `--gpus` is int-validated although documented as verbatim "operator-owned strings, ARITY-validated only"

**File:** `pipeline/run_sweep_shard.py:385-388` (vs. help text at `:303-311` and module docstring at `:114-119`)
**Issue:** The `--gpus` help text and module docstring state each value "is
passed verbatim as that worker's CUDA_VISIBLE_DEVICES — operator-owned
strings, ARITY-validated only (no nvidia-smi probing)". But `_parse_gpus`
coerces every token with `int(stripped)` and collects
`non-numeric GPU id {stripped!r}` as a problem — so a legitimate
`CUDA_VISIBLE_DEVICES` value that is not a decimal integer (a GPU UUID or a
MIG instance id like `MIG-GPU-xxxx/...`, both legal and commonly used on
multi-GPU hosts to pin devices robustly) is refused at validation. Either the
docs over-promise or the code over-validates; on the machine where N>2 smoke
runs (D-05), UUID pinning is a realistic operator need.
**Fix:** Validate arity and emptiness only, keeping the tokens as strings:

```python
def _parse_gpus(raw, problems):
    if raw is None:
        return None
    gpus = []
    for token in raw.split(","):
        stripped = token.strip()
        if not stripped:
            problems.append(f"empty GPU id element in --gpus {raw!r}")
            continue
        gpus.append(stripped)   # verbatim operator-owned string (D-05)
    return gpus
```

(and drop the `str(gpus[i])` at the spawn site — it is already a string). If
int-only is the intended contract, fix the help text and module docstring
instead so the runbook does not promise verbatim forwarding.

### WR-02: Frozen worker-log path opened `"w"` — a resume relaunch destroys the previous run's diagnostic log

**File:** `pipeline/run_sweep_shard.py:1071-1072` (naming at `:205-209`)
**Issue:** The tee log is opened `open(log_i, "w", ...)` at the frozen,
NON-unique path `{base}-mgpu-w{i}.log`. The module docstring says the spawn
discipline is "the `sweep_launcher._spawn` discipline, copied VERBATIM" — but
the launcher derives its tee path with a per-launch timestamp
(`tui/services/sweep_launcher.py:466-474`,
`TEE_TIMESTAMP_FORMAT`/`TEE_FILENAME_FORMAT`), so its `"w"` open never
clobbers a prior log. Here the frozen path plus `"w"` means the documented
recovery path (a worker dies; relaunch the orchestrator — workers are
resume-safe via the `trainer_state.json` marker, A4/D-08) TRUNCATES the exact
log that would explain the crash. The recovery action destroys the evidence.
**Fix:** Either append (`open(log_i, "a", encoding="utf-8")`) or make the log
name per-launch (e.g. `{base}-mgpu-w{i}-{timestamp}.log`, the launcher's own
discipline). Append is the smallest change consistent with the frozen-naming
authority.

### WR-03: Re-merge over a previously-merged root with a changed worker set leaves stale cell files that downstream consumers will export

**File:** `pipeline/run_sweep_shard.py:506-529` (`_copy_verified` overwrite-only semantics), copy pass `:839-865`, manifest write `:906-909`
**Issue:** The merge never deletes anything (by design) and `_copy_verified`
only overwrites destinations it copies to. The idempotency guarantee
("idempotent re-merge: re-copying identical bytes re-verifies green", pinned
by `test_merge_is_idempotent_byte_stable`) holds only for an UNCHANGED worker
set. Reachable sequence: launch workers over `{a,b}`/`{c}` under base
`finetuned`, merge (merged root now holds `a`,`b`,`c`), later delete one
worker root and relaunch the orchestrator with a smaller `--models` set, then
merge again — the merged `sweep_manifest.json` correctly lists only the new
union, but the previously-copied `c` cell files remain on disk under the
merged root. `script/export_runs.load_run_records` walks the FILE TREE (model
dirs × `seed_\d+` dirs), not the manifest (this is exactly what
`test_merged_root_is_consumer_equivalent` asserts), so the stale cells leak
into the exported leaderboard data while the manifest claims they are absent
— a silent wrong-number path in a repo whose stated core value is "every
number on the public leaderboard is correct".
**Fix:** Before the copy pass, enumerate the merged root's existing
allowlisted files under `base_root` and (a) refuse if any exists that the
current copy plan does not cover, or (b) at minimum print a loud
`[Merge] warning: N pre-existing file(s) under the merged root are not part
of this merge` so the operator can clean the root first. Refusal is
consistent with the module's own collect-all discipline.

### WR-04: Unhandled `OSError` from `shutil.copyfile`/`mkdir` bypasses the designed merge-refusal message

**File:** `pipeline/run_sweep_shard.py:527-529`
**Issue:** `_copy_verified` handles an unreadable source hash (`_sha256_file`
returns `None` → `False`), but the copy step itself is unprotected:
`dst.parent.mkdir(...)` and `shutil.copyfile(src, dst)` raise on ENOSPC,
EACCES, or a read-only destination. The exception propagates out of the
verify pass as a raw traceback instead of the designed
`[Error] SHA256 mismatch ... merge refused, merged manifests NOT written`
collect-all diagnostic. The safety property accidentally holds (the crash
still lands before the manifests are written), but the operator gets a stack
trace, not a diagnosis, and the failure is indistinguishable from a bug.
**Fix:** Wrap the copy step and convert to the mismatch path:

```python
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copyfile(src, dst)
    except OSError:
        return False
    return _sha256_file(dst) == src_hash
```

### WR-05: Lane-equality comparison canonicalizes Python sets via `json.dumps(..., default=str)` — hash-order-fragile

**File:** `pipeline/run_sweep_shard.py:775-776`
**Issue:** The cross-worker lane check canonicalizes each root's value SET
with `json.dumps(value, sort_keys=True, default=str)`. A `set` is not JSON
serializable, so `default=str` fires and the canonical form becomes
`str(set)` — whose element order is the set's internal iteration order, which
for strings is PYTHONHASHSEED-dependent across processes and can differ even
between two equal-content sets with different insertion histories (different
cell orders across worker manifests). Two workers with IDENTICAL lane values
can therefore, in rare layouts, produce different canonical strings and be
falsely refused ("lane flag differs"), the opposite failure of the Pitfall-6
silent pick-first but still a spurious operator-facing refusal. (False
accepts are not possible: unequal contents always yield unequal strings.)
**Fix:** Canonicalize deterministically:

```python
canonical = {
    json.dumps(sorted(value), default=str)
    if isinstance(value, (set, frozenset)) else
    json.dumps(value, sort_keys=True, default=str)
    for value in per_root.values()
}
if len(canonical) > 1:
```

### WR-06: `--models` is silently ignored in merge mode

**File:** `pipeline/run_sweep_shard.py:689-702` (`run_merge` validation block; flag help at `:317-321`)
**Issue:** The `--models` help text and the module docstring state "Merge
mode takes no `--models` (the worker manifests are the merge's source of
truth)", and `run_merge` already refuses a non-empty passthrough
("a merge takes no sweep flags") and `--dry-run` combined with `--merge`.
But because `--models` is an orchestrator-owned flag it never lands in the
passthrough — a launch-mode command line reused with `--merge` added (an easy
copy-paste) silently ignores `--models` instead of refusing collect-all,
contradicting the module's own "never a silent pick-first / collect-all
fail-fast" discipline.
**Fix:** In `run_merge`'s validation block add:

```python
    if args.models is not None:
        problems.append(
            "--merge takes no --models (the worker manifests are the "
            "merge's source of truth)")
```

### WR-07: A marked-then-disabled custom model is stuck in the run spec — rendered unmarked, counted, launched, and impossible to unmark from the picker

**File:** `tui/screens/run_config.py:1242` (mark suppression), `:522-537` and `:1454-1477` (unmark impossible on disabled rows), `:1287-1314` (`_compose_spec` never sanitizes)
**Issue:** `_render_picker` suppresses the visual mark for disabled customs
(`marked.append(key in marked_set and not is_disabled)`), but the persisted
spec is never sanitized: if an operator marks a custom model and the entry is
later disabled in the management overlay, on the next mount `spec.models`
still contains the key. The screen then shows the row UNMARKED while the
status line, preview counts, and the launch-gate enumeration all include it —
and because both mark paths (`PickerList.action_select`, screen
`action_toggle_mark`) deliberately refuse disabled rows with a warning, the
operator CANNOT unmark it from the UI (the only escape is re-enabling the
entry). The UI under-reports what will actually be trained.
**Fix:** Sanitize at load (in `on_run_config_screen_loaded`, after
`self._entries = message.entries`):

```python
        disabled = {
            key for key, status in self._entries.custom_status.items()
            if status.get("custom") and not status.get("enabled", True)
        }
        if set(message.spec.models) & disabled:
            message.spec = replace(
                message.spec,
                models=tuple(m for m in message.spec.models
                             if m not in disabled),
                # same for tasks if disabled customs can be datasets
            )
```

(or surface it as a `disabled_custom` gate problem instead of silently
dropping — either way the spec and the render must agree).

### WR-08: Operator-facing copy composed in the screen module with CJK punctuation — bypasses the I18N-01 grep lock

**File:** `tui/screens/run_config.py:1356` (constants at `tui/strings.py:691-692`; lock at `tests/tui/test_pilot_run_config.py:1414`)
**Issue:** The subset-OFF copy is built inline as
`text = f"{CFG_SUBSET_OFF}（{path}）"` — the fullwidth parentheses
(U+FF08/U+FF09) are CJK punctuation literals living in the screen module,
while the ON counterpart `开（{path}）` lives wholly in `tui/strings.py`. The
module header's locked contract says "zero Chinese literals in this module —
every operator-facing string renders through `tui/strings.py` constants
(grep-enforced)", but the grep lock regex `[一-鿿]` (U+4E00–U+9FFF) cannot see
CJK punctuation, so the lock passes while the contract is violated. The copy
shape is also split across two homes, so OFF/ON can drift.
**Fix:** Move the OFF-with-path shape into `tui/strings.py`:

```python
CFG_SUBSET_OFF_WITH_PATH = "关（{path}）"
```

and render `CFG_SUBSET_OFF_WITH_PATH.format(path=path)` from the screen;
optionally extend the lock regex to CJK punctuation ranges (e.g. add
`　-〿＀-￯`) so this class cannot recur.

## Info

### IN-01: Dead constant `PROGRESS.LEGEND`

**File:** `dnallm-mark/js/progress.js:22`
**Issue:** `LEGEND: '✓ Done · ⠋ Running · ✗ Failed · ⊘ Skipped · ◌ Queued'`
is never referenced — `renderTable()` builds the legend from `CELL_STATES`
directly (lines 312-314). Dead copy invites drift from the real legend.
**Fix:** Delete the constant, or render the table legend from it so the
UI-SPEC copy table stays the single source.

### IN-02: Seed column header interpolated unescaped

**File:** `dnallm-mark/js/progress.js:327`
**Issue:** `PROGRESS.COL_SEED.replace('{seed}', seed)` injects the raw seed
value into a `<th>` while every other data-driven string (model, task, root,
stamp, fraction title) goes through `DataAPI.escapeHTML`. Seeds arrive as
numbers from the maintainer-generated `sweep.json`, so exposure is minimal,
but the inconsistency breaks the page's own escaping discipline.
**Fix:** `PROGRESS.COL_SEED.replace('{seed}', DataAPI.escapeHTML(String(seed)))`.

### IN-03: Zenodo bearer preview token in the public README (pre-existing, documented)

**File:** `README.md:251`
**Issue:** The datasets link carries `?preview=1&token=<JWT>` — a live
(though record-scoped, read-only) bearer token committed to a public
repository. The in-file comment (lines 244-250) documents this as maintainer
decision D-08 with a narrow `.gitleaks.toml` allowlist and a Phase 6 removal
item, so this is a flagged known accepted risk rather than an oversight —
listed here for phase-close awareness only.
**Fix:** No new action beyond the tracked one: when Zenodo record 19135551
publishes, replace the link with the public DOI/URL and drop the allowlist
rule in the same commit (already mandated by the README comment).

---

_Reviewed: 2026-10-13T14:19:48Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
