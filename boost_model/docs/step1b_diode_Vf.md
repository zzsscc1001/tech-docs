# Step 1b: 二极管压降 Vf 对 Boost 稳态的影响

> **状态**: ✅ 已完成 | 被 Step 1e 取代 | $V_f$ 修正公式仍被后续步骤继承，仅作历史参考

## 核心区别

```
理想:   Toff 期间 VL = Vin - Vout
含 Vf:  Toff 期间 VL = Vin - Vout - Vf   ← 二极管压降叠加到输出
```

Toff 期间，电感看到的"等效输出电压"变为 **(Vout + Vf)**。

## 公式推导

### 1. 占空比

伏秒平衡：Vin·D + (Vin − Vout − Vf)·(1−D) = 0

整理：Vin = (Vout + Vf)·(1−D)

$$\boxed{D = 1 - \frac{V_{in}}{V_{out} + V_f}}$$

> Vf > 0 → D 增大。Toff 期间去磁更慢，需要更长的 Ton 来维持平衡。

### 2. 电感平均电流

输出 KCL 不变：Iout = (1−D) × IL_avg

代入 (1−D) = Vin/(Vout+Vf)：

$$\boxed{I_{L,avg} = \frac{I_{out} \cdot (V_{out} + V_f)}{V_{in}}}$$

功率验证：

```
Pin  = Vin × IL_avg = Iout × (Vout + Vf)
Pout = Vout × Iout
P_diode = Vf × Iout
Pin = Pout + P_diode ✓
```

### 3. 电感纹波

公式形式不变（Ton 期间 Vf 不参与）：

$$\Delta I_L = \frac{V_{in} \cdot D}{L \cdot f_{sw}}$$

D 增大 → ΔIL 数值增大。

### 4. 临界电感

从 IL_avg = ΔIL/2 推导：

$$\boxed{L_{crit} = \frac{V_{in}^2 \cdot (V_{out}+V_f-V_{in})}{2 \cdot (V_{out}+V_f)^2 \cdot I_{out} \cdot f_{sw}}}$$

> 当 Vf=0 时退化为理想公式。Vf > 0 时 Lcrit 略微减小（CCM 更容易维持）。

### 5. 器件应力

公式形式不变，但 IL_avg 和 D 变了，数值随之变化：

```
IQ_rms = √[D × (IL_avg² + ΔIL²/12)]
ID_rms = √[(1-D) × (IL_avg² + ΔIL²/12)]
IC_rms = √[ID_rms² - Iout²]
```

### 6. 效率

$$\boxed{\eta = \frac{V_{out}}{V_{out} + V_f}}$$

Vf=0.7V 时 η ≈ 97.7%（仅二极管损耗，不含开关损耗、铜损等）。

## 数值对比

Vin=9V, Vout=30V, L=10µH, fsw=400kHz, Iout=0.5A, Vf=0.7V

| 参数 | 理想 | 含 Vf | 变化 |
|------|------|-------|------|
| D | 0.7000 | 0.7068 | +0.0068 |
| IL_avg | 1.6667 A | 1.7056 A | +2.3% |
| ΔIL | 1.5750 A | 1.5904 A | +1.0% |
| IL_peak | 2.4542 A | 2.5008 A | +1.9% |
| Lcrit | 4.725 µH | 4.66 µH | −1.4% |
| Pin | 15.000 W | 15.350 W | +2.3% |
| P_diode | 0 | 0.350 W | — |
| η | 100% | 97.72% | −2.3% |

## 一致性验证

- ✅ 功率平衡：Pin = Pout + P_diode
- ✅ KCL：IL_avg = Iout/(1−D) 与功率法一致
- ✅ 伏秒平衡：Vin·D + (Vin−Vout−Vf)·(1−D) = 0
- ✅ Lcrit 自洽：代入 Lcrit → IL_valley = 0

---

*代码: `step1b_diode_Vf.py`*
*状态: ✅ 公式推导 + 四项一致性验证通过*
