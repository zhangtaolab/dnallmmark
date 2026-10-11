# Phase 8: TUI Foundation (Env Check & Selection) - Pattern Map

**Mapped:** 2026-10-11
**Files analyzed:** ~20 (new `tui/` package files, `pipeline/env_smoke.py` refactor, `schemas/run_template.json`, `pyproject.toml`, `Makefile`, `tests/conftest.py`, `tests/tui/*`)
**Analogs found:** 8 strong / 8 total categories

All analog paths below are git-tracked source (verified: `pipeline/artifact_loader.py`, `pipeline/registry_loader.py`, `pipeline/env_smoke.py`, `tests/conftest.py`, `tests/test_registry_loader.py`, `Makefile`, `pyproject.toml`, `schemas/flops_report.json` all appear in `git ls-files`).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `tui/__init__.py` | config | — | `pipeline/artifact_loader.py` (module-docstring discipline) | convention |
| `tui/__main__.py` | route/entry | file-I/O | `tests/conftest.py:41-44` (sys.path bootstrap idiom) | exact idiom |
| `tui/app.py` | component (composition root) | event-driven | none (first Textual code in repo) | none — use RESEARCH.md Patterns 2/3 |
| `tui/constants.py` (strings) | config | — | `dnallm-mark/js/config.js` (single-home constants) | convention |
| `tui/screens/env_check.py` | component | event-driven | none (Textual) — RESEARCH.md Pattern 2 | none |
| `tui/screens/selection.py` | component | event-driven | none (Textual) — RESEARCH.md Pattern 3 | none |
| `tui/screens/matrix.py` | component | transform | none (Textual) | none |
| `tui/services/env_check.py` | service | file-I/O | `pipeline/env_smoke.py` + `pipeline/artifact_loader.py` | exact |
| `tui/services/env_gate.py` | service | pure | `pipeline/artifact_loader.py` (pure-function module shape) | role-match |
| `tui/services/quick_check.py` | service | pure | `pipeline/env_smoke.py` kernels | role-match |
| `tui/services/registries.py` | service | request-response | `pipeline/registry_loader.py` | exact (consumer side) |
| `tui/services/selection.py` | service | pure | `pipeline/run_sweep.py` `enumerate_matrix` | role-match |
| `tui/services/templates.py` | service | file-I/O + transform | `schemas/flops_report.json` + `jsonschema` consumers | role-match |
| `tui/services/settings.py` | service | file-I/O | `pipeline/registry_loader.py:57-81` (env-var > XDG > home override chain — mirror with platformdirs) | exact idiom |
| `pipeline/env_smoke.py` (MODIFY) | utility | file-I/O | itself; refactor shape = RESEARCH.md Pattern 1 | self |
| `schemas/run_template.json` (NEW) | config/schema | — | `schemas/flops_report.json` | exact |
| `tests/tui/test_services_*.py` | test | — | `tests/test_registry_loader.py` | exact |
| `tests/tui/test_pilot_*.py` | test | event-driven | none (first async tests) — RESEARCH.md Pattern 7 | none |
| `pyproject.toml` (MODIFY) | config | — | existing `[dependency-groups]` (data/dev/gpu) | exact |
| `Makefile` (MODIFY) | config | — | `lint:130` / `typecheck:139` / `test:89-91` + `PHASE7_MODULES:129` | exact |

## Pattern Assignments

### `tui/services/*.py` (service layer — ZERO textual imports)

**Analog:** `pipeline/artifact_loader.py` — the Phase 7 pure-module template every service file should copy structurally.

**Module-header contract pattern** (`pipeline/artifact_loader.py:1-22`): large module docstring stating phase/decision provenance, a `Contract` bullet list of locked decisions (D-numbers), explicit "zero dependencies beyond stdlib" lane statement. Services replace the last line with "imports only `pipeline/env_smoke`, `pipeline/registry_loader`, `pipeline/artifact_loader`, `platformdirs` — never `textual`".

**Docstring style** (`pipeline/artifact_loader.py:28-37`):
```python
def load_json_artifact(path):
    """Tolerantly read a JSON artifact from disk.

    Args:
        path: the file to read (str or os.PathLike).

    Returns:
        The parsed JSON document (dict, list, or scalar), or None when the
        file is missing, unreadable, empty, truncated, or not valid JSON.
    """
```

**Tolerant-read discipline** (`pipeline/artifact_loader.py:38-45`) — every JSON read in services (state file, n_audit.json, templates at rest, saved presets) goes through `artifact_loader.load_json_artifact`, never a bare `json.load`:
```python
try:
    text = Path(path).read_text(encoding="utf-8")
except (OSError, UnicodeDecodeError):
    return None
try:
    return json.loads(text)
except json.JSONDecodeError:
    return None
```

### `tui/services/settings.py`

**Analog idiom:** `pipeline/registry_loader.py:57-81` — the env-var whole-dir override chain. Mirror exactly, with platformdirs as the base resolver (D-10: do NOT modify the pipeline-side original):
```python
override = os.environ.get("DNALLMMARK_CUSTOM_REGISTRY_DIR")
if override:
    return Path(override)
xdg = os.environ.get("XDG_CONFIG_HOME")
if xdg:
    return Path(xdg) / "dnallmmark"
return Path.home() / ".config" / "dnallmmark"
```
TUI shape: two whole-dir vars (recommended `DNALLMMARK_TUI_STATE_DIR` + `DNALLMMARK_TUI_CONFIG_DIR`, RESEARCH Open Question 1) overriding `platformdirs.user_state_dir("dnallmmark")` / `user_config_dir("dnallmmark")`. Empty value = unset (registry_loader precedent). Atomic writes: tmp + `os.replace`.

### `tui/__main__.py` + test import bootstrap

**Analog:** `tests/conftest.py:40-44`:
```python
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "script"))   # summarize_comparison, export_runs, freeze_snapshot
sys.path.insert(0, str(REPO_ROOT / "baseline")) # compare (walk) for reuse
sys.path.insert(0, str(REPO_ROOT / "pipeline")) # run_sweep (stdlib-only sweep driver)
```
`tui/__main__.py` computes `REPO_ROOT` from `__file__` (never CWD) and inserts `REPO_ROOT / "pipeline"` before importing `env_smoke`/`registry_loader`/`artifact_loader` (pipeline/ has no `__init__.py). Tests need ONE added line — either root-conftest `sys.path.insert(0, str(REPO_ROOT))` or a `tests/tui/conftest.py` — so `import tui` resolves (RESEARCH Pitfall 4).

### `pipeline/env_smoke.py` (MODIFY — D-02 structured-return refactor)

**Analog:** itself. The refactor must keep, byte-identical:
- `main()` at `pipeline/env_smoke.py:411-444` — result-list order: `check_version_pins(pins)`, `check_dnallm()`, literal line `results.append(check_peft())` (line 418, grep-locked by `tests/test_run_finetune_contracts.py:1593-1657`), torch-import gate with the two-`False` append + `FAIL: torch unavailable — CUDA + matmul checks not run` line (428-434), `check_numpy(...)` (435), non-gating `print_ecosystem_diagnostics()` (436), `check_dataset_dirs()` (437), trailer lines (439-444).
- Kernel print-line formats, e.g. `check_numpy` at :186-197, `import_or_fail` at :240-248 (`PASS: import {module_name} resolves ({origin})`), `check_version_pins` at :261-276 (iterates `sorted(pins)`), `check_dataset_dirs` at :353-383 (double-nested note format).
- Module docstring sanction block and version labels (grep tests 1-2 pin `"1.2.1"`, `"datasets<=5.1.0"`, `"2026-10-11"`/`"sanction"`/`"bounded"`/`"dual gate"`/`"GPU-free"` within first 4200 chars).
- Target shape: kernels return `CheckResult(name, ok, lines)` and stop printing; `main()` renders lines (RESEARCH Pattern 1 renderer approach + golden byte-stability test under `capsys` + monkeypatched `import_module`).

### `schemas/run_template.json`

**Analog:** `schemas/flops_report.json:1-23` — copy verbatim discipline:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://raw.githubusercontent.com/zhangtaolab/dnallmmark/main/schemas/run_template.json",
  "$comment": "Strict contract (one-way, D-07) for ... consumed by the Phase 11 run-config screen ...",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", ...],
  "properties": {
    "schema_version": { "const": 1 },
    ...
  }
}
```
`additionalProperties: false` everywhere, `schema_version: {"const": 1}`, long `$comment` recording decision provenance and the GA semantics (`GA = max(1, effective_batch // batch_size)`, maintainer default 16).

### `tests/tui/test_services_*.py`

**Analog:** `tests/test_registry_loader.py:1-65` — copy the structure:
- Module docstring listing pinned locked-decisions as bullets with D-numbers.
- `import registry_loader  # conftest puts pipeline/ on sys.path` comment style for imports.
- Helper-fixture pattern: `pin_custom_dir(monkeypatch, tmp_path, name)` (:57-65) — monkeypatch env var to a `tmp_path` dir so tests are machine-independent. Reuse this shape for `DNALLMMARK_TUI_STATE_DIR`/`_CONFIG_DIR` injection and for fake-kernel injection (tier-1 CI tests never run real GPU kernels — D-03).
- Small synthetic registries built inline (`make_official_registry`, :68-80).
- Plus the 5-line services-textual-free import lock (walk `tui/services/*.py`, assert no `textual` import — Phase 7 absence-lock discipline).

### `pyproject.toml` (MODIFY)

**Analog:** existing groups at `pyproject.toml:10-36` — each group carries inline `#` comments citing phase/decision/date. Add with the same comment discipline:
```toml
tui = [
    "textual>=8.2,<9",
    "platformdirs>=3.6,<5",
]
```
dev group gains `"pytest-asyncio>=1.4,<2"` (:19-29). `[tool.pytest.ini_options]` (:74-86) gains `asyncio_mode = "auto"` with a dated comment. `[tool.ty.src] include` (:72) gains `"tui"`; `[tool.ty.environment] extra-paths` (:61) gains `"tui"` (mirroring the conftest contract comment already there). `replace-imports-with-any` list (:64) untouched — textual ships py.typed.

### `Makefile` (MODIFY)

**Analog:** `Makefile:124-131` — the existence-guard idiom, copied exactly:
```makefile
PHASE7_MODULES := $(foreach s,pipeline/flops_counter.py pipeline/registry_loader.py pipeline/artifact_loader.py,$(if $(wildcard $(s)),$(s)))
```
Add `PHASE8_TUI := $(foreach s,$(wildcard tui/*.py tui/screens/*.py tui/services/*.py),$(s))` and append `$(PHASE8_TUI)` to the `lint:` file list (:131). `test:` recipe (:89-91) gains `--group tui`:
```makefile
test: check-node
	$(UV) run --group dev --group tui pytest
	node --test tests/js/*.test.js
```
New target mirroring `typecheck:139-141` style:
```makefile
tui:
	$(UV) run --group tui --group gpu python -m tui
```
Zero CI workflow edits (test job already runs `make test`).

### `tui/app.py`, `tui/screens/*.py`, `tests/tui/test_pilot_*.py`

No repo analog (first Textual code). Use RESEARCH.md Patterns 2 (thread worker + nested `Message`), 3 (DataTable + `coordinate_to_cell_key` mark-set, `update_cell`), 7 (Pilot: `async with app.run_test(size=(120, 40))`, `await pilot.pause()` before assertions, constructor-injected fake services) — full sketches with imports are in `08-RESEARCH.md` §Architecture Patterns. Follow `dnallm-mark/js/` class-per-entrypoint + `constants` single-home conventions for structure; Python style follows the `artifact_loader.py` docstring/`# =====` banner conventions.

## Shared Patterns

### Import boundary (tui → pipeline, one direction)
**Source:** `pipeline/artifact_loader.py:5-7`, `pipeline/registry_loader.py` — services import `env_smoke`, `registry_loader`, `artifact_loader` as top-level modules (pipeline/ on sys.path, not a package). Never re-implement registry/presence/tier logic in `tui/`.

### Env-var whole-dir test injection
**Source:** `pipeline/registry_loader.py:75-81` + `tests/test_registry_loader.py:57-65`
**Apply to:** `tui/services/settings.py`, every tier-1/tier-2 test that touches XDG paths. monkeypatch.setenv to tmp_path; empty value treated as unset.

### Fail-loud vs tolerant-read split
**Source:** `pipeline/registry_loader.py:110-117` (malformed custom file → `SystemExit` naming the file) vs `pipeline/artifact_loader.py:38-45` (corrupt artifact → None sentinel).
**Apply to:** template import = jsonschema strict + collect-all failure list (fail-fast, like `_validate_filters` discipline); state file read = tolerant (None → treat as no cache).

### Module docstring contract blocks
**Source:** `pipeline/artifact_loader.py:1-22`, `tests/test_registry_loader.py:1-34`
**Apply to:** every new file in `tui/` and `tests/tui/` — phase + D-number provenance, Google-style `Args:/Returns:`, `# =====` section banners, bilingual EN/zh acceptable.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `tui/app.py` | composition root | event-driven | first Textual code in repo |
| `tui/screens/env_check.py`, `selection.py`, `matrix.py` | components | event-driven | first Textual code in repo |
| `tests/tui/test_pilot_*.py` | test | event-driven | first async/Pilot tests |

For all four, planner should inline the verified sketches from `08-RESEARCH.md` §Patterns 2, 3, 7 (they include exact Textual import paths and API calls verified against official docs).

## Metadata

**Analog search scope:** `pipeline/`, `tests/`, `schemas/`, `Makefile`, `pyproject.toml`, `dnallm-mark/js/`
**Files scanned:** ~14 (all analogs read directly this session)
**Pattern extraction date:** 2026-10-11
