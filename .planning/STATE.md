---
gsd_state_version: "1.0"
milestone: v1.2
milestone_name: TUI任务
current_phase: 11
current_phase_name: Run Config, Launch Gates & Single-GPU Monitoring
current_plan: Not started
status: planning
stopped_at: Phase 10 complete, ready to plan Phase 11
last_updated: "2026-10-12T23:29:39.275Z"
last_activity: 2026-10-13
last_activity_desc: Phase 10 complete, transitioned to Phase 11
state_head: d5feb38090033a9831575108a4517630fdb86738
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 25
  completed_plans: 25
  percent: 67
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-11)

**Core value:** Every number on the public leaderboard is correct and reproducible from code that external reviewers can trust. (v1.2 extension: operators drive the platform confidently from one terminal console without losing CLI parity.)
**Current focus:** Phase 11 — Run Config, Launch Gates & Single-GPU Monitoring

## Current Position

Phase: 11 — Run Config, Launch Gates & Single-GPU Monitoring
Current Plan: Not started
Total Plans in Phase: 0 (not yet planned)
Status: Ready to plan
Last activity: 2026-10-13 — Phase 10 complete, transitioned to Phase 11

Progress (v1.2): [██████░░░░] 67% (4/6 phases; 25/25 planned plans)

## Performance Metrics

**Velocity (v0.7.1, archived):**
- Total plans completed: 24 (6 phases)
- Average duration: ~24 min/plan
- Total execution time: ~9.7 hours

**By Phase (v0.7.1):**

| Phase | Plans |
|-------|-------|
| 01 / 02 / 03 | 3 / 3 / 4 — all complete |
| 04 / 05 / 06 | 5 / 4 / 5 — all complete |

**v1.2:** Phase 7 complete (6 plans, 2026-10-11); Phase 8 plans 1-5 of 7 complete (08-01..08-05).

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 07 P01 | 13 min | 3 tasks | 7 files |
| Phase 07 P02 | 11 min | 3 tasks | 5 files |
| Phase 07 P03 | 12 min | 3 tasks | 2 files |
| Phase 07 P03 | 12 min | 3 tasks | 2 files |
| Phase 07 P04 | 8 min | 2 tasks | 2 files |
| Phase 07 P05 | 10 min | 3 tasks | 10 files |
| Phase 07 P06 | 5 min | 3 tasks | 1 files |
| Phase 08 P08-01 | 17 min | 2 tasks | 2 files |
| Phase 08 P08-02 | 84 min | 2 tasks | 11 files |
| Phase 08 P08-03 | 15 min | 1 tasks | 8 files |
| Phase 08 P08-04 | 32 min | 3 tasks | 13 files |
| Phase 08 P08-05 | 26 min | 2 tasks | 7 files |
| Phase 08 P08-06 | 43 min | 2 tasks | 6 files |
| Phase 08 P08-07 | 79 min | 3 tasks | 13 files |
| Phase 09 P09-01 | 47 min | 3 tasks | 7 files |
| Phase 09 P09-02 | 19 min | 3 tasks | 4 files |
| Phase 09 P09-03 | 44 min | 3 tasks | 13 files |
| Phase 09 P09-04 | 41 min | 3 tasks | 4 files |
| Phase 09 P09-05 | 95 min | 3 tasks | 3 files |
| Phase 09 P09-06 | 91 min | 3 tasks | 6 files |
| Phase 10 P01 | 43m | 3 tasks | 4 files |
| Phase 10 P02 | 30 min | 3 tasks | 2 files |
| Phase 10 P03 | 25 min | 3 tasks | 5 files |
| Phase 10 P04 | 58 min | 3 tasks | 8 files |
| Phase 10 P05 | 31min | 2 tasks | 5 files |
| Phase 10 P06 | 41min | 3 tasks | 4 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table. Recent decisions affecting current work:

- Roadmap v1.2 revision (maintainer, 2026-10-11): custom entries split along the maintainer-drawn seam — the pipeline-side registry overlay (CUST-05) joined Phase 7 (same run_sweep/run_finetune files, same byte-identical-when-absent discipline as argv parity, must precede wizard consumption); the wizard surface (CUST-01..04, CUST-06) is a dedicated Phase 9 directly after the selection foundation it marks; downstream phases renumbered 9→10, 10→11, 11→12 (free — zero plans existed)
- Custom/official registry separation is binding (maintainer refinement: 自定义不与官方放在一起，免得冲突): wizards write only user-owned `~/.config/dnallmmark/custom_{models,datasets}.json`; official `pipeline/{models,datasets}_info.json` never written by custom flows; overlay fails fast on custom-key collision with official; absent custom files = byte-identical behavior, existing tests untouched — recorded as binding constraint 11 in ROADMAP.md
- Roadmap v1.2 (pre-revision): pipeline enablement → TUI foundation → data manager → config/launch/monitor (single-GPU) → multi-GPU + extras; Phase 12 hard-gated on Phase 11 validation (maintainer sequencing 单卡→多卡); requirement count corrected 28 → 32 → 38 (CUST category added by revision)
- Roadmap v1.2: all three PIPE-* plus CUST-05 in Phase 7 — pipeline-side verification deliberately uncoupled from TUI phases; PIPE-02 folded there per coarse granularity (research sketched it as a separate "Phase 2.5")
- Roadmap v1.2: WEB-01 + TEST-01 attached to Phase 12 (canonical screens are final only after multi-GPU views exist; keeps Phase 11 focused on the bounded-smoke gate). TEST-01 follows the requirement (official snapshot goldens) over the research preference (Pilot-only assertions) — requirement wins
- Carried binding constraints (full list in ROADMAP.md): E2' maintainer dual-gate; CI GPU/dnallm-free with textual-the-library allowed in a CPU test lane (ratify in Phase 8 discuss); DNALLM repo read-only; CLI parity rule; TUI orchestrates never computes; ruff + ty gates from Phase 7 on
- [Phase 07]: flops_report.json v1 schema published exactly as derived (maintainer ratified publish-as-derived at the 07-01 Task-1 checkpoint, 2026-10-11); D-27 one-way contract — field names immutable downstream
- [Phase 07]: flops_report layer_details/total_flops_exact values typed number (not integer): the verbatim HyenaFilter FFT formula emits fractional FLOPs, and an integer map would reject legitimate writer output (Rule-1; every ratified field name unchanged)
- [Phase 07]: FlopsCounter ported behind lazy _torch_nn/_torch seams with no module-top torch import — the CPU dev/CI lane imports and stub-tests the full 20+ architecture dispatch (PIPE-01 criterion 2)
- [Phase 07]: CUST-05 registry overlay seam landed: DNALLMMARK_CUSTOM_REGISTRY_DIR whole-dir override (D-07 覆盖整个目录 — no suffix on the env value; the dnallmmark join applies to the XDG/~/.config bases only); custom entries add-only, collision fails fast naming key + both file paths
- [Phase 07]: platformdirs refinement: hand-rolled env>XDG>home resolver in registry_loader (platformdirs undeclared in every CPU-side group — RESEARCH Pitfall 2; reserved for Phase 8 [tui] by constraint 10); identical Linux path, Phase 8 may consolidate behind the seam
- [Phase 07]: 07-03 PIPE-02 argv threading: the four sweep flags are pure pass-through with zero GA arithmetic (GA=max(1, N//bs_new) stays child-side, D-10/D-16); underscore names only, bare --effective_batch_size=16, absent flag = zero argv elements and zero manifest keys (D-11/D-12/D-13)
- [Phase 07]: D-14 implemented as sweep-owned shallow collect-all (_validate_subset_file: readable-JSON/object/registry-key/int-list with bool exclusion) against the overlay-merged registry view; child validate_subset_file stays authoritative — defense-in-depth, no shared import (sweep stays stdlib-only headless-importable)
- [Phase 07]: Manifest records present flags in cells only (D-13); run_record.json untouched (D-02 spirit); dry-run path now routes through _manifest_payload so planned and executed cells record identically; byte-determinism tests green unmodified
- [Phase 07]: 07-04 PIPE-01 integration: FLOPs always-on via the pre-training calibration slot (count_split_tokens -> unconditional FlopsCounter -> single no_grad forward via calibration_forward -> remove_hooks BEFORE the DNATrainer ctor) + a single post-success flops_report.json write ordered final_metrics < flops_report < trainer_state marker (WR-13 three-artifact chain); run_record/final_metrics payload contracts untouched (D-01/D-02)
- [Phase 07]: 07-04 hardware capture (D-05): gpu_device verbatim from torch.cuda.get_device_name() (no enum normalization, 5090D/4090D pass through), train_time from metrics.get('train_runtime') (None-tolerant), max_mem_gb from the peak-memory counter read at write time inside the rank-0 success block BEFORE trainer.evaluate() — scopes the captured peak to training
- [Phase 07]: [Phase 07]: 07-05 D-04 closed: dnallmmark_pipeline.py deleted (final commit 1b74037e — git history is the reference); the five parity expectations in test_run_finetune_contracts.py are self-contained sha-documented verbatim literals; zero live-code references remain and .claude/CLAUDE.md's FLOPs reference of record is pipeline/flops_counter.py
- [Phase 07]: [Phase 07]: 07-05 provenance convention: after a D-04-style deletion, live-code/test comments cite the deleted source by description + final commit sha, never by live path (the Task-1 comment template vs Task-2 zero-grep-gate reconciliation)
- [Phase 07]: 07-06 runtime proof: bounded GB10 smoke (plant-dnabert-6mer x iDNA_ABF_datasets__5mC, 1 epoch, default mode, 77s wall, 1.56GB peak) emitted flops_report.json with all six D-23 criteria green — ratio 0.332 vs HF total_flos (the ~1/3 fwd-only expectation), gpu_device 'NVIDIA GB10' verbatim, uncovered_layers empty; PIPE-02 proven live via dry-run (present flags recorded, absent flags leave no keys, D-13)
- [Phase 07]: 07-06 evidence discipline: real run artifacts stay gitignored under pipeline/finetuned/ (D-26) — the committed evidence is the SUMMARY's pasted key fields + mechanical assertion outputs (D-25); the bounded-smoke evidence shape is the template for Phase 11's bounded smoke
- [Phase 08]: 08-01 D-02 landed: env_smoke kernels return frozen CheckResult(name/ok/lines) with zero printing; main() is the sole renderer (_emit + two segment loops); CLI stdout and 0/1 exit proven byte-identical by a golden characterization suite (S1/S2/S3) recorded from live runs + live before/after diff + the three untouched grep-lock tests
- [Phase 08]: 08-01 check_peft stays byte-exact un-annotated (def check_peft(): pinned by test_env_smoke_peft_check_is_gating); torch-unavailable cuda/matmul become ok=False empty-lines CheckResult placeholders (same two-failed-groups semantics, type-clean list)
- [Phase 08]: 08-02 package legitimacy gate closed (maintainer verdict 2026-10-11, delegation on record): textual 8.2.8 (Textualize), platformdirs 4.13.0 (tox-dev, signed provenance — same-day release accepted), pytest-asyncio 1.4.0 (pytest-dev) all APPROVED via PyPI page + JSON API; uv.lock pins exactly these versions; verdict lines recorded verbatim in 08-02-SUMMARY.md
- [Phase 08]: 08-02 typecheck lane gains --group tui (Rule 3, empirically proven): ty cannot resolve textual's py.typed types in a fresh env — make typecheck failed tui/app.py with unresolved-import in exactly CI's lint-typecheck state, so the recipe installs the maintainer-approved [tui] group in that existing CPU static lane; NO replace-imports-with-any entry (real types, per RESEARCH); data/gpu lanes still never see textual; ci.yml byte-identical
- [Phase 08]: 08-02 spine landed: [tui] group (exactly textual>=8.2,<9 + platformdirs>=3.6,<5), make tui (--group tui --group gpu, Pitfall 10), PHASE8_TUI wildcard lint guard (later tui files join coverage with zero Makefile edits), asyncio_mode=auto (A3 proven — 560 sync tests green), tui/ skeleton with the services-textual-free contract declared and the __file__-derived REPO_ROOT bootstrap; uv sync for the tui group must use --inexact (plain sync is exact and strips the GB10 GPU stack + dnallm)
- [Phase 08]: 08-03 tracer landed: console boots on the env-check shell (seven pending rows, main() kernel order, stable kernel-id row keys) and the first service crosses the tui-to-pipeline seam (load_registry_counts -> RegistryCounts(62, 50) from the real overlay-merged registries); services-textual-free import lock green and non-vacuous from the first module
- [Phase 08]: 08-03 Rule 3: Makefile test-fast + ci gain --group tui — pytest imports every collected module before -m filtering, so the first textual-importing test file would break both lanes on a fresh dev-only venv; every pytest lane now carries textual-the-library (D-01 posture), data/gpu lanes untouched
- [Phase 08]: 08-03 RUF012 resolved by mirroring the App base ClassVar annotations verbatim (BINDINGS: ClassVar[list[BindingType]], SCREENS: ClassVar[dict[str, Callable[[], Screen[Any]]]]) — framework-read class constants, truthful typing, no noqa
- [Phase 08]: 08-04 env/registry services landed: five textual-free services — settings (D-04 XDG state/config split via platformdirs + whole-dir env overrides + atomic writes), env_check (D-05 same-local-day cache + whole-item persistence over the imported env_smoke kernels, D-02 import-only), env_gate (D-09 pure judgment; CRITICAL = six ids incl. numpy — the plan action's five-id list omitted numpy, resolved as a plan-text slip per the seven-coverage contract), quick_check (six non-matmul ids, computed on demand, never persisted), registries (canonical entries + MODEL_CARD_* casing-twin constants + presence_for pure data from n_audit, D-08); zero pipeline changes (D-10)
- [Phase 08]: 08-04 seams for the rest of Phase 8: default_kernels() is the one shared env_smoke sequence (main() order, torch-gate two-False fallback) consumed by run_full_check, quick_check's subset, and the 08-06 worker; run_full_check(kernels=None, state_path=None, now=None) grew explicit persistence-target/moment params; canonical entry vocabulary models {key,type,species,size_m,card} / datasets {key,category,type,metric,card} + MODEL_CARD_* casing constants (committed card twins genuinely diverge — prokbert-mini Mean_token_length 6 vs mean_token_len 1) are the 08-05 filter / 08-07 column contract; presence_for's four statuses (present/missing/unknown/unavailable) with exact integer rows
- [Phase 08]: D-07 ratified verbatim 2026-10-11 (maintainer: ratify): schemas/run_template.json field set frozen as proposed — schema_version const 1, models/tasks minItems 1 unique, seeds default 42/43/44, peft none/lora/ia3, config_variant default/head/probe/curve, optional curve_fractions/subset_file/effective_batch_size(>=1)/num_train_epochs(>0)/cache_dir; GA semantics in $comment (GA = max(1, effective_batch // batch_size), maintainer default 16, small-model batch 64 -> GA 1); custom presets -> presets.json under XDG config root; ONE-WAY from landing — field names are a published contract consumed by the Phase 11 run-config screen
- [Phase 08]: 08-05 tier interop encoding: template_to_tiers emits one tier of explicit cross-product pairs (a bare priorities name covers the model's EVERY task — it would cover unselected tasks too); tiers_to_template is registry-blind, preserves file order first-occurrence, and refuses names-only tiers files (minItems-1 tasks would carry nothing); both compositions preserve model/task membership exactly
- [Phase 08]: 08-05 filter grammar: axis names are the strict lowercase five-axis vocabulary (models species/type/size — size maps to the canonical size_m field; datasets category/type/metric); values and bare substrings match case-insensitively over key + display fields (never card); unknown-axis tokens drop from applied terms into diagnostics; selection.py imports NOTHING from registries (entries/keys arrive as parameters, 08-07 wires them)
- [Phase 08]: 08-05 jsonschema lane note: tui/services/templates.py imports jsonschema at module top level — dev/CI test + typecheck lanes carry it (dev group), the make tui display lane does not yet import the module; 08-07 must add jsonschema>=4.26.0 to the [tui] group when the selection screen wires template import (same locked range as dev)
- [Phase 08]: 08-06 env screen landed: EnvCheckServiceProtocol is the injection seam (structural — real EnvCheckBackend adapter + Pilot fakes conform); the adapter lives in the screen module because the plan's file list forbids new service files, and it is thin delegation glue over the tested 08-04 service
- [Phase 08]: 08-06 worker shape: CheckItemChecking posted BEFORE each kernel call makes the pending->checking->done progression observable per row; the gated-fake (threading.Event) Pilot test doubles as the T-08-07 UI-responsiveness proof; kernel() exists exactly once in the screen, inside the exclusive @work(thread=True) worker
- [Phase 08]: 08-06 presentation derivations: the summary column is the kernel's own first detail line (PASS:/FAIL: prefix stripped, byte-stable D-02 text); the routing count n counts the dataset_dirs '  - ' listing lines; the UI-SPEC mockup's summaries were hand-abbreviated sketches
- [Phase 08]: 08-06 textual 8.2.8 facts (probe-pinned): Static.content is the content read API (no .renderable); from textual import work (no textual.work module — research A1 path was wrong); the focused DataTable consumes enter (RowSelected) so the screen enter Binding serves the Footer hint + unfocused path; plain-Screen push/pop hides everything beneath (the min-size guard mechanism)
- [Phase 08]: 08-06 styles decisions: zero hex (the optional dnallmmark teal theme deliberately not landed — default tokens satisfy the contract); the xl 12-cell token is skipped because Textual CSS has no media queries; the drill-down RichLog max-height 20 is a scroll bound, not a spacing token (the prohibition governs paddings)
- [Phase 08]: 08-07 mark-set home: marks live in app-state sets constructed once on the composition root and passed BY REFERENCE through build_selection_screen / the v push — selection/matrix are deliberately NOT zero-arg SCREENS slots (a slot-built screen would carry fresh sets and silently lose the SEL-01 persistence guarantee; the 08-06 slot comment is superseded)
- [Phase 08]: 08-07 model presence = the unknown copy (◌ 未知): the real backend fills presence per DATASET key only (models are not n_audit subjects) — the UI-SPEC mockup's per-split counts on model rows were a hand-sketch error; dataset rows carry the counts
- [Phase 08]: 08-07 80-column budget: column widths sum 66 per view (66 + 12 cell-padding + 2 scrollbar == 80, probe-validated and backstop-pinned); the selection footer is compact with show_command_palette=False (9 binding labels exceed 80 in the default style; ctrl+p keeps working, only the hint hides)
- [Phase 08]: 08-07 jsonschema>=4.26.0 joined the [tui] group (the 08-05 handoff flag closed): the selection backend imports tui.services.templates at module top, so the make tui display lane needs it — same locked range as dev
- [Phase 08]: 08-07 gap-filler copy landed and documented: SEL_PRESENCE_UNKNOWN (the four-status vocabulary lacked render copy), SEL_PRESET_SAVED / SEL_TEMPLATE_IMPORTED (the truths pin 'a toast fires' but only the applied/exported toasts were worded), and SEL_CLEAR_MARKS_CONFIRM landed unsurfaced per the contract's 'if surfaced' (the keyboard map defines no clear binding in Phase 8)
- [Phase 08]: 08-07 Phase 8 console complete: selection + matrix + env surfaces composed over the shared mark sets, both 80-column backstops and the cross-screen integration green — roadmap criteria 4 and 5 TRUE (SEL-01..04 + I18N-01 closed with 167 green tests/tui, make test 728, lint/typecheck clean, CI byte-untouched)
- [Phase 08]: UAT width feedback (2026-10-12): selection key columns widened to fit the longest committed registry keys (_MODEL_KEY_W 25→46, _DATASET_KEY_W 20→68; budget 80→128/101) — narrower terminals h-scroll (matrix precedent), 80x24 min grid intact, full keys always in row detail. Supersedes the 80-column pin recorded at 08-07. — UAT width feedback (2026-10-12): selection key columns widened to fit the longest committed registry keys (_MODEL_KEY_W 25→46, _DATASET_KEY_W 20→68; budget 80→128/101) — narrower terminals h-scroll (matrix precedent), 80x24 min grid intact, full keys always in row detail. Supersedes the 80-column pin recorded at 08-07.
- [Phase 09]: 09-01: custom-registry store = single write seam (land/undo/set_enabled through settings.atomic_write); land relativizes absolute paths (Pitfall 4), stamps Model_name/Dataset_name = key (Pitfall 6/11), drops the wizard key field, coerces Train/Dev/Test ints with bool excluded
- [Phase 09]: 09-01: METRIC_REGISTRY = frozen 28-name SUITE_CANONICAL twin in tui/services/custom_validation, parity-locked by a tier-1 test importing export_runs via the tests/conftest.py sys.path; the service module never imports it (AST import lock) — IN-03 single authority preserved
- [Phase 09]: 09-01: one-defect-one-problem collect-all semantics — numeric checks skip absent/empty values (the required check owns them), enum checks skip empty injected vocabularies; declared Train/Dev/Test are DERIVED from split counting (the wizard never collects them) and must equal well-formed row counts when present
- [Phase 09]: 09-01: schemas/custom_registry.json = per-ENTRY contract (plain {key: entry} file top level, NO envelope; optional per-entry schema_version const 1; quirks model-only / label_column dataset-only; required = wizard-required subset; field types probed from the official 62/50)
- [Phase 09]: [Phase 09]: 09-02: D-09 filter = skip iff isinstance(entry, dict) and entry.get('enabled') is False — the isinstance guard preserves the pre-D-09 merge of non-object entry values (a new AttributeError there would crash formerly accepted input); skip sits after the collision loop so disabled shadow attempts still fail fast
- [Phase 09]: [Phase 09]: 09-02: gauntlet counterpart resolution is read-time deterministic (first official Train-truthy task / first official model key, read directly from the official files — overlay state can never leak a custom key into the slot); corrupt existing-custom registry = failed item launching nothing
- [Phase 09]: [Phase 09]: 09-02: gauntlet verdicts from parsed artifacts only (manifest planned cells / n_audit fields — exit-0-but-absent is a FAIL); the service carries zero f-strings and zero copy (detail tokens are data: planned_cells=N, Train_mismatch_declared=N_measured=M); audit leg doubly isolated (candidate-only registry + empty overlay env) with all five output flags temp — committed artifacts hash-pinned clobber-safe
- [Phase 09]: [Phase 09]: 09-03 nav shell landed: top-bar slot format is the D-13 verbatim digit+label attachment (1环境检查, 未开放 attached) — the only fixed-vocabulary formulation fitting 80 columns with the ◆ prefix (78 cells, Pilot-asserted); digit bindings are show=False plain per-screen bindings (the top bar carries the digit labels; never priority)
- [Phase 09]: [Phase 09]: 09-03: tui/screens/nav.py is a NEW screens-tier chrome module (12th file over the deliberate 11-file budget, Rule 3): bars cannot live in app.py (screens import them; app imports screens — a cycle); binding_row moved there as the single key-map projection the help modal and bottom bar share
- [Phase 09]: [Phase 09]: 09-03 probe-pinned textual 8.2.8 facts: (a) switch_screen away from the BOOT screen raises IndexError (missing result-callback bookkeeping) — one _push_result_callback shim in App.on_mount; (b) rich Text spans styled with $token strings crash the Static render path (MissingStyle) — keycap keys resolve app.current_theme.accent at mount, labels use rich dim; zero hardcoded hex
- [Phase 09]: [Phase 09]: 09-03 about derivations: official counts read the committed registries directly (official-only 62/50 — the overlay-merged view would count customs into the 官方 row); 自定义 counts via the 09-01 direct store read; deps tolerance is per-package (one exploding probe → 未安装, never blanks neighbors); 里程碑阶段 is the one static milestone constant
- [Phase 09]: [Phase 09]: 09-03 migration: env s binding retired (menu slot 2 supersedes — one navigation path per target; help modal auto-reflects), Header/Footer retired on the three base screens (modal Footer hints and matrix chrome kept per the migration table); placeholder slots 3/4/5 carry Phases 10/11/12 in NAV_SLOTS
- [Phase 9]: 09-04: wizard = one ModalScreen over declarative step tables (FieldSpec/StepSpec/KindSpec); compose renders only the active phase view and every value lives in self._values — report/gauntlet are VIEWS inside the same modal, so their dismissal structurally cannot destroy entered values (Pitfall 9); only esc-confirm / land / used undo clear the form
- [Phase 9]: 09-04: dataset split-file Inputs collect file names advisory-only — Train/Dev/Test never compose into the candidate (the 09-01 derive-at-composition decision); Task_type stores under the registry field 'type' (#11); the candidate stamps nothing service-owned, numerics compose as numbers when parseable (raw text passes through for the collect-all to flag), optional strings as '' never None, quirks as the three-key dict
- [Phase 9]: 09-04 probe-pinned textual 8.2.8 facts: TCSS has no min()/arithmetic (the wizard width amendment applies in code at min(100,w-4)); border_title parses console markup at set time so the step-indicator accent resolves app.current_theme.accent (no hardcoded hex); SelectionList.deselect accepts the option VALUE and fires no re-toggle (single-pick enforcement loop-free)
- [Phase 09]: 09-05: the gauntlet panel drives the service's two PUBLIC per-leg entry points (not the batch reconcile) — per-item progression needs a service call per row flip; reconcile's kind rule is mirrored 1:1
- [Phase 09]: 09-05: run id increments at launch only; staleness = id mismatch OR phase not gauntlet/drill — esc mid-run abandons the run (late results drop, an abandoned all-pass never lands); the EntryDone event-loop handler is the panel's ONLY write call site (the injected land seam)
- [Phase 09]: 09-05: imports continue past a failing entry (the others land); every status surface is state-then-DOM (verdicts landing while a drill view holds the DOM survive the return); panel entry rows scroll in a code-bounded region (grid minus chrome) after a probe-confirmed 6-entry clip at 80x24
- [Phase 09]: 09-06: the w/e seams are an optional SelectionScreen constructor injection (custom_service = CustomOnboardingBackend) — the Phase 8 protocol and fakes stay byte-unchanged; the backend composes the real validator (official keys = merged minus landed customs), observed vocabularies, GauntletService, and the 09-01 store seams, with land/undo firing the refresh worker; WizardModal imports lazily (wizard imports ConfirmModal from selection — the cycle broken at call time)
- [Phase 09]: 09-06: the management second read honors DNALLMMARK_CUSTOM_REGISTRY_DIR via the additive read_entries(registry_dir=None) param — the overlay-merged view and the management view always describe ONE file (Pitfall 7), and the Phase 8 backend tests stay machine-independent; disabled customs append after the merged entries with custom_status recording the truth
- [Phase 09]: 09-06: disabled-entry marking is blocked at every mark entry (T-09-13): the spacebar guard refuses with the warning toast AND _deliverable_keys excludes disabled customs from the preset/template key sets so references ride the Phase 8 unknown-key loud skip — a mark the sweep can never see never exists
- [Phase 09]: 09-06 probe re-encounter: rich Text SPANS cannot carry $token styles (MissingStyle; whole-text styles can) — the badge span resolves the live theme accent at render (the nav.py precedent), the disabled spans and the count segment use rich-native dim
- [Phase 10]: 10-01: channel resolver + CLI probe landed inside Task 1 (the plan's ordering resolution — missing-set derivation needs resolve_channel)
- [Phase 10]: 10-01: parse_progress returns integer percents (plan contract: integer-percent change throttling) though the research snippet returned strings
- [Phase 10]: 10-01: enqueue precedence is existing-entry-first (D-08's unconditional already_queued) ahead of the unknown/disabled/cli gates; behavior tests chosen over the AST Lock pin (advisory)
- [Phase 10]: 10-02: reconcile verdicts split on artifact-disproof (parsed-record violations -> mismatch, the banner data) vs cannot-run (nonzero/timeout/unparseable/key-absent -> failed); the done gate populates entry.reconcile as the reconciled_rows overlay source, and ONLY reaudit_baseline may ever construct a no-flag audit argv (R-03 default outputs)
- [Phase 10]: 10-03: the zenodo bundle entry carries {per_key: verdict} in entry.reconcile — reconciled_rows (the D-11 overlay source) deliberately contributes nothing for it; bundle-landed keys flip the env disk-scan kernel naturally, selection presence follows the g re-audit
- [Phase 10]: 10-03: bundle final-state precedence is failed(nothing-landed/stage-failed) > mismatch > done, and done additionally requires zero FAILED reconciles (a swallowed infrastructure failure can never read as done); the string block landed with exactly the 47 constant names 10-04/10-05 reference (the W1 mirror), tripwired by inventory test
- [Phase 10]: 10-04: per-worker @work groups are mandatory for concurrent exclusive workers — textual exclusivity cancels by (node, group), so the mount pair (snapshot + Zenodo probe) sharing the default group silently cancelled each other; probe-pinned on 8.2.8, fixed as dl-snapshot/dl-probe/dl-reaudit
- [Phase 10]: 10-04: the driver posts one indeterminate (percent=None) claim tick so the row flips to downloading before any CLI percent parses (unparsed output may never fire a real tick); apply_queue_event/apply_queue_progress re-read the entry from the service (persisted-state-as-truth) so late/duplicate events can never overwrite newer state
- [Phase 10]: 10-04: boot resume fires ONLY from tui/__main__ (call_later(boot_resume_queue)) — App.on_mount never kicks, so test-constructed apps stay provably inert while the operator's console resumes; the busy-guard proof is the generation counter staying at 1 across two rapid kicks
- [Phase 10]: 10-04: the two-Protocol seam — QueueDriverProtocol (app: load/entries/claim_next/run_task) and DataManagerServiceProtocol (screen: snapshot/enqueue/probe/reaudit/channel_detail/read_log) bridged by the Any-typed DataManagerBackend over the ONE shared queue instance (the build_data_manager_screen factory prevents a zero-arg SCREENS slot from forking the state)
- [Phase 10]: 10-05: the selection enqueue seam is SelectionQueueBackend — an Any-typed bridge over the app's shared queue (the DataManagerBackend two-Protocol shape); a direct pass would fail ty because the app field's declared QueueDriverProtocol does not carry enqueue
- [Phase 10]: 10-05: the merged presence gates on truthiness (if audit:) not is-not-None — merge_presence returns {} for a None+empty input and truthiness preserves Phase 8's byte-exact degenerate render; audit_available = committed OR overlay non-empty so an audit-less machine still shows a done flip
- [Phase 10]: 10-05: apply_queue_event reuses the existing exclusive _load_data worker (the _on_custom_registry_changed idiom) — the landed 10-04 app forward needed zero changes to reach the mounted selection screen; env_check.py stays pristine (the ENV-03 [3] hint is the amended constant through the existing render path, test-pinned)
- [Phase 10]: CLI availability gate lives at the consumers (enqueue/run_task), not the resolver: resolve_modelscope_cli keeps the pinned verbatim-explicit contract while a nowhere-pointing explicit path is the honest cli_unavailable state (10-06)
- [Phase 10]: The corrupt-load diagnostic is session memory (last_load_diagnostic): load() returns it once, the screen's reloads surface the remembered value; the restart downgrade skips keys with a live process so a mid-flight reload can never re-queue the running entry (10-06)
- [Phase 10]: The real service's probe_zenodo routes the zenodo_fetch seam — the whole queue surface (probe included) is offline-injectable; no queue test lane can reach the wire (10-06)

### Pending Todos

None yet.

### Blockers/Concerns

- GB10 GPU work is permanently outside CI scope; ALL pipeline execution (including Phase 11's bounded smoke) requires explicit maintainer authorization — this milestone is code-first
- Zenodo record 19135551 not yet public — DATA-04's bulk entry is designed in Phase 10 but activates only when the record publishes
- ModelScope CLI flag/progress-parsing specifics are MEDIUM confidence — confirm during Phase 10 (narrow in-phase item, not a research phase)
- Custom-registry storage location (`~/.config/dnallmmark/` vs repo-local ignored dir) and the exact overlay read seam are Phase 7/9 discuss items — the user-owned-file principle itself is fixed
- v0.7.1 carryover registry questions (space/SPACE merge decision; 7 models without locatable public cards) remain maintainer-owned — outside v1.2 scope unless registries are touched

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-12T18:03:44.441Z
Stopped at: Phase 10 complete, ready to plan Phase 11
Resume file: None

## Operator Next Steps

- Phase 8 execution is COMPLETE (all 7/7 plans, 2026-10-11): run the phase close-out — verification / `/gsd-progress` to transition toward Phase 9 (Custom Model & Dataset Onboarding)
