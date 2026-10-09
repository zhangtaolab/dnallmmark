---
phase: "02"
slug: "data-contracts-test-harness"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-09"
---

# Phase 02 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| PyPI registry → dev group / uv.lock | dev-toolchain dependency resolution crosses the network; a misresolved package silently changes test/suite behavior | pinned package metadata + hashes |
| make data regeneration path | the single-command recipe rewrites derived data; an unattributed write corrupts the baseline discipline | derived leaderboard JSON bytes |
| tests/fixtures/ | synthetic inputs and goldens are executable-test inputs masquerading as data; tampered fixtures could mask regressions | fixture JSON bytes |
| pytest tmp confinement | determinism/JS tests must never leak writes into the committed tree | regenerated outputs |
| node invocation (no npm) | JS test execution must stay dependency-free per the no-npm architectural constraint | Node builtins only |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-02-01 | Tampering | pyproject.toml dev group / uv.lock | high | mitigate | RESEARCH Package Legitimacy Audit approved pytest/jsonschema/ruff; uv.lock pins exact versions with hashes; `uv lock --check` is a verify gate — re-verified exit 0 twice this session (post-execution and regression gate) | closed |
| T-02-02 | Tampering | make data regeneration path | medium | mitigate | `make data` hard-fails on any git status output under dnallm-mark/data/; diffs adjudicated against the D-06 vocabulary; chain never writes model_performance/ inputs — zero-diff proven on every run this session (executor, verifier, orchestrator re-runs) | closed |
| T-02-SC | Tampering | uv installs (pytest, jsonschema, ruff) | high | mitigate | All three packages empirically installed and probed live on Python 3.13 during research; no [ASSUMED]/[SUS] install remains (matches Phase 1 T-01-SC disposition); hashes pinned in uv.lock | closed |
| T-02-03 | Tampering | tests/fixtures/ (synthetic models + goldens) | medium | mitigate | Goldens chain-produced and committed in the same task that proves zero-diff regeneration; fixtures reviewed like code and schema-validated in-suite (bucket canary pins 42/47/4/1 — WR-03 fix); tests parse with stdlib json only | closed |
| T-02-04 | Tampering | tests/js/generate-tasks-index.test.js | low | mitigate | Copy trick confines the generator's import-time execution to an OS mkdtemp fixture tree (never the repo tree); asserts run against tmp-produced tasks.json only — suite runs left the committed tree clean | closed |
| T-02-SC | Tampering | node test execution | low | mitigate | JS suite uses Node builtins exclusively (node:test/assert/fs/path/child_process) — zero npm installs, no package.json (architectural constraint held; code review confirmed) | closed |
| T-02-05 | Tampering | tests/test_determinism.py write scope | high | mitigate | Test copies inputs into pytest tmp and asserts `git status --porcelain -- dnallm-mark/data/` empty at end of every run; JS step runs a script COPY in tmp — post-suite porcelain empty on every full-suite run this session (6× stability runs + fix-round gates) | closed |
| T-02-06 | Repudiation | tests/test_known_defects.py locks | medium | mitigate | `strict=True` (XPASS fails the suite); `--runxfail` probe proves each lock fails on the real defect (5 FAILED verified by verifier and fix round); every reason string names the finding ID; markers removed only in the fix commit | closed |
| T-02-SC | Tampering | node invocation inside determinism test | low | mitigate | Plain node running a copied first-party script with Node builtins only — no packages, no network, tmp-confined | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|

*Accepted risks do not resurface in future audit runs.*

*If none: "No accepted risks."*

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-09 | 9 | 9 | 0 | verify-work complete_session dispatch (L1 short-circuit: threats_open 0, register authored at plan time, asvs_level 1; evidence from execution + verification + fix-round runs this session) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-09
