# Dual Phase Boost 计算模型 — 开发日志

## 项目信息

- **目标**: 建立 dual phase boost 计算模型，公式+代码+仿真三方验证
- **仿真工具**: 用户自建仿真模型
- **验证基准**: Vin=9V, Vout=30V, L=10µH, fsw=400kHz, Iout=0.5A (单相)

## 文件结构

```
boost_model/
├── LOG.md                          ← 本文件
├── WRITING_GUIDE.md                ← 写作规范
├── step1_steady_state.py           ← Step 1: 理想 CCM 公式 ✅
├── step1b_diode_Vf.py              ← Step 1b: 加 Vf ✅
├── step1e_eta_approach.py          ← Step 1e: η预设+KCL反推 (基础模型) ✅
├── step1f_snubber.py               ← Step 1f: +RC Snubber 损耗 ✅
├── archive/                        ← 已废弃的探索文件
│   ├── step1c_eta_model.py         ← 伏秒法(不准确)
│   ├── step1d_full_losses.py       ← 伏秒法(不准确)
│   ├── step1c_eta_model_output.txt
│   └── step1d_full_losses_output.txt
└── docs/
    ├── step1_steady_state.md
    ├── step1b_diode_Vf.md
    ├── step1e_eta_approach_output.txt
    ├── step1f_snubber.md
    ├── step1f_snubber_output.txt
    └── debug_current_status.md
```

## 开发历程

### Step 1: 理想 CCM 稳态 (2026-05-29) ✅

**内容**: 建立理想 Boost 公式体系 (9 个公式)

**关键公式**:
- D = 1 - Vin/Vout
- IL_avg = Iout/(1-D)
- ΔIL = Vin·D/(L·fsw)

**验证**: ✅ 数值计算正确，仿真完全一致

---

### Step 1b: 加入二极管压降 Vf (2026-05-29) ✅

**内容**: Vf 影响 Toff 期间电感电压

**关键修正**:
- D = 1 - Vin/(Vout+Vf)
- IL_avg = Iout·(Vout+Vf)/Vin

**验证**: ✅ 四项一致性验证通过，仿真误差 <0.1%

---

### Step 1c/1d: 伏秒平衡法 (2026-05-29) ❌ 已废弃

**尝试**: 用伏秒平衡求 D

**问题**: 伏秒平衡在仿真中不完全成立 (开关过渡过程)

**教训**: **D 不应从伏秒平衡算，应从 KCL 反推**

---

### Step 1e: η 预设 + KCL 反推 (2026-05-29) ✅ 当前基础模型

**方法**: 不用伏秒平衡，改用 KCL 反推 D

**迭代流程**:
```
η (预设) → IL_avg → D (KCL) → ΔIL (含R) → 损耗 → η_new → 循环
```

**关键发现**:
1. D 从 KCL 反推比伏秒平衡准确得多
2. ΔIL 考虑 Rds+DCR 压降后降低 12.8%

**仿真对比**:
| 参数 | 模型 | 仿真 | 误差 |
|------|------|------|------|
| D | 0.7402 | 0.7398 | +0.05% |
| IL_peak | 2.651A | 2.648A | +0.10% |
| IL_avg | 1.925A | 1.933A | -0.42% |

---

### Step 1f: 加入 RC Snubber 损耗 (2026-06-03) ✅

**内容**: 在 step1e 基础上增加 RC snubber 损耗

**Snubber 公式**:
```
E_off = 0.5 × C × ((Vout+Vf)² - (IL_peak×Rds)²)
E_on  = 0.5 × C × ((Vout+Vf)² - (IL_valley×Rds)²)
P_snub = (E_on + E_off) × fsw
```

**结果**: Snubber 占总损耗 ~7% (0.19W / 2.57W)

**问题**: 与仿真误差 ~27%，可能需要考虑开关过渡时间

---

## 当前模型能力

| 损耗项 | Step 1e | Step 1f |
|--------|---------|---------|
| Vf | ✅ | ✅ |
| DCR | ✅ | ✅ |
| Rds | ✅ | ✅ |
| RC Snubber | ❌ | ✅ |
| 开关损耗 | ❌ | ❌ (TODO) |

## 下一步

- [ ] Snubber 模型优化 (减小 27% 误差)
- [ ] 双相交错模型 (两相 180° 交错)
- [ ] 纹波抵消分析
- [ ] 输出电容纹波电压
- [ ] 小信号建模 (Gvd, 电流环/电压环)
