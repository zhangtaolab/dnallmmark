#!/bin/bash
# 清理 lora 已完成 cell 的冗余 pytorch_model.bin (4.2G/个)
# 该文件是 PeftModel 的全量合并 state_dict = models/evo2_1b_base + adapter_model.safetensors,
# 完全冗余; 只删带 trainer_state.json 完成标记的 cell, 避免碰在跑的 cell。
cd /root/autodl-tmp/dnallmmark/pipeline || exit 1
while true; do
  find finetuned/evo2_1b_base+lora -name pytorch_model.bin 2>/dev/null | while read -r f; do
    d=$(dirname "$f")
    if [ -f "$d/trainer_state.json" ]; then
      rm -f "$f" && echo "[clean] removed $f $(date '+%F %T')"
    fi
  done
  sleep 600
done
