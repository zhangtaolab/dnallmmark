---
phase: 01-audit-release-foundations
plan: "03"
subsystem: infra
tags: [determinism, sorted-iteration, sort_keys, data-migration, gitleaks, secret-scan, license, mit, cc-by, reproducibility]

requires:
  - phase: 01-01
    provides: "data-v1 frozen baseline (tag + SHA256 manifest) and the --summary-json comparator contract this plan's migration gate consumes"
  - phase: 01-02
    provides: "published AUDIT.md with the pre-documented expected migration inventory and the secret-scan evidence placeholder"
provides:
  - "Deterministic data generators: sorted(os.listdir) in both Python scripts, sort_keys=True on all four json.dump calls, no live-clock stamp in the JS index generator"
  - "One-time fully-attributed migration of the 52 derived data files against data-v1 (every diff class gated; run-twice byte-identity proven)"
  - "Post-fix migration record in AUDIT.md (observed counts, fourth-tie-pair D-06 investigation, stamp-drop rationale)"
  - "LICENSE (MIT per D-10) + README License section with separate CC BY 4.0 data terms and upstream-terms disclaimer verified via git ls-files"
  - ".gitleaks.toml (default rules + zenodo-preview-token detection rule + rule-scoped AND allowlist) and the full-history two-scan proof recorded in AUDIT.md"
affects: [phase-2-tests, phase-5-ci, phase-4-fixes, release-packaging]

actuals:
  tokens: 1439176   # chars/4 over the realized diff — dominated by the 52-file deterministic key-order regeneration (~122k changed JSON lines); source/config/doc edits alone are a small fraction
  tasks: 3
  commits: 4

tech-stack:
  added:
    - "gitleaks 8.30.1 (brew-bottled) — full-history secret scan over all refs"
  patterns:
    - "Two-scan secret proof: rules-only probe (expect exactly the 1 known finding) + committed-config production scan (expect 0) — scanner behavior verified rather than trusted"
    - "Rule-scoped [[rules.allowlists]] with condition AND instead of global path allowlists (global paths = file-level exclusion in gitleaks 8.30.1)"
    - "Migration gate: complete machine-readable inventory (baseline/compare.py --summary-json) with required-present assertions so an unregenerated tree cannot pass vacuously"

key-files:
  created:
    - LICENSE
    - .gitleaks.toml
  modified:
    - script/summarize_comparison.py
    - script/get_task_performance.py
    - scripts/generate-tasks-index.js
    - dnallm-mark/data/models_comparison.json
    - dnallm-mark/data/models_comparison_animal.json
    - dnallm-mark/data/models_comparison_plant.json
    - dnallm-mark/data/models_comparison_microbe.json
    - dnallm-mark/data/tasks.json
    - dnallm-mark/data/task_performance/ (47 files, key order only)
    - README.md
    - AUDIT.md

key-decisions:
  - "Fourth exact-tie pair (plant file, caduceus-ph vs space, rank_score 116.0) accepted into the migration inventory after D-06 investigation: exact tie on both file sides, sorted() resolves it alphabetically, and the plan-01-01 pin-validation evidence could not have exposed it (that run's os.listdir order coincidentally matched the committed order). Complete census: 6 tie groups exist; sorted() flips exactly the 4 whose committed order is non-alphabetical — which is also why the two pre-documented global pairs do NOT actually swap"
  - "generatedAt dropped from tasks.json output (planner decision per Pitfall 6): no frontend consumer, input-derived stamps unstable across clones, Phase 5 reintroduces an authoritative data-version stamp"
  - "gitleaks config carries a zenodo-preview-token DETECTION rule: the 8.30.1 built-in jwt rule misses JWTs closed by a markdown-link ')' (the exact README shape), so without the rule the allowlist would be vacuous"
  - "Allowlist scoped inside the rule ([[rules.allowlists]] AND condition), not as a global block: a global [[allowlists]] with paths acts as file-level exclusion in 8.30.1 and silences every rule's findings in README.md — canary-proven, violates the REL-05 narrowness prohibition"
  - "Probe scan runs with an explicit rules-only config because gitleaks auto-loads ./.gitleaks.toml from CWD when --config is omitted (the committed allowlist would make the probe vacuous)"
  - "SURFACED ASSUMPTION (maintainer may override before the repo flips public): copyright holder named as 'Copyright (c) 2026 Tao Zhang and DNALLM-Mark contributors' — derived from git author + remote organization; cheap to change now, contractual after release"

patterns-established:
  - "data-v1 -> deterministic generators migration record form: expected-vs-observed inventory table with per-file counts, investigated additions documented inline, never rewritten after the fact"
  - "Secret-scan evidence form: both command lines + exit codes + location-only finding references + the config-decision record for reviewer scrutiny"

requirements-completed: [FIX-05, REL-01, REL-05]

coverage:
  - id: D1
    description: "Deterministic generators (FIX-05): sorted iteration in both Python scripts, sort_keys on all four dumps, live-clock stamp removed; run-twice byte-identity across all 52 outputs"
    requirement: FIX-05
    verification:
      - kind: other
        ref: "edit-site greps: sorted(os.listdir) 1/1, sort_keys=True 2/1 (exact counts); ! grep 'new Date' scripts/generate-tasks-index.js"
        status: pass
      - kind: other
        ref: "second full-chain run sha256sum -c clean across 52 files (BYTE-IDENTICAL-RUN2, executed twice)"
        status: pass
      - kind: other
        ref: "tasks.json top-level keys exactly [count, tasks, version]; version 1.0.0 and count 47 unchanged"
        status: pass
    human_judgment: false
  - id: D2
    description: "One-time data migration fully attributed against data-v1 (47/47 task files value-identical; comparison/index diffs only in documented classes; AUDIT.md Post-fix migration record)"
    requirement: FIX-05
    verification:
      - kind: other
        ref: "migration gate over 52 --summary-json inventories: FLOAT_ULP only on /performance/sum_zscore (164, max rel 5.98e-14), FLOAT_BIG only on exact-tie /performance/rank paths, tasks.json casing + generatedAt both required present; MIGRATION-INVENTORY-OK re-run post-commit"
        status: pass
      - kind: other
        ref: "data-v1 tag still at 788e909 (pre-fix commit); no re-tagging"
        status: pass
    human_judgment: true
    rationale: "Acceptance of the fourth exact-tie pair into the inventory (and of the two global pairs NOT swapping) is correctness judgment over investigated evidence — a reviewer should confirm the D-06 reasoning in AUDIT.md's Post-fix migration record before the migration commit is treated as fully attributed."
  - id: D3
    description: "LICENSE (MIT per D-10) + README License section with separate CC BY 4.0 data terms, upstream-terms disclaimer, Project Structure tree update, atomic single commit, D-08 link untouched"
    requirement: REL-01
    verification:
      - kind: other
        ref: "LICENSE contains MIT License text + exactly one 'Copyright (c) 2026' line; README exactly one License section, CC BY 4.0 stated"
        status: pass
      - kind: other
        ref: "git diff data-v1 -- README.md has zero ^[+-].*zenodo lines (line 116 byte-identical); git ls-files spot-check: 94 tracked JSONs only, zero raw dataset files"
        status: pass
      - kind: other
        ref: "all eight new root paths present in the Project Structure tree; LICENSE + README in single commit 8a78c4a"
        status: pass
    human_judgment: false
  - id: D4
    description: "gitleaks full-history scan over all refs with narrow rule-scoped allowlist; evidence in AUDIT.md citing location only (REL-05)"
    requirement: REL-05
    verification:
      - kind: other
        ref: "probe (rules-only config, --log-opts=--all): exit 1, exactly 1 finding, File=README.md line 116, RuleID zenodo-preview-token"
        status: pass
      - kind: other
        ref: "production (committed config, --log-opts=--all): exit 0, zero findings"
        status: pass
      - kind: other
        ref: "AND-semantics canary proof: 19135551-link in other file caught; classic JWT in README.md caught; different-record link in README.md caught; exact README+19135551 suppressed"
        status: pass
      - kind: other
        ref: "AUDIT.md Secret-scan evidence section present, placeholder gone, zero token text in AUDIT.md/.gitleaks.toml"
        status: pass
    human_judgment: false

duration: 16min
completed: 2026-10-08
status: complete
commits: 4
plan_head_before: c1cfb878e75d65a82c95f878178a4edebb683f3a
plan_head_after: 511a1006594ad767c69a7716ae8758bbc59b4e70
---

# Phase 01 Plan 03: Deterministic Generators + Data Migration + Release Hygiene Summary

**Deterministic generators landed with the one-time, fully-attributed 52-file data migration (run-twice byte-identity proven), MIT LICENSE with separate CC BY 4.0 data terms, and a gitleaks full-history two-scan proof that exactly one intentional secret exists.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-10-08T14:37:24Z
- **Completed:** 2026-10-08T14:54:19Z
- **Tasks:** 3
- **Files modified:** 59 (2 created, 57 modified; 52 of those are the regenerated derived-data tree)

## Accomplishments

- **FIX-05 executed surgically (Task 1, tracer):** the five Python edit sites exactly as pattern-mapped (sorted iteration pins float-summation order and tie-breaks, not just key layout; sort_keys on all four dumps) plus the JS stamp removal — with CWD-relative config blocks untouched. Tracer feedback gate discharged: the automated-only verify suite was re-run end-to-end post-commit (edit greps, full migration gate, determinism run-twice, AUDIT record) — all PASS — and execution expanded without a checkpoint (end-of-phase mode).
- **One-time migration fully attributed:** 47/47 task_performance files VALUES IDENTICAL; 164 FLOAT_ULP diffs confined to sum_zscore (max rel 5.98e-14); 4 FLOAT_BIG diffs confined to exact-tie rank pairs; tasks.json limited to the metric-casing VALUE and generatedAt MISSING_IN_REGEN (both required present by the gate so an unregenerated tree cannot pass vacuously). Every diff count cross-checked for total == len(diffs) == sum(counts). Observed inventory recorded in AUDIT.md's Post-fix migration record.
- **D-06 investigation of a fourth exact-tie pair** (the gate's one out-of-inventory hit): caduceus-ph vs space at rank_score 116.0 in the plant file — exact tie on both sides, alphabetical resolution, and a root-caused explanation of why the pin-validation evidence could not expose it. Complete tie census recorded (6 groups; 4 flip, 2 already alphabetical — which also explains why the two pre-documented global pairs do not actually swap).
- **LICENSE + README landed atomically (Task 2):** canonical MIT text with the surfaced copyright-holder assumption; README License section declaring MIT for code, CC BY 4.0 for repo-produced derived aggregates, and the upstream-terms disclaimer spot-verified via git ls-files (94 tracked JSONs, zero raw dataset files); Project Structure tree extended with the eight new root paths; the README:116 Zenodo link byte-for-byte unchanged (D-08).
- **Secret hygiene settled with a behavioral two-scan proof (Task 3):** probe over all refs finds exactly the one known intentional README link; the committed-config production scan finds zero. The scanner's own blind spots were found and fixed empirically — the built-in jwt rule misses markdown-paren-closed JWTs (detection rule added), and global path allowlists act as file-level exclusion (rule-scoped AND allowlist used, canary-proven in both directions). Evidence recorded in AUDIT.md with location-only references.

## Task Commits

Each task was committed atomically:

1. **Task 1: FIX-05 determinism edits + one-time regeneration migration (tracer)** - `5620988` (fix: generators) + `6a8495a` (fix: 52-file migration + AUDIT.md record)
2. **Task 2: LICENSE (MIT per D-10) + README license section with separate data terms** - `8a78c4a` (docs)
3. **Task 3: gitleaks full-history scan with narrow allowlist + evidence** - `511a100` (chore)

**Plan metadata:** *(final docs commit follows)*

## Files Created/Modified

- `script/summarize_comparison.py` - sorted(os.listdir) at the read loop; sort_keys=True on total + species dumps
- `script/get_task_performance.py` - sorted(os.listdir); sort_keys=True on the task dumps
- `scripts/generate-tasks-index.js` - generatedAt live-clock property removed; version/count/tasks keys unchanged
- `dnallm-mark/data/` (52 files) - the one-time deterministic migration (key order everywhere; value diffs only in the gated classes)
- `LICENSE` - MIT, Copyright (c) 2026 Tao Zhang and DNALLM-Mark contributors
- `README.md` - License section (MIT / CC BY 4.0 / upstream terms) + Project Structure tree with eight new root paths
- `.gitleaks.toml` - default rules + zenodo-preview-token detection rule + rule-scoped AND allowlist for the README record-19135551 link
- `AUDIT.md` - Post-fix migration record appended; Secret-scan evidence placeholder replaced

## Decisions Made

- Fourth exact-tie pair accepted after investigation (same D-06 path as plan 01-01's third pair); the migration-gate TIE regex extended to the AUDIT.md inventory class — the plan's own action defers to the AUDIT.md inventory as authoritative.
- generatedAt dropped per the planner decision (Pitfall 6); Phase 5 owns the authoritative data-version stamp.
- gitleaks config gains a detection rule and uses a rule-scoped allowlist — both empirically necessary for the config to detect what it watches and to keep the allowlist maximally narrow (REL-05 prohibition honored: exactly one AND-conditioned entry, no path-only or regex-only suppression).
- **SURFACED ASSUMPTION for maintainer override before the repo flips public (D-09):** the LICENSE copyright holder is named "Tao Zhang and DNALLM-Mark contributors" (derived from git author + remote org). One-line edit now; relicensing consent later.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Investigation] Fourth exact-tie rank pair outside the enumerated migration inventory**
- **Found during:** Task 1 (migration gate)
- **Issue:** The gate flagged caduceus-ph_seqlen-131k_d_model-256_n_layer-16 vs space (plant file, ranks 37↔36) as OUT-OF-INVENTORY; the plan's verify TIE regex named only the two global pairs.
- **Fix:** D-06 investigation: exact tie (rank_score 116.0) on both file sides; complete census found 6 tie groups, sorted() flips exactly the 4 whose committed order is non-alphabetical; the pin-validation evidence missed this pair because that machine's os.listdir order coincidentally matched the committed order (space idx 15 < caduceus idx 20). Gate regex extended to the documented inventory class; investigation + census recorded in AUDIT.md's Post-fix migration record.
- **Files modified:** AUDIT.md
- **Verification:** gate re-run clean (MIGRATION-INVENTORY-OK); tie values quoted from both sides; both non-flipping pairs confirmed already-alphabetical.
- **Committed in:** `6a8495a`

**2. [Rule 2 - Missing critical functionality] gitleaks default rules cannot detect the intentional link's token class**
- **Found during:** Task 3 (probe scan)
- **Issue:** The no-allowlist probe returned 0 findings — the plan's proof (expect exactly 1 README.md finding) was unsatisfiable: gitleaks 8.30.1's built-in jwt rule does not match JWTs closed by a markdown-link ")" (empirically proven with both the real link and synthetic tokens: caught at end-of-line, missed before ")"). The committed allowlist would have been vacuous.
- **Fix:** Added the zenodo-preview-token detection rule to .gitleaks.toml (default ruleset stays fully active). Probe then found exactly 1 finding: README.md:116, commit 09fb0ae.
- **Files modified:** .gitleaks.toml
- **Verification:** probe exit 1 / 1 finding / File=README.md; production exit 0.
- **Committed in:** `511a100`

**3. [Rule 1 - Bug] Global allowlist form over-suppresses (would violate the REL-05 prohibition)**
- **Found during:** Task 3 (AND-semantics verification, assumption A7)
- **Issue:** A top-level [[allowlists]] with paths — the RESEARCH skeleton's form — behaves as file-level exclusion in 8.30.1: a classic JWT placed in README.md and a different-record Zenodo link in README.md both went undetected (silently disabling future-secret detection in README.md).
- **Fix:** Moved the allowlist inside the rule as [[rules.allowlists]] with condition AND. Canary-proven: 19135551-link elsewhere caught; classic JWT in README.md caught; different-record link in README.md caught; only README.md + record-19135551 suppressed.
- **Files modified:** .gitleaks.toml
- **Verification:** four-direction canary matrix (ta/tb1/tb2/tc scans) + production scan clean.
- **Committed in:** `511a100`

**4. [Planned adjustment - Probe mechanics] Probe runs with an explicit rules-only config**
- **Found during:** Task 3
- **Issue:** The plan's literal probe command (no --config) auto-loads ./.gitleaks.toml from CWD once that file exists, so the allowlist would suppress the probe finding and the proof would be vacuous.
- **Fix:** Probe uses /tmp/gitleaks-probe-config.toml (defaults + detection rule, no allowlist). Documented in the AUDIT.md evidence section.
- **Files modified:** AUDIT.md (documentation)
- **Verification:** probe/production assertion pair passes; auto-load behavior demonstrated empirically.
- **Committed in:** `511a100`

---

**Total deviations:** 4 auto-fixed (1 D-06 investigation, 1 Rule 2 detection gap, 1 Rule 1 config hazard, 1 planned probe-mechanics adjustment)
**Impact on plan:** None on deliverable shape — every acceptance criterion passes; the deviations strengthened the evidence (documented census, behavioral scanner proof) rather than changing any artifact decision.

## Issues Encountered

None blocking. Two gitleaks behaviors (default jwt rule paren blindness; CWD config auto-load) were discovered during verification and handled as deviations 2-4 with empirical proof.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 1 is complete: audit published (01-02), baseline frozen + env pinned (01-01), determinism landed + migration attributed + release hygiene settled (this plan).
- The data chain is now byte-reproducible by construction — Phase 2's determinism tests can regenerate and byte-compare against the committed tree; Phase 5's TEST-07 regenerate-and-diff job no longer has a built-in date-stamp failure.
- The gitleaks config + documented scan commands are ready for Phase 5 CI wiring.
- One maintainer action remains open by design: the LICENSE copyright-holder naming (surfaced assumption above) should be confirmed or edited before the repo flips public at milestone end (D-09).

## Self-Check: PASSED

All key files exist on disk (LICENSE, .gitleaks.toml, both Python generators, JS indexer, README.md, AUDIT.md, tasks.json; 47 task_performance files); all 4 task commits (`5620988`, `6a8495a`, `8a78c4a`, `511a100`) are ancestors of HEAD; measured commits from ledger `git rev-list --count c1cfb87..HEAD` = 4, matching frontmatter; data-v1 tag unchanged at 788e909; tracer verify suite re-run end-to-end post-commit all-PASS.

---
*Phase: 01-audit-release-foundations*
*Completed: 2026-10-08*
