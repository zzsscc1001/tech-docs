# 情况 C：DCM + 二极管占空比 $< 0.5$

> 条件：DCM，$D_d = \delta < 0.5$
> 特点：$D$ 随负载变化，需按 $D$ 和 $D+D_d$ 分三个子情况
> 计算脚本：`calc_case_c1.py`

---

## 1. 前提条件

### 1.1 DCM 判定

$$R > R_{critical} \quad \Rightarrow \quad \text{DCM}$$

其中 $R_{critical}$ 由 CRM 边界条件 $I_{L,avg} = \Delta I_L / 2$ 推导：

$$R_{critical} = \frac{V_{out}^2}{\eta \cdot V_{in} \cdot \Delta I_L}, \quad \Delta I_L = \frac{V_{in} \cdot D_{ccm} \cdot T_s}{L}$$

### 1.2 DCM 下 D 的求解

**CCM 的 $D = 1 - V_{in}/(V_{out}+V_f)$ 在 DCM 下不适用。**

DCM 下 $V_{out} = f(D, R, L, f_s)$，输出电压由 D、负载、电感、频率共同决定。控制器通过调节 D 来稳定 $V_{out}$。

从 DCM 能量平衡方程（两相）：

$$I_{out} = \frac{V_{in}^2 \cdot D^2 \cdot T_s}{L \cdot (V_{out}+V_f-V_{in})}$$

结合 $I_{out} = V_{out}/R$，整理得：

$$V_{out}^2 - (V_{in}-V_f) \cdot V_{out} = \frac{R \cdot \eta \cdot V_{in}^2 \cdot D^2 \cdot T_s}{L}$$

给定 $V_{out}$ 反解 D：

$$\boxed{D = \sqrt{\frac{\left[V_{out}^2 - (V_{in}-V_f) \cdot V_{out}\right] \cdot L}{R \cdot \eta \cdot V_{in}^2 \cdot T_s}}}$$

**关键结论：DCM 下 D 小于 CCM 的 D，控制器需要减小占空比来维持 $V_{out}$。**

### 1.3 二极管占空比

$$D_d = \delta = \frac{D \cdot V_{in}}{V_{out}+V_f-V_{in}}$$

### 1.4 子情况分类

| 子情况 | 条件 | $t=0$ 状态 | D2 起始 |
|--------|------|-----------|---------|
| **C1** | $D > 0.5$ | 死区（D2 未导通） | $(D-0.5)T_s$ |
| **C2a** | $D < 0.5$, $D+D_d < 0.5$ | 死区（D2 已归零） | $t=0$（上周期延续） |
| **C2b** | $D < 0.5$, $D+D_d > 0.5$ | D2 导通中（从上周期延续） | $t=0$ 之前 |

> **判断顺序：先看 D 是否 > 0.5，再看 D+Dd 是否 > 0.5。**

### 1.5 基础知识

> **Diode 电流永远是下降斜坡。** 开关断开瞬间电感电流达到峰值，diode 电流从该峰值线性下降。

---

## 2. 子情况 C1：$D > 0.5$

> Phase 2 的 diode 在 $t=0$ 未导通，从 $(D-0.5)T_s$ 开始。

### 2.1 时序（同步关沿）

| 区间 | 时间范围 | SW1 | SW2 | D1 | D2 | 说明 |
|------|----------|-----|-----|----|----|------|
| ① | $[0, (D-0.5)T_s]$ | ON | OFF | ✗ | ✗ | 死区 |
| ② | $[(D-0.5)T_s, (D-0.5+\delta)T_s]$ | OFF | OFF | ✗ | ✓ | D2 下降 |
| ③ | $[(D-0.5+\delta)T_s, DT_s]$ | OFF | ON/OFF | ✗ | ✗ | 死区 |
| ④ | $[DT_s, (D+\delta)T_s]$ | OFF | OFF | ✓ | ✗ | D1 下降 |
| ⑤ | $[(D+\delta)T_s, T_s]$ | OFF | OFF | ✗ | ✗ | 死区 |

### 2.2 D1 电流（下降斜坡）

$$I_{d1}(t) = I_{L,peak} - m(t - DT_s), \quad t \in [DT_s, \ (D+\delta)T_s]$$

### 2.3 D2 电流（下降斜坡）

$$I_{d2}(t) = I_{L,peak} - m\bigl(t - (D-0.5)T_s\bigr), \quad t \in [(D-0.5)T_s, \ (D-0.5+\delta)T_s]$$

### 2.4 总 diode 电流 $I_d(t)$

**区间① $t \in [0, \ (D-0.5)T_s]$ — 死区**

$$I_d(t) = 0$$

**区间② $t \in [(D-0.5)T_s, \ (D-0.5+\delta)T_s]$ — D2 导通（下降）**

$$I_d(t) = I_{L,peak} - m\bigl(t - (D-0.5)T_s\bigr)$$

**区间③ $t \in [(D-0.5+\delta)T_s, \ DT_s]$ — 死区**

$$I_d(t) = 0$$

**区间④ $t \in [DT_s, \ (D+\delta)T_s]$ — D1 导通（下降）**

$$I_d(t) = I_{L,peak} - m(t - DT_s)$$

**区间⑤ $t \in [(D+\delta)T_s, \ T_s]$ — 死区**

$$I_d(t) = 0$$

### 2.5 波形特征

- 两个下降斜坡脉冲，都从 $I_{L,peak}$ 降至 0
- 脉冲底宽 $\delta T_s$
- 三段死区，两路不交叠

---

## 3. 子情况 C2a：$D < 0.5$, $D+D_d < 0.5$

> Phase 2 的 diode 在 $t=0$ 之前已归零。$t=0$ 是死区。

### 3.1 时序（同步开沿）

| 区间 | 时间范围 | SW1 | SW2 | D1 | D2 | 说明 |
|------|----------|-----|-----|----|----|------|
| ① | $[0, \ DT_s]$ | OFF | OFF | ✗ | ✗ | 死区 |
| ② | $[DT_s, \ (D+\delta)T_s]$ | OFF | OFF | ✓ | ✗ | D1 下降 |
| ③ | $[(D+\delta)T_s, \ 0.5T_s]$ | OFF | OFF | ✗ | ✗ | 死区 |
| ④ | $[0.5T_s, \ (0.5+D)T_s]$ | OFF | ON | ✗ | ✗ | 死区（SW2 ON） |
| ⑤ | $[(0.5+D)T_s, \ (0.5+D+\delta)T_s]$ | OFF | OFF | ✗ | ✓ | D2 下降 |
| ⑥ | $[(0.5+D+\delta)T_s, \ T_s]$ | OFF | OFF | ✗ | ✗ | 死区 |

> 注意：C2a 的 D2 在 $[0.5Ts$ 之后开始（Phase 2 的 off-time），不是从 $t=0$ 开始。
> $D+D_d < 0.5$ 保证 D2 在 $T_s$ 之前归零。

### 3.2 D1 电流（下降斜坡）

$$I_{d1}(t) = I_{L,peak} - m(t - DT_s), \quad t \in [DT_s, \ (D+\delta)T_s]$$

### 3.3 D2 电流（下降斜坡）

$$I_{d2}(t) = I_{L,peak} - m\bigl(t - (0.5+D)T_s\bigr), \quad t \in [(0.5+D)T_s, \ (0.5+D+\delta)T_s]$$

### 3.4 总 diode 电流 $I_d(t)$

**区间①③④⑥ — 死区**

$$I_d(t) = 0$$

**区间② $t \in [DT_s, \ (D+\delta)T_s]$ — D1 导通（下降）**

$$I_d(t) = I_{L,peak} - m(t - DT_s)$$

**区间⑤ $t \in [(0.5+D)T_s, \ (0.5+D+\delta)T_s]$ — D2 导通（下降）**

$$I_d(t) = I_{L,peak} - m\bigl(t - (0.5+D)T_s\bigr)$$

---

## 4. 子情况 C2b：$D < 0.5$, $D+D_d > 0.5$

> Phase 2 的 diode 在 $t=0$ 时仍在导通（从上一周期延续）。
> D2 从 $t=0$ 开始下降，在 $D_d \cdot T_s$ 时归零。

### 4.1 时序（同步开沿）

| 区间 | 时间范围 | SW1 | SW2 | D1 | D2 | 说明 |
|------|----------|-----|-----|----|----|------|
| ① | $[0, \ \delta T_s]$ | OFF | OFF | ✗ | ✓ | D2 下降（从上周期延续） |
| ② | $[\delta T_s, \ DT_s]$ | OFF | OFF | ✗ | ✗ | 死区 |
| ③ | $[DT_s, \ (D+\delta)T_s]$ | OFF | OFF | ✓ | ✗ | D1 下降 |
| ④ | $[(D+\delta)T_s, \ 0.5T_s]$ | OFF | OFF | ✗ | ✗ | 死区 |
| ⑤ | $[0.5T_s, \ T_s]$ | OFF/ON | ON/OFF | ✗ | ✗ | 死区 |

### 4.2 D2 电流（下降斜坡，从上周期延续）

$$I_{d2}(t) = I_{L,peak} - m \cdot t, \quad t \in [0, \ \delta T_s]$$

边界值：$I_{d2}(0) = I_{L,peak}$，$I_{d2}(\delta T_s) = 0$

### 4.3 D1 电流（下降斜坡）

$$I_{d1}(t) = I_{L,peak} - m(t - DT_s), \quad t \in [DT_s, \ (D+\delta)T_s]$$

### 4.4 总 diode 电流 $I_d(t)$

**区间① $t \in [0, \ \delta T_s]$ — D2 导通（下降）**

$$I_d(t) = I_{L,peak} - m \cdot t$$

**区间②④⑤ — 死区**

$$I_d(t) = 0$$

**区间③ $t \in [DT_s, \ (D+\delta)T_s]$ — D1 导通（下降）**

$$I_d(t) = I_{L,peak} - m(t - DT_s)$$

### 4.5 特征

- D2 从 $t=0$ 开始下降（从上周期延续），D1 从 $DT_s$ 开始下降
- 两个脉冲都是下降斜坡，都从 $I_{L,peak}$ 降至 0
- 两路波形形状相同，时间偏移约 $T_s/2$

---

## 5. 三个子情况对比

| 参数 | C1 ($D>0.5$) | C2a ($D<0.5$, $D+D_d<0.5$) | C2b ($D<0.5$, $D+D_d>0.5$) |
|------|-------------|---------------------------|---------------------------|
| $t=0$ 状态 | 死区 | 死区 | D2 导通中 |
| D2 起始 | $(D-0.5)T_s$ | $(0.5+D)T_s$ | $0$（上周期延续） |
| D1 波形 | 下降斜坡 | 下降斜坡 | 下降斜坡 |
| D2 波形 | 下降斜坡 | 下降斜坡 | 下降斜坡 |
| 同步方式 | 同步关沿 | 同步开沿 | 同步开沿 |
| 约束 | $D+D_d<1$ | $D+D_d<0.5$ | $0.5<D+D_d<1$ |

> **所有子情况的 diode 电流都是下降斜坡。区别在于 D2 的起始时间和同步方式。**

---

## 6. 待完成

- [ ] 数值验证（仿真对比）
- [ ] C2a↔C2b 过渡点（$D+D_d = 0.5$）的连续性验证
- [ ] C1↔C2 过渡点（$D = 0.5$）的连续性验证
