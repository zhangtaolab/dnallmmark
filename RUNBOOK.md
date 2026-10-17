# DNALLM-Mark Benchmark 多机跑批手册（RUNBOOK）

## 一、任务是什么

**对指定的一个 DNA 大模型做全量 benchmark 微调评测**：

- 矩阵：`1 个模型 × 50 个数据集 × 3 种微调方式 × 3 个随机种子 = 450 个训练 cell`
  - 微调方式：`full`（全量微调）、`lora`（LoRA 微调）、`probe`（冻结骨干只训 head）
  - 种子：42 / 43 / 44
- 每个数据集按注册表 `pipeline/datasets_info.json` 的配置训练（3 epochs，dev 指标选最优 checkpoint，test 出最终指标）
- 产出：每个 cell 一套测试指标（f1 / AUROC / mcc / ...，按数据集定）+ 最优模型权重
- 最终汇总是实验室层面做的事，单机只管把 450 个 cell 跑完、指标落盘正确

**验收标准**（每个 cell）：
1. `finetuned/{模型}[+lora|+probe]/{数据集}/seed_{seed}/` 下四个 json 齐全：
   `test_metrics.json`、`eval_test_result.json`（两者数值应一致）、`final_metrics.json`、`trainer_state.json`
2. 目录内**无** `checkpoint-*` 残留（最优权重已在目录根部 `model.safetensors`）
3. `logs/{模型}_error_log.txt` 无该 cell 的报错

## 二、怎么跑（就一条命令）

```bash
cd /root/autodl-tmp/dnallmmark/pipeline
bash run_benchmark.sh DNABERT-2-117M          # <<< 换成你分到的模型名，见第四节
```

后台运行 + 看进度：

```bash
nohup bash run_benchmark.sh DNABERT-2-117M > logs/driver.log 2>&1 &
tail -f logs/formal_DNABERT-2-117M_*.log      # 训练进度
grep -c "CELL EXIT" logs/formal_*.log         # 已完成 cell 数（目标 450）
ls finetuned/DNABERT-2-117M*/                 # 产出目录
```

脚本行为：
- 自动顺序跑 3 模式 × 3 seeds，每个 seed 进程内遍历全部 50 个数据集
- **断点续跑**：中断后重新执行同一条命令即可，已完成的 cell 自动跳过
- evo2 系列自动跳过 probe（suite 硬性不支持）
- 耗时参考（RTX 5090 32G）：DNABERT-2 全程约 3-5 天；PlantHelixSeek 约 30-40 天（慢 10 倍，慎排）

### 2.1 显存策略（2026-10-17 更新，实测验证）

`run_finetune.py` 默认 `--mem_ratio` 已从 0.70 **改为 0.95**，并新增 **OOM 自动降级**：
训练/评估/Trainer 构造中发生 CUDA OOM 时，活动 mem_ratio 自动以 **0.05 步进下降**（下限 0.50），
并**重试同一数据集**（清空缓存、清除残留 checkpoint 与完成标记、按新比例重估 batch、重载模型）。
降到 0.50 仍 OOM 才走原错误日志路径跳过该数据集。降档过程记录在 stdout 与 `logs/{模型}_error_log.txt`。

实测（RTX 5090, PlantCAD2-Medium-l48-d1024, GUE__emp_H3, full 模式）：
- mem_ratio 0.70 → batch 5×3，6.8 样本/s（GPU 利用率 31%）
- mem_ratio 0.80 → batch 7×2，9.4 样本/s
- mem_ratio 0.95 → batch 11×1，**10.0 样本/s（+47%）**，GPU 利用率 57%，实测显存 28.9/32GB
- 强制 OOM 测试（`--gpu_memory 40` 谎报显存）：batch16→OOM→0.90→OOM→0.85→OOM→0.80→batch13 训练成功，重试周转秒级

多卡 torchrun 约定（2026-10-17 加固，本机单卡未实测）：
- error_log 按 rank 分流：rank 0 独占 `{模型}_error_log.txt`（验收产物），非零 rank 写 `{模型}_error_log_rank{N}.txt`
- OOM 自动降级**仅单进程生效**；`WORLD_SIZE>1` 下检测到 CUDA OOM 会快速失败并提示降低 `--mem_ratio`（单边重试/跳过会使其他 rank 死锁在 NCCL 集合通信）
- 注意 `--effective_batch_size 16` 为全局协议值，多卡会摊薄每卡 batch、重新引入 kernel-launch 瓶颈；多卡需谨慎评估协议变更

验证通过的命令（默认即 0.95，无需显式传参）：

```bash
cd /root/autodl-tmp/dnallmmark/pipeline
# 正式任务（自动使用新默认值与 OOM 自动降级）
nohup bash run_benchmark.sh PlantCAD2-Medium-l48-d1024 > logs/driver.log 2>&1 &
# 植物类数据集优先（可选第二参数，其余类照跑、只影响顺序）
nohup bash run_benchmark.sh PlantCAD2-Medium-l48-d1024 Plants > logs/driver.log 2>&1 &
# 单测命令（2026-10-17 实测通过：batch 11, ~10 样本/s, 无 OOM）
python run_finetune.py --seed 42 --target_model PlantCAD2-Medium-l48-d1024 \
  --target_dataset GUE__emp_H3 --batch_size 16 --auto_batch_size \
  --effective_batch_size 16 --output_dir ./tmp_bench
```

## 三、跑之前的一次性准备（新机器必做）

### 3.1 拷贝代码与数据

```bash
mkdir -p ~/autodl-tmp/dnallmmark && cp -r ~/dnallmmark/. ~/autodl-tmp/dnallmmark/
cd ~/autodl-tmp/dnallmmark/pipeline && mkdir -p models datasets
cp -r ~/autodl-fs/datasets/* datasets/                      # 全量数据 2.6G
for m in <你分到的模型目录名>; do cp -r ~/autodl-fs/models/$m models/; done
```

**目录名注意（不改文件夹，改注册表）**：
- PlantHelixSeek → 改 `models_info.json`：`"Model_path": "models/PlantHelixSeek"`
- mamba2_370M_Allplant → 注册表名是 `mamba2_plant_genome`，改 `"Model_path": "models/mamba2_370M_Allplant"`

### 3.2 代码修复状态（先拉最新代码）

```bash
git pull   # dnallmmark@dev 与 DNALLM@v1.3 的修复已于 2026-10-17 推送
```

已推送、拉取即得的修复：
- `dnallmmark`：run_finetune.py（test 指标保存、checkpoint 全删磁盘策略、evo2 bf16、dry-run 防御）、models_info.json 路径
- `DNALLM`：lora_targets.yaml（PlantBiMoE 新增、DNABERT-2/EVO-2 修正）、special/evo.py（evo2 可训练性五连修）

**还需手动做的两处**（模型目录内文件，不在 git 里）：
1. 跑 DNABERT-2 时：
   - `models/DNABERT-2-117M/config.json` 加 `"pad_token_id": 3`
   - `models/DNABERT-2-117M/bert_layers.py` 的 `rebuild_alibi_tensor` 计算体包一层
     `with torch.device("cpu" if device is None else device):`（transformers 5.x 兼容）
   - 改完删缓存：`rm -rf /root/.cache/huggingface/modules/transformers_modules/DNABERT_*`
2. 跑 evo2 时：
   - `pip install evo2 vtx biopython --no-deps`（必须 --no-deps，防止改动 torch/transformers）

### 3.3 跑前 5 分钟自检（强烈建议）

```bash
cd /root/autodl-tmp/dnallmmark/pipeline
# LoRA 目标模块验证（应打印 preset selected + N modules matched，无报错）
python run_finetune.py --seed 42 --target_model <模型名> --target_dataset GUE__emp_H3 \
  --peft lora --peft_dry_run --output_dir ./tmp_check
rm -rf tmp_check
```

## 四、模型分派与状态（2026-10-17 实测）

| 模型（run_benchmark.sh 用这个名字） | 共享盘目录名 | 状态 |
|---|---|---|
| DNABERT-2-117M | 同名 | ✅ 3 模式全验证（需 3.2 手动两处修复） |
| PlantHelixSeek | PlantHelixSeek | ✅ 3 模式全验证（需改注册表路径） |
| PlantBiMoE | 同名 | ✅ 加载+LoRA 验证 |
| PlantCAD2-Small-l24-d0768 | 同名 | ✅ 加载+LoRA 验证 |
| PlantCAD2-Medium-l48-d1024 | 同名 | ✅ 加载+LoRA 验证 |
| nucleotide-transformer-v2-500m-multi-species | 同名 | ✅ 加载+LoRA 验证 |
| mamba2_plant_genome | mamba2_370M_Allplant | ✅ 加载+LoRA 验证（需改注册表路径） |
| plant-genomic-jamba | 同名 | ✅ 加载+LoRA 验证 |
| evo2_1b_base | 同名 | ✅ full+LoRA 验证（probe 自动跳过；需装 evo2；**训练峰值磁盘约 120G、每 cell 落盘 4.2G**） |
| PlantGFM | 同名 | ❌ 共享盘缺 `configuration_plantgfm.py`，等补文件 |

## 五、报错速查

| 现象 | 原因/处理 |
|---|---|
| `BertConfig has no attribute pad_token_id` | 3.2 手动修复第 1 条 |
| `Tensor on device meta ...` | 同上（bert_layers.py），并删 HF 远程代码缓存 |
| `No PEFT target-module preset / NoMatchingPeftModuleError` | 代码没拉到最新（DNALLM@v1.3） |
| `Tried to access the schema ... INTERNAL ASSERT`（evo2） | 代码没拉到最新（special/evo.py 导入顺序守卫） |
| `Inference tensors cannot be saved for backward`（evo2） | 同上 |
| 指标接近随机、训练却飞快（evo2） | 同上（骨干未参与训练的修复缺失） |
| 首个数据集（BEND CpG）极慢 | 缺 `--batch_size 16`（用 run_benchmark.sh 不会发生） |
| 磁盘告急 | 确认用了 run_benchmark.sh（带 --remove_checkpoints）；evo2 见第四节磁盘提示 |
