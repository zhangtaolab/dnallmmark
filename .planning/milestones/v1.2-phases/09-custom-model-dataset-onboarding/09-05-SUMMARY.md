---
phase: 09-custom-model-dataset-onboarding
plan: 09-05
subsystem: tui/screens wizard writing half (gauntlet panel + import/export over the 09-01/09-02 services)
tags: [tui, gauntlet-panel, land-only-on-all-pass, session-undo, import, export, wr-02, thread-worker]
requires:
  - 09-02 (GauntletService per-leg entry points + GauntletItem — the run-id-tagged data contract the panel renders)
  - 09-01 (custom_entries land/undo/read_entries/export_registry + custom_validation import seams — the only write/copy paths)
  - 09-04 (WizardModal's phase machine, the gauntlet phase slot, the f/o/on_valid callback seams, the ConfirmModal destructive gate)
  - 08-02/08-06 (textual 8.2.8, the exclusive @work(thread=True) worker discipline, the WR-02 run-id tag-and-drop)
provides:
  - "The gauntlet panel: kind-aware item rows progressing pending -> running -> pass/fail from ONE exclusive thread worker driving the injected service per leg, with run-id-tagged messages and stale-drop"
  - "Land-only-on-all-pass: the EntryDone handler is the panel's ONLY write call site (the injected land seam) — an abandoned mid-run gauntlet can complete all-pass and still never land (phase-guarded stale drop)"
  - "The failure surface: the verbatim zero-touch banner, verbatim-detail fail rows, enter-on-row drill-down into the subprocess's own output lines, esc-return with every value intact"
  - "The session [u] undo affordance (single-use, toast-confirmed, form-clearing land semantics)"
  - "The D-11 import view: fail-closed numbered conflicts report through the path-prompt surface, then the same panel grouped per entry running sequentially in FILE order with entry-level rollback and {n} toasts"
  - "The D-11 export view: empty-state short-circuit before any path is asked + the verbatim registry copy through the seam"
  - "The GAUNTLET_* copy block complete in tui/strings.py (Copywriting Contract verbatim + the two derived rows documented)"
affects:
  - tui/strings.py (additive GAUNTLET_* block; no existing constant touched)
  - 09-06 wires the real GauntletService/store seams + the validator at the composition root and pushes the wizard via w
actuals:
  tokens: 24547   # chars/4 over the realized tui/+tests/ diff (98186 diff chars)
  tasks: 3
  commits: 6      # MEASURED: git rev-list --count 930c9e8..HEAD
plan_head_before: 930c9e810366b352184f4a7c0d1cdbed2bf65af1
plan_head_after: 13ede1c8b6668e172d551b5483d081e219943e3c
tech-stack:
  added: []        # zero new packages (T-09-SC: the panel drives the 09-02 in-repo service)
  patterns:
    - "per-leg service calls from ONE exclusive thread worker (reconcile's kind rule mirrored leg-for-leg so per-item progression is observable per row — the batch API cannot progress rows)"
    - "stale-drop = run-id mismatch OR non-gauntlet phase (an esc-then-resubmit window can never backfill the form; an abandoned all-✓ never lands)"
    - "every status surface lands in STATE first, then the DOM (a drill view may hold the DOM — verdicts survive the return recompose)"
    - "_first_or_none: DOMQuery.first RAISES NoMatches on empty (probe-pinned 8.2.8) — optional-widget lookups need a real None path"
key-files:
  created: []
  modified:
    - tui/screens/wizard.py
    - tui/strings.py
    - tests/tui/test_pilot_wizard.py
key-decisions:
  - "The worker calls the service's two PUBLIC per-leg entry points (dry_run_precheck / audit_reconciliation) rather than the batch reconcile: the must-have per-item progression (truth 1, the T-08-07 gated-fake proof) requires a service call per row flip; reconcile's kind-aware leg composition (models dry-run only, datasets both) is mirrored 1:1"
  - "The run id increments at ONE site (launch); staleness = id mismatch OR phase not gauntlet/drill — esc mid-run abandons the run (its late results drop, its all-✓ never lands: the operator re-gauntlets on resubmit), and a message arriving outside a live gauntlet view can never backfill the form"
  - "Land happens in the EntryDone HANDLER on the event loop (never the worker thread), keyed to the current run + a live view — the single write call site through the injected seam; the success toast reuses the landed-row copy verbatim (the copy table names no separate toast); a land clears the form (one of the three clearing events)"
  - "Import continues past a failing entry (the UI-SPEC's the others land): every entry's legs run unconditionally in FILE order (reconcile's own unconditional-legs semantics), each failing entry renders its own banner naming only itself, earlier AND later passing entries land, and the completion toast fires with the landed count only when n >= 1 (banners carry the zero story)"
  - "Imported entries' Train/Dev/Test counts pass through VERBATIM as the audit leg's declared side (data extraction, never computed — binding constraint 5); the wizard's own candidate declares none (the 09-01 derive-at-composition decision)"
  - "The export empty state short-circuits BEFORE the path prompt is pushed (nothing at any destination can be created — structural), with the seam's (False, diagnostic) path as the race backstop rendered as a write-failure problem line"
  - "_PathPromptModal reuses the PathInputModal IDIOM in-module (the plan's files_modified holds wizard.py only): its problems view is a wrapping scroll-bounded RichLog (68-char keys wrap, never truncate) and a clean pass dismisses into an ASYNC accept continuation — the import transition recomposes the wizard beneath the popping modal"
  - "The gauntlet panel's entry rows live in a code-bounded VerticalScroll (grid minus panel chrome, recomputed on resize): the UI-Considerations gauntlet-list scroll rule — a 6-entry import at 80x24 clipped statuses beyond the grid before the bound (probe-confirmed y>=24)"
  - "Probe-pinned textual 8.2.8 facts recorded in code: Static Text $token styles render correctly POST-MOUNT (the 09-03 MissingStyle crash was the mount-context path — the styling pass runs after every recompose); DOMQuery.first raises NoMatches on empty (never returns None); the panel must ALWAYS focus a live row after recompose (the pre-panel focus target is a removed Input whose stale focus swallowed keys — esc from the import panel died on it)"
patterns-established:
  - "The gauntlet message family (ItemChecking/ItemDone/EntryDone/RunDone, all run-id-tagged) + gated-fake Pilot idiom over per-(leg, run_id) Events — the data-manager download queue and the run-config smoke reuse this shape"
  - "State-then-DOM status rendering for async surfaces that can be covered by sibling views (the drill-over-panel race pattern)"
requirements-completed: [CUST-04]
# The plan frontmatter carries [CUST-01, CUST-02, CUST-04]; CUST-01/02 stay
# Pending — 09-06 (which also declares them) owns the composition-root
# wiring (real validator + real GauntletService + the w-key push) that
# makes the wizard operator-reachable. CUST-04 is complete across its two
# declarers: 09-02 delivered the service half, this plan the UI half.
coverage:
  - id: CUST04-PANEL
    description: "The gauntlet panel UI: async kind-aware rows with observable pending->running->verdict progression over a gated fake (the console never freezes), run-id stale-drop (a cancelled run's late FAIL never overwrites the fresh run's landed state and never lands), land-exactly-once through the injected seam, never-land-on-any-fail (zero seam calls AND the tmp custom root never gains the file), the verbatim zero-touch banner, verbatim drill-down, esc-return with values intact, and the single-use session undo (real-store variant removes exactly the landed key)"
    requirement: CUST-04
    verification:
      - kind: automated
        ref: "tests/tui/test_pilot_wizard.py (Task-1 suite: 5 tests incl. the gated progression, the two-run stale fixture, and the real-store never-land pin)"
        status: pass
      - kind: automated
        ref: "grep zero-Chinese over tui/screens/wizard.py -> exit 1 (GAUNTLET_* copy only)"
        status: pass
    human_judgment: false
    rationale: "Pilot key-event drives over the real app with gated fakes — mechanical assertions on rendered row text, seam call order, and toast copy"
  - id: CUST04-IMPORT-EXPORT
    description: "The D-11 share-unit flows: fail-closed import (numbered conflicts with full-length keys, tolerant unreadable-file problem lines, nothing merges on any problem), per-entry sequential gauntlet in FILE order with entry-level rollback (the failing entry's banner names only it; earlier lands stand; {n} toasts for any landed count), byte-verbatim export (the exported file equals the landed registry file), and the empty-export short-circuit that writes nothing anywhere"
    requirement: CUST-04 / D-08 / D-11
    verification:
      - kind: automated
        ref: "tests/tui/test_pilot_wizard.py (Task-2 suite: 7 tests incl. the real-store undo/export integration variants)"
        status: pass
    human_judgment: false
    rationale: "Pilot drives + real custom_entries store on monkeypatched tmp config roots (the plan's blessed real-file variant)"
  - id: HARDENING-80x24
    description: "Terminal-contract hardening: a 6-entry import panel at 80x24 stays inside the grid with the entry rows in a bounded scrollable region whose bottom is reachable; a 50-line drill-down wraps (no line elided) and scrolls within its bound; the conflict report wraps a 68-char key and a >100-char path; the WR-01 min-size guard round trip mid-gauntlet restores the panel and the gated run still lands; verdicts arriving while a drill holds the DOM render on return"
    requirement: CUST-04 UI / the UI-Spec terminal contract
    verification:
      - kind: automated
        ref: "tests/tui/test_pilot_wizard.py (Task-3 suite: 5 tests) + make lint / make typecheck clean + the full tests/tui lane (361) and repository suite (930)"
        status: pass
    human_judgment: false
    rationale: "cell-region arithmetic + scroll-state assertions + resize drives over the real app"
  - id: PROHIBITIONS
    description: "The panel performs zero writes itself (land/undo/export exclusively through the injected seams — fake-asserted call counts); the panel never recomputes verdicts (row text formats the service's parsed detail tokens only); official registry files are never written by any flow and the failure banner states the zero-touch guarantee verbatim; no import entry merges without passing its own gauntlet"
    requirement: must_haves prohibitions 1-3 + binding constraints 5/11
    verification:
      - kind: automated
        ref: "the never-land/no-write Pilot assertions (tmp-root file absence) + the hardcoded banner-literal pin + the conflicts/rollback suite"
        status: pass
    human_judgment: false
    rationale: "seam fakes record every call; file-existence assertions over pinned tmp roots"
duration: 95 min
completed: 2026-10-12
status: complete
---

# Phase 09 Plan 5: Wizard Writing Half (gauntlet 面板 + 会话撤销 + 导入/导出) Summary

One-liner: The wizard's writing half landed — an async run-id-safe gauntlet panel over the 09-02 service (rows progressing ◌→⠋→✓/✗ from one exclusive thread worker, landing exactly once through the 09-01 store on all-✓, bannering verbatim and landing nothing on any ✗), the session-scoped [u] undo, and the D-11 import (fail-closed conflicts report, then the same panel grouped per entry with entry-level rollback in file order) and export (empty-state short-circuit + byte-verbatim copy) views behind the 09-04 f/o seams.

## Performance

- 3/3 tasks, 6 commits (3 RED + 3 GREEN, all TDD), 95 min (estimate: 27000 tokens / 3 tasks; actual 24547 tokens over a 1848-insertion diff — estimate 10% high, right on target).
- Verification: tests/tui 361 passed (17 new wizard tests), full repository suite 930 passed, `make lint` + `make typecheck` zero findings, wizard.py zero-Chinese grep exit 1.
- RED evidence: `.planning/tdd-evidence/09-05-task{1,2,3}-red.json`, all RED_EVIDENCE_OK (targets: the panel progression test / the entry-level-rollback test / the 80x24 scroll-bound test).

## Accomplishments

- **tui/screens/wizard.py — the gauntlet panel (Task 1):** the GauntletItemChecking/Done + EntryDone/RunDone message family (all run-id-tagged), ONE `@work(exclusive=True, thread=True)` worker calling the injected service's per-leg entry points with the cancellation poll between legs and the unconditional per-leg result post (the exact WR-02 env-panel discipline); handlers drop stale ids AND anything not addressed to a live gauntlet view; the EntryDone handler performs the only write (the injected land seam) with the landed row + toast + single-use [u] undo affordance and the form-clearing land semantics; any ✗ renders the verbatim zero-touch banner and never lands; enter on a focused row drills into the subprocess's verbatim output in a code-bounded RichLog; esc returns to the form with every value intact.
- **tui/screens/wizard.py — import/export (Task 2):** `_PathPromptModal` (the PathInputModal idiom, in-module) with a wrapping scroll-bounded problems RichLog and an async accept continuation; `f` pushes the import prompt — read failures and conflicts render as numbered report lines and NOTHING merges, a clean file re-enters the same panel grouped per entry (header rows carry each entry's gauntlet title) with the worker iterating the queue in FILE order and per-entry rollback made visible in per-group status lines; `o` short-circuits the empty state to its toast before any path is asked and otherwise routes to the verbatim copy seam with write failures as problem lines.
- **tui/screens/wizard.py — hardening (Task 3):** the entry rows moved into a code-bounded VerticalScroll (grid minus panel chrome, resize-aware) closing the probe-confirmed 6-entry clip at 80x24; every status surface (banner, per-entry status lines, the undo rewrite) became state-derived so verdicts landing while a drill view holds the DOM survive the return; `_first_or_none` gives the optional-widget lookups a real None path (DOMQuery.first raises on empty).
- **tui/strings.py — the GAUNTLET_* block:** every Copywriting Contract row verbatim (items, running row, dry-run pass row, banner, landed row, undo affordance + toast, conflicts header, imported/exported/empty toasts) plus the two documented derived rows (the pending line carrying its item identity; the export problems header) and the drill chrome.
- **tests/tui/test_pilot_wizard.py:** 22 -> 39 tests — gated-fake progression (both kinds), land-exactly-once + undo + form clear, never-land-on-fail (real-store tmp-root pin), the two-run stale fixture, drill-down round trips, conflicts/unreadable/rollback/all-pass import flows, real-store undo and byte-verbatim export, empty export, the 80x24 scroll/wrap/guard hardening set, and the drill-race pin.

## Task Commits

| Task | Commit | Type |
|------|--------|------|
| 1 RED — gauntlet panel suite + GAUNTLET_* strings | 134dcf0 | test(09-05) |
| 1 GREEN — async panel, run-id drop, land-only-on-all-pass | 4ab3ff9 | feat(09-05) |
| 2 RED — import/export + real-store undo suite | 93aa1c9 | test(09-05) |
| 2 GREEN — session undo + per-entry import gauntlet + export views | fcc4d13 | feat(09-05) |
| 3 RED — hardening suite (80x24 scroll bound) | f2e1d73 | test(09-05) |
| 3 GREEN — bounded panel rows + state-derived statuses | 13ede1c | feat(09-05) |

## Files Created/Modified

Modified: `tui/screens/wizard.py` (the panel + flows; 09-04 collection half untouched in behavior — all 22 pre-existing tests green unmodified), `tui/strings.py` (additive GAUNTLET_* block), `tests/tui/test_pilot_wizard.py` (17 new tests, additions only). Broken-windows ledger ids 17-19 (the 09-04 gauntlet/f/o stubs) flipped `fixed`.

## Decisions Made

See key-decisions (frontmatter). Highlights: per-leg service calls for observable per-row progression; the single-increment run id + phase-guarded stale drop making an abandoned all-✓ structurally unlandable; land in the event-loop handler as the only write call site; continue-past-failure imports with per-entry banners; the state-then-DOM status rule; the code-bounded panel scroll region.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing-critical] The import panel's entry rows clipped beyond the 80x24 grid**
- **Found during:** Task 3 (probe before writing the hardening suite)
- **Issue:** the panel composed groups as flat Statics inside the non-scrolling wizard-box — a 6-entry import rendered status lines at y=24/25, outside the grid and permanently invisible (the UI-Considerations gauntlet-list rule demands wrap+scroll with the Phase 8 bound).
- **Fix:** the groups compose inside a `VerticalScroll` with a code-applied max-height cap (grid height minus the panel's fixed chrome, recomputed on every resize alongside the width rule); pinned by `test_import_panel_many_entries_scroll_within_bound_at_80x24`.
- **Files modified:** tui/screens/wizard.py
- **Commit:** 13ede1c

**2. [Rule 1 - Bug] A land or verdict arriving while the drill view held the DOM was lost**
- **Found during:** Task 3 (the drill-race pin test I added alongside the planned suite)
- **Issue:** the banner and per-entry status lines were DOM-only writes — `_render_entry_status` skipped the update when the drill view held the DOM, so a mid-drill land left an empty banner after the return recompose (the land itself survived; its visible record did not).
- **Fix:** every status surface lands in panel STATE first and renders from it (compose + the styling pass), the DOM write becoming an optimization; pinned by `test_verdicts_arriving_during_drill_render_on_return`.
- **Files modified:** tui/screens/wizard.py
- **Commit:** 13ede1c

**3. [Rule 3 - Blocker] `DOMQuery.first()` raises `NoMatches` on empty queries**
- **Found during:** Task 3 GREEN (the first full-lane run after adding the scroll container)
- **Issue:** the plan's query idiom guarded `.first(...)` results with `if x is None`, but textual 8.2.8's `DOMQuery.first` RAISES on an empty query (probe-pinned against the installed source) — every optional-widget lookup (the scroll region outside the panel view, rows during a drill) crashed instead of skipping.
- **Fix:** `_first_or_none` (nodes-empty check) replaces every optional lookup in the new code; the pre-existing 09-04 advisory lookup is always-matching by construction and stays untouched.
- **Files modified:** tui/screens/wizard.py
- **Commit:** 13ede1c

**4. [Test refinements] Harness fixes at GREEN (assertion strength unchanged)**
- Textual's `app._notifications` is a `Notifications` manager, not a list (the selection-suite `[n.message for n in app._notifications]` idiom adopted); the model wizard's step 4 carries only the quirk trio (values-intact asserted by navigating `b` back to step 1); the real-store export test now creates the destination parent (copyfile needs one — the uncovered-parent OSError path itself renders correctly as a write-failure problem line).

Otherwise the plan executed exactly as written.

## Issues Encountered

None open. No auth gates, no checkpoints (fully autonomous plan). The WINDOWS.md ledger required a manual reconciliation (its rendered table had drifted from its JSON source on rows 17-19 — line numbers only); the JSON stays the sole source of truth and the fixed flips + reasons live there.

## User Setup Required

None. Every test runs over tmp config roots or fakes; the user-owned registries are only written by the injected 09-01 seams under test-pinned temporary roots.

## Known Stubs

None. The 09-04 stubs (ids 17-19) are closed: the gauntlet phase now renders the real panel whenever the service seam is wired (the minimal pending view remains only for the seam-less construction the 09-04 tests pin), and `f`/`o` route to the real import/export views whenever their seams are wired (the plain 09-04 callbacks remain the fallback). 09-06 binds the real GauntletService, store, and validator seams at the composition root.

## Next Phase Readiness

- 09-06 consumes: the constructor seams (`gauntlet_service` / `land` / `undo` / `import_read` + `import_validate` / `export_registry` + `has_custom_entries`) pre-bound to the real GauntletService and the 09-01 functions over `ValidationSources`; the `w` push (with the D-12 prefill map); and the zero-Chinese grep extension to `tui/screens/wizard.py` (already clean).
- The import flow's declared-splits pass-through means an exported-and-reimported registry carries its Train/Dev/Test counts into the audit reconciliation verbatim.
- Success criteria confirmed at the UI level: land-only-on-all-✓ with the never-land Pilot evidence, entry-level rollback for both the wizard and the import path, the console never freezing during any gauntlet (gated-fake responsiveness proof), and the per-entry rollback + never-land tests standing as the ROADMAP criterion 4 UI evidence.

## TDD Gate Compliance

All three tdd-marked tasks followed RED -> GREEN with persisted, gate-validated evidence (INVALID_RED guarded):

- **Task 1 RED** (`RED_EVIDENCE_OK`, target `test_gauntlet_panel_progression_pending_running_done`): 5 fail / 22 pass — every gauntlet-panel test failed on the absent seams (`gauntlet_service` constructor kwarg); all 22 pre-existing wizard tests passed unmodified.
- **Task 2 RED** (`RED_EVIDENCE_OK`, target `test_import_two_entries_sequential_entry_level_rollback`): 6 fail / 28 pass — the f/o seams still routed to the 09-04 callbacks; the real-store undo test passed on Task 1's undo implementation (recorded in the evidence's actual field).
- **Task 3 RED** (`RED_EVIDENCE_OK`, target `test_import_panel_many_entries_scroll_within_bound_at_80x24`): 1 fail / 37 pass — the probe-confirmed grid clip; the three hardening pins passed on the Task 1-2 mechanics as expected (they pin, not introduce — the 09-04 Task-3 precedent).
- Every GREEN commit ran the FULL wizard suite before the feat commit (and the full tests/tui lane at plan level); no test was weakened to pass — the Deviation-4 harness fixes kept every planned assertion.

## Self-Check: PASSED

All 3 modified files exist on disk; all 6 task commits (134dcf0, 4ab3ff9, 93aa1c9, fcc4d13, f2e1d73, 13ede1c) are ancestors of HEAD; commits measured 6 via `git rev-list --count 930c9e8..HEAD` (matches `actuals.commits`); tests/tui 361 passed, full repository suite 930 passed, lint + typecheck clean, official registries git-clean.
