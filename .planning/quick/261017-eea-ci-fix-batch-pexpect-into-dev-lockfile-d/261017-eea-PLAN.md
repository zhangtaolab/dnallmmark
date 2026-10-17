---
phase: quick-261017-eea
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - pyproject.toml
  - uv.lock
  - requirements.txt
  - scripts/demo/record_tui_demo.py
  - dnallm-mark/data/model_performance/helixgen-2stage_performance.json
  - dnallm-mark/data/model_performance/helixgen-2stage-w015625_performance.json
  - dnallm-mark/data/model_performance/helixgen-mlm_performance.json
  - dnallm-mark/data/models_comparison_multi-species.json
  - dnallm-mark/data/models_comparison.json
  - dnallm-mark/data/models_comparison_animal.json
  - dnallm-mark/data/models_comparison_plant.json
  - dnallm-mark/data/models_comparison_microbe.json
  - dnallm-mark/data/permutation_tests.json
  - tests/test_schemas.py
  - tests/test_determinism.py
  - .planning/quick/261017-eea-ci-fix-batch-pexpect-into-dev-lockfile-d/261017-eea-SUMMARY.md
autonomous: true
requirements: [EEA-1, EEA-2, EEA-3, EEA-4, EEA-5, EEA-6]

user_setup: []

estimate:
  tokens: 45000
  raw_tokens: 90000
  tasks: 4
  confidence: high

must_haves:
  truths:
    - "EEA-1 (pexpect joins the dev group — CI lint+typecheck lane root cause): scripts/demo/record_tui_demo.py imports pexpect lazily at exactly two sites (spawn path, lines ~1102 and ~1120); pexpect is in NO dependency group, so CI's clean lock-built env fails ty with unresolved-import x2 while the local venv passes environmentally. Fix: pexpect>=4.9 joins [dependency-groups] dev (version 4.9.0 is the exact version the script docstring already cites and PyPI's current latest; legitimacy verified at planning time per the 08-02 delegation pattern — PyPI project pexpect, authors Noah Spurrier / Thomas Kluyver / Jeff Quast, source github.com/pexpect/pexpect, ISC license, sole dep ptyprocess>=0.5; verdict lines go in the SUMMARY). uv lock re-resolves and the uv.lock diff adds ONLY the pexpect + ptyprocess blocks — the D-05 anchors (pandas 2.3.3, numpy 2.5.3) and every other pin survive byte-unchanged (verified by grepping the uv.lock diff for any touched version lines outside the two new blocks — ANY other movement halts the task and reports). requirements.txt is re-exported with uv export --group data --no-emit-project -o requirements.txt and must come out byte-identical (the data group is untouched); a non-empty diff there halts the task. The script docstring's --with pexpect==4.9.0 overlay instructions (lines ~30-33) are updated to the dev-group reality. NO ty ignore / replace-import masking — the real dependency is declared (repo discipline: real types, never any). Proof of CI parity: uv run --isolated --group dev --group tui ty check (isolated env built from the lock — reproduces CI's clean state) fails with the two unresolved-imports BEFORE the pyproject edit and passes AFTER."
    - "EEA-2 (helixgen info.path stripped): the three helixgen performance files carry info.path with maintainer server paths (/root/autodl-tmp/labshare/zt/scratch/... — an info disclosure into the public data tree) and schemas/model_performance.json sets info additionalProperties false with a closed 11-key property list that excludes path — hence test_schemas failures path29/path30/path31. Repo-wide consumer check at planning time found ZERO consumers of info.path (the only 'path' key producer is script/run_migration_inventory.py's own output key, unrelated). Decision per the task brief's planning-time mandate: STRIP the field (do NOT extend the schema) — no consumer exists and the leaked paths are the reason the field is forbidden. After the strip the three files validate against the model_performance schema."
    - "EEA-3 (helixgen dataset.species rewritten to the canonical per-dataset arena): all 47 dataset entries in each of the three helixgen files carry dataset.species 'multi-species' — the AUD-01 defect signature (species copied from the MODEL row; the helixgen models are multi-species models) — violating the dataset.species enum [Animals, Plants, Microbe] (hence the test_dataset_enums failure). The canonical corpus is internally unanimous: across the 42 non-helixgen files there are ZERO per-dataset species disagreements over all 47 datasets (planning-time verified; e.g. the same 47 tasks carry Animals 22 / Plants 12 / Microbe 13 in DNABERT-2-117M_performance.json). Fix: rewrite each helixgen dataset.species to that dataset's canonical value, sourced by building the {task: species} map from the canonical corpus and asserting unanimity at edit time. Card-level info.species stays OPEN in the schema (plain string) — the helixgen cards' 'multi-species' value is schema-fine and stays. The rewrite also stops the js datasets page (js/datasets.js reads data.dataset.species) from rendering 'multi-species' rows. Edits are byte-surgical: the files are json.dumps form indent=4, ensure_ascii=False, NO sort_keys, NO trailing newline — the executor proves the round-trip on an unmodified file first (load+dump == original bytes), then applies edits with the identical recipe, so the git diff shows ONLY the intended key changes."
    - "EEA-4 (data chain re-synced; multi-species file removed with recorded justification): planning-time provenance of dnallm-mark/data/models_comparison_multi-species.json — it is the ALL-view (all 45 models x all 47 datasets; per-model task participation identical to the all view, samples 47) regenerated on the AutoDL training server with include_weighted=False, NOT a species-grouped subset; it carries the stale pre-D-18 alias plant-dnamamba2-BPE (renamed PlantDNAMamba2-BPE in dfb9a80) and ULP-level float differences from a foreign numpy — it is byte-non-reproducible on this machine in principle. It has NO consumer anywhere: js/data.js arenaMap and CONFIG.ARENAS are exactly all/animal/plant/microbe, the models_comparison schema $comment scopes itself to ALL FOUR committed files and its test enumeration lists four, the bucket pin says 4, and no test or script references the filename. Decision (the brief's fold-in instruction was conditioned on reverse-engineering grouping rules from the file content + js consumer cross-check — both checks came back negative: no grouping exists, no consumer exists, and a script-emitted twin would be a schema-divergent duplicate of models_comparison.json minus weighted_score): DELETE the file and integrate helixgen the canonical way — regenerate the four arena files. Execution: git rm the file; bump tests/test_schemas.py EXPECTED_BUCKET_SIZES model_performance 42 -> 45 (the pin's own comment sanctions deliberate corpus-growth updates) and the stale '42 real committed model_performance inputs' count in the tests/test_determinism.py docstring to 45; run make data; commit the regenerated models_comparison{,_animal,_plant,_microbe}.json (42 -> 45 models each, helixgen entries now present, PlantDNAMamba2-BPE alias correct) + permutation_tests.json (n_models 42 -> 45, family_size 861 -> 990, shifted p_adj values — planning-time regenerated preview confirms exactly this shape, no independent permutation cause: it shares load_model_inputs with summarize). manifest.json, provenance.*, tasks.json do NOT move (constants / registry-driven / task_performance-driven). After the commit, make data runs a SECOND time and git diff --exit-code -- dnallm-mark/data/ is empty — the CI drift lane's exact check, plus two-run idempotence."
    - "EEA-5 (new test baseline pinned; every gate green): pytest tests/test_schemas.py tests/test_determinism.py fully green (path29-31 + dataset_enums + bucket_counts + determinism all collapse — they are the drift's manifestations, reproducing the local 6 failures exactly as diagnosed). Full make test enumerates the NEW baseline membership empirically and the SUMMARY pins the exact list — expected residue: the root-user chmod persist-failure sims and test_services_run_config (machine-local), but the executor reports what actually fails, not what was predicted. Zero NEW failures vs the 7F baseline minus the six this batch collapses. make lint green; make typecheck green; uv run --isolated --group dev --group tui ty check green (CI parity); node --test tests/js/*.test.js green at its established count (26). Goldens untouched: git status --porcelain over tests/fixtures/golden/ and tests/tui/__snapshots__/ is empty at the end."
    - "EEA-6 (process discipline and boundaries): commits are PLAIN — zero attribution trailers ever; the executor does NOT push (the orchestrator pushes, which retriggers PR #7's four lanes). Any regenerated or hand-edited public number is documented before/after in the SUMMARY (models-per-file 42 -> 45, helixgen rank positions in the four views, permutation n_models/family_size/p_adj deltas, the three before values of info.path, the 3x47 dataset.species value distribution) — the every-number-reproducible mandate. The SUMMARY notes WINDOWS #22's schema/determinism half is closed by this batch (its chmod-sim half remains open — ledger status is the orchestrator's call). tui/ is untouched (dnr's turf); the DNALLM sibling repo is untouched; no new committed scripts (the helixgen edit runs as a throwaway python -I one-liner, never a repo file)."
  artifacts:
    - pyproject.toml
    - uv.lock
    - scripts/demo/record_tui_demo.py
    - dnallm-mark/data/model_performance/helixgen-2stage_performance.json
    - dnallm-mark/data/model_performance/helixgen-2stage-w015625_performance.json
    - dnallm-mark/data/model_performance/helixgen-mlm_performance.json
    - dnallm-mark/data/models_comparison.json
    - dnallm-mark/data/models_comparison_animal.json
    - dnallm-mark/data/models_comparison_plant.json
    - dnallm-mark/data/models_comparison_microbe.json
    - dnallm-mark/data/permutation_tests.json
    - tests/test_schemas.py
    - tests/test_determinism.py
    - .planning/quick/261017-eea-ci-fix-batch-pexpect-into-dev-lockfile-d/261017-eea-SUMMARY.md
  key_links:
    - "scripts/demo/record_tui_demo.py pexpect imports <-> [dependency-groups] dev in pyproject.toml <-> uv.lock pexpect+ptyprocess blocks <-> CI lint-typecheck lane (make typecheck installs from the lock via uv run --group dev --group tui)"
    - "dnallm-mark/data/model_performance/ (45 files) -> script/summarize_comparison.py -> models_comparison{,_animal,_plant,_microbe}.json + script/permutation_tests.py -> permutation_tests.json <-> tests/test_determinism.py byte pins <-> CI drift lane (make data + git diff --exit-code -- dnallm-mark/data/)"
    - "helixgen dataset.species values <-> schemas/model_performance.json dataset.species enum <-> tests/test_schemas.py test_dataset_enums + EXPECTED_BUCKET_SIZES pin"
    - "helixgen info.path <-> schemas/model_performance.json info additionalProperties=false <-> tests/test_schemas.py path29-31"
---

<objective>
Close the four red PR #7 CI lanes at their root causes: (1) pexpect missing from the lock behind the lint+typecheck lane's ty unresolved-import; (2) the data-chain drift behind the drift lane's git diff --exit-code (models_comparison family + permutation_tests.json) plus the non-regenerable models_comparison_multi-species.json stray from 9e803ca; (3) the three helixgen performance files' schema violations behind the test lanes' path29-31 + dataset_enums failures; (4) the stale test pin (bucket count 42 vs the 45-model corpus). Everything lands as the corrected, re-synchronized committed state of record with a freshly pinned local baseline.

Purpose: the standing mandate — every number on the public leaderboard is correct and reproducible from code external reviewers can trust. 9e803ca broke the reproducibility chain (data committed that no code path regenerates byte-identically); this batch restores it and documents every moved number before/after.

Output: pexpect in the dev group with a discipline-checked lock; three schema-valid helixgen performance files; a re-synced derived-data tree whose regeneration is a byte-identical no-op; green test_schemas/test_determinism; a SUMMARY with the before/after ledger and the new baseline membership.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md

Planning-time investigation findings (verified on this machine, 2026-10-17 — the executor does NOT need to re-derive these, only to act on them):

- CI failure anatomy (PR #7 run 38992319016, four lanes): lint+typecheck = ty unresolved-import pexpect x2; drift = models_comparison{,_animal,_microbe,_plant}.json + permutation_tests.json drift after make data, plus the committed models_comparison_multi-species.json that make data never produces; test 3.13/3.14 = test_determinism (file-set 4 vs committed 5, plus byte drift of the four) and test_schemas path29-31.
- Local reproduction of the test-lane failures: pytest tests/test_schemas.py tests/test_determinism.py -> exactly 6 failed (path29, path30, path31, test_schema_bucket_counts_are_pinned, test_dataset_enums_match_committed_data_across_all_schemas, test_chain_is_deterministic_and_matches_committed), 100 passed. The 7F baseline = these 6 + test_services_run_config (machine-local).
- 9e803ca (2026-10-14) added ONLY: three helixgen performance files + models_comparison_multi-species.json. The four arena files were last regenerated at dfb9a80 (D-18 alias normalization), pre-helixgen — that is the whole drift story; permutation_tests.py shares load_model_inputs with summarize_comparison.py, so its drift has no independent cause (regenerated-preview confirmed: n_models 42->45, family_size 861->990).
- models_comparison_multi-species.json forensic: 45 models (the 42 + 3 helixgen), all 47 datasets, per-model participation identical to the all view; NO weighted_score (aggregate_models include_weighted=False shape); carries pre-D-18 alias plant-dnamamba2-BPE; sum_zscore last-digit float deltas vs local regeneration (foreign-machine numpy — generated on the AutoDL box the helixgen info.path values leak). Zero js/test/script references to the filename; js/data.js arenaMap and CONFIG.ARENAS are exactly all/animal/plant/microbe; schemas/models_comparison.json $comment scopes itself to ALL FOUR files and requires weighted_score; tests/test_schemas.py enumerates exactly four comparison files and pins the bucket at 4.
- helixgen files: info.path present in all three (server paths /root/autodl-tmp/labshare/zt/scratch/... — the disclosure the closed schema forbids; zero consumers repo-wide); dataset.species == 'multi-species' on all 47 entries in each file (AUD-01 species-from-model-row defect signature); the 42 canonical files agree per-dataset with zero disagreements across all 47 datasets. File JSON recipe: indent=4, ensure_ascii=False, no sort_keys, no trailing newline. Card info.species is an open string in the schema — 'multi-species' cards are valid and stay.
- Dependency facts: make typecheck = uv run --group dev --group tui ty check (CI installs from the lock; local passes only because pexpect lives environmentally in the venv — CI-parity proof is uv run --isolated --group dev --group tui ty check). requirements.txt is exactly uv export --group data --no-emit-project (data group only — a dev-group addition must leave it byte-identical). uv lock adds pexpect + ptyprocess (pexpect's sole dependency). pexpect legitimacy per the 08-02 maintainer delegation: PyPI pexpect, Noah Spurrier / Thomas Kluyver / Jeff Quast, github.com/pexpect/pexpect, ISC; 4.9.0 is both PyPI latest and the version already cited in scripts/demo/record_tui_demo.py's docstring.
- WINDOWS #22 (.planning/WINDOWS.md): '5 schema/determinism pins stale after data commit 9e803ca' — this batch closes that half; its 5 root-user chmod sims are out of scope and keep it open (ledger status is the orchestrator's call; the SUMMARY must carry the note).
</context>

<tasks>

<task type="auto">
  <name>Task 1: pexpect into the dev group — lock, export, docstring, CI-parity ty proof</name>
  <files>pyproject.toml, uv.lock, requirements.txt, scripts/demo/record_tui_demo.py</files>
  <precondition>The working tree is clean over pyproject.toml, uv.lock, and requirements.txt (the three lock-discipline files start unmodified).</precondition>
  <action>
First reproduce CI's failure locally: run uv run --isolated --group dev --group tui ty check and record the two unresolved-import pexpect diagnostics (lines ~1102 and ~1120 of scripts/demo/record_tui_demo.py — the lazy spawn-path imports; laziness does not help ty, which resolves statically). Then fix: add pexpect to the dev group in pyproject.toml with a comment in the group's established style (dated 2026-10-17, purpose: the demo scene driver's spawn path imports it lazily and ty resolves imports statically, so CI's lock-built env needs it as a real group member; floor pexpect>=4.9 — 4.9.0 is PyPI latest and the version the script docstring cites; legitimacy verdict pointer: PyPI-verified per the 08-02 delegation, lines in this batch's SUMMARY). Run uv lock. Inspect git diff -- uv.lock: the change must be confined to the new pexpect and ptyprocess blocks; if the diff touches the pandas or numpy version lines or any other existing pin, STOP — do not commit, report the movement. Re-export with uv export --group data --no-emit-project -o requirements.txt; git diff -- requirements.txt must be empty (the data group is untouched) — a non-empty diff halts the task the same way. Update the docstring lines of scripts/demo/record_tui_demo.py (~30-33) that instruct the uv run --group dev --with pexpect==4.9.0 overlay to state the dev-group reality (plain uv run --group dev now resolves pexpect; keep the lazy-import note and the --dry-run / --list-scenes no-pexpect guarantee intact). Do NOT add any ty ignore or replace-import masking — the fix is the real dependency. Finally re-run uv run --isolated --group dev --group tui ty check (must pass) and make typecheck (local lane, must stay green).
  </action>
  <verify>
    <automated>git diff --stat -- uv.lock && git diff --exit-code -- requirements.txt && uv run --isolated --group dev --group tui ty check && make typecheck</automated>
  </verify>
  <done>pexpect>=4.9 declared in the dev group; uv.lock diff adds exactly the pexpect + ptyprocess blocks with every pre-existing pin (pandas 2.3.3, numpy 2.5.3 anchors included) untouched; requirements.txt re-export byte-identical; the demo docstring overlay instructions updated; the isolated (CI-parity) ty check passes along with make typecheck; committed plain.</done>
</task>

<task type="auto">
  <name>Task 2: helixgen performance files — strip info.path, rewrite dataset.species to the canonical arena</name>
  <files>dnallm-mark/data/model_performance/helixgen-2stage_performance.json, dnallm-mark/data/model_performance/helixgen-2stage-w015625_performance.json, dnallm-mark/data/model_performance/helixgen-mlm_performance.json</files>
  <action>
Surgical data edit on the three helixgen files, no new repo files (throwaway python -I one-liner, never committed). Step 0 — prove the byte recipe: for each file, json.loads followed by json.dumps with indent=4, ensure_ascii=False (NO sort_keys, NO trailing newline) must reproduce the original bytes exactly; any mismatch halts the task. Step 1 — build the canonical species map: load every non-helixgen file in dnallm-mark/data/model_performance/, collect {task_name: dataset.species}, and assert zero disagreements (planning-time verified: unanimous across the 42 files over all 47 datasets); abort loudly if any task disagrees. Step 2 — per helixgen file: delete info.path (leaks the maintainer's AutoDL server paths; zero consumers repo-wide; schemas/model_performance.json info is additionalProperties false with a closed 11-key list excluding path) and rewrite every performance[task].dataset.species from 'multi-species' to that task's canonical map value (the AUD-01 defect signature fix; the enum is [Animals, Plants, Microbe]). Leave everything else untouched — the card's info.species 'multi-species' stays (info.species is an open string in the schema), as do all metrics, parameters, and key order. Write back with the proven Step-0 recipe so the git diff shows only the intended key changes. Record for the SUMMARY: the three before info.path values verbatim, and the resulting per-file dataset.species distribution (expect the canonical 22/12/13 shape over the same 47 tasks).
  </action>
  <verify>
    <automated>.venv/bin/python -m pytest tests/test_schemas.py -q -k "path29 or path30 or path31 or dataset_enums" && .venv/bin/python -I -c "import json,glob,collections; sm={}; [sm.setdefault(t,set()).add(e['dataset'].get('species')) for f in glob.glob('dnallm-mark/data/model_performance/*_performance.json') for t,e in json.load(open(f))['performance'].items()]; assert all(len(v)==1 and v!={'multi-species'} for v in sm.values()), 'disagreement or multi-species residue'; print('corpus unanimous:', len(sm), 'datasets')"</automated>
  </verify>
  <done>The three files contain no info.path key and no dataset.species outside [Animals, Plants, Microbe]; schema tests path29/path30/path31 and dataset_enums pass; the 45-file corpus is unanimous per-dataset (no multi-species residue anywhere); the diff is confined to the intended keys; committed plain with the before/after recorded for the SUMMARY.</done>
</task>

<task type="auto">
  <name>Task 3: data-chain re-sync — remove the multi-species stray, bump the stale pin, regenerate, commit</name>
  <files>dnallm-mark/data/models_comparison_multi-species.json, tests/test_schemas.py, tests/test_determinism.py, dnallm-mark/data/models_comparison.json, dnallm-mark/data/models_comparison_animal.json, dnallm-mark/data/models_comparison_plant.json, dnallm-mark/data/models_comparison_microbe.json, dnallm-mark/data/permutation_tests.json</files>
  <precondition>Task 2 is committed (the regenerated comparison files must be built from schema-valid inputs).</precondition>
  <action>
First capture the before state for the SUMMARY ledger: per comparison file, the model count (42) and the top-6 rank_score order; permutation_tests.json info n_models (42) and family_size (861). Then: git rm dnallm-mark/data/models_comparison_multi-species.json — the planning-time forensic (all-view content, no weighted_score, stale pre-D-18 alias plant-dnamamba2-BPE, foreign-machine floats, zero js/test/script consumers, schema scoped to four files) is the recorded justification; the file stays recoverable at 9e803ca and the SUMMARY documents its semantics so nothing is lost knowledge-wise. In tests/test_schemas.py, bump EXPECTED_BUCKET_SIZES model_performance from 42 to 45 (the pin's comment sanctions deliberate corpus-growth updates). In tests/test_determinism.py, update the stale docstring count of real committed model_performance inputs from 42 to 45 (prose only — no assertion changes). Run make data (the Makefile handles the CWD-sensitive script chain: summarize from dnallm-mark/data/, permutation + provenance + the node index from the repo root). Review the regenerated diff: the four comparison files each grow the three helixgen models (42 -> 45; helixgen rank positions recorded for the SUMMARY — planning-time regeneration preview: helixgen-2stage-w015625 lands around rank 24, helixgen-2stage around 26, helixgen-mlm near the bottom at 40 of the all view) and permutation_tests.json moves to n_models 45 / family_size 990 with shifted p_adj values; manifest.json, provenance.*, tasks.json, and the model_performance inputs must show NO changes — any other file moving is a stop-and-report. Commit the removal, the pin/docstring edits, and the regenerated artifacts together (the tree is only self-consistent as one commit). Then prove the drift gate: run make data a second time and confirm git diff --exit-code -- dnallm-mark/data/ passes — the CI drift lane's exact check, now a byte-identical no-op, and the two-run idempotence proof.
  </action>
  <verify>
    <automated>make data && git diff --exit-code -- dnallm-mark/data/ && .venv/bin/python -m pytest tests/test_schemas.py tests/test_determinism.py -q</automated>
  </verify>
  <done>models_comparison_multi-species.json no longer exists and every remaining data file regenerates byte-identically (make data is a no-op against the committed tree, proven across two consecutive runs); the four comparison files carry 45 models including helixgen with the correct PlantDNAMamba2-BPE alias; permutation_tests.json at n_models 45 / family_size 990; the bucket pin reads 45 and the determinism docstring reads 45; pytest tests/test_schemas.py tests/test_determinism.py fully green (all six drift failures collapsed); before/after numbers recorded for the SUMMARY; committed plain.</done>
</task>

<task type="auto">
  <name>Task 4: full-suite baseline reset, gates, SUMMARY ledger</name>
  <files>.planning/quick/261017-eea-ci-fix-batch-pexpect-into-dev-lockfile-d/261017-eea-SUMMARY.md</files>
  <action>
Run the complete gate set and pin the new baseline. make test (full pytest including the slow lane plus the node lane) — enumerate EVERY remaining failure by exact test id and pin that membership list in the SUMMARY as the new baseline for all subsequent quick tasks; expected residue is the root-user chmod persist-failure sims and test_services_run_config (machine-local), but the list is empirical — report what fails, not what was predicted, and if anything beyond the predicted residue fails, investigate before writing it off (a new failure introduced by this batch is a defect to fix, not a baseline entry). make lint and make typecheck green; uv run --isolated --group dev --group tui ty check green (the CI-parity proof from Task 1, re-run at the end state). node --test tests/js/*.test.js green at its established count. Verify the untouched guarantees: git status --porcelain over tests/fixtures/golden/ and tests/tui/__snapshots__/ is empty (goldens untouched), tui/ has zero modifications, no changes exist under the DNALLM sibling path. Write the SUMMARY with: the four-lane root-cause table (pexpect lock gap; 9e803ca drift; multi-species forensic and the deletion decision with its evidence; helixgen schema surgery), the pexpect legitimacy verdict lines (PyPI, authors, source repo, license, 4.9.0), the full before/after number ledger from Tasks 2-3 (three info.path values, dataset.species distributions, per-file model counts 42 -> 45, helixgen rank positions, permutation n_models/family_size/p_adj movement, top-6 order stability note — the 42 shared models' relative order DOES legitimately shift where helixgen ranks above them, task_rank_score is N minus rank so every insertion moves neighbors), the new baseline membership list, and the WINDOWS #22 note (the 5 schema/determinism pins half is closed by this batch; the chmod-sims half remains — ledger action is the orchestrator's). Do NOT push and do NOT add attribution trailers on any commit.
  </action>
  <verify>
    <automated>make lint && make typecheck && uv run --isolated --group dev --group tui ty check && node --test tests/js/*.test.js && make test ; echo "---- untouched guarantees ----" ; test -z "$(git status --porcelain tests/fixtures/golden/ tests/tui/__snapshots__/ tui/)" && echo goldens-and-tui-untouched</automated>
  </verify>
  <done>All four PR #7 lane equivalents pass locally (lint+typecheck incl. isolated CI-parity, full test suite at the pinned new baseline with zero new failures, node lane green, make data drift gate green from Task 3); the SUMMARY exists with the root-cause table, legitimacy verdict, complete before/after ledger, new baseline membership, and the WINDOWS #22 note; no push; every commit plain.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| committed data tree -> public site | dnallm-mark/data/ is published as-is; any field in it reaches external reviewers |
| lockfile -> CI env | uv.lock is the sole source CI installs; an unreviewed re-resolution silently changes what CI tests against |
| PyPI -> repo | new dependency pins pull third-party code into every dev/CI environment |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-eea-01 | Information Disclosure | helixgen performance files info.path | medium | mitigate | Task 2 strips the field: the values leak the maintainer's server layout (/root/autodl-tmp/labshare/zt/scratch/... — provider, username, share structure) into the public data tree, which is precisely what the closed 11-key info schema exists to prevent; zero consumers verified at planning time, so removal is lossless |
| T-eea-02 | Tampering | uv.lock re-resolution | high | mitigate | Task 1 confines the lock diff to the pexpect + ptyprocess blocks and halts on ANY other pin movement (D-05 anchors pandas 2.3.3 / numpy 2.5.3 byte-unchanged); requirements.txt re-export must stay byte-identical, proving the data group CI installs is untouched |
| T-eea-03 | Tampering | regenerated public numbers | high | mitigate | Task 3 commits only make data output regenerated from the committed inputs, gates it with the two-run git diff --exit-code idempotence check (the CI drift lane's own gate), and records every moved number before/after in the SUMMARY per the every-number-reproducible mandate |
| T-eea-SC | Tampering | pexpect/ptyprocess PyPI install | high | mitigate | Package legitimacy per the 08-02 maintainer delegation: PyPI-verified at planning time (project pexpect, authors Noah Spurrier / Thomas Kluyver / Jeff Quast, source github.com/pexpect/pexpect, ISC license; 4.9.0 is both PyPI latest and the version the repo's own docstring cites); verdict lines recorded in the SUMMARY; the lock pins the exact versions so CI never resolves freely |
</threat_model>

<verification>
- Task-level: each task's automated block above (isolated-env ty check; targeted schema tests + corpus unanimity probe; drift gate + schema/determinism suites; full lint/typecheck/test/node gates).
- Lane-equivalence: the four local checks map one-to-one onto PR #7's four lanes — lint-typecheck (make lint, make typecheck plus the isolated CI-parity run), test 3.13/3.14 (make test), drift (make data + git diff --exit-code -- dnallm-mark/data/), and the node/static lane (node --test). Remote green on PR #7 is the orchestrator's post-push verification, out of this plan's scope.
- Untouched-scope proofs: goldens, snapshots, and t/ verified unmodified; DNALLM sibling untouched.
</verification>

<success_criteria>
- The six drift-manifestation failures (path29-31, dataset_enums, bucket_counts, determinism) are green; the full suite runs at an empirically enumerated, SUMMARY-pinned new baseline with zero new failures.
- make data is a byte-identical no-op against the committed tree, proven over two consecutive runs.
- uv.lock gained exactly pexpect + ptyprocess; requirements.txt and every other pin byte-unchanged.
- The multi-species stray is gone with its forensic recorded; every moved public number has a before/after row in the SUMMARY.
- Commits plain, nothing pushed, tui/ and the DNALLM sibling untouched.
</success_criteria>

<output>
Create .planning/quick/261017-eea-ci-fix-batch-pexpect-into-dev-lockfile-d/261017-eea-SUMMARY.md when done
</output>
