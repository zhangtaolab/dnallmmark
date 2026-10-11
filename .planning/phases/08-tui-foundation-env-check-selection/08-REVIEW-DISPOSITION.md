---
phase: 08-tui-foundation-env-check-selection
generated: 2026-10-11T16:29:19Z
review: 08-REVIEW.md
review_status: issues_found
total: 14
open: 10
resolved: 9
deferred: 0
---

# Review Disposition — Phase 08

One row per finding in 08-REVIEW.md. Default disposition: `open` — a triaged finding is distinguishable downstream from a forgotten one.

| ID | Disposition | Commit | Note |
|----|-------------|--------|------|
| CR-01 | fixed | 0b5405e | Text-rendered help rows + hidden-binding filter |
| CR-02 | fixed | 7956c2d | OSError catches in export/tiers/save + strings copy |
| CR-03 | fixed | 76aa1cd | matrix degraded-state compose + is_valid_coordinate guards |
| WR-01 | fixed | 9cc1879 | pop-only-when-top + action_help suppression |
| WR-02 | fixed | 932703f | run-id message tagging + handler drops + persist poll |
| WR-03 | fixed | 7a4ca2b | task-omitting tier-1 pairs accepted in derive_presets |
| WR-04 | fixed | 2b5f27a | preset_menu moved to exclusive worker |
| WR-05 | fixed | d2ce620 | empty-overlay pins on machine-dependent tests |
| IN-01 | open | | Info — out of fix scope, persists per loop contract |
| IN-02 | open | | Info — out of fix scope, persists per loop contract |
| IN-03 | open | | Info — out of fix scope, persists per loop contract |
| IN-04 | open | | Info — out of fix scope, persists per loop contract |
| IN-05 | open | | Info — out of fix scope, persists per loop contract |
| IN-06 | open | | Info — out of fix scope, persists per loop contract |

## Legend
- `open` — not yet triaged or fixed
- `fixed` — a commit resolved the finding (recorded by the fix flow)
- `wontfix` / `deferred` — accepted with rationale (requires a Note)
