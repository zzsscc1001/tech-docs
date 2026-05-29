# Dual Phase Boost 计算模型 — 开发日志

## 项目信息

- **目标**: 建立 dual phase boost 计算模型，公式+代码+仿真三方验证
- **仿真工具**: 用户自建仿真模型
- **验证基准**: Vin=9V, Vout=30V, L=10µH, fsw=400kHz, Iout=0.5A (单相)

## 文件结构

```
boost_model/
├── LOG.md                          ← 本文件
├── step1_steady_state.py           ← Step 1: 理想 CCM 公式
├── step1b_diode_Vf.py              ← Step 1b: 加 Vf (解析)
├── step1c_eta_model.py             ← Step 1c: Vf+DCR 迭代 (已废弃)
├── step1d_full_losses.py           ← Step 1d: Vf+DCR+Rds (伏秒法，已废弃)
├── step1e_eta_approach.py          ← Step 1e: η预设+KCL反推 (当前最佳)
└── docs/
    ├── step1_steady_state.md       ← Step 1 理论文档
    ├── step1b_diode_Vf.md          ← Step 1b 理论文档
    ├── debug_current_status.md     ← Debug 文档
    ├── step1_output.txt            ← Step 1 输出 (带时间戳)
    ├── step1b_output.txt           ← Step 1b 输出
    ├── step1c_output.txt           ← Step 1c 输出
    ├── step1d_output.txt           ← Step 1d 输出
    └── step1e_output.txt           ← Step 1e 输出
```

## 开发历程

### Step 1: 理想 CCM 稳态 (2026-05-29)

**内容**: 建立理想 Boost 公式体系 (9 个公式)

**公式**:
- D = 1 - Vin/Vout
- IL_avg = Iout/(1-D)
- ΔIL = Vin·D/(L·fsw)
- Lcrit = Vin²(Vout-Vin)/(2·Vout²·Iout·fsw)
- IQ_rms = √(D·(IL²+ΔIL²/12))
- 等等

**验证**: ✅ 数值计算正确

**关键修正**: Lcrit 公式 v1 有误 (少了一个 Vout)，v2 已修正

**仿真**: ✅ 完全一致 (imax 2.45A, ipp 1.58A)

---

### Step 1b: 加入二极管压降 Vf (2026-05-29)

**内容**: Vf 影响 Toff 期间电感电压

**公式变化**:
- D = 1 - Vin/(Vout+f)  (Vf 使 D 增大)
- IL_avg = Iout·(Vout+Vf)/Vin  (Vf 使 IL 增大)
- η = Vout/(Vout+Vf)  (Vf 降低效率)

**验证**: ✅ 四项一致性验证通过 (功率/KCL/伏秒/Lcrit)

**仿真**: ✅ imax=2.501A (模型 2.501A), ipp=1.590A (模型 1.590A)

---

### Step 1c: Vf+DCR 模型 (2026-05-29) — 已废弃

**尝试**: 用伏秒平衡+KCL 联立求解 D 和 IL_avg

**问题**: 伏秒平衡在仿真中不完全成立 (开关过渡过程)

**教训**: D 不应从伏秒平衡算，应从 KCL 反推

---

### Step 1d: Vf+DCR+Rds 伏秒法 (2026-05-29) — 已废弃

**尝试**: 加入 Rds_on，用伏秒平衡求 D

**问题**: 与仿真差距 3.5% (伏秒平衡在仿真中不准确)

**教训**: 伏秒平衡假设理想开关波形，实际仿真有过渡过程

---

### Step 1e: η 预设 + KCL 反推 (2026-05-29) — 当前最佳 ✅

**方法**: 不用伏秒平衡，改用 KCL 反推 D

**迭代流程**:
```
η (预设) → IL_avg = Vout·Iout/(η·Vin)
  → D = 1 - Iout/IL_avg  (KCL)
  → ΔIL = (Vin - IL_avg·(Rds+DCR))·D/(L·fsw)  (含电阻修正)
  → IQ_rms, ID_rms (三角波 RMS)
  → P_MOS, P_DCR, P_diode (损耗)
  → η_new = Pout/(Pout+P_sum)
  → 循环直到 η 收敛
```

**关键发现**:
1. D 从 KCL 反推比伏秒平衡准确得多
2. ΔIL 考虑 Rds+DCR 压降后降低 12.8% (1.59A → 1.45A)
3. 迭代 13 步收敛

**仿真对比**:
| 参数 | 模型 | 仿真 | 误差 |
|------|------|------|------|
| D | 0.7402 | 0.7398 | +0.05% |
| IL_peak | 2.651A | 2.648A | +0.10% |
| IL_avg | 1.925A | 1.933A | -0.42% |
| IL_valley | 1.199A | 1.199A | -0.01% |

---

## 下一步

- [ ] 双相交错模型 (两相 180° 交错)
- [ ] 纹波抵消分析
- [ ] 输出电容纹波电压
- [ ] 小信号建模 (Gvd, 电流环/电压环)
