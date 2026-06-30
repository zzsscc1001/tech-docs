# 双相交错 180° Boost — $I_d(t)$ 时域公式

> 继承单相模型（见 `01_single_phase.md`）
> 条件：$D < 0.5$（两相 diode 导通区间不重叠）
> 功率定义：$P_{dp}$ = 双相总功率，$P_{sp} = P_{dp}/2$ = 单相功率

---

## 1. 单相参数

$$I_{L,avg,sp} = \frac{P_{dp}}{2\eta \cdot V_{in}}$$

$$\Delta I_L = \frac{V_{in} \cdot D \cdot T_s}{L}$$

$$I_{L,peak} = I_{L,avg,sp} + \frac{\Delta I_L}{2}, \quad I_{L,valley} = I_{L,avg,sp} - \frac{\Delta I_L}{2}$$

---

## 2. 时序（D < 0.5）

| 事件 | 时间 |
|------|------|
| Phase 1 开关 ON | $t = 0$ |
| Phase 1 开关 OFF（diode 1 开始导通） | $t = DT_s$ |
| Phase 2 开关 ON（diode 2 截止） | $t = 0.5T_s$ |
| Phase 2 开关 OFF（diode 2 开始导通） | $t = (0.5+D)T_s$ |
| diode 1 截止 / 周期结束 | $t = T_s$ |

Diode 导通区间（无重叠）：
- $I_{d1}$：$[DT_s, \ (0.5+D)T_s]$
- $I_{d2}$：$[0.5T_s, \ T_s]$（等价于 $[0, \ DT_s]$ 在下一周期）

---

## 3. CCM — $I_d(t)$

TOFF 期间下降斜率：$m = \frac{V_{out} + V_f - V_{in}}{L}$（正值）

### 3.1 Phase 1 diode 电流

$$I_{d1}(t) = I_{L,peak} - m(t - DT_s), \quad t \in [DT_s, \ (0.5+D)T_s]$$

### 3.2 Phase 2 diode 电流

$$I_{d2}(t) = I_{L,peak} - m\left(t - \frac{T_s}{2}\right), \quad t \in [0.5T_s, \ T_s]$$

等价地，在 $t \in [0, \ DT_s]$ 区间（Phase 2 的 diode 从上一周期延续）：

$$I_{d2}(t) = I_{L,valley} + m \cdot t, \quad t \in [0, \ DT_s]$$

### 3.3 总 diode 电流（D < 0.5 无重叠）

$$I_d(t) = \begin{cases} I_{d2}(t) & t \in [0, \ DT_s] \\ I_{d1}(t) & t \in [DT_s, \ (0.5+D)T_s] \\ I_{d2}(t) & t \in [(0.5+D)T_s, \ T_s] \end{cases}$$

---

## 4. DCM — $I_d(t)$

DCM 额外条件：diode 电流在 $T_s/2$ 之前降为零，即 $D + \delta < 0.5$。

### 4.1 导通时间比

$$\delta = \frac{\Delta I_L}{m \cdot T_s} = \frac{D \cdot V_{in}}{V_{out} + V_f - V_{in}}$$

### 4.2 Phase 1 diode 电流（从 0 上升到峰值再降回 0）

$$I_{d1}(t) = \begin{cases} m(t - DT_s) & t \in [DT_s, \ (D+\delta)T_s] \\ 0 & \text{otherwise} \end{cases}$$

### 4.3 总 diode 电流

$$I_d(t) = I_{d1}(t) + I_{d1}\!\left(t - \frac{T_s}{2}\right)$$

其中第二项是 Phase 1 波形延迟 $T_s/2$（Phase 2 与 Phase 1 波形相同，仅相位差 180°）。

---

## 5. 待完成

- [ ] $D \geq 0.5$ 的情况（diode 导通区间重叠）
- [ ] 输出纹波电压计算（含 $C_{out}$ ESR）
- [ ] 数值验证脚本
- [ ] $I_d$ 波形可视化（matplotlib）
