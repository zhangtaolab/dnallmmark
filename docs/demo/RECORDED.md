# TUI demo recording ledger

Every row states what the GIF truly shows: the real targets the
live presence scan chose, the resets applied before spawn (the
re-record lever), and honest notes for anything that degraded.
Regenerate any row: `scripts/demo/record.sh <scene> <lang> [speed]`.

Scene | Lang | Real targets / what actually happened | Cast | GIF | Date
|---|---|---|---|---|---|
| env-check | en | model_target=PlantCaduceus_l24, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — 8 kernels live on boot (fresh state dir); r re-run; version_pins drill-down | casts/env-check-en.cast (105.0 KB) | gifs/env-check-en.gif (200.9 KB) | 2026-10-15 |

| env-check | zh | model_target=PlantCaduceus_l24, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — 8 kernels live on boot (fresh state dir); r re-run; version_pins drill-down | casts/env-check-zh.cast (193.5 KB) | gifs/env-check-zh.gif (341.5 KB) | 2026-10-15 |

| selection-presets | en | model_target=PlantCaduceus_l24, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — SCREEN AT FAILURE:
 DNABERT-2-117M            ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 FungiHelixSeek            ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 GENA-LM-yeast             ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 GENERanno-eukaryote-0.5…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 GENERanno-prokaryote-0.…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 GROVER                    ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 GenomeOcean-500M          ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 Jamba-DNA-v1-114M-hg38    ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓▇▇
 Mistral-DNA-v1-138M-vir…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 Mistral-DNA-v1-417M-Ath…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 Mistral-DNA-v1-422M-hg38  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 ModernBERT-DNA-v1-37M-h…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 MutBERT-Multi             ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 Omni-DNA-700M             ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 OmniNA-220m               ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantBiMoE                ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantCAD2-Large           ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantCAD2-Medium-l48-d1…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantCAD2-Small-l24-d07…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantCaduceus_l24         ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantCaduceus_l32         ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantDNAMamba2-BPE        ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
                  ▍
  Cursor: BEND__CpG_methylation; space marks on the plant-dnabert family (filter+tab idiom); species:plants registry-grammar filter; tier-1 preset apply; preset save 'demo-walkthrough'; 59x50 presence matrix | casts/selection-presets-en.cast (614.7 KB) | gifs/selection-presets-en.gif (852.2 KB) | 2026-10-15 |

| selection-presets | zh | model_target=PlantCaduceus_l24, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — SCREEN AT FAILURE:
 DNABERT-2-117M            ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 FungiHelixSeek            ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 GENA-LM-yeast             ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 GENERanno-eukaryote-0.5…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 GENERanno-prokaryote-0.…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 GROVER                    ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 GenomeOcean-500M          ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 Jamba-DNA-v1-114M-hg38    ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓▇▇
 Mistral-DNA-v1-138M-vir…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 Mistral-DNA-v1-417M-Ath…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 Mistral-DNA-v1-422M-hg38  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 ModernBERT-DNA-v1-37M-h…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 MutBERT-Multi             ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 Omni-DNA-700M             ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 OmniNA-220m               ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantBiMoE                ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantCAD2-Large           ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantCAD2-Medium-l48-d1…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantCAD2-Small-l24-d07…  ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantCaduceus_l24         ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantCaduceus_l32         ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
 PlantDNAMamba2-BPE        ✓         ✓         ✓         ✓         ✓         ✓         ✓         ✓
                  ▍
  光标: BEND__CpG_methylation; space marks on the plant-dnabert family (filter+tab idiom); species:plants registry-grammar filter; tier-1 preset apply; preset save 'demo-walkthrough'; 59x50 presence matrix | casts/selection-presets-zh.cast (616.4 KB) | gifs/selection-presets-zh.gif (1.0 MB) | 2026-10-15 |

| language-toggle | en | model_target=PlantCaduceus_l24, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — the L live toggle: full-screen re-render, bars/footer follow, one navigation in the toggled language, restored before quit | casts/language-toggle-en.cast (259.2 KB) | gifs/language-toggle-en.gif (443.6 KB) | 2026-10-15 |

| language-toggle | zh | model_target=PlantCaduceus_l24, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — the L live toggle: full-screen re-render, bars/footer follow, one navigation in the toggled language, restored before quit | casts/language-toggle-zh.cast (200.3 KB) | gifs/language-toggle-zh.gif (388.7 KB) | 2026-10-15 |

| run-config-preview | en | model_target=PlantCaduceus_l24, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — position cursor on plant-dnabert-6mer via filter+tab; mark plant-dnabert-6mer via filter+tab; position cursor on iDNA_ABF_datasets__5mC via filter+tab; mark iDNA_ABF_datasets__5mC via filter+tab; picker m flip + filter marks (plant-dnabert-6mer, iDNA_ABF_datasets__5mC); seeds 42,43; epochs 1; output root ./finetuned/demo; verbatim dry-run argv preview | casts/run-config-preview-en.cast (880.4 KB) | gifs/run-config-preview-en.gif (1.2 MB) | 2026-10-15 |

| run-config-preview | zh | model_target=PlantCaduceus_l24, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — position cursor on plant-dnabert-6mer via filter+tab; mark plant-dnabert-6mer via filter+tab; position cursor on iDNA_ABF_datasets__5mC via filter+tab; mark iDNA_ABF_datasets__5mC via filter+tab; picker m flip + filter marks (plant-dnabert-6mer, iDNA_ABF_datasets__5mC); seeds 42,43; epochs 1; output root ./finetuned/demo; verbatim dry-run argv preview | casts/run-config-preview-zh.cast (1018.7 KB) | gifs/run-config-preview-zh.gif (1.4 MB) | 2026-10-15 |

| wizard | en | model_target=PlantCaduceus_l24, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — dataset wizard with real field edits (enter/b, esc-cancel, nothing landed); model wizard open/step/esc over the blank form | casts/wizard-en.cast (545.3 KB) | gifs/wizard-en.gif (436.5 KB) | 2026-10-15 |

| wizard | zh | model_target=PlantCaduceus_l24, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — dataset wizard with real field edits (enter/b, esc-cancel, nothing landed); model wizard open/step/esc over the blank form | casts/wizard-zh.cast (686.8 KB) | gifs/wizard-zh.gif (650.8 KB) | 2026-10-15 |

| custom-entries | en | model_target=PlantCaduceus_l24, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — position cursor on demo-custom-model via filter+tab; e disables demo-custom-model (disabled suffix renders) and RESTORES it; w opens the prefilled edit form; esc discards | casts/custom-entries-en.cast (367.9 KB) | gifs/custom-entries-en.gif (381.4 KB) | 2026-10-15 |

| custom-entries | zh | model_target=PlantCaduceus_l24, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — SCREEN AT FAILURE:
[7;38;5;23;48;5;235m        ▌                                                  ▌
▌ 已切换到中文
▌
▌ ✓ 已停用
▌ demo-custom-model（运行不再加载，loader 级）
▌                                                                             已标记: 模型 0/60 · 数据集 0/50 · 官方 59/50 · 自定义 1/0
(已适配 1/37)
 Mk  Models                                          Type  Species   Size(M)  Adapt     Download
     ◇ demo-custom-model（已停用）                   MLM   plants    89       自定义    ✓ 已下载
                                                 ▌
                                                 ▌ 已切换到中文
                                                 ▌
                                                 ▌ ✓ 已停用
                                                 ▌ demo-custom-model（运行不再加载，loader 级）
                                                 ▌                                                                                                   ▌
                                                                                                                                                   ▌
                                                                                     ▌                                                                                                 ▌; position cursor on demo-custom-model via filter+tab; e disables demo-custom-model (disabled suffix renders) and RESTORES it; w opens the prefilled edit form; esc discards | casts/custom-entries-zh.cast (183.4 KB) | gifs/custom-entries-zh.gif (258.3 KB) | 2026-10-15 |

| model-download | en | model_target=PlantCaduceus_l24, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — reset download target models/PlantCaduceus_l24 before spawn (the re-record lever); position cursor on PlantCaduceus_l24 via filter+tab; REAL ModelScope download of PlantCaduceus_l24 (smallest missing adapted model, live scan) with percent + transfer-rate ticks; download column flip | casts/model-download-en.cast (229.7 KB) | gifs/model-download-en.gif (360.8 KB) | 2026-10-15 |

| model-download | zh | model_target=caduceus-ph_seqlen-131k_d_model-256_n_layer-16, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — SCREEN AT FAILURE:
9;1H                                                                                     ▌              ▌
▌ ✓
▌ caduceus-ph_seqlen-131k_d_model-256_n_layer-16
▌ 模型下载完成 — 下载列已更新
▌                                                                             已标记: 模型 0/60 · 数据集 0/50 · 官方 59/50 · 自定义 1/0
(已适配 1/37)
 Mk  Models                                          Type  Species   Size(M)  Adapt     Download
     caduceus-ph_seqlen-131k_d_model-256_n_layer-16  MLM   human     8        已适配    ✓ 已下载
                                                 ▌
                                                 ▌ ✓
                                                 ▌ caduceus-ph_seqlen-131k_d_model-256_n_layer-16
                                                 ▌ 模型下载完成 — 下载列已更新
                                                 ▌                                                                                                   ▌
                                                                                     ▌                                                                                                 ▌; reset download target models/caduceus-ph_seqlen-131k_d_model-256_n_layer-16 before spawn (the re-record lever); position cursor on caduceus-ph_seqlen-131k_d_model-256_n_layer-16 via filter+tab; REAL ModelScope download of caduceus-ph_seqlen-131k_d_model-256_n_layer-16 (smallest missing adapted model, live scan) with percent + transfer-rate ticks; download column flip | casts/model-download-zh.cast (212.4 KB) | gifs/model-download-zh.gif (281.7 KB) | 2026-10-15 |

| launch-monitor-kill | en | model_target=gpn-brassicales, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — wiped finetuned/demo; the fail root finetuned/demo-fail carries 1 real failure(s) from the off-camera CLI prep sweep; position cursor on plant-dnabert-6mer via filter+tab; mark plant-dnabert-6mer via filter+tab; position cursor on iDNA_ABF_datasets__5mC via filter+tab; mark iDNA_ABF_datasets__5mC via filter+tab; REAL launch of plant-dnabert-6mer x iDNA_ABF_datasets__5mC seeds 42,43 epochs 1 at ./finetuned/demo through the y-gate (enter shown inert); auto-switch + live 0/2 stats; log tail; failures modal empty mid-run; EHC-3 stage-0 refusal naming the running root; q->k kills the sweep mid-seed-42 (the console's cell-completion stall makes the fold-then-kill sequence unreachable on this box — WINDOWS row) | casts/launch-monitor-kill-en.cast (1.8 MB) | gifs/launch-monitor-kill-en.gif (2.1 MB) | 2026-10-15 |

| dataset-download | en | model_target=gpn-brassicales, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — REAL ModelScope dataset download of iPro-WAEL_datasets__Promoter_R_capsulatus (the box's one n_audit-missing key, reset lever documented in RECORDED.md) with queue percent + progress bar + rate; reconcile flip; queue-row drill-down | casts/dataset-download-en.cast (153.9 KB) | gifs/dataset-download-en.gif (287.4 KB) | 2026-10-15 |

| rerun-from-failures | en | model_target=gpn-brassicales, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — attach target carries 1 real failure(s); attach the fail root (repo-relative path form); the real failure from launch A is listed; r->y (enter shown inert) re-runs it at the sweep's own root; the now-present dataset lets the seed retrain to completion | casts/rerun-from-failures-en.cast (4.2 MB) | gifs/rerun-from-failures-en.gif (382.0 KB) | 2026-10-15 |

| launch-monitor-kill | zh | model_target=gpn-brassicales, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — SCREEN AT FAILURE:
────────────────────────────────────────────────────────────────────────────────────────────────────
  干跑: 1 模型 × 1 任务 × 2 种子 = 2 训练项
  [space]标记 [m]数据集 [/]过滤 [p]干跑预览 [s]保存默认 [ctrl+o]选目录…    [?]帮助 [q]退出 [L]语言  ┌─ 启动门 ─────────────────────────────────────────────────┐
│                                                          │
│    ⚠ 预览校验失败 — 共 1 处问题：                        │
│    1. ⚠                                                  │
│    单卡机器上已有训练任务在运行（/home/forrest/Gith      │
│    — 请等待完成、经退出门终止，或换一个结果目录          │
│                                 ▋                        │
│     esc Back                                             │
│                                                          │
└──────────────────────────────────────────────────────────┘┌─ 启动门 ─────────────────────────────────────────────────┐
│                                                          │
│    ⚠ 预览校验失败 — 共 1 处问题：                        │
│    1. ⚠                                                  │
│    单卡机器上已有训练任务在运行（/home/forrest/Gith      │
│    — 请等待完成、经退出门终止，或换一个结果目录          │
│                                 ▋                        │
│     esc Back                                             │
│                                                          │
└──────────────────────────────────────────────────────────┘
                             ▋
 esc Back
                             ▋; wiped finetuned/demo; the fail root finetuned/demo-fail carries 1 real failure(s) from the off-camera CLI prep sweep; position cursor on plant-dnabert-6mer via filter+tab; mark plant-dnabert-6mer via filter+tab; position cursor on iDNA_ABF_datasets__5mC via filter+tab; mark iDNA_ABF_datasets__5mC via filter+tab; REAL launch of plant-dnabert-6mer x iDNA_ABF_datasets__5mC seeds 42,43 epochs 1 at ./finetuned/demo through the y-gate (enter shown inert); auto-switch + live 0/2 stats; log tail; failures modal empty mid-run; EHC-3 stage-0 refusal naming the running root; q->k kills the sweep mid-seed-42 (the console's cell-completion stall makes the fold-then-kill sequence unreachable on this box — WINDOWS row) | casts/launch-monitor-kill-zh.cast (1.5 MB) | gifs/launch-monitor-kill-zh.gif (2.2 MB) | 2026-10-15 |

| dataset-download | zh | model_target=gpn-brassicales, dataset_target=iPro-WAEL_datasets__Promoter_R_capsulatus, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — SCREEN AT FAILURE:
 Task                               State       Progress           Row reconcile
 iPro-WAEL_datasets__Promoter_R…    ✓ done      100%               ✓ 10581 行一致
▌
▌ ✓ 已入队:
▌ iPro-WAEL_datasets__Promoter_R_capsulatus
▌                                                                                                                       在场 50/50 · 缺失 0
 缺失数据集 (0) — 来自 n_audit
 Datasets                           n_audit baseline rows
 ✓ 无缺失数据集 — 全部 50 个数据集
▌
下载队列 (1) — 串行 · 状态持久化于 XDG state
▌ ✓ 已入队:
 Task                               State       P▌ iPro-WAEL_datasets__Promoter_R_capsulatus
 iPro-WAEL_datasets__Promoter_R…    ✓ done      1▌
▌
▌ ✓ iPro-WAEL_datasets__Promoter_R_capsulatus
▌ 下载完成且对账一致 — 在场已更新
▌                                                ▌
▌ ✓ iPro-WAEL_datasets__Promoter_R_capsulatus
▌ 下载完成且对账一致 — 在场已更新
▌                                                ──────────────────────────────────────────────────────────────────────────────────────────────────
         [z] 备选 Zenodo 整包 · 未公开（探测于 23:18
 Task                               State       Progress           Row reconcile
 iPro-WAEL_datasets__Promoter_R…    ✓ done      100%               ✓ 10581 行一致; REAL ModelScope dataset download of iPro-WAEL_datasets__Promoter_R_capsulatus (the box's one n_audit-missing key, reset lever documented in RECORDED.md) with queue percent + progress bar + rate; reconcile flip; queue-row drill-down | casts/dataset-download-zh.cast (112.4 KB) | gifs/dataset-download-zh.gif (238.6 KB) | 2026-10-15 |

 ✓          peft           peft 0.
 ✓          CUDA           CUDA av
 ⠋ checkin  matmul smoke
 ◌ pending  numpy≥2
 ◌ pending  model dirs
 ◌ pending  dataset dirs
                                                                                                                                                       Last check: 2026-10-15 23:19
 State      Check          Summary
 ✓          version pins   import
 ✓          dnallm import  import
 ✓          peft           peft 0.
 ✓          CUDA           CUDA av
 ✓          matmul smoke   small-t
 ✓          numpy≥2        import
 ✗          model dirs     47 of 5
 ✓          dataset dirs   all 50
────────────────────────────────────────────────────────────────────────────────────────────────────
    ✓ environment ready (launch allowed)
    ⚠ 47 model dirs missing — models are placed by hand (the storage location is visible in [4]
    Run Config)
                                                                                                    ────────────────────────────────────────────────────────────────────────────────────────────────────
    ✓ environment ready (launch allowed)
    ⚠ 47 model dirs missing — models are placed by hand (the storage location is visible in [4]
    Run Config); attach target carries 1 real failure(s); attach the fail root (repo-relative path form); the real failure from launch A is listed; r->y (enter shown inert) re-runs it at the sweep's own root; the now-present dataset lets the seed retrain to completion | casts/rerun-from-failures-zh.cast (38.4 KB) | gifs/rerun-from-failures-zh.gif (124.8 KB) | 2026-10-15 |

| rerun-from-failures | zh | model_target=gpn-brassicales, demo_model=plant-dnabert-6mer, demo_task=iDNA_ABF_datasets__5mC, demo_seeds=42,43, demo_epochs=1, demo_root=./finetuned/demo, demo_fail_root=./finetuned/demo-fail, custom_key=demo-custom-model — attach target carries 1 real failure(s); attach the fail root (repo-relative path form); the real failure from launch A is listed; r->y (enter shown inert) re-runs it at the sweep's own root; the now-present dataset lets the seed retrain to completion | casts/rerun-from-failures-zh.cast (536.4 KB) | gifs/rerun-from-failures-zh.gif (383.6 KB) | 2026-10-15 |

