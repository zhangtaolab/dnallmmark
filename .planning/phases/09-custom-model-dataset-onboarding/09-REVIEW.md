---
phase: 09-custom-model-dataset-onboarding
reviewed: 2026-10-12T00:00:00Z
depth: standard
files_reviewed: 26
files_reviewed_list:
  - pipeline/registry_loader.py
  - schemas/custom_registry.json
  - tests/test_registry_loader.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_matrix.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/test_pilot_wizard.py
  - tests/tui/test_services_about.py
  - tests/tui/test_services_custom_entries.py
  - tests/tui/test_services_custom_validation.py
  - tests/tui/test_services_custom_validation_import.py
  - tests/tui/test_services_gauntlet.py
  - tui/app.py
  - tui/screens/about.py
  - tui/screens/env_check.py
  - tui/screens/nav.py
  - tui/screens/selection.py
  - tui/screens/wizard.py
  - tui/services/about.py
  - tui/services/custom_entries.py
  - tui/services/custom_validation.py
  - tui/services/gauntlet.py
  - tui/strings.py
  - tui/styles.tcss
findings:
  critical: 1
  warning: 5
  info: 7
  total: 13
status: issues_found
---

# Phase 9: Code Review Report

**Reviewed:** 2026-10-12
**Depth:** standard
**Files Reviewed:** 26
**Status:** issues_found

## Summary

Adversarial review of the custom model/dataset onboarding phase: the D-09 enabled-skip addition to `registry_loader`, the entry-shape schema, the wizard/gauntlet/custom-store services, the nav shell + about screen, the selection integration, and all 13 test modules.

The load-bearing invariants largely hold, verified independently against source (not just the test suite):

- **Official registries never written.** Every custom-registry write routes through `custom_entries._write_entries` → `settings.atomic_write` under `settings.config_dir()`; no code path targets `pipeline/{models,datasets}_info.json`; tests hash-pin the official files across land/undo/toggle and the full w→gauntlet→land→e loop. The gauntlet's only outputs live in `tempfile.TemporaryDirectory` scopes.
- **registry_loader change is additive.** With no overlay present the official dict object is returned as-is (byte-identity); the D-09 skip is literal-`False`-only via `entry.get("enabled") is not False` with an `isinstance(entry, dict)` guard preserving pre-D-09 behavior for non-object entries; the skip sits after the collision fail-fast.
- **Gauntlet subprocess discipline.** argv is a list (`sys.executable` + absolute script paths, never shell-interpolated), env is `dict(os.environ)` plus exactly one override, verdicts come from parsed artifacts (`sweep_manifest.json` cells / `n_audit.json` fields, never exit codes alone), every audit output flag is temp-pinned with a real-subprocess byte-unchanged regression gate over the four committed artifacts.
- **Land-only-on-all-pass / rollback semantics.** The land seam fires exactly once per all-✓ entry on the event loop keyed to the current run; import per-entry rollback keeps earlier lands on later failures (documented semantics, pinned by tests); session undo is single-use; the WR-02 run-id drop prevents an abandoned run from landing.
- **Digit nav** has zero `Binding(priority=True)` anywhere under `tui/` (grep-verified, matching the lock test); the Input-eats-digits interplay is Pilot-pinned.
- **i18n / styles / CI.** Zero Chinese literals in all six screen modules and `tui/app.py` (grep-verified); zero hardcoded hex in `tui/` (grep-verified — the `$token` span workaround resolves `app.current_theme.accent` live, no hex leakage); `tui/services/**` carries zero textual imports (grep-verified); the CI workflow is byte-untouched since phase 05-01.

One Critical defect and several Warning-level gaps remain, detailed below. The Critical is an input-encoding gap in the one file the whole overlay design funnels through.

## Critical Issues

### CR-01: Non-UTF-8 custom registry file raises uncaught UnicodeDecodeError — breaks the fail-loud contract AND hangs the selection screen

**File:** `pipeline/registry_loader.py:125`
**Issue:** The custom-file read catches only `OSError` and `json.JSONDecodeError`:

```python
try:
    with open(custom_path, "r", encoding="utf-8") as f:
        custom = json.load(f)
except (OSError, json.JSONDecodeError) as exc:
    raise SystemExit(...) from exc
```

`UnicodeDecodeError` (a `UnicodeError`/`ValueError` subclass, a *sibling* of `json.JSONDecodeError`, not a subclass) escapes both clauses. A custom registry saved in a non-UTF-8 encoding (e.g. GBK for Chinese entry names — a plausible operator artifact for this project's audience; the schema tests themselves round-trip `自定义系列` content) therefore:

1. **Pipeline side:** crashes `run_finetune.py` at module level with a raw `UnicodeDecodeError` traceback instead of the contracted named `SystemExit` ("a present-but-malformed custom file … is a hard error **naming the file**", T-07-04). The sibling tolerant seam `artifact_loader.load_json_artifact` (pipeline/artifact_loader.py:38-41) *does* catch `UnicodeDecodeError` — the loader is the one JSON reader in this chain that does not.
2. **TUI side:** `SelectionBackend._load_entries` (`tui/screens/selection.py:646-659`) degrades only on `(OSError, SystemExit)`. The `UnicodeDecodeError` escapes into the `@work(thread=True)` load worker; `DataLoaded` never posts, so the selection screen sits on the "加载中…" loading row forever — the documented "malformed custom overlay degrades to the load-error state naming the path — the app stays alive" contract is silently bypassed.

**Fix:**
```python
    try:
        with open(custom_path, "r", encoding="utf-8") as f:
            custom = json.load(f)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SystemExit(
            f"[Error] custom registry file {custom_path} is not readable "
            f"JSON: {exc}"
        ) from exc
```

Once the loader converts it to the named `SystemExit`, the selection-screen seam already handles it correctly, and a regression test mirroring `test_malformed_custom_models_json_fails_loud_naming_file` with `path.write_bytes("{\"k\": \"自定义\"}".encode("gbk"))` closes the loop.

## Warnings

### WR-01: Read side honors `DNALLMMARK_CUSTOM_REGISTRY_DIR` but the write seam does not — lands and toggles silently vanish in a single-var-pin configuration

**File:** `tui/services/custom_entries.py:135-158` (read), `tui/services/custom_entries.py:172-206, 232-256, 383-395` (writes); `tui/screens/selection.py:662-671` (`_overlay_registry_dir`)
**Issue:** The 09-06 machine-dependence self-fix added `registry_dir` to `read_entries`/`custom_registry_path`, and `SelectionBackend.load_selection_data` passes `_overlay_registry_dir()` (the `DNALLMMARK_CUSTOM_REGISTRY_DIR` env value) so the management view and the overlay view describe one file. But every **write** (`land`, `undo`, `set_enabled`, and `export_registry`'s source read) still resolves `settings.config_dir()` unconditionally. When an operator pins only `DNALLMMARK_CUSTOM_REGISTRY_DIR=/shared` (the documented whole-dir override) with `DNALLMMARK_TUI_CONFIG_DIR` unset:

- the table lists `/shared` customs, but `e` on one of them calls `set_enabled` against `~/.config/dnallmmark`, finds no key, returns `False`, and just refreshes — the toggle deterministically never works with no honest error;
- a successful wizard land writes to `~/.config/dnallmmark`, the `on_changed` refresh re-reads `/shared`, and the just-landed badge/count never appears — the operator lands successfully and the entry is invisible both to the table and to `registry_loader` (which reads `/shared`).

Every test pins **both** env vars to the same root (`_pin_roots`, `_pin_config_roots`), which masks the divergence. The default production case (no env vars) is coherent — both roots resolve `~/.config/dnallmmark`.
**Fix:** Either make the write rail resolve the same root the overlay reader resolved (pass `_overlay_registry_dir()` through `land`/`set_enabled`/`undo`), or fail loud at TUI startup when the two roots diverge, and add a test that pins only one variable.

### WR-02: Missing official registry raises OSError across the gauntlet service boundary — panel rows stick in-flight

**File:** `tui/services/gauntlet.py:475-503` (`_dry_run_counterpart`), `tui/services/gauntlet.py:542-554` (`_official_registry`)
**Issue:** The module contract states "A timeout or a crash yields a failed `GauntletItem` … **never an exception crossing the service boundary**". Every other failure path honors it (`read_entries` failure → failed item; subprocess timeout/crash → failed item). But `dry_run_precheck`'s first act, `_dry_run_counterpart`, calls `_official_registry`, whose bare `open(...)`/`json.load` raises `OSError`/`json.JSONDecodeError` if the official registry is missing or corrupt. The exception propagates out of `dry_run_precheck`, kills the wizard's `_gauntlet_worker` OS thread before any `GauntletItemDone` is posted, and the panel rows stay "⠋ …运行中" forever — the exact hang the boundary contract exists to prevent.
**Fix:** Wrap the `_official_registry` read and return `self._failed_item(run_id, kind, LEG_DRY_RUN, candidate_key, ("official_registry_unreadable",))` on failure (mirroring the `existing_custom_registry_unreadable` path at gauntlet.py:219-227).

### WR-03: Import lane accepts metrics and model types the wizard lane rejects — a landed entry can reference an uncomputable metric

**File:** `tui/services/custom_validation.py:508-581`; `schemas/custom_registry.json:28` (`"type": {"type": "string"}`), `schemas/custom_registry.json:64` (`"metric": {"type": "string"}`)
**Issue:** The two validation lanes disagree. The wizard lane enforces `metric ∈ METRIC_REGISTRY` (28 frozen names), model `type ∈ {MLM, CLM, DL}`, and dataset `Category`/`type` enums. The import lane (`validate_import_document`) validates schema + collisions only — and the schema types `metric` and model `type` as plain strings (`Category` and dataset `type` *are* schema enums, so those two are covered). A shared file with `"metric": "bleu"` or model `"type": "RNN"` passes validation, passes the gauntlet (the dry-run plans cells without reading `metric`; the audit leg never sees models), lands, and produces a run whose primary metric the downstream scripts cannot compute — a defect discovered only after launch, the class of failure this phase's gate design exists to prevent.
**Fix:** Add the metric enum (and the model-type enum) to the `$defs` in `schemas/custom_registry.json`, or extend `validate_import_document` to run the same vocabulary checks the wizard lane runs over the injected `metric_registry`.

### WR-04: Import/export file I/O runs on the event loop, regressing the D-03 worker discipline the phase applies everywhere else

**File:** `tui/screens/wizard.py:1509-1524` (`_validate_import_path` — JSON read inside `Input.Submitted`), `tui/screens/wizard.py:1562-1575` (`_validate_export_path` — `shutil.copyfile` inside `Input.Submitted`), `tui/screens/wizard.py:1481-1505` (`action_do_export` → `has_custom_entries()` read)
**Issue:** The `_PathPromptModal.on_input_submitted` handler invokes the injected `import_read`/`export_registry` seams synchronously on the event loop. These perform real file I/O (`read_import_candidates`, `shutil.copyfile`). The phase's own D-03 discipline — pinned by `test_preset_menu_load_runs_off_the_event_loop` for the preset-menu read and stated in the wizard docstring ("the 08-06 discipline: the console never freezes") — routes every registry/file read through an exclusive thread worker. On a network-mounted import path or a slow disk the prompt freezes the whole console for the duration.
**Fix:** Move the validate call into a `@work(exclusive=True, thread=True)` worker posting a message back to the prompt (the `PresetMenuLoaded` pattern), or at minimum document the deviation.

### WR-05: `tui/services/about.py` carries Chinese literals and no i18n lock covers it — the "i18n grep-lock close-out" is incomplete

**File:** `tui/services/about.py:1-44`
**Issue:** The stated invariant is "zero Chinese in screens/services source," and the services-tier locks assert it for `gauntlet.py` (`test_services_gauntlet.py:471-475`) and `custom_validation.py` (`test_services_custom_validation.py:661-664`). But `tui/services/about.py`'s docstring is full of Chinese (关于-screen, 软件版本, 数据版本, 未安装, 自定义, 官方…), no lock test scans it (nor `quick_check.py`, which also matches the CJK grep), and the 09-06 close-out commit (34f5d17) claims the i18n grep lock is complete. It is docstring text, not rendered copy, so there is no operator-facing duplication — but the lock has a hole and the module violates the letter of the invariant the phase declares closed.
**Fix:** Either extend the services-tier lock list to every `tui/services/*.py` module (and anglicize or accept the about/quick_check docstrings), or scope the invariant to "operator-facing copy" in the lock assertion.

## Info

### IN-01: Dead None-guard on a raising API — `DOMQuery.first` never returns None on 8.2.8

**File:** `tui/screens/wizard.py:860-864`
**Issue:** `_refresh_advisories` does `check = self.query(f"#wiz-{spec.wid}-check").first(Static)` then `if check is None: continue`. Per the module's own probe-pinned fact (nav.py `_first_or_none` docstring): `DOMQuery.first` **raises** `NoMatches` on an empty query on textual 8.2.8 — it never returns None. Today the guard is unreachable (advisory widgets always exist for the current step's fields), but the comment claims a None path that does not exist; a future caller invoking `_refresh_advisories` outside the form phase becomes a `NoMatches` crash.
**Fix:** Use `_first_or_none(self.query(...))` like the rest of the module.

### IN-02: Private textual API `_push_result_callback` in the composition root

**File:** `tui/app.py:253`
**Issue:** `self.screen._push_result_callback(self.screen, None)` touches a private textual internal to patch the boot-screen bookkeeping gap (documented, probe-pinned on 8.2.8). Mitigated by the `textual>=8.2,<9` pin in pyproject.toml, but it belongs on the textual-9 upgrade checklist explicitly.
**Fix:** Note it in the upgrade checklist; prefer an upstream issue/fix when the major bump happens.

### IN-03: Session undo toasts success unconditionally

**File:** `tui/screens/wizard.py:1352-1374`
**Issue:** `action_undo_landed` ignores the undo seam's return value: `custom_entries.undo` returns `False` for an absent key or corrupt file, but the wizard toasts "✓ 已撤销 {key}" regardless — a small honesty gap against the "never toast a lie" discipline `action_toggle_enabled` follows (refresh-to-honest-state on a `False` return).
**Fix:** Toast the undo result only when the seam returns True; otherwise surface a failure toast/refresh.

### IN-04: Import-mode group heads always render in the success style

**File:** `tui/screens/wizard.py:1053-1059`
**Issue:** `_style_gauntlet_panel` styles every import-mode `#gauntlet-head-{i}` with `_ROW_STYLE_PASS` (bold `$success`) regardless of the group's outcome; the verdict lives only in the group's status line. Cosmetic (glyph structure carries the meaning under NO_COLOR), but a failed entry's header reads as bold-green.
**Fix:** Style the head dim/pass from `group["status"]` when present.

### IN-05: Nondeterministic metric-enumeration text in the enum problem message

**File:** `tui/services/custom_validation.py:354-358`
**Issue:** `_check_enum` renders `allowed=", ".join(allowed)`. For `metric`, `allowed` is the `METRIC_REGISTRY` **frozenset**, so the 28-name "可选:" list renders in hash order that varies per process (PYTHONHASHSEED) — same defect, different message, on every run. The species/tokenizer vocabularies are sorted tuples and deterministic.
**Fix:** `", ".join(sorted(allowed))` (or pass a sorted tuple at the call site).

### IN-06: Version-pinned test breaks on every release bump

**File:** `tests/tui/test_services_about.py:299-304`
**Issue:** `test_derive_about_data_default_root_is_the_repo_pyproject` asserts `data.software_version == "0.7.1"` — a hardcoded literal that fails on the next version bump (and unlike the 62/50 registry counts, it has no structural reason to be pinned).
**Fix:** Parse the repo pyproject in the test and assert equality against it, keeping the "default root is the repo pyproject" property without the literal.

### IN-07: Misleading test structure — second app block indented inside the first scenario

**File:** `tests/tui/test_pilot_nav_shell.py:318-327`
**Issue:** In `test_bottom_bar_clips_at_80_help_modal_stays_complete`, the 120x40 "full map renders" scenario is a second `app = _app()` / `run_test` block indented at 4 spaces inside the same function, preceded by a comment left *inside* the first `async with` block ("# at the 120x40 design grid the full left map renders (no clip)") that actually describes the code after it. Valid Python, but it reads as one scenario and confuses failure attribution.
**Fix:** Split into its own `test_bottom_bar_full_map_renders_at_design_grid` function.

---

_Reviewed: 2026-10-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
