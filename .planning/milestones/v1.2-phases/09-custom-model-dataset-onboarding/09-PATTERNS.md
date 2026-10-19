# Phase 9: Custom Model & Dataset Onboarding (自定义接入向导) - Pattern Map

**Mapped:** 2026-10-12
**Files analyzed:** 15 (4 services, 2 screens, 2 modified roots, 1 pipeline edit, 1 schema, 7 test files — several files carry multiple concerns counted once)
**Analogs found:** 15 / 15 (the codebase has a strong analog for every file; several are exact-role exact-flow matches from Phases 7/8)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `tui/services/custom_entries.py` (NEW) | service / store | file-I/O (XDG JSON read-modify-write) | `tui/services/settings.py` (+ presets service seam) | exact |
| `tui/services/custom_validation.py` (NEW) | service | transform (collect-all validation) | `tui/services/templates.py` (`validate_template`) | exact |
| `tui/services/gauntlet.py` (NEW) | service | batch (subprocess orchestration) | Phase 7 `pipeline/run_sweep.py` argv discipline + `env_check.py` run-id worker pattern | role-match (composite) |
| `tui/services/about.py` (NEW) | service | transform (read-only derivations) | `tui/services/registries.py` (tolerant registry reads) | role-match |
| `tui/screens/wizard.py` (NEW) | component (ModalScreen) | request-response (form → report → gauntlet views) | `tui/screens/selection.py:612-805` modal family | exact |
| `tui/screens/about.py` (NEW) | component (Screen) | request-response (read-only) | `tui/screens/env_check.py` (screen + Protocol service injection) | role-match |
| `tui/app.py` (MODIFY) | config / composition root | event-driven (bindings, screen registry, nav shell) | itself (`tui/app.py` HelpModal/SCREENS/guard wiring) | exact |
| `tui/screens/selection.py` (MODIFY) | component | event-driven (`w`/`e` bindings, badge cells, count line) | itself (BINDINGS + `_presence_cell` render helpers) | exact |
| `tui/strings.py` (MODIFY) | config (i18n constants) | n/a | itself (existing SEL_/APP_ constants) | exact |
| `tui/styles.tcss` (MODIFY) | config (CSS) | n/a | itself (theme-token-only rule) | exact |
| `pipeline/registry_loader.py` (MODIFY — D-09 skip) | model / loader | CRUD-read (merge) | itself, `pipeline/registry_loader.py:124-133` collision loop | exact |
| `schemas/custom_registry.json` (NEW) | config (schema) | n/a | `schemas/run_template.json` | exact |
| `tests/tui/test_services_custom_{entries,validation,gauntlet,about}.py` (NEW) | test (tier-1) | n/a | `tests/tui/test_services_templates.py` | exact |
| `tests/tui/test_pilot_{wizard,nav_shell,selection_custom}.py` (NEW) | test (tier-2 Pilot) | n/a | `tests/tui/test_pilot_selection.py` | exact |
| `tests/test_registry_loader.py` (MODIFY — additive enabled-skip tests) | test (tier-1) | n/a | itself (`pin_custom_dir` helper) | exact |

## Pattern Assignments

### `tui/services/custom_entries.py` (service/store, file-I/O)

**Analog:** `tui/services/settings.py`

Copy the XDG-root + atomic-write rails exactly; do NOT write new path or write code.

**Root resolution** (`tui/services/settings.py:69-87`) — custom registries resolve under the SAME config root:
```python
override = os.environ.get(CONFIG_DIR_ENV)   # DNALLMMARK_TUI_CONFIG_DIR — whole-dir override, empty = unset
if override:
    return Path(override)
return Path(user_config_dir(APP_NAME))      # ~/.config/dnallmmark — same root as presets.json & custom_*.json
```
Note: the PIPELINE resolves the custom dir through its own hand-rolled resolver (`pipeline/registry_loader.py:57-81`, env `DNALLMMARK_CUSTOM_REGISTRY_DIR` > XDG > home). The TUI store should target `settings.config_dir() / "custom_models.json"`; the two resolvers yield the identical Linux path by design (settings.py docstring D-10 note).

**Atomic write** (`tui/services/settings.py:90-107`) — all three sanctioned writes (gauntlet-land, undo, `e` toggle) go through this exact function, never a bare `write_text`:
```python
target = Path(path)
target.parent.mkdir(parents=True, exist_ok=True)
tmp = target.with_name(target.name + ".tmp")
tmp.write_text(text, encoding="utf-8")
os.replace(tmp, target)
```

**Docstring contract style** — every Phase 8 service opens with a locked-decisions contract block (see `settings.py:1-36`, `templates.py:1-55`). New services repeat this with D-01..D-16 citations and the "ZERO textual imports" footer.

**Management-view second read path (Pitfall 7):** read the user-owned custom file DIRECTLY (tolerant, `artifact_loader.load_json_artifact`-style None sentinel — the `templates.load_template_file` shape at `templates.py:208-230`), never through `registry_loader` (which hides `enabled:false` rows after D-09).

---

### `tui/services/custom_validation.py` (service, collect-all validation)

**Analog:** `tui/services/templates.py`

**Collect-all pattern** (`templates.py:119-142`) — returns EVERY problem as `(pointer, message)` tuples, sorted, never raises on untrusted input:
```python
validator = jsonschema.Draft202012Validator(load_schema())
problems = [
    (_json_pointer(error.absolute_path), error.message)
    for error in validator.iter_errors(doc)
]
return sorted(problems)
```
Adapt for D-05: the wizard path uses hand-rolled field checks (Chinese labels come from `tui/strings.py`, so jsonschema messages cannot be user-facing verbatim); the IMPORT path uses jsonschema against the new `schemas/custom_registry.json`. Inject data sources (official keys, existing custom file, metric registry constant, fs root) as arguments — pure function, tier-1 testable.

**Tolerant file read for diagnostics** (`templates.py:224-230`):
```python
target = Path(path)
if not target.exists():
    return None, f"template file not found: {target}"
doc = artifact_loader.load_json_artifact(target)
if doc is None:
    return None, f"template file unreadable or not valid JSON: {target}"
return doc, None
```

**Named JSON-shape predicates** (`templates.py:357-376` `_is_json_object`/`_is_json_list`/`_is_json_string`) — reuse the ValueError-for-data-shape / TypeError-for-Python-args discipline.

**Schema loading** (`templates.py:97-116` `load_schema`) — committed schema unreadable raises RuntimeError (repo integrity failure, not input problem).

---

### `tui/services/gauntlet.py` (service, subprocess orchestration)

**Analog A:** Phase 7 `pipeline/run_sweep.py` subprocess/argv discipline — argv is a LIST, `sys.executable`, absolute script paths, explicit env `{**os.environ, "DNALLMMARK_CUSTOM_REGISTRY_DIR": str(staging)}`. Full verified invocation skeleton is in 09-RESEARCH.md "Code Examples" (dry-run argv, manifest parse, audit flags). Load-bearing: audit subprocess MUST override `--data-dir`/`--subsets-out`/`--data-md` to temp (defaults clobber committed artifacts — Pitfall 1); artifact parse via `artifact_loader.load_json_artifact` (None sentinel), never bare `json.load`.

**Analog B:** run-id message tagging — `tui/screens/env_check.py:276-433` (WR-02). The gauntlet runs on a thread worker; every result message carries a `run_id`, and handlers drop stale ones:

```python
# env_check.py:321,388,412 (structure, verbatim ids)
self._run_id = 0
...
run_id = self._run_id  # the run this worker serves (WR-02)
...
def on_check_item_done(self, message) -> None:
    if message.run_id != self._run_id:
        return                          # stale worker result — dropped
```
The gauntlet panel applies the identical tag-and-drop so a cancelled/relaunched gauntlet never backfills a later result (09-RESEARCH STRIDE row pins it).

**Staging rules** (from 09-RESEARCH Pattern 3/4, probed live): overlay = existing custom + candidate with `enabled` true; audit leg = candidate-only temp registry-dir with ABSOLUTE `Dataset_path` + empty env-override dir; pass = parsed artifact fields, not exit code alone.

---

### `tui/services/about.py` (service, read-only derivations)

**Analog:** `tui/services/registries.py` — tolerant reads over the pipeline registries returning plain dataclasses/tuples; every probe fails soft (missing file → neutral value), zero computation beyond counting. Keep it textual-free (import-lock test AST-walks it automatically).

---

### `tui/screens/wizard.py` (component, ModalScreen wizard family)

**Analog:** `tui/screens/selection.py` modal family, lines 612-805

**Modal shell pattern** (`PresetModal`, `selection.py:612-657`) — every Phase 8 modal: `BINDINGS` with `escape → dismiss`, constructor takes callbacks, `Vertical(id="...-box", classes="modal-box")` root, `border_title` from strings constants, `Footer()` last:
```python
class PresetModal(ModalScreen):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", APP_MODAL_BACK_LABEL),
    ]
    def compose(self) -> ComposeResult:
        with Vertical(id="preset-box", classes="modal-box"):
            ...
            yield Footer()
    def on_mount(self) -> None:
        self.query_one("#preset-box", Vertical).border_title = SEL_PRESET_TITLE
```

**Collect-all problems view** (`PathInputModal.on_input_submitted`, `selection.py:729-745`) — numbered problem lines; nothing applied on failure, modal stays open:
```python
problems = self._on_submit(value)
if problems:
    lines = [SEL_TEMPLATE_PROBLEMS.format(n=len(problems))]
    lines.extend(
        SEL_TEMPLATE_PROBLEM_LINE.format(
            n=index + 1, location=location, message=message)
        for index, (location, message) in enumerate(problems))
    self.query_one("#path-problems", Static).update("\n".join(lines))
else:
    self.dismiss()
```

**Esc-confirm gate** (`ConfirmModal`, `selection.py:748-774`) — Enter/Esc confirm for destructive actions; bindings stay `show=False` for enter. The wizard's esc-cancel-with-values branches on `self._phase` inside ONE modal (Pitfall 9) rather than pushing new screens.

**TYPE_CHECKING app narrowing** (`selection.py:813-819`):
```python
if TYPE_CHECKING:
    app = getters.app(DnallmMarkTui)
```
Required wherever the wizard needs `self.app.below_minimum_grid` (WR-06 guard check before any async chrome push).

**SelectionList single-pick enforcement + Input-eats-digits facts:** verified excerpts in 09-RESEARCH Pattern 1/2 (Pilot-proved on textual 8.2.8). Never `Binding(priority=True)` for digit keys.

---

### `tui/screens/about.py` (component, read-only screen)

**Analog:** `tui/screens/env_check.py` — screen class with `SelectionServiceProtocol`-style Protocol injection seam in `__init__`, data loaded via a worker Message (`DataLoaded`, `selection.py:834-839`), compose of Static rows, copy from strings constants. The about screen is stateless → may join the zero-arg `SCREENS` registry (D-13 slot 6); the selection screen's factory discipline stays.

---

### `tui/app.py` (MODIFY — nav shell + about wiring)

**Analog:** itself

- **SCREENS registry** (`app.py:154-156`): add `"about": AboutScreen` zero-arg slot (permitted — no live state). Selection/matrix stay factory-only (`build_selection_screen`, `app.py:188-201`).
- **Min-size guard** (`app.py:223-260`): the nav bars must not render while `MinSizeScreen` is up — plain-Screen push already hides all chrome (D-16 satisfied by existing mechanics; the guard needs no change, but any new async push must gate on `below_minimum_grid` like `action_help` at `app.py:272-274`).
- **Bottom-bar left segment:** reuse `_binding_row` (`app.py:292-309`) — per-screen BINDINGS declarations stay the single key-map source; the bar is presentational.
- **Digit nav actions:** plain per-base-screen `BINDINGS` entries (`Binding("1", "nav_env_check", NAV_LABEL_ENV)` style), never priority.

### `tui/screens/selection.py` (MODIFY — w/e keys, badge, counts)

Add to the existing `BINDINGS` list (`selection.py:821-832`) — copy the shape of `Binding("p", "apply_preset", SEL_PRESET_LABEL)`. Badge/count cells follow `_presence_cell` (`selection.py:571-595`): service decides, screen formats via `Text(value, style=...)` with theme-token styles; count-line copy from strings constants.

### `tui/strings.py` / `tui/styles.tcss` (MODIFY)

All new Chinese copy as `NAV_*`, `ABOUT_*`, `WIZ_*`, `WIZM_*`, `WIZD_*`, `GAUNTLET_*`, `SEL_*` constants — mirrors the existing constant block consumed by BINDINGS/compose (e.g. `APP_HELP_ROW.format(key=..., label=...)`, `app.py:90`). Styles: theme tokens only, no hex (the `app.py:130-133` comment is the rule).

---

### `pipeline/registry_loader.py` (MODIFY — D-09, the ONE pipeline change)

**Analog:** itself, `_load_registry` collision loop (`registry_loader.py:124-133`)

Landing point is AFTER the collision loop, replacing `registry.update(custom)`:
```python
for key in custom:
    if key in registry:
        raise SystemExit(...)   # existing collision fail-fast — unchanged
registry.update(
    {key: entry for key, entry in custom.items()
     if entry.get("enabled") is not False}   # absent/true → loaded (D-09 缺席=启用)
)
```
Only explicit literal `False` disables; official entries lack the field so the absent-overlay byte-identity contract (module docstring D-06) holds and every existing test stays green unmodified.

### `schemas/custom_registry.json` (NEW)

**Analog:** `schemas/run_template.json` — strict draft 2020-12, `additionalProperties: false`, `schema_version` const, `$id` under the repo schemas URL, provenance in `$comment` next to the governed fields (the templates.py:11-19 contract description documents the discipline). NOTE (anti-pattern, 09-RESEARCH): the schema describes the ENTRY shape only; the custom file's TOP LEVEL stays a plain `{key: entry}` map — no envelope.

---

### Tests

**Tier-1 service tests** — analog `tests/tui/test_services_templates.py`: module docstring citing pinned decisions; fixture builders (`full_valid_document()` returning a dict exercising every field); synthetic names only; parity test asserting the frozen metric constant equals `export_runs.SUITE_CANONICAL` (importable in the test lane via `tests/conftest.py` sys.path, never at TUI runtime).

**Tier-2 Pilot tests** — analog `tests/tui/test_pilot_selection.py`: async (`asyncio_mode=auto`), fake service injected via constructor seam, `await pilot.pause()` before assertions, modal push/dismiss flows, zero-Chinese-literals grep assertions extended to new screen modules (the `test_pilot_selection.py:1302` pattern). Nav-shell tests additionally cover digit keys + min-size guard interplay (the guard regression tests in `tests/tui/test_pilot_boot.py` family).

**Registry-loader tests** — analog `tests/test_registry_loader.py:57-65`:
```python
def pin_custom_dir(monkeypatch, tmp_path, name="custom"):
    custom_dir = tmp_path / name
    custom_dir.mkdir()
    monkeypatch.setenv("DNALLMMARK_CUSTOM_REGISTRY_DIR", str(custom_dir))
    return custom_dir
```
Reuse this helper for the additive enabled-skip tests AND for every gauntlet test (isolation from the real `~/.config/dnallmmark/` — this machine has one). Add the byte-unchanged regression test for committed audit artifacts (Pitfall 1).

**Import lock** — `tests/tui/test_import_lock.py:44-58` AST-walks all `tui/services/*.py` by glob: new services comply automatically and the lock stays non-vacuous; zero edits needed.

## Shared Patterns

### Services tier invariants (apply to all 4 new services)
**Source:** `tui/services/settings.py:33-35`, `templates.py:50-54`, locked by `tests/tui/test_import_lock.py`
Zero textual imports; dependencies = stdlib + platformdirs/jsonschema + `artifact_loader`; module docstring opens with the locked-decision contract; every repo-relative path resolved from `Path(__file__).resolve().parents[N]`, never CWD (`templates.py:64`).

### Tolerant JSON reads (gauntlet artifacts, custom files, about data)
**Source:** `artifact_loader.load_json_artifact` via `templates.py:227-229` — None sentinel, never raises; the pattern at `templates.load_template_file` shows the `(doc, message)` diagnostic pair.

### Subprocess discipline (both gauntlet legs)
**Source:** Phase 7 sweep/T-03-10 discipline + live probes in 09-RESEARCH Patterns 3-4 — argv LIST, `sys.executable`, absolute script path, explicit `env={**os.environ, "DNALLMMARK_CUSTOM_REGISTRY_DIR": <temp>}`, `timeout=`, `capture_output=True, text=True`; registry values never reach a shell; verdict from parsed artifacts.

### Async result integrity (run-id tagging)
**Source:** `tui/screens/env_check.py:276-433` (WR-02) — excerpt above; every gauntlet result message carries `run_id`; handlers drop mismatches.

### i18n single home
**Source:** `tui/app.py:126-128` + strings module — all new copy as constants; BINDINGS descriptions ARE the strings constants; zero-Chinese-literals grep tests extend to new modules.

### Modal safety (Pitfall 11 / WR-01 / WR-06)
**Source:** `tui/app.py:66-94, 223-274` — ModalScreen blocks base bindings; any async push checks `self.app.below_minimum_grid` first; min-size guard is a plain Screen hiding all chrome (D-16 inherits this for free).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | — | — | Every file has an in-repo analog; the only genuinely novel mechanics (staged-overlay gauntlet staging rules, audit pass-criteria parsing, wizard step composition) are fully specified with verified probes in 09-RESEARCH.md Patterns 1-4 and Code Examples — the planner should copy those skeletons directly. |

## Metadata

**Analog search scope:** `tui/` (screens, services, app, strings, styles), `pipeline/registry_loader.py`, `pipeline/run_sweep.py`, `script/audit_n_frequencies.py`, `schemas/`, `tests/`, `tests/tui/`
**Files scanned:** ~20 (targeted reads; analog excerpts verified against git-tracked source on branch `autorun`)
**Pattern extraction date:** 2026-10-12
