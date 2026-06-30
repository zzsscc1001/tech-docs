# 双相交错 180° Boost — $I_d(t)$ 时域公式

> 继承单相模型（见 `01_single_phase.md`）
> 功率定义：$P_{dp}$ = 双相总功率，$P_{sp} = P_{dp}/2$ = 单相功率

---

## 1. 单相参数

$$I_{L,avg,sp} = \frac{P_{dp}}{2\eta \cdot V_{in}}$$

$$\Delta I_L = \frac{V_{in} \cdot D \cdot T_s}{L}$$

$$I_{L,peak} = I_{L,avg,sp} + \frac{\Delta I_L}{2}, \quad I_{L,valley} = I_{L,avg,sp} - \frac{\Delta I_L}{2}$$

TOFF 期间下降斜率（正值）：

$$m = \frac{V_{out} + V_f - V_{in}}{L}$$

---

## 2. 同步方式与 D 的关系

> **关键结论：180° 交错的"180°"作用在哪个沿，取决于 D 和 0.5 的关系。**

### D < 0.5：同步开沿

- Phase 1 开关 ON：$[0, DT_s]$
- Phase 2 开关 ON：$[0.5T_s, (0.5+D)T_s]$（延迟 $T_s/2$）
- Phase 1 的 OFF 时间 $(1-D)T_s > 0.5T_s$，能容纳 Phase 2 的完整 ON 区间
- **结果：两路 diode 导通区间有重叠**

### D > 0.5：同步关沿

- Phase 1 开关 ON：$[0, DT_s]$
- Phase 2 开关 ON：$[(D-0.5)T_s, 0.5T_s]$
- Phase 1 的 ON 时间 $DT_s > 0.5T_s$，无法在 $0.5T_s$ 让 Phase 2 也开
- **结果：两路 diode 完全不重叠，有两段死区**

---

## 3. D > 0.5（diode 占空比 $< 0.5$）— CCM $I_d(t)$

> 此情况 diode 完全不交叠，波形最简单。

### 3.1 时序

| 区间 | SW1 | SW2 | D1 | D2 | 说明 |
|------|-----|-----|----|----|------|
| $[0, (D-0.5)T_s]$ | ON | OFF | ✗ | ✗ | 死区 |
| $[(D-0.5)T_s, 0.5T_s]$ | OFF | OFF | ✗ | ✓ | 仅 D2 |
| $[0.5T_s, DT_s]$ | OFF | ON | ✗ | ✗ | 死区 |
| $[DT_s, T_s]$ | OFF | OFF | ✓ | ✗ | 仅 D1 |

- Diode 占空比：$1-D < 0.5$
- 每路 diode 导通时间：$(1-D)T_s$
- 两段死区总时长：$2(D-0.5)T_s = (2D-1)T_s$

### 3.2 D1 电流（下降斜坡）

$$I_{d1}(t) = I_{L,peak} - m(t - DT_s), \quad t \in [DT_s, \ T_s]$$

边界值：$I_{d1}(DT_s) = I_{L,peak}$，$I_{d1}(T_s) = I_{L,valley}$

### 3.3 D2 电流（上升斜坡）

$$I_{d2}(t) = I_{L,valley} + m(t - (D-0.5)T_s), \quad t \in [(D-0.5)T_s, \ 0.5T_s]$$

边界值：$I_{d2}((D-0.5)T_s) = I_{L,valley}$，$I_{d2}(0.5T_s) = I_{L,peak}$

### 3.4 总 diode 电流

$$I_d(t) = \begin{cases} 0 & t \in [0, \ (D-0.5)T_s] \quad \text{死区} \\ I_{L,valley} + m\bigl(t-(D-0.5)T_s\bigr) & t \in [(D-0.5)T_s, \ 0.5T_s] \quad \text{D2} \\ 0 & t \in [0.5T_s, \ DT_s] \quad \text{死区} \\ I_{L,peak} - m(t-DT_s) & t \in [DT_s, \ T_s] \quad \text{D1} \end{cases}$$

波形特征：两个三角脉冲，中间隔两段零电流死区，完全不交叠。D1 是下降斜坡，D2 是上升斜坡，关于中心对称。

---

## 4. 待完成

- [ ] D < 0.5 的情况（diode 导通区间重叠）
- [ ] DCM 分析
- [ ] 输出纹波电压计算（含 $C_{out}$ ESR）
- [ ] 数值验证脚本
- [ ] $I_d$ 波形可视化（matplotlib）
