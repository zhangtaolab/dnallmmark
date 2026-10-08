# Phase 1: Audit & Release Foundations - Research

**Researched:** 2026-10-08
**Domain:** Release engineering for a research benchmark repo — systematic audit mechanics, reproducible dependency manifests (uv/PEP 735), golden-baseline capture, generator determinism, full-history secret scanning
**Confidence:** HIGH — every load-bearing claim was verified this session by direct code reads (with line quotes), PyPI registry JSON API queries, local tool probes, and a full empirical regeneration of the data chain on the target machine (Python 3.13.16, aarch64, pandas 2.3.3, numpy 2.5.3)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Fresh systematic review — parallel review agents across the three subsystems (pipeline / data scripts / frontend); `.planning/codebase/CONCERNS.md` is input, not conclusion; every finding must be reproduced/verified and severity-graded before entering the report
- **D-02:** Audit report is published in-repo as `AUDIT.md` (cleaned, public) — transparency toward reviewers is the milestone's selling point
- **D-03:** Findings beyond existing REQ-IDs are placed by tier: anything affecting leaderboard correctness or page function joins Phase 4 scope; the rest (dead code, performance, log noise) goes to the milestone backlog
- **D-04:** Audit effort is correctness-first: deep-dive aggregation math (rank/MinMax/z-score/robust), FLOPs extrapolation, pipeline config mutation, data-flow consistency; maintainability findings are recorded but not severity-graded
- **D-05:** Original data-generation environment (2026-03-31 data) no longer exists — pin by floor bounds (`pandas>=2.2,<3.0` latest 2.x, numpy bounded alongside) and validate by regenerating the data chain, comparing values against committed JSONs — **Reversibility:** costly — pins propagate into uv.lock, CI matrix, and every consumer environment once published
- **D-06:** Validation standard: any value difference → stop and investigate (version behavior change / floating-point / hidden bug) until explained; only then are pins authoritative
- **D-07:** Data-chain environment: repo-local uv-managed venv, **Python 3.13**, strictly isolated from `/home/forrest/Github/DNALLM/.venv` (pandas 3.0.6 — reserved for Phase 3 pipeline adaptation); uv 0.12.23 already installed at `~/.local/bin/uv`
- **D-08:** The Zenodo record-19135551 preview link + token at `README.md:116` **stays as-is** — it is the intentional dataset-sharing mechanism (record-scoped, read-only); do NOT revoke, do NOT rewrite git history for it; a full-history secret scan remains useful only to confirm no OTHER secrets exist beyond this known-intentional link
- **D-09:** Repo visibility assumed private now, flipping public at milestone end
- **D-10:** MIT per the existing README badge (`README.md:3`), with a separate data-terms statement for derived leaderboard data — user may override any time before planning lands it — **Reversibility:** one-way once publicly released

### Claude's Discretion
- Severity scheme and report structure for AUDIT.md (suggest P0/P1/P2 with file:line + reproduction + recommended fix per finding)
- How review agents are partitioned (by subsystem × dimension)
- pyproject.toml / uv.lock / requirements.txt-export structure (follow `.planning/research/STACK.md` recommended stack)
- Exact form of the `data-v1` baseline artifact (tag + golden copies vs tag-only)

### Deferred Ideas (OUT OF SCOPE)
- Zenodo record 19135551: after formal publish, swap the README link to the clean token-free record URL (preview tokens invalidate naturally on publish) — post-release nicety, not milestone work
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUDIT-01 | Severity-graded findings report covering all three subsystems, every finding with `file:line` evidence and a recommended fix | Audit execution mechanics section: agent partitioning, per-subsystem reproduction methods, P0/P1/P2 scheme, AUDIT.md skeleton; CONCERNS.md seed inventory; one pre-verified fresh finding (stale `tasks.json` metric casing) |
| AUDIT-02 | Pre-fix baseline captured — golden outputs of the current data chain plus a `data-v1` git tag — before any result-affecting fix lands | Baseline capture section: tag mechanics (no tags exist yet), checksum manifest + canonical comparator (validated this session), full scratch-regeneration procedure with verified commands |
| REL-01 | LICENSE file present (explicit code license; data licensing declared separately) | MIT text standard per README badge; data-terms pattern — repo redistributes only derived aggregates (raw datasets gitignored), which keeps the data-terms statement simple and factual |
| REL-02 | Dependency manifests for the offline/data chain, version-pinned (`pandas>=2.2,<3.0`); GPU pipeline dependencies in a separate group CI never installs | pyproject.toml skeleton (PEP 621 + PEP 735 + `[tool.uv] package = false`), verified pandas 2.3.3 / numpy 2.5.3 cp313 aarch64 wheels, empirically validated pin floor, **`.gitignore:47` currently ignores `uv.lock` — must be removed** |
| REL-05 | Secret hygiene settled per maintainer decision — Zenodo link stays; full-history scan confirms no OTHER secrets | gitleaks 8.30.1 (brew-bottled on this machine), `.gitleaks.toml` allowlist config with AND-condition, `gitleaks git` full-history invocation, clean-evidence definition |
| FIX-05 | All three data generators produce deterministic output (sorted directory iteration + `sort_keys` JSON writing) | Exact fix sites read and quoted from source; one fix site already sorted (JS); residual JS nondeterminism is `generatedAt`; empirical run-twice byte-identity proof; tie-rank root cause |
</phase_requirements>

## Summary

Phase 1 is de-risked to an unusual degree by this research: **the pin-validation experiment (D-05/D-06) and the determinism experiment were actually executed this session** in a scratch checkout (`/tmp/dnallm-regen`). The full 3-script chain ran successfully on a uv-managed CPython 3.13.16 (aarch64) with pandas 2.3.3 + numpy 2.5.3, run twice with byte-identical outputs, and value-compared against the committed JSONs. The comparison surfaced a complete, root-caused diff taxonomy: **0/47 task_performance files differ in value; models_comparison differs ONLY in `sum_zscore` (38 models, relative diff ≤ 2.4e-14 — numpy cross-version float behavior in mean/std, not a pandas semantic change) and `rank` (4 models = two exact-tie pairs at rank_score 1232.0 and 749.0 whose order is decided by `os.listdir` insertion order on the generating machine — exactly the class of nondeterminism FIX-05 eliminates)**. Every other field — raw scores, minmax, robust, rank_score, top-K counts, FLOPs sums, samples — is bit-identical. The D-06 "any value diff → investigate" obligation is therefore already substantially discharged: the phase formalizes the evidence, it does not discover it.

Three repo-state traps found: **`.gitignore:47` ignores `uv.lock`** (fatal for a reproducibility milestone — the lockfile must be committed); `scripts/generate-tasks-index.js` is **already sorted** (lines 18–20) and its only remaining nondeterminism is the `generatedAt` date stamp (line 50), which will also break Phase 5's drift-detection job if not addressed now; and the committed `tasks.json` carries `metric: 'auprc'` for `BEND__CpG_methylation` while the sibling `task_performance` file says `'AUPRC'` — a live stale-derived-data instance that seeds AUDIT-01. Tooling is verified available: uv 0.12.23 with `--group`/`export` support, Node 26.10.0, brew 7.0.8 bottling gitleaks 8.30.1, jq 1.7, make 4.3; only gitleaks needs installing (`brew install gitleaks`).

**Primary recommendation:** Sequence the phase as (1) parallel audit agents → merged/verified AUDIT.md; (2) `data-v1` tag + SHA256 manifest + canonical comparator committed; (3) pyproject.toml + uv.lock + requirements.txt export (with the `.gitignore` fix); (4) FIX-05 determinism commit + one-time regeneration + value-compare against the baseline (expected diffs = key order + the 38 `sum_zscore` ULP + 2 tie-rank swaps, all pre-root-caused) + run-twice byte-identity check; (5) LICENSE + data-terms; (6) gitleaks install + allowlisted full-history scan with clean evidence recorded in AUDIT.md.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Systematic audit (AUDIT-01) | Review tooling (parallel agents) | All 3 subsystems as subjects | Findings must originate from fresh code reading; agents partition by subsystem, orchestrator verifies each finding before it enters AUDIT.md (D-01) |
| Baseline freeze (AUDIT-02) | Git/repo substrate | Offline data chain | A git tag + checksum manifest makes the pre-fix byte state permanently recoverable and diffable; derived-file bytes live in git already |
| Determinism fix (FIX-05) | Offline data scripts (`script/`, `scripts/`) | — | Only the 3 generators write derived JSON; sorting + `sort_keys` there is the single leverage point |
| Dependency manifests (REL-02) | Repo/build substrate (pyproject.toml + uv.lock) | Offline data chain as consumer | uv owns resolution + lock; CI (Phase 5) and contributors consume groups; GPU pipeline group documented but never installed in CI |
| License + data terms (REL-01) | Repo substrate (root files) | README | Legal declaration is a root-level artifact; data terms must be separate from code license (P7 pitfall) |
| Full-history secret scan (REL-05) | Security tooling (gitleaks over `.git`) | Repo config (`.gitleaks.toml`) | Only a scanner over full history produces the "no other secrets" evidence; allowlist lives in-repo, reviewable |
| Frontend verification (audit input) | Static frontend (browser via local server) | Static reasoning | Pages need an HTTP origin (ES modules + fetch); audit agents verify rendering claims in a browser, not by guesswork |

## Standard Stack

### Core

| Tool / Package | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| uv + uv.lock | 0.12.23 (installed, `~/.local/bin/uv`) | venv + resolution + lockfile + requirements export | One tool for the reproducibility substrate; `uv sync --group`, `uv export --format requirements.txt`, `uv venv --python 3.13` all verified against the installed binary this session. PEP 735 groups natively supported [VERIFIED: local binary `uv sync --help` / `uv export --help` output this session] |
| pandas | 2.3.3 (latest 2.x; latest overall is 3.0.6) | `script/summarize_comparison.py` aggregation | D-05 floor `>=2.2,<3.0`. `requires_python >=3.9`; numpy dep `numpy>=1.26.0; python_version >= "3.12"`; **cp313 AND cp314 manylinux aarch64 wheels verified on PyPI** (also musl + cp313t). Empirically installed and ran the chain on 3.13.16/aarch64 [VERIFIED: pypi.org/pypi/pandas/2.3.3/json + this session's scratch run] |
| numpy | 2.5.3 (latest 2.x) | float math in `summarize_comparison.py` | `requires_python >=3.12`; cp313 aarch64 manylinux wheels verified; installed and executed this session [VERIFIED: pypi.org/pypi/numpy/2.5.3/json] |
| gitleaks | 8.30.1 | Full-history secret scan (REL-05) | Latest release ships `gitleaks_8.30.1_linux_arm64.tar.gz`; **brew 7.0.8 on this machine bottles exactly 8.30.1** → `brew install gitleaks`. `git` subcommand (history scan via `git log -p`; `detect` deprecated since v8.19.0); `[extend] useDefault = true` + `[[allowlists]]` config model [VERIFIED: GitHub Releases API + `brew info gitleaks` + github.com/gitleaks/gitleaks README] |
| git tags | built-in | `data-v1` annotated tag (AUDIT-02) | Zero-dependency freeze; no tags currently exist in the repo (`git tag -l` empty) [VERIFIED: local git this session] |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| Node.js | v26.10.0 (system) | Run `scripts/generate-tasks-index.js` (no deps) | Every regeneration; verified working this session |
| jq | 1.7 | Quick JSON inspection during audit | Ad-hoc checks; canonical comparison still needs the Python comparator (key-order-insensitive) |
| make | 4.3 | (Phase 2 formalizes targets) Optional Phase 1 convenience | Not required this phase; scratch procedure uses plain commands |
| brew | 7.0.8 (linuxbrew, aarch64) | Install gitleaks | `brew install gitleaks` — bottled 8.30.1 matches upstream latest |
| uv-managed CPython | 3.13.16 | Data-chain interpreter (D-07) | `uv python list` shows `cpython-3.13.16-linux-aarch64-gnu <download available>` — verified this session; keep isolated from DNALLM/.venv (3.13.15 + pandas 3.0.6 — do NOT touch) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| gitleaks | trufflehog | trufflehog not installed either; gitleaks is brew-bottled (zero friction), has the allowlist model REL-05 needs, and a stabled `git` history-scan subcommand. trufflehog's live-credential verification is irrelevant here (token is intentionally live) |
| uv + pyproject (PEP 621/735) | plain requirements.txt | requirements.txt alone gives no lockfile/consistency guarantee; keep a `uv export`-generated requirements.txt alongside for pip-only contributors (best of both, per STACK.md) |
| pandas 2.3.3 floor pins | exact `==2.3.3` pins | D-05 locks floor bounds, not exact pins — the original generation env is gone, so "exact" would be false precision; the lockfile supplies exactness for reproducibility while the manifest documents intent |
| SHA256 manifest + canonical comparator | golden copies in-tree | git already stores exact bytes at the tag; copies duplicate 47+ files and rot. Manifest + comparator + `git diff data-v1` covers "recoverable and diffable" with one artifact each |

**Installation:**

```bash
brew install gitleaks                      # 8.30.1 bottled — verified
~/.local/bin/uv venv .venv --python 3.13   # repo-local, CPython 3.13.16 — verified this session
~/.local/bin/uv sync                       # after pyproject.toml exists (creates uv.lock)
~/.local/bin/uv export --group data --no-emit-project -o requirements.txt
```

**Version verification:** pandas 2.3.3, numpy 2.5.3, their `requires_python`, and aarch64 cp313/cp314 wheel filenames all confirmed via PyPI JSON API (`pypi.org/pypi/{pandas,numpy}/{ver}/json`) on 2026-10-08. gitleaks 8.30.1 confirmed via GitHub Releases API and `brew info`.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| pandas | PyPI | since 2010 (2.3.3 published recently; 3.0.6 latest) | PyPI download counts unavailable via seam | pandas-dev/pandas (PyPI metadata null via seam) | SUS* | Approved — D-05 locked; see note |
| numpy | PyPI | since 2005 (2.5.3 current line) | PyPI download counts unavailable via seam | numpy/numpy (PyPI metadata null via seam) | SUS* | Approved — see note |
| gitleaks | binary (GitHub Releases / brew) | since 2018 | n/a | github.com/gitleaks/gitleaks | OK | Approved |

*The seam's PyPI probe returns `weeklyDownloads: null` and `repoUrl: null`, so canonical packages mechanically flag as SUS on missing signals — not on negative evidence. Both packages are **locked by user decision D-05**, were resolved directly against `pypi.org/pypi/{name}/json` this session (wheels, `requires_python`, and dependency metadata inspected), and were **empirically installed and executed end-to-end** in this session's scratch validation. No `checkpoint:human-verify` is warranted; the empirical run is stronger evidence than any registry signal.

**Packages removed due to SLOP verdict:** none
**Packages flagged as suspicious [SUS]:** none beyond the metadata-gap note above

## Architecture Patterns

### System Architecture Diagram

The audit observes three subsystems; the baseline freeze and determinism work act on the offline data chain only. Data flows one way (pipeline → committed inputs → derived JSON → static frontend); nothing in Phase 1 changes the runtime architecture.

```
                          ┌──────────────────────────── PHASE 1 OBSERVERS ────────────────────────────┐
                          │  audit agents (pipeline / data scripts / frontend)  →  verified findings   │
                          │  gitleaks ──scan──▶ full git history ──▶ report (allowlisted link only)    │
                          └───────────────────────────────────────────────────────────────────────────┘
                                              │ AUDIT.md (repo root)
                                              ▼
 pipeline/dnallmmark_pipeline.py     ┌── offline data chain (FIX-05 targets) ───────────────┐
 (GPU, static-analysis-only this     │                                                       │
  phase; species bug → Phase 4)      │  model_performance/*.json  (42 committed inputs)      │
        │ historical producer        │        │                                             │
        ▼                            │        ├─▶ summarize_comparison.py ──▶ models_comparison{,_animal,_plant,_microbe}.json
 {model}_performance.json ─────────▶ │        │    (numpy+pandas, sums floats in listdir order)   │
                                    │        └─▶ get_task_performance.py ──▶ task_performance/*.json (47, stdlib-only)
                                    │                     │                                   │
                                    │                     ▼                                   │
                                    │          generate-tasks-index.js ──▶ tasks.json          │
                                    │          (already sorted; `generatedAt` = today)          │
                                    └──────────────────────┬────────────────────────────────┘
                                                           ▼
                                    dnallm-mark/js/* (static MPA, fetch './data/...')
                                    ═══ byte-baseline frozen at git tag data-v1 ═══
```

### Recommended Project Structure (additions only)

```
/ (repo root)
├── AUDIT.md                    # NEW — public findings report (D-02)
├── LICENSE                     # NEW — MIT (D-10)
├── pyproject.toml              # NEW — PEP 621 + PEP 735 groups, [tool.uv] package=false
├── uv.lock                     # NEW — committed (REMOVE from .gitignore:47 first)
├── requirements.txt            # NEW — generated: uv export --group data (header: "generated")
├── .gitleaks.toml              # NEW — default rules + allowlist for the intentional link
├── .python-version             # NEW (optional) — "3.13"; REMOVE from .gitignore:7 if committed
└── baseline/
    ├── data-v1.sha256          # NEW — checksums of all committed derived JSON at tag time
    └── compare.py              # NEW — canonical (order-insensitive) value comparator, validated
```

### Pattern 1: Audit agent partitioning — subsystem agents × shared dimension checklist

**What:** Three parallel review agents (pipeline / data scripts / frontend), each receiving the same correctness-first dimension checklist from D-04, plus the CONCERNS.md entries for its subsystem as *seed hypotheses to re-verify, not conclusions*.

**When to use:** AUDIT-01 execution (parallelization is enabled in `.planning/config.json`).

**Dimensions per D-04 (assign to every agent; pipeline gets extra weight on 2–3):**
1. Aggregation math — rank (`method='min'`, `N - rank`), MinMax, z-score, robust (median/IQR) in `script/summarize_comparison.py`; division-by-zero guards; missing-metric exclusion semantics
2. FLOPs extrapolation — hook coverage, ×3 ×epochs scaling, silent-zero risk (FlopsCounter dispatch)
3. Pipeline config mutation — in-place config edits leaking across models (CONCERNS: lines 835–838, 862–864), resume semantics, error swallowing that silently drops models from rankings
4. Data-flow consistency — the `{info, performance}` seam across pipeline → scripts → every JS consumer (three known nesting misreads already documented)
5. (Frontend agent) rendering/event-binding correctness beyond the known crash — listener loss on re-render, sort-state bugs, stale-cache/mismatch class

**Finding schema every agent must emit (enables the verify pass):**
`subsystem | severity-proposal (P0/P1/P2) | file:line | claim | reproduction evidence | recommended fix`

**Reproduction standard per subsystem (what "verified" means):**
- **Data scripts:** runnable — regenerate in a scratch copy (procedure below, validated this session) or reason over exact inputs/outputs; every numeric claim checked against actual committed JSON values (jq / python)
- **Pipeline:** static analysis only this phase — no GPU/dnallm environment exists and importing the module raises NameError (module globals defined under `if __name__ == "__main__":` per CONCERNS); "reproduction" = a code-path trace with quoted lines, plus data-side cross-checks against the 42 committed `model_performance/*.json` (e.g., species-field provenance)
- **Frontend:** browser verification — `bash start-server.sh` (or `python3 -m http.server 8080` from `dnallm-mark/`), then check each page in a browser; claims about console errors / dead pages must cite what was actually observed. Static claims (dead code, unused CDN includes) verified by grep with quoted evidence

**Merge/verify pass (D-01 enforcement):** the orchestrator independently reproduces every finding before it enters AUDIT.md; findings that fail reproduction are dropped or demoted to "unverified observation" — they do not get severity grades.

### Pattern 2: AUDIT.md report structure (discretion item — recommended)

```markdown
# DNALLM-Mark Code Audit — 2026-10
Scope: pipeline / data scripts / frontend at commit <sha> (pre-fix, tag data-v1)
Method: parallel systematic review; every finding independently reproduced; seed inventory (.planning/codebase/CONCERNS.md) re-verified, not copied

## Executive summary          (counts by severity × subsystem; top risks)
## Findings table
| ID | Sev | Subsystem | Location | Finding | Reproduction | Recommended fix | Disposition |
(AUD-xx-P0/P1/P2; disposition per D-03: "Phase 4 scope" / "milestone backlog" / "recorded, not graded")
## Severity definitions       (P0/P1/P2 — see below)
## Methodology & limitations  (what was and was not run: no GPU, no dnallm import; browser checks listed)
## Secret-scan evidence       (gitleaks command + exit code + empty report, link stays per D-08)
```

**Severity scheme (recommended):**
- **P0 — leaderboard integrity:** anything that makes a published number wrong or risks corrupting data (aggregation math errors, pipeline data-integrity regressions, silent model dropping, live unintended secrets)
- **P1 — user-facing breakage / reproducibility:** dead pages, broken flows, nondeterminism, unreproducible environment, missing license — breaks external trust or blocks the release
- **P2 — hygiene & debt:** dead code, doc drift, console noise, performance, log noise (recorded; routed to backlog per D-03)

Maintainability findings: recorded in a separate non-graded list (D-04).

### Pattern 3: Baseline capture & validation regeneration (AUDIT-02 + D-05/D-06 mechanics)

**Validated procedure (executed this session — commands are proven, not hypothetical):**

```bash
# 0) Freeze pre-fix state FIRST (no result-affecting change has landed)
cd /home/forrest/Github/dnallmmark
git tag -a data-v1 -m "Pre-fix derived-data baseline (FIX-05 lands after this point)"
cd dnallm-mark/data && sha256sum models_comparison*.json tasks.json task_performance/*.json \
  > ../../baseline/data-v1.sha256 && cd ../../..

# 1) Scratch copy (layout must mirror repo for generate-tasks-index.js — see Pitfall 7)
mkdir -p /tmp/dnallm-regen/scripts /tmp/dnallm-regen/dnallm-mark/data
cp -r dnallm-mark/data/model_performance /tmp/dnallm-regen/dnallm-mark/data/
cp scripts/generate-tasks-index.js /tmp/dnallm-regen/scripts/

# 2) Isolated Python 3.13 env (D-07 — repo-local pattern proven here in /tmp)
~/.local/bin/uv venv /tmp/dnallm-regen/.venv --python 3.13
~/.local/bin/uv pip install --python /tmp/dnallm-regen/.venv/bin/python 'pandas==2.3.3' 'numpy>=2.0,<3'

# 3) Run the chain — BOTH Python scripts are CWD-sensitive (run from the scratch data dir)
cd /tmp/dnallm-regen/dnallm-mark/data
/tmp/dnallm-regen/.venv/bin/python /home/forrest/Github/dnallmmark/script/summarize_comparison.py
/tmp/dnallm-regen/.venv/bin/python /home/forrest/Github/dnallmmark/script/get_task_performance.py
node /tmp/dnallm-regen/scripts/generate-tasks-index.js

# 4) Value-compare against committed files (order-insensitive)
/tmp/dnallm-regen/.venv/bin/python baseline/compare_json.py \
  <committed.json> <regenerated.json>        # per file

# 5) Determinism: rerun step 3 → byte-identical (verified: cmp across all outputs)
```

**CWD contracts, quoted from source [VERIFIED: script/summarize_comparison.py:274-277; script/get_task_performance.py:78-82]:**
- `summarize_comparison.py` — `input_dir = 'model_performance'`, `output_total = 'models_comparison.json'` ("written to CWD")
- `get_task_performance.py` — `input_dir = "model_performance"`, `output_dir = "task_performance"`
- `generate-tasks-index.js` — `__dirname`-relative, CWD-independent [VERIFIED: scripts/generate-tasks-index.js:11-12 — `path.join(__dirname, '..', 'dnallm-mark', 'data', 'task_performance')`]

### Pattern 4: Three distinct comparisons — never confuse them

| Comparison | Tool | Question answered | Expected result (pandas 2.3.3 vs committed) |
|------------|------|-------------------|---------------------------------------------|
| **Byte** | `cmp` / `sha256sum` | Determinism (FIX-05, success criterion 3) | run-1 vs run-2: **identical** (verified); regen vs committed: differs (key order) |
| **Canonical value** | `baseline/compare_json.py` (parse → recursive walk, key-order-insensitive, exact per-value) | Pin validation (D-06) | **Only** `sum_zscore` (38/42 models, rel ≤ 2.4e-14) + `rank` (2 tie pairs) in comparison files; `task_performance` 0/47; `tasks.json` 1 field + `generatedAt` |
| **Tolerant float** | same comparator, rel < 1e-12 bucket | Root-cause triage | ULP bucket vs BIG bucket separates noise from real changes |

### Anti-Patterns to Avoid
- **Re-running the pre-fix chain to "produce" the golden baseline:** the committed derived files at tag `data-v1` ARE the golden outputs; pre-fix regeneration is itself order-nondeterministic across machines. Use git + checksums, not fresh runs, as the freeze.
- **Comparing regenerated bytes to committed bytes to judge pandas behavior:** byte diffs conflate key order with values; only the canonical comparator answers D-06 questions.
- **Interpreting the 38 `sum_zscore` ULP diffs or the 2 tie-rank swaps as pandas-3.0-style semantic breakage:** both are root-caused (see Common Pitfalls 4/8); the raw, minmax, robust, rank_score, top-K, and FLOPs fields are bit-identical.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Full-history secret detection | grep/regex over `git log -p` | gitleaks 8.30.1 (`gitleaks git` subcommand) | Detector rulesets cover ~150 secret types (incl. JWT — the Zenodo token is JWT-shaped); hand-rolled regex miss encodings/history edge cases and give no report artifact |
| Dependency locking | manually curated version lists | uv lockfile (`uv.lock`) committed | Lock captures the full resolution incl. transitive deps and hashes; manual lists rot instantly |
| Order-insensitive JSON diff | `diff`/`grep` over pretty-printed JSON | canonical parse + recursive walk (validated comparator committed as `baseline/compare.py`) | Key order and float repr make textual JSON diff useless for value questions; a 60-line validated comparator already exists from this research |
| Wheel/platform availability checks | guessing "probably supports 3.13" | PyPI JSON API (`pypi.org/pypi/<pkg>/<ver>/json` → `.urls[].filename`) | cp313/cp314 aarch64 wheel presence is a 1-request factual check; this session proved both pandas 2.3.3 and numpy 2.5.3 ship them |
| Pre-fix state freeze | copying derived JSONs into a `backup/` folder | annotated git tag + SHA256 manifest | git already stores exact bytes forever; copies duplicate and silently diverge |

**Key insight:** every "don't hand-roll" item here is a place where a hand-rolled version produces *plausible but wrong* evidence — the exact failure mode a public-scrutiny release cannot afford.

## Common Pitfalls

### Pitfall 1: `.gitignore` swallows the lockfile
**What goes wrong:** `.gitignore:47` contains `uv.lock` (inherited from upstream dnallm tooling, like the `.ruff_cache/` entries CONVENTIONS.md notes). The lockfile silently never gets committed and the reproducibility guarantee evaporates. `.gitignore:7` also ignores `.python-version`.
**How to avoid:** Remove `uv.lock` from `.gitignore` (and `.python-version` if the phase commits one) in the same commit that adds `pyproject.toml`. Verify with `git check-ignore uv.lock` returning nothing.
**Warning signs:** `git status` clean after `uv lock`; CI installing drifting versions.

### Pitfall 2: Tag-after-fix ordering
**What goes wrong:** If FIX-05 or the regeneration commit lands before `data-v1` is tagged, the tag no longer marks the as-published byte state; the "before" side of every before/after comparison is blurred.
**How to avoid:** First commit of any result-affecting change triggers the tag first. Tag placement = last pre-fix commit (planner pins the exact SHA; no tags exist today — verified `git tag -l` is empty).
**Warning signs:** tag created on a commit that already touches `script/`, `scripts/`, or `dnallm-mark/data/`.

### Pitfall 3: Byte comparison used where value comparison is meant (and vice versa)
**What goes wrong:** "Regenerated output differs from committed!" panic over key order, or false confidence over byte equality on the same machine only.
**How to avoid:** Apply the three-comparison table (Pattern 4). Determinism = run-twice byte identity. Pin validation = canonical value compare. D-06 investigation = the ULP/BIG triage.
**Warning signs:** any diff discussion that doesn't say which of the three comparisons it is.

### Pitfall 4: ULP-level `sum_zscore` diffs misread as pandas behavior change
**What goes wrong:** 38 of 42 models show `sum_zscore` diffs (e.g. `36.08327926630596` vs `36.08327926630597`, rel 3.9e-16) — looks like "pandas changed the numbers."
**Root cause (established this session):** per-dataset z-score uses `np.mean`/`np.std` (summarize_comparison.py:143-144); their float summation behavior differs between the original (unknown, 2026-03-31) generation environment and numpy 2.5.3. Fields computed without mean/std — raw, MinMax (`np.min`/`np.max` + one division), robust sums, integer-valued rank scores, top-K counts, FLOPs — are **bit-identical**, which is exactly the signature of float-noise, not semantic change.
**How to avoid:** document this taxonomy in AUDIT.md / the pin rationale; accept via the established inventory (any NEW field diffing → stop, per D-06).

### Pitfall 5: Tie-rank swaps look like ranking corruption
**What goes wrong:** `Omni-DNA-700M` vs `plant-dnabert-6mer` (both rank_score 1232.0) and `gena-lm-bigbird-base-t2t` vs `hyenadna-large-1m-seqlen-hf` (both 749.0) swap rank 13↔14 and 29↔30 between committed and regenerated files.
**Root cause:** exact ties; Python `sorted()` is stable, so order falls back to `models_info` insertion order = `os.listdir` order on the generating machine (the original machine's directory order differed from this machine's — proven: identical values otherwise, and readdir order here is name-hash stable [verified: a reverse-order copy produced the same listdir order and identical output]). FIX-05's `sorted(os.listdir())` makes ties resolve deterministically (alphabetical) everywhere — note this means the fix commit itself may flip these two pairs once more; that is the documented, expected byte-layout change.
**How to avoid:** pre-document both tied pairs in AUDIT.md so the post-fix diff is attributable rather than alarming.

### Pitfall 6: `generatedAt` breaks cross-day byte stability (and Phase 5's drift job)
**What goes wrong:** `scripts/generate-tasks-index.js:50` stamps `generatedAt: new Date().toISOString().split('T')[0]` — same-day reruns are byte-identical (verified), but any next-day regeneration (or the future CI regenerate-and-`git diff --exit-code` job, TEST-07) always fails on that one field. Committed value is `2026-03-31`; today's run writes `2026-10-08`.
**How to avoid:** handle inside FIX-05 — derive the stamp from inputs (e.g., max input mtime), make it a CLI argument the (Phase 2) Makefile passes, or drop the field. Planner decision; leaving it as-is pushes the failure into Phase 5.
**Warning signs:** `tasks.json` diff whose only content line is the date.

### Pitfall 7: Scratch regeneration writes into the live repo
**What goes wrong:** the Node script resolves `task_performance` and `tasks.json` via `__dirname`, so running the repo's copy in place overwrites committed files mid-audit; the Python scripts write to CWD, so running them from the repo root scatters outputs.
**How to avoid:** scratch layout mirrors the repo (`<scratch>/scripts/`, `<scratch>/dnallm-mark/data/model_performance/`), Python scripts run with CWD = scratch data dir (Pattern 3, validated).

### Pitfall 8: gitleaks allowlist too broad
**What goes wrong:** a global allowlist with `paths = ['''README\.md''']` alone (default condition OR, matching on any criterion) would mask any *future* secret committed to README; a regex targeting only `token=` similarly over-allows.
**How to avoid:** `condition = "AND"` combining the README path with a tight regex on the exact record URL + token prefix (`zenodo\.org/records/19135551\?preview=1&token=`); sanity-test the config by scanning and confirming exit 0, and optionally by a canary file with a fake token that MUST be caught. First run may need regex tuning — the config is [CITED: github.com/gitleaks/gitleaks] and iteratively verifiable.
**Warning signs:** scan exit 0 on the first try with no allowlist firing evidence; report shows nothing while README still contains the token.

### Pitfall 9: stale derived data discovered mid-phase (it already exists)
**What goes wrong:** committed `tasks.json` says `metric: 'auprc'` for `BEND__CpG_methylation` while its own input (`task_performance/BEND__CpG_methylation_task_performance.json`, and the model files) says `'AUPRC'` — the index is not a faithful projection of the current tree (generated 2026-03-31; the generation also does not apply summarize_comparison's `metric_key_map` casing map, which maps `"AUPRC": "auprc"` [VERIFIED: script/summarize_comparison.py:299]). Possible downstream effect: the task page looking up performance by the cased key misses — audit lead for the frontend agent, NOT a confirmed page bug.
**How to avoid:** treat as an AUDIT-01 seed finding (stale-derived-data class); FIX-05's regeneration will reconcile it (regenerated value: `'AUPRC'`) — that diff is expected and must be listed in the pre-documented diff inventory.

## Code Examples

### pyproject.toml skeleton (REL-02 — discretion item, follow STACK.md)

```toml
# Source: structure per docs.astral.sh/uv (package=false, PEP 735 groups verified in
# .planning/research/STACK.md on 2026-10-08; flags verified against installed uv 0.12.23)
[project]
name = "dnallmmark"
version = "0.7.1"
description = "DNALLM-Mark — DNA language-model benchmark platform (offline data toolchain)"
requires-python = ">=3.13"
dependencies = []

[dependency-groups]
data = [
    "pandas>=2.2,<3.0",   # D-05 floor; latest 2.x = 2.3.3 (verified; pandas 3.0.6 excluded)
    "numpy>=2.0,<3",      # bounded alongside pandas per D-05
]
dev = []                   # Phase 2 adds pytest/ruff — keep Phase 1 minimal or add now per STACK.md
pipeline = [
    # GPU-only, NEVER installed in CI (REL-02). dnallm pinned from the local dev clone
    # in Phase 3 (PIPE-02) — deliberately not resolvable here.
    "torch>=2.0",
    "transformers>=4.0",
]

[tool.uv]
package = false            # virtual project: deps installed, repo not built/packaged
default-groups = ["data"]  # `uv sync` installs data chain only
```

Companion commands (all flags verified against the installed uv 0.12.23 binary):

```bash
~/.local/bin/uv venv .venv --python 3.13     # CPython 3.13.16 (uv-managed download, verified available)
~/.local/bin/uv sync                          # data group (default) → .venv + uv.lock
~/.local/bin/uv sync --group pipeline         # maintainer GPU env only — CI never runs this
~/.local/bin/uv export --group data --no-emit-project -o requirements.txt
```

Notes: `requires-python = ">=3.13"` is safe for 3.14 too — pandas 2.3.3 cp314 aarch64 wheels verified (closes STACK.md's "3.14 wheels unverified" gap). Committing `.python-version` containing `3.13` (removing `.gitignore:7`) pins contributor machines to D-07's interpreter.

### `.gitleaks.toml` (REL-05)

```toml
# Source: github.com/gitleaks/gitleaks README (config/allowlist syntax, `git` subcommand)
title = "DNALLM-Mark secret scan — allowlist the intentional Zenodo sharing link"

[extend]
useDefault = true

[[allowlists]]
description = "Intentional Zenodo record-19135551 preview link (maintainer decision 2026-10-08, D-08)"
condition = "AND"
paths = ['''README\.md''']
regexes = ['''zenodo\.org/records/19135551\?preview=1&token=''']
```

```bash
# Full history (detect subcommand deprecated since v8.19.0; `git` scans via git log -p)
gitleaks git -v --config .gitleaks.toml --report-path /tmp/gitleaks-report.json .
# "--log-opts=--all" additionally covers all refs if needed
```

**"Clean" evidence (REL-05 success):** command line + exit code 0 + empty/absent findings in the report, recorded in AUDIT.md, plus the allowlist entry itself in-repo for reviewer scrutiny. Any non-allowlisted finding = a NEW secret → stop and handle (D-08 covers only this one link).

### FIX-05 exact change sites (all quoted from source read this session)

```python
# script/summarize_comparison.py:309 — CURRENT (unsorted):
    for filename in os.listdir(input_dir):
# FIX:
    for filename in sorted(os.listdir(input_dir)):

# script/summarize_comparison.py:380-381 — CURRENT (no sort_keys):
    with open(output_total, "w", encoding='utf-8') as f:
        json.dump(total_comparison, f, indent=4, ensure_ascii=False)
# FIX: add sort_keys=True (same change at lines 407-408 for species_comparison)

# script/get_task_performance.py:100 — CURRENT (unsorted):
    for filename in os.listdir(input_dir):
# FIX: sorted(os.listdir(input_dir))

# script/get_task_performance.py:158-159 — CURRENT (no sort_keys):
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(ds_data, f, indent=4, ensure_ascii=False)
# FIX: add sort_keys=True
```

```javascript
// scripts/generate-tasks-index.js:18-20 — ALREADY SORTED (verified; no change needed):
  const files = fs.readdirSync(TASK_PERFORMANCE_DIR)
    .filter(file => file.endsWith('_task_performance.json'))
    .sort();

// scripts/generate-tasks-index.js:50 — the remaining nondeterminism (date stamp):
    generatedAt: new Date().toISOString().split('T')[0],
// FIX (planner decision): derive from inputs / CLI arg / drop — see Pitfall 6

// scripts/generate-tasks-index.js:56 — deterministic given fixed literal key order
// (JSON.stringify serializes string-keyed own properties in insertion order; the
// object literals at lines 48-53 and 35-45 are fixed) — verified empirically:
// two runs produced byte-identical tasks.json
```

**Why sorted iteration matters beyond key order:** `aggregate_models` sums floats in dataset order — `total_rank_score = sum(s['task_rank_score'] for s in model_m_stats)` and `sum_zscore`/`sum_minmax`/`sum_robust` at summarize_comparison.py:235-253 — and both dataset order and per-dataset model order derive from `os.listdir` (models inserted into `raw_dataset_scores` while iterating files). Unsorted iteration therefore makes not just layout but *numeric sums* machine/filesystem-dependent. `sorted()` pins summation order everywhere.

### Canonical value comparator (validated this session — commit as `baseline/compare.py`)

A ~60-line recursive walker: parse both files → compare dicts as key-sets → recurse → exact per-value compare, bucketing float diffs into `FLOAT_ULP` (rel < 1e-12) vs `FLOAT_BIG`. Full implementation exists at `/tmp/dnallm-regen/compare_json.py` (this session's validated artifact) — port verbatim, add `--tolerance` flag if desired.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `gitleaks detect` | `gitleaks git` (history scan) | v8.19.0 deprecates `detect` | Use `gitleaks git` for REL-05; `detect` still works but is deprecated |
| requirements.txt as only manifest | PEP 621 `pyproject.toml` + PEP 735 `[dependency-groups]` + lockfile | PEP 735 accepted 2024; pip 25.1+ / uv support installs per group | Groups are the standard mechanism for the data/dev/pipeline split REL-02 needs |
| pandas 2.x default dtype era | pandas 3.0 (2026-01-21): string dtype, copy-on-write, groupby changes | pandas 3.0.0 released 2026-01-21 | Why `>=2.2,<3.0` is locked (D-05); migration is post-release work |
| Tag-free "data update" commits | tagged, checksummed data versions (`data-v1`/`data-v2`) | — | AUDIT-02/DATA-03 convention; attribute every number change |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | MIT license text and copyright line ("Copyright (c) 2026 …" — holder name TBD) | REL-01 | Low — standard text; holder naming needs one user answer at execution |
| A2 | Data-terms statement content: repo redistributes only derived aggregates + metadata (raw datasets gitignored, downloaded from Zenodo) — derived metrics under a permissive statement, upstream data per original terms | REL-01 | Medium — if any raw dataset bytes are actually committed, the exposure grows; the audit agents should spot-verify `git ls-files` for data files |
| A3 | Zenodo token is record-scoped and read-only | User Constraints (D-08) | None for repo work — maintainer assertion, accepted per D-08; scan scope unchanged either way |
| A4 | P0/P1/P2 severity definitions and AUDIT.md structure as proposed | Audit patterns | Low — discretion item; planner may adjust |
| A5 | Audit agent partitioning (3 subsystem agents × shared dimensions) as proposed | Audit patterns | Low — discretion item |
| A6 | Original generation environment ran a numpy whose mean/std float behavior differs from 2.5.3 (the ULP-diff explanation); its exact versions are unknowable | Pitfall 4 | Low — D-05 already accepts the original env is gone; the empirical diff inventory stands on its own evidence |
| A7 | gitleaks allowlist `condition = "AND"` behaves on global allowlists as on per-rule allowlists | REL-05 config | Low — verify on first scan run; tune regex if the token fires through (Pitfall 8) |
| A8 | `pipeline` group contents (torch, transformers; dnallm deferred to Phase 3) keep `uv lock` resolvable | pyproject skeleton | Low — if torch resolution stalls locking, move pipeline group to a documented `requirements-pipeline.txt` instead; CI boundary unchanged |

## Open Questions

1. **`generatedAt` handling in tasks.json (FIX-05 scope decision)**
   - What we know: it is the only cross-day nondeterminism left; Phase 5's TEST-07 drift job regenerates + `git diff --exit-code` — impossible with a live date stamp.
   - Recommendation: make it derived-from-inputs or CLI-injectable now (part of FIX-05), not later.
2. **Data-terms license choice for derived data (CC-BY-4.0 vs "MIT for everything we produce")**
   - What we know: D-10 locks MIT for code and requires a separate data statement; wording/choice of the data license is open.
   - Recommendation: CC-BY-4.0 for derived aggregates (community standard for datasets), stated in README + LICENSE-adjacent DATA notice; confirm with user at execution (A2/A1).
3. **Commit `.python-version` or rely on `requires-python`?**
   - What we know: `.gitignore:7` currently ignores it; uv convention is to commit it for contributor pinning.
   - Recommendation: commit it (`3.13`) and drop the ignore line — one less way environments drift.
4. **Does the `metric` casing mismatch (`auprc` vs `AUPRC`) break the BEND task page render?**
   - What we know: `tasks.json` (committed) says lowercase; regenerated output says uppercase; frontend consumers unverified this session.
   - Recommendation: assign to the frontend audit agent as a seed finding with a browser check; regeneration under FIX-05 reconciles the data side either way.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | REL-02 (venv/lock/export) | ✓ | 0.12.23 (`~/.local/bin/uv`, aarch64) | — |
| CPython 3.13 | D-07 data chain | ✓ (uv-managed download verified) | 3.13.16 | system 3.12.3 / 3.14.7 exist but D-07 mandates 3.13 |
| pandas 2.x cp313 aarch64 wheel | REL-02 | ✓ (verified on PyPI) | 2.3.3 | cp314 wheels also verified |
| numpy 2.x cp313 aarch64 wheel | REL-02 | ✓ (verified + installed) | 2.5.3 | — |
| Node.js | generate-tasks-index.js | ✓ | v26.10.0 | — |
| gitleaks | REL-05 scan | ✗ (not installed) | — | `brew install gitleaks` (brew 7.0.8 bottles exactly 8.30.1 — verified) or GitHub Releases `gitleaks_8.30.1_linux_arm64.tar.gz` |
| brew | gitleaks install | ✓ | 7.0.8 (linuxbrew aarch64) | direct tarball download |
| git + GitHub remote | tag push, history scan | ✓ | — | remote: github.com/zhangtaolab/dnallmmark (private per D-09) |
| jq / make | audit conveniences | ✓ | 1.7 / 4.3 | — |
| Network to PyPI | dependency install | ✓ (registry queries succeeded this session) | — | offline impossible for first sync; uv caches thereafter |

**Missing dependencies with no fallback:** none — gitleaks has a verified two-path install.
**Missing dependencies with fallback:** none.

**Empirical artifacts from this session (reusable by the phase):** scratch checkout with validated venv at `/tmp/dnallm-regen` (chain runnable in seconds; full outputs from two runs + comparator + results). The phase may recreate it from the documented procedure rather than reuse `/tmp` state.

## Security Domain

`security_enforcement: true`, ASVS level 1 (config). This phase adds no application attack surface (no backend, no auth — static MPA constraint); its security content is release hygiene.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No backend/auth exists (static-site hard constraint) |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | Static files only |
| V5 Input Validation | no (this phase) | JSON consumers unchanged; submission-flow input handling is FIX-03/FIX-04 (Phase 4) |
| V6 Cryptography | no | No crypto in scope |
| V14 Config / secrets (L1-relevant) | **yes** | REL-05: gitleaks full-history scan with narrow AND-conditioned allowlist; intentional token documented in-repo (AUDIT.md) so reviewers see it is deliberate |
| Supply chain (L1-adjacent) | **yes** | REL-02: floor-bounded deps + committed uv.lock (integrity hashes via lockfile); pipeline group isolated from CI install set |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Future secrets committed (post-release contributor flow) | Information Disclosure | Commit `.gitleaks.toml` + document scan command in AUDIT.md (Phase 5 may wire it into CI); allowlist is narrow enough that new tokens still fire |
| Unpinned dependency swap changes leaderboard numbers silently | Tampering | Floor bounds (D-05) + committed lockfile + baseline diff discipline (this phase's core deliverable) |
| CDN script tampering (Chart.js/SheetJS, no SRI) | Tampering | Out of scope by REQUIREMENTS "Out of Scope" table (deep hardening descoped); AUDIT.md records it (already in CONCERNS) |
| Stored XSS via submission JSON | Tampering/Elevation | Phase 4 (FIX-04) — audit records; no submission flow live this phase (submit.html absent) |

## Sources

### Primary (HIGH confidence)
- Direct code reads this session (all line-anchored quotes): `script/summarize_comparison.py` (lines 100-161, 164-184, 187-267, 270-312, 332-414), `script/get_task_performance.py` (lines 1-168), `scripts/generate-tasks-index.js` (lines 1-69), `README.md` (lines 1-6, 100-139), `.gitignore`, `pipeline/dnallmmark_pipeline.py` (imports)
- Empirical run this session: full 3-script chain on CPython 3.13.16 + pandas 2.3.3 + numpy 2.5.3 (aarch64 GB10 machine); two runs byte-identical; canonical value-compare vs committed JSONs (diff inventory in Pitfalls 4/5/9); reverse-order copy experiment; readdir-order probe across 3 directories
- PyPI JSON API: `pypi.org/pypi/pandas/{json,2.3.3/json}` (latest 2.x = 2.3.3; requires_python; numpy dep matrix; cp313/cp314 aarch64 wheel filenames), `pypi.org/pypi/numpy/{json,2.5.3/json}` (requires >=3.12; cp313 aarch64 wheels)
- Installed-binary verification: `uv sync --help`, `uv export --help`, `uv venv --help` on uv 0.12.23 (group/export/python flags); `uv python list` (cpython-3.13.16 aarch64 available)
- GitHub Releases API: gitleaks v8.30.1 + `gitleaks_8.30.1_linux_arm64.tar.gz` asset; `brew info gitleaks` (bottled 8.30.1)
- Local environment probes: node v26.10.0, jq 1.7, make 4.3, brew 7.0.8, git tags empty, remote URL
- Project research (verified 2026-10-08, same-day): `.planning/research/STACK.md` (uv/PEP 735 docs verification, pandas 3.0 hazard, action SHAs), `.planning/research/PITFALLS.md` (P1/P2/P6/P7 practices), `.planning/codebase/CONCERNS.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/INTEGRATIONS.md`

### Secondary (MEDIUM confidence)
- github.com/gitleaks/gitleaks README (fetched this session): allowlist syntax, `condition`, `git` subcommand, `.gitleaksignore`, `#gitleaks:allow` — syntax verified against docs; exact AND-semantics on *global* allowlists to confirm on first run (A7)

### Tertiary (LOW confidence)
- None load-bearing. (Zenodo token scope is a maintainer assertion per D-08, tagged A3.)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every version verified against PyPI registry JSON or local binary this session; core path empirically executed end-to-end
- Architecture/patterns: HIGH — audit mechanics derive from D-01..D-04 plus validated reproduction procedures; comparator and scratch procedure are proven, not proposed
- Pitfalls: HIGH — pitfalls 3-7 and 9 are empirical observations from this session's runs, not literature
- License/data-terms specifics: MEDIUM — MIT text standard; data-terms wording and holder name need one execution-time confirmation (A1/A2)

**Research date:** 2026-10-08
**Valid until:** 2026-11-07 (30 days — pandas/numpy/gitleaks are slow-moving at these pins; re-verify if pandas 3.0.x behavior questions arise)
