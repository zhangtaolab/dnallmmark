#!/bin/bash
# DNABERT-Bench 单模型全量 benchmark 驱动脚本
# 用法: bash run_benchmark.sh <注册表模型名>   例: bash run_benchmark.sh DNABERT-2-117M
# 行为: 该模型 × 全部 50 个数据集 × {full, lora, probe} × seeds {42,43,44}
#       断点续跑: 已完成的 cell (存在 trainer_state.json) 自动跳过, 中断后重跑本命令即可
set -u
MODEL="${1:?用法: bash run_benchmark.sh <模型名> [类别优先序, 如 Plants 或 Plants,Microbe]   例: bash run_benchmark.sh DNABERT-2-117M Plants}"
# 可选第二参数: --category_order (指定类先跑, 其余照跑; 不传则按注册表原序)
ORDER_ARG=""
if [[ -n "${2:-}" ]]; then ORDER_ARG="--category_order $2"; fi

source /root/miniconda3/etc/profile.d/conda.sh
conda activate dnallm

mkdir -p logs
LOG="logs/formal_${MODEL}_$(date +%m%d_%H%M).log"
echo "=== BENCHMARK START model=$MODEL log=$LOG $(date '+%F %T') ==="

for mode in full lora probe; do
  # evo2 系列不支持 probe (suite 硬拒绝), 跳过
  if [[ "$MODEL" == evo2_* && "$mode" == "probe" ]]; then
    echo "=== SKIP $MODEL probe (not supported) ==="
    continue
  fi
  for seed in 42 43 44; do
    extra=""
    [ "$mode" = "lora" ] && extra="--peft lora"
    [ "$mode" = "probe" ] && extra="--config-variant probe"
    echo "=== CELL START $MODEL | $mode | seed $seed $(date '+%F %T') ==="
    python run_finetune.py \
      --seed "$seed" \
      --target_model "$MODEL" \
      --batch_size 16 \
      --auto_batch_size \
      --effective_batch_size 16 \
      --remove_pt \
      --remove_checkpoints \
      --subset_file eval_subsets.json \
      $ORDER_ARG \
      $extra 2>&1 | tee -a "$LOG"
    echo "=== CELL EXIT  $MODEL | $mode | seed $seed code=${PIPESTATUS[0]} $(date '+%F %T') ==="
  done
done
echo "=== BENCHMARK DONE $MODEL $(date '+%F %T') ==="
