# Pitfalls Research

**Domain:** Adding a Textual TUI operator console to an existing subprocess-driven benchmark platform (dnallmmark v1.2)
**Researched:** 2026-10-11
**Confidence:** MEDIUM (community + official-docs cross-checked; no single authoritative "Textual integration post-mortem" corpus exists — findings triangulated from official guides/API docs, Textualize GitHub issues/discussions, and real Textual wrapper projects)

**Context anchors (verified in this repo):** `pipeline/run_sweep.py` launches cells via blocking `subprocess.run(argv, check=True)` with **uncaptured** child stdout, cwd pinned to `PIPELINE_DIR` (`run_sweep.py:860-876`); `sweep_failures.json` is deleted at sweep start (WR-06, `run_sweep.py:1024-1027`); `run_record.json` is never rewritten (WR-12) but is written **non-atomically** (`_write_json` = `open("w")` + `json.dump`, no tmp+rename, `run_sweep.py:899-902`); the `trainer_state.json` resume marker is written LAST per cell (WR-13, `run_finetune.py:1487-1489`); CI is CPU-only, ruff+ty gated, 14-min timeout, matrix 3.13/3.14 (`.github/workflows/ci.yml`); dependency groups are `data` (default), `dev`, `gpu` (`pyproject.toml`). Textual current release: **8.2.8**, pure-Python deps, `requires-python >=3.9,<4.0` (3.13 fine).

**Milestone phase skeleton used below** (per `docs/TUI-REQUIREMENTS.md` §6): P1 TUI foundation → P2 data manager (downloads) → P3 single-GPU launch + monitoring → P4 multi-GPU orchestration (hard-gated on P3). FlopsCounter port lands as its own work package before P3.

---

## Critical Pitfalls

### Pitfall 1: Blocking the Textual event loop with sync subprocess/SDK calls

**What goes wrong:**
The UI freezes mid-interaction. Every symptom of a "laggy" or "hung" TUI: keys echo seconds late, clicks queue up and replay in a burst, the spinner stops, and long output appears "all at once" at the end instead of streaming. In the worst case the operator concludes the sweep hung and kills it.

**Why it happens:**
`run_sweep.py`'s default executor is blocking (`subprocess.run(..., check=True)`, cells run for minutes-to-hours). The ModelScope download SDK is synchronous. `env_smoke.py` runs imports of torch/dnallm (seconds). Any of these called directly inside a Textual message handler (`on_button_pressed`, `on_input_changed`, `on_mount`) stops the event loop, because a single-threaded asyncio app can't repaint or process input while the handler runs. Official Textual docs name the symptom explicitly: "a noticeable delay between pressing a key and seeing it echoed on screen," and prescribe the worker discipline for anything over "a few milliseconds." Textualize discussion #3788 documents the exact "output appears all at once" failure for blocking `Popen` reads.

**How to avoid:**
- **Never import-and-call the sweep executor in-process.** The TUI always spawns `python pipeline/run_sweep.py ...` itself via `asyncio.create_subprocess_exec` (argv LIST, never `shell=True` — repo rule T-03-10) and reads `proc.stdout.readline()` inside an async worker. This one decision removes hours-long blocking by construction and keeps the GPU stack out of the TUI process.
- Wrap every blocking call that cannot be subprocessed (ModelScope SDK download, big JSON reads of 62-model registries) in a **thread worker**: `@work(thread=True, exclusive=True)`. Touch the UI from the thread only via `self.post_message(...)` (thread-safe) or `App.call_from_thread` — never set reactives or call widget methods directly from the worker thread.
- Use `exclusive=True` on workers that serve one slot (one download stream, one sweep supervisor, one log tail per cell) so re-triggering cancels the stale worker instead of stacking them — this is also the official fix for out-of-order results (e.g. a slow read for cell A landing after cell B's).
- Prefer handling `on_worker_state_changed` over `await worker.wait()` inside handlers (the await blocks the UI); set `exit_on_error=False` on workers whose failures must surface as a UI error state, not an app-killing traceback.

**Warning signs:**
- Any `await` or sync call in a handler that takes >100 ms in manual testing (key-echo lag is the canary).
- A `RichLog` that fills in one dump at process end rather than streaming.
- Code review: `subprocess.run`/`requests`/`modelscope` appearing inside an `on_*` handler or `watch_*` method.

**Phase to address:** P1 (foundation) — the worker/subprocess discipline is the first architectural decision; it is nearly impossible to retrofit once handlers are full of sync calls.

---

### Pitfall 2: Losing subprocess output — uncaptured children, teardown, and resize

**What goes wrong:**
Three related failure modes. (a) **Terminal corruption:** the sweep child inherits the TUI's stdout/stderr (that is what `subprocess.run` without capture does today), so thousands of lines of training output paint straight over the alternate-screen buffer — the display becomes garbage. (b) **Output lost on teardown:** the operator quits the TUI (or SSH drops) and the reader tasks die; if the child was killed too, a half-finished cell has neither a live viewer nor a durable log. (c) **Output lost around resize:** uncaptured/piped-but-unread buffers plus a mid-flight resize leave the log view and the artifact on disk disagreeing about what happened.

**Why it happens:**
`launch_subprocess` today deliberately lets the child write to the parent's terminal — correct for CLI usage, catastrophic when the parent is a full-screen TUI. Community Textual wrapper projects (textual-shell, terraform-tui, terok) all converge on the same fix: PIPE + reader worker + `proc.terminate()` cleanup, because there is no official one-page recipe and the default (inherit) is the trap.

**How to avoid:**
- Spawn the sweep with `stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT` (merged; run_finetune's error log file remains the durable per-model record on disk).
- **Tee, don't just tail:** every line read by the worker goes both to a per-sweep log file on disk (append) and to the `RichLog` widget. The file is the source of truth; the widget is a view. Then TUI death, SSH drop, or resize can never destroy the record.
- **Bound the widget:** construct `RichLog(max_lines=N)` (e.g. 10k) — an hours-long, 3-seed sweep emits far more than any terminal view should hold in memory.
- Detach the sweep's lifetime from the TUI's: start it with `start_new_session=True` (its own process group) so quitting the TUI or an SSH hiccup does not SIGHUP a 40-minute cell. The TUI then *supervises* (poll + log tail) rather than *is* the sweep. Explicit "stop sweep" action sends SIGTERM to the group, with a confirmation modal (an accidental Ctrl+C must not equal killing a GPU run).
- In `on_unmount` (or the screen's teardown): cancel reader tasks, then terminate the child — but only the child the TUI owns as a foreground choice; detached sweeps are left running by design and shown as such on reattach.

**Warning signs:**
- Garbage on screen the first time a real cell runs (always test with one tiny smoke cell before wiring all 50 datasets).
- `RichLog` memory growing monotonically in a long session (watch RSS).
- A "quit TUI" that also silently kills the sweep (operator discovers runs died overnight).

**Phase to address:** P3 (single-GPU launch + monitoring). The tee-to-file and detach decisions define the launch architecture; P1 only needs to not preclude them (keep the log-tail widget a leaf component).

---

### Pitfall 3: Terminal matrix failures — SSH, tmux, mouse mode, colors, escape leaks

**What goes wrong:**
The GB10 box is SSH-only, so every operator runs the TUI through at least one multiplexer. Documented failure modes in exactly this stack:
- **Scrollback appears dead:** a full-screen TUI enables mouse reporting, so wheel events go to the app instead of tmux/terminal scrollback. Users perceive "the TUI ate my scrollback."
- **Crash on tmux detach/reattach or SSH reconnect:** Textual issue #6668 — when the terminal is rebuilt under a live app, SGR mouse negotiation (`?1006`) is dropped and the terminal falls back to legacy X10 encoding; X10 reports with coordinates past column ~95 produce bytes >0x7F, and the strict UTF-8 stdin decoder raises `UnicodeDecodeError`. Reattach mid-sweep is precisely when this fires.
- **256-color degradation:** colors picked on a truecolor local terminal become wrong/muddy when `TERM=xterm-256color` over SSH (or inside tmux without RGB overrides). Status semantics that live only in color (red=fail) silently lose meaning.
- **Escape-sequence leaks:** a hard crash (or a subprocess writing raw bytes mid-alt-screen) can leave the operator's shell with a hidden cursor, weird keybindings, or mouse mode stuck on after exit.

**Why it happens:**
Terminal capabilities are negotiated state, not constants; SSH + tmux chains renegotiate on detach/reattach and drop capabilities the app assumed. Textual restores the terminal on clean exit, but not on SIGKILL or a mid-screen subprocess write.

**How to avoid:**
- Make **tmux the blessed operating environment** (it also solves Pitfall 2's SSH-drop case) and document the operator setup once: `mouse on`, generous `history-limit`, `allow-passthrough on`, truecolor via `terminal-features ",*:RGB"` (or `terminal-overrides`), and wheel bindings that enter copy-mode. Put this in the TUI README/ONBOARDING, not tribal memory.
- **Never encode state in color alone** — pair color with a glyph/text (`✗ FAILED`, `⏸ skipped`), which survives 256-color and monochrome. Use Textual's theme/semantic styles rather than hardcoded truecolor hex.
- **Provide keybindings for everything the mouse does** (scroll, focus next pane, select row) — over SSH the wheel is the least reliable input.
- Reattach robustness: prefer restarting the TUI after a detach (it re-reads artifacts — see Pitfall 4) over surviving in-place; test the reattach path explicitly. Pin a floor Textual version and track #6668-class fixes in the CHANGELOG (see Pitfall 7's version policy).
- Add an exit-hygiene smoke check to the manual test list: launch, interact, quit, verify the shell prompt is sane (`reset` not required).

**Warning signs:**
- Bug reports that only reproduce "over SSH from my laptop" or "inside tmux."
- Any widget state communicated only by shade of color.
- Operators routinely running `reset` after using the console.

**Phase to address:** P1 (the compatibility test matrix and the color/glyph discipline are cheap only if set as conventions up front); re-verified in P3 when long-lived monitoring sessions make reattach common.

---

### Pitfall 4: State desync — TUI view vs filesystem truth

**What goes wrong:**
The dashboard shows a world that no longer exists: a "failed" list from a sweep that was re-launched, a cell shown "running" whose `run_record.json` already says `completed`, a truncated JSON parsed as empty, or "done" claimed for a cell whose resume marker was never written. Concretely in this repo:
- `sweep_failures.json` is **deleted at sweep start** (WR-06) — a TUI holding the old list in memory shows phantom failures the moment a re-run begins.
- `run_record.json` / `sweep_manifest.json` are written with `open("w")` + `json.dump` — **not atomic** — so a poll that lands mid-write reads truncated JSON.
- A cell is resumable/complete only when `trainer_state.json` exists, and it is written **last** (WR-13) — a directory existing proves nothing.
- `run_record.json` is never rewritten once final (WR-12) — so "current status" is a blend of manifest enumeration + record state + marker presence, and any cached blend goes stale.

**Why it happens:**
The sweep is the writer and the TUI is a reader with no notification channel. Textual offers **no public stable filesystem-watching API** (the `api/watcher/` docs page 404s in 8.x; the internal `FileMonitor` is an mtime-polling helper, not a watchfiles/inotify API — Textualize's own `toolong` ships its own polling watchers rather than using one). So the TUI must poll, and naive polling plus caching manufactures desync.

**How to avoid:**
- **One artifact-loader module, used by every widget** (the `DataAPI` pattern from the web frontend is the in-house precedent). No widget opens `sweep_*.json` itself.
- Poll on a `set_interval` timer (1-2 s is plenty; cells run for minutes). Each tick: stat mtimes first, re-read only what changed; tolerate `json.JSONDecodeError`/`FileNotFoundError` by **keeping last-known-good and skipping the tick** — never crash the dashboard on a mid-write artifact.
- Treat every read as a snapshot with an "as of" timestamp rendered in the UI; on sweep-start detection (manifest mtime reset / failures file gone), **drop all cached state**, don't merge.
- Derive cell status the same way `run_sweep.py` does: record status + `trainer_state.json` marker presence — reuse the repo's own semantics rather than inventing a parallel state machine (which is also Pitfall 8).
- Reattach = cold read. Since the TUI is a supervisor (Pitfall 2), "restart TUI, see truth" must always work.

**Warning signs:**
- Any `json.load` in a widget file rather than the loader.
- Tests that only exercise the loader with well-formed, complete JSON (add a truncated-file and missing-file case to the P1 loader tests).
- UI state surviving a detected re-launch.

**Phase to address:** P1 (loader seam + tolerant-read tests land with the foundation, because every later screen consumes it); P3 exercises it against real sweep timing.

---

### Pitfall 5: Long-lived session resource leaks (handles, timers, workers, widget memory)

**What goes wrong:**
A monitoring session left open for a multi-day sweep degrades: RSS creeps (unbounded log buffer, ever-growing caches), file handles accumulate (each poll tick opening without closing, log-tail handles per cell never released), stale `set_interval` timers keep firing for screens that were popped, and repeated actions (re-entering the dashboard, retrying a download) stack duplicate workers.

**Why it happens:**
TUIs are long-lived in a way CLIs never are — the process that would have exited in the pipeline world now lives for days. Python's GC hides most handle leaks until the box is slow, and Textual workers/timers are tied to DOM nodes: removing a screen cleans them up *only if* they were created on that node and nothing else references them.

**How to avoid:**
- `with open(...)` context managers everywhere in the loader (the repo's `script/` convention already mandates this — carry it into TUI code; ruff's lint surface should flag bare `open`).
- `RichLog(max_lines=...)`; bounded dicts for any per-cell cache (the `TaskLoader` LRU-of-10 pattern in `js/task-loader.js` is the in-house precedent).
- Create timers/workers on the screen or widget that owns them so teardown is automatic; cancel log-tail workers in `on_unmount`; `exclusive=True` on any retryable action.
- One open log-tail per viewed cell (not per cell in the matrix), closed on view change.

**Warning signs:**
- `lsof` on a TUI left running overnight shows growing fd counts.
- Two entries for the same action in a worker listing; CPU pegged by timers after navigating away.

**Phase to address:** P1 conventions; enforced structurally in P3 (the first genuinely long-lived screens).

---

### Pitfall 6: Testing pitfalls — Pilot flakiness, time dependence, headless CI

**What goes wrong:**
TUI tests flap in CI (pass locally, fail on the runner, or fail randomly), and the team loses trust in them; or worse, they're written as smoke-only and catch nothing. Classic flavors: asserting immediately after `pilot.press()` before messages settle; sleeping fixed durations (either too short → flake, or too long → the CI 14-minute budget erodes); snapshot baselines that differ per environment; tests that need a real terminal and can't run headless.

**Why it happens:**
Textual apps are asynchronous message machines; Pilot simulates input faster than the app processes it. The official remedy is `await pilot.pause()` (drains the message queue and waits for idle) — skipping it is the #1 flake source. `App.run_test()` runs headless via `HeadlessDriver`, which is exactly right for CI, but only if the app's data/seams are injectable (no real GPU, no real ModelScope, no real sweeps — the repo's CI constraint). Snapshot testing (`pytest-textual-snapshot`) has its own trap: the **first run always fails** (no baseline) and `--snapshot-update` must follow *human verification*, or garbage becomes the golden.

**How to avoid:**
- Land the test harness in P1 together with the skeleton: `pytest` + `pytest-asyncio` with `asyncio_mode = "auto"`, every TUI test through `async with app.run_test() as pilot:`; assert only after `await pilot.pause()`.
- **No wall-clock sleeps.** Synchronize on conditions: `await app.workers.wait_for_complete()` for worker-backed loads; make every `set_interval` interval an injectable constructor/parameter (tests pass 0.01 s). This mirrors the repo's existing fake-executor discipline in `tests/test_sweep.py` — the TUI's sweep-launcher seam gets the same fake (a stub process or stubbed `create_subprocess_exec`), keeping CI GPU-free per the milestone constraint.
- Snapshot tests: use sparingly (a few canonical screens), commit SVGs as maintainer-verified goldens per the repo's golden-file discipline, treat snapshot diffs in CI as review artifacts (HTML report uploaded as artifact), and re-baseline only with eyes on the report.
- Use `run_test(size=(N, M))` to test the narrow-SSH-terminal rendering (e.g. 100×30 and 200×50 legs), catching truncation bugs that only appear over SSH.
- Expect `WaitForScreenTimeout`-class failures to mean "deadlock/unprocessed message," not "slow runner" — fix the app, never the timeout.

**Warning signs:**
- `time.sleep` in any TUI test (ban via review).
- Tests that only pass with `--snapshot-update` run first.
- A TUI test importing `torch`, `dnallm`, or hitting the network.

**Phase to address:** P1 (harness + fake seams land with the first screen — retrofitting testability into a live app is the expensive path); every later phase inherits the pattern.

---

### Pitfall 7: Dependency-gate pitfalls — TUI deps leaking into the wrong groups

**What goes wrong:**
`uv sync` on the offline data chain (or in CI's data lane) suddenly drags in `textual` + `rich` + `platformdirs` + `pygments` + `markdown-it-py`; or the operator's GPU environment gets a textual upgrade that breaks the TUI mid-milestone; or `textual-dev` (the dev-tools package with the console/serve commands) lands as a runtime dependency of the operator console.

**Why it happens:**
uv's `default-groups` currently `["data"]` — anything added there (or to `dev`, which CI installs) becomes ambient. Textual releases every few weeks, follows SemVer with real cross-major breaks (2.0.0 `OptionList` API removal, 3.0.0 `App.query` default-screen semantics change, 8.0.0 `Select.BLANK`→`NULL`), and has **no official upgrade guide** — the CHANGELOG is the only reference. Ecosystem practice (gptme, atlas, hypergumbo) is bounded ranges with deliberately-raised floors. Textual 8.2.8 itself is pure-Python and CPU-only, so it *can* live in CI — the question is which lanes must carry it.

**How to avoid:**
- New **`tui` dependency group**: `textual>=8.2,<9` (floor at the audited version, cap at the audited major — consistent with the repo's bounded-range discipline). `default-groups` stays `["data"]` so the data chain and website tooling never see it. `gpu` group never gains TUI deps; `textual-dev` (if wanted for `textual run --dev` console) goes in `dev` only, never `tui`.
- CI: the test lane that runs Pilot tests installs `--group tui` explicitly (textual is pure-Python CPU — the "CI stays GPU/dnallm-free" constraint is satisfied; the open requirement 3.6 checkbox should be resolved as "no GPU/TUI *runtime display*, textual-the-library is fine in the test lane").
- Lock discipline unchanged: floors in `pyproject.toml`, exact pins in `uv.lock` (the existing dev-group pattern). Version bumps are deliberate commits that read the CHANGELOG's breaking-change flags — same treatment `ty` already gets in this repo.
- ruff + ty gates cover TUI sources from day one (add the TUI package dir to `[tool.ty.src] include` and ruff's paths in the same commit that creates the package — memory rule: ty wired in from Phase 3 on, and here from P1).

**Warning signs:**
- `uv sync` output on a clean data-lane checkout mentioning textual/rich.
- A `uv.lock` diff that touches torch lanes because of a TUI dependency change.
- Unbounded `textual>=X` with no cap.

**Phase to address:** P1 (the group is created with the first line of TUI code; retro-fitting group hygiene after widgets exist always misses a lane).

---

### Pitfall 8: Scope creep — reimplementing pipeline logic client-side instead of reading artifacts

**What goes wrong:**
The TUI grows its own copy of benchmark semantics: its own cell enumeration that counts 3,112 cells when `run_sweep.py --dry-run` says 3,100; its own rank/aggregation preview that disagrees with `script/summarize_comparison.py`; its own dataset-presence check that diverges from `n_audit.json`; its own "is this model eligible for probe" guard instead of surfacing `PROBE_INELIGIBLE`. Every disagreement becomes a correctness incident on a platform whose core value is "every number is correct and reproducible."

**Why it happens:**
It starts innocently — a quick recomputation to show a richer preview — and each instance is small. But the TUI then holds a second implementation of rules that already exist in `run_sweep.py`/`run_finetune.py`/`script/`, and the two drift on every upstream change (the repo has lived this movie: "duplicate frontend aggregation logic" is already a named anti-pattern in the web UI).

**How to avoid:**
- **Hard rule: the TUI reads registries and artifacts; it orchestrates; it does not compute benchmark semantics.** Selection matrices come from `models_info.json`/`datasets_info.json`; presence from `n_audit.json`; preview counts from **invoking `run_sweep.py --dry-run` and rendering its manifest** (subprocess, cheap, CPU-only — and it is already a tested contract); failures from `sweep_failures.json`; resume state from `trainer_state.json` markers.
- Where pure helpers genuinely must be shared (argv building, priority tiers), import the *existing* function from `pipeline/run_sweep.py` (CPU-side, torch-free — CI's sweep tests prove it) rather than copying it; one definition, two consumers.
- The launch preview shows the **actual argv** the TUI will exec — so preview and execution cannot diverge by construction.
- The E2' full-sweep gate confirms against the sweep's own dry-run manifest, not a TUI-side tally.

**Warning signs:**
- A PR diff touching only TUI files yet changing displayed counts/eligibility rules.
- Two implementations of the same rule found by grep (e.g. tier logic, metric-key mapping).
- Any numeric literal in TUI code that also exists in `script/` or `pipeline/`.

**Phase to address:** P1 (the architecture rule and the dry-run-manifest preview pattern are set before the first feature screen); audited per-phase thereafter.

---

### Pitfall 9: The "TUI becomes the only interface" trap

**What goes wrong:**
Six months in, the only tested path to launch a sweep is clicking through the console. The CLI paths (`run_sweep.py`, `run_finetune.py`, `env_smoke.py`) silently rot — flags drift, the E2' authorization becomes "whoever has TUI access," cron/CI/automation can't drive the platform, and a broken terminal on the GPU box becomes a blocked benchmark. Community consensus is blunt: full-screen TUIs are "GUI programs in disguise" — not composable or scriptable — which is why mature tools keep a machine mode next to the human mode (Amplitude Wizard's dual-mode architecture: TUI + `--agent` NDJSON + `--ci` non-interactive, patterned on gh/stripe/terraform CLIs).

**Why it happens:**
The TUI is where the new development energy goes; every convenience lands there first "because that's what operators use," and the CLI equivalents stop being maintained or never gain the new knobs.

**How to avoid:**
- **Every TUI capability must already exist as a CLI capability** — this milestone's design already satisfies it (selection → `--models`/`--tasks`/priorities file; downloads → ModelScope CLI/SDK; launch → `run_sweep.py`; retry → `--from-failures`; checks → `env_smoke.py`). The TUI is a view+supervisor over those entry points, never a replacement (and the TUI should show the equivalent command line for what it's about to do — which Pitfall 8's argv preview provides for free).
- Keep the CLI path CI-exercised: the existing `tests/test_sweep.py` dry-run/fake-executor contract tests are the regression net — new TUI-driving flags (e.g. `--effective-batch`) land in `run_sweep.py`/`run_finetune.py` first, with tests, then get surfaced in the TUI.
- The E2' maintainer authorization must remain a *documented, reproducible CLI act* (the confirmation gate records the exact command the maintainer is authorizing), not a TUI-internal state.
- Documentation (ONBOARDING) shows both paths side by side for every operator task.

**Warning signs:**
- A feature request that can only be satisfied by changing TUI code.
- Docs that say "open the console and..." with no CLI equivalent.
- CI green while the last-touched CLI flag has no test.

**Phase to address:** P1 (architecture principle: TUI wraps entry points); P3 verifies it end-to-end (launch from TUI ≡ launch from CLI, same artifacts); P4 (multi-GPU orchestration is the highest-risk regression point — the sharding layer must equally be a CLI-invocable mode).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Parse sweep stdout as a data contract in the TUI | No changes to sweep code needed | Brittle to any print-format change; P1→P4 rework | Never — read JSON artifacts; stdout is for humans/logs |
| Poll every artifact every tick (no mtime check) | Simpler loader | Wasted IO at 62×50 scale; CI-time slowdown | MVP-only in P1, replaced before P3 dashboard |
| Sync ModelScope calls in a handler "just for one download" | Ships the data manager faster | Frozen UI during multi-GB downloads (Pitfall 1) | Never |
| One giant App class for all screens | Fast start | Unnavigable; test setup drags the whole app | Never beyond P1 skeleton — one screen-module per domain from the start |
| Hardcoded 80×24 assumptions in layouts | Looks fine locally | Broken on narrow SSH windows | Never — test at two sizes (Pitfall 6) |
| Skipping the per-sweep tee-to-file because RichLog shows it | Less code in P3 | Output lost on TUI death/SSH drop; no audit trail | Never (Pitfall 2) |
| Snapshot tests for every screen | Cheap visual coverage | Baseline churn on every styling tweak; CI noise | Only canonical screens, maintainer-verified goldens |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `run_sweep.py` (as child process) | Importing its executor in-process; inheriting stdout; assuming CWD | `create_subprocess_exec` with argv list, PIPE, cwd pinned like `launch_subprocess` does (`PIPELINE_DIR`); pass `--output-root` explicitly (directory-settings requirement) rather than relying on CWD |
| `run_sweep.py` (pure helpers) | Copying enumeration/argv logic into the TUI | Import the existing functions; one definition (Pitfall 8) |
| ModelScope SDK | Sync calls on the event loop; token echoed into TUI logs/config | Thread worker (`@work(thread=True)`); SDK reads `~/.modelscope` itself — never copy/log the token; persist only queue state, never credentials |
| `env_smoke.py` | Ignoring its exit code; parsing human text only | Non-zero exit blocks launch; parse the greppable `PASS:`/`FAIL:` lines for the reasons view (stable, documented contract) |
| tmux / SSH terminals | Assuming wheel-scroll, truecolor, SGR mouse always available | Blessed tmux config documented; keybindings for scroll; color+glyph redundancy (Pitfall 3) |
| Artifact JSON (`run_record`/`sweep_failures`/`trainer_state`) | Caching reads across sweep restarts; crashing on mid-write files | Loader with tolerant reads + mtime diffing + cold-read on reattach (Pitfall 4) |
| GitHub Actions CI | Installing the `gpu` group for TUI tests; or excluding TUI tests entirely | `--group tui` (+dev) in the test lane only; fakes for any process seam (Pitfalls 6, 7) |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Unbounded `RichLog` growth | RSS climbs over a multi-hour monitoring session | `RichLog(max_lines=10_000)`; durable copy on disk anyway | First multi-hour sweep (P3) |
| Re-rendering the full 62×50 matrix on every poll tick | Dashboard CPU-pegged; flicker | Update only changed rows/cells; tick at 1-2 s; stat-mtime gating before re-read | First full-matrix dashboard render |
| Re-reading all 47-50 task artifacts every tick | IO storm, slow ticks | Loader memoizes by (path, mtime, size) | P2/P3 as artifact counts grow |
| Fixed-interval timers that also fire when hidden/unfocused | Background CPU burn while operator reads a log | Pause polling when the screen isn't visible (`Screen` visibility / timers owned by the screen) | Long-lived sessions (P3) |
| One worker per matrix cell (e.g. 3,100 log tails) | Worker explosion, fd exhaustion | Tail only the currently viewed cell; one supervisor worker for the sweep | First "tail all logs" feature idea |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Copying the ModelScope token into TUI config/session files | Token leaks via dotfiles, screenshots, sync | SDK reads `~/.modelscope` directly; TUI stores no credentials; session/state files audited to contain paths/flags only |
| `shell=True` or string-joining user-selected model names into commands | Injection through registry values / template imports | Argv-list discipline (T-03-10 continuity); validate imported run-config templates against registries the way `--from-failures` validation does |
| TUI logs echoing full child environment | Secret-bearing env vars in durable tee-files | Log child stdout/stderr only; never dump env |
| E2' gate as a saved/default setting in a template | Full three-seed sweep auto-authorized by imported config | Full-sweep authorization is per-session interactive confirmation over the dry-run manifest, never a persisted default |
| Template import (JSON) trusted blindly | Malicious/typo paths in project/storage dir settings escape the repo | Same-path validation as `--from-failures` (`_read_operator_json` pattern); reject unknown keys, resolve and display effective paths before applying |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|------------------|
| Color-only status | 256-color/SSH users misread cell states | Glyph + text + color (Pitfall 3) |
| Mouse-only interactions | Wheel/selection unreliable over SSH+tmux | Full keyboard path for every action; document bindings on-screen (`?` help) |
| Modal blocking the dashboard while a download runs | Operator can't check anything during multi-GB fetches | Non-modal status/queue area; downloads are workers, not dialogs |
| "Where did my sweep go?" after quitting the TUI | Operators assume quitting killed the run | Detached-by-design supervision + an always-visible "sweep running (PID N) — TUI exit will NOT stop it" affordance (Pitfall 2) |
| Hidden refresh age | Decisions made on stale data during a re-launch | "as of HH:MM:SS" timestamp on every artifact-derived panel (Pitfall 4) |
| Bilingual strings interleaved ad hoc | Mixed-language UI drift | Pick per-string language policy at P1 (team requirement flags 中文界面/双语 as open) — one constants module, never inline duplicated strings |

## "Looks Done But Isn't" Checklist

- [ ] **Sweep launch:** often missing the tee-to-file durable log — verify a log file exists on disk with the full child output after a smoke cell
- [ ] **Sweep supervision:** often missing detach semantics — verify quitting the TUI leaves the sweep running and a restarted TUI reattaches (shows live progress, not stale state)
- [ ] **Stop path:** often missing group-kill — verify "stop" terminates the whole child tree (`start_new_session` + group signal), not just the wrapper
- [ ] **Artifact reader:** often missing mid-write tolerance — verify a truncated-JSON tick keeps last-known-good instead of blanking the dashboard
- [ ] **Terminal hygiene:** often missing exit-restore check — verify shell prompt is normal after quit, including after a crashed run
- [ ] **Matrix coverage:** often missing the SSH/tmux/256-color legs — verify at least: local truecolor, SSH plain, SSH+tmux, narrow window
- [ ] **Reattach:** often missing the tmux detach/reattach test — verify no `UnicodeDecodeError` (issue #6668 class) on reattach with the mouse in use
- [ ] **CI parity:** often missing group isolation proof — verify `uv sync` (data default) does not install textual, while the TUI test lane does
- [ ] **Preview fidelity:** often missing argv equality — verify the dry-run preview's manifest matches the actual launch's manifest byte-for-byte
- [ ] **Failure re-run:** often missing CLI equivalence — verify TUI re-run and `--from-failures` produce the same outcome on the same manifest
- [ ] **Resource ceiling:** often missing the overnight soak — verify RSS and fd count are flat after an hours-long monitoring session

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Event-loop blocking baked into handlers | HIGH (touch every handler) | Introduce a `Supervisor` service object owning all process/IO workers; handlers shrink to post_message calls; migrate screen-by-screen |
| Child-output loss (no tee) | MEDIUM | Add tee in the reader worker; historical output unrecoverable — accept, re-run affected cell via `--from-failures` |
| Terminal matrix breakage found late | LOW-MEDIUM | Mostly config/docs (tmux blessed setup) + keybinding pass; color-only fixes are widget-local |
| Desync architecture (widgets reading files directly) | HIGH | Extract the loader module, redirect widgets, add tolerant-read tests — same shape as the web `DataAPI` consolidation |
| Flaky Pilot suite | MEDIUM | Audit for sleeps → replace with `pause()`/`wait_for_complete()`/injectable intervals; quarantine genuinely timing-bound tests behind a marker |
| Textual major bump forced mid-milestone | LOW | Bounded `>=8.2,<9` cap makes this a deliberate upgrade: read CHANGELOG breaking flags, fix call sites, refresh snapshots with review |
| Client-side logic duplication discovered | HIGH (correctness brand) | Diff TUI-computed values against `--dry-run`/script outputs; delete the TUI copy; add a parity test that runs both and compares |
| CLI rot | MEDIUM | Feature-freeze TUI additions until CLI parity restored; add the missing CLI tests; document dual paths |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|---------------|
| 1. Event-loop blocking | P1 (worker/subprocess discipline is the foundation architecture) | Pilot test asserting UI stays responsive while the fake sweep streams; code-review ban on sync calls in handlers |
| 2. Subprocess output loss / teardown | P3 (launch + monitoring) | Smoke cell leaves complete tee-file; quit-TUI-reattach test; stop-action kills process group |
| 3. Terminal matrix (SSH/tmux/mouse/color) | P1 conventions, P3 verification | Manual matrix checklist (4 environments) executed at P3 exit; color+glyph lint over status renderers |
| 4. View-vs-filesystem desync | P1 (loader seam), P3 (live timing) | Loader unit tests with truncated/missing/stale artifacts; cold-read-on-relaunch test |
| 5. Resource leaks | P1 conventions, P3 enforced | Overnight soak with RSS + fd-count assertions (manual, documented) |
| 6. Pilot/testing pitfalls | P1 (harness lands with first screen) | Zero `time.sleep` in TUI tests (grep gate); CI runs the TUI lane headless green |
| 7. Dependency groups | P1 (`tui` group created day one) | `uv sync` dry-run shows no textual in default resolution; CI lane matrix green |
| 8. Client-side logic duplication | P1 rule, audited each phase | Preview-vs-dry-run parity test; grep audit for duplicated tier/metric logic per phase review |
| 9. TUI-only interface trap | P1 principle, P3/P4 verification | Every operator task documented with CLI equivalent; E2' gate records the authorized command line; CLI contract tests still green |

## Sources

- Textual official docs — Workers guide (textual.textualize.io/guide/workers/) and Testing guide (textual.textualize.io/guide/testing/), fetched 2026-10-11 — MEDIUM (first-party, cross-checked against API docs and discussions)
- Textualize discussions #3788 and #2689 ("Displaying output from script in a RichLog", "continuously update TextLog from a running process") — MEDIUM (official maintainer answers)
- Textualize/textual issue #6668 (SGR mouse negotiation dropped on tmux reattach/SSH reconnect → X10 fallback → UnicodeDecodeError) — MEDIUM (single issue, reproducer-graded)
- textual-shell (jason-lawrence.github.io/textual-shell) and terraform-tui `plan.py` — subprocess+RichLog reference implementations — MEDIUM (community code, convergent pattern)
- Textual PyPI metadata JSON (version 8.2.8, requires-dist, requires-python) — HIGH (registry fact)
- Textual CHANGELOG + ecosystem pinning practice (frogmouth #94, gptme PR #3202, atlas, hypergumbo) — MEDIUM (version-break history triangulated)
- Textual `file_monitor.py` source + api/watcher 404 — negative finding: no public stable file-watching API in 8.x — MEDIUM (docs + source verified)
- Amplitude Wizard dual-mode architecture doc; Chef Courier antipattern doc; HN TUI composability thread — MEDIUM (multi-source consensus on keeping CLI first-class)
- Repo grounding: `pipeline/run_sweep.py` (subprocess/cwd/WR-06/WR-12/_write_json), `pipeline/run_finetune.py` (WR-13 marker ordering), `pipeline/env_smoke.py` (exit contract), `.github/workflows/ci.yml`, `pyproject.toml` — HIGH (read directly, 2026-10-11)

---
*Pitfalls research for: dnallmmark v1.2 TUI milestone (Textual console over subprocess-driven sweeps)*
*Researched: 2026-10-11*
