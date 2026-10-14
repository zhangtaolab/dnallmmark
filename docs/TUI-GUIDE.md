<!-- generated-by: gsd-doc-writer -->
# TUI Guide — Operator Console

This is the operations guide for the DNALLM-Mark TUI console: what an operator does on each of the six screens and which keys do what. Every key table below is derived from the `BINDINGS` declarations in `tui/screens/*.py` — those declarations are the single key-map authority; the top/bottom bars and the `?` help modal render from the same source. For requirements and design intent, see `docs/TUI-REQUIREMENTS.md`; for the multi-GPU workflow, see `docs/multi-gpu.md`.

## Quick start

```bash
make tui
```

`make tui` runs `uv run --group tui --group gpu python -m tui` (`Makefile` target `tui`) — the `tui` group (Textual, platformdirs) plus the `gpu` group (torch, transformers). It can be invoked from any directory; the entry point (`tui/__main__.py`) resolves the repo root from its own file location.

Typical first session:

1. `make tui` — the console opens on the **environment check** screen (slot 1). A same-day cached check renders instantly; otherwise the seven kernels run in a background worker.
2. Press `2` — pick models and datasets (space marks, `m` flips the table, `/` filters).
3. Press `3` — if any dataset is missing locally, enqueue downloads (`d` / `a`); the queue persists across restarts and resumes at boot.
4. Press `4` — compose the run (seeds, PEFT, variant, dirs), press `p` for a dry-run preview, press `enter` to go through the launch gate.
5. Press `5` (or let the launch jump you there) — watch the sweep: cell states, ETA, failures, log tail.

Terminal contract: the console requires at least **80x24**. Below that, every screen is replaced by the min-size message showing the current dimensions; grow the window to restore.

## The shell: top bar, bottom bar, global keys

The shell is two one-row bars around every screen (`tui/screens/nav.py`):

- **Top bar** — six digit-prefixed menu slots. The active screen's slot carries the `◆` diamond prefix plus bold/accent styling. Slot names (UI copy is Chinese; keys are the slot digits):

| Digit | Slot | Screen file |
|-------|------|-------------|
| `1` | 环境检查 (environment check) | `tui/screens/env_check.py` |
| `2` | 模型·数据集 (models · datasets) | `tui/screens/selection.py` |
| `3` | 数据管理 (data manager) | `tui/screens/data_manager.py` |
| `4` | 运行配置 (run config) | `tui/screens/run_config.py` |
| `5` | 任务监控 (monitor) | `tui/screens/monitor.py` |
| `6` | 关于 (about) | `tui/screens/about.py` |

- **Bottom bar** — the active screen's keycaps on the left (declaration order, clipped with a trailing ellipsis on narrow terminals) and the constant help/quit pair on the right.

Global keys (declared app-level in `tui/app.py`, active on every screen):

| Key | Action |
|-----|--------|
| `q` | Quit. With a live sweep (one the TUI spawned, or a CLI-launched sweep attached in the monitor that is running), `q` opens the exit modal instead — see below. |
| `?` | Help modal: every active binding with its label (app bindings first, then the active screen's). `esc` closes. |
| `1`–`6` | Switch to the slot's screen (declared per screen as hidden bindings routed to the app's `nav` action). Pressing the active slot's digit is a no-op. |

**Exit modal** (pushed by `q` when a live sweep exists, `tui/app.py` `ExitModal`):

| Key | Action |
|-----|--------|
| `enter` | Detach and quit (default) — drop the handle; the sweep survives and stays resume-safe via the per-cell `trainer_state.json` marker. |
| `k` | Kill — SIGTERM the sweep's process group, then quit. |
| `esc` | Return to the console without quitting. |

While any modal is open, screen/app keys do not fire (`esc` is the universal close). A focused input (filter, seeds, paths) consumes its own keystrokes — including digits — until focus leaves it; this is by design so typing can never trigger navigation or launch.

## Screen 1 — Environment check (环境检查)

Runs the seven `pipeline/env_smoke.py` kernels and shows the verdict that the slot-4 launch gate enforces. Results persist for the local calendar day: a same-day restart renders the cached result instantly and runs zero kernels.

The seven rows, in kernel order: `version_pins`, `dnallm`, `peft`, `cuda`, `matmul`, `numpy`, `dataset_dirs`.

| Key | Action |
|-----|--------|
| `r` | Re-run every kernel (the only path that re-runs after a cache hit). Rows reset to pending, the exclusive worker restarts. |
| `enter` | Open the cursor row's drill-down modal: the kernel's own detail lines, verbatim, wrapping and scrolling — never elided. `esc` closes. |

Verdict block (rendered from `tui/services/env_gate.py`):

- A failure in any **critical** kernel — `version_pins`, `dnallm`, `peft`, `cuda`, `matmul`, `numpy` — renders "✗ 关键项未通过" naming the kernels, and the slot-4 launch gate blocks the launch (env preflight re-runs the same critical set at gate time).
- A `dataset_dirs` failure does not block launch by itself; it renders the routing hint "⚠ {n} 个数据集目录缺失 — [3] 前往数据管理" with the CLI re-audit command (`python script/audit_n_frequencies.py`).

## Screen 2 — Models · datasets selection (模型·数据集)

The operator's daily surface: two tables (models, datasets) browsed one at a time, type-to-filter, spacebar marks, presets/templates, and the local-presence column (per-dataset train/dev/test counts from `n_audit`, flipping live when a queued download reconciles).

Marks live in shared app-state sets (not inside the table), so filter rebuilds and table switches never lose them.

| Key | Action |
|-----|--------|
| `space` | Toggle the mark on the cursor row. Marking a **disabled custom** entry is refused with a warning (a mark the sweep can never see). State rows (loading / no-match / error) never mark. |
| `m` | Switch between the models table and the datasets table (title flips; both mark sets stay alive). |
| `/` | Focus the filter input — k9s-style type-to-filter over the registry grammar; live `(N/total)` readout; unknown-axis terms render a dim warning while valid terms still apply. |
| `esc` | Clear the filter and refocus the table (when the filter is not active, `esc` is a no-op here). |
| `enter` | Open the cursor row's card drill-down (every registry field, wrapping, never elided). |
| `p` | Open the preset picker: derived tier-1 / tier-2 / all presets plus your saved customs (sorted). Highlight a preset and press `enter` (or toggle it) — the first selection **applies and closes**. Applying **replaces** the mark set(s); keys not in the current registry are skipped with a loud warning, never silently. |
| `s` | Save the current marks as a named custom preset (path/name modal; an existing name asks a confirm before overwrite). Presets persist to `presets.json` under the XDG config root. |
| `x` | Template menu (import / export / tier-convert). Import validates collect-all and fail-closed — a bad file renders the numbered problem list and applies nothing; export writes the selection as a run template JSON; tier-convert exports it as a `sweep_priorities.json`-style tier list. |
| `w` | Open the onboarding wizard for the **active table's kind** (models table → model wizard, datasets table → dataset wizard). With the cursor on a custom row, the form prefills from that entry (edit = re-record). Wizard keys: `enter` advance, `b` back, `f` import (step 1), `o` export registry (step 1), `u` undo a just-landed entry, `esc` cancel. |
| `e` | Toggle the cursor **custom** entry's enabled state (disable removes it from runs at loader level; the row stays visible with the disabled suffix). On an official row it is a no-op with an honest toast. |
| `d` | (Datasets table only) Enqueue the cursor's **missing** dataset into the shared download queue — the same queue and toasts as the data manager's `d`. A present row gets a no-op toast; the models view ignores the key. |
| `v` | Push the read-only 59×50 presence matrix (marks shown as `◆` prefixes). `enter` shows a cell's full keys; `esc` returns. |

## Screen 3 — Data manager (数据管理)

Two stacked panes over one shared, persistent download queue: the **missing-datasets list** (top, from the committed `n_audit` plus live reconcile results) and the **queue table** (bottom; rows in five states — pending / downloading / done / failed / mismatch — with live percent + progress bar and a reconcile column). Mismatch and failed rows sort to the top and each number-carrying mismatch gets a banner. The title bar shows the presence summary (present/total/missing), and a right-aligned line probes the Zenodo whole-package record (19135551) for publication.

Key-target contract (`d`/`r`/`x` act on their own table's cursor regardless of focus; only `enter` routes by focus):

| Key | Target | Action |
|-----|--------|--------|
| `d` | missing table | Enqueue the cursor row's dataset. Idempotent; outcome toasts for already-queued / disabled-channel / unknown-key / CLI-unavailable / persist-failed. |
| `a` | — | Enqueue **every** missing downloadable dataset (count toast). |
| `r` | queue table | Re-queue the cursor's failed/mismatch entry. Other states get a no-op toast. |
| `x` | queue table | Cancel the cursor's pending/downloading entry — always behind a confirm modal (`enter` confirms, `esc` cancels). |
| `enter` | focused table | Drill-down modal: full key, registry `download_url` (the only download authority), the composed download argv, state/attempts/percent, reconcile numbers, and the verbatim CLI/audit log lines — data, never elided. |
| `g` | queue table | (Hidden) Re-run the n_audit audit for the cursor's **mismatch** row — live only on mismatch rows; refreshes both panes when done. |
| `z` | — | (Hidden) Enqueue the Zenodo whole-package bundle — offered only when the publication probe answered "public"; otherwise an explanatory toast. |

The queue is serial, persisted to XDG state, and resumed automatically on the next `make tui` if pending work exists. A done download that reconciles (declared vs measured row counts) is the moment presence flips to ✓ everywhere (slot 2's column, the missing list, the counts). A landed-but-mismatched dataset never flips; use `g` after fixing.

## Screen 4 — Run config (运行配置)

The composition surface: its own model/dataset pickers (slot 2's marks are never read here — this screen owns a persistent run spec), the params pane, directory fields, a live dry-run preview line, and the launch gate.

| Key | Action |
|-----|--------|
| `space` | Toggle the mark on the picker's cursor row. Marks live in the run spec itself and persist to XDG state; disabled customs warn instead of marking. |
| `m` | Flip the picker between models and datasets. |
| `/` | Focus the picker filter (same grammar as slot 2). `esc` clears it. |
| `enter` | **Open the launch gate** (see the next section). On the picker itself, `enter` is pinned to the gate — only `space` marks. On a focused choice row (PEFT / variant), `enter` opens that row's radio-set modal instead; a focused text input consumes its own `enter` (re-applies the field) — typing can never launch. |
| `p` | Dry-run preview modal: the same-source enumeration counts, the note that the gate re-derives everything fresh, the exact `run_sweep.py` argv (verbatim, when the spec is clean), and the numbered problem list otherwise. |

Params pane fields (edits persist and re-derive the preview line on every change):

| Field | Form | Notes |
|-------|------|-------|
| seeds | text input | Comma-separated; default `42,43,44`. Three-plus seeds over the full official matrix is what triggers the E2' gate. |
| PEFT | choice row (`enter`) | `none` / `lora` / `ia3`; a hint shows the adapter alias for the first marked model. Cannot be combined with a config variant. |
| variant | choice row (`enter`) | `none` / `head` / `probe` / `curve`. `probe` surfaces the frozen probe-ineligible model list if any marked model is affected; `head` shows its own note. |
| 曲线档位 (curve) | text input | Comma-separated train fractions (`--curve`). |
| 公平子集 (fairness subset) | checkbox | Off by default; when on, the path row appears (default `pipeline/eval_subsets.json`) with an exists/missing advisory. |
| epochs / effective_batch_size | text inputs | Optional overrides (`--num_train_epochs`, `--effective_batch_size`). |
| output root / dataset root / cache | text inputs | Defaults `./finetuned` and `./datasets`; each carries an exists/missing advisory (missing roots are advisory only — the sweep creates them). |

After a successful launch the console toasts the cell count and auto-switches to the monitor (slot 5) with the new sweep attached.

## The launch gate and the E2' trust boundary

`enter` on slot 4 opens a terraform-style gate pipeline. Every stage recomputes through the services — the preview line's cache is never trusted:

1. **Fresh enumeration** — invalid specs (empty selection, bad seeds/curve, probe-ineligible models, PEFT×variant composition, invalid output root) open the numbered problems modal and nothing launches. A launch into an output root that already has a **live** sweep is also refused here, naming the root.
2. **Env preflight** — the critical kernel set re-runs; failure opens the env-block modal naming the failing kernels and their verbatim reasons (route to slot 1, press `r` after fixing).
3. **Confirm** — a summary modal (models × tasks × seeds → cells, output root). `enter` launches, `esc` cancels.
4. **E2' escalation (when applicable)** — if the spec is the **full official re-run** (models superset of the official registry, tasks superset of the official trainable tasks, and **≥ 3 seeds** — `E2X_MIN_SEEDS = 3`, `tui/services/run_config.py`), the plain confirm is replaced by the typed-phrase modal.

The typed-phrase modal ("⚠ 全量 E2' sweep — 59 模型 × 50 数据集 × 3 种子 = 8850 cell") demands the operator type the **final directory name of the resolved absolute output root** (e.g. an output root `./finetuned` demands the phrase `finetuned` — the modal itself shows the exact expected name). The verdict is exact string equality — no stripping, no case folding — evaluated by the service tier on every keystroke (the widget holds no matching logic), and `enter` confirms **only** on the exact-match indicator. The check fails closed on a degenerate empty phrase, and the launcher service re-proves the phrase structurally before spawning — no widget path can normalize its way past it. This is the maintainer authorization boundary for full E2' runs.

The same gate, including the E2' phrase, applies to the monitor's from-failures re-run (below): an E2'-class effective matrix refuses at the phrase stage and re-prompts.

The CLI has no such gate, by design — `run_sweep.py` / `run_sweep_shard.py` are the maintainer trust surface (see "The E2' trust boundary" in `docs/multi-gpu.md`).

## Screen 5 — Monitor (任务监控)

Monitoring over the artifact scanner. Cadence (shown right of the title): a 2-second frontier pass over the **attached** root and a 60-second full scan; `[r]` forces a full rescan immediately. The layout is a **discovered sweeps** table (top) and a **cell table** (bottom, the attached sweep's model × task rows with one column per seed), plus a one-row stats line (done/total, current model×task×seed, elapsed, ETA point/range/pending).

Discovered rows carry three states — running / finished / artifacts-only (a root with artifacts but no live process and no completion) — with a `{done}/{total}` progress bar and ETA on running rows, and the manifest scale (`models×tasks×seeds`) when the terminal is wide. Cell seed glyphs: `✓` completed, `✗` failed, `⊘` skipped-by-resume-marker, `⠋` running, `◌` queued; curve cells fold to `glyph done/total`. A resume-count note sits on the cells title row.

| Key | Action |
|-----|--------|
| `enter` | On the discovered table: **attach** the cursor's sweep root (the `◆` marker moves; the cell table, stats, failures, and log keys rebind to it; a toast confirms). On the cell table: open the cell-detail modal — per-seed states, per-fraction lines, and the seed's `run_record` fields verbatim. |
| `f` | Failures modal over the attached root (live failure records / `sweep_failures.json`): one row per failure; `enter` drills the verbatim error string. |
| `r` *(inside the failures modal)* | Re-run the failures — behind its own confirm (real GPU spend), then the **same gate as slot 4**: env preflight first, the E2' phrase if the effective matrix demands it, then a `--from-failures` launch at the sweep's own root carrying the source sweep's own lane (`--peft` / `--config-variant` recovered from its artifacts). |
| `t` | Log-tail modal: the attached sweep's tee file, refreshed on the 2s cadence while open; the dim line names the file. A CLI-launched sweep (no tee) renders the designed unavailable state and schedules no refresh. |
| `a` | Attach a **manual root**: path modal, validated as a real sweep root; invalid paths keep the modal open with the reason. Manual roots persist across sessions. |
| `r` *(screen level)* | Immediate full rescan; the count toast lands when the scan does. |

After a TUI launch, the new sweep is auto-attached and the console switches here automatically.

## Screen 6 — About (关于)

Read-only. Five rows — software (version + git sha), data (official/custom counts + n_audit presence), milestone, dependencies, repository — derived in a background worker, tolerant of any missing probe. No action keys beyond the nav digits and the global `?` / `q`.

## Multi-GPU monitoring (worker roots)

Multi-GPU runs are CLI-orchestrated (`pipeline/run_sweep_shard.py` — see `docs/multi-gpu.md`); the TUI composes single sweeps only. Because each worker is an independent output root (`{output-root}-mgpu-w{i}`), the monitor renders N workers natively with zero new screens:

1. `make tui`, go to slot 5.
2. Press `a` once per worker root — e.g. `pipeline/finetuned-mgpu-w0`, `pipeline/finetuned-mgpu-w1`. Attachments are validated and **persisted** (they survive restarts).
3. The discovered table lists every worker as its own row with independent progress/ETA; `enter` on a row switches the attached cell-table/stats/failures/log view to that worker.

Roots are discovered from two default scan roots plus your manual roots: `{repo}/pipeline/finetuned` and `{repo}/finetuned` (both resolution homes of the default `./finetuned` — TUI-launched sweeps run with cwd pinned to `pipeline/`, CLI runs resolve against the shell's cwd) plus everything in the persisted manual-roots list.

Two limits to know:

- The TUI exit prompt (`q` → kill) can only kill processes **the TUI spawned**. CLI-launched workers must be stopped with the process-group recipe in `docs/multi-gpu.md` (`kill -TERM -<pgid>`); workers are deliberately Ctrl-C-immune (own session, resume-safe).
- Failed-worker re-runs from the TUI's `[f]` modal operate on the attached worker root only; healthy workers are never touched.

## State persistence (what lives where)

All TUI state resolves through `tui/services/settings.py` via platformdirs, with whole-directory env overrides. The state/config split is absolute: regenerable machine state never lands under the config root; hand-authored config never lands under the state root. Every write is atomic (temp sibling + `os.replace`).

**`~/.local/state/dnallmmark`** (XDG state root — regenerable machine state):

| File | Contents |
|------|----------|
| `env_check.json` | Env-check results + checked-at (the same-day cache) |
| `download_queue.json` | The persistent download queue (entries, states, reconcile payloads) — resumed at boot |
| `run_config.json` | The slot-4 run spec (marks, seeds, PEFT, variant, dirs) |
| `monitor_roots.json` | Manually attached monitor roots |
| `zenodo-19135551/…` | Staging for the Zenodo whole-package download |

**`~/.config/dnallmmark`** (XDG config root — user-owned, hand-shareable):

| File | Contents |
|------|----------|
| `presets.json` | Saved custom selection presets (`s` on slot 2) |
| custom model/dataset registries | Landed custom entries from the `w` wizard (same root the pipeline's overlay loader reads) |

Overrides (whole directory; empty value = unset): `DNALLMMARK_TUI_STATE_DIR`, `DNALLMMARK_TUI_CONFIG_DIR`, and `DNALLMMARK_CUSTOM_REGISTRY_DIR` for the custom-registry overlay root.

## Troubleshooting

**The launch gate blocked with an env failure (EnvBlockModal).** The critical kernels are `version_pins`, `dnallm`, `peft`, `cuda`, `matmul`, `numpy`. Go to slot 1, `enter` the failing row for the verbatim reason, fix, press `r`, then retry the gate. Common causes: `dnallm` is deliberately not in any committed dependency group — it must be installed manually from a local clone (see `docs/CONFIGURATION.md`); `cuda`/`matmul` require the `gpu` group and a real GPU (`make tui` already includes `--group gpu`).

**Missing datasets (dataset_dirs ✗ / presence ✗).** Slot 1 shows the count and the `[3]` routing hint. On slot 3, `d` enqueues the cursor's missing row or `a` enqueues all; watch the queue pane (states, progress bar, reconcile column). Presence flips to ✓ exactly when a download lands and reconciles. If a download finishes as **mismatch** (declared vs measured rows differ), fix the cause and press `g` on the row to re-audit; **failed** rows are re-queued with `r`. A `cli_unavailable` toast means the ModelScope CLI is not on PATH; a `disabled` toast names the dataset key whose channel is disabled in the registry.

**Keys 1–6 or `enter` "do nothing" while typing.** A focused input consumes its keystrokes. Press `esc` (clears the filter and refocuses the table) or move focus off the input. Related pin: a focused text input also consumes `enter`, so typing parameters can never open the launch gate — `enter` opens the gate only from the picker or an unfocused surface.

**The terminal went blank with a single Chinese line.** The window is below 80×24 — the min-size guard replaced everything. Enlarge the window; the previous screen (and any open modal beneath the guard) is restored exactly.

**Log tail says unavailable.** The attached sweep was launched from the CLI, so the TUI holds no tee file for it. Follow the worker's own per-launch log (`{root}-mgpu-w{i}-{stamp}.log`, or the launcher's tee under the output root) in another terminal.

**A download stalled with a persist-failure toast.** The queue state file could not be written (permissions/disk). The entry stays pending; fix the state rail (`~/.local/state/dnallmmark/download_queue.json` and its directory) and re-kick by enqueuing anything or restarting the console — pending work resumes at boot.

**Everything looks stale after an external change.** The monitor rescans every 60 seconds (2s for the attached root) — press `r` on slot 5 for an immediate rescan, or `r` on slot 1 to re-run the env check. The data manager reloads both panes whenever you navigate to it (press another slot's digit, then `3` again).
