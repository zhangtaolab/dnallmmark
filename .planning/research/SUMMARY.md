# Project Research Summary

**Project:** DNALLM-Mark — public-release hardening of a DNA LLM benchmark platform
**Domain:** Brownfield quality/release engineering for a research benchmark repo (static no-build JS leaderboard MPA + offline Python/Node data scripts + GPU PyTorch pipeline, the latter permanently out of CI scope)
**Researched:** 2026-10-08
**Confidence:** HIGH for release-blocking decisions — every P1 recommendation rests on primary-verified sources (package registries, official docs, direct codebase inspection). Residual MEDIUM/LOW items affect v1.x polish, not the release-blocking set.

## Executive Summary

DNALLM-Mark is not a greenfield build — it is a hardening milestone over three existing subsystems (static leaderboard MPA, offline data chain, GPU pipeline). The survey of comparable platforms (HELM, lm-evaluation-harness, DNABERT-2/GUE, BEND, Nucleotide Transformer, GenBench CBT) shows that credible benchmark repos run exactly the shape this research recommends: pinned dependency manifests, CPU-only pytest suites over synthetic fixtures, path-filtered CI with lint/test jobs, and versioned changelogged results. No surveyed DNA benchmark ships CI-validated derived data — DNALLM-Mark can make that a genuine differentiator cheaply, because the machinery (committed source JSON, three-script chain) already exists. The FLOPs-efficiency instrumentation is already built and unmatched by any competitor; it needs documentation, not construction.

The recommended approach is to wrap, not rewrite: a verification layer (tests, schemas, Makefile, CI) is layered read-only around the existing runtime, and the only writer of committed derived data remains a maintainer running the regeneration chain. Ordering is the whole game. Determinism fixes (~4 lines: sorted directory listing, `sort_keys`) must precede every diff-based check; dependency manifests must precede CI; JSON Schemas must lock the data contract *before* correctness fixes move the numbers; unit tests must exist *before* the species-grouping fix (failing-test-first); and recomputation must happen last, under full CI protection, with a before/after changelog and a version stamp so the number migration is auditable rather than suspicious. The Zenodo token revocation is the one P1 item that cannot be expressed as a commit — it is a manual, out-of-repo action that must happen first.

The dominant risks are procedural, not technical: silently migrating leaderboard numbers (P1), over-refactoring during hardening (P2), float-coupled flaky tests (P3), goldens that block legitimate refreshes (P4), CI that cannot run locally (P5), treating README-deletion as token cleanup (P6), and applying one code license to 50 redistributed datasets (P7). Each has a concrete, cheap prevention documented in PITFALLS.md — tolerances and thread-pinning decided at scaffold time, layered goldens, thin Makefile-driven CI, revocation-first, dual license declaration. Two decisions research cannot make for the maintainer: the code license (Apache-2.0 recommended, DNABERT-2 precedent) and confirming the exact pandas/numpy versions of the known-good data-generation environment before locking pins.

## Key Findings

### Recommended Stack

Summary from [STACK.md](STACK.md) — every version verified against primary registries on the research date; confidence HIGH.

The stack is deliberately boring and split along the milestone's hard boundary: a GPU-less Python/Node toolchain for everything CI touches, with the torch/dnallm pipeline documented in a separate dependency group and never installed in CI. A single `pyproject.toml` (PEP 621 + PEP 735 dependency-groups, `[tool.uv] package = false` virtual project) describes the whole system without making the repo a package.

**Core technologies:**
- **uv 0.12.23 + uv.lock** — dependency resolution and lockfile; the reproducibility guarantee for a repo whose core value is "every number is reproducible"
- **pytest 9.1.1** — test standard; parametrize + `tmp_path` fit JSON-in/JSON-out script testing exactly
- **node:test (Node 24 LTS)** — zero-dependency runner for `generate-tasks-index.js` tests and the internal-link check; pin CI to Node 24 (satisfies every tool's engines)
- **ruff 0.16.10** — one tool replacing flake8+isort+black; doubles as a free static audit of the data scripts
- **ESLint 10.12.0 (flat config) + globals** — lints the no-build MPA directly with no bundler; dev-only `package.json`, site files stay raw
- **html-validate 11.16.2** — offline HTML5 structural check in CI, no browser (chosen over vnu for recurring CI; over htmlhint for verified configurability)
- **jsonschema 4.26.0 (Python)** — validates leaderboard JSON in pytest, keeping ONE test runner for the repo
- **GitHub Actions, SHA-pinned** — free on standard runners for public repos; `permissions: contents: read`; SHA pins are GitHub's only immutable release form
- **pre-commit 4.6.2** — local hygiene gate (`check-json` catches corrupt derived JSON before commit)

**Critical version constraints:**
- **pandas `>=2.2,<3.0`** — pandas 3.0.0 (2026-01-21) silently changes aggregation semantics (string dtype, copy-on-write, groupby behavior); unpinned installs get 3.0.6 and numbers drift with no code change. This is exactly the bug class the milestone exists to prevent. The authoritative pin is the known-good env export (see Gaps).
- **numpy `>=2.0,<3`** (2.5.3 requires Python >=3.12); CI matrix Python 3.12/3.13 + one Node 24 job.
- GPU deps (`torch`, `dnallm`) in a `pipeline` dependency group, never installed in CI — the install list *is* the boundary enforcement.

### Expected Features

Summary from [FEATURES.md](FEATURES.md) — all P1 items justified by the live-verified repo survey and academic release checklists.

**Must have (table stakes — the release-blocking set):**
- Revoked Zenodo token — a live secret in a public repo is an incident, not a release
- LICENSE (recommend Apache-2.0; DNABERT-2 precedent) — "without a license your software cannot be legally reused"
- Pinned dependency manifests for the data chain, separate from GPU pipeline notes
- Correctness fixes: navbar/render (all pages), species-as-dataset grouping, submit-flow repair
- Unit tests for aggregation/pivot logic (synthetic fixtures, CPU-only) — tests are what separate well-run repos (HELM, lm-eval, GenBench) from typical academic ones
- GitHub Actions CI + README badge
- Documented single-command regeneration chain (Makefile target)
- Data recomputation + CHANGELOG.md with before/after comparisons
- README reproducibility section, dataset provenance table, BibTeX citation

**Should have (differentiators — cheap because machinery exists):**
- Results versioning: git tag per data refresh + "data generated: DATE, pipeline: SHA" stamp
- Restored PR-based submission flow (the only submission model compatible with a static, backend-less site); label submissions self-reported
- CI validation of derived data via JSON Schema — no surveyed DNA benchmark does this
- Aggregation-methodology documentation (rank/MinMax/z-score/robust) + kill the divergent `js/data.js:recalculateComparison()` shadow logic
- Zenodo DOI on first tagged release; `CITATION.cff`; per-model metadata enrichment (time-boxed)
- Document the FLOPs/efficiency column — it is the differentiator vs GUE/BEND-era tables

**Defer (v2+):**
- CODE_OF_CONDUCT / CONTRIBUTING (until external contributions arrive), full Datasheets per dataset, Docker env export, any server-based verification (violates static-site constraint)

**Anti-features (explicitly rejected):** automated evaluation server, maintainer re-run verification of submissions, Playwright/E2E suite, deep security hardening pass, full-history rewrite after successful revocation, any pipeline rewrite during hardening.

### Architecture Approach

Summary from [ARCHITECTURE.md](ARCHITECTURE.md) — codebase facts verified by direct inspection at `a44d310` (HIGH); the quality layer **wraps** the three existing subsystems without changing the runtime architecture. Tests and CI are read-only observers of committed data; the only writer of derived JSON is a maintainer running the chain through the Makefile, and freshness is *proven* by regenerate-into-scratch-and-diff, never assumed.

**Major components:**
1. **tests/ (root, pytest)** — four layers: unit tests over the 4 pure functions in `summarize_comparison.py`; golden-file tests on a synthetic 2-3-model fixture tree (never a copy of the real corpus); data-contract tests validating every committed JSON against schemas; a determinism test (chain x2, byte-identical)
2. **schemas/** — 4 JSON Schema files (model_performance, task_performance, models_comparison, tasks_index) making the pipeline→scripts→UI seam an executable contract; reusable by `js/submit.js`
3. **Makefile** — the single discoverable entry point (`make data|test|lint|verify-data|check`) encoding the scripts' CWD contract; CI invokes make targets so local ≡ CI
4. **CI workflow** — three small path-filtered jobs (lint / test / verify-data), `permissions: contents: read`, GPU-less by construction
5. **Determinism fixes in the 3 generators** — prerequisite, not enhancement: `sorted(os.listdir())`, `sort_keys=True`, `readdirSync().sort()` (~4 lines, verified needed at `summarize_comparison.py:309,381,408`, `get_task_performance.py:159`, `generate-tasks-index.js:18,56`)

**Key patterns:** two-tier fixtures (synthetic for logic, committed corpus as its own integration golden); golden-file testing via regenerate-and-diff with an explicit boring update path; schema-strict-on-structure/permissive-on-metadata; Make-not-just (zero extra tool for contributors); anti-patterns catalogued (no CI auto-commits of regenerated data, no version matrix in the byte-diff job, no refactoring the scripts' CWD coupling, no letting tooling mutate the frontend).

### Critical Pitfalls

Top 5 from [PITFALLS.md](PITFALLS.md) (7 critical total, all mapped to phases):

1. **Silent leaderboard-number migration (P1)** — the species fix will legitimately move numbers; treat the recomputation as a release: tag pre-fix data (`data-v1`), check in a before/after artifact per fix, stamp `meta.data_version`/`generated_at`, one number-affecting change per PR, declare non-comparability in README (lm-eval-harness changelog format verified).
2. **Over-refactoring breaks reproducibility and attribution (P2)** — grade audit findings into correctness / cheap-behavior-preserving / deferred; tag the as-published state; bitwise-identical output required for pure refactors; unexplained deltas after a fix are a red flag.
3. **Tests coupled to exact floats (P3)** — never `==` on computed floats; `pytest.approx` (rel 1e-6/abs 1e-12) / `assert_allclose` with explicit tolerances; pin `OMP/OPENBLAS/MKL_NUM_THREADS=1` in conftest (scikit-learn's own CI pattern); prefer integer/structural assertions (ranks, membership).
4. **Goldens that block legitimate updates (P4)** — exact goldens only on tiny pinned fixtures; schema/contract + summary-statistic assertions on production outputs; one-command golden regen whose diff is the review artifact; CI drift-detection converts "golden blocks updates" into "CI names the stale files".
5. **Token treated as removed when it lives in history (P6)** — revoke/rotate FIRST (GitHub's own doc); only then decide on hygiene; scan full history (gitleaks), enable push protection, note Zenodo tokens likely escape GitHub's default patterns.

Also load-bearing: **P5** (CI must be thin wrappers over locally-runnable make targets — no logic in YAML) and **P7** (dual declaration: code LICENSE + explicit data terms + 50-row provenance table; Data Provenance Initiative found 70%+ license omission and 50%+ error rates across dataset hosts — misattribution is the norm).

## Implications for Roadmap

The four research files converge on one ordering. ARCHITECTURE.md's dependency-ordered build order, FEATURES.md's dependency graph, and PITFALLS.md's phase mapping agree: foundations before contracts, contracts before fixes, fixes before recomputation, recomputation under CI protection, packaging last. Suggested 5-phase structure:

### Phase 1: Release-Blocking Foundations (security + reproducibility substrate)
**Rationale:** The token revocation is the only P1 item that cannot be a commit and must precede any public visibility; manifests unblock CI entirely; determinism fixes must precede every diff-based check or the gates will false-fail and get disabled; the LICENSE decision keys off everything downstream (README, provenance, DOI).
**Delivers:** Revoked Zenodo token + full-history secret-scan evidence + push protection; LICENSE + data-terms statement; `pyproject.toml` + `uv.lock` (pandas `>=2.2,<3.0`, numpy `>=2.0,<3`, groups `data`/`dev`/`pipeline`) exported from the known-good env; minimal `package.json` (`"type": "module"`, dev-only); determinism fixes in the 3 generators as their own commit with a one-time sorted recompute; pre-fix baseline tag + checksums of all committed JSON.
**Addresses:** Token revocation, LICENSE, dependency manifests (FEATURES table stakes).
**Avoids:** P6 (revocation-first), P2 (baseline capture + as-published tag), Anti-Pattern 1 (diff-without-determinism).

### Phase 2: Data Contracts + Test Harness
**Rationale:** Schemas must lock the data contract *before* correctness fixes change the numbers, so recomputed files are auto-validated and before/after comparisons have a shape anchor. The float-tolerance and thread-pinning discipline (P3) is decided the day the harness is scaffolded, not retrofitted. The species-grouping unit test is written here as a failing test first.
**Delivers:** `schemas/` (4 files) + contract tests over every committed JSON; unit tests for the 4 pure functions in `summarize_comparison.py`; golden-file tests on the synthetic fixture tree; determinism test; `tests/conftest.py` (thread pinning, `monkeypatch.chdir` fixture factory); `Makefile` (`data`, `test`, `lint`, `verify-data`, `check`).
**Uses:** pytest 9.1.1, jsonschema 4.26.0, node:test, ruff 0.16.10.
**Implements:** Architecture components 1-3 (tests, schemas, Makefile).
**Avoids:** P3 (tolerances + env pinning at scaffold time), P4 (layered goldens: exact only on tiny fixtures), Anti-Pattern 2 (no corpus duplication), Anti-Pattern 3 (chdir accommodation, not refactor).

### Phase 3: Correctness Fixes (surgical, one fix per PR)
**Rationale:** With contracts and tests in place, each fix lands as its own reviewable PR with test evidence and a diff containing only fix-explained deltas. The submit flow must wait for schema stability post-fix (FEATURES dependency), so it lands late in this phase.
**Delivers:** Navbar/render fix verified on ALL pages (not just the 3 known-broken); species-as-dataset grouping fix (pipeline-side constant + aggregation effect); `submit.html` restoration + orphaned `js/submit.js` wired to the current schema; sink-side escaping at DOM-build sites the phase touches; `js/data.js:recalculateComparison()` deleted or explicitly deprecated with a pointer to the authoritative script.
**Avoids:** P2 (one-fix-per-PR, diff discipline), UX pitfalls (dead pages, 404 nav links), the stored-XSS exposure the restored submission flow would otherwise create.

### Phase 4: CI + Recomputation + Number-Migration Record
**Rationale:** CI requires tests + manifests (both now exist); recomputation must happen last so the verify-data job *proves* the recomputation is complete and committed; the changelog only exists after recomputation (FEATURES dependency). Verify-data runs on the single pinned env — a version matrix and a byte-diff check are incompatible in one job (Anti-Pattern 4).
**Delivers:** `.github/workflows/ci.yml` (lint / test / verify-data, SHA-pinned actions, `permissions: contents: read`, concurrency cancel, path filters) as thin wrappers over `make`; README badge; recomputation via `make data` under CI protection; `CHANGELOG.md` with a before/after artifact per result-affecting fix (lm-eval-harness format); `meta.data_version`/`generated_at` stamp in derived JSON + leaderboard footer; pre-fix data tag `data-v1`.
**Avoids:** P1 (documented, attributable migration), P5 (thin workflow, local ≡ CI, secret-free so forks can run it), Anti-Pattern 5 (no CI auto-commits — fail with "run make data and commit"), Anti-Pattern 7 (three small jobs, not one mega job).

### Phase 5: Release Packaging + Provenance
**Rationale:** The DOI chain requires LICENSE + revocation + changelog (FEATURES dependency graph); the provenance table is drafted during fixes but lands with the docs; README reproducibility documents the Makefile commands that now verifiably exist.
**Delivers:** README reproducibility section (clone → install → `make check` → `make data`); `DATA.md` provenance table for all 50 datasets (source, citation, license-as-stated, redistributes-raw-vs-derived-only); BibTeX block + `CITATION.cff`; aggregation-methodology documentation; tagged release → GitHub release → Zenodo DOI; optional time-boxed model-metadata enrichment.
**Avoids:** P7 (dual license declaration, provenance table, no silent code-license-covers-data assumption), citation UX pitfalls.

### Phase Ordering Rationale

- **Dependency spine (all four files agree):** determinism → manifests → schemas/tests → fixes → CI → recompute → changelog → DOI. Each phase's outputs are the next phase's prerequisites; nothing later depends on undone earlier work.
- **Grouping follows the wrap architecture:** contracts/tests/Makefile are one harness (Phase 2); correctness fixes are independent review-unit PRs (Phase 3); CI + recompute is a single verification event (Phase 4) — recompute before CI exists would be unverifiable, and CI before tests exists would be an empty gate.
- **Pitfall timing is enforced by ordering:** P2's baseline is captured in Phase 1 before any fix; P3/P4 are decided at Phase 2 scaffold time; P1's changelog is only possible after Phase 4's recompute; P6's revocation precedes everything.
- **Anti-feature discipline holds in every phase:** no eval server, no Playwright, no deep security pass, no history rewrite after successful revocation, no pipeline changes, no build step introduced anywhere.

### Resolved Cross-Research Divergences (decisions for the roadmapper to inherit)

1. **html-validate (STACK, registry-verified) vs htmlhint (ARCHITECTURE, model-knowledge):** use **html-validate 11.16.2** — capability verified against official docs; ARCHITECTURE's own htmlhint reference is its one LOW-confidence item.
2. **SHA-pinned actions (STACK, GitHub security guidance) vs major-tag pins (ARCHITECTURE):** **SHA-pin** — a public-scrutiny release is exactly GitHub's stated case for immutable pins; SHAs are already fetched and tabulated in STACK.md.
3. **ESLint (STACK) vs node --check only (ARCHITECTURE's minimal lint job):** run **both** — `node --check` over all `*.js` is free syntax safety; ESLint flat config adds real value for the no-build MPA at negligible cost. Both are dev-only and touch no site files.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** No research-phase needed, but two *decisions* belong in discuss-phase: license choice (Apache-2.0 vs MIT — MEDIUM community-practice judgment) and confirmation of whether the repo redistributes raw dataset data or only derived aggregates (changes the P7 licensing exposure).
- **Phase 5:** Data licensing specifics (pairing code license with CC-BY-4.0 for data) is MEDIUM practice judgment; dataset-by-dataset license terms for the murkier genomics datasets may need spot verification during execution.

Phases with standard patterns (skip research-phase):
- **Phase 2:** pytest/jsonschema/golden-file patterns are fully specified in ARCHITECTURE.md with working code examples and verified line anchors.
- **Phase 3:** Fixes are repo-specific but anchored to verified code locations; no external research required.
- **Phase 4:** STACK.md provides the exact CI shape, action versions + SHAs, and matrix; lm-evaluation-harness provides the precedent workflow.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Every version verified against primary registries (PyPI/npm JSON APIs, GitHub Releases) on 2026-10-08; zero versions from training data |
| Features | MEDIUM | Repo survey live-verified via GitHub API; leaderboard-behavior claims (Open LLM Leaderboard, GLUE) from model knowledge, corroborated but not live-verified — none load-bearing for P1 items |
| Architecture | HIGH (codebase) / MEDIUM (ecosystem) | Codebase facts verified by direct inspection at `a44d310` with line numbers; ecosystem patterns cross-verified; node --check/`"type":"module"` specifics flagged LOW — confirm on first lint run |
| Pitfalls | MEDIUM overall | Core claims primary-verified (GitHub sensitive-data doc, pytest/numpy docs, lm-eval guide, scikit-learn CI, arXiv 2310.16787); community-consensus items individually tagged as strong hypotheses |

**Overall confidence:** HIGH for roadmap decisions — every release-blocking recommendation traces to primary-verified evidence; the MEDIUM/LOW residue affects v1.x polish items and two maintainer decisions, not phase structure.

### Gaps to Address

- **Known-good environment export (blocks Phase 1 pinning):** the exact numpy/pandas versions that produced the current leaderboard JSON live on the maintainer's machine (system Python here has no pandas). Export (`uv pip freeze`) and lock before any pin is treated as authoritative; floor pins are MEDIUM until then.
- **License + data-terms choice (blocks Phase 1 LICENSE):** Apache-2.0 recommended (DNABERT-2 precedent, patent grant); maintainer decision in discuss-phase.
- **Raw-data redistribution status (affects Phase 5 provenance scope):** verify whether the repo commits raw dataset files or only derived aggregates — derived-metrics-only is much weaker licensing exposure.
- **Zenodo token revocation mechanics:** the Zenodo help page could not be fetched this run; the revoke-PAT-under-account-settings mechanism is standard but should be confirmed when the maintainer performs it.
- **`node --check` + `"type": "module"` behavior:** ARCHITECTURE's LOW-confidence hypothesis; confirm in the first lint-job run (trivial, caught immediately).
- **Python 3.14 wheel availability for pinned pandas 2.3.x:** unverified; keep the CI matrix at 3.12/3.13 (local dev Python is 3.14.7 — do not let it leak into CI assumptions).

## Sources

### Primary (HIGH confidence)
- PyPI JSON API (pytest, ruff, uv, pre-commit, pytest-cov, pandas, numpy, jsonschema) and npm registry (eslint, html-validate, globals, ajv-cli) — versions + `requires_python`/`engines`, fetched 2026-10-08
- GitHub Releases/tag API — actions/checkout v7.0.1, setup-python v7.0.0, setup-node v7.1.0 with full-length SHAs; astral/setup-uv v10.2.0
- pandas 3.0.0 whatsnew (pandas.pydata.org) — breaking changes, Jan 2026 release, 2.3-first migration path
- Node.js official docs + release schedule — node:test stable since v20; Node 24 LTS, Node 26 LTS 2026-10-28
- docs.github.com — security hardening (SHA pinning), billing (public repos free on standard runners), "Removing sensitive data from a repository" (revoke-first, filter-repo, cached views, fork limits)
- docs.astral.sh/uv, pip.pypa.io, docs.pytest.org, eslint.org migration guide, html-validate.org — tool behavior
- pytest + NumPy official API references — `approx` and `assert_allclose` default tolerances
- EleutherAI/lm-evaluation-harness `docs/new_task_guide.md` — result-affecting-fix versioning + changelog format
- scikit-learn `.circleci/config.yml` — thread-pinning env vars in CI
- arXiv:2310.16787 (Data Provenance Initiative) — dataset license omission/error rates
- Direct codebase inspection at commit `a44d310` — all ARCHITECTURE.md codebase facts (script line numbers, data layout, `__main__` guards, CWD coupling)

### Secondary (MEDIUM confidence)
- GitHub API survey of stanford-crfm/helm, EleutherAI/lm-evaluation-harness, MAGICS-LAB/DNABERT_2, gluonfield/BEND, instadeepai/nucleotide-transformer, GenBench/genbench_cbt — file listings, licenses, CI shapes
- Academic release checklists (Imageomics, Zenodo FAIR, KU Leuven, UCSB, GEO-Inquire, NCCR Exit Strategy) — table-stakes criteria
- Ecosystem pattern sources for goldens/contracts/task-runners/determinism (MongoDB, Dart pub, check-jsonschema, reproducible-builds notes, pytest good practices) — cross-verified web sources
- HELM "Reproducing Leaderboards" docs — version-pinned leaderboard recreation

### Tertiary (LOW confidence — strong hypotheses, not load-bearing for P1)
- Open LLM Leaderboard v1→v2 non-comparability declarations; GLUE/SuperGLUE evaluation-server model; Datasheets/Model Cards specifics
- Golden-update tool conventions (pytest-regressions/Syrupy/ApprovalTests); `act` local-runner limitations; actionlint practice
- Vendor-reported credential-harvesting timing (GitGuardian); Zenodo push-protection pattern coverage

---
*Research completed: 2026-10-08*
*Ready for roadmap: yes*
