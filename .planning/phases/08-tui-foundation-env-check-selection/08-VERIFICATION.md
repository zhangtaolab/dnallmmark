---
phase: 08-tui-foundation-env-check-selection
verified: 2026-10-14T13:29:01Z
status: gaps_found
score: 5/6 must-haves verified
covered_files:
  - .planning/phases/08-tui-foundation-env-check-selection/08-01-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-01-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-02-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-02-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-03-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-03-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-04-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-04-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-05-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-05-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-06-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-06-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-07-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-07-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-08-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-08-SUMMARY.md
  - dnallm-mark/data/n_audit.json
  - pipeline/env_smoke.py
  - tests/test_env_smoke_bytes.py
  - tests/tui/test_pilot_boot.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_matrix.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_services_registries.py
  - tests/tui/test_work_site_hardening.py
  - tui/__main__.py
  - tui/app.py
  - tui/screens/about.py
  - tui/screens/data_manager.py
  - tui/screens/env_check.py
  - tui/screens/matrix.py
  - tui/screens/monitor.py
  - tui/screens/selection.py
  - tui/screens/wizard.py
  - tui/services/env_check.py
  - tui/services/env_gate.py
  - tui/services/quick_check.py
  - tui/services/registries.py
  - tui/services/selection.py
  - tui/strings.py
  - tui/styles.tcss
covered_digest: "v3:sha256:7c1ffc3862c582402bb6198081acb59ef031332cd3d2031c13639e91b06d9202"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - "Chain 1: non-dict custom entry through SelectionBackend.load_selection_data() now degrades to the empty-card entry — re-reproduced by this verifier through the real seams (61-entry overlay run: type ''/species ''/size_m 0.0, card verbatim, presence UNKNOWN, preset_menu survives, no raise)"
    - "Chain 2: corrupt official models_info.json (json.JSONDecodeError AND UnicodeDecodeError) degrades through _load_entries to ([], path); backend yields models_load_error naming the path while datasets stay healthy; preset_menu inherits the widened seam"
    - "WR-01: env screen survives a broken checkout (per-kernel + kernels()-enumeration degrade guards inside the exclusive worker); both named Pilot tests green; run_config's direct registry reads covered by its internal broad except (AST-pin-verified)"
    - "env_smoke directory kernels fail-closed via _read_registry (named ok=False FAIL lines; non-dict/path-less entries count as missing); S1-S4 byte goldens green unmodified"
    - "@work never-exit floor: 13 exit_on_error=False decorator sites + 11 internal-broad-except sites pinned by tests/tui/test_work_site_hardening.py (green at HEAD); pipeline/registry_loader.py byte-unmodified across the entire gap-closure range (empty git diff 22ca261..HEAD)"
    - "Box baseline holds exactly: full suite 7 failed / 1725 passed / 9 xfailed (6 documented data/schema + 1 machine-state storage-overview + 9 strict-xfail SVG goldens) — zero new failures; snapshots untouched"
  gaps_remaining:
    - "Two screen-side DIRECT card reads still crash-exit the console on the same loader-accepted non-dict-card input class (fresh Pilot reproductions this pass; see gaps)"
  regressions: []
gaps:
  - truth: "Goal-derived foundation invariant (the phase goal's own words: 'trustworthy at rest' + the prior gap's own wording: registry inputs the loader contract accepts 'degrade … — the console never exits on them'): every consumer of the projected entries' card field must tolerate the loader-accepted non-dict card, not only the load-path seams 08-08 closed"
    status: failed
    reason: >-
      The 08-08 load-path closure is complete and re-proven by this
      verifier's own executions — but two SCREEN-SIDE direct card reads
      on user-action paths still raise AttributeError into textual
      8.2.8's App._handle_exception ("Always results in the app
      exiting" — confirmed from the installed package), exiting the
      whole console on the same non-dict-card input class. Both were
      reproduced by this verifier this pass with real-app Pilot runs
      over the REAL selection backend (non-dict overlay via
      DNALLMMARK_CUSTOM_REGISTRY_DIR). (1) w PRESS, ANY cursor
      position: build_wizard's observed-vocabularies set
      comprehensions call entry["card"].get("species") /
      .get(Tokenizer) over ALL merged model entries
      (selection.py:712-719) — reproduced: app._exception =
      AttributeError("'list' object has no attribute 'get'"). The
      executor's deferred-items claim "reached only by explicit
      w/d/enter action ON a non-dict-card row" is imprecise for w: no
      row interaction is required, any w press on the models screen
      exits the console while a non-dict entry is merged. (2) ENTER on
      the degraded row: _open_detail's entry.get("card") or {}
      (selection.py:2144) is defeated by a truthy non-dict card, and
      RowDetailModal.on_mount iterates self._card.items()
      (selection.py:1236) — reproduced: AttributeError("'list' object
      has no attribute 'items'"). Dating (#3304): the RowDetailModal
      chain is PHASE 8 origin (card-or-{} at dafcf94 08-07; the modal
      at bfc477f 08-07) — the same commit family as the prior chain-2
      tuple; the w chain is Phase 9 origin (9b83965 09-06). Both sites
      live in selection.py, git-modified since the last PASSED
      verification (2026-10-13), and both carry deterministic evidence
      (this verifier's Pilot reproductions), so both remain blocking
      under the evidence gate. The empty-card projection 08-08 landed
      deliberately renders the degraded row into the table with the
      card verbatim — making the enter drill-down a plainly reachable
      path (t pool-toggle → navigate → enter; the row is hidden in the
      DEFAULT pool but visible in the ALL pool). A third site,
      _manual_landing_path (selection.py:1758, same `or {}` idiom), is
      currently SHIELDED — reproduced alive this pass — but only
      incidentally: the d action returns on presence UNKNOWN (the new
      model_presence guard) before reaching the card read.
    artifacts:
      - path: tui/screens/selection.py
        issue: "L712-719 build_wizard observed vocabularies: entry[\"card\"].get(...) over all merged entries unguarded (w press, any cursor). L2144 _open_detail: entry.get(\"card\") or {} defeated by truthy non-dict card. L1236 RowDetailModal.on_mount: self._card.items() raises on non-dict. L1758 _manual_landing_path: same or-{} idiom, incidentally shielded by the UNKNOWN presence branch"
    missing:
      - "isinstance(card, dict) guards at the two crashing sites, mirroring the 08-08 projection pattern: build_wizard's two set comprehensions skip non-dict cards (no species/tokenizer vocabulary from a degraded card); _open_detail passes {} for a non-dict card (or RowDetailModal renders the verbatim value without .items())"
      - "harden _manual_landing_path's `or {}` to an isinstance guard (the current shield is the UNKNOWN presence branch — incidental, one refactor away from breaking)"
      - "regression Pilot tests pressing w / enter / d on a degraded-row registry snapshot (the same real-app shape this verifier used): all three must keep the app alive"
deferred:
  - truth: "Critical FAILs block entry into the launch flow (ENV-03) and the quick-check re-validates before each task launch (ENV-04) — the launch-flow wiring itself"
    addressed_in: "Phase 11"
    evidence: "CLOSED by its successor: Phase 11 landed the env preflight + E2' typed gate (d8e63ed) and the launch gate screen — Phase 11 verification passed at c50abe4, UAT 64ad9e3. Kept as the historical deferral record."
advisory:
  - finding: "WR-02: degraded dnallm_compat map renders a silent blank models table on slot 2 (no degraded-state row when the default pool yields zero entries)"
    category: architectural
    reason: "Introduced by quick-261014-mlc (post-phase scope); tracked open in 08-REVIEW-DISPOSITION.md. Unchanged this pass. Resolved by carrying a degraded signal on SelectionData and rendering a state row."
    evidence_status: "none provided"
  - finding: "WR-03: new synchronous event-loop file reads (_render_storage, _submit_save→custom_names) contradict the module's own D-03 read-seam discipline"
    category: architectural
    reason: "Added by quick tasks 261014-f4w/mlc (post-phase scope); bounded local-file stalls, not a Phase 8 must-have breach; tracked open in the disposition. Unchanged this pass."
    evidence_status: "none provided"
  - finding: "IN-01..IN-04: dead strings constants after the slot split; matrix Header() chrome inconsistency; missing is_valid_coordinate guard in EnvCheckScreen.action_show_detail (present in SelectionScreen.action_show_detail); degenerate filter tokens (=x, type=)"
    category: other
    reason: "Info-level, post-phase scope, tracked open in 08-REVIEW-DISPOSITION.md; none breaches a Phase 8 must-have. Unchanged this pass."
    evidence_status: "none provided"
---

# Phase 8: TUI Foundation (Env Check & Selection) Verification Report

**Phase Goal:** The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module i18n convention) landed so later phases add screens, not architecture
**Verified:** 2026-10-14T13:29:01Z
**Status:** gaps_found
**Re-verification:** Yes — third pass, after gap plan 08-08 (commits 87c1458..3267836). This pass re-verified ALL six truths at HEAD 3267836, re-executed both prior crash chains through the real seams, re-ran the named 08-08 regression tests and the AST pin, ran the FULL suite once (7 failed / 1725 passed / 9 xfailed == the locked box baseline exactly), assessed the executor's two documented deviations, and probed the deferred screen-side direct card reads with fresh real-app Pilot runs — two of the three still exit the console and are reported as the (now much narrower) residual gap.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1: `make tui` opens the console; startup runs the full environment check reusing env_smoke kernels; per-item ✓/✗ status with drill-down | ✓ VERIFIED | Recipe unchanged (`uv run --group tui --group gpu python -m tui`, Makefile:206-207); `get_default_screen() → EnvCheckScreen` (app.py:424-426); 8 kernels live-confirmed (`ENV_KERNEL_LABELS`, len 8); boot + env-check Pilot suites green inside the full-suite baseline run |
| 2 | SC2: Check results persist with visible 上次检查 date; same-day restarts read the cache; manual refresh re-checks | ✓ VERIFIED | `ENV_LAST_CHECK_LINE = "上次检查: {checked_at}"` (strings.py:94) rendered env_check.py:544; `Binding("r", "refresh")` (:324); cache/persistence tests green in the suite |
| 3 | SC3: Critical FAILs visibly block with reason; missing-dataset routes to data management; quick-check re-validates launch-required subset | ✓ VERIFIED | Live: CRITICAL={cuda, dnallm, matmul, numpy, peft, version_pins} disjoint from ROUTING={model_dirs, dataset_dirs}; quick-check 7 ids (matmul excluded, D-09 held), subset of the 8 kernel labels; Phase-11 deferral CLOSED (launch-flow wiring landed d8e63ed, verified passed at c50abe4) |
| 4 | SC4: Model/dataset lists first-class selectable; k9s filter; spacebar marks on stable row_keys; presets; read-only matrix auxiliary view | ✓ VERIFIED | Bindings intact at HEAD (selection.py:1256+: space/t/p/x/s/slash/w/e/d/v/enter + nav digits); live 59 models / 50 datasets through the real backend; slot-split + 62→59 reshapes carry their maintainer provenance (unchanged from the prior pass); selection + matrix lanes green in the suite |
| 5 | SC5: Presence columns; templates round-trip as validated JSON with sweep_priorities tier interop; Chinese-primary i18n via constants module; foundation invariants (services textual-free, `[tui]` isolation, Pilot green CPU-side) | ✓ VERIFIED | Live at HEAD: 50/50 datasets present through the real `load_n_audit` seam; template↔tier round-trip over the REAL sweep_priorities file (validate=0 errors, membership preserved exactly both directions); 3 presets (tier-1/tier-2/all, load_error None); greps: 0 textual imports across tui/services/, 0 CJK outside strings.py, `[tui]` = exactly textual>=8.2,<9 + platformdirs + jsonschema and absent from data/dev/gpu; full suite at the exact box baseline |
| 6 | Goal-derived foundation invariant: tolerant artifact loading landed such that loader-accepted registry inputs degrade — the console never exits on them | ✗ FAILED | **The 08-08 closure itself is complete and independently re-proven** — chains 1+2 degrade through the real seams (this verifier's own reproductions), WR-01 guards landed, env_smoke fail-closed, AST never-exit pin green (13 kwargs + 11 internal guards), loader byte-unmodified, baseline exact. **But the invariant's own words still do not hold for two screen-side direct card reads**, both reproduced by this verifier with real-app Pilot runs over the real backend: (1) **any `w` press** on the models screen with a non-dict custom entry merged → `entry["card"].get(...)` in build_wizard's vocabularies (selection.py:712-719) → `AttributeError: 'list' object has no attribute 'get'` → console EXIT (no row interaction needed); (2) **enter on the degraded row** (visible in the ALL pool) → `_open_detail`'s `or {}` defeated (selection.py:2144) → `RowDetailModal.on_mount` `self._card.items()` (:1236) → `AttributeError: 'list' object has no attribute 'items'` → console EXIT. Both route to `App._handle_exception` ("Always results in the app exiting", confirmed in installed textual 8.2.8) — event-loop action/handler paths the @work net cannot cover. Dating: the enter chain is PHASE 8 origin (dafcf94/bfc477f, 08-07); the w chain is Phase 9 origin (9b83965, 09-06). A third site (`_manual_landing_path`, :1758) is shielded — reproduced alive — but only incidentally (the d action returns on presence UNKNOWN before the card read) |

**Score:** 5/6 truths verified (0 present, behavior-unverified)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ENV-03/ENV-04 launch-flow wiring (historical record) | Phase 11 | CLOSED by Phase 11: env preflight + E2' typed gate landed (d8e63ed), Phase 11 verification passed at c50abe4. Kept for the audit trail |

### Advisory (New Scope, Unevidenced)

Unchanged from the prior pass (all tracked open in 08-REVIEW-DISPOSITION.md; none evidenced as a must-have breach). Note the two newly-evidenced screen-side crashes are NOT here — they carry deterministic evidence and sit in the gap above.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | WR-02: degraded compat map renders a silent blank models table on slot 2 | architectural | mlc-scope; review-tracked open; no execution evidence this pass |
| 2 | WR-03: synchronous event-loop file reads contradict the pinned D-03 read-seam discipline | architectural | f4w/mlc-scope; bounded stall; review-tracked open |
| 3 | IN-01..IN-04: dead constants, matrix Header chrome, missing coordinate guard in env detail action, degenerate filter tokens | other | info-level, later scope |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `pipeline/env_smoke.py` | structured kernels + renderer main(); fail-closed registry reads | ✓ VERIFIED | `_read_registry` helper in both directory kernels; per-entry dict-guards; S1-S4 byte goldens green unmodified |
| `tui/services/registries.py` | entries + presence + compat; isinstance-guarded projections | ✓ VERIFIED | `_project_model_entry`/`_project_dataset_entry` empty-card guards (chain-1 root); live 59/50 + presence 50/50 |
| `tui/screens/selection.py` | slot-2 models screen | ✓ VERIFIED (with Truth 6 residual) | load-path seam widened and proven; the two screen-side direct card reads are the residual gap |
| `tui/services/selection.py` | filter/presets/presence | ✓ VERIFIED | model_presence isinstance guard (the Rule-1 deviation) verified in code and by execution (UNKNOWN, no raise) |
| `tui/screens/env_check.py` | env panel + WR-01 guards | ✓ VERIFIED | per-kernel + enumeration degrade inside the exclusive worker; `exit_on_error=False`; both named Pilot tests green |
| `tests/tui/test_work_site_hardening.py` | AST never-exit pin | ✓ VERIFIED | green at HEAD; 24 sites found; dichotomy enforced; non-vacuity floor 20 |
| `tui/app.py` | composition root | ✓ VERIFIED | default screen env-check; run_download_queue kwarg landed (ledger row 4) |
| `tui/strings.py` | i18n single home | ✓ VERIFIED | `ENV_KERNEL_DEGRADED` the one new constant; 0 CJK elsewhere |
| `pyproject.toml` `[tui]` group | textual isolation | ✓ VERIFIED | exactly textual>=8.2,<9 + platformdirs + jsonschema; absent from data/dev/gpu |
| `pipeline/registry_loader.py` | fail-loud contract BYTE-UNMODIFIED (prohibition) | ✓ VERIFIED | empty `git diff 22ca261..HEAD` over the file; loader contract tests byte-unmodified and green |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `make tui` | `tui.app` | recipe → `python -m tui` → bootstrap | ✓ WIRED | Recipe unchanged; boot Pilot green |
| SelectionBackend.load_selection_data | registries projections → table rows | guarded projection + widened seam | ✓ WIRED | Both chains re-proven degrading by this verifier's own runs |
| preset_menu | same `_load_entries` seam | shared seam | ✓ WIRED | Survives corrupt official registry (live-proven) |
| env screen worker | kernels → CheckItemDone → persist | WR-01 guards | ✓ WIRED | Raising kernel / failing enumeration both degrade; app alive (named Pilot tests green) |
| env_smoke directory kernels | fail-closed named FAIL | `_read_registry` | ✓ WIRED | Corrupt/missing registry → named ok=False; goldens byte-identical |
| AST pin → every @work site | structural dichotomy | exit_on_error=False OR internal broad except | ✓ WIRED | Pin green; 13 kwarg sites grep-confirmed in tui/ |
| Services layer | textual | must NOT import | ✓ WIRED (negative) | 0 imports across all service modules |
| Presence column | committed n_audit | load → presence_for | ✓ WIRED | Live 50/50 present — FLOWING |
| **Screen-side card consumers → degraded rows** | **`w` vocabularies / `enter` detail modal** | **direct `entry["card"]` reads** | **✗ NOT_WIRED (2 sites)** | Both crash-exit the console on non-dict cards — Truth 6 residual |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| selection/matrix presence | `presence_for(key, audit)` | committed `n_audit.json` via `load_n_audit` | Yes — 50/50 present, live | ✓ FLOWING |
| model list | `load_model_entries()` | overlay-merged registry | Yes — 59 officials + customs; non-dict customs project as empty card (live) | ✓ FLOWING |
| presets menu | `derive_presets(path, keys…)` | `pipeline/sweep_priorities.json` | Yes — 3 presets, load_error None (live) | ✓ FLOWING |
| templates | `tiers_to_template`/`template_to_tiers` | real priorities doc | Yes — round-trip membership exact, 0 validation errors (live) | ✓ FLOWING |
| env panel | kernels → CheckResult | real kernel execution + persisted state | Yes — Pilot + cache tests green; degraded kernels render named FAIL rows | ✓ FLOWING |

### Behavioral Spot-Checks

All run by this verifier at HEAD 3267836.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full suite (once) | `uv run --group dev --group tui pytest -q` | **7 failed / 1725 passed / 9 xfailed** — exactly the locked box baseline (6 documented data/schema + 1 machine-state + 9 strict-xfail goldens); zero new failures | ✓ PASS |
| **Chain 1 re-reproduction** | non-dict overlay via `DNALLMMARK_CUSTOM_REGISTRY_DIR` → `load_model_entries()` + real `SelectionBackend.load_selection_data()` | 61 entries; broken entry = empty card (type ''/species ''/size_m 0.0), card verbatim `[1,2,3]`, presence UNKNOWN, `preset_menu` OK — **no raise** | ✓ PASS (gap item closed) |
| **Chain 2 re-reproduction** | corrupt-official loaders → `_load_entries` + real backend + `preset_menu` | JSONDecodeError AND UnicodeDecodeError each degrade to `([], path)`; backend `models_load_error` names models_info.json, datasets healthy 50; preset_menu survives — **no raise** | ✓ PASS (gap item closed) |
| Named 08-08 regression tests | `pytest -k "non_dict_custom_entry or corrupt_official"` / `-k "raising_kernel or broken_checkout"` / `-k "degrade or broken_entries"` | 3 + 2 + 2 passed | ✓ PASS |
| AST never-exit pin | `pytest tests/tui/test_work_site_hardening.py -q` | 1 passed (24 sites ≥ floor 20) | ✓ PASS |
| Loader prohibition | `git diff 22ca261..HEAD -- pipeline/registry_loader.py` | empty (byte-unmodified) | ✓ PASS |
| Snapshots prohibition | `git status --short -- tests/tui/__snapshots__/` | clean | ✓ PASS |
| **Deferred-path probe: `w` press** (real app, real backend, non-dict overlay) | Pilot: open slot 2, press `w` | `app._exception = AttributeError('list' object has no attribute 'get')` at selection.py:712 — **console exit**, any cursor position | ✗ FAIL (Truth 6 residual) |
| **Deferred-path probe: `enter` on degraded row** (t → navigate → enter) | Pilot: cursor to `hand-edited-nondict`, press `enter` | `AttributeError: 'list' object has no attribute 'items'` at selection.py:1236 (`RowDetailModal.on_mount`) — **console exit** | ✗ FAIL (Truth 6 residual) |
| Deferred-path probe: `d` on degraded row | Pilot: press `d` | app alive, no exception (shielded by the UNKNOWN presence branch) | ✓ PASS |
| textual exit semantics | installed textual 8.2.8 `App._handle_exception` + message_pump routing | "Always results in the app exiting"; action/handler exceptions route there — the @work net does not cover event-loop paths | ✗ CONFIRMED (consequence for both residual crashes) |
| Crash-site dating (#3304) | `git log -S` (RowDetailModal / `_card.items` / `card=entry.get("card") or {}` / `observed_species`) | enter-chain: dafcf94 + bfc477f (08-07, **Phase 8**); w-chain: 9b83965 (09-06, Phase 9); selection.py modified since last PASSED verify (2026-10-13) | ✗ CONFIRMED in-contract (enter chain Phase 8 origin; both evidenced + modified-since) |
| Live SC3-5 (gate disjointness, quick subset, presence, presets, round-trip, counts) | `python -I` driving the real services | disjoint=True; quick 7 ids ⊂ 8 kernels; 59/50; 50/50 present; 3 presets; round-trip exact | ✓ PASS |
| Architecture greps | services textual imports / CJK outside strings / `[tui]` group contents | 0 / 0 / exact | ✓ PASS |
| Debt markers | TBD/FIXME/XXX/TODO/HACK over all 15 covered source files | 0 real markers (all "PLACEHOLDER" hits are Textual `Input(placeholder=…)` UI constants) | ✓ PASS |

### Probe Execution

No probes declared for this phase — not applicable.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ENV-01 | 08-01, 08-03, 08-04, 08-06, 08-08 | Startup full env check, per-item ✓/✗ + detail | ✓ SATISFIED | Truth 1 (8 kernels; WR-01 survivability now closed) |
| ENV-02 | 08-04, 08-06 | Persisted results + check date + refresh; same-day cache | ✓ SATISFIED | Truth 2 |
| ENV-03 | 08-04, 08-06 | Critical FAIL blocks launch flow; missing data routes to data management | ✓ SATISFIED | Truth 3; Phase-11 wiring landed (deferral closed) |
| ENV-04 | 08-04, 08-06 | Quick-check re-validation of launch-required subset | ✓ SATISFIED | Truth 3 (7-id subset, matmul excluded) |
| SEL-01 | 08-07, 08-08 | Browsable model/dataset lists, k9s filter + mark sets, read-only matrix | ✓ SATISFIED | Truth 4; the browse/filter/mark/matrix surfaces hold — the residual Truth-6 crashes are the w/enter auxiliary actions, not SEL-01's named surfaces |
| SEL-02 | 08-05, 08-07 | Presets: tier-1 pair, tier-2 representatives, all, saved customs | ✓ SATISFIED | Truth 4 (live-verified) |
| SEL-03 | 08-05, 08-07 | Template import/export with validation; sweep_priorities tier interop | ✓ SATISFIED | Truth 5 (round-trip over the real file, 0 errors) |
| SEL-04 | 08-04, 08-07 | Per-row local data presence (✓/✗ + n_audit rows) | ✓ SATISFIED | Truth 5 (50/50 live) |
| I18N-01 | 08-02, 08-03, 08-06, 08-07 | Chinese-primary copy via constants module, technical terms English | ✓ SATISFIED | grep gate 0; the one new ENV_ constant landed in strings.py |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| tui/screens/selection.py | 712-719 | Unguarded `entry["card"].get(...)` in build_wizard vocabularies — crashes on ANY `w` press with a non-dict entry merged | 🛑 Blocker | Console exit on loader-accepted input (Phase 9-origin site; Phase 8 truth breach) |
| tui/screens/selection.py | 2144 + 1236 | `_open_detail`'s `or {}` defeated by truthy non-dict card; `RowDetailModal.on_mount` `.items()` raises | 🛑 Blocker | Console exit on enter over the degraded row (Phase 8 origin: dafcf94/bfc477f) |
| tui/screens/selection.py | 1758 | `_manual_landing_path`'s `or {}` idiom — currently shielded only incidentally | ⚠️ Warning | Harden alongside the two blockers (the shield is the UNKNOWN presence branch, one refactor from breaking) |

### Human Verification Required

None. Both the closures and the residual failures are machine-evidenced (this verifier's own command reproductions above).

### Gaps Summary

One narrow residual gap, same root-cause family as the closed CR-01. The 08-08 gap plan executed exactly as written and every one of its six closure truths was independently re-proven by this verifier at HEAD 3267836: chains 1 and 2 degrade through the real seams (fresh reproductions), WR-01 env survivability holds, env_smoke fails closed with byte-identical healthy output, the @work never-exit floor is structurally pinned (and `pipeline/registry_loader.py`'s fail-loud contract is byte-unmodified), and the full suite sits exactly at the locked box baseline (7 failed / 1725 passed / 9 xfailed, zero new).

What remains is the tier of consumers the plan's named seams did not cover: SCREEN-SIDE direct reads of the projected entries' `card` field on event-loop user-action paths — which the @work net cannot shield and textual 8.2.8 turns into console exits. This verifier reproduced both with real-app Pilot runs over the real backend: any `w` press on the models screen exits the console while a non-dict custom entry is merged (build_wizard vocabularies; no row interaction needed — the executor's deferred-items reachability claim was imprecise here), and `enter` over the degraded row exits via RowDetailModal (a Phase-8-origin site, dafcf94/bfc477f). A third site (`_manual_landing_path`) was probed and survives, but only incidentally. The fix is the same one-line guard family 08-08 already landed twice, plus three Pilot regression tests — after which Truth 6's own words ("the console never exits on them") finally hold across every consumer of the tolerant loader's output.

Both documented deviations were assessed and are sound: the Rule-1 file addition (`model_presence`'s isinstance guard in `tui/services/selection.py`) was required for the plan's own chain-1 truth — `load_selection_data` calls `model_presence` over the merged entries at selection.py:461 — and is verified in code and by execution; the Task-3 commit-granularity deviation is process-only, with the RED evidence JSONs committed and the pin green at HEAD.

---

_Verified: 2026-10-14T13:29:01Z (third pass, post 08-08 gap closure, at HEAD 3267836)_
_Verifier: Claude (gsd-verifier)_
