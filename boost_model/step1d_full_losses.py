"""
Step 1d: Vf + DCR + Rds_on 完整模型 (修正版)
==============================================
关键修正: D 由伏秒平衡决定，不受 DCR/Rds 影响

推导:
  Ton:  VL = Vin - IL·Rds - IL·DCR
  Toff: VL = Vin - Vout - Vf - IL·DCR

  伏秒: [Vin-IL(Rds+DCR)]·D = [Vout+Vf+IL·DCR-Vin]·(1-D)

  展开: Vin·D - IL(Rds+DCR)·D = (Vout+Vf-Vin)·(1-D) + IL·DCR·(1-D)
  左+右 IL·DCR: Vin·D - IL·Rds·D = (Vout+Vf-Vin)·(1-D) + IL·DCR
  → D = 1 - Vin/(Vout+Vf)  ← DCR 和 Rds 消失!

  但 IL_avg 受 DCR/Rds 影响 (损耗需要更大电流)
  → 功率平衡 + KCL 联立迭代求解 IL_avg
"""

import math

def boost_solve(Vin, Vout, Iout, L, fsw, Vf, DCR, Rds, verbose=False):
    """
    求解模型:
      D = 1 - Vin/(Vout+Vf)               ← 固定，不受 DCR/Rds 影响
      IL_avg 由功率平衡迭代求解:
        Pin = Pout + P_MOS + P_diode + P_DCR
        Vin × IL = Vout×Iout + IQ²×Rds + Vf×Iout + IL²×DCR
    """
    # D 由伏秒平衡确定
    D = 1 - Vin / (Vout + Vf)

    # 迭代求解 IL_avg
    IL_avg = Iout / (1 - D)  # 初始: 忽略损耗

    for i in range(100):
        dIL = Vin * D / (L * fsw)
        IQ_rms = math.sqrt(D * (IL_avg**2 + dIL**2 / 12))
        ID_rms = math.sqrt((1 - D) * (IL_avg**2 + dIL**2 / 12))

        # 功率平衡: Vin × IL = Pout + 各项损耗
        Pout = Vout * Iout
        P_MOS = IQ_rms**2 * Rds
        P_diode = Vf * Iout
        P_DCR = IL_avg**2 * DCR
        IL_new = (Pout + P_MOS + P_diode + P_DCR) / Vin

        if verbose and i < 10:
            print(f"  iter {i}: IL={IL_new:.6f}  P_MOS={P_MOS:.4f}  P_DCR={P_DCR:.4f}")

        if abs(IL_new - IL_avg) < 1e-10:
            IL_avg = IL_new
            break
        IL_avg = IL_new

    # 最终计算
    dIL = Vin * D / (L * fsw)
    IL_peak = IL_avg + dIL / 2
    IL_valley = IL_avg - dIL / 2
    IQ_rms = math.sqrt(D * (IL_avg**2 + dIL**2 / 12))
    ID_rms = math.sqrt((1 - D) * (IL_avg**2 + dIL**2 / 12))
    IC_rms = math.sqrt(ID_rms**2 - Iout**2)
    Pin = Vin * IL_avg
    Pout = Vout * Iout
    eta = Pout / Pin
    P_MOS = IQ_rms**2 * Rds
    P_diode = Vf * Iout
    P_DCR = IL_avg**2 * DCR

    # 验证
    kcl_check = (1 - D) * IL_avg
    vs_check = (Vin - IL_avg*(Rds+DCR)) * D + (Vin - Vout - Vf - IL_avg*DCR) * (1-D)

    return {
        'D': D, 'IL_avg': IL_avg, 'dIL': dIL,
        'IL_peak': IL_peak, 'IL_valley': IL_valley,
        'IQ_rms': IQ_rms, 'ID_rms': ID_rms, 'IC_rms': IC_rms,
        'Pin': Pin, 'Pout': Pout, 'eta': eta,
        'P_MOS': P_MOS, 'P_diode': P_diode, 'P_DCR': P_DCR,
        'P_sum': P_MOS + P_diode + P_DCR,
        'kcl_check': kcl_check, 'vs_check': vs_check,
        'iters': i + 1,
    }


# =====================================================================
#  验证
# =====================================================================

Vin, Vout, L, fsw, Iout = 9.0, 30.0, 10e-6, 400e3, 0.5
Vf = 0.7
DCR = 0.3  # 300mΩ
Rds = 0.3  # 300mΩ

print("=" * 70)
print("Step 1d: Vf + DCR + Rds_on 完整模型")
print("=" * 70)
print(f"参数: Vin={Vin}V, Vout={Vout}V, L={L*1e6}µH, fsw={fsw/1e3}kHz")
print(f"      Iout={Iout}A, Vf={Vf}V, DCR={DCR*1000:.0f}mΩ, Rds={Rds*1000:.0f}mΩ\n")

# 迭代过程
print("--- 迭代过程 ---")
r = boost_solve(Vin, Vout, Iout, L, fsw, Vf, DCR, Rds, verbose=True)

print(f"\n--- 结果 ({r['iters']} 步收敛) ---")
print(f"D         = {r['D']:.6f}  (= 1 - Vin/(Vout+Vf), 与 DCR/Rds 无关)")
print(f"IL_avg    = {r['IL_avg']:.4f} A")
print(f"ΔIL       = {r['dIL']:.4f} A")
print(f"IL_peak   = {r['IL_peak']:.4f} A")
print(f"IL_valley = {r['IL_valley']:.4f} A")
print(f"IQ_rms    = {r['IQ_rms']:.4f} A")
print(f"ID_rms    = {r['ID_rms']:.4f} A")
print(f"IC_rms    = {r['IC_rms']:.4f} A")

print(f"\n--- 功率 ---")
print(f"Pin     = {r['Pin']:.4f} W")
print(f"Pout    = {r['Pout']:.4f} W")
print(f"η       = {r['eta']*100:.2f}%")
print(f"P_MOS   = {r['P_MOS']:.4f} W (Rds={Rds*1000:.0f}mΩ)")
print(f"P_diode = {r['P_diode']:.4f} W (Vf={Vf}V)")
print(f"P_DCR   = {r['P_DCR']:.4f} W (DCR={DCR*1000:.0f}mΩ)")
print(f"P_sum   = {r['P_sum']:.4f} W  (≈ Pin-Pout={r['Pin']-r['Pout']:.4f}W)")

# --- 极限验证 ---
print(f"\n--- 极限验证 ---")
cases = [
    ("理想",           0,   0,    0),
    ("仅Vf",           0.7, 0,    0),
    ("仅DCR=300mΩ",    0.7, 0.3,  0),
    ("仅Rds=300mΩ",    0.7, 0,    0.3),
    ("全部",           0.7, 0.3,  0.3),
]
for name, vf, dcr, rds in cases:
    ri = boost_solve(Vin, Vout, Iout, L, fsw, vf, dcr, rds)
    print(f"  {name:<16} D={ri['D']:.4f} IL={ri['IL_avg']:.4f}A "
          f"η={ri['eta']*100:.2f}% Ploss={ri['P_sum']:.4f}W")

# --- D 不变验证 ---
print(f"\n--- D 不变验证 ---")
D_ref = 1 - Vin/(Vout+Vf)
for name, vf, dcr, rds in cases:
    ri = boost_solve(Vin, Vout, Iout, L, fsw, vf, dcr, rds)
    print(f"  {name:<16} D={ri['D']:.6f} == {D_ref:.6f} ? {abs(ri['D']-D_ref)<1e-10}")

# --- 仿真对比表 ---
print(f"\n{'='*70}")
print(f"仿真对比参数表 (Vf={Vf}V, DCR={DCR*1000:.0f}mΩ, Rds={Rds*1000:.0f}mΩ)")
print(f"{'='*70}")
r2 = boost_solve(Vin, Vout, Iout, L, fsw, Vf, DCR, Rds)
print(f"  占空比 D        = {r2['D']:.4f} ({r2['D']*100:.2f}%)")
print(f"  电感平均电流     = {r2['IL_avg']:.4f} A")
print(f"  电感纹波电流     = {r2['dIL']:.4f} A")
print(f"  电感峰值电流     = {r2['IL_peak']:.4f} A")
print(f"  电感谷值电流     = {r2['IL_valley']:.4f} A")
print(f"  MOSFET Irms      = {r2['IQ_rms']:.4f} A")
print(f"  二极管 Irms      = {r2['ID_rms']:.4f} A")
print(f"  电容 Irms        = {r2['IC_rms']:.4f} A")
print(f"  效率 η           = {r2['eta']*100:.2f}%")
