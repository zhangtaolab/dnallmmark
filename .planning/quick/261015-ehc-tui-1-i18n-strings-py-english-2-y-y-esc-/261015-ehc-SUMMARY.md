---
phase: quick-261015-ehc
plan: 01
subsystem: tui
tags: [tui, i18n, launch-gate, single-gpu, download-speed, strings]
requires:
  - 261015-c4j (the slot-2 live download surface + slot-3 split substrate)
  - 11-03 (the launch refusal chain + spawner-never-called evidence style)
provides:
  - EHC-1 bilingual strings registry (zh+en per constant, DEFAULT English, live L toggle, XDG persistence)
  - EHC-2 y-confirm launch gates (enter provably cannot launch; E2' phrase stays double insurance)
  - EHC-3 single-GPU serialization guard (stage-0 refusal on both gated launch paths)
  - EHC-4 parsed download speed on slots 2+3 only (honest percent-only fallback)
affects:
  - tui/strings.py (the whole registry), tui/app.py, tui/__main__.py
  - every tui/screens/*.py (module-attribute strings conversion)
  - tui/services/sweep_launcher.py, tui/services/download_queue.py
  - tests/tui/ (conftest zh pin + the touched suites), docs/TUI-GUIDE.md
tech-stack:
  added: []   # zero new dependencies; textual stays pinned 8.2.8
  patterns:
    - "bilingual _t registry with set_language globals() rebinding + translate_value byte-equality remap"
    - "recompose + idempotent on_mount re-invocation (the probe-pinned live re-render mechanism)"
    - "MRO action override for enter-inert launch confirms (the 12-03 precedent, no binding shadowing)"
    - "lazy torch seam + tolerant getattr service seams (the flops_counter / 11-03 precedents)"
key-files:
  created: []
  modified:
    - tui/strings.py
    - tui/app.py
    - tui/__main__.py
    - tui/screens/selection.py
    - tui/screens/run_config.py
    - tui/screens/monitor.py
    - tui/screens/data_manager.py
    - tui/screens/env_check.py
    - tui/screens/matrix.py
    - tui/screens/wizard.py
    - tui/screens/about.py
    - tui/screens/nav.py
    - tui/services/sweep_launcher.py
    - tui/services/download_queue.py
    - tests/tui/conftest.py
    - tests/tui/test_strings_phase11.py
    - tests/tui/test_services_download_queue.py
    - tests/tui/test_services_sweep_launcher.py
    - tests/tui/test_snapshots.py
    - tests/tui/test_pilot_boot.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_selection_custom.py
    - tests/tui/test_pilot_data_manager.py
    - tests/tui/test_pilot_env_check.py
    - tests/tui/test_pilot_nav_shell.py
    - docs/TUI-GUIDE.md
decisions:
  - "Live re-render mechanism (the plan's probe clause resolved): recompose() alone LOSES on_mount-populated rows (env table 8->0, proven live on 8.2.8) — the uniform mechanism recomposes the chrome AND re-invokes the screen's on_mount (population-only over instance state behind exclusive workers; the monitor's cadence timers stop-before-re-arm guard makes it idempotent)"
  - "The binding-description remap covers ALL Binding-owning screen classes (sys.modules sweep over tui.screens + the app-local modal registry), not just stacked instances — otherwise a screen constructed after a toggle renders the wrong language forever; __main__'s boot load runs the same remap (class BINDINGS freeze at import in the import-time language)"
  - "Binding.description is FROZEN on textual 8.2.8 (probe-pinned: FrozenInstanceError) — every remapped entry is rebuilt in place with the original key/action/show/key_display/priority"
  - "The E2' modal's matched enter ADVANCES via set_focus(None) (the blur arms the modal-level y binding — while the input holds focus y types into it, correct k9s behavior); the phrase predicate and service-side structural gate are untouched"
  - "The download-column width is 28 (Rich-measured over BOTH languages' widest honest composition '⠋ downloading 100% 123.4MB/s'), not the plan's rough 22 — never clip live data; the table budget pin updated 106 -> 119"
  - "progress_cb keeps the 2-argument call whenever no rate parses (the additive-fake pin made structural) — every pre-existing 2-arg injected fake conforms without edits"
  - "APP_LANGUAGE_TOGGLE_LABEL / APP_LANGUAGE_TOAST carry the APP_ prefix with NO APP_ inventory tripwire existing today — any future APP_ inventory must register them (recorded here per the plan)"
metrics:
  duration: 118 min
  completed: 2026-10-15
actuals:
  tokens: 100424   # chars/4 over the realized diff (401699 chars); plan estimate 120000
  tasks: 5
  commits: 5       # MEASURED: git rev-list --count df9aac0..87a7db4
plan_head_before: df9aac03f5d0b764b4312a70bf30e75e2799f57d
plan_head_after: 87a7db40f0fdfb1ef8bb396060a796544d57e51e
status: complete
---

# Phase quick-261015-ehc Plan 01: TUI hardening — bilingual i18n + y-confirm launch gates + single-GPU guard + download speed Summary

**One-liner:** tui/strings.py becomes a 368-constant bilingual registry (zh terminology table applied verbatim, English default, live `L` toggle persisting through the XDG state root), the three launch confirms become y-only (enter lands on a documented no-op; the E2' phrase advances to a y-ready state instead of confirming), both gated launch paths refuse at stage 0 on a busy single-GPU machine (WORLD_SIZE-else-lazy-torch count, spawner never called), and the parsed transfer rate renders beside the percent on slots 2 and 3 only.

## What Was Built

### Task 1 — EHC-1a: the bilingual strings registry (f2c7a32)

- `tui/strings.py` restructured in place: every constant is `CONST = _t("CONST", "<zh>", "<en>")` (PEP 695 TypeVar — ty keeps seeing named typed attributes); `LANGUAGES`/`DEFAULT_LANGUAGE = "en"`/`set_language()`/`language()`/`translate_value()` are the machinery; `set_language` rebinds every registry constant through `globals()` so module-attribute access resolves live.
- The approved zh terminology table applied verbatim (sweep→训练任务, 输出根→结果目录, 附加/attach→监控, 发射/launch→启动, 短语门→二次确认, cell→训练项, 存储根→存储位置, 发现的 sweep→自动找到的训练任务); the whole-file grep gate over the retired zh terms is zero (comments included); English keeps sweep/cell/output root.
- The six structured constants (ENV_KERNEL_LABELS / ENV_STORAGE_LABELS / WIZM*D_FIELD_LABELS / WIZM*D_STEPS) carry identical key sets/arities across languages.
- conftest + the snapshot script-mode bootstrap pin zh (frozen from-import copies match the zh-rendering committed tests); `_GOLDEN_REFRESH_REASON` amended in place (the 261014-mlc precedent) naming this task's copy drift.
- Both-language inventory loops (phase11 + download_queue tripwires), the registry-consistency tripwire (same-zh implies same-en — `translate_value`'s well-definedness), the terminology tripwire (word-boundary sweep/cell match so `sweep_failures.json` and `sweep_priorities` stay verbatim data), and the default-English test.

### Task 2 — EHC-1b: the L toggle, persistence, module-attribute conversion (b31ae68)

- Every production strings reference converted to `from tui import strings as S` + `S.CONST` (tokenize-based: string literals/comments untouched); `grep -rn "from tui.strings import" tui/` is empty.
- App-level `L` binding (verified free — no screen binds L/l; a focused Input consumes it as text). `action_toggle_language`: flip, atomic-persist `language.json` under the redirectable state root (OSError-tolerant), remap every rendered binding description (all Binding-owning classes), re-render every stacked screen, toast; below the minimum grid it sets+persists only (WR-06).
- The live re-render mechanism is `recompose()` + re-invocation of the screen's idempotent `on_mount` (the probe-pinned resolution — recompose alone drops the on_mount-built rows to zero); the monitor's interval arming stops-before-re-arming.
- `tui/__main__.main` owns the ONLY boot read (`load_persisted_language`: missing/corrupt/wrong-value → DEFAULT_LANGUAGE, never raises) plus the boot-time description remap; test-constructed apps stay inert (pinned).
- TopMenuBar re-translates the frozen NAV_SLOTS labels at mount via `translate_value` from the captured build language; the boot screen title follows via `self.title`.

### Task 3 — EHC-2: y-confirm launch gates (1b66fb5)

- `LaunchConfirmModal(ConfirmModal)`: the hidden `y` binding + `action_confirm` overridden to a documented no-op (plain MRO — the inherited enter lands on the no-op); ConfirmModal and its non-launch consumers stay byte-identical (the preset-overwrite and queue-cancel enter pins untouched and green).
- `_GateConfirmModal` re-parents onto it; the monitor's `request_rerun` pushes it.
- `E2PhraseModal`: the matched enter ADVANCES (blur via `set_focus(None)` — arming the modal-level `y`; indicator stays on the [y] wording) instead of confirming; a further enter does nothing; `y` launches carrying the typed phrase; the mismatch enter stays the no-op pin; the phrase predicate + service-side structural gate untouched.
- Registry values updated through `_t` naming the [y] keycap (LNC_GATE_CONFIRM / LNC_E2_MATCH_OK / MON_RERUN_CONFIRM, both languages).
- Pilot pins rewritten with enter-refusal call-count assertions on all three gates.

### Task 4 — EHC-3: single-GPU serialization guard (4cf15ac)

- `effective_gpu_count()`: WORLD_SIZE (parsed int >= 1) wins without importing torch (proven in a fresh `-I` subprocess — the dev venv holds torch, so in-process asserts prove nothing); else lazy `torch.cuda.device_count()` (honors CUDA_VISIBLE_DEVICES) inside except-everything → 0; no module-top torch import (grep-gated).
- `SweepLauncher(gpu_count=None)` + `single_gpu_launch_blocked()`; the guard is the FIRST stage of BOTH `launch_spec` and `launch_from_failures` — the tier-1 pins prove the preview/official-keys/phrase counters stay zero and the spawner is never called; count >= 2 and count == 0 unrestricted; `launch_argv` stays ungated.
- Screen pre-checks through the tolerant getattr seam (the LauncherBackend pass-through added; fakes without the method never block — pilot-pinned): the slot-4 gate refuses with the bilingual ProblemsModal copy naming the running root(s); the monitor refuses before the confirm modal; the service-refusal render path maps the code to LNC_SINGLE_GPU_BLOCKED (registered + inventoried).

### Task 5 — EHC-4: download speed on slots 2+3 (87a7db4)

- `SPEED_RE` + `parse_speed` (tqdm 892kB/s / 1.23MB/s + spaced 5.0 MiB/s; LAST token wins; adversarial ANSI/CR/huge-digit garbage never raises); the token returns VERBATIM (parsed data — no new strings constants).
- Both stderr pumps fire on (percent, speed) PAIR changes (a stalled percent with a streaming rate is a real tick); the callback keeps the 2-arg call when no rate parses (additive-fake pin).
- `QueueProgressMessage.speed` (claim tick None) + the pair-comparing driver throttle + the additive-default `apply_queue_progress` forward.
- Slot 3: the dim rate word beside the percent/bar (None keeps the byte-stable composition); slot 2: word+percent+speed within the widened 28-cell column (budget 106 → 119); slot 4 byte-untouched (the git-diff purity gate proves it across the task); no global download banner anywhere.

## Verification

- Every task's `<verify>` chain green at commit time (targeted suites + grep gates + `make lint` + `make typecheck`).
- Full `make test` after EVERY task: exactly the box baseline — 7 documented failures (`test_determinism` + 5 × `test_schemas` + `test_storage_overview_defaults_mirror_real_consumers`, the machine-local pipeline/logs pin) + 9 strict-xfail goldens, zero new (final run: 7 failed, 1786 passed, 9 xfailed).
- `tests/tui/__snapshots__/` byte-untouched throughout (`git status` clean over the dir after every task); xfail-strict state unchanged.
- The CJK lock holds: `git grep -nP "[\x{4e00}-\x{9fff}]" -- tui/ ':!tui/strings.py'` is empty (both languages single-homed).
- The @work never-exit AST pin + the card-extraction allowlist green unmodified.
- Probe results recorded in code comments: Binding.description frozen (rebuild-in-place); Screen.recompose exists but loses on_mount rows (the chosen mechanism documented); `set_focus(None)` blur arms modal bindings; the LaunchConfirmModal MRO binding merge works.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The plan's recompose-only re-render loses rows**
- **Found during:** Task 2 (the probe the plan itself demanded)
- **Issue:** `screen.recompose()` rebuilds the compose tree but never re-runs the screen's own `on_mount` — every base screen populates there, so a language toggle would leave EMPTY tables (env-check proven 8 → 0 rows).
- **Fix:** The uniform mechanism recomposes AND re-invokes the screen's `on_mount`; the monitor's cadence timers gained a stop-before-re-arm guard making its on_mount idempotent. The plan's "pick ONE mechanism and apply uniformly" clause resolved by probe.
- **Files modified:** tui/app.py, tui/screens/monitor.py
- **Commit:** b31ae68

**2. [Rule 2 - Missing correctness] Stacked-instances-only binding remap strands later-built screens**
- **Issue:** Remapping only app.BINDINGS + stacked screens' BINDINGS leaves every screen class constructed AFTER a toggle rendering the import-time language forever (screens are rebuilt per navigation).
- **Fix:** The remap walks ALL Binding-owning screen classes (sys.modules sweep over tui.screens + the app-local modal registry) — future screen modules join automatically; `__main__`'s boot load runs the same remap.
- **Files modified:** tui/app.py, tui/__main__.py
- **Commit:** b31ae68

**3. [Rule 3 - Blocking] NAV_SLOTS labels are import-frozen**
- **Issue:** The top bar's slot labels freeze at nav.py import (en in production, zh under the conftest pin) — a bare recompose re-renders the same frozen tuple.
- **Fix:** nav.py captures the build language; TopMenuBar translates each label at mount via `translate_value` (correct in every import-language/toggle combination).
- **Files modified:** tui/screens/nav.py
- **Commit:** b31ae68

**4. [Rule 1 - Bug] Test-side leaks found at final verification**
- **Issue:** The L-toggle Pilot test wrote the REAL `~/.local/state/dnallmmark/language.json` (unpinned state root); the persistence test left the registry + class BINDINGS descriptions in the post-toggle language, breaking later zh assertions order-dependently.
- **Fix:** The toggle test pins its state root (tmp_path); the persistence test restores language AND remaps descriptions back in finally; the stray real-state file removed.
- **Files modified:** tests/tui/test_pilot_boot.py
- **Commits:** b31ae68, 87a7db4

**5. [Rule 3 - Blocking] Lint/style conformance of the new machinery**
- PEP 695 type parameters for `_t` (UP047), PERF102/TRY004/UP037 fixes, ruff --fix for the mechanical import sorting after the conversion; the dangling blank lines the conversion left in `_problem_line` cleaned.
- **Commits:** f2c7a32, b31ae68, 1b66fb5, 4cf15ac, 87a7db4

## Known Stubs

None — every rendered state reaches a real data source and every degradation renders an honest designed constant.

## D-03 Visual-Change Notes (for the maintainer's snapshot re-review)

The goldens were NOT regenerated (the locked constraint — `make snapshot-update` is the maintainer's D-03 step). They were already stale-xfail since 261014-mlc; this task's drift keeps them failing. After regeneration, expect these diffs:

1. **Bilingual toggle (every golden):** the bottom bar's constant right segment gains the `[L]语言` keycap (en mode: `[L]Language`); the committed goldens render zh (the snapshot bootstrap pins zh), so only the L keycap is new there. A regeneration under `en` would flip every screen's copy — regenerate under the pinned zh (the script-mode pin keeps the goldens' language stable).
2. **zh terminology swaps (zh-rendering goldens):** sweep → 训练任务 (LNC_E2_WARNING, LNC_LAUNCH_TOAST, LNC_EXIT_MESSAGE[_MULTI], MON_DISCOVERED_*, MON_LOG_UNAVAILABLE), 输出根 → 结果目录 (CFG_FIELD_OUTPUT_ROOT row label, MON_COL_ROOT header, MON_ATTACH_* copy), 附加 → 监控 (MON_CELLS_EMPTY, the [a] keycap label), cell → 训练项 (CFG_PREVIEW_LINE, LNC_GATE_SUMMARY, MON_CELLS_TITLE, MON_RESUME_NOTE*, MON_RERUN_*), 短语门/存储根 rewordings (CFG_OUTPUT_ROOT_PROBLEM, ENV_ROUTE_MISSING_MODELS).
3. **Column width changes (selection goldens):** the download column widens 15 → 28 (Rich-measured for the rate token); the table's total budget 106 → 119 at the pinned widths — the h-scroll geometry at 80 columns moves accordingly.
4. **Gate modal copy (run_config goldens):** `LNC_GATE_CONFIRM` now reads "启动以上训练任务？— [y] 启动 / Esc 取消"; `LNC_E2_MATCH_OK` carries the "[y] 确认启动" wording; `MON_RERUN_CONFIRM` (monitor goldens) names the [y] keycap.
5. **Speed word (data_manager goldens):** the queue progress cell MAY carry a trailing dim rate token on downloading rows — the goldens' static fixtures emit no rates, so their cells stay the prior composition (the fallback pin proves byte-stability).

The known snapshot-determinism flake under load (261014-dcl deferred-items) remains pre-existing.

## Threat-Model Dispositions

- **T-ehc-01 (tampered child stderr):** mitigated — regex-only `parse_speed`/`parse_progress` reuse, no interpolation; adversarial-garbage tests pin never-raises (T-c4j-02 posture).
- **T-ehc-02 (tampered language.json):** mitigated — tolerant json load; missing/corrupt/wrong-value resolves to DEFAULT_LANGUAGE, never raises, never blocks boot (test-pinned all three degradation shapes).
- **T-ehc-03 (weakened E2' gate):** mitigated — the phrase predicate and the service-side structural gate are untouched; Pilot pins prove enter-cannot-launch and phrase-then-enter-then-y; the single-GPU guard ADDS a stage, removes none.
- **T-ehc-04 (hung torch import):** accepted — lazy import inside try/except-everything degrades to count 0 (unrestricted, the ruling's letter); no timeout machinery warranted.
- **T-ehc-SC (package installs):** zero new packages — pyproject.toml/uv.lock untouched.

## Self-Check: PASSED

- Files: all modified files exist on disk (`git diff --name-only df9aac0..87a7db4` — 28 files, all present).
- Commits: f2c7a32, b31ae68, 1b66fb5, 4cf15ac, 87a7db4 — all ancestors of HEAD (`git merge-base --is-ancestor` verified via the ledger range listing at write time).
- Full-suite baseline: 7F + 9XF exactly; goldens byte-untouched; lint + typecheck green on the final tree.
