---
phase: 08-tui-foundation-env-check-selection
plan: 09
subsystem: tui (selection screen-side card consumers) — gap closure, round 2
tags: [tui, gap-closure, truth-6, registry-tolerance, screen-side-guards, ast-pin, sel-01]
requires:
  phase: ["08-08"]
provides:
  - "tui/screens/selection.py build_wizard — dict-narrowing conditions on BOTH observed-vocabulary set comprehensions (walrus-bound card): a loader-accepted non-dict card contributes NO species/tokenizer vocabulary, the wizard opens over the officials' vocabularies (crash site 1 — ANY w press, any cursor)"
  - "tui/screens/selection.py _open_detail — the card bind + isinstance narrowing: a non-dict card opens RowDetailModal CARD-LESS (border title the key, empty detail log — the 08-08 degraded-row drill-down twin); RowDetailModal itself untouched, its card: dict annotation stays truthful (crash site 2)"
  - "tui/screens/selection.py _manual_landing_path — the model_presence extraction idiom verbatim: a non-dict card returns None independent of the UNKNOWN-presence shield (the hardening; the shield is no longer load-bearing)"
  - "tests/tui/test_card_site_hardening.py — the card-extraction family pin: every X[\"card\"] subscript and X.get(\"card\") call across t/ confined to the four-function ALLOWLIST, each function guard-carrying (deleting a Task-1 guard fails the pin), >=4-node non-vacuity floor, positive-control detector proof, file:line offender messages, the full 8-row sweep ledger in the module docstring"
affects:
  - tui/screens/selection.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_card_site_hardening.py
actuals:
  tokens: 8159    # chars/4 over the realized diff (32638 chars, 850e047..a1d1591)
  tasks: 2
  commits: 3      # measured: git rev-list --count 850e047..a1d1591
plan_head_before: 850e047ae0b872e158b8137f957ff3f0ac460d62
plan_head_after: a1d1591647aeb29b1014e72242b3941a49fef4f3
tech-stack:
  added: []        # zero new dependencies; textual stays pinned 8.2.8
  patterns:
    - "extraction-site-local isinstance(card, dict) guards — the 08-08 model_presence idiom (bind, then .get(...) if isinstance(card, dict) else None) mirrored at every screen-side pull of the card field"
    - "the AST family pin: extraction sites confined to a guard-carrying allowlist + guard-presence checked per allowlisted function + a temp-module positive control proving the detector detects + a non-vacuity node floor — the instance fixes become a structural invariant"
key-files:
  created:
    - tests/tui/test_card_site_hardening.py
    - .planning/tdd-evidence/08-09-task1-red.json
    - .planning/tdd-evidence/08-09-task2-red.json
  modified:
    - tui/screens/selection.py
    - tests/tui/test_pilot_selection.py
key-decisions:
  - "The w fix lands INSIDE the comprehensions' conditions (isinstance((card := entry[\"card\"]), dict) and card.get(...)) rather than pre-filtering the entry list — the officials' vocabularies populate unchanged and the degraded card contributes nothing; the walrus form passes ruff + ty, so the flat double-evaluation fallback was not needed"
  - "DECIDED UX encoded exactly as blessed: enter on the degraded row opens the modal CARD-LESS (border title carries the key, log renders nothing) — the drill-down twin of the row's blank type/species/size_m axes; RowDetailModal is NOT modified and its card: dict constructor annotation stays truthful because only dicts reach it after the guard"
  - "_manual_landing_path is hardened even though d is currently shielded — the UNKNOWN-presence early return is incidental (one refactor from breaking); the unit pin makes the seam's own survival independent of the shield, and the d Pilot test documents the shield as the reason it passes pre-fix"
  - "The pin's ALLOWLIST is exactly sweep-ledger rows 1/2/4/7 (build_wizard, _open_detail, _manual_landing_path, model_presence); RowDetailModal._card and the _custom_*_entry/_project_*_entry projections are param-consumers outside the extraction pattern BY DESIGN — documented in the module docstring's boundary-honesty note, and any NEW extraction feeding them is itself a node the pin catches"
metrics:
  duration: 17 min
  completed: 2026-10-14
status: complete
---

# Phase 08 Plan 09: Round-2 gap closure — screen-side card guards + the extraction-family AST pin Summary

**One-liner:** Three extraction-site-local isinstance(card, dict) guards (wizard vocabularies, card-less detail modal, manual-landing path) close the round-2 Truth-6 crash family on the real app's w/enter/d action paths, and the new AST pin confines every future card extraction in tui/ to a guard-carrying four-function allowlist — the closure is structural, not instance-by-instance.

Closes the second 08-VERIFICATION.md's single residual gap (Truth 6, machine-evidenced at HEAD 3a6e56a: the `w`-press and degraded-row-`enter` console exits, plus the incidentally-shielded `_manual_landing_path`), so phase re-verification can pass 6/6.

## Tasks Completed

| # | Task | Commit | Outcome |
|---|------|--------|---------|
| 1 | The three screen-side guards + the _manual_landing_path hardening, pinned by real-app Pilot reproductions | RED f69d616 / GREEN fd5009d | 4 tests over the REAL app + REAL selection backend (env fake only, non-dict overlay via DNALLMMARK_CUSTOM_REGISTRY_DIR + state isolation): w/enter reproduced the verifier's exact AttributeErrors pre-fix; all green post-fix; the 34 pre-existing selection-lane tests stay green |
| 2 | The card-extraction family pin — sweep ledger + AST structural invariant | a1d1591 (RED evidence in-file) | pin green over the full tui tree (5 extraction nodes, exactly the 4 allowlisted functions, each guard-carrying); RED honestly captured against the guard-removed tree (named all three guard removals with file:line); positive control proven; the 08-08 @work pin green in the same lane |

## TDD Gate Compliance

`gsd_run check tdd-red-evidence` is UNAVAILABLE in this executor environment (gsd_run not installed, exit 1), so the machine classifier could not run; per the reference's error-handling path the RED records with real command/exit/output plus semantic assessments are committed at `.planning/tdd-evidence/08-09-task{1,2}-red.json` (the 08-08 precedent).

- **Task 1 RED** (`uv run --group dev pytest tests/tui/test_pilot_selection.py -q -k "survives_non_dict_card or degraded_row or manual_landing_path_returns_none"` → 3 failed, 1 passed): the two Pilot tests failed on the verifier's exact reproduced crashes through the real app (`app._exception` AttributeError `'list' object has no attribute 'get'` at build_wizard's vocabularies; `'list' object has no attribute 'items'` at RowDetailModal) and the unit test raised on the `or {}` chain at selection.py:1758. The d test PASSED pre-fix exactly as the plan documents (the UNKNOWN-presence shield; its docstring records that). VALID_RED.
- **Task 1 GREEN:** the three guards in the 08-08 idiom. Verify lane `tests/tui/test_pilot_selection.py`: **38 passed** (34 baseline + 4 new) — the guards change nothing for dict cards.
- **Task 2 RED** (guards removed from the working tree, see deviation 1): the pin failed listing exactly `tui/screens/selection.py:1749 _manual_landing_path / :2138 _open_detail / :681 build_wizard — allowlisted but its isinstance(card, dict) guard is gone`, with the floor assertion passing first (7 pre-guard nodes — non-vacuous) and the positive control green in the same run. VALID_RED.
- **Task 2 GREEN:** guards restored; `tests/tui/test_card_site_hardening.py tests/tui/test_work_site_hardening.py` → **3 passed** (the two structural floors compose: workers AND event-loop action paths).
- **REFACTOR:** none needed — the guards ARE the 08-08 idiom; the pin's scanner/violation helpers landed in their final shape with GREEN (annotation-only conformance fixes for ruff UP037 / ty lineno narrowing, amended into the Task-2 commit before the final full-suite run).

## Deviations from Plan

### Auto-fixed Issues

**1. [Process] Task 2's RED protocol — stash shape vs committed guards**
- **Found during:** Task 2 RED capture.
- **Issue:** the plan's `git stash push -- tui/screens/selection.py` assumed the Task-1 guards were still uncommitted; per the task-commit protocol they were already committed (fd5009d), so a stash would be a no-op on the clean tree.
- **Fix:** the identical working-tree state ("the Task-1 guards leave the working tree") was produced with the file-scoped `git checkout fd5009d~1 -- tui/screens/selection.py`, the pin run (FAILED naming all three guard removals), then restored with `git checkout HEAD -- tui/screens/selection.py` (file-scoped — the sanctioned discard form; no blanket reset, no stash). Same tree state, same assertion, honest RED. Recorded in the evidence JSON and here.
- **Files modified:** none (transient working-tree state only).

**2. [Test-side] Task-1 RED fixture spelling**
- **Found during:** the first RED run — the w test failed with NameError (`DnallmMarkTui` typo) instead of the crash; the initial test insertion also left two dangling header lines.
- **Fix:** corrected the app-class spelling and removed the dangling lines before capturing RED; the re-run reproduced the exact AttributeError. Zero implementation impact; noted in the evidence JSON's semantic assessment.
- **Files modified:** tests/tui/test_pilot_selection.py (test-side only, part of the RED commit f69d616).

**3. [Tooling] gsd_run unavailable** (exit 1) — the TDD red-evidence classifier and the state handler verbs ran manually: evidence records committed under `.planning/tdd-evidence/`, STATE.md updated by direct edit (the 08-08 deviation #4 precedent).

Otherwise the plan executed exactly as written (guard shapes, the card-less modal decision, the walrus comprehension form, the four-function allowlist, test names, and assertions all per spec; the run_config.py:298 card-construction site left untouched per the checker INFO).

## Verification Evidence

| Check | Command | Result |
|-------|---------|--------|
| Task 1 lane | `uv run --group dev pytest tests/tui/test_pilot_selection.py -q` | **38 passed** (34 baseline + 4 new; the 08-08 chain tests stay green) |
| Task 2 lane | `uv run --group dev pytest tests/tui/test_card_site_hardening.py tests/tui/test_work_site_hardening.py -q` | **3 passed** (card pin ×2 incl. positive control + the 08-08 @work pin) |
| Full suite (final tree) | `uv run --group dev --group tui pytest -q` | **7 failed / 1731 passed / 9 xfailed** — the failure set byte-identical to the locked box baseline (same 7: 6 documented data/schema + 1 machine-state storage-overview); 1731 = 1725 baseline + 6 new tests; ZERO new failures |
| Lint | `make lint` | All checks passed |
| Typecheck | `make typecheck` (ty, dev+tui groups) | All checks passed |
| Verifier reproduction 1 (post-fix) | the w Pilot test over the real app + real backend | wizard pushed, `app._exception` None, officials' species/tokenizer vocabularies populate, the degraded card contributes nothing |
| Verifier reproduction 2 (post-fix) | the degraded-row enter Pilot test (t → filter → tab → enter) | card-less RowDetailModal pushed (entry_key the key, `_card == {}`, empty log), `app._exception` None |
| Prohibition: snapshots | `git status --short -- tests/tui/__snapshots__/` | clean (untouched) |
| Prohibition: loader contract | `git diff 0559c40..HEAD -- pipeline/registry_loader.py` | empty (byte-unmodified) |
| Prohibition: services/strings/deps | `git diff 850e047..HEAD --stat -- tui/strings.py tui/services/ pyproject.toml uv.lock` | 0 lines — zero new strings constants, services byte-unchanged, zero new dependencies, textual pinned 8.2.8 |

## Known Stubs

None — no stubs, no skipped tests, no unrun verifies. All lanes and gates executed on this box.

## Gap Truths — closure status

- **w never exits** (any cursor, no row interaction): the wizard opens over the officials' vocabularies, the degraded card contributes no species/tokenizer entry — **closed** (test_w_press_survives_non_dict_card_and_opens_wizard).
- **enter never exits on the degraded row** (ALL pool, filter-narrowed, table-focused): the card-less RowDetailModal opens with the key as border title and an empty detail log, app alive — **closed** (test_enter_on_degraded_row_opens_cardless_detail_modal).
- **d never exits on the degraded row**: silent-and-alive through the UNKNOWN-presence shield, AND `_manual_landing_path` no longer leans on the `or {}` idiom (direct unit call returns None without raising) — **closed** (test_d_press_on_degraded_row_stays_silent_and_alive + test_manual_landing_path_returns_none_for_non_dict_card).
- **The family cannot regrow**: the AST pin enforces the four-function guard-carrying allowlist, the ≥4-node floor, and the positive-control detector proof over every tui/**/*.py — **closed** (test_every_card_extraction_site_is_guarded + test_scanner_flags_unguarded_extraction_positive_control).
- **Zero new failures against the locked box baseline; ruff + ty clean; snapshots untouched; zero new dependencies; zero new strings constants** — **closed** (the verification table above).

Phase 8 Truth 6 can flip to verified on re-verification — every consumer of the tolerant loader's output (load-path seams AND screen-side action paths) now degrades on the loader-accepted non-dict card.

## Self-Check: PASSED

All created/modified files exist on disk; all three commits (f69d616, fd5009d, a1d1591) verified as ancestors of HEAD via `git merge-base --is-ancestor`.
