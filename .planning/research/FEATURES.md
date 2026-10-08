# Feature Research

**Domain:** Public release of an ML/DNA-LLM benchmark platform (leaderboard + fine-tuning pipeline + offline data scripts) — release-hardening milestone
**Researched:** 2026-10-08
**Confidence:** MEDIUM (repo-structure claims live-verified via GitHub API on 2026-10-08; leaderboard-behavior claims for Open LLM Leaderboard / GLUE from model knowledge, consistently corroborated but not live-verified — JS-rendered pages)

**"Users" here** are external reviewers, paper readers, researchers comparing DNA LLMs, and potential result submitters. The bar being researched: what a well-run public benchmark repo ships, so the release does not look unserious next to HELM, lm-evaluation-harness, DNABERT-2/GUE, BEND, Nucleotide Transformer, and GenBench.

## Feature Landscape

### Table Stakes (Users Expect These)

Present in essentially every surveyed benchmark repo or demanded by every academic release checklist (Imageomics, Zenodo FAIR, KU Leuven, UCSB, GEO-Inquire, NCCR). Missing any of these is what makes a release look unserious.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| LICENSE file with explicit code license | All 6 surveyed repos have one (HELM Apache-2.0, lm-eval MIT, DNABERT-2 Apache-2.0, BEND BSD-3, NT and GenBench custom); "without a license your software cannot be legally reused" (KU Leuven). DNALLM-Mark has none today | LOW | MIT or Apache-2.0 for code; if derived-data files are licensed separately, note data licensing in README. DNABERT-2 (Apache-2.0) is the closest DNA-LLM precedent |
| Dependency manifests (`requirements.txt`/`pyproject.toml` for `script/`, `package.json` for the Node step) | Every surveyed Python repo ships one; CI cannot exist without it; reviewers check reproducibility here first | LOW | Pin versions (NCCR/Zenodo checklists). `pipeline/` may need a separate note that it requires GPU + external `dnallm` — do NOT put that burden into the CI-tested manifest |
| README reproducibility section: end-to-end commands | Every checklist demands scripted, copy-pasteable reproduction (setup, data download/refresh, aggregate, serve); DNABERT-2 and BEND both document run commands | LOW–MEDIUM | The 3-step data chain is currently README-prose only; make each step a literal command from repo root |
| Documented + detectable data-regeneration chain | Checklists: "data preprocessing scripted, not manual"; HELM makes leaderboard regeneration a named procedure (`helm-run` → `helm-summarize` → `helm-server`); GenBench CBT ships a Makefile for this | LOW–MEDIUM | A `make data` (or `npm run data`) target wrapping get_task_performance.py → summarize_comparison.py → generate-tasks-index.js, plus a freshness check (see Differentiators: staleness detection) |
| Data provenance for the 50 datasets (source, citation, license per dataset) | Datasheets-for-Datasets norm; DNABERT-2 documents GUE composition; HF dataset cards are the de-facto standard; Data Provenance Initiative shows license misattribution is the #1 provenance failure | MEDIUM | The repo already has a datasets catalog page — add provenance fields there or in a `DATA.md`. A provenance table (source/citation/license/preprocessing) is enough; full datasheets per dataset are not required this milestone |
| Citation file (BibTeX in README at minimum) | DNABERT-2, HELM (`CITATION.bib`), lm-eval-harness (`CITATION.bib`) all ship one; GenBench CBT adds `AUTHORS` | LOW | Needed for paper-adjacent scrutiny — reviewers must be able to cite the benchmark |
| Secret hygiene: revoked leaked Zenodo token before public push | Universal; a live token in a public repo is an automatic incident and makes the "audit" retroactively embarrassing | LOW (manual) | Revocation is the fix. Note: if revocation were impossible, history scrub before first public push would matter; after successful revocation, history rewrite adds fork/SHA-breakage risk for near-zero gain |
| Unit tests for data-processing scripts | Present in HELM (`conftest.py`), lm-eval-harness (`tests/`), GenBench CBT (`tests/`); absent in DNABERT-2/BEND/NT — i.e., tests separate well-run repos from typical academic ones. For a repo whose Core Value is "every number is correct and reproducible", tests are table stakes, not gold-plating | MEDIUM | Already an explicit milestone requirement. Test the aggregation logic (rank/MinMax/z-score/robust) with small synthetic fixtures — no GPU, no `dnallm` |
| CI (GitHub Actions) running the tests, with badge in README | lm-eval-harness `unit_tests.yml`, HELM `test-python.yml`, GenBench CBT workflows, even DNABERT-2 has `check_build.yml`; badge is the first-run trust signal | LOW (once tests exist) | CPU-only, stdlib/numpy/pandas scope per project constraint. Keep it modest — flagship repos run exactly this shape (unit tests + build/publish), not elaborate matrices |
| Changelog / before-after documentation when leaderboard numbers change | HELM maintains `CHANGELOG.md`; Open LLM Leaderboard froze v1 with explicit "scores not comparable" statements when methodology changed. A benchmark whose aggregates shifted (species-grouping fix) without a written record invites "numbers moved silently" accusations | LOW–MEDIUM | Milestone already requires before/after comparison notes — land them as `CHANGELOG.md` entries + a note on the leaderboard page, not as chat/drawer artifacts |
| Correct, reachable pages (no dead-on-load pages, no orphaned features) | Baseline competence signal; 3 pages currently abort in `setup()` | MEDIUM | Already milestone scope (navbar bug, submit flow) |

### Differentiators (Competitive Advantage)

Not required for a credible release, but they are where community trust is won — and most are unusually cheap for this repo because the machinery already exists.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Results versioning: tagged releases + version/date stamp on leaderboard data | HELM pins every leaderboard release to versioned config/schema so any number can be recreated; OLL's versioned-but-archived history is the community norm. Makes the species-fix recomputation auditable instead of suspicious | LOW | Git tag per data refresh + a "data generated: DATE, pipeline: SHA" line in the leaderboard footer / derived JSONs. Derived from work the milestone already does |
| Restored PR-based submission flow (`submit.html` + validation + PR instructions) | The only submission model compatible with a static, backend-less site (SQuAD/Papers-with-Code pattern; GenBench CBT ships a PR template). 300 lines already exist (`js/submit.js`), currently unreachable | MEDIUM | Milestone scope is *repair* (restore missing HTML, wire the orphaned JS, update to current data schema) — not submission automation. Label submitted results as self-reported |
| CI validation of derived data (JSON schema / sanity checks on performance files) | Detects the "stale derived files" failure mode the repo has today; HELM's `test-scenarios.yml` is the analog. No surveyed DNA benchmark does this — genuine differentiator | MEDIUM | Define minimal schema for the performance JSONs; CI fails if `dnallm-mark/data/` files are missing/malformed/mutually inconsistent. Extends the required test suite naturally |
| Public aggregation-methodology documentation (rank vs MinMax vs z-score vs robust) | The repo computes 4 aggregation methods offline but only shows one on the leaderboard; documenting (and optionally surfacing) the choice addresses the #1 reviewer question about composite scores | LOW | Docs page or README section; optionally a metric-dropdown reuse on the main page later. Kill the divergent dead code in `js/data.js:recalculateComparison()` while documenting (single source of truth) |
| Per-model metadata on the models catalog (license, params, checkpoint link, citation) | Model-card norm (Mitchell et al.); HF cards are the de-facto standard. A benchmark ranking 41 models without linking them is a dead end for readers | MEDIUM | Catalog page exists; enriching is data-entry + template work, no architecture change. Defer if time-boxed |
| Zenodo-archived release with DOI | Checklists: "GitHub is not a preservation solution"; UCSB/Zenodo workflows auto-DOI each release. Repo already uses Zenodo (the leaked token proves it) | LOW | Flip existing usage into a documented release pipeline: tag → GitHub release → Zenodo DOI in README |
| `CITATION.cff` (in addition to BibTeX) | GitHub renders a "Cite this repository" button; recommended by FAIR checklists (cff 1.2.0, ORCID) | LOW | 30-minute task; few academic repos do it, so it reads as polish |
| FLOPs/efficiency column as first-class metric | Already built (custom FLOPs instrumentation) — this IS the differentiator vs GUE/BEND-era tables. Research just confirms nobody else ships it; keep and document it | LOW (documentation only) | Mention in README/paper framing: efficiency-adjusted ranking, not just accuracy |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|----------|---------------|-----------------|-------------|
| Automated evaluation server (GLUE/SuperGLUE/EvalAI/Open-LLM-Leaderboard-style) | "Real" leaderboards re-run submissions on hidden test sets | Violates the hard static-site constraint; requires GPU infra, queueing, and permanent maintenance (OLL needed a dedicated cluster and still retired); hidden-test-set integrity is a full program | PR-based submissions clearly labeled self-reported, with a PR template asking for configs/logs; revisit only if community demand appears |
| Maintainer re-run verification of submitted results | Reviewers ask "did you verify their numbers?" | Unbounded GPU cost per submission; turns a static benchmark into a service with an SLA | Publication-of-record policy: leaderboard shows maintainer-run numbers only; submissions live in a separate clearly-marked table |
| Playwright/E2E frontend test suite | "Regression-proof the pages" | Explicitly descoped by decision; high maintenance for a vanilla MPA; the current bugs (navbar, missing HTML) are construction errors tests would only partially catch | Data-script unit tests + CI now; add a trivial `node --check`/HTML-lint CI step later if frontend regressions recur |
| Deep security hardening (CSP, SRI on CDN scripts, XSS surface removal) | Unescaped `innerHTML` is a real stored-XSS risk | Descoped this milestone by explicit prioritization; attempting it widens the diff against the surgical-fix discipline | Revoke the token (required), note the XSS surface as a known issue in the audit report so it is a documented risk, not a hidden one |
| Full Datasheets for all 50 datasets (Gebru-style, per dataset) | Reviewers cite the datasheet literature | 50 structured documents is weeks of work and blocks release on the least-certain data (older genomics datasets have murky licenses) | Provenance table now (source/citation/license/preprocessing columns); full datasheets only for datasets the paper highlights |
| Git history rewrite to purge the leaked token | "The token is still in history" | Post-revocation it protects nothing, breaks commit SHAs/forks, and rewrites the audited history the milestone just created | Revoke (the actual fix). Only if revocation fails: scrub before the first public push while history is still private |
| Pipeline rewrite / framework migration / new benchmark features | Natural reviewer urges ("while you're in there") | Explicit out-of-scope; widens review surface exactly when scrutiny is the point | Surgical fixes; park everything else in the backlog the audit report produces |

## Feature Dependencies

```
[Unit tests for data scripts]
    └──requires──> [Dependency manifests]        (CI installs what tests import)
                          │
[CI + badge] ──requires──┤
                          │
[JSON-schema data validation in CI] ──requires──> [Unit tests] (extends the suite)

[Token revocation] ─┐
[LICENSE] ──────────┼──requires──> [Tagged release] ──requires──> [Zenodo DOI]
[Changelog w/ before-after] ──┘

[Data recomputation] ──requires──> [Correctness fixes (species-grouping, navbar)]
       │
       └──enables──> [Results versioning / data date-stamp]

[Documented regeneration chain (Makefile target)] ──enhances──> [README reproducibility]
[Provenance table (DATA.md)] ──enhances──> [README reproducibility]

[submit.html restoration] ──requires──> [Current data schema stable after fixes]
                                    └──enhances──> [PR template (submission instructions)]
```

### Dependency Notes

- **CI requires tests + manifests:** the test suite must import only stdlib/numpy/pandas and declare them; CI that installs the GPU pipeline or `dnallm` is infeasible per project constraint — manifests must be split accordingly.
- **Changelog requires recomputation:** before/after numbers only exist after the species-grouping fix lands and data is regenerated; the changelog is therefore late-phase work, not documentation-day work.
- **Tagged release requires LICENSE + token revocation:** publishing a DOI on a repo with no license or a live secret archives the problem permanently.
- **submit.html restoration requires schema stability:** wiring orphaned JS against a data schema that fixes are actively changing would produce a second orphan; restore after recomputation freezes the derived-data shape.
- **Schema validation conflicts with nothing** but should ride in the same CI workflow as unit tests to avoid workflow sprawl.

## MVP Definition

### Launch With (v1 — this milestone's release-blocking set)

These map 1:1 onto the milestone's Active requirements; the research confirms each is table stakes, not gold-plating.

- [ ] Revoked Zenodo token — public repo with a live secret is an incident, not a release
- [ ] LICENSE (recommend MIT or Apache-2.0; DNABERT-2 precedent is Apache-2.0)
- [ ] Dependency manifests for the offline/data chain (pinned), separate from GPU pipeline notes
- [ ] Correctness fixes (navbar/render, species-as-dataset grouping, submit-flow repair)
- [ ] Unit tests for `script/` aggregation + pivot logic (synthetic fixtures, CPU-only)
- [ ] GitHub Actions CI running tests, badge in README
- [ ] Documented regeneration chain (single command target from repo root)
- [ ] Data recomputation + CHANGELOG.md with before/after comparisons of leaderboard numbers
- [ ] README reproducibility + dataset provenance table + BibTeX citation

### Add After Validation (v1.x — same quarter, post-release)

- [ ] `CITATION.cff` + Zenodo DOI on first tagged release — polish, 1–2 hours combined
- [ ] Version/date stamp on leaderboard pages (data-generated date + pipeline SHA)
- [ ] JSON-schema validation of derived data files in CI — after the post-fix schema settles
- [ ] Aggregation-methodology documentation (and remove the divergent dead code in `js/data.js`)
- [ ] Submission PR template + self-report labeling on the restored submit flow — trigger: first external submission request
- [ ] Per-model metadata enrichment on the models catalog — trigger: paper reviewers / community questions

### Future Consideration (v2+)

- [ ] CODE_OF_CONDUCT / CONTRIBUTING — none of DNABERT-2/BEND/NT ship them; becomes worthwhile when external contributions actually arrive (GenBench CBT is the model)
- [ ] Full datasheets for paper-highlighted datasets
- [ ] Docker environment export of the data-processing chain (NCCR checklist item; low value until someone else needs to regenerate)
- [ ] Any server-based verification — only if the benchmark gains a community that demands it, and only as a separately-hosted component (violates static-site constraint today)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Token revocation | HIGH | LOW | P1 |
| LICENSE | HIGH | LOW | P1 |
| Correctness fixes (navbar, species, submit) | HIGH | MEDIUM | P1 |
| Data-script unit tests | HIGH | MEDIUM | P1 |
| CI + badge | HIGH | LOW | P1 |
| Dependency manifests | HIGH | LOW | P1 |
| README reproducibility + regeneration target | HIGH | LOW | P1 |
| Recompute + CHANGELOG (before/after) | HIGH | MEDIUM | P1 |
| Dataset provenance table | HIGH | MEDIUM | P1 |
| Citation (BibTeX; CFF optional) | MEDIUM | LOW | P1 (BibTeX) / P2 (CFF) |
| Version/date stamp on leaderboard | MEDIUM | LOW | P2 |
| Aggregation-method docs | MEDIUM | LOW | P2 |
| JSON-schema CI validation | MEDIUM | MEDIUM | P2 |
| Zenodo DOI + tagged release | MEDIUM | LOW | P2 |
| Model metadata enrichment | MEDIUM | MEDIUM | P2–P3 |
| Submission PR template | MEDIUM | LOW | P2 |
| CoC/CONTRIBUTING | LOW now | LOW | P3 |
| Datasheets (full) | MEDIUM | HIGH | P3 |
| Eval server / verification service | — | — | Out (constraint) |

## Competitor Feature Analysis

| Feature | HELM (Stanford) | Open LLM Leaderboard / lm-eval-harness | DNABERT-2 (GUE) | BEND | Nucleotide Transformer | GenBench CBT | DNALLM-Mark approach |
|---------|-----------------|----------------------------------------|------------------|------|------------------------|--------------|----------------------|
| License | Apache-2.0 | MIT | Apache-2.0 | BSD-3 | Custom LICENSE.md | Custom (10KB) | Add MIT/Apache-2.0 (none today) |
| Tests + CI | 9 workflows, conftest | unit_tests.yml, tests/ | check_build.yml only, no tests | none | none | tests/ + CI | Add CPU-only pytest suite + one workflow |
| Reproducibility docs | "Reproducing Leaderboards" with version-pinned configs | harness versioning; archived v1 with non-comparability warnings | README commands, GUE via Drive | docs site, conf-driven | notebooks | README + Makefile | Single-command data chain + pinned manifests |
| Results versioning | CHANGELOG.md + per-release schema | v1 frozen/archived; explicit cross-version warnings | Figures in README (static) | n/a | Site leaderboard | n/a | Git-tag data refreshes + CHANGELOG + date stamp |
| Data provenance | Scenario configs per benchmark | HF dataset cards | GUE composition documented | Task defs in conf/ + docs | HF model/dataset cards | Templates for tasks | Provenance table for 50 datasets (DATA.md + catalog) |
| Submission model | Self-run via harness | Automated server + flagging | n/a (self-run) | n/a | Site leaderboard | PR-based + PR template | Repair PR-based flow (static-site compatible) |
| Citation | CITATION.bib | CITATION.bib | README BibTeX | README BibTeX | README | AUTHORS | BibTeX now, CITATION.cff soon after |
| Efficiency metrics | Calibration/bias/toxicity beyond accuracy | No (accuracy-centric) | No | No | No | No | FLOPs-vs-performance already built — keep and document it |

## Sources

Live-verified 2026-10-08:
- GitHub API file listings + license (SPDX) checks: `stanford-crfm/helm`, `EleutherAI/lm-evaluation-harness`, `gluonfield/BEND`, `instadeepai/nucleotide-transformer`, `MAGICS-LAB/DNABERT_2`, `GenBench/genbench_cbt` (MEDIUM confidence per source-hierarchy seam — websearch-verified)
- HELM "Reproducing Leaderboards" docs (crfm-helm.readthedocs.io) — version-pinned leaderboard recreation (MEDIUM)
- DNABERT-2 repo page fetch: README structure, GUE data distribution, figures-based results, no CONTRIBUTING/tests (MEDIUM)
- Live web results: Imageomics Code Checklist, Zenodo FAIR Code Publishing roadmap, KU Leuven FAIR software, UCSB Research Data Services, GEO-Inquire FAIR training, NCCR Exit Strategy (MEDIUM); BEND paper (arXiv 2311.12570) and NT public leaderboard reference (MEDIUM)

Model-knowledge fallbacks (LOW — consistently corroborated across searches and training, but pages JS-rendered/unfetchable this run):
- Open LLM Leaderboard v1→v2 archive, non-comparability warnings, flagging features, 2025 retirement
- GLUE/SuperGLUE evaluation-server submission model (registration, terms, single-model rule)
- Datasheets for Datasets / Model Cards / Croissant specifics; PR-vs-server submission-pattern taxonomy

None of the P1 recommendations above rest on LOW-confidence claims: every P1 item is justified by the live-verified repo survey and checklists.

---
*Feature research for: public-release hardening of a DNA LLM benchmark platform*
*Researched: 2026-10-08*
