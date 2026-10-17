# Stack Research — v1.2 TUI Console

**Domain:** Terminal UI (TUI) operator console for a DNA-LLM benchmark platform — subprocess-driven training launches, output streaming, filesystem polling, ModelScope downloads
**Researched:** 2026-10-11
**Confidence:** HIGH for versions/footprint facts (every version verified against the PyPI JSON API and the Textual v8.2.8 source tree/tag on the research date — no version from training data), MEDIUM for practice-level recommendations (tagged individually)

**Repo facts this stack is fitted to** (from PROJECT.md / pyproject.toml / Makefile / ci.yml, not re-researched): Python `>=3.13` floor with a 3.14 CI probe leg; uv virtual project (`package = false`, PEP 735 groups `data`/`dev`/`gpu`, `default-groups = ["data"]`); ruff + ty double gate (ty 0.0.86 current, repo floor `>=0.0.85`); pytest 9.1.1 with `slow`/`ci` markers; CI is CPU-only and must stay GPU/dnallm-free with TUI tests running "CPU-side with injectable seams"; `rich`, `markdown-it-py`, `pygments`, and `pyyaml` are **already present in uv.lock** as transitive deps (rich via typer, pyyaml via datasets/huggingface-hub/transformers); the TUI drives the already-validated `run_finetune.py` / `run_sweep.py` / `env_smoke.py` CLIs and the ModelScope SDK 1.34 validated in the gpu env.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Textual** | **8.2.8** (2026-06-30) — pin `>=8.2,<9` | The TUI framework: App/Widget DOM model, TSS CSS, DataTable/RichLog/SelectionList widgets, workers, headless test driver | The only pure-Python full-screen TUI framework with a first-class testing story. Wheel is `py3-none-any` (verified on PyPI) — zero build step, zero compiled deps; runtime deps are markdown-it-py + mdit-py-plugins + platformdirs + pygments + rich + typing-extensions, and **rich/pygments/markdown-it-py are already in uv.lock**, so the real install delta is ~2 pure-Python packages. App/Widget + CSS matches the repo's existing page-controller + CSS-custom-properties mental model. Strict SemVer discipline (below) makes the `<9` cap safe and upgrades legible. **Confidence: HIGH** |
| **pytest-asyncio** | **1.4.0** (2026-05-26) — pin `>=1.4,<2` in the `dev` group | Runs `App.run_test()` async tests under the existing pytest 9.1.1 suite | Textual's `run_test()` is an async context manager; it needs an async pytest plugin. pytest-asyncio 1.4.0 requires `pytest<10,>=8.4` (verified on PyPI) — compatible with the repo's pytest 9.1.1. Set `asyncio_mode = "auto"` in `[tool.pytest.ini_options]` so async TUI tests need no per-test decorator and existing sync tests are unaffected (auto mode only touches `async def` tests). **Confidence: HIGH** |
| **platformdirs** | 4.13.0 (2026-10-11) — pin `>=3.6,<5` | `~/.config/dnallmmark/` session/filter/config persistence location (TUI-REQUIREMENTS §4) | It is already a transitive dependency of textual (`platformdirs<5,>=3.6.0` in textual's requires_dist, verified) — declaring it explicitly in the `[tui]` group costs nothing new and stops the anti-pattern of importing a transitive dep without declaring it. Handles XDG/Windows/macOS precedence correctly so the requirements doc's `~/.config/dnallmmark/?` question gets a standards answer. **Confidence: HIGH** |
| **JSON (stdlib `json`)** | stdlib | Run-config template import/export, session state, download queue persistence | The requirements specify templates as **JSON** files (§3.1 模板导入) and the repo's entire data contract is JSON with `ensure_ascii=False` conventions. Zero deps, diff-friendly, validated by the existing `jsonschema` test pattern if a template schema is wanted. **Confidence: HIGH (process judgment)** |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **PyYAML** | 6.0.3 (2025-09-29) | Reading/editing `finetune_config.yaml` / `finetune_config_with_head.yaml` from the TUI | **Only if a phase actually parses or edits YAML.** Already in uv.lock transitively (datasets, huggingface-hub, transformers depend on it), so adding `pyyaml>=6.0.2` to `[tui]` changes nothing in the install. cp313/cp314 wheels exist (verified). Maintenance is slow-but-alive (6.0.3 Sep 2025; packaged by Debian/Fedora/FreeBSD) — Snyk labels it "Inactive", which is acceptable for a load-only use. **Do not add pre-need.** |
| **textual-dev** | 1.8.0 (2025-10-11) | `textual console` devtools + `textual run --dev` hot-reload for CSS/widget iteration | **Never in a committed group.** Use on demand: `uv run --group tui --with textual-dev==1.8.0 textual run --dev python tui/main.py`. It drags aiohttp + click + msgpack + textual-serve; committing it to `dev` would bloat every CI lane for a maintainer-only convenience. **Confidence: HIGH (footprint verified on PyPI)** |
| **anyio** | 4.15.1 | Alternative async pytest plugin (built-in plugin, no extra package if already present) | Only if pytest-asyncio clashes with the existing suite in practice — it shouldn't. One plugin, not both. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `App.run_test()` + `Pilot` | Headless behavioral tests of screens/widgets | `async with app.run_test(size=(120, 40)) as pilot:` → `pilot.press(...)`, `pilot.click("#selector")`, `await pilot.pause()` to drain the message queue before asserting. `headless=True` is the default — no terminal, no display, CI-safe (official testing guide, verified 2026-10-11). |
| `# ty: ignore[rule]` | Per-line suppression for ty edge cases | Documented ty escape hatch (ty docs FAQ). Expected use: near-zero; Textual ships `py.typed` (verified present at the v8.2.8 tag) so ty reads real types — unlike torch/dnallm, **no `replace-imports-with-any` entry is needed for textual**. |
| `uv run --with textual-dev==…` | Ephemeral devtools without group pollution | The uv-native way to keep heavy dev conveniences out of CI (see above). |

## Installation

Proposed `pyproject.toml` delta (surgical — one new group, one dev-group addition, three config lines):

```toml
[dependency-groups]
# ... existing data / dev / gpu unchanged ...
tui = [
    # Textual 8.2.8 (2026-06-30): pure-python wheel, no build step; <9 cap because
    # Textual bumps major on ANY breaking change (strict SemVer — see research).
    "textual>=8.2,<9",
    # Already a textual transitive dep; declared because the TUI imports it
    # directly for ~/.config/dnallmmark (do not rely on transitive luck).
    "platformdirs>=3.6,<5",
]
# dev group gains exactly one line:
#   "pytest-asyncio>=1.4,<2",   # run_test() is async; pytest<10,>=8.4 ✓ with 9.1.1

[tool.pytest.ini_options]
asyncio_mode = "auto"   # async TUI tests need no decorator; sync tests unaffected

# [tool.ty.src] include gains "tui"; [tool.ty.environment] extra-paths gains "tui"
# (mirrors the pipeline/ contract). modelscope.** joins replace-imports-with-any
# ONLY if the TUI imports the SDK directly instead of shelling to its CLI.
```

```bash
# Operator launch (GB10 gpu box): data (default) + tui + gpu all present
uv run --group tui --group gpu python -m tui

# CPU-side iteration (no gpu group)
uv run --group tui python -m tui

# TUI tests (CPU, headless — injectable seams for launch/download)
uv run --group dev --group tui pytest tests/tui

# Devtools on demand (never committed to a group)
uv run --group tui --with textual-dev==1.8.0 textual run --dev python tui/main.py
```

**Makefile integration** (the existing pattern, extended):

- `make tui` → `$(UV) run --group tui --group gpu python -m tui` (operator entry; `--group gpu` optional for dry-run/data-management sessions)
- `make test` recipe becomes `$(UV) run --group dev --group tui pytest` — textual is pure-Python, installs in seconds, and the constraint "CI 不引入 GPU/TUI 运行时" is satisfied because `run_test()` is headless and GPU/dnallm/modelscope never enter the test path (seams)
- `make lint` file list gains `tui/` files; `make typecheck` picks up `tui/` via `[tool.ty.src]` — both gates stay green by construction, no new tools
- CI workflow (`ci.yml`) needs **zero new jobs** — `make lint`/`make typecheck`/`make test` already define the lanes; the `--group tui` addition rides along

**Code layout** (repo convention — flat top-level packages, not src/): `tui/` package with `__main__.py`, `tui/app.py`, `tui/screens/`, `tui/css/app.tcss`, tests in `tests/tui/`. Loading `tui/` on `python -m tui` mirrors how `pipeline/` scripts are invoked.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Textual 8.2.8 | **rich alone** (Rich Live + manual key handling) | Never for this milestone — rich has no widget system, no CSS, no test driver; a 62×50 selection matrix + cell dashboard + log tailing is exactly what rich-only apps drown in. rich still gets used *through* Textual (it is textual's rendering engine). |
| Textual | **urwid** | Only under a hard C-extension-free + async-free constraint that doesn't apply. urwid's design predates asyncio, its widget set is thinner, docs/testing story weaker, and development is community-speed. Nothing here urwid does better. |
| Textual | **prompt_toolkit** | If the deliverable were a wizard/REPL rather than a full-screen dashboard. The monitoring requirement (cell grid + live log tail + failure list) rules it out. |
| Textual | **curses/stdlib** | Zero-dep but hand-rolls everything (color, input decoding, layout) — hundreds of lines of platform quirks to re-derive; contradicts reviewability goals. |
| Polling loop (`asyncio.sleep` + re-read artifacts) | **watchfiles / Textual Watcher** | Not an option: Textual 8.x **has no file-watching API** (verified — no watcher module in the v8.2.8 source tree; `watchfiles` absent from requires_dist). If inotify-grade latency were ever needed, watchfiles 1.3.0 ships prebuilt abi3 wheels (no build step on install) — but Rust-compiled, so it violates the pure-Python spirit for no real gain over 1–2 s polling. |
| pytest-asyncio | **anyio pytest plugin** | If the suite ever standardizes on anyio (it doesn't — no trio/anyio anywhere in the repo). |
| JSON persistence | **ruamel.yaml** (0.19.1, pure-python wheel, active) | Only if a phase must edit YAML **preserving comments/formatting** (round-trip). Surgical scope says: don't edit training YAML from the TUI — pass CLI flags to the validated entry points instead. |
| Direct ModelScope SDK import in TUI | **`modelscope` CLI as subprocess** (same pattern as training launches) | Prefer the subprocess/CLI seam by default: it keeps the TUI CPU-testable (constraint: injectable seams), keeps `modelscope` out of CPU-side groups, and the CLI (`modelscope download --dataset X`) is already validated at 50/50 coverage. Import the SDK directly only inside the gpu-env run if progress-callback granularity demands it — then add `modelscope.**` to ty's `replace-imports-with-any` (exact pattern already used for torch/dnallm). |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **textual-serve / textual-dev in committed groups** | Web-serving the TUI (open question 5, "可要可不要") drags aiohttp+jinja2 into every sync; textual-dev drags aiohttp+click+msgpack+textual-serve into CI lanes for a maintainer-only tool | `uv run --with textual-dev==1.8.0 …` on demand; revisit textual-serve only if the team answers Q5 "yes" |
| **pytest-textual-snapshot** (1.1.0) | SVG golden snapshots pin `syrupy==4.8.0` + jinja2 and are invalidated by textual version bumps — churn generator in a milestone whose gate discipline is "zero-diagnostics baseline". Last release 2025-01-23 (slow-moving). | Pilot behavioral assertions (`pilot.press`/`click` + query widget state); add snapshots post-v1.2 only if visual regressions hurt |
| **Any JS/Node tooling for the TUI** | Hard repo constraint (no build step, vanilla ES modules) — and nothing is needed | Textual's own TSS CSS |
| **Blocking `subprocess.Popen` reads on the event loop** | Output batches up and the UI freezes (Textualize discussion #3788) — the single most common Textual+subprocess mistake | `@work` async worker + `asyncio.create_subprocess_exec(..., stdout=PIPE, stderr=STDOUT)` + `readline()` loop into `RichLog` |
| **`textual` in the `data` or default groups** | `default-groups = ["data"]` means every `uv sync`/CI lane would carry the TUI runtime; the data chain must stay untouched (reproducibility substrate) | Dedicated `[tui]` group, added explicitly where needed |
| **Relying on Textual for filesystem watching** | The API does not exist in 8.x (verified) — code written against old docs/blogs (`watch_path`, `Watcher`, watchfiles) will not even import | `set_interval`/async worker polling of `sweep_failures.json`, `trainer_state.json`, directory mtimes |
| **Capturing business logic in the TUI** | An operator console that re-implements selection/sweep/audit logic forks the truth and becomes untestable in CI | TUI = thin launcher/monitor: subprocess the CLIs, render the JSON artifacts they already emit |

## Stack Patterns by Variant

**If a run must keep streaming while the TUI exits** (long E2' cells survive operator disconnect):
- Launch training via `nohup`-style detach or a supervisor script the TUI *starts and monitors* rather than *owns*
- Because Textual cancels its workers on app exit — a subprocess started inside a worker is killed unless you `proc.detach()`/ignore SIGHUP explicitly; decide the ownership semantic per phase (monitor-only resume already exists via `trainer_state.json` skip logic)

**If tmux is the primary operator environment** (it is, for SSH GPU boxes):
- Document the two rules up front: scrollback lives in tmux copy-mode (`prefix+[`) because the app owns the alternate screen + mouse; hold **Shift** for native terminal selection/copy
- Known open bug Textualize/textual#6668 (against 8.2.8, Linux): after tmux detach/reattach or SSH reconnect, lost SGR mouse negotiation can crash with `UnicodeDecodeError` once the mouse crosses ~column 95 — operational guidance "restart the TUI after reattach" until upstream fixes it; keeping the TUI monitor-only-and-resumable (above) makes that cheap

**If Windows Terminal operators appear** (currently Linux/GB10 only):
- Textual's supported terminal matrix includes Windows Terminal (ecosystem-standard claim, **MEDIUM confidence — re-verify against the official FAQ if Windows becomes real**); legacy `conhost` is the known-poor path. tmux guidance is moot there.

**If the download queue needs resume-after-restart** (open question 4: "需要"):
- Persist the queue as JSON under the platformdirs config dir; reconcile against on-disk presence (`n_audit` row counts) at TUI startup — pure stdlib, no new deps

## Version Compatibility

| Component | Compatible With | Notes |
|-----------|-----------------|-------|
| textual 8.2.8 | Python 3.9–3.14 | `requires_python <4.0,>=3.9` (PyPI); 3.14 support added in 6.3.0 (2025-10-11, CHANGELOG PR #6121). Repo floor 3.13 ✓, CI 3.14 probe leg ✓ |
| textual ↔ rich 15.0.0 | ✓ (needs `rich>=14.2.0`) | rich 15.0.0 (2026-04-12) is pure-python, already locked via typer |
| pytest-asyncio 1.4.0 | pytest `>=8.4,<10` | Repo pins pytest 9.1.1 ✓; Python >=3.10 ✓ |
| pyyaml 6.0.3 (if added) | cp313/cp314 wheels verified | Already in uv.lock transitively — zero resolution change |
| ty 0.0.86 (2026-10-09) | textual's `py.typed` | Verified py.typed exists at tag v8.2.8 — ty sees real Textual types; **no** `replace-imports-with-any` entry needed for textual. No Textual-specific ty issues surfaced (searched astral-sh/ty — **negative claim, MEDIUM**: absence of evidence; per-line `# ty: ignore[rule]` is the escape hatch) |
| GitHub Actions lanes | unchanged | No new actions, no new jobs; `--group tui` rides existing `make` targets; textual adds seconds of pure-python install, well inside the 14-min job ceilings |

### Textual version-cadence fact the roadmap must plan around

Strict SemVer: **any** breaking change bumps the major, and majors are frequently tiny — 7.0.0 was "much smaller change than the version number may suggest"; 8.0.0's breaking change was a `Select.BLANK`→`Select.NULL` rename. Eight majors since 1.0.0 (2024-12-12): 2.0 Feb 2025, 3.0 Mar 2025, 4.0 Jul 2025, 5.0 Jul 2025, 6.0 Aug 2025, 7.0 Jan 2026, 8.0 Feb 2026; patches roughly biweekly (8.2.3→8.2.8 spanned Apr–Jun 2026; no release since 2026-06-30 as of research date). Practical discipline for this repo: cap `<9`, upgrade deliberately via `uv lock --upgrade-package textual` with a CHANGELOG scan, and never let dependabot-style auto-bumps cross a major. **Confidence: HIGH** (CHANGELOG + PyPI, both fetched 2026-10-11).

### The three load-bearing API facts (verified, current)

1. **Workers** (official guide): `run_worker(...)` / `@work(exclusive=True)` for async work; `thread=True` + `call_from_thread()`/`post_message()` + `is_cancelled` polling for blocking code (the ModelScope SDK is blocking — run it in a thread worker or behind the CLI subprocess seam). Workers auto-cancel when their widget/screen is removed or the app exits.
2. **Subprocess streaming** (official discussion #3788 + multiple production apps): `await asyncio.create_subprocess_exec(..., stdout=PIPE, stderr=STDOUT)` → `readline()` loop → `RichLog.write()` → `await proc.wait()`. Never `communicate()` (buffers everything).
3. **No filesystem watching in 8.x** (verified against source): poll `sweep_failures.json` / `trainer_state.json` / mtimes on an interval. This *answers TUI-REQUIREMENTS open question 2*: polling vs in-process callbacks — polling is not the compromise, it is the only mechanism, and it is also the correct one for cross-process truth (the sweep is a separate process).

## Sources

- PyPI JSON API (pypi.org/pypi/{textual,rich,textual-dev,textual-serve,pytest-asyncio,pytest-textual-snapshot,pyyaml,ruamel-yaml,platformdirs,watchfiles,anyio,ty}/json) — versions, release dates, requires_python, requires_dist, wheel purity; fetched 2026-10-11 — **HIGH (primary registry)**
- Textual CHANGELOG at tag v8.2.8 (raw.githubusercontent.com/Textualize/textual/v8.2.8/CHANGELOG.md) — major-version history/breaking changes, Python 3.14 support (6.3.0), 8.0.0 contents — **HIGH (official)**
- Textual v8.2.8 source tree (GitHub tree API + raw file fetches) — no watcher module / no `watch_path`; `py.typed` present; `run_test()` signature in app.py — **HIGH (primary source)**
- Textual official guides — /guide/workers/, /guide/testing/, /guide/CSS/ (HTTP 200 + content fetched 2026-10-11); widget docs /widgets/{data_table,rich_log,selection_list,tabbed_content,progress_bar,log}/ all current — **HIGH (official docs)**
- Textualize/textual discussion #3788 (RichLog streaming; blocking-Popen pitfall) — **HIGH (official maintainers)**
- Textualize/textual issue #6668 (open, 8.2.8, Linux): UnicodeDecodeError after terminal rebuild / X10 mouse fallback under tmux reattach — **HIGH (verified open 2026-10-11)**
- astral-sh/ty issues search — no Textual-specific false positives found — **MEDIUM (negative claim)**
- PyYAML maintenance signal: Snyk "Inactive" label vs 6.0.3 distro adoption (Debian/Fedora/FreeBSD packaging news) — **MEDIUM**
- uv.lock / pyproject.toml / Makefile / .github/workflows/ci.yml — integration surface facts — **HIGH (repo)**

---
*Stack research for: DNALLM-Mark v1.2 TUI console*
*Researched: 2026-10-11*
