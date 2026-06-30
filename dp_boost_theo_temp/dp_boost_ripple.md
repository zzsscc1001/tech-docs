# 非同步 Boost 输出纹波 — 解析模型

> 输入参数：$V_{in}$, $V_{out}$, $I_{out}$ (或 $P_{out}$), $\eta$, $V_f$, $L$, $C_{out}$, $T_s$ (或 $f_s$)
> 模型特点：全解析，无迭代，$\eta$ 和 $V_f$ 解耦在不同公式中

---

## 1. 平均电感电流

用效率 $\eta$ 吸收所有损耗（开关损耗、铜损、铁损、驱动损耗、$V_f$ 损耗），从功率守恒直接得到：

$$P_{in} = \frac{P_{out}}{\eta} = \frac{V_{out} \cdot I_{out}}{\eta}$$

$$I_{L,avg} = I_{in,avg} = \frac{P_{in}}{V_{in}} = \frac{V_{out} \cdot I_{out}}{\eta \cdot V_{in}}$$

> **不需要知道占空比 D 就能算出 $I_{L,avg}$。**

---

## 2. 占空比 D（精确解，含 $V_f$）

### 2.1 TON 期间（开关闭合，二极管截止）

$$V_L = V_{in} \quad \Rightarrow \quad \frac{dI_L}{dt} = \frac{V_{in}}{L}$$

### 2.2 TOFF 期间（开关断开，二极管导通）

二极管导通时：$V_{anode} - V_{cathode} = V_f$，即 switching node 电压为 $V_{out} + V_f$。

$$V_L = V_{in} - V_{out} - V_f \quad \Rightarrow \quad \frac{dI_L}{dt} = \frac{V_{in} - V_{out} - V_f}{L}$$

### 2.3 伏秒平衡求 D

$$V_{in} \cdot D \cdot T_s + (V_{in} - V_{out} - V_f) \cdot (1-D) \cdot T_s = 0$$

解出：

$$\boxed{D = \frac{V_{out} + V_f - V_{in}}{V_{out} + V_f} = 1 - \frac{V_{in}}{V_{out} + V_f}}$$

验证：$V_f = 0$ 时退化为理想公式 $D = 1 - V_{in}/V_{out}$ ✓

---

## 3. 电感纹波电流

纹波电流是纯几何量，与效率 $\eta$ 无关。

### 3.1 由 TON 伏秒计算

$$\boxed{\Delta I_L = \frac{V_{in} \cdot D \cdot T_s}{L}}$$

### 3.2 由 TOFF 伏秒计算（等价）

$$\Delta I_L = \frac{(V_{out} + V_f - V_{in}) \cdot (1-D) \cdot T_s}{L}$$

### 3.3 峰值与谷值

$$I_{L,peak} = I_{L,avg} + \frac{\Delta I_L}{2}$$

$$I_{L,valley} = I_{L,avg} - \frac{\Delta I_L}{2}$$

---

## 4. CCM / DCM 分界条件

### 4.1 边界条件

CCM/DCM 分界点：电感电流谷值刚好为零。

$$I_{L,valley} = 0 \quad \Rightarrow \quad I_{L,avg} = \frac{\Delta I_L}{2}$$

### 4.2 临界电感

代入 $I_{L,avg}$ 和 $\Delta I_L$ 的表达式，解出临界电感：

$$\boxed{L_{critical} = \frac{D \cdot V_{in}^2 \cdot T_s \cdot \eta}{2 \cdot P_{out}}}$$

其中 $D = \frac{V_{out} + V_f - V_{in}}{V_{out} + V_f}$，$P_{out} = V_{out} \cdot I_{out}$。

### 4.3 判断规则

- $L > L_{critical}$ → CCM（连续导通模式）
- $L < L_{critical}$ → DCM（断续导通模式）

> **设计注意**：$D(1-D)$ 在 $D = 0.5$ 时取最大值，对应 $V_{out} \approx 2V_{in}$ 附近为最坏情况。设计时用最坏情况的 $L_{critical}$ 选电感可保证全负载范围 CCM。

---

## 5. 公式汇总表

| 编号 | 公式 | 说明 |
|------|------|------|
| 1 | $I_{L,avg} = \frac{V_{out} \cdot I_{out}}{\eta \cdot V_{in}}$ | 平均电感电流，$\eta$ 吸收所有损耗 |
| 2 | $D = 1 - \frac{V_{in}}{V_{out} + V_f}$ | 精确占空比，含二极管压降 |
| 3 | $\Delta I_L = \frac{V_{in} \cdot D \cdot T_s}{L}$ | 纹波电流，纯几何量 |
| 4 | $I_{L,peak} = I_{L,avg} + \frac{\Delta I_L}{2}$ | 电感峰值电流 |
| 5 | $I_{L,valley} = I_{L,avg} - \frac{\Delta I_L}{2}$ | 电感谷值电流 |
| 6 | $L_{critical} = \frac{D \cdot V_{in}^2 \cdot T_s \cdot \eta}{2 \cdot P_{out}}$ | CCM/DCM 临界电感 |

---

## 6. 双相交错 180° — $I_d(t)$ 时域公式

> 条件：$D < 0.5$（两相 diode 导通区间不重叠）
> 功率定义：$P_{dp}$ = 双相总功率，$P_{sp} = P_{dp}/2$ = 单相功率

### 6.1 单相参数

$$I_{L,avg,sp} = \frac{P_{dp}}{2\eta \cdot V_{in}}$$

$$\Delta I_L = \frac{V_{in} \cdot D \cdot T_s}{L}$$

$$I_{L,peak} = I_{L,avg,sp} + \frac{\Delta I_L}{2}, \quad I_{L,valley} = I_{L,avg,sp} - \frac{\Delta I_L}{2}$$

### 6.2 时序（D < 0.5）

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

### 6.3 CCM — $I_d(t)$

TOFF 期间下降斜率：$m = \frac{V_{out} + V_f - V_{in}}{L}$（正值）

**Phase 1 diode 电流：**

$$I_{d1}(t) = I_{L,peak} - m(t - DT_s), \quad t \in [DT_s, \ (0.5+D)T_s]$$

**Phase 2 diode 电流：**

$$I_{d2}(t) = I_{L,peak} - m\left(t - \frac{T_s}{2}\right), \quad t \in [0.5T_s, \ T_s]$$

等价地，在 $t \in [0, \ DT_s]$ 区间（Phase 2 的 diode 从上一周期延续）：

$$I_{d2}(t) = I_{L,valley} + m \cdot t, \quad t \in [0, \ DT_s]$$

**总 diode 电流（D < 0.5 无重叠）：**

$$I_d(t) = \begin{cases} I_{d2}(t) & t \in [0, \ DT_s] \\ I_{d1}(t) & t \in [DT_s, \ (0.5+D)T_s] \\ I_{d2}(t) & t \in [(0.5+D)T_s, \ T_s] \end{cases}$$

### 6.4 DCM — $I_d(t)$

DCM 额外条件：diode 电流在 $T_s/2$ 之前降为零，即 $D + \delta < 0.5$。

定义导通时间比：

$$\delta = \frac{\Delta I_L}{m \cdot T_s} = \frac{D \cdot V_{in}}{V_{out} + V_f - V_{in}}$$

**Phase 1 diode 电流（从 0 上升到峰值再降回 0）：**

$$I_{d1}(t) = \begin{cases} m(t - DT_s) & t \in [DT_s, \ (D+\delta)T_s] \\ 0 & \text{otherwise} \end{cases}$$

**总 diode 电流：**

$$I_d(t) = I_{d1}(t) + I_{d1}\!\left(t - \frac{T_s}{2}\right)$$

其中第二项是 Phase 1 波形延迟 $T_s/2$（Phase 2 与 Phase 1 波形相同，仅相位差 180°）。

---

## 7. 待完成

- [ ] 输出纹波电压计算（含 Cout ESR）
- [ ] D ≥ 0.5 的情况（diode 导通区间重叠）
- [ ] 数值验证脚本
- [ ] Id 波形可视化（matplotlib）
