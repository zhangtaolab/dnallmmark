#!/bin/bash
# Per-GPU benchmark driver: one cell (mode x seed) at a time on one GPU.
# Usage: bash run_benchmark_gpu.sh <gpu_id> <mode:seed> [mode:seed ...]
# Example: bash run_benchmark_gpu.sh 1 lora:42 lora:43 probe:42 probe:43
set -u

GPU="${1:?用法: bash run_benchmark_gpu.sh <gpu_id> <mode:seed> [...]}"
shift
MODEL="${MODEL:-GENERanno-eukaryote-0.5b-base}"
GPU_MEMORY="${GPU_MEMORY:-24}"

source /root/miniconda3/etc/profile.d/conda.sh
conda activate dnallm

export CUDA_VISIBLE_DEVICES="$GPU"
mkdir -p logs
CANON="logs/${MODEL}_error_log.txt"
touch "$CANON"

for cell in "$@"; do
  mode="${cell%%:*}"
  seed="${cell##*:}"
  extra=""
  [ "$mode" = "lora" ] && extra="--peft lora"
  [ "$mode" = "probe" ] && extra="--config-variant probe"
  # One error log per cell: the driver runs each cell in its own process,
  # and the default "w" open would otherwise truncate the previous cell's
  # errors (both GPUs are rank 0).
  export DNALLM_ERROR_LOG_SUFFIX="_${mode}_s${seed}"
  LOG="logs/formal_${MODEL}_${mode}_seed${seed}_$(date +%m%d_%H%M).log"
  echo "=== CELL START gpu=$GPU model=$MODEL mode=$mode seed=$seed log=$LOG $(date '+%F %T') ===" | tee -a "$LOG"
  python run_finetune.py \
    --seed "$seed" \
    --target_model "$MODEL" \
    --batch_size 16 \
    --auto_batch_size \
    --effective_batch_size 16 \
    --gpu_memory "$GPU_MEMORY" \
    --remove_pt \
    --remove_checkpoints \
    --subset_file eval_subsets.json \
    --category_order Plants \
    $extra 2>&1 | tee -a "$LOG"
  echo "=== CELL EXIT  gpu=$GPU model=$MODEL mode=$mode seed=$seed code=${PIPESTATUS[0]} $(date '+%F %T') ===" | tee -a "$LOG"
  CELL_ERR="logs/${MODEL}${DNALLM_ERROR_LOG_SUFFIX}_error_log.txt"
  if [ -s "$CELL_ERR" ]; then
    { echo "=== $mode seed $seed ==="; cat "$CELL_ERR"; } >> "$CANON"
  fi
done
echo "=== GPU DONE gpu=$GPU model=$MODEL $(date '+%F %T') ==="
