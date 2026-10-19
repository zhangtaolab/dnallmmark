#!/bin/bash
# evo2_1b_base full lane 续跑 (GPU0) — mem_ratio 跳过恢复修复后重启
# 与 run_benchmark_2gpu.sh 的 full lane 同参数; 断点续跑 (trainer_state.json) 自动跳过
set -u
source /root/miniconda3/etc/profile.d/conda.sh
conda activate dnallm
cd /root/autodl-tmp/dnallmmark/pipeline
LOG="logs/formal_evo2_1b_base_full_gpu0_$(date +%m%d_%H%M).log"
export CUDA_VISIBLE_DEVICES=0 DNALLM_ERROR_LOG_TAG=_gpu0_full
for seed in 42 43 44; do
  echo "=== CELL START evo2_1b_base | full | seed $seed | gpu 0 $(date '+%F %T') ==="
  python run_finetune.py \
    --seed "$seed" \
    --target_model evo2_1b_base \
    --batch_size 16 \
    --auto_batch_size \
    --effective_batch_size 16 \
    --remove_pt \
    --remove_checkpoints \
    --subset_file eval_subsets.json \
    --category_order Plants 2>&1 | tee -a "$LOG"
  echo "=== CELL EXIT  evo2_1b_base | full | seed $seed | gpu 0 code=${PIPESTATUS[0]} $(date '+%F %T') ==="
done
echo "=== LANE DONE full $(date '+%F %T') ==="
