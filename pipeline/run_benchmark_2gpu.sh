#!/bin/bash
# evo2_1b_base 双卡分流驱动 (2026-10-18)
# 用法: bash run_benchmark_2gpu.sh <模型名> [类别优先序]
# 行为: GPU0 跑 full 模式 (seeds 42/43/44), GPU1 跑 lora 模式 (seeds 42/43/44)
#       两个独立单进程各占一卡 —— 保留 OOM 自动降级 (torchrun 多卡会禁用该兜底,
#       且 effective_batch_size 会被摊薄, RUNBOOK 2.1 标注本机未实测)。
#       error log 按 lane 分流 (依赖 run_finetune.py 的 DNALLM_ERROR_LOG_TAG):
#         logs/{模型}_gpu0_full_error_log.txt  /  logs/{模型}_gpu1_lora_error_log.txt
# 断点续跑: 同 run_benchmark.sh, 已完成 cell (trainer_state.json) 自动跳过。
set -u
MODEL="${1:?用法: bash run_benchmark_2gpu.sh <模型名> [类别优先序, 如 Plants]}"
ORDER_ARG=""
if [[ -n "${2:-}" ]]; then ORDER_ARG="--category_order $2"; fi

source /root/miniconda3/etc/profile.d/conda.sh
conda activate dnallm

mkdir -p logs

run_lane() {
  local GPU="$1" MODE="$2" TAG="$3" EXTRA="$4"
  local LOG="logs/formal_${MODEL}_${MODE}_gpu${GPU}_$(date +%m%d_%H%M).log"
  echo "=== LANE START gpu=$GPU mode=$MODE log=$LOG $(date '+%F %T') ==="
  for seed in 42 43 44; do
    echo "=== CELL START $MODEL | $MODE | seed $seed | gpu $GPU $(date '+%F %T') ==="
    CUDA_VISIBLE_DEVICES="$GPU" DNALLM_ERROR_LOG_TAG="$TAG" \
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
        $EXTRA 2>&1 | tee -a "$LOG"
    echo "=== CELL EXIT  $MODEL | $MODE | seed $seed | gpu $GPU code=${PIPESTATUS[0]} $(date '+%F %T') ==="
  done
  echo "=== LANE DONE gpu=$GPU mode=$MODE $(date '+%F %T') ==="
}

# GPU0: full (重负载, 磁盘大头)  |  GPU1: lora (轻负载, 落盘小)
run_lane 0 full _gpu0_full "" &
PID_FULL=$!
run_lane 1 lora _gpu1_lora "--peft lora" &
PID_LORA=$!

wait $PID_FULL $PID_LORA
echo "=== BENCHMARK DONE $MODEL (2gpu) $(date '+%F %T') ==="
