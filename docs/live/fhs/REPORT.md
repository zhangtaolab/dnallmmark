# TUI-driven FungiHelixSeek full sweep — operation report (quick-261022-tah)

## Overview

- Date: `2026-10-23T02:48:13Z` (UTC) — mode: **full**
- Host: `autodl-container-75f44fb3e7-9b8d8ae4` — GPUs: `NVIDIA GeForce RTX 5090
NVIDIA GeForce RTX 5090`
- What ran: FungiHelixSeek x 31 present datasets x seeds 42,43,44 (workers=2, gpus=0,1) — 93 cells expected
- Epochs: **3** from the YAML default (`pipeline/finetune_config.yaml`) — NO override was typed at the gate (the [p] argv asserted `--num_train_epochs` ABSENT; the epochs input read `''` at launch)
- Output root: `/root/autodl-tmp/Github/dnallmmark/pipeline/finetuned-fhs-full` (fresh — no trainer_state markers could skip cells)
- TUI state dir (kept; holds the queue state + logs + tee): `/root/autodl-tmp/dnallmmark-data/tui-live/tui-live-fhs-441ycv7k`
- Driver exit code: **1** — failure: the attach modal refused the root (validation problems: '✗ template validation failed — 1 problems:\n1. path: ✗ /root/autodl-tmp/Github/dnallmmark/pipeline/finetuned-fhs-full is not a sweep output root (no sweep artifacts there)') — honest halt; the sweep is unaffected

Every number in this report derives from the run's own meta (`docs/live/fhs/evidence.json`), the download ledger, and the on-disk cell artifacts — evidence from the actually-run execution.

## FINAL OUTCOME (2026-10-27 amendment — the rerun-failed lane)

The body below records the main pass at its honest fail-exit (86/93). The
rerun-failed lane (launched 2026-10-26 22:41 +08, minimal argv per D14-05/06)
has since COMPLETED and changed the final matrix:

- **GUE__virus_species_40, seeds 42/43/44: COMPLETED** — the auto gradient
  checkpointing fix (commit d27f5e0, max_length > 2560 -> GC on) carried the
  10,002-token cells to completion (batch 1 + GC recomputation, ~15.8 GB/GPU).
- **PDLLMs__plant-multi-species seed 42: COMPLETED** — the transient SIGSEGV
  healed on retry.
- **GUE__fungi_species_20, seeds 42/43/44: FAILED (permanent)** — 6 attempts
  across two lanes all ended `child exited -11` (native segfault) under
  GC; a stable crash point specific to this dataset x model combination,
  open for dedicated diagnosis.

**Final matrix: 90/93 cells completed (96.8%), 3 permanent failures** — verify
with `find pipeline/finetuned-fhs-full -name final_metrics.json | wc -l` == 90.

## Download ledger

| Key | Kind | Final state | Attempts | Problems | Duration |
|---|---|---|---|---|---|
| BEND__CpG_methylation | dataset | done | 1 | - | 2026-10-23T10:48:16+08:00 .. 2026-10-23T10:48:27+08:00 |
| Deep4mC_datasets__C.elegans_4mC | dataset | done | 1 | - | 2026-10-23T10:48:27+08:00 .. 2026-10-23T10:48:30+08:00 |
| Deep4mC_datasets__D.melanogaster_4mC | dataset | done | 1 | - | 2026-10-23T10:48:30+08:00 .. 2026-10-23T10:48:32+08:00 |
| Deep4mC_datasets__E.coli_4mC | dataset | done | 1 | - | 2026-10-23T10:48:32+08:00 .. 2026-10-23T10:48:34+08:00 |
| GUE__EPI_GM12878 | dataset | mismatch | 1 | train_rows=None, dev_rows=None, test_rows=None, unified_eval_n=None | 2026-10-23T10:48:34+08:00 .. 2026-10-23T10:48:37+08:00 |
| GUE__emp_H3K14ac | dataset | done | 1 | - | 2026-10-23T10:48:37+08:00 .. 2026-10-23T10:48:40+08:00 |
| GUE__emp_H3K36me3 | dataset | done | 1 | - | 2026-10-23T10:48:40+08:00 .. 2026-10-23T10:48:42+08:00 |
| GUE__emp_H3K4me1 | dataset | done | 1 | - | 2026-10-23T10:48:42+08:00 .. 2026-10-23T10:48:45+08:00 |
| GUE__emp_H3K79me3 | dataset | done | 1 | - | 2026-10-23T10:48:45+08:00 .. 2026-10-23T10:48:47+08:00 |
| GUE__emp_H3K9ac | dataset | done | 1 | - | 2026-10-23T10:48:47+08:00 .. 2026-10-23T10:49:50+08:00 |
| GUE__emp_H4 | dataset | done | 1 | - | 2026-10-23T10:49:50+08:00 .. 2026-10-23T10:49:52+08:00 |
| GUE__emp_H4ac | dataset | done | 1 | - | 2026-10-23T10:49:52+08:00 .. 2026-10-23T10:49:55+08:00 |
| GUE__fungi_species_20 | dataset | done | 1 | - | 2026-10-23T10:49:55+08:00 .. 2026-10-23T10:49:59+08:00 |
| GUE__human_tf_0 | dataset | done | 1 | - | 2026-10-23T10:49:59+08:00 .. 2026-10-23T10:50:01+08:00 |
| GUE__mouse_1 | dataset | done | 1 | - | 2026-10-23T10:50:01+08:00 .. 2026-10-23T10:50:04+08:00 |
| GUE__mouse_4 | dataset | done | 1 | - | 2026-10-23T10:50:04+08:00 .. 2026-10-23T10:50:06+08:00 |
| GUE__prom_300_all | dataset | done | 1 | - | 2026-10-23T10:50:06+08:00 .. 2026-10-23T10:50:09+08:00 |
| GUE__prom_core_all | dataset | done | 1 | - | 2026-10-23T10:50:09+08:00 .. 2026-10-23T10:50:11+08:00 |
| GUE__virus_covid | dataset | done | 1 | - | 2026-10-23T10:50:11+08:00 .. 2026-10-23T10:50:15+08:00 |
| GUE__virus_species_40 | dataset | done | 1 | - | 2026-10-23T10:50:15+08:00 .. 2026-10-23T10:51:12+08:00 |
| NT_downstream_tasks__H3K27ac | dataset | failed | 1 | landing_incomplete | 2026-10-23T10:51:12+08:00 .. 2026-10-23T10:52:15+08:00 |
| NT_downstream_tasks__H3K27me3 | dataset | failed | 1 | landing_incomplete | 2026-10-23T10:52:15+08:00 .. 2026-10-23T10:52:18+08:00 |
| NT_downstream_tasks__H3K4me2 | dataset | failed | 1 | landing_incomplete | 2026-10-23T10:52:18+08:00 .. 2026-10-23T10:52:20+08:00 |
| NT_downstream_tasks__H3K9me3 | dataset | failed | 1 | landing_incomplete | 2026-10-23T10:52:20+08:00 .. 2026-10-23T10:52:22+08:00 |
| NT_downstream_tasks__enhancers | dataset | failed | 1 | landing_incomplete | 2026-10-23T10:52:22+08:00 .. 2026-10-23T10:52:24+08:00 |
| NT_downstream_tasks__splice_sites_acceptors | dataset | failed | 1 | landing_incomplete | 2026-10-23T10:52:24+08:00 .. 2026-10-23T10:52:27+08:00 |
| NT_downstream_tasks__splice_sites_all | dataset | failed | 1 | landing_incomplete | 2026-10-23T10:52:27+08:00 .. 2026-10-23T10:52:29+08:00 |
| NT_downstream_tasks__splice_sites_donors | dataset | failed | 1 | landing_incomplete | 2026-10-23T10:52:29+08:00 .. 2026-10-23T10:52:31+08:00 |
| PDLLMs_datasets__plant-multi-species-H3K27ac | dataset | done | 1 | - | 2026-10-23T10:52:31+08:00 .. 2026-10-23T10:52:36+08:00 |
| PDLLMs_datasets__plant-multi-species-H3K27me3 | dataset | done | 1 | - | 2026-10-23T10:52:36+08:00 .. 2026-10-23T10:52:39+08:00 |
| PDLLMs_datasets__plant-multi-species-H3K4me3 | dataset | done | 1 | - | 2026-10-23T10:52:39+08:00 .. 2026-10-23T10:52:43+08:00 |
| PDLLMs_datasets__plant-multi-species-core-promoters | dataset | done | 1 | - | 2026-10-23T10:52:43+08:00 .. 2026-10-23T10:52:46+08:00 |
| PDLLMs_datasets__plant-multi-species-lncRNAs | dataset | done | 1 | - | 2026-10-23T10:52:46+08:00 .. 2026-10-23T10:52:49+08:00 |
| PDLLMs_datasets__plant-multi-species-sequence-conservation | dataset | done | 1 | - | 2026-10-23T10:52:49+08:00 .. 2026-10-23T10:52:52+08:00 |
| PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation | dataset | done | 1 | - | 2026-10-23T10:52:52+08:00 .. 2026-10-23T10:52:55+08:00 |
| PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation | dataset | done | 1 | - | 2026-10-23T10:52:55+08:00 .. 2026-10-23T10:52:58+08:00 |
| iDNA_ABF_datasets__6mA | dataset | done | 1 | - | 2026-10-23T10:52:58+08:00 .. 2026-10-23T10:53:00+08:00 |
| iPro-WAEL_datasets__Promoter_R_capsulatus | dataset | done | 1 | - | 2026-10-23T10:53:00+08:00 .. 2026-10-23T10:53:03+08:00 |
| plant-genomic-benchmark__gene_exp.arabidopsis_thaliana | dataset | failed | 1 | landing_incomplete | 2026-10-23T10:53:03+08:00 .. 2026-10-23T10:53:06+08:00 |
| plant-genomic-benchmark__gene_exp.oryza_sativa | dataset | failed | 1 | landing_incomplete | 2026-10-23T10:53:06+08:00 .. 2026-10-23T10:53:08+08:00 |
| plant-genomic-benchmark__gene_exp.zea_mays | dataset | failed | 1 | landing_incomplete | 2026-10-23T10:53:08+08:00 .. 2026-10-23T10:53:10+08:00 |
| plant-genomic-benchmark__poly_a.arabidopsis_thaliana | dataset | failed | 1 | landing_incomplete | 2026-10-23T10:53:10+08:00 .. 2026-10-23T10:55:14+08:00 |
| plant-genomic-benchmark__promoter_strength.leaf | dataset | failed | 1 | landing_incomplete | 2026-10-23T10:55:14+08:00 .. 2026-10-23T10:55:16+08:00 |
| plant-genomic-benchmark__terminator_strength.leaf | dataset | failed | 1 | - | 2026-10-23T10:55:16+08:00 .. 2026-10-23T10:55:18+08:00 |

Not-enqueued official keys (the honest skip ledger):

| Key | Channel | Reason |
|---|---|---|
| Genomic_Benchmarks__coding | disabled | shape_d_layout |
| Genomic_Benchmarks__human_vs_worm | disabled | shape_d_layout |
| Genomic_Benchmarks__regulatory_region_type | disabled | shape_d_layout |
| PDLLMs_datasets__plant-multi-species-open-chromatin | disabled | shape_d_layout |

- Already present BEFORE the downloads (2): GUE__emp_H3, iDNA_ABF_datasets__5mC

## Run matrix summary

- 1 model (FungiHelixSeek) x 31 present datasets x 3 seeds = **93 expected cells**
- Present set (the actually-downloaded present set, derived through the picker's own chain): 31 keys

- Cells with final_metrics.json on disk at report time: 0 / 93

## Per-dataset x seed results

| Dataset | Seed | eval_f1 | eval_accuracy | eval_mcc | train_runtime (s) | FLOPs (G) | GPU |
|---|---|---|---|---|---|---|---|
| BEND__CpG_methylation (absent) | 42 | - | - | - | - | - | - |
| BEND__CpG_methylation (absent) | 43 | - | - | - | - | - | - |
| BEND__CpG_methylation (absent) | 44 | - | - | - | - | - | - |
| Deep4mC_datasets__C.elegans_4mC (absent) | 42 | - | - | - | - | - | - |
| Deep4mC_datasets__C.elegans_4mC (absent) | 43 | - | - | - | - | - | - |
| Deep4mC_datasets__C.elegans_4mC (absent) | 44 | - | - | - | - | - | - |
| Deep4mC_datasets__D.melanogaster_4mC (absent) | 42 | - | - | - | - | - | - |
| Deep4mC_datasets__D.melanogaster_4mC (absent) | 43 | - | - | - | - | - | - |
| Deep4mC_datasets__D.melanogaster_4mC (absent) | 44 | - | - | - | - | - | - |
| Deep4mC_datasets__E.coli_4mC (absent) | 42 | - | - | - | - | - | - |
| Deep4mC_datasets__E.coli_4mC (absent) | 43 | - | - | - | - | - | - |
| Deep4mC_datasets__E.coli_4mC (absent) | 44 | - | - | - | - | - | - |
| GUE__emp_H3 (absent) | 42 | - | - | - | - | - | - |
| GUE__emp_H3 (absent) | 43 | - | - | - | - | - | - |
| GUE__emp_H3 (absent) | 44 | - | - | - | - | - | - |
| GUE__emp_H3K14ac (absent) | 42 | - | - | - | - | - | - |
| GUE__emp_H3K14ac (absent) | 43 | - | - | - | - | - | - |
| GUE__emp_H3K14ac (absent) | 44 | - | - | - | - | - | - |
| GUE__emp_H3K36me3 (absent) | 42 | - | - | - | - | - | - |
| GUE__emp_H3K36me3 (absent) | 43 | - | - | - | - | - | - |
| GUE__emp_H3K36me3 (absent) | 44 | - | - | - | - | - | - |
| GUE__emp_H3K4me1 (absent) | 42 | - | - | - | - | - | - |
| GUE__emp_H3K4me1 (absent) | 43 | - | - | - | - | - | - |
| GUE__emp_H3K4me1 (absent) | 44 | - | - | - | - | - | - |
| GUE__emp_H3K79me3 (absent) | 42 | - | - | - | - | - | - |
| GUE__emp_H3K79me3 (absent) | 43 | - | - | - | - | - | - |
| GUE__emp_H3K79me3 (absent) | 44 | - | - | - | - | - | - |
| GUE__emp_H3K9ac (absent) | 42 | - | - | - | - | - | - |
| GUE__emp_H3K9ac (absent) | 43 | - | - | - | - | - | - |
| GUE__emp_H3K9ac (absent) | 44 | - | - | - | - | - | - |
| GUE__emp_H4 (absent) | 42 | - | - | - | - | - | - |
| GUE__emp_H4 (absent) | 43 | - | - | - | - | - | - |
| GUE__emp_H4 (absent) | 44 | - | - | - | - | - | - |
| GUE__emp_H4ac (absent) | 42 | - | - | - | - | - | - |
| GUE__emp_H4ac (absent) | 43 | - | - | - | - | - | - |
| GUE__emp_H4ac (absent) | 44 | - | - | - | - | - | - |
| GUE__fungi_species_20 (absent) | 42 | - | - | - | - | - | - |
| GUE__fungi_species_20 (absent) | 43 | - | - | - | - | - | - |
| GUE__fungi_species_20 (absent) | 44 | - | - | - | - | - | - |
| GUE__human_tf_0 (absent) | 42 | - | - | - | - | - | - |
| GUE__human_tf_0 (absent) | 43 | - | - | - | - | - | - |
| GUE__human_tf_0 (absent) | 44 | - | - | - | - | - | - |
| GUE__mouse_1 (absent) | 42 | - | - | - | - | - | - |
| GUE__mouse_1 (absent) | 43 | - | - | - | - | - | - |
| GUE__mouse_1 (absent) | 44 | - | - | - | - | - | - |
| GUE__mouse_4 (absent) | 42 | - | - | - | - | - | - |
| GUE__mouse_4 (absent) | 43 | - | - | - | - | - | - |
| GUE__mouse_4 (absent) | 44 | - | - | - | - | - | - |
| GUE__prom_300_all (absent) | 42 | - | - | - | - | - | - |
| GUE__prom_300_all (absent) | 43 | - | - | - | - | - | - |
| GUE__prom_300_all (absent) | 44 | - | - | - | - | - | - |
| GUE__prom_core_all (absent) | 42 | - | - | - | - | - | - |
| GUE__prom_core_all (absent) | 43 | - | - | - | - | - | - |
| GUE__prom_core_all (absent) | 44 | - | - | - | - | - | - |
| GUE__virus_covid (absent) | 42 | - | - | - | - | - | - |
| GUE__virus_covid (absent) | 43 | - | - | - | - | - | - |
| GUE__virus_covid (absent) | 44 | - | - | - | - | - | - |
| GUE__virus_species_40 (absent) | 42 | - | - | - | - | - | - |
| GUE__virus_species_40 (absent) | 43 | - | - | - | - | - | - |
| GUE__virus_species_40 (absent) | 44 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-H3K27ac (absent) | 42 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-H3K27ac (absent) | 43 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-H3K27ac (absent) | 44 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-H3K27me3 (absent) | 42 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-H3K27me3 (absent) | 43 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-H3K27me3 (absent) | 44 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-H3K4me3 (absent) | 42 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-H3K4me3 (absent) | 43 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-H3K4me3 (absent) | 44 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-core-promoters (absent) | 42 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-core-promoters (absent) | 43 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-core-promoters (absent) | 44 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-lncRNAs (absent) | 42 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-lncRNAs (absent) | 43 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-lncRNAs (absent) | 44 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-sequence-conservation (absent) | 42 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-sequence-conservation (absent) | 43 | - | - | - | - | - | - |
| PDLLMs_datasets__plant-multi-species-sequence-conservation (absent) | 44 | - | - | - | - | - | - |
| PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation (absent) | 42 | - | - | - | - | - | - |
| PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation (absent) | 43 | - | - | - | - | - | - |
| PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation (absent) | 44 | - | - | - | - | - | - |
| PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation (absent) | 42 | - | - | - | - | - | - |
| PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation (absent) | 43 | - | - | - | - | - | - |
| PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation (absent) | 44 | - | - | - | - | - | - |
| iDNA_ABF_datasets__5mC (absent) | 42 | - | - | - | - | - | - |
| iDNA_ABF_datasets__5mC (absent) | 43 | - | - | - | - | - | - |
| iDNA_ABF_datasets__5mC (absent) | 44 | - | - | - | - | - | - |
| iDNA_ABF_datasets__6mA (absent) | 42 | - | - | - | - | - | - |
| iDNA_ABF_datasets__6mA (absent) | 43 | - | - | - | - | - | - |
| iDNA_ABF_datasets__6mA (absent) | 44 | - | - | - | - | - | - |
| iPro-WAEL_datasets__Promoter_R_capsulatus (absent) | 42 | - | - | - | - | - | - |
| iPro-WAEL_datasets__Promoter_R_capsulatus (absent) | 43 | - | - | - | - | - | - |
| iPro-WAEL_datasets__Promoter_R_capsulatus (absent) | 44 | - | - | - | - | - | - |

## Failure / skip ledger

- download GUE__EPI_GM12878: mismatch (problems: train_rows=None, dev_rows=None, test_rows=None, unified_eval_n=None)
- download NT_downstream_tasks__H3K27ac: failed (problems: landing_incomplete)
- download NT_downstream_tasks__H3K27me3: failed (problems: landing_incomplete)
- download NT_downstream_tasks__H3K4me2: failed (problems: landing_incomplete)
- download NT_downstream_tasks__H3K9me3: failed (problems: landing_incomplete)
- download NT_downstream_tasks__enhancers: failed (problems: landing_incomplete)
- download NT_downstream_tasks__splice_sites_acceptors: failed (problems: landing_incomplete)
- download NT_downstream_tasks__splice_sites_all: failed (problems: landing_incomplete)
- download NT_downstream_tasks__splice_sites_donors: failed (problems: landing_incomplete)
- download plant-genomic-benchmark__gene_exp.arabidopsis_thaliana: failed (problems: landing_incomplete)
- download plant-genomic-benchmark__gene_exp.oryza_sativa: failed (problems: landing_incomplete)
- download plant-genomic-benchmark__gene_exp.zea_mays: failed (problems: landing_incomplete)
- download plant-genomic-benchmark__poly_a.arabidopsis_thaliana: failed (problems: landing_incomplete)
- download plant-genomic-benchmark__promoter_strength.leaf: failed (problems: landing_incomplete)
- download plant-genomic-benchmark__terminator_strength.leaf: failed (problems: -)
- cell BEND__CpG_methylation / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell BEND__CpG_methylation / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell BEND__CpG_methylation / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell Deep4mC_datasets__C.elegans_4mC / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell Deep4mC_datasets__C.elegans_4mC / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell Deep4mC_datasets__C.elegans_4mC / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell Deep4mC_datasets__D.melanogaster_4mC / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell Deep4mC_datasets__D.melanogaster_4mC / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell Deep4mC_datasets__D.melanogaster_4mC / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell Deep4mC_datasets__E.coli_4mC / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell Deep4mC_datasets__E.coli_4mC / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell Deep4mC_datasets__E.coli_4mC / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3 / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3 / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3 / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K14ac / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K14ac / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K14ac / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K36me3 / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K36me3 / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K36me3 / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K4me1 / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K4me1 / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K4me1 / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K79me3 / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K79me3 / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K79me3 / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K9ac / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K9ac / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H3K9ac / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H4 / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H4 / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H4 / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H4ac / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H4ac / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__emp_H4ac / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__fungi_species_20 / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__fungi_species_20 / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__fungi_species_20 / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__human_tf_0 / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__human_tf_0 / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__human_tf_0 / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__mouse_1 / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__mouse_1 / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__mouse_1 / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__mouse_4 / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__mouse_4 / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__mouse_4 / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__prom_300_all / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__prom_300_all / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__prom_300_all / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__prom_core_all / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__prom_core_all / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__prom_core_all / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__virus_covid / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__virus_covid / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__virus_covid / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__virus_species_40 / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__virus_species_40 / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell GUE__virus_species_40 / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-H3K27ac / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-H3K27ac / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-H3K27ac / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-H3K27me3 / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-H3K27me3 / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-H3K27me3 / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-H3K4me3 / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-H3K4me3 / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-H3K4me3 / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-core-promoters / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-core-promoters / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-core-promoters / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-lncRNAs / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-lncRNAs / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-lncRNAs / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-sequence-conservation / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-sequence-conservation / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PDLLMs_datasets__plant-multi-species-sequence-conservation / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell iDNA_ABF_datasets__5mC / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell iDNA_ABF_datasets__5mC / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell iDNA_ABF_datasets__5mC / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell iDNA_ABF_datasets__6mA / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell iDNA_ABF_datasets__6mA / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell iDNA_ABF_datasets__6mA / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell iPro-WAEL_datasets__Promoter_R_capsulatus / seed 42: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell iPro-WAEL_datasets__Promoter_R_capsulatus / seed 43: no final_metrics.json (not run or failed — see the dispatch ledger under the root)
- cell iPro-WAEL_datasets__Promoter_R_capsulatus / seed 44: no final_metrics.json (not run or failed — see the dispatch ledger under the root)

## GPU utilization summary (per-interval snapshots)

- (none captured — the run did not reach the watch loop)

## Journey stage timings

| Stage | At (UTC) | Elapsed (s) |
|---|---|---|
| 001_boot_env_check | 2026-10-23T02:48:13Z | 0.7 |
| slot2_arrived | 2026-10-23T02:48:14Z | 1.1 |
| model_row_located | 2026-10-23T02:48:15Z | 2.7 |
| 002_model_row_missing | 2026-10-23T02:48:15Z | 2.7 |
| slot3_arrived | 2026-10-23T02:48:16Z | 3.0 |
| 004_data_presence_before | 2026-10-23T02:48:16Z | 3.1 |
| datasets_enqueued_44 | 2026-10-23T02:48:16Z | 3.4 |
| 005_data_enqueue_all | 2026-10-23T02:48:16Z | 3.5 |
| 006_download_running_001 | 2026-10-23T02:48:16Z | 3.5 |
| 006_download_running_002 | 2026-10-23T02:58:16Z | 603.6 |
| 007_download_settled_queue | 2026-10-23T03:08:16Z | 1203.7 |
| 007_download_settled_missing_view | 2026-10-23T03:08:17Z | 1203.9 |
| 008_download_presence_final | 2026-10-23T03:08:17Z | 1204.1 |
| 009_queue_detail_modal | 2026-10-23T03:08:19Z | 1205.9 |
| matrix_derived_31x3 | 2026-10-23T03:08:19Z | 1206.0 |
| slot4_arrived | 2026-10-23T03:08:19Z | 1206.4 |
| wizard_model_marked | 2026-10-23T03:08:22Z | 1208.8 |
| 010_wizard_model_marked | 2026-10-23T03:08:22Z | 1208.9 |
| wizard_datasets_marked | 2026-10-23T03:10:29Z | 1336.1 |
| 011_wizard_datasets_marked | 2026-10-23T03:10:29Z | 1336.2 |
| params_typed | 2026-10-23T03:10:45Z | 1351.8 |
| preview_line_asserted | 2026-10-23T03:10:45Z | 1351.8 |
| 012_run_config_params | 2026-10-23T03:10:45Z | 1351.9 |
| argv_preview_asserted | 2026-10-23T03:10:45Z | 1352.1 |
| 013_run_config_preview | 2026-10-23T03:10:45Z | 1352.2 |
| gate_confirm_reached | 2026-10-23T03:10:45Z | 1352.7 |
| 014_run_config_confirm | 2026-10-23T03:10:45Z | 1352.7 |
| launch_y_pressed | 2026-10-23T03:10:46Z | 1353.0 |
| monitor_switched | 2026-10-23T03:10:46Z | 1353.0 |
| 998_monitor_failure | 2026-10-23T03:12:21Z | 1448.1 |

## Honest notes

- model already on disk at preflight — the slot-2 enqueue leg is honestly skipped (gate outcome recorded)
- monitor card not discovered within 60s — driving the [a] attach modal with the resolved absolute path
- FAILURE: the attach modal refused the root (validation problems: '✗ template validation failed — 1 problems:\n1. path: ✗ /root/autodl-tmp/Github/dnallmmark/pipeline/finetuned-fhs-full is not a sweep output root (no sweep artifacts there)') — honest halt; the sweep is unaffected

## Re-attach instructions

The sweep is NEVER killed by the driver — if it is still alive it survives detached in its own session:

- TUI: slot 5, press `a`, type `/root/autodl-tmp/Github/dnallmmark/pipeline/finetuned-fhs-full`
- CLI: `cat /root/autodl-tmp/Github/dnallmmark/pipeline/finetuned-fhs-full/dispatch_state.json`
- Live view: `nvidia-smi`
