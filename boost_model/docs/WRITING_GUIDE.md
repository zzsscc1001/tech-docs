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

## 目录结构

```
boost_model/
├── LOG.md              ← 开发日志 (必须更新)
├── WRITING_GUIDE.md    ← 本文件
├── step*.py            ← 当前有效代码
├── docs/
│   ├── step*.md        ← 理论文档
│   └── step*_output.txt← 运行输出
└── archive/            ← 废弃文件
```
