# Step 1: 单相 Boost 稳态工作点 — 公式推导

## 1. 占空比 D

**来源：电感伏秒平衡**

Q 导通 (Ton)：VL = Vin（电感充磁，电流线性上升）
Q 关断 (Toff)：VL = Vin − Vout（电感去磁，电流线性下降）

伏秒平衡：Vin·D·T + (Vin−Vout)·(1−D)·T = 0

$$\boxed{D = 1 - \frac{V_{in}}{V_{out}}}$$

## 2. 电感平均电流 IL_avg

**来源：输出节点 KCL（平均值）**

电感电流仅在 (1−D)T 期间通过二极管到达输出：

$$\boxed{I_{L,avg} = \frac{I_{out}}{1-D}}$$

这同时也是输入平均电流（Boost 拓扑中电感 = 输入通路）。

## 3. 电感纹波电流 ΔIL

**来源：Q 导通期间电感伏安关系**

VL = L·di/dt，Q 导通时 VL = Vin：

$$\boxed{\Delta I_L = \frac{V_{in} \cdot D}{L \cdot f_{sw}}}$$

## 4. 峰值/谷值电流

$$I_{L,peak} = I_{L,avg} + \frac{\Delta I_L}{2}$$

$$I_{L,valley} = I_{L,avg} - \frac{\Delta I_L}{2}$$

## 5. CCM 判据

$$\boxed{CCM: \quad I_{L,valley} > 0 \quad \Longleftrightarrow \quad I_{L,avg} > \frac{\Delta I_L}{2}}$$

## 6. 临界电感 Lcrit

**CCM/DCM 边界**：IL_avg = ΔIL/2

左边 = Iout/(1−D)，右边 = Vin·D/(2·L·fsw)

解出 Lcrit：

$$\boxed{L_{crit} = \frac{V_{in} \cdot D \cdot (1-D)}{2 \cdot I_{out} \cdot f_{sw}} = \frac{V_{in}^2 \cdot (V_{out}-V_{in})}{2 \cdot V_{out}^2 \cdot I_{out} \cdot f_{sw}}}$$

判据：L > Lcrit → CCM；L < Lcrit → DCM

> **自洽验证**：代入 L = Lcrit 时，IL_valley 应精确为 0。

## 7. MOSFET 电流有效值

Q 仅在 DT 内导通，电流为三角波（平均 IL_avg，纹波 ΔIL）：

$$\boxed{I_{Q,rms} = \sqrt{D \cdot \left(I_{L,avg}^2 + \frac{\Delta I_L^2}{12}\right)}}$$

近似（纹波小时）：IQ_rms ≈ IL_avg × √D

## 8. 二极管电流有效值 & 平均值

D 仅在 (1−D)T 内导通：

$$I_{D,rms} = \sqrt{(1-D) \cdot \left(I_{L,avg}^2 + \frac{\Delta I_L^2}{12}\right)}$$

$$I_{D,avg} = I_{L,avg} \cdot (1-D) = I_{out}$$

## 9. 输出电容纹波电流

iC(t) = iD(t) − Iout，取 RMS：

$$\boxed{I_{C,rms} = \sqrt{I_{D,rms}^2 - I_{out}^2}}$$

---

## 数值验证代入

Vin=9V, Vout=30V, L=10µH, fsw=400kHz, Iout=0.5A

| 公式 | 计算 | 结果 |
|------|------|------|
| D = 1−Vin/Vout | 1−9/30 | **0.700** |
| IL_avg = Iout/(1−D) | 0.5/0.3 | **1.667 A** |
| ΔIL = Vin·D/(L·fsw) | 9×0.7/(10µ×400k) | **1.575 A** |
| IL_peak | 1.667+0.788 | **2.454 A** |
| IL_valley | 1.667−0.788 | **0.879 A > 0 → CCM** |
| Lcrit | 81×21/(2×900×0.5×400k) | **4.725 µH** |
| L > Lcrit? | 10 > 4.725 | **CCM ✓** |
| IQ_rms | √(0.7×(1.667²+1.575²/12)) | **1.445 A** |
| ID_rms | √(0.3×(1.667²+1.575²/12)) | **0.946 A** |
| IC_rms | √(0.946²−0.5²) | **0.803 A** |
| Pin (理想) | 9×1.667 | **15.0 W** |
| Pout | 30×0.5 | **15.0 W** |

---

## 仿真验证清单

- [ ] 占空比 ≈ 70%
- [ ] IL_avg ≈ 1.67A
- [ ] ΔIL ≈ 1.58A
- [ ] IL_peak ≈ 2.45A
- [ ] IL_valley ≈ 0.88A（>0 确认 CCM）
- [ ] MOSFET Vds ≈ 30V
- [ ] Vout 稳定在 30V

---

*代码: `step1_steady_state.py`*
*状态: ✅ 公式推导 + 数值验证通过，待仿真确认*
