---
phase: 08-tui-foundation-env-check-selection
reviewed: 2026-10-14T11:51:28Z
depth: standard
files_reviewed: 24
files_reviewed_list:
  - Makefile
  - pipeline/env_smoke.py
  - tests/test_env_smoke_bytes.py
  - tests/tui/test_pilot_boot.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_matrix.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_services_env_check.py
  - tests/tui/test_services_env_gate.py
  - tests/tui/test_services_quick_check.py
  - tests/tui/test_services_registries.py
  - tests/tui/test_services_selection.py
  - tui/app.py
  - tui/__main__.py
  - tui/screens/env_check.py
  - tui/screens/matrix.py
  - tui/screens/selection.py
  - tui/services/env_check.py
  - tui/services/env_gate.py
  - tui/services/quick_check.py
  - tui/services/registries.py
  - tui/services/selection.py
  - tui/strings.py
  - tui/styles.tcss
findings:
  critical: 1
  warning: 3
  info: 4
  total: 8
status: issues_found
---

# Phase 8 (TUI Foundation — env check + selection): Incremental Code Review Report

**Reviewed:** 2026-10-14T11:51:28Z
**Depth:** standard (cross-module: textual 8.2.8 worker/screen semantics verified against the installed package)
**Files Reviewed:** 24
**Status:** issues_found (1 Critical, 3 Warnings, 4 Info)

## Summary

Incremental re-review of the Phase 08 deliverable surface at HEAD, over the
changes that landed since this phase's review converged at diff_base
`220c0bc` (phases 09-12 plus quick tasks 261014-l6h/mlc/f4w/dcl — most
heavily: `selection.py` reshaped into the models-only slot 2 by mlc,
`registries.py` gaining `load_dnallm_compat`, matrix/strings/styles
extension, and the env-check/storage threading).

The foundation invariants mostly hold under the later changes: the services
layer stays textual-free (verified imports), the Pilot harness seams stayed
fake-injectable through every reshaping, i18n stays single-homed (grep locks
green), the byte goldens were re-verified coherent against the current
`main()` order, and the heavily-reworked app.py queue driver / min-size
guard / refresh-race logic (WR-01/WR-02/WR-06 classes) checked out —
including two non-obvious textual facts verified against the installed
8.2.8 package: `@work(exclusive=True)` cancels only workers sharing the
same (node, group), so the default-group workers across screens/app cannot
cancel each other; and `ModalScreen.dismiss()` pops the stack synchronously,
so the `TemplateMenuModal` dismiss-then-push ordering is safe.

However, one BLOCKER-class defect chain was found and **proven by
execution**: the tolerant artifact-loading invariant (an enumerated
foundation invariant of this phase) is incomplete, and because every
`@work` site uses textual's default `exit_on_error=True` (whose handler
"always results in the app exiting"), inputs the loader contract
explicitly accepts crash the entire console rather than degrading. Two
reproductions were run against the real venv (see CR-01/WR-01). The mlc
default-pool rework also introduced a silent degraded state (WR-02), and
several new event-loop file reads contradict the module's own pinned
read-seam discipline (WR-03).

## Critical Issues

### CR-01: Loader-contract registry input crashes the entire console (tolerant seam incomplete + `exit_on_error=True`)

**File:** `tui/services/registries.py:135-145`, `tui/screens/selection.py:794-807`
**Issue:** Two proven crash chains, both ending in a full console exit:

1. **Non-dict custom entry (user-owned file).**
   `registry_loader` deliberately preserves non-object entry values —
   pinned by
   `tests/test_registry_loader.py::test_non_dict_custom_entry_still_merges_after_skip_filter`
   (`{"model-scalar": [1, 2]}` must "not crash the loader where it
   previously merged"). But the Phase 8 projection
   `registries.load_model_entries()` calls `card.get("type")` /
   `card.get("species")` / `card.get(MODEL_CARD_SIZE_FIELD)` on every
   merged entry. Reproduced against the real venv:

   ```
   loader merged OK: [1, 2]
   PROJECTION CRASHES: AttributeError 'list' object has no attribute 'get'
   ```

   A hand-edit of the user-owned `~/.config/dnallmmark/custom_models.json`
   (documented as "user-owned advisory data", T-08-06) therefore raises
   inside the `_load_data` worker (`tui/screens/selection.py:1401-1405`).

2. **Corrupt official registry JSON.** `_load_entries`
   (`tui/screens/selection.py:804-807`) catches only
   `(OSError, SystemExit)`. A corrupt `models_info.json` raises
   `json.JSONDecodeError` (a `ValueError`) from the loader's raw
   `json.load(f)` of the official file. Reproduced:

   ```
   SEAM UNCAUGHT: JSONDecodeError - Expecting property name enclosed
   in double quotes: line 1 column 2 (char 1)
   ```

Both exceptions escape the worker, and no `@work` site in the reviewed
files passes `exit_on_error=False` — textual 8.2.8's default handler
(`App._handle_exception`, "Always results in the app exiting") kills the
console (return code 1) instead of rendering the documented
`SEL_REGISTRY_LOAD_FAILED` degraded state. The same projections also run
in `preset_menu()` (worker, `selection.py:492-497`) and
`CustomOnboardingBackend.build_wizard`. Note the management-read loop at
`selection.py:433-434` already guards
`if not isinstance(entry, dict): continue` — the codebase itself treats
non-dict entries as possible, but the overlay-merged projection does not.

**Fix:** Guard the projection and widen the seam's exception tuple:

```python
# tui/services/registries.py — project non-dict cards as the empty card
def load_model_entries():
    models = registry_loader.load_models_registry()
    entries = []
    for key, card in models.items():
        card = card if isinstance(card, dict) else {}
        entries.append({
            "key": key,
            "type": card.get("type") or "",
            "species": card.get("species") or "",
            "size_m": _to_float(card.get(MODEL_CARD_SIZE_FIELD)),
            "card": card,
        })
    return entries
```

```python
# tui/screens/selection.py — the tolerant seam also degrades on a
# corrupt OFFICIAL file (json.JSONDecodeError is a ValueError, not OSError)
except (OSError, SystemExit, json.JSONDecodeError):
    return [], str(registry_path)
```

Add regression tests: a non-dict custom entry through
`SelectionBackend.load_selection_data()` (must degrade, never raise), and
a corrupt official registry through `_load_entries`.

## Warnings

### WR-01: env_smoke directory kernels raise on missing/malformed registry — console crash at boot, violating the gate's own never-traceback contract

**File:** `pipeline/env_smoke.py:456-457, 461, 516`; `tui/screens/env_check.py:440-446`
**Issue:** The module contract says every check "prints a greppable
PASS:/FAIL: line" and the import kernels honor "report, never traceback" —
but the two directory kernels read their registries raw:

- `check_model_dirs` / `check_dataset_dirs`: bare `open(MODELS_INFO_PATH)`
  / `open(DATASETS_INFO_PATH)` — a missing file raises `FileNotFoundError`
  (reproduced: `KERNEL RAISES: FileNotFoundError ...`);
- `check_dataset_dirs:516`: `datasets_info[name]["Dataset_path"]` — a
  non-dict entry raises `TypeError` (reproduced:
  `KERNEL RAISES: TypeError: string indices must be integers`), and a
  missing key raises `KeyError` (`check_model_dirs:461` already uses the
  tolerant `.get` + `isinstance` form — its twin does not).

The Phase 8 env screen is the OPENING screen and runs these kernels on
every cache-miss boot inside the un-guarded worker loop
(`result = kernel()`, `env_check.py:440-446`), so the exception takes the
CR-01 path (`exit_on_error=True`) and the console exits at startup — in
exactly the broken-environment state the screen exists to diagnose.
`quick_check` (`tui/services/quick_check.py:69-72`) reuses the same
kernels at launch pre-flight. (Same family:
`read_gpu_pins`/`read_numpy_floor_major` `sys.exit` on a malformed
pyproject would raise `SystemExit` — a `BaseException` textual's
`except Exception` does not even catch.)

**Fix:** Make the two kernels honor their own contract:

```python
def check_model_dirs(root=None) -> CheckResult:
    try:
        with open(MODELS_INFO_PATH, "r", encoding="utf-8") as fh:
            models_info = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return CheckResult(
            name="model_dirs", ok=False,
            lines=(f"FAIL: models_info.json unreadable — {exc}",),
        )
    ...
```

plus `datasets_info[name]` shape-guarded the way `check_model_dirs:460-461`
already guards `Model_path` (and update the byte goldens for the new FAIL
shape). Alternatively/additionally, wrap `kernel()` per-kernel in the
screen worker and post an ok=False result on unexpected exceptions.

### WR-02: Degraded compat map renders a silent blank models table on slot 2

**File:** `tui/screens/selection.py:1493-1513, 1473-1484`; `tui/services/registries.py:212-241`
**Issue:** Since the mlc default-pool filter, `_pool_entries()` hides every
official model when `load_dnallm_compat()` degrades to `{}` (missing or
corrupt `pipeline/dnallm_compat.json` — the documented degraded read). With
no landed customs, `entries == []`, so `_rebuild_rows` composes ZERO table
rows: the no-match branch is skipped (`if not filtered and entries:` —
entries falsy), no error row renders (`models_load_error` is None; compat
degradation carries no error signal on `SelectionData`), and the count
readout shows `(已适配 0/0)`. The primary slot-2 surface thus presents a
blank table with no explanation — the operator cannot distinguish
"compat map unreadable" from "no models exist" without pressing `t` by
accident. Contrast: the registries-degraded state renders
`SEL_REGISTRY_LOAD_FAILED` and the n_audit-degraded state renders
`SEL_N_AUDIT_MISSING` on the matrix; compat has no degraded surfacing.

**Fix:** Carry a degraded signal (e.g. a `compat_available: bool = True`
field on `SelectionData`, set False when `load_dnallm_compat()` returns
`{}` while `model_entries` is non-empty) and render a dedicated state row
or warning line under the default pool; or minimally, when the DEFAULT pool
yields zero entries while `data.model_entries` is non-empty, render a
state row naming the degraded pool instead of a blank table.

### WR-03: New synchronous event-loop file reads contradict the pinned D-03/WR-04 read-seam discipline

**File:** `tui/screens/selection.py:1759-1763, 2071`; `tui/screens/env_check.py:201-206, 572-607`
**Issue:** The selection screen's own contract ("every file-reading
service call — the registry/n_audit/compat load AND the preset-menu read —
runs in an exclusive `@work` worker ... a cold cache or a network-mounted
home must never stall the UI", WR-04/T-08-07) is violated by the newer
additions:

- `_manual_landing_path` (`selection.py:1759-1763`, 261014-mlc) calls
  `run_config.load_state()` + `resolve_dirs()` synchronously in the `d`
  action handler;
- `_render_storage` → `EnvCheckBackend.storage_rows()` →
  `run_config.storage_overview()` (`env_check.py:201-206`, 261014-f4w)
  runs `load_state()` plus five `Path.exists()` stats on the event loop at
  mount and on every `[r]`;
- `_submit_save` → `custom_names()` (`selection.py:2071`) reads
  `presets.json` under the config root synchronously — the exact same
  file `preset_menu()` reads inside a worker because of the
  network-mounted-home stall scenario.

All are small local files, so the stall is bounded, but the reads
re-introduce precisely the event-loop blocking the module moved off-loop
by design, and future readers will copy the pattern.

**Fix:** Route the reads through the existing worker discipline: seed the
storage rows / landing path from the loaded snapshot (the same
`load_selection_data` worker already resolves `dirs`), and read
`custom_names()` inside the preset-menu worker (or cache it on the
snapshot). If the synchronous reads are accepted deliberately, amend the
module contract comment to say which reads are exempt and why.

## Info

### IN-01: Dead strings constants after the 2026-10-14 slot split

**File:** `tui/strings.py:212-232, 139, 349`
**Issue:** Seven constants have zero consumers anywhere in the repo
(verified by repo-wide grep): `SEL_COL_TASK`, `SEL_COL_CATEGORY`,
`SEL_COL_METRIC`, `SEL_COL_PRESENCE`, `SEL_PRESENCE_PRESENT`,
`SEL_PRESENCE_MISSING` (all superseded by the `DL_*` vocabulary on slot
3's data manager when the dataset table left slot 2 —
`tests/tui/test_pilot_selection.py:1285-1290` records the test removal),
and `ENV_QUICK_CHECK_PASS` (its `FAIL` twin is consumed by run_config,
but the `PASS` twin never gained a consumer even after Phase 11 shipped).
`SEL_CLEAR_MARKS_CONFIRM` (`:349`) is documented as
landed-for-the-record.
**Fix:** Prune the six superseded constants (or annotate them like the
deliberately-kept `NAV_*` placeholder pair in `tui/screens/nav.py:80-84`,
which documents its own zero-consumer status).

### IN-02: Matrix screen still composes a Textual `Header()` after the nav-shell migration

**File:** `tui/screens/matrix.py:176`
**Issue:** The 09-03 migration retired the Textual Header/Footer on the
env-check and selection screens ("the two shell bars own those rows now"),
but the matrix auxiliary screen still `yield Header()` — it renders the
generic app-title Header and no nav bars, so the pushed matrix shows
different chrome from every base screen (no slot marker, no digit
navigation).
**Fix:** Either migrate the matrix to the `TopMenuBar`/`BottomBar` pair
like its siblings, or leave a comment pinning the auxiliary-screen chrome
as deliberate so the next screen does not copy the retired pattern.

### IN-03: `EnvCheckScreen.action_show_detail` lacks the `is_valid_coordinate` guard its sibling screens carry

**File:** `tui/screens/env_check.py:609-613`
**Issue:** `table.coordinate_to_cell_key(...)` raises for invalid
coordinates — the CR-03 crash class that `matrix.py:253-257` and
`selection.py:1635-1639, 1669-1677, 2124-2128` all guard with
`is_valid_coordinate`. The env screen's enter action calls it unguarded.
Currently unreachable (the eight kernel rows are added at mount and never
removed), but the guard is the codebase's own standard and one future
row-removal change away from a crash.
**Fix:** Add the same guard:

```python
def action_show_detail(self) -> None:
    table = self.query_one("#env-kernels", DataTable)
    if not table.is_valid_coordinate(table.cursor_coordinate):
        return
    row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
    self._open_detail(str(row_key.value))
```

### IN-04: Filter grammar accepts degenerate tokens that render oddly

**File:** `tui/services/selection.py:381-391, 484-492`
**Issue:** `parse_filter_query("=x")` partitions to `axis=""`, producing
`UnknownAxis(axis="")` — the warning line renders an empty axis name
("未知过滤轴: （可用: ...）"). An axis term with an empty value
(`"type="`) matches EVERY entry (`"" in anything`). Both are cosmetic
edge cases on degenerate input.
**Fix:** Skip tokens that are empty on either side of `=` (treat `"=x"`
as a substring term or drop it), and ignore axis terms with empty values
in `_matches_axis`.

---

**Verified-clean notes (for the record):** the default-group
`@work(exclusive=True)` workers across screens/app cannot cancel each
other (textual scopes exclusivity to node+group — verified in
`worker_manager.cancel_group`); `ModalScreen.dismiss()` pops the stack
synchronously so `TemplateMenuModal`'s dismiss-then-push and
`_submit_save`'s `call_after_refresh` confirm are correctly ordered; the
`run_download_queue` busy-flag/generation protocol has no double-release
or lost-wakeup window on the traced interleavings; the env-check refresh
run-id race handling drops stale messages and never persists stale
results; `model_presence`/`_effective_base` join semantics are consistent
with the `run_finetune` expression across all three call sites; the
Makefile lanes (`test`/`test-fast`/`ci` gaining `--group tui`,
`PHASE8_TUI` glob, `snapshot-update`) are internally consistent; and the
styles contract (zero hex, declared spacing tokens) holds in the extended
`tui/styles.tcss`.

_Reviewed: 2026-10-14T11:51:28Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
