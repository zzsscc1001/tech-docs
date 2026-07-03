# Dual Phase Boost 迭代计算模型

这是一个用于高精度计算 **双相交错 (Dual Phase) Boost 变换器** 稳态工作点、损耗分布及输出纹波的理论与工程计算项目。

## 🎯 项目目标

建立一个无需依赖昂贵且耗时的电路仿真（SPICE），仅通过基础物理参数即可快速、准确预估 Boost 变换器性能的数学模型。
模型采用 **自洽迭代算法 ($\eta$ 预设 + KCL 反推)**，有效克服了传统伏秒平衡法在考虑非理想寄生参数时的精度问题。

## 📂 目录结构说明

经过系统工程梳理，本项目目录结构如下：

```text
boost_model/
├── README.md                 ← 本项目主说明文档
├── docs/
│   ├── ROADMAP.md            ← 🌟 核心：系统工程路线图与阶段规划
│   ├── LOG.md                ← 开发日志与版本演进记录
│   ├── WRITING_GUIDE.md      ← 文档与代码规范
│   ├── step1_*.md            ← 各阶段理论推导与验证报告
│   └── *_output.txt          ← 验证脚本的控制台输出存档
├── step1e_eta_approach.py    ← 核心计算引擎 (无 Snubber 基础版)
├── step1f_snubber.py         ← 核心计算引擎 (含 RC Snubber 完整版)
└── archive/                  ← 已废弃的探索分支 (如伏秒平衡法)
```

> **注**：双相交错的时序理论推导目前在仓库根目录的 `dp_boost_theo_temp/` 下进行，待推导完成后将合并至本目录。

## 🚀 核心技术突破

1. **抛弃理想伏秒平衡**：在考虑 $R_{ds(on)}$ 和 DCR 时，伏秒平衡会导致占空比 $D$ 产生较大误差。
2. **KCL 反推占空比**：通过预设效率 $\eta$ 算出输入电流，再由 KCL ($I_{out} = (1-D)I_L$) 精确反推 $D$。
3. **自洽迭代循环**：$\eta \rightarrow I_L \rightarrow D \rightarrow \Delta I_L \rightarrow P_{loss} \rightarrow \eta_{new}$，循环至收敛。
4. **高精度验证**：单相稳态模型与 SPICE 仿真对比，关键电流参数误差 **< 0.5%**。

## 🗺️ 路线图 (Roadmap)

请参阅 [`docs/ROADMAP.md`](docs/ROADMAP.md) 了解项目的完整四个阶段：
1. 单相基础稳态模型 (已完成 ✅)
2. 双相交错时序理论推导 (进行中 🔄)
3. 双相交错迭代计算模型整合 (TODO)
4. 高级特性与小信号模型 (TODO)

## 🛠️ 快速开始

运行当前最完整的单相损耗计算模型（包含 Vf, DCR, Rds, RC Snubber）：

```bash
python3 step1f_snubber.py
```

这将输出完整的稳态工作点、RMS 电流、各部分损耗占比，并与无 Snubber 情况进行对比。
