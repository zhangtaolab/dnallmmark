# 04-CATEGORY-REVIEW — Maintainer Category Review (CONTEXT species-Q2 evidence)

**Plan:** 04-01 (Task 1, STEP 0 blocking-human gate)
**Gate:** `blocking-human` — maintainer personal confirmation of all 50 `pipeline/datasets_info.json` `Category` rows BEFORE any regeneration ran
**Review list generated:** 2026-10-10, read live from `pipeline/datasets_info.json` (50 rows: name + Category), cross-referenced against the committed per-dataset `species` values in `dnallm-mark/data/model_performance/*.json`

## Disposition

**Maintainer response (recorded verbatim):** `approved`

Date: 2026-10-10. The maintainer approved all 50 Category rows as listed AND the Multiple→Animals majority mapping. No row corrections were made; the expected diff inventory from 04-RESEARCH Pattern 1 therefore stands unchanged.

## The confirmed 50-row review record

Category counts: Animals 20, Plants 15, Microbe 13, Multiple 2.
Committed-file cross-reference: 45 rows agree with the committed result-file species values, 2 rows conflict, 3 registry rows have no committed results (inert — invisible to the aggregation).

| # | Dataset | Registry Category | Committed file species | Review status |
|---|---------|-------------------|------------------------|---------------|
| 1 | BEND__CpG_methylation | Animals | Animals | agree |
| 2 | Deep4mC_datasets__C.elegans_4mC | Animals | Animals | agree |
| 3 | Deep4mC_datasets__D.melanogaster_4mC | Animals | Animals | agree |
| 4 | Deep4mC_datasets__E.coli_4mC | Microbe | Microbe | agree |
| 5 | GUE__EPI_GM12878 | Animals | Microbe | **CONFLICT** — registry Animals vs file Microbe |
| 6 | GUE__emp_H3 | Microbe | Microbe | agree |
| 7 | GUE__emp_H3K14ac | Microbe | Microbe | agree |
| 8 | GUE__emp_H3K36me3 | Microbe | Microbe | agree |
| 9 | GUE__emp_H3K4me1 | Microbe | Microbe | agree |
| 10 | GUE__emp_H3K79me3 | Microbe | Microbe | agree |
| 11 | GUE__emp_H3K9ac | Microbe | Microbe | agree |
| 12 | GUE__emp_H4 | Microbe | Microbe | agree |
| 13 | GUE__emp_H4ac | Microbe | Microbe | agree |
| 14 | GUE__fungi_species_20 | Microbe | Animals | **CONFLICT** — registry Microbe vs file Animals |
| 15 | GUE__human_tf_0 | Animals | Animals | agree |
| 16 | GUE__mouse_1 | Animals | Animals | agree |
| 17 | GUE__mouse_4 | Animals | Animals | agree |
| 18 | GUE__prom_300_all | Animals | Animals | agree |
| 19 | GUE__prom_core_all | Animals | Animals | agree |
| 20 | GUE__virus_covid | Microbe | Microbe | agree |
| 21 | GUE__virus_species_40 | Microbe | Microbe | agree |
| 22 | Genomic_Benchmarks__coding | Animals | Animals | agree |
| 23 | Genomic_Benchmarks__human_vs_worm | Animals | Animals | agree |
| 24 | Genomic_Benchmarks__regulatory_region_type | Animals | Animals | agree |
| 25 | NT_downstream_tasks__H3K27ac | Animals | Animals | agree |
| 26 | NT_downstream_tasks__H3K27me3 | Animals | Animals | agree |
| 27 | NT_downstream_tasks__H3K4me2 | Animals | Animals | agree |
| 28 | NT_downstream_tasks__H3K9me3 | Animals | Animals | agree |
| 29 | NT_downstream_tasks__enhancers | Animals | Animals | agree |
| 30 | NT_downstream_tasks__splice_sites_acceptors | Animals | Animals | agree |
| 31 | NT_downstream_tasks__splice_sites_all | Animals | Animals | agree |
| 32 | NT_downstream_tasks__splice_sites_donors | Animals | Animals | agree |
| 33 | PDLLMs_datasets__plant-multi-species-H3K27ac | Plants | Plants | agree |
| 34 | PDLLMs_datasets__plant-multi-species-H3K27me3 | Plants | Plants | agree |
| 35 | PDLLMs_datasets__plant-multi-species-H3K4me3 | Plants | Plants | agree |
| 36 | PDLLMs_datasets__plant-multi-species-core-promoters | Plants | Plants | agree |
| 37 | PDLLMs_datasets__plant-multi-species-lncRNAs | Plants | Plants | agree |
| 38 | PDLLMs_datasets__plant-multi-species-open-chromatin | Plants | Plants | agree |
| 39 | PDLLMs_datasets__plant-multi-species-sequence-conservation | Plants | Plants | agree |
| 40 | PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation | Plants | Plants | agree |
| 41 | PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation | Plants | Plants | agree |
| 42 | iDNA_ABF_datasets__5mC | **Multiple** | Animals | **MULTIPLE-ORIGIN** → majority arena **Animals** (= today's file value: zero net change) |
| 43 | iDNA_ABF_datasets__6mA | **Multiple** | Animals | **MULTIPLE-ORIGIN** → majority arena **Animals** (= today's file value: zero net change) |
| 44 | iPro-WAEL_datasets__Promoter_R_capsulatus | Microbe | Microbe | agree |
| 45 | plant-genomic-benchmark__gene_exp.arabidopsis_thaliana | Plants | — | INERT (no committed results) |
| 46 | plant-genomic-benchmark__gene_exp.oryza_sativa | Plants | — | INERT (no committed results) |
| 47 | plant-genomic-benchmark__gene_exp.zea_mays | Plants | — | INERT (no committed results) |
| 48 | plant-genomic-benchmark__poly_a.arabidopsis_thaliana | Plants | Plants | agree |
| 49 | plant-genomic-benchmark__promoter_strength.leaf | Plants | Plants | agree |
| 50 | plant-genomic-benchmark__terminator_strength.leaf | Plants | Plants | agree |

## Call-outs presented at the gate

1. **The 2 conflicting rows — these ARE the fix's diff.** `GUE__EPI_GM12878` (registry Animals, committed file Microbe) and `GUE__fungi_species_20` (registry Microbe, committed file Animals). Under the fix, EPI_GM12878 moves microbe→animal and fungi_species_20 moves animal→microbe — exactly one membership swap per arena file, with both arena dataset counts preserved (22 animal / 13 microbe; the two moves cancel).
2. **The 2 Multiple-origin rows.** `iDNA_ABF_datasets__5mC` and `iDNA_ABF_datasets__6mA` carry cross-species composition; their majority-species arena was proposed as **Animals** (research A1 — committed files already carry "Animals", so the mapping produces zero net diff). **Confirmed by the maintainer with the row approval.**
3. **The 3 inert rows.** The `plant-genomic-benchmark__gene_exp.*` trio (arabidopsis_thaliana, oryza_sativa, zea_mays) exists in the registry but has no committed results in any of the 42 model files — invisible to the aggregation, needing no review action beyond presence.

## Consequence for the expected diff inventory

With no row corrections, the pre-documented inventory (04-RESEARCH Pattern 1) stands verbatim:

- `models_comparison.json` and `models_comparison_plant.json` regenerate **byte-identical** (plant membership identical under both sources: 15 registry-Plants = 12 file-Plants present + 3 inert).
- `models_comparison_animal.json` and `models_comparison_microbe.json` change **42/42 model entries each** via exactly the one membership swap per file; arena dataset counts stay 22 (animal) / 13 (microbe); zero models added or dropped.

Dry-run ground truth (maintainer-verified sandbox regeneration, 2026-10-10): animal 22 = 19 agree-with-results + EPI_GM12878 in + 2 Multiple; microbe 13 = 12 agree + fungi_species_20 in; total + plant byte-identical; sample check DNABERT-2-117M animal avg_rank 19.36→19.73, microbe 20.85→20.23.
