# Step 1f: RC Snubber 损耗建模

## 模型概述
在 step1e 基础上增加 RC snubber 损耗，用于模拟开关损耗等高频损耗。

## Snubber 参数
- C_snub = 500pF
- R_snub = 5Ω

## Snubber 损耗公式

### 简化公式（不准确）
```
P_snub = 0.5 × C × Vout² × fsw  ❌
```

### 修正公式（考虑实际开关电压）
```
关断: C 从 IL_peak×Rdson 充电到 Vout+Vf
开通: C 从 Vout+Vf 放电到 IL_valley×Rdson

E_off = 0.5 × C × ((Vout+Vf)² - (IL_peak×Rdson)²)
E_on  = 0.5 × C × ((Vout+Vf)² - (IL_valley×Rdson)²)
P_snub = (E_on + E_off) × fsw
```

### 问题：与仿真误差较大
- 模型计算: 471 nJ/cycle (0.2356 + 0.2355 µJ)
- 实际仿真: 372 nJ/cycle
- 误差: ~27%

**TODO**: 需要进一步分析 snubber 损耗模型，可能需要考虑：
1. 开关过渡时间（非理想阶跃）
2. 电流重叠期间的波形
3. Rdson 随电流变化

## 迭代结果（Vin=9V, Vout=30V, Iout=0.5A）

| 参数 | 值 |
|------|-----|
| η | 85.36% |
| D | 0.7439 |
| IL_avg | 1.9525 A |
| IL_peak | 2.6804 A |
| IL_valley | 1.2245 A |
| ΔIL | 1.4559 A |

### 损耗分布
| 损耗项 | 功率 | 占比 |
|--------|------|------|
| P_DCR | 1.1436 W | 44.5% |
| P_MOS | 0.8902 W | 34.6% |
| P_diode | 0.3500 W | 13.6% |
| P_snub | 0.1884 W | 7.3% |
| **P_sum** | **2.5723 W** | 100% |

### 对比：无 Snubber vs 有 Snubber
| 参数 | 无Snubber | 有Snubber | 差值 |
|------|-----------|-----------|------|
| η | 86.59% | 85.36% | -1.23% |
| IL_avg | 1.9248 A | 1.9525 A | +0.028 A |
| P_sum | 2.3232 W | 2.5723 W | +0.249 W |
