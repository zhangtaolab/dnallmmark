# Feature Research

**Domain:** Terminal UI consoles for ML benchmark/experiment launching — dnallmmark v1.2 TUI milestone
**Researched:** 2026-10-11
**Confidence:** MEDIUM overall (claims grounded in official docs of Textual, rich, accelerate, lm-evaluation-harness, huggingface_hub, terraform, nvitop, gpustat, k9s — read directly; Optuna Dashboard and Textual example claims cross-checked across official docs + second sources. Context7 provider was unreachable this run; official-doc WebFetch + cross-checked WebSearch was the fallback, capping most tiers at MEDIUM. No claim below rests on a single third-party source unless flagged LOW.)

**"Users" here** are benchmark operators (maintainer + team) driving 62-model × 50-dataset × multi-seed fine-tuning sweeps on single- then multi-GPU machines over SSH. The bar being researched: how established launcher/monitor TUIs and consoles solve selection, configuration, launch gating, monitoring, log tailing, failure re-run, downloads, and template sharing — so the TUI feels familiar rather than inventive.

**Existing assets assumed (NOT re-researched, per milestone context):** `run_sweep.py` (tiers, `--from-failures`, `--dry-run`, `--peft`, `--curve`), `run_finetune.py` (`--config-variant` probe/head/curve, `--train_fraction`, `--subset_file`), registries (`models_info.json`, `datasets_info.json`), `n_audit.json` presence/row-count audit, `eval_subsets.json`, `env_smoke.py` gate, ModelScope channels (SDK/CLI/raw API, 50/50 coverage), `make snapshot`.

The eight feature classes below mirror `docs/TUI-REQUIREMENTS.md` §3. Each class gets table stakes / differentiators / anti-features with tool evidence.

---

## Feature Landscape

### FC1 — Model×Dataset Selection (62×50 grid)

#### Table Stakes

| Feature | Why Expected | Complexity | Notes + Tool Evidence |
|---------|--------------|------------|-----------------------|
| Filterable, sortable list view per axis (models table, tasks table) | Every surveyed tool puts a filter line over a table, never raw scrolling: k9s `/`regex + `!`inverse + `-l` label selector; nvitop `,`/`.` column sort + `/` reverse; Optuna Dashboard sortable/filterable param columns | LOW | Textual `DataTable` filtering = `clear()` + re-add rows (documented approach); sort via `sort()` with key functions (docs warn formatted cells break sort keys — sort on raw values) |
| Multi-select as a mark/tag set over the filtered view | k9s `space`/`ctrl-space` mark + `ctrl-\` clear; nvitop `space` tag + `Esc` clear — the universal "mark rows, act on marks" model | LOW | Textual has **no built-in multi-select** (official DataTable docs: single cursor, `cursor_type` cell/row/column/none). Build it: checkbox glyph column (cells accept Rich renderables), spacebar binding, track `row_key`s in a set — keys are stable across sort/delete, coordinates are not |
| Per-row presence/status column (✓ local / ✗ missing + row counts) | Presence coloring is what makes a 62-row registry table actionable; Optuna colors state chips, k9s container-state columns | LOW | Source = existing `n_audit.json`; render glyph + counts via `update_cell` |
| Preset groups: tier-1 / tier-2 / arena-representative / all / none / invert | lm-eval selects tasks by tags, wildcards (`lambada_openai_mt_*`), and groups — tag-based selection IS preset selection | LOW | Presets = named filter predicates over the registry, stored in `sweep_priorities.json` tier structure (exists) |
| Selection export to runner arguments | lm-eval `--tasks a,b,c`; accelerate passes args through verbatim | LOW | Existing `--models`/`--tasks` flags; this is serialization, not new runner work |

#### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Read-only matrix overview (62×50 grid of cell states) as a *summary pane*, not the interaction surface | One-glance coverage picture (Optuna's history graph plays exactly this role vs its trial table) | MEDIUM | 3,100 cells render fine in Textual, but see Anti-Features — it must not be the primary selection mechanism |
| Cross-axis selection preview ("6 models × 4 tasks × 3 seeds = 72 cells, 2 datasets missing") | No surveyed tool does this well; directly answers the "how big is this run" question before config | LOW | Pure arithmetic over selection set + n_audit |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full editable 62×50 cell matrix as the primary UI | "Matrix" is in the requirements doc | Terminal-hostile: 3,100 focusable cells, column widths for 50 task names, keyboard navigation nightmare; no surveyed tool does grid-cell selection (k9s/Optuna/nvitop are all row-table + filter) | Filterable lists + mark sets for interaction; matrix as read-only overview/summary pane |
| Mouse-first interaction | Point-and-click feels easier | SSH/tmux mouse support is unreliable (project non-functional requirement lists terminal width/color/mouse as risks); k9s, nvitop, Textual apps are key-first | Keys first, mouse as bonus; publish a keymap (`?` help — k9s/nvitop convention) |

### FC2 — Run Configuration (seeds / PEFT / variant / curve / epochs / GA)

#### Table Stakes

| Feature | Why Expected | Complexity | Notes + Tool Evidence |
|---------|--------------|------------|-----------------------|
| Interactive config form with sane defaults from the existing config file | `accelerate config` is the canonical interactive questionnaire; defaults persist to `default_config.yaml` in cache and later runs need zero flags | LOW | Defaults from `finetune_config.yaml` (epochs=3 already matches maintainer note); persist per project convention `~/.config/dnallmmark/` |
| Enum-constrained inputs validated against registries (model names, PEFT modes, variant names) | wandb sweep YAML validates `method: grid|random|bayes`; lm-eval `--model_args` key=value pairs fail loudly on unknown keys | LOW | Reject free-text where a registry or enum exists |
| Guard/ineligibility warnings surfaced in-form | lm-eval `validate` subcommand exists precisely to check config before running; project already has PROBE_INELIGIBLE guard | LOW-MEDIUM | e.g. probe variant + ineligible model → block with reason, not runtime crash |
| Derived-value live preview (adapter alias `{model}+lora`, effective GA = max(1, N//batch_size)) | accelerate's questionnaire echoes the resolved launch command it will use | LOW | Pure display logic; the `--effective-batch` flag itself is pipeline work (open Q7, D-decision pending) |
| Named, persisted profiles ("smoke 1-epoch", "E2' three-seed") | accelerate `--config_file path.yaml` selects alternative persisted configs — the standard pattern | MEDIUM | Profile = saved run-config JSON; distinct from shareable templates (FC8) only by scope |

#### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Dry-run cost preview inside the config screen (cell count, est. runtime from historical per-cell times) | No surveyed tool previews sweep cost before launch; project's own `--dry-run` gives cell enumeration — add time estimates from prior runs | LOW-MEDIUM | `run_sweep --dry-run` already enumerates cells; historical runtime exists in performance JSONs |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| In-TUI YAML/text editor pane for configs | Power users want raw editing | Duplicates editor tooling, breaks enum validation, widens review surface against "surgical fixes" discipline; k9s `e` shells out to `$EDITOR`, it does not embed one | Suspend-to-editor pattern (Textual ships a `suspend_process.py` example) or edit outside, import/validate inside |
| Live parameter mutation of a running sweep | "Tune it while it runs" | No surveyed launcher supports it; breaks resume-safety and reproducibility contract (every number reproducible) | Stop, adjust, resume — `trainer_state.json` skip logic already gives checkpoint-resume semantics |

### FC3 — Launch with Confirmation Gate

#### Table Stakes

| Feature | Why Expected | Complexity | Notes + Tool Evidence |
|---------|--------------|------------|-----------------------|
| Dry-run preview of exact actions before commit | terraform `plan` (the gold standard: `+`/`~`/`-` change preview, `-out` saves the exact plan to apply); `hf download --dry-run` prints a file/size/cached table; project `run_sweep --dry-run` already enumerates cells | LOW | Surfacing only — the enumeration exists; render it as a reviewable table (models × tasks × seeds rows, presence status) |
| Environment preflight, hard-fail with reasons | `env_smoke.py` already PASS/FAIL with exit code; nvitop `-1/--once` single-shot probe is the same shape | LOW | Call env_smoke, block launch on FAIL, show its output |
| Confirmation modal before launch | terraform `apply` prompts interactive approval (`-auto-approve` exists but is the documented bypass, not the default); k9s separates `ctrl-d` (delete-with-confirm) from `ctrl-k` (kill, no confirm) | LOW | Textual `ModalScreen[bool]` + `dismiss(result)` + `push_screen` callback is the documented confirmation-dialog pattern (official screens guide) |
| Typed confirmation for the full E2' sweep | This project's E2' boundary is a maintainer dual-gate (PROJECT.md) — safety-critical here even though rare elsewhere | LOW | Type the sweep name / an explicit phrase (stronger than y/N — the point is friction proportional to cost); mirrors terraform's insistence that `-auto-approve` be deliberate |

#### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Saved-plan launch: preview → serialize exact cell list → launch exactly that list | terraform `-out tfplan` guarantees what was reviewed is what executes (docs emphasize the saved plan pins the changes); guards against registry drift between preview and launch | MEDIUM | Serialize the dry-run cell enumeration; feed as explicit `--models/--tasks`/priorities input |

### FC4 — Live Progress Dashboard (cell/queue states)

#### Table Stakes

| Feature | Why Expected | Complexity | Notes + Tool Evidence |
|---------|--------------|------------|-----------------------|
| State-colored run/cell table (queued/running/done/failed/skipped; seeds adjacent) | Optuna Dashboard's trial table: state always shown, color-coded chips, filter-by-state (RUNNING/WAITING/COMPLETE/PRUNED/FAIL — official `optuna.trial.TrialState`); k9s container status columns | MEDIUM | Textual DataTable + `update_cell`; color map fixed and documented (colors carry meaning) |
| Polling refresh at a visible, adjustable interval + manual refresh | Optuna Dashboard polls storage on a reload-interval atom (~5s default, user-adjustable — verified across DeepWiki component docs + Tunny docs mirror); nvitop `--interval` default 2s; k9s `ctrl-r` manual refresh | MEDIUM | `set_interval` on the screen; interval in status bar; **this answers open question Q2: poll durable artifacts (`sweep_failures.json`, output-dir mtimes, `trainer_state.json`) — see Anti-Features for why not in-process callbacks** |
| Aggregate header: done/total, current model×task×seed, elapsed/ETA | nvitop header bars, k9s `:pulse` aggregate health view | LOW | Derived from polled state |
| Attach to an already-running sweep (TUI started later / restarted) | optuna-dashboard attaches to a storage URL and shows history + live trials — monitor and producer are separate processes | MEDIUM-HIGH | Requires launch to write all state to disk artifacts (it already does); TUI never assumes it owns the run |
| Resume-state recognition | Project already skips completed datasets via `trainer_state.json`; lm-eval `--use_cache` skips evaluated (model, task) pairs — same concept | LOW-MEDIUM | Mark cells with resume-skip status distinctly from fresh-done |

#### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Worker/GPU pane in multi-GPU phase (per-worker health, sharding map) | nvitop/gpustat-style process table fused with sweep state — no surveyed launcher couples both | HIGH | P4; depends on worker orchestration design (open Q3) |
| Per-cell drill-down into performance JSON as it lands | Optuna shows per-trial params/values on click; here it verifies correctness early (a bad metric surfaces mid-sweep, not after) | MEDIUM | Read-only viewer over existing output schema |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| In-process event callbacks from the sweep (TUI imports/hosts the sweep loop) | Feels "real-time" | Couples lifecycles: TUI crash kills the sweep, SSH drop kills the sweep, TUI upgrade requires sweep restart; every durable console (Optuna Dashboard, k9s) deliberately decouples via polled state | Poll durable artifacts (Optuna precedent); TUI-launched runs are subprocesses whose logs/stdout stream to files the monitor reads |
| Sub-second refresh | "Live" feel | GPU-run cells change on minute scales; 1s polling burns CPU on a training box (nvitop defaults 2s for a reason; Optuna ~5s) | 2–5s default, user-adjustable; manual refresh key |

### FC5 — Log Tailing of Subprocess Output

#### Table Stakes

| Feature | Why Expected | Complexity | Notes + Tool Evidence |
|---------|--------------|------------|-----------------------|
| Follow current cell's stdout/stderr with scrollback | k9s `l` (logs) / `p` (previous logs) on the selected resource — log-follow on selection is the universal gesture | MEDIUM | Verified Textual pattern (official discussions #245, #3788 + textual-shell docs): `asyncio.create_subprocess_exec` (or `Popen` + reader thread) → queue → timer drains → `RichLog.write()`. **Textual has no built-in subprocess runner** (verified against source: only an internal `run_process_messages` loop; `run_process` is not an export) — use asyncio subprocess in a worker |
| Bounded log buffer | RichLog `max_lines` pruning (documented) prevents unbounded memory on multi-hour runs | LOW | Cap + "lines truncated" marker |
| Failed-cell log retrieval after the fact | k9s `p` previous-container logs solve exactly this | LOW-MEDIUM | Requires launch to persist per-cell logs to files (pipeline error-log convention exists); tail from file, not memory |
| Toggle merged vs split stdout/stderr | Debugging interleaving vs attribution | LOW | Two streams or merged-with-tag; store separately on disk |

#### Critical Pitfall (complexity driver)

Child-process block buffering: when stdout is a pipe, not a TTY, Python (and most runtimes) block-buffer, so output arrives in one lump after the process exits (Textualize discussion #3788 documents exactly this in a RichLog). Mitigation: launch with `PYTHONUNBUFFERED=1` (env) or `-u`, and use line-oriented reads. LOW complexity but must be designed in from day one — it is the #1 reason naive log-tailing "doesn't stream."

### FC6 — Failure Review + Re-run

#### Table Stakes

| Feature | Why Expected | Complexity | Notes + Tool Evidence |
|---------|--------------|------------|-----------------------|
| Failure list view with state filter | Optuna Dashboard's filter-by-state (FAIL) isolates failures for review | LOW | Source = `sweep_failures.json` (exists) |
| Failure detail: log tail + error class per cell | k9s drill-down: `d` describe / `l` logs from the row | LOW-MEDIUM | Requires per-cell persisted logs (see FC5) |
| One-action re-run of failed set | Project's `--from-failures` already exists — the rare case where the hard part is built | LOW | Button/key constructs the command, confirmation-gated (FC3), into a new sweep process |
| Scoped re-run (mark subset of failures) | k9s mark-set → act; avoids re-running 40 failures to retry 3 | LOW | Reuse FC1 mark-set machinery on the failure table |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Automatic retry loops (N attempts, backoff) | Unattended resilience | Masks systemic failures (OOM, bad dataset) behind repeated GPU spend; no surveyed benchmark launcher auto-retries — Optuna retries are explicit ask-and-tell, terraform re-applies are human-triggered | Surface failures, let the operator decide; maybe a "retry once" explicit action |

### FC7 — Dataset Download Manager with Verification

#### Table Stakes

| Feature | Why Expected | Complexity | Notes + Tool Evidence |
|---------|--------------|------------|-----------------------|
| Presence table with authoritative source column | Registry `download_url` is declared the single authority (requirements doc §3.2) | LOW | Filter/join over registries + n_audit — presentation only |
| Download with per-item progress | `hf download` shows multi-file progress bars; tqdm idiom everywhere | MEDIUM | ModelScope SDK/CLI channels exist; progress plumbing per channel (SDK callbacks vs subprocess parsing) is the cost |
| Post-download verification against expected content | `hf download --dry-run` reports cached-vs-to-download per file (the habit of verifying before trusting); project's n_audit row-count reconciliation is the verification contract | MEDIUM | Re-run audit after fetch: row counts per split vs n_audit baseline; mismatch = mark not-verified, block selection for launch |
| Persistent, resumable queue (survives TUI restart) | Maintainer answer to open Q4: "需要" (needed); huggingface_hub `local_dir` mode persists `.cache/huggingface` metadata precisely so re-runs skip completed files (official guide) | MEDIUM-HIGH | Queue = JSON with per-item state machine (absent → queued → downloading → verified/failed) stored under the config dir; resume = re-read queue + skip completed |
| Download dry-run (what would be fetched, sizes) | `hf download --dry-run` + programmatic `dry_run=True` → `DryRunFileInfo` (size/cached/would-download) is the model | MEDIUM | For ModelScope: HEAD the raw API for sizes or list-before-fetch; show table before starting |

#### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Row-count reconciliation as the verification gate (not just file existence) | Stronger than any surveyed tool's check (HF checks bytes/etag; nobody checks semantic content); catches truncated/partial dataset uploads | MEDIUM | n_audit baseline already exists — this is a genuine cheap differentiator |
| Zenodo bulk bundle as fallback source (record 19135551, when public) | Requirements doc §3.2; alternate channel for whole-corpus fetch | MEDIUM | Keep registry download_url authoritative; bundle is a source option, not a second authority |

### FC8 — Template Import/Export

#### Table Stakes

| Feature | Why Expected | Complexity | Notes + Tool Evidence |
|---------|--------------|------------|-----------------------|
| Export current selection + config as one shareable file | wandb sweeps: the YAML *is* the sharing artifact (`wandb sweep file.yaml` creates from it); accelerate configs are YAML files the docs explicitly say to "copy and send across your nodes" | MEDIUM | JSON (project convention) containing models × tasks × seeds × PEFT × variant × GA/epochs + provenance (generator version, date) |
| Import with validation against current registries | lm-eval `validate` subcommand checks before running; unknown names must fail loudly, not silently drop | MEDIUM | Reject unknown model/task names with a diff-style report (which names, why — not in registry); validate guard combos (probe-ineligible) same as FC2 |
| Interop/round-trip with `sweep_priorities.json` tier structure | Requirements doc §3.1 explicitly demands compatibility or conversion | MEDIUM | Either embed tiers in the template or ship a converter both ways; pick one representation to avoid dual maintenance |
| Schema version field | Every durable config format surveyed has one (wandb config keys, accelerate YAML keys are versioned by release) | LOW | `schema_version` at top; reject unknown-major on import |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Opaque binary/saved-state "plan" files as the sharing format | terraform `-out` precedent might suggest it | Terraform's own docs warn the plan file is opaque, contains full config + secrets in cleartext — explicitly not a sharing artifact | Share human-readable, diffable JSON; the saved-plan launch concept (FC3) is internal state, templates are the share format |
| Macro/templating language inside templates (`${...}` substitution à la wandb `command` macros) | Flexibility | wandb needs macros because it synthesizes commands; here the TUI is the renderer — macros add a parser, injection surface, and debugging pain for zero operator value | Explicit fields, no string interpolation |

---

## Feature Dependencies

```
[Registries: models_info / datasets_info]  ──exists──>  (FC1 selection, FC2 validation, FC8 import validation)
[n_audit.json]              ──exists──>  (FC1 presence column, FC7 verification gate)
[ModelScope channels]       ──exists──>  (FC7 downloads)
[env_smoke.py]              ──exists──>  (FC3 preflight gate)
[run_sweep --dry-run]       ──exists──>  (FC3 preview, FC2 cost preview)
[run_sweep --from-failures] ──exists──>  (FC6 re-run)
[sweep_failures.json / trainer_state.json / output dirs] ──exists──>  (FC4 polling monitor)
[finetune_config.yaml]      ──exists──>  (FC2 defaults)

[FC1 selection set] ──requires──> registries + n_audit
[FC2 config form]   ──requires──> FC1 (what is being configured) + registries/enums
[FC8 templates]     ──requires──> FC1 + FC2 (exports their combined state); interop with sweep_priorities.json
[FC3 launch gate]   ──requires──> FC2 + env_smoke + dry-run; ──enhances──> saved-plan exact-cell launch
[FC7 download mgr]  ──requires──> registries + channels + n_audit; ──enables──> FC1 full-selection launchability (missing data blocks)
[FC4 monitor]       ──requires──> durable artifacts (independent of FC3! can attach to externally-launched sweeps)
[FC5 log tailing]   ──requires──> TUI-owned subprocess (FC3 launch) OR persisted per-cell log files (file-tail mode also serves FC6)
[FC6 failure re-run]──requires──> FC4 (failure visibility) + FC5 (log access) + --from-failures
[P4 multi-GPU]      ──requires──> FC3+FC4 validated on single GPU (hard gate per PROJECT.md decision) + worker sharding design
[FlopsCounter port] ──independent work package──> benefits FC4 (per-cell FLOPs display) and E2' correctness (per PROJECT.md)
```

### Dependency Notes

- **FC4 is deliberately launch-independent:** the monitor polls files, so it works for TUI-launched *and* externally-launched (cron/tmux/nohup) sweeps — the Optuna attach-to-storage model. This decoupling is the single most consequential architecture decision in the milestone; it makes every other feature cheaper (TUI restart never loses the view).
- **FC5 has two modes with different prerequisites:** streaming (needs FC3-launched subprocess) vs file-tail (needs per-cell persisted logs). File-tail mode is also what FC6 failure review consumes — persisting logs to disk serves both and is cheaper than pure-pipe streaming alone.
- **FC7 blocks honest FC3:** launching a selection referencing missing datasets should route through the download manager (or explicitly confirm-and-skip), not fail deep in the sweep.
- **FC1/FC2/FC8 share the validation layer:** registry-name checking, guard rules (probe eligibility), and template validation are one module used three times.

---

## MVP Definition

### Launch With (P1–P3 skeleton per requirements doc §6)

- [ ] FC1 filterable mark-set selection with presence columns + preset groups (tier structure) — the core operator gesture; everything else configures or observes a selection
- [ ] FC2 run-config form with registry validation, defaults from `finetune_config.yaml`, derived-value preview (adapter alias, GA rule) — cannot launch safely without it
- [ ] FC8 template export/import with registry validation + priorities interop — explicitly required (unchecked box in requirements §3.1); shares the FC2 validation module so cost is mostly amortized
- [ ] FC3 launch gate: env_smoke preflight → dry-run cell table → ModalScreen confirm → typed-confirm for full E2' — the safety contract of the milestone
- [ ] FC5 log tailing for TUI-launched cells (with the buffering fix) + per-cell log persistence — without visible logs, operators will drop back to tmux and the TUI dies in practice
- [ ] FC4 polling monitor: state-colored cell table, counts header, attach mode, resume recognition — the reason a TUI beats a shell loop
- [ ] FC6 failure list + log drill-down + confirmation-gated `--from-failures` re-run — the loop that closes monitoring into recovery
- [ ] FC7 download manager: presence table, queued downloads with progress, n_audit verification, persistent queue — required before any full-grid selection is launchable

### Add After Validation (P4 / v1.x)

- [ ] Multi-GPU orchestration view (worker table, sharding map, per-worker isolation re-run) — hard-gated on single-GPU validation (PROJECT.md decision)
- [ ] Saved-plan exact-cell launch (terraform `-out` analog) — after basic gate proves out
- [ ] Per-cell performance drill-down in monitor — once E2'-scale data flows
- [ ] Auto-GA (`--effective-batch`) surface — after the pipeline flag lands (open Q7 decision)
- [ ] DDP/torchrun layer — complements model sharding; decide per-model-size need at discuss time (requirements §3.4 cross-check)

### Future Consideration (defer / out)

- [ ] Web read-only mirror of TUI state (open Q5 "可要可不要") — the static leaderboard already serves public visibility; defer
- [ ] Optuna-style analytics over historical runs — not this milestone's value proposition
- [ ] Zenodo bulk bundle — when the record goes public (external dependency)

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Phase Fit |
|---------|------------|---------------------|----------|-----------|
| FC1 selection (list+filter+marks+presets+presence) | HIGH | LOW-MEDIUM | P1 | P1 TUI 地基 |
| FC2 config form + validation + profiles | HIGH | LOW-MEDIUM | P1 | P1 |
| FC8 template import/export + priorities interop | HIGH | MEDIUM | P1 | P1 (validation module shared with FC2) |
| FC3 launch gate (env_smoke + dry-run + confirm + E2' typed gate) | HIGH | LOW (surfacing existing seams) | P2-P3 | P3 单卡启动 (gate design lands with launch) |
| FC5 log tailing + per-cell log persistence | HIGH | MEDIUM | P2-P3 | P3 监控 |
| FC4 polling monitor + attach mode | HIGH | MEDIUM | P3 | P3 监控 |
| FC6 failure review + re-run | HIGH | LOW-MEDIUM | P3 | P3 |
| FC7 download manager + verification + persistent queue | HIGH | MEDIUM-HIGH | P2 | P2 数据管理器 |
| Matrix overview pane (read-only) | MEDIUM | MEDIUM | P3 | polish, post-core |
| Saved-plan launch | MEDIUM | MEDIUM | P3+ | post-validation |
| Multi-GPU orchestration | HIGH (when multi-GPU) | HIGH | P4 | P4, hard-gated |
| Web mirror | LOW | MEDIUM | defer | out of milestone focus |

**Priority key:** P1 = must have earliest (foundation + explicitly-required template feature); P2 = data readiness before launch; P3 = launch/monitor/recover loop; P4 = scale-out after single-GPU proof.

---

## Competitor Feature Analysis

| Feature | k9s | Optuna Dashboard | lm-eval CLI | accelerate CLI | hf hub CLI | Our Approach |
|---------|-----|-------------------|-------------|----------------|------------|--------------|
| Large-set selection | `:resource` + `/` filter + space mark-set | n/a (trials not user-selected) | `--tasks` list/wildcard/tags | n/a (config declares) | repo/file args + `--include` globs | Filterable model/task tables + mark-set + tier presets |
| Config surface | skins/views YAML (external files) | n/a | `--model_args` k=v; `--config` YAML | interactive questionnaire → persisted YAML; `--config_file` | flags | Form validated against registries; profiles persisted as JSON |
| Pre-launch check | n/a | n/a | `validate` subcommand; `write_out.py`; `--limit` | `accelerate config` before launch | `--dry-run` size/cached table | env_smoke gate + run_sweep `--dry-run` cell table |
| Confirmation gate | ctrl-d confirm vs ctrl-k no-confirm | n/a | n/a | n/a | n/a | ModalScreen confirm; typed phrase for E2' full sweep |
| Live state table | container status columns, continual watch | trial table, state chips, filter-by-state | n/a | n/a | n/a | Cell table polled from sweep artifacts, attach-mode |
| Refresh model | k8s API watch | poll storage, ~5s adjustable | n/a | n/a | n/a | poll `sweep_failures.json`/dirs at 2-5s, adjustable + manual |
| Log access | `l` logs / `p` previous | n/a (artifact URLs) | `--log_samples` files | console only | n/a | RichLog tail of running cell; file-tail for failed cells |
| Failure handling | faults view, describe, delete/recreate | FAIL filter; retry via ask-and-tell (not UI-first-class) | rerun command manually | rerun manually | redownload | failure list → log drill-down → gated `--from-failures` |
| Download mgmt | n/a | n/a | task data auto-fetch | n/a | `--dry-run`, progress, local_dir resume metadata | ModelScope queue + n_audit row-count verification + persistent queue |
| Template sharing | YAML configs copyable | n/a | YAML task/config files | "copy config across nodes" (docs) | n/a | JSON run-config template, versioned, registry-validated on import |
| Testing story | n/a | n/a | n/a | n/a | n/a | Textual Pilot `run_test()` headless + pytest (official testing guide) — CI-compatible, no GPU/terminal needed |

**Real-world Textual-for-exactly-this exemplars found:** NVIDIA physicsnemo-curator ships `PipelineProgressApp`, a Textual progress app for pipeline runs; `c3t` (club-3090) is a Textual GPU test-console. Existence proofs that Textual handles long-running pipeline monitoring (LOW-MEDIUM confidence, search-level evidence).

---

## Gaps to Address (needs phase-level research)

- **ModelScope progress plumbing specifics:** whether the SDK exposes per-file progress callbacks vs requiring subprocess tqdm parsing — affects FC7 estimate (MEDIUM vs HIGH). Phase 2 research item.
- **Textual version pin + widget set:** Textual 6.x current line; exact version choice and CSS/theme approach is STACK.md territory (parallel researcher), not settled here.
- **`--effective-batch` semantics** (open Q7): pipeline-side flag design (GA = max(1, N//batch_size), default 16) is a pending decision — TUI only surfaces it.
- **Multi-GPU scheduling strategy** (open Q3): static model sharding vs dynamic queue — P4 discuss item; monitoring UI shape depends on it.
- **Per-cell log persistence format:** rotation/naming convention needed before FC5 file-tail mode is buildable (trivial but must be decided in P3 planning).
- **Optuna Dashboard failed-trial re-run** is not first-class in its UI (retry is programmatic ask-and-tell) — confirms our one-key re-run is a deliberate improvement, not a copied pattern; test its UX carefully in UAT.

## Sources

Official documentation read directly (primary, MEDIUM):
- Textual DataTable widget — https://textual.textualize.io/widgets/data_table/
- Textual Screens/ModalScreen guide — https://textual.textualize.io/guide/screens/
- Textual Workers guide — https://textual.textualize.io/guide/workers/
- Textual Testing (Pilot/run_test) — https://textual.textualize.io/guide/testing/
- rich Progress — https://rich.readthedocs.io/en/stable/progress.html
- accelerate launch tutorial — https://huggingface.co/docs/accelerate/en/basic_tutorials/launch
- lm-evaluation-harness README (CLI) — https://github.com/EleutherAI/lm-evaluation-harness
- huggingface_hub download guide — https://huggingface.co/docs/huggingface_hub/en/guides/download
- terraform plan — https://developer.hashicorp.com/terraform/cli/commands/plan
- k9s README — https://github.com/derailed/k9s
- nvitop README — https://github.com/XuehaiPan/nvitop
- gpustat README — https://github.com/wookayin/gpustat

Cross-checked secondary (MEDIUM):
- Optuna `TrialState` reference — https://optuna.readthedocs.io/en/v3.3.0/reference/generated/optuna.trial.TrialState.html; optuna-dashboard trial management — https://deepwiki.com/optuna/optuna-dashboard/3.2-trial-management-components; issue #820 — https://github.com/optuna/optuna-dashboard/issues/820; Tunny visualize docs (reload-interval indicator) — https://tunny.hrntsm.com/docs/v0.12/optimize-window/visualize-tab
- wandb sweep config keys — https://docs.wandb.ai/models/sweeps/sweep-config-keys
- Textualize discussions #245 (streaming pattern) — https://github.com/Textualize/textual/discussions/245; #3788 (buffering pitfall) — https://github.com/Textualize/textual/discussions/3788; textual-shell async-subprocess docs — https://jason-lawrence.github.io/textual-shell/commands/bash/
- Textual source (no public run_process; internal-only) — https://github.com/Textualize/textual/blob/main/src/textual/app.py (verified 2026-10-11)

Single-source / training-data only (LOW, flagged in text):
- Textual dashboard.py demo widget composition (not directly fetched; 404 on example paths)
- physicsnemo-curator PipelineProgressApp, c3t console — search-result existence proofs

---
*Feature research for: dnallmmark v1.2 TUI milestone*
*Researched: 2026-10-11*
