# 情况 C：DCM + 二极管占空比 $< 0.5$

> 条件：DCM，$D_d = \delta < 0.5$
> 特点：$D$ 随负载变化，需按 $D$ 分两个子情况

---

## 1. 前提条件

$$\text{DCM：} I_{L,valley} = I_{L,avg,sp} - \frac{\Delta I_L}{2} \leq 0$$

$$D_d = \delta = \frac{D \cdot V_{in}}{V_{out}+V_f-V_{in}} < 0.5$$

DCM 下 $D$ 随负载减小而减小（能量平衡约束），不再由电压比唯一决定。

---

## 2. 子情况 C1：$D > 0.5$

> 来自轨迹 A→C 的 DCM 阶段（初始 $D > 0.5$，轻载后 $D$ 递减但可能仍 $> 0.5$）

### 2.1 时序

| 区间 | 时间范围 | SW1 | SW2 | D1 | D2 | 说明 |
|------|----------|-----|-----|----|----|------|
| ① | $[0, (D-0.5)T_s]$ | ON | OFF | ✗ | ✗ | 死区 |
| ② | $[(D-0.5)T_s, (D-0.5+\delta)T_s]$ | OFF | OFF | ✗ | ✓ | D2 上升 |
| ③ | $[(D-0.5+\delta)T_s, DT_s]$ | OFF | ON/OFF | ✗ | ✗ | 死区 |
| ④ | $[DT_s, (D+\delta)T_s]$ | OFF | OFF | ✓ | ✗ | D1 下降 |
| ⑤ | $[(D+\delta)T_s, T_s]$ | OFF | OFF | ✗ | ✗ | 死区 |

**Phase 2 diode 在 $t=0$ 未导通**，从 $(D-0.5)T_s$ 开始。

### 2.2 D2 电流

$$I_{d2}(t) = m\bigl(t - (D-0.5)T_s\bigr), \quad t \in [(D-0.5)T_s, \ (D-0.5+\delta)T_s]$$

边界值：$I_{d2}((D-0.5)T_s) = 0$，$I_{d2}((D-0.5+\delta)T_s) = m \cdot \delta T_s$

### 2.3 D1 电流

$$I_{d1}(t) = m\bigl((D+\delta)T_s - t\bigr), \quad t \in [DT_s, \ (D+\delta)T_s]$$

边界值：$I_{d1}(DT_s) = m \cdot \delta T_s$，$I_{d1}((D+\delta)T_s) = 0$

### 2.4 总 diode 电流 $I_d(t)$

**区间① $t \in [0, \ (D-0.5)T_s]$ — 死区**

$$I_d(t) = 0$$

**区间② $t \in [(D-0.5)T_s, \ (D-0.5+\delta)T_s]$ — D2 导通**

$$I_d(t) = m\bigl(t - (D-0.5)T_s\bigr)$$

**区间③ $t \in [(D-0.5+\delta)T_s, \ DT_s]$ — 死区**

$$I_d(t) = 0$$

**区间④ $t \in [DT_s, \ (D+\delta)T_s]$ — D1 导通**

$$I_d(t) = m\bigl((D+\delta)T_s - t\bigr)$$

**区间⑤ $t \in [(D+\delta)T_s, \ T_s]$ — 死区**

$$I_d(t) = 0$$

### 2.5 波形特征

```
Id
 ▲
 │    ╱╲          ╱╲
 │   ╱  ╲        ╱  ╲
 │  ╱    ╲      ╱    ╲
 │ ╱      ╲    ╱      ╲
 │╱        ╲  ╱        ╲
 ┼──────────╲╱──────────╲──→ t
 0    ①   ②  ③   ④   ⑤  Ts
      死区 D2 死区  D1  死区
```

- 两个对称三角脉冲，峰值 = $m \cdot \delta T_s$
- 脉冲底宽 $\delta T_s$，比 Case A 的 $(1-D)T_s$ 更窄
- 三段死区（比 Case A 多一段）

---

## 3. 子情况 C2：$D < 0.5$

> $D$ 继续减小穿过 0.5 后进入此区间

### 3.1 时序

| 区间 | 时间范围 | SW1 | SW2 | D1 | D2 | 说明 |
|------|----------|-----|-----|----|----|------|
| ① | $[0, \delta T_s]$ | OFF | OFF | ✗ | ✓ | D2 下降（从上周期延续） |
| ② | $[\delta T_s, DT_s]$ | OFF | ON/OFF | ✗ | ✗ | 死区 |
| ③ | $[DT_s, (D+\delta)T_s]$ | OFF | OFF | ✓ | ✗ | D1 上升 |
| ④ | $[(D+\delta)T_s, 0.5T_s]$ | OFF | ON | ✗ | ✗ | 死区 |
| ⑤ | $[0.5T_s, T_s]$ | ON | OFF | ✗ | ✗ | 死区 |

**Phase 2 diode 在 $t=0$ 已导通**（从上一周期延续），在 $\delta T_s$ 时降为零。

### 3.2 D2 电流

$$I_{d2}(t) = m(\delta T_s - t), \quad t \in [0, \ \delta T_s]$$

边界值：$I_{d2}(0) = m \cdot \delta T_s$，$I_{d2}(\delta T_s) = 0$

### 3.3 D1 电流

$$I_{d1}(t) = m(t - DT_s), \quad t \in [DT_s, \ (D+\delta)T_s]$$

边界值：$I_{d1}(DT_s) = 0$，$I_{d1}((D+\delta)T_s) = m \cdot \delta T_s$

### 3.4 总 diode 电流 $I_d(t)$

**区间① $t \in [0, \ \delta T_s]$ — D2 导通**

$$I_d(t) = m(\delta T_s - t)$$

**区间② $t \in [\delta T_s, \ DT_s]$ — 死区**

$$I_d(t) = 0$$

**区间③ $t \in [DT_s, \ (D+\delta)T_s]$ — D1 导通**

$$I_d(t) = m(t - DT_s)$$

**区间④ $t \in [(D+\delta)T_s, \ 0.5T_s]$ — 死区**

$$I_d(t) = 0$$

**区间⑤ $t \in [0.5T_s, \ T_s]$ — 死区**

$$I_d(t) = 0$$

### 3.5 波形特征

```
Id
 ▲
 │╲              ╱
 │ ╲            ╱
 │  ╲          ╱
 │   ╲        ╱
 │    ╲      ╱
 ┼─────╲────╱────────────→ t
 0  ①  ②  ③  ④    ⑤   Ts
    D2 死区 D1  死区  死区
```

- D2 从 $t=0$ 开始下降（从上周期延续），D1 从 $DT_s$ 开始上升
- 两个脉冲不关于中心对称
- D2 的峰值在 $t=0$（即上一周期的末尾）
- 三段死区，第二段和第三段合并后更宽

---

## 4. C1 与 C2 对比

| 参数 | C1（$D > 0.5$） | C2（$D < 0.5$） |
|------|-----------------|-----------------|
| Phase 2 diode 在 $t=0$ | 未导通 | 已导通 |
| D2 起始时间 | $(D-0.5)T_s$ | $0$ |
| D2 波形 | 上升斜坡 | 下降斜坡 |
| D1 波形 | 下降斜坡 | 上升斜坡 |
| 脉冲峰值 | $m \cdot \delta T_s$ | $m \cdot \delta T_s$ |
| 对称性 | 关于中心对称 | 不对称 |
| 同步方式 | 同步关沿 | 同步开沿 |

---

## 5. 待完成

- [ ] 数值验证
- [ ] C1→C2 过渡点（$D = 0.5$）的连续性验证
