"""
Step 1f: 加入 RC Snubber 损耗
==============================
在 step1e 基础上增加 RC snubber 损耗建模

RC Snubber 损耗分析:
  - Snubber 并联在 MOSFET DS 两端
  - MOSFET 关断时: C 通过 R 充电到 Vout，R 消耗 0.5CV²
  - MOSFET 导通时: C 通过 R 放电到 0V，R 消耗 0.5CV²
  - 每个周期总损耗: E = 0.5CV² + 0.5CV² = CV²
  - 平均功率: P_snub = CV² × fsw

  注意: R 只影响充放电时间常数和峰值电流，不影响平均功率

参数:
  C_snub = 500pF (典型值，用于抑制开关振铃)
  R_snub = 5Ω   (限制放电峰值电流)
"""

import math


def boost_with_snubber(Vin, Vout, Iout, L, fsw, Vf, DCR, Rds,
                       C_snub, R_snub, tol=1e-8, max_iter=100, verbose=False):
    """
    完整模型: Vf + DCR + Rds + RC Snubber

    方法: η 预设 + KCL 反推 + 精确 ΔIL + Snubber 损耗
    """
    # Snubber 损耗: 开关各半个周期
    # 关断: C 从 Ipeak×Rdson 充电到 Vout+Vf, R 消耗 E_off
    # 开通: C 从 Vout+Vf 放电到 Ivalley×Rdson, R 消耗 E_on
    V_high = Vout + Vf

    # 初始 η: 仅 Vf
    eta = Vout / (Vout + Vf)

    for i in range(max_iter):
        # Step 1: IL_avg from η
        IL_avg = Vout * Iout / (eta * Vin)

        # Step 2: D (KCL)
        D = 1 - Iout / IL_avg

        # Step 3: ΔIL (考虑 Rds+DCR)
        R_ton = Rds + DCR
        dIL = (Vin - IL_avg * R_ton) * D / (L * fsw)
        dIL_check = (Vout + Vf - Vin + IL_avg * DCR) * (1 - D) / (L * fsw)

        # Step 4: 峰值/谷值
        IL_peak = IL_avg + dIL / 2
        IL_valley = IL_avg - dIL / 2

        # Step 5: RMS
        IQ_rms = math.sqrt(D * (IL_avg**2 + dIL**2 / 12))
        ID_rms = math.sqrt((1 - D) * (IL_avg**2 + dIL**2 / 12))
        IC_rms = math.sqrt(ID_rms**2 - Iout**2)

        # Step 6: 损耗 (snubber 用实际电压)
        P_MOS = IQ_rms**2 * Rds
        P_diode = Vf * Iout
        P_DCR = IL_avg**2 * DCR

        # Snubber: 关断充电 + 开通放电
        V_low_charge = IL_peak * Rds      # 关断开始时的 SW 电压
        V_low_discharge = IL_valley * Rds  # 开通结束时的 SW 电压
        E_off = 0.5 * C_snub * (V_high**2 - V_low_charge**2)
        E_on = 0.5 * C_snub * (V_high**2 - V_low_discharge**2)
        P_snub = (E_on + E_off) * fsw

        P_sum = P_MOS + P_diode + P_DCR + P_snub

        # η 更新
        Pout = Vout * Iout
        eta_new = Pout / (Pout + P_sum)

        if verbose and i < 10:
            print(f"  iter {i}: η={eta*100:.4f}% IL={IL_avg:.4f} P_snub={P_snub:.4f}W")

        if abs(eta_new - eta) < tol:
            eta = eta_new
            break
        eta = eta_new

    # 最终结果
    Pin = Vin * IL_avg
    eta_actual = Pout / Pin

    return {
        'D': D, 'IL_avg': IL_avg, 'dIL': dIL, 'dIL_check': dIL_check,
        'IL_peak': IL_peak, 'IL_valley': IL_valley,
        'IQ_rms': IQ_rms, 'ID_rms': ID_rms, 'IC_rms': IC_rms,
        'Pin': Pin, 'Pout': Pout,
        'eta': eta_actual,
        'P_MOS': P_MOS, 'P_diode': P_diode, 'P_DCR': P_DCR, 'P_snub': P_snub,
        'P_sum': P_sum,
        'kcl_check': (1 - D) * IL_avg,
        'iters': i + 1,
        'C_snub': C_snub, 'R_snub': R_snub,
    }


# =====================================================================
#  验证
# =====================================================================

Vin, Vout, L, fsw, Iout = 9.0, 30.0, 10e-6, 400e3, 0.5
Vf = 0.7
DCR = 0.3
Rds = 0.3
C_snub = 500e-12  # 500pF
R_snub = 5.0      # 5Ω

print("=" * 70)
print("Step 1f: 加入 RC Snubber 损耗")
print("=" * 70)
print(f"参数: Vin={Vin}V, Vout={Vout}V, L={L*1e6}µH, fsw={fsw/1e3}kHz")
print(f"      Iout={Iout}A, Vf={Vf}V, DCR={DCR*1000:.0f}mΩ, Rds={Rds*1000:.0f}mΩ")
print(f"      C_snub={C_snub*1e12:.0f}pF, R_snub={R_snub:.0f}Ω\n")

# Snubber 损耗理论 (使用迭代后的 IL_peak/IL_valley)
print(f"--- Snubber 损耗公式 ---")
print(f"关断: E_off = 0.5×C×((Vout+Vf)² - (IL_peak×Rdson)²)")
print(f"开通: E_on  = 0.5×C×((Vout+Vf)² - (IL_valley×Rdson)²)")
print(f"P_snub = (E_on + E_off) × fsw  (需迭代后计算)\n")

# --- 迭代 ---
print("--- 迭代过程 ---")
r = boost_with_snubber(Vin, Vout, Iout, L, fsw, Vf, DCR, Rds,
                        C_snub, R_snub, verbose=True)

print(f"\n--- 结果 ({r['iters']} 步收敛) ---")
print(f"η         = {r['eta']*100:.4f}%")
print(f"D         = {r['D']:.6f}  (KCL 反推)")
print(f"IL_avg    = {r['IL_avg']:.4f} A")
print(f"ΔIL       = {r['dIL']:.4f} A")
print(f"ΔIL_check = {r['dIL_check']:.4f} A")
print(f"IL_peak   = {r['IL_peak']:.4f} A")
print(f"IL_valley = {r['IL_valley']:.4f} A")
print(f"IQ_rms    = {r['IQ_rms']:.4f} A")
print(f"ID_rms    = {r['ID_rms']:.4f} A")
print(f"IC_rms    = {r['IC_rms']:.4f} A")

print(f"\n--- 功率平衡 ---")
print(f"Pin       = {r['Pin']:.4f} W")
print(f"Pout      = {r['Pout']:.4f} W")
print(f"P_MOS     = {r['P_MOS']:.4f} W  (Rds={Rds*1000:.0f}mΩ)")
print(f"P_diode   = {r['P_diode']:.4f} W  (Vf={Vf}V)")
print(f"P_DCR     = {r['P_DCR']:.4f} W  (DCR={DCR*1000:.0f}mΩ)")
print(f"P_snub    = {r['P_snub']:.4f} W  (C={C_snub*1e12:.0f}pF, R={R_snub:.0f}Ω)")
print(f"P_sum     = {r['P_sum']:.4f} W")
print(f"Pin-Pout  = {r['Pin']-r['Pout']:.4f} W  (应 ≈ P_sum)")

# --- Snubber 能量分解 ---
print(f"\n--- Snubber 能量分解 ---")
V_high = Vout + Vf
V_low_charge = r['IL_peak'] * Rds
V_low_discharge = r['IL_valley'] * Rds
E_off = 0.5 * C_snub * (V_high**2 - V_low_charge**2)
E_on = 0.5 * C_snub * (V_high**2 - V_low_discharge**2)
print(f"V_high (Vout+Vf)       = {V_high:.2f} V")
print(f"V_low_charge (Ipeak×Rds)   = {V_low_charge:.4f} V")
print(f"V_low_discharge (Ivalley×Rds) = {V_low_discharge:.4f} V")
print(f"E_off (关断) = 0.5×C×({V_high}²-{V_low_charge:.4f}²) = {E_off*1e6:.4f} µJ")
print(f"E_on  (开通) = 0.5×C×({V_high}²-{V_low_discharge:.4f}²) = {E_on*1e6:.4f} µJ")
print(f"P_snub = ({E_on*1e6:.4f}+{E_off*1e6:.4f})µJ × {fsw/1e3:.0f}kHz = {r['P_snub']:.4f} W")

# --- 验证 ---
print(f"\n--- 验证 ---")
print(f"KCL: (1-D)×IL = {r['kcl_check']:.8f} == {Iout} ? {abs(r['kcl_check']-Iout)<1e-8}")
print(f"ΔIL: Ton侧={r['dIL']:.6f} vs Toff侧={r['dIL_check']:.6f} ? {abs(r['dIL']-r['dIL_check'])<1e-6}")

# --- 对比: 无 snubber vs 有 snubber ---
print(f"\n{'='*70}")
print("对比: 无 Snubber vs 有 Snubber")
print(f"{'='*70}")

# 无 snubber (C=0)
r_no = boost_with_snubber(Vin, Vout, Iout, L, fsw, Vf, DCR, Rds, 0, R_snub)

print(f"{'参数':<14} {'无Snubber':<14} {'有Snubber':<14} {'差值':<12}")
print("-" * 54)
print(f"{'η(%)':<14} {r_no['eta']*100:<14.4f} {r['eta']*100:<14.4f} {(r['eta']-r_no['eta'])*100:+.4f}")
print(f"{'IL_avg(A)':<14} {r_no['IL_avg']:<14.4f} {r['IL_avg']:<14.4f} {r['IL_avg']-r_no['IL_avg']:+.4f}")
print(f"{'D':<14} {r_no['D']:<14.6f} {r['D']:<14.6f} {r['D']-r_no['D']:+.6f}")
print(f"{'P_sum(W)':<14} {r_no['P_sum']:<14.4f} {r['P_sum']:<14.4f} {r['P_sum']-r_no['P_sum']:+.4f}")

# --- Snubber 损耗占比 ---
print(f"\n--- 损耗分布 ---")
total = r['P_sum']
print(f"P_MOS   = {r['P_MOS']:.4f} W ({r['P_MOS']/total*100:.1f}%)")
print(f"P_diode = {r['P_diode']:.4f} W ({r['P_diode']/total*100:.1f}%)")
print(f"P_DCR   = {r['P_DCR']:.4f} W ({r['P_DCR']/total*100:.1f}%)")
print(f"P_snub  = {r['P_snub']:.4f} W ({r['P_snub']/total*100:.1f}%)")
print(f"P_sum   = {r['P_sum']:.4f} W (100%)")

# --- R_snub 影响说明 ---
print(f"\n--- R_snub 影响 ---")
print(f"R_snub = {R_snub:.0f}Ω 不影响平均功率，只影响:")
tau = R_snub * C_snub
print(f"  时间常数 τ = R×C = {R_snub:.0f}×{C_snub*1e12:.0f}pF = {tau*1e9:.1f}ns")
t_on = Vin * r['D'] / (L * fsw) * L / Vin  # 简化: D/fsw
print(f"  Ton = D/fsw = {r['D']:.4f}/{fsw/1e3:.0f}kHz = {r['D']/fsw*1e6:.1f}µs")
print(f"  τ/Ton = {tau/(r['D']/fsw)*100:.1f}%  (应 << 100% 以完全放电)")
I_peak_discharge = Vout / R_snub
print(f"  放电峰值电流 = Vout/R = {Vout}/{R_snub:.0f} = {I_peak_discharge:.1f}A")
