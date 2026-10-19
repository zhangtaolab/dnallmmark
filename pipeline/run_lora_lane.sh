#!/bin/bash
# evo2_1b_base LoRA lane 续跑 (GPU1) — 2026-10-19 PEFT 嵌套 modules_to_save 修复后重启
# 与 run_benchmark_2gpu.sh 的 lora lane 同参数; 断点续跑 (trainer_state.json) 自动跳过
set -u
source /root/miniconda3/etc/profile.d/conda.sh
conda activate dnallm
cd /root/autodl-tmp/dnallmmark/pipeline
LOG="logs/formal_evo2_1b_base_lora_gpu1_$(date +%m%d_%H%M).log"
export CUDA_VISIBLE_DEVICES=1 DNALLM_ERROR_LOG_TAG=_gpu1_lora
for seed in 42 43 44; do
  echo "=== CELL START evo2_1b_base | lora | seed $seed | gpu 1 $(date '+%F %T') ==="
  python run_finetune.py \
    --seed "$seed" \
    --target_model evo2_1b_base \
    --batch_size 16 \
    --auto_batch_size \
    --effective_batch_size 16 \
    --remove_pt \
    --remove_checkpoints \
    --subset_file eval_subsets.json \
    --category_order Plants \
    --peft lora 2>&1 | tee -a "$LOG"
  echo "=== CELL EXIT  evo2_1b_base | lora | seed $seed | gpu 1 code=${PIPESTATUS[0]} $(date '+%F %T') ==="
done
echo "=== LANE DONE lora $(date '+%F %T') ==="
