# Phase 1: Audit & Release Foundations - Context

**Gathered:** 2026-10-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the repository safe for public visibility with every leaderboard-number change attributable: a fresh systematic audit of all three subsystems (AUDIT-01), a frozen pre-fix `data-v1` baseline (AUDIT-02), LICENSE (REL-01), version-pinned dependency manifests with a validated pin baseline (REL-02), the settled secret-hygiene decision (REL-05), and deterministic data generators (FIX-05). Not in this phase: any behavioral fix beyond determinism (Phase 4), tests/CI (Phase 2/5), pipeline adaptation (Phase 3).

</domain>

<decisions>
## Implementation Decisions

### Audit depth & destination
- **D-01:** Fresh systematic review — parallel review agents across the three subsystems (pipeline / data scripts / frontend); `.planning/codebase/CONCERNS.md` is input, not conclusion; every finding must be reproduced/verified and severity-graded before entering the report
- **D-02:** Audit report is published in-repo as `AUDIT.md` (cleaned, public) — transparency toward reviewers is the milestone's selling point
- **D-03:** Findings beyond existing REQ-IDs are placed by tier: anything affecting leaderboard correctness or page function joins Phase 4 scope; the rest (dead code, performance, log noise) goes to the milestone backlog
- **D-04:** Audit effort is correctness-first: deep-dive aggregation math (rank/MinMax/z-score/robust), FLOPs extrapolation, pipeline config mutation, data-flow consistency; maintainability findings are recorded but not severity-graded

### Dependency pin baseline (REL-02)
- **D-05:** Original data-generation environment (2026-03-31 data) no longer exists — pin by floor bounds (`pandas>=2.2,<3.0` latest 2.x, numpy bounded alongside) and validate by regenerating the data chain, comparing values against committed JSONs — **Reversibility:** costly — pins propagate into uv.lock, CI matrix, and every consumer environment once published
- **D-06:** Validation standard: any value difference → stop and investigate (version behavior change / floating-point / hidden bug) until explained; only then are pins authoritative
- **D-07:** Data-chain environment: repo-local uv-managed venv, **Python 3.13**, strictly isolated from `/home/forrest/Github/DNALLM/.venv` (pandas 3.0.6 — reserved for Phase 3 pipeline adaptation); uv 0.12.23 already installed at `~/.local/bin/uv`

### Token & visibility (REL-05 — substance changed by maintainer decision)
- **D-08:** The Zenodo record-19135551 preview link + token at `README.md:116` **stays as-is** — it is the intentional dataset-sharing mechanism (record-scoped, read-only); do NOT revoke, do NOT rewrite git history for it; a full-history secret scan remains useful only to confirm no OTHER secrets exist beyond this known-intentional link
- **D-09:** Repo visibility assumed private now, flipping public at milestone end (default framing; user did not correct when offered)

### License (builder default — user declined discussion)
- **D-10:** MIT per the existing README badge (`README.md:3`), with a separate data-terms statement for derived leaderboard data — user may override any time before planning lands it — **Reversibility:** one-way once publicly released — a license is a public contract; changing it after release requires relicensing consent

### Claude's Discretion
- Severity scheme and report structure for AUDIT.md (suggest P0/P1/P2 with file:line + reproduction + recommended fix per finding)
- How review agents are partitioned (by subsystem × dimension)
- pyproject.toml / uv.lock / requirements.txt-export structure (follow `.planning/research/STACK.md` recommended stack)
- Exact form of the `data-v1` baseline artifact (tag + golden copies vs tag-only)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Codebase intel (audit input)
- `.planning/codebase/CONCERNS.md` — full known-concerns inventory (2026-10-08, mapped at `a44d310`); includes bugs beyond current REQ-IDs (sorting, nesting iteration, pipeline config leak, models_info sync)
- `.planning/codebase/ARCHITECTURE.md` — system structure, data flows, the JSON seam contract
- `.planning/codebase/STACK.md` — current stack facts, no-manifests status

### Research (verified 2026-10-08)
- `.planning/research/STACK.md` — verified tool versions, pandas-3.0 hazard, SHA-pinned CI actions
- `.planning/research/PITFALLS.md` — number-migration practice, float tolerances, secret-handling guidance
- `.planning/research/SUMMARY.md` — synthesized strategy, dependency ordering

### Repo facts referenced in discussion
- `README.md` line 116 — the intentional Zenodo preview link
- `script/summarize_comparison.py` (line 309 unsorted `os.listdir`; lines 381/408 `json.dump` without `sort_keys`), `script/get_task_performance.py` line 159, `scripts/generate-tasks-index.js` (lines 18, 56) — determinism fix sites (FIX-05)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- The three data scripts (`script/summarize_comparison.py`, `script/get_task_performance.py`, `scripts/generate-tasks-index.js`) — both the determinism-fix targets and the regeneration-validation vehicle for D-05/D-06
- `.planning/codebase/` map set — seed inventory for the audit agents
- uv 0.12.23 on PATH; `/usr/bin/python3.12` and brew 3.14 available (env picks 3.13 via uv)

### Established Patterns
- Data scripts must run from `dnallm-mark/data/` (relative-path CWD coupling) — keep accommodating, don't refactor (surgical discipline)
- Performance-JSON seam `{info, performance}` is load-bearing across producers/consumers — Phase 2 locks it as schemas

### Integration Points
- New `pyproject.toml` at repo root (data/dev/pipeline dependency groups; pipeline group never CI-installed)
- `data-v1` git tag on the pre-fix commit; AUDIT.md at repo root
- Baseline capture must happen BEFORE the determinism fix lands (byte layout changes once)

</code_context>

<specifics>
## Specific Ideas

- User explicitly clarified: "regeneration" means the CPU-only 3-script data chain over the 42 committed `model_performance/*.json` — never re-running model fine-tuning
- Token link intent in user's words: "是要共享给大家的" (it is meant to be shared with everyone)

</specifics>

<deferred>
## Deferred Ideas

- Zenodo record 19135551: after formal publish, swap the README link to the clean token-free record URL (preview tokens invalidate naturally on publish) — post-release nicety, not milestone work

</deferred>

---

*Phase: 1-Audit & Release Foundations*
*Context gathered: 2026-10-08*
