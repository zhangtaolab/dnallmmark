# Pitfalls Research

**Domain:** Auditing and hardening a research benchmark repository (DNA LLM benchmark: pipeline + data scripts + static leaderboard) for public release
**Researched:** 2026-10-08
**Confidence:** MEDIUM overall — core claims verified against primary sources (GitHub docs, pytest/numpy official docs, lm-evaluation-harness official guides, arXiv abstract, scikit-learn CI config); community-consensus claims that could not be primary-verified this run are individually tagged and must be treated as strong hypotheses, not authoritative fact.

> **How to read this file.** Each pitfall is specific to the "hardening-and-release of a research benchmark repo" domain and anchored to DNALLM-Mark's known findings (leaked Zenodo token in `README.md:116`, dead pages from `renderNavbar()`, species-grouping bug at `dnallmmark_pipeline.py:1229`, unescaped `innerHTML`, no tests/CI/LICENSE, manual 3-step data chain). "Phase to address" uses the milestone's logical phases: **Audit → Correctness Fixes → Recomputation → Tests+CI → Release Hygiene**. Renumber when the roadmap lands.

---

## Critical Pitfalls

### Pitfall 1: Silent leaderboard-number migration (numbers change with no documented trail)

**What goes wrong:**
The species-as-dataset fix (`dnallmmark_pipeline.py:1229`) will legitimately move aggregated leaderboard numbers. The failure mode is not the change itself — it is regenerating `dnallm-mark/data/*.json` and committing them with a message like "update data" so that every external user who already cited or screenshotted a number finds it silently different. Anyone diffing the release sees thousands of changed float fields and zero explanation of which fix caused which movement. Trust in the whole platform drops: if numbers change silently once, users assume they can change silently again.

**Why it happens:**
Derived-data regeneration feels like a mechanical build step, so it gets a mechanical commit. Authors know *why* numbers moved and forget that consumers don't. Benchmarks also compound this: one pipeline fix + one aggregation tweak + a dependency upgrade can land together, making the before/after delta unattributable even to the authors.

**How to avoid:**
- Treat number changes as releases, not chores. Before regenerating, tag the pre-fix data state (`git tag data-v1`) so the old numbers stay retrievable.
- Produce an explicit before/after artifact per result-affecting fix: which datasets/models/ranks moved, by how much, and why (the fix's PR description). The milestone already mandates "before/after comparison notes" — make that a checked-in file (e.g. `docs/data-changelog.md` or `CHANGELOG.md` entry), not a chat message.
- Follow the lm-evaluation-harness pattern (verified from their official `docs/new_task_guide.md`): bump a version marker on the data/protocol when a change alters results, and record a dated changelog entry with PR number — their example format is literally "*[date] (PR #999) Version 0.0 → 1.0: Fixed a bug with answer extraction that led to underestimated performance*". DNALLM-Mark's equivalent: stamp the regenerated JSON (top-level `meta.data_version` / `generated_at` / `pipeline_commit`) so any leaderboard page can display "results as of vX".
- One number-affecting change per commit/PR where feasible, so each delta in the comparison file maps to one named fix.
- State the non-comparability explicitly in the README (industry precedent: the HF Open LLM Leaderboard v1→v2 reboot publicly declared old and new results non-comparable — LOW confidence, synthesis; the practice itself is standard).

**Warning signs:**
- A regenerated data commit touching more than a handful of JSON files with no accompanying note.
- No way to answer "which numbers were different before the species fix?" without archaeology (`git show data-v1:...`).
- Leaderboard pages displaying numbers with no version/date stamp.
- Before/after comparisons living only in PR review conversation.

**Phase to address:** Recomputation phase (structure + changelog), seeded during Correctness Fixes (one-fix-per-PR discipline), surfaced in Release Hygiene (README statement + data version display).

---

### Pitfall 2: Over-refactoring during hardening breaks reproducibility and muddies attribution

**What goes wrong:**
An audit finds dozens of code smells (and this repo has them: duplicated aggregation logic, a 1200+ line pipeline script, dead JS modules). The tempting move is to fix them all in the same pass as the correctness bugs. Result: the public release's diff versus the code that produced the published numbers is enormous, and when recomputed numbers shift, nobody can say whether the shift came from the species-grouping fix, the refactor, or float reordering introduced by restructured loops. Worse, "safe" cleanups delete hard-coded constants or reorder operations that were load-bearing, changing outputs for reasons no one intended.

**Why it happens:**
Auditors are in bug-hunting mindset; every smell looks fixable. Refactoring feels like it improves reviewability, so it seems *helpful* for public release. The discipline failure is treating hygiene changes and behavior-affecting changes as the same class of change.

**How to avoid:**
- Enforce the milestone's own constraint: surgical fixes only, no opportunistic refactors. The audit report should grade findings into "correctness (fix now)", "maintainability (fix if cheap and behavior-preserving)", and "deferred (list, don't touch)".
- Capture golden outputs from the *current, unfixed* code before changing anything (checksums of the existing committed JSON are already available — record them). Then after each fix, regenerate and diff; an unexpected delta that isn't explained by the fix is a red flag.
- Explicit equivalence policy for anything that must be restructured: bitwise-identical output required (no tolerance) for pure refactors; documented, explained deltas allowed only for the named correctness fixes.
- Tag/branch the as-published state before the fix series starts, so "what produced the old leaderboard" is always answerable.
- Community-consensus checklist for research-code release (LOW confidence, synthesis — consistent across Software Sustainability Institute / Turing Way guidance): archive as-run state first; first public pass is hygiene-only (README, LICENSE, CITATION, pinned env, relative paths); refactor later under tests.

**Warning signs:**
- PRs mixing whitespace/renaming/structural changes with behavior fixes.
- A finding labeled "correctness" whose fix also renames functions, moves files, or rewrites loops.
- No tagged pre-fix commit when the fix series begins.
- Recomputed diff shows movements in datasets/models unrelated to the known bug.

**Phase to address:** Audit phase (capture baseline + tag pre-fix state) and Correctness Fixes phase (diff discipline enforced in review).

---

### Pitfall 3: Tests coupled to exact floating-point outputs

**What goes wrong:**
The new data-script test suite (first tests this repo will have) asserts `result == expected` on floats produced by the aggregation scripts (`summarize_comparison.py` does rank/MinMax/z-score/robust aggregation over pandas frames). The tests pass on the author's machine, then fail on GitHub Actions' Ubuntu runner, on macOS, or after a numpy/pandas version bump — not because the code is wrong but because non-associative IEEE 754 summation reorders under different BLAS backends (OpenBLAS vs MKL vs Accelerate), different thread counts, and FMA contraction. The team concludes the tests are "flaky by nature" and starts ignoring or deleting them before the release is out.

**Why it happens:**
Exact assertions are the path of least resistance when writing the first tests against known JSON outputs. Cross-platform float divergence is invisible until CI runs somewhere else, and each failure costs 5+ minutes of round-trip, which trains people to `--update` or skip rather than investigate.

**How to avoid:**
- Never assert `==` on computed floats. Verified defaults for the two standard tools:
  - `pytest.approx`: relative tolerance 1e-6, absolute 1e-12, `nan_ok=False` — note the absolute floor exists precisely because *nothing but 0.0 is relatively close to 0.0*; pass an explicit `abs=` whenever expected values can be near zero.
  - `numpy.testing.assert_allclose`: `rtol=1e-07, atol=0, equal_nan=True` — its zero default `atol` bites for near-zero comparisons; set both explicitly.
- Pin thread counts for determinism *before* numpy/pandas import (conftest or CI env): `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`. Primary-source example: scikit-learn's own CI pins exactly these three env vars (verified in their `.circleci/config.yml`).
- Prefer integer/structural assertions where the domain allows: ranks are integers, row counts are integers, membership ("model X in top-5 for dataset Y") is boolean. Reserve float tolerances for scores.
- Round-trip/property tests are immune to float drift: aggregation of a known tiny fixture should satisfy invariants (monotonicity under scaling for MinMax, z-score mean≈0/std≈1) regardless of last-ULP noise.
- Pin the pandas/numpy versions in the manifest so local and CI environments don't silently diverge.

**Warning signs:**
- Any `assert x == 0.5`-style line in tests for computed values.
- Test failures that differ between local machine and CI, or between CI runs, with tiny (1e-12-ish) diffs.
- Tests passing only after setting thread env vars by hand, not in config.

**Phase to address:** Tests+CI phase — this is decided the day the test harness is scaffolded (conftest + tolerances + env pinning), not retrofitted.

---

### Pitfall 4: Golden-file tests that block legitimate data updates (or train the team to blindly regenerate)

**What goes wrong:**
The suite golden-copies the full aggregated performance JSON (50 datasets × 41 models). Every legitimate data refresh then fails CI. Two bad equilibria follow: (a) the team runs the regenerate flag with no review, at which point the golden no longer tests anything — it just snapshots whatever the code currently produces, bugs included; or (b) data updates get deferred indefinitely because "updating the goldens is a pain", and the repo ships with stale derived files (already a live risk here: the data chain is manual and stale derived files are undetectable today).

**Why it happens:**
Full-output goldens are the easiest test to write and they do catch the species-grouping class of bug — once. But they conflate "output changed" with "output changed *unexpectedly*", and only the second is a bug. Without a designed update flow, the test suite becomes an obstacle to the one thing a benchmark repo must do routinely: refresh results.

**How to avoid:**
- Layer the goldens:
  - **Exact goldens only on tiny, pinned fixtures** (3 models × 2 datasets, checked in as test fixtures, never the production data).
  - **Contract/schema assertions on production outputs** (required keys present, types correct, model/dataset IDs match the catalogs, ranks are valid permutations, scores in expected ranges) — these pass across legitimate refreshes and fail on structural breakage.
  - **Summary-statistic checks** (counts per dataset, no NaN where forbidden) instead of full-file equality.
- One-command regeneration with review friction in the right place: `make update-goldens` (or pytest flag) regenerates; the update lands as its own commit/PR whose diff *is* the review artifact, paired with the data-changelog entry from Pitfall 1. Never hand-edit goldens (community consensus, LOW confidence synthesis — matches pytest-regressions/Syrupy/ApprovalTests documented workflows).
- Add a CI **drift-detection** job: regenerate derived files from upstream inputs and `git diff --exit-code`. This converts "golden blocks updates" into "CI tells you exactly which derived files are stale", which is the actual property this repo needs.
- Scrub/mask volatile fields (timestamps) or exclude them from comparison so only meaningful content is compared.

**Warning signs:**
- Golden update commits containing thousands of changed lines with no explanation.
- Team members deleting or `xfail`ing golden tests "to unblock a data refresh".
- Derived JSON regenerated by hand-editing instead of the chain.
- No command exists to regenerate goldens; people copy-paste expected values into test files.

**Phase to address:** Tests+CI phase (layered structure, regen command, drift job), interacting with Recomputation phase (goldens updated in a reviewed, changelogged commit).

---

### Pitfall 5: CI that cannot be run (or debugged) locally

**What goes wrong:**
The first GitHub Actions workflow embeds real logic — multi-line `run:` blocks installing numpy/pandas, invoking the data chain, diffing JSON — directly in the YAML. It works, but nobody can reproduce a failure without pushing commits. Academic contributors (this repo's audience) won't iterate via push-wait-5-minutes-watch-logs cycles; they open an issue instead, or abandon the PR. Additionally, if the workflow grows dependencies on the GPU pipeline or the external `dnallm` package, CI becomes permanently red or permanently skipped — both equivalent to no CI.

**Why it happens:**
Workflows are written in the GitHub UI or by pasting from docs, where embedding shell logic is the shortest path. There is no first-class local execution of GitHub Actions (community tool `act` approximates runners in Docker with known gaps; GitHub's own `gh act` local runner was preview-stage — LOW confidence synthesis). The constraint that CI must not require GPU or `dnallm` (already a project constraint) also has to be actively designed for, since the data scripts import from the pipeline tree in subtle ways sometimes.

**How to avoid:**
- Thin workflow, fat scripts: the YAML does `run: make test` (or `./scripts/ci.sh`). The identical command is documented in the README/CONTRIBUTING and run by developers locally. If it can't run locally in under a minute on a laptop, it shouldn't be in CI.
- Statically lint the workflow with `actionlint` (+ `yamllint`/`shellcheck` for embedded shell) before pushing — catches most schema/expression errors that would otherwise cost a push-and-wait cycle (community practice, LOW confidence synthesis).
- Keep the CI dependency set to stdlib+numpy+pandas with pinned versions and a lockfile/requirements the CI installs; any import of `dnallm` or torch in a tested module fails fast at import time — structure the data scripts so their imports don't transitively pull the GPU stack.
- Free/included tooling first: pytest, `node --check` for ES modules, a JSON parse + schema check, actionlint. No paid runners, no secrets needed — a workflow requiring secrets cannot run on forks.
- Validate the CI on a clean fork or with `act` before trusting it.

**Warning signs:**
- Workflow files longer than ~50 lines or containing loops/conditionals in `run:` blocks.
- Tests that import the fine-tuning pipeline (and would drag in torch/dnallm).
- No local command in the docs that corresponds to what CI runs.
- Commits named "try fix ci", "ci?", "wip ci" — the signature of push-driven debugging.

**Phase to address:** Tests+CI phase (structure decided at workflow creation).

---

### Pitfall 6: Treating a leaked token as "removed" when it lives in git history (revocation-first)

**What goes wrong:**
The Zenodo token is deleted from `README.md:116`, the commit is pushed, and the repo is declared clean for public release. The token remains fully retrievable from every prior commit (`git log -p`, any file view by SHA), in forks and clones, and in GitHub's cached views. If it was ever pushed to a remote — and it is at HEAD, so it was — it must be assumed harvested: automated scanners index credentials pushed to public remotes within minutes (vendor-reported figure; LOW confidence). Deleting from HEAD is cosmetic.

**Why it happens:**
Mental model of git as "the current files" rather than an append-only history. Revocation also feels optional when the repo is currently private — but making a repo public publishes its entire history, so "we'll deal with it at release" is exactly the wrong order.

**How to avoid:**
All points below verified against GitHub's official "Removing sensitive data from a repository" doc unless noted:
1. **Revoke/rotate FIRST.** GitHub's doc is explicit that for credentials you "need to revoke and/or rotate that secret" — rotation alone may make a history rewrite unnecessary. For Zenodo: revoke the personal access token in Zenodo account settings (mechanism is standard; exact help URL could not be primary-verified this run), and check Zenodo usage logs for the exposure window.
2. Only then decide on history hygiene. GitHub officially recommends `git filter-repo` (v2.47+ even has a `--sensitive-data-removal` flag); `filter-branch` is deprecated; BFG is a simpler alternative for text replacement.
3. Know the limits of rewriting: GitHub keeps cached views reachable by commit SHA; contact GitHub Support to clear cached views and run server-side GC. You cannot clean other users' clones or forks.
4. Coordinate the force-push: collaborators must re-clone or rebase — one merge commit from an old clone reintroduces the tainted history. Check that no open PRs/reviews reference the old commits.
5. Prevent recurrence: enable GitHub push protection / secret scanning, and add a pre-commit gitleaks hook for arbitrary token formats GitHub doesn't know (Zenodo tokens are not in GitHub's default pattern set — inference from it being a non-first-party provider; verify configuration).
6. Scan the *full history* (gitleaks/trufflehog over all commits), not just HEAD — the README copy may not be the only copy (docs, scripts, notebooks).

**Warning signs:**
- A "removed token" commit with no corresponding revocation recorded anywhere.
- No full-history scan evidence before the release tag.
- Release checklist says "delete token from README" instead of "revoke token".

**Phase to address:** Release Hygiene phase — but make revocation a **manual, out-of-repo checklist item** (the milestone already flags it); the repo-side work (history scan, optional rewrite, push protection) is code/CI and belongs in the same phase. Note: this is the one pitfall where the fix cannot be expressed as a commit.

---

### Pitfall 7: License/provenance gap for benchmark data (code license silently applied to data)

**What goes wrong:**
A single LICENSE file (MIT/Apache) is added at release, and everything in the repo is implicitly covered by it. But the repo redistributes derived artifacts of 50 datasets, each with its own upstream source, license, and citation expectations. The Data Provenance Initiative's audit (verified from the arXiv abstract of 2310.16787) found license omission of 70%+ and license error rates of 50%+ across popular dataset hosting sites — misattribution is the norm, not the exception, and a benchmark platform amplifies it by re-publishing aggregates of many datasets under one roof. Downstream users assume "MIT repo → data is MIT", which can be wrong for non-commercial or share-alike upstream sources.

**Why it happens:**
"Add a LICENSE" is on every release checklist; "add a DATA_LICENSE and per-dataset provenance" is on none. Benchmark authors usually fetched the datasets programmatically and never recorded terms. The datasets catalog page (`datasets.js`) exists for science, not licensing, so nobody thinks of it as the provenance record.

**How to avoid:**
- Dual declaration: LICENSE (code) + explicit data-terms statement (separate DATA_LICENSE or a README section): "aggregated performance metrics are ours; underlying datasets belong to their original publishers; see the provenance table".
- Provenance table for all 50 datasets: name, original source (paper/URL), license as stated upstream (or "unknown"), and whether DNALLM-Mark redistributes raw data or only derived aggregates (derived metrics are a much weaker exposure than raw redistribution — verify which one this repo commits).
- If any upstream dataset is non-commercial or ambiguous, say so in the table rather than resolving it silently.
- Add CITATION.cff + a BibTeX block so the platform itself gets cited correctly (academic UX, cheap, expected).
- Do this before public flipping: relicensing/retrofitting provenance after users have already consumed the data is far messier.

**Warning signs:**
- Release checklist contains only "choose LICENSE".
- Datasets catalog displays names/sources but no license column anywhere in the repo.
- Raw dataset files (FASTA etc.) committed without any terms note.
- No citation file and no license header on the leaderboard site.

**Phase to address:** Release Hygiene phase (license decision is already an active requirement; the provenance table can be drafted earlier during the audit, when each dataset is being touched anyway).

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Ship release with no dependency manifest (`requirements.txt`/`pyproject.toml`) | No version-research work today | CI can't install; reviewers can't run; recomputation environment unreproducible (feeds Pitfalls 3, 8) | Never for a public benchmark repo |
| Hand-edit a derived JSON to fix "one number" | 2-minute fix | Regeneration chain overwrites it; number's provenance becomes unexplainable | Never — fix upstream or accept the number |
| Keep dead-but-plausible duplicate logic (`js/data.js:recalculateComparison` vs `script/summarize_comparison.py`) | Zero deletion risk during hardening | Two sources of truth; someone "fixes" the JS copy and the site silently disagrees with the scripts | Acceptable to *defer* deletion if reported in the findings doc; not acceptable to leave unreported |
| Full-output golden tests (against Pitfall 4) | Fastest first test to write | Every legit refresh fails CI; suite degraded to auto-snapshot | Only on tiny pinned fixtures |
| README prose hardcoding leaderboard numbers ("Model X achieves Y") | Nice for the paper | Diverges from data on every recomputation; someone must remember to update it | Avoid; link to the leaderboard page instead |
| Test logic embedded in workflow YAML (against Pitfall 5) | One less file | Cannot run/debug locally; push-driven CI debugging | Thin wrappers only |
| Defer LICENSE/CITATION to "after the code is clean" | Sequencing feels tidy | Everything (data table, README, site footer) keys off the license; retrofitting provenance post-release is painful | Decide early even if the final text lands late |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Zenodo (token leak, `README.md:116`) | Treat README deletion as cleanup; assume a private repo's history is safe forever | Revoke first, scan full history, rewrite only if desired, coordinate force-push (Pitfall 6) |
| Zenodo (future data deposits) | Pasting working token snippets into docs as "instructions" | Use `<your-token>` placeholders in all docs; real tokens only via env var, never in examples that get copy-pasted into commits |
| GitHub Actions | Over-broad `GITHUB_TOKEN` permissions; actions referenced by mutable tags; workflow that needs secrets (breaks on forks) | Read-only default permissions (`permissions: contents: read`), pin actions by SHA, keep the test workflow secret-free so external contributors' PRs run it |
| GitHub Pages (static hosting constraint) | Assuming "static site, nothing can break" — the `renderNavbar()` class of bug shipped because nothing loads pages | Cheap structural checks in CI: every nav link resolves to an existing file, every `js/*.js` passes `node --check`, every data JSON parses (full E2E is out of scope by decision — these checks are not) |
| Git history rewrite | Rewriting while PRs are open; merging (not rebasing) from pre-rewrite clones; forgetting forks keep old history | Close/merge PRs first; announce re-clone requirement; accept forks as unfixable (GitHub docs, verified) |

## Performance Traps

Patterns that work at small scale but fail as usage grows. Scale here = datasets × models × history, not users.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Golden-diffing full production JSON (Pitfall 4) | CI diffs of 10k+ lines; humans stop reading them | Layered assertions; summary stats; drift job | Immediately at 50×41; worsens with every model added |
| Committing regenerated bulk JSON on every refresh | Repo bloat, noisy history, huge PR diffs | Keep derived data small and normalized; consider data release tags for big refreshes | After several recomputation cycles |
| Test suite running the real 50-dataset pipeline | CI minutes balloon; contributors skip the suite | Tests run on tiny fixtures; full-data checks limited to the drift job | First time the data doubles |
| Browser pages loading the full performance JSON eagerly (existing two-tier cache exists, but new pages tend to skip it) | Leaderboard feels fine to authors with cache, slow to first-time visitors | Reuse the existing caching pattern for any page the fixes touch | New visitor, doubled data size |

## Security Mistakes

Domain-specific issues beyond general web security. (Deep security is out of scope this milestone by decision; these are the ones that interact with the audit's own findings.)

| Mistake | Risk | Prevention |
|---------|------|------------|
| Treating the `innerHTML` finding as cosmetic because "the data JSON is trusted, we generate it" | The submission flow (`js/submit.js` + PR instructions) invites external input; one accepted community submission with a hostile model/dataset string turns stored XSS live | Escape at the sinks (DOM building / `textContent`) during the correctness pass; treat submission-generated JSON as untrusted forever after |
| Revocation-free "cleanup" of the leaked token (Pitfall 6) | Live credential in public history post-release | Revocation-first runbook; full-history gitleaks scan in CI |
| Assuming push protection covers Zenodo tokens | GitHub's pattern set targets first-party providers; a Zenodo token likely slips through | Pre-commit gitleaks with a custom rule for the token format; verify empirically |
| Client-side-only submission validation presented as a security control | Bypassed trivially; hostile data enters the PR pipeline | Document validation as UX-only; the real gate is human PR review + sink-side escaping |

## UX Pitfalls

Users here are researchers who consume the leaderboard and cite the platform.

| Pitfall | User Impact | Better Approach |
|---------|-------------|------------------|
| Numbers change without a data changelog (Pitfall 1) | Cited numbers stop matching the site; platform presumed unreliable | Data version stamp + changelog + archived old snapshot |
| No date/version on displayed results | "As of when?" is unanswerable; screenshots circulate without context | Render `meta.generated_at` / `data_version` in the page footer |
| Nav links to missing pages (`submit.html` orphan) | Users hit 404s and conclude the project is abandoned | Link-resolution check in CI; fix or remove the link in the correctness pass |
| No citation guidance | The platform gets mis-cited or not cited | CITATION.cff + BibTeX block + one-line "how to cite" on the leaderboard |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces. Run this before the release tag.

- [ ] **Token revoked:** Zenodo token *revoked at the provider* (not just absent from README); gitleaks/trufflehog scan over **full history** is clean; push protection enabled.
- [ ] **History actually clean:** (if rewrite chosen) commits by old SHA no longer fetch; GitHub Support contacted about cached views; collaborators re-cloned.
- [ ] **Numbers reproducible:** fresh clone → run the documented data chain → output matches committed JSON (drift job green).
- [ ] **Number migration documented:** data changelog entry per result-affecting fix, before/after artifact checked in, pre-fix data tagged.
- [ ] **Every page renders:** each HTML page loads in a browser without console errors; navbar renders on all pages (`renderNavbar()` fix verified on *all* pages, not just the three known-broken ones).
- [ ] **Every link resolves:** no nav/anchor references missing files (`submit.html` fixed or link removed).
- [ ] **CI is green from a clean fork:** no secrets, no GPU, no `dnallm` import; workflow runnable by an outside contributor.
- [ ] **Local ≡ CI:** the documented local command runs the same suite CI runs, in comparable time.
- [ ] **Licensing complete:** code license chosen; data terms stated; per-dataset provenance table exists; CITATION.cff present.
- [ ] **Dependency manifest:** `pip install -r requirements.txt` (or equivalent) on a clean venv suffices to run tests and data scripts.
- [ ] **No shadow logic:** duplicate divergent aggregation in `js/data.js` deleted or explicitly marked deprecated with a pointer to the authoritative script.

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Token found live after release (P6) | LOW (technical) / varies (impact) | Revoke immediately; pull Zenodo usage logs for the exposure window; then optional history rewrite + Support contact; disclose if misuse found |
| Numbers changed silently post-release (P1) | MEDIUM | Publish a retroactive migration note; tag the pre-change data; reconstruct before/after from git history; add the version stamp going forward |
| Golden suite all-red after a legitimate update (P4) | LOW | Regenerate via the official command; review the diff in a dedicated PR with a changelog entry; never delete tests or hand-edit goldens to get green |
| Over-refactor already merged (P2) | HIGH | Revert to the tagged pre-fix baseline; re-apply fixes as surgical diffs; recompute and document deltas per fix |
| CI chronically red / ignored (P5) | MEDIUM | Split a fast local-runnable core suite from full CI; fix determinism (thread pinning, tolerances); delete jobs nobody fixes |
| Mislicensed data discovered post-release (P7) | MEDIUM-HIGH | Add provenance table immediately; restrict or annotate the affected datasets; update README and any redistributed archives; consult the data owner if uncertain |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls. Phase names are the milestone's logical stages — renumber to the roadmap's actual phases.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| P1 Silent number migration | Recomputation (changelog + version stamp), seeded in Correctness Fixes (one-fix-per-PR) | Data changelog exists; pre-fix data tag exists; before/after artifact reviewed |
| P2 Over-refactor breaks reproducibility | Audit (baseline capture + pre-fix tag + severity-grading rules), Correctness Fixes (diff discipline) | Post-fix diff contains only fix-explained deltas; no unexplained movements |
| P3 Exact-float test coupling | Tests+CI | Zero `==` asserts on computed floats; conftest pins thread env vars; CI green on Ubuntu + one other OS ideally |
| P4 Goldens block legit updates | Tests+CI | Layered suite (fixture goldens + schema contracts + summary stats); regen command documented; drift job green on fresh clone |
| P5 CI not locally runnable | Tests+CI | Workflow ≤ thin wrapper; README documents the identical local command; contributor-fork run passes |
| P6 Token-in-history / revocation-first | Release Hygiene (revocation is a manual checklist item) | Token shown revoked at Zenodo; full-history secret scan clean; push protection on |
| P7 Data license/provenance gap | Release Hygiene (table drafted during Audit) | LICENSE + data terms + 50-row provenance table + CITATION.cff present |
| Moderate: recomputation environment drift | Recomputation | Recompute in an environment pinned by the new manifest; manifest committed before recomputation |
| Moderate: shadow aggregation logic divergence | Correctness Fixes (report) → Tests+CI (delete or deprecate) | Single authoritative implementation or explicit deprecation pointer |
| Moderate: sink-side escaping vs blanket escape | Correctness Fixes | Pages render real data without artifacts (no double-escaping); escaping verified at DOM-build sites |

## Sources

Confidence per the classify-confidence seam: all web providers rate LOW mechanically; items below marked **verified** were fetched directly from the named primary source this run and are the strongest available evidence.

**Verified primary sources (best evidence):**
- GitHub official docs, "Removing sensitive data from a repository" (docs.github.com) — revoke-first ordering, filter-repo recommendation incl. `--sensitive-data-removal` (2.47+), cached views by SHA, Support contact for GC, fork/clone recontamination, rebase-not-merge. [P6, P5-adjacent]
- pytest official API reference — `approx` defaults rel=1e-6 / abs=1e-12 / nan_ok=False, near-zero rationale. [P3]
- NumPy official docs — `assert_allclose` defaults rtol=1e-07 / atol=0 / equal_nan=True. [P3]
- EleutherAI/lm-evaluation-harness `docs/new_task_guide.md` (via GitHub API) — task versioning policy + changelog entry format for result-affecting fixes; release notes v0.4.x pattern of grouped "Task Fixes". [P1]
- scikit-learn `.circleci/config.yml` (via GitHub API) — pins MKL/OPENBLAS/OMP_NUM_THREADS=1 in CI. [P3]
- arXiv:2310.16787 abstract, "The Data Provenance Initiative" — 70%+ license omission, 50%+ error rates across audited dataset collections. [P7]

**Community-consensus claims (LOW confidence per seam; consistent across multiple independent syntheses but not primary-verified this run — treat as strong hypotheses):**
- HF Open LLM Leaderboard v1→v2 declared results non-comparable; SWE-bench Verified re-annotation changed rankings; EvalPlus/HumanEval+ score drops. [P1]
- Golden-file update workflow (regenerate-review-diff; pytest-regressions / Syrupy / ApprovalTests conventions). [P4]
- `act`/`gh act` local-execution limitations; actionlint pre-push linting practice. [P5]
- Research-code release discipline (archive as-run state; hygiene-only first pass; characterization tests before refactor) — Software Sustainability Institute / Turing Way consensus. [P2]
- Bots harvesting pushed credentials "within minutes" (GitGuardian vendor reporting); TruffleHog live-credential verification; gitleaks pre-commit mode. [P6]

**Environment caveat:** the WebSearch tool in this run returned model-knowledge syntheses without live citations; every load-bearing claim above was therefore re-verified by direct fetch (WebFetch / GitHub API) where a canonical URL existed. Claims that could not be re-verified are the LOW-confidence group. The Zenodo token-revocation help page could not be fetched (404 at attempted URLs); the mechanism (revoke personal access tokens under account settings) is standard and consistent with GitHub's revoke-first guidance.

---
*Pitfalls research for: audit-and-release hardening of research benchmark repositories*
*Researched: 2026-10-08*
