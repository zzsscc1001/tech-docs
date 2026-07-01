# 计算注意事项与易错点

> 在推导过程中反复出现的错误，记录下来避免再犯。

---

## 1. Diode 电流永远是下降斜坡

开关断开瞬间，电感电流达到峰值，diode 电流从该峰值**线性下降**（$dI/dt = (V_{in}-V_{out}-V_f)/L < 0$）。

- CCM：从 $I_{L,peak}$ 降到 $I_{L,valley}$
- DCM：从 $I_{L,peak}$ 降到 $0$

**永远不存在上升斜坡的 diode 电流。**

---

## 2. 效率 η 的使用方式

### ✅ 正确：从功率守恒推输出电流

$$P_{in} = 2 \cdot V_{in} \cdot I_{L,avg} \quad \text{（两相总输入功率）}$$

$$P_{out} = \eta \cdot P_{in}$$

$$I_{out} = \frac{P_{out}}{V_{out}} = \frac{\eta \cdot 2 \cdot V_{in} \cdot I_{L,avg}}{V_{out}}$$

### ❌ 错误：直接套用 $I_{out} = I_{L,avg} \times (1-D) \times \eta$

这个公式没有正确的物理依据。曾经导致 $R_{critical}$ 算出 268Ω（错误），实际应为 131Ω。

---

## 2. 占空比 D 公式的选择

### CCM 下

$$D = 1 - \frac{V_{in}}{V_{out}+V_f}$$

仅由电压比决定，与负载无关。

### DCM 下

D 随负载变化，不能用 CCM 的公式。需要从能量平衡方程数值求解。

### ⚠️ 判断顺序

**先判断 CCM/DCM，再选 D 公式。** 不能用 CCM 的 D 算出 $I_{L,valley} < 0$ 就说进入了 DCM——如果用 CCM 公式算出来的 D 导致 DCM，说明这个工况本身就不在 CCM，需要用 DCM 的方法重新解 D。

---

## 3. 自洽性检查（必须做！）

每次算完后，检查以下条件是否自洽：

| 检查项 | 条件 | 矛盾时说明 |
|--------|------|-----------|
| $I_{L,valley}$ 与 $L_{critical}$ | $I_{L,valley} > 0 \Leftrightarrow L > L_{critical}$ | 如果一个说 CCM 一个说 DCM，计算有误 |
| $D + D_d$ | CCM: $D + D' = 1$；DCM: $D + D_d < 1$ | 如果 $D + D_d > 1$，D 公式用错了 |
| 功率守恒 | $P_{out} = \eta \cdot P_{in}$ | 验证 $V_{out} \times I_{out}$ 是否等于 $\eta \times 2 \times V_{in} \times I_{L,avg}$ |

---

## 4. 单相 vs 总量

| 量 | 单相 | 两相总量 |
|----|------|---------|
| 功率 | $P_{sp} = P_{dp}/2$ | $P_{dp} = V_{out}^2/R$ |
| 电感电流 | $I_{L,avg,sp}$ | $I_{in,total} = 2 \cdot I_{L,avg,sp}$ |
| 输出电流 | $I_{out}/2$ | $I_{out} = V_{out}/R$ |
| 负载电阻 | — | $R$ 是总负载 |

**纹波电流 $\Delta I_L$ 是单相量**，不乘 2。

---

## 5. CRM 边界计算的正确流程

1. 用 CCM 公式算 D（CRM 是 CCM 的边界，D 公式仍然适用）
2. 算 $\Delta I_L = V_{in} \cdot D \cdot T_s / L$
3. 边界条件：$I_{L,avg} = \Delta I_L / 2$
4. 从功率守恒推 $I_{out}$：$I_{out} = \eta \cdot 2 \cdot V_{in} \cdot (\Delta I_L/2) / V_{out}$
5. $R_{critical} = V_{out} / I_{out}$
6. 验证：$P_{out} = V_{out} \times I_{out}$，$P_{in} = 2 \times V_{in} \times \Delta I_L / 2$，$\eta = P_{out}/P_{in}$

---

## 6. 参考数值（本工况）

| 参数 | 值 |
|------|-----|
| $V_{in}$ | 6 V |
| $V_{out}$ | 30 V |
| $V_f$ | 0.7 V |
| $L$ | 10 µH |
| $f_s$ | 400 kHz |
| $\eta$ | 0.95 |
| $D$ (CCM) | 0.8046 |
| $\Delta I_L$ | 1.207 A |
| $R_{critical}$ | 131 Ω |
| 仿真 $R_{critical}$ | ~150 Ω |
