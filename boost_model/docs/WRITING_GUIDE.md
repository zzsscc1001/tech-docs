# Dual Phase Boost 模型 — 写作规范

## 文件命名

```
step{N}_{description}.py      ← 代码
docs/step{N}_{description}.md ← 理论文档
docs/step{N}_output.txt       ← 运行输出 (带时间戳)
```

**示例**:
- `step1e_eta_approach.py`
- `docs/step1e_eta_approach.md`

## 代码规范

### 1. Docstring 格式
```python
"""
Step 1e: η 预设 + KCL 反推
============================
在 step1b 基础上加入 DCR + Rds_on 损耗
方法: η 预设 → IL_avg → D (KCL) → ΔIL → 损耗 → η_new → 迭代

参数:
  Vin = 9V, Vout = 30V, L = 10µH, fsw = 400kHz, Iout = 0.5A
"""
```

### 2. 函数签名
```python
def boost_model_name(Vin, Vout, Iout, L, fsw, Vf, DCR, Rds,
                     tol=1e-8, max_iter=100, verbose=False):
    """
    返回:
      dict: {D, IL_avg, dIL, IL_peak, IL_valley, IQ_rms, ID_rms,
             Pin, Pout, eta, P_MOS, P_diode, P_DCR, P_sum, ...}
    """
```

### 3. 验证块
```python
if __name__ == "__main__":
    # 参数
    Vin, Vout, L, fsw, Iout = 9.0, 30.0, 10e-6, 400e3, 0.5
    Vf, DCR, Rds = 0.7, 0.3, 0.3

    # 运行
    r = boost_model_name(...)

    # 输出 (英文，避免字体问题)
    print(f"D = {r['D']:.6f}")
    print(f"IL_avg = {r['IL_avg']:.4f} A")
    # ...
```

### 4. 输出语言
- **所有 print 用英文** (公司电脑可能缺中文字体)
- **注释用中文**

## 文档规范

### 1. 结构
```markdown
# Step 1e: η 预设 + KCL 反推

## 模型概述
[一段话描述]

## 迭代流程
```
η → IL_avg → D → ΔIL → 损耗 → η_new
```

## 公式推导
[关键公式]

## 仿真对比
| 参数 | 模型 | 仿真 | 误差 |
|------|------|------|------|

## 关键发现
1. ...
2. ...

## 问题 / TODO
- ...
```

### 2. 公式格式
- 简单公式: 行内 `D = 1 - Vin/Vout`
- 复杂公式: 代码块
```
ΔIL = (Vin - IL_avg × (Rds + DCR)) × D / (L × fsw)
```

### 3. 仿真对比表格
必须包含: 模型值、仿真值、误差百分比

## LOG.md 更新规范

每个新 Step 完成后，在 `docs/LOG.md` 添加:

```markdown
### Step 1x: 标题 (日期) ✅/❌

**内容**: 一句话描述

**关键发现**:
1. ...

**仿真对比**:
| 参数 | 模型 | 仿真 | 误差 |

**问题**: (如有)
```

## 废弃文件处理

1. 移动到 `archive/` 文件夹
2. 在 LOG.md 标注 `❌ 已废弃`
3. 记录废弃原因和教训

## 文档层级与维护责任

本项目的文档分为三个层级，各自有不同的更新频率和维护责任：

| 文件 | 层级 | 更新时机 | 维护规则 |
|------|------|----------|----------|
| `docs/ROADMAP.md` | 战略层 | 每个 Phase 完成后更新一次 | 记录阶段目标、产出物、已知技术债 |
| `docs/LOG.md` | 战术层 | 每个 Step 完成后追加一条 | 只追加，不修改历史记录 |
| `docs/step*.md` | 执行层 | 写完后不再修改 | 是历史快照，忠实记录当时认知 |

> **原则**：执行层文档一旦写完就是历史记录，不要事后修正。如果发现问题，在新的 Step 文档中说明，并在 LOG.md 的「已知问题」区块登记。

## 状态标签规范

每份 `step*.md` 文档的**第一行**（标题下方）必须有一个状态引用块，格式如下：

```markdown
> **状态**: ✅ 已完成 | 被 Step 1f 取代 | 核心算法仍在使用
```

状态字段说明：
- 第一字段：`✅ 已完成` / `❌ 已废弃` / `🔄 进行中`
- 第二字段：与其他 Step 的关系，例如「被 Step 1f 取代」或「在 Step 1e 基础上扩展」
- 第三字段（可选）：补充说明，例如「核心算法仍在使用」或「仅作历史参考」

## 目录结构

```
boost_model/
├── README.md           ← 项目入口说明
├── step*.py            ← 当前有效代码
├── docs/
│   ├── ROADMAP.md      ← 战略层：整体规划与阶段目标
│   ├── LOG.md          ← 战术层：开发日志 (只追加)
│   ├── WRITING_GUIDE.md← 本文件：规范说明
│   ├── step*.md        ← 执行层：各步骤理论文档 (写完不改)
│   └── step*_output.txt← 运行输出存档
└── archive/            ← 废弃文件 (含废弃原因)
```
