"""
Step 1c: Vf + DCR 迭代求解模型
================================
独立参数: Vin, Vout, Iout, L, fsw, Vf, DCR
方法: 固定点迭代 (KCL + 伏秒平衡)
η 是推导结果，不是输入
"""

import math

# =====================================================================
#  Case 1: 仅 Vf (解析解，已验证)
# =====================================================================

def boost_vf_only(Vin, Vout, Iout, L, fsw, Vf):
    """仅考虑 Vf，解析解"""
    D = 1 - Vin / (Vout + Vf)
    IL_avg = Iout / (1 - D)
    dIL = Vin * D / (L * fsw)
    eta = Vout / (Vout + Vf)
    return D, IL_avg, dIL, eta


# =====================================================================
#  Case 2: Vf + DCR (迭代求解)
# =====================================================================

def boost_vf_dcr_iterate(Vin, Vout, Iout, L, fsw, Vf, DCR, tol=1e-8, max_iter=50):
    """
    迭代求解 Vf + DCR

    伏秒平衡 (无 R_ML):
        Vin·D = (Vout + Vf + IL·DCR - Vin)·(1-D)
        → D = (Vout + Vf + IL·DCR - Vin) / (Vout + Vf + IL·DCR)

    KCL:
        IL_avg = Iout / (1-D)

    迭代: 从理想 IL_avg 开始，交替代入直到收敛
    """
    # 初始值: 理想 (无损耗)
    IL_avg = Iout * Vout / Vin

    history = []
    for i in range(max_iter):
        # 伏秒平衡 → D (用当前 IL_avg)
        D = (Vout + Vf + IL_avg * DCR - Vin) / (Vout + Vf + IL_avg * DCR)

        # KCL → IL_avg (用新的 D)
        IL_new = Iout / (1 - D)

        err = abs(IL_new - IL_avg)
        history.append({
            'iter': i, 'IL': IL_new, 'D': D, 'err': err
        })

        if err < tol:
            IL_avg = IL_new
            break
        IL_avg = IL_new

    # 纹波
    VL_ton = Vin  # 无 R_ML，Ton 期间 VL = Vin
    dIL = VL_ton * D / (L * fsw)

    # 效率
    Pin = Vin * IL_avg
    Pout = Vout * Iout
    eta = Pout / Pin

    # 损耗
    P_diode = Vf * Iout
    P_DCR = IL_avg**2 * DCR

    return {
        'D': D, 'IL_avg': IL_avg, 'dIL': dIL, 'eta': eta,
        'P_diode': P_diode, 'P_DCR': P_DCR, 'Ploss': Pin - Pout,
        'VL_ton': VL_ton, 'VL_toff': Vin - Vout - Vf - IL_avg * DCR,
        'history': history,
    }


# =====================================================================
#  验证 & 对比
# =====================================================================

Vin, Vout, L, fsw, Iout = 9.0, 30.0, 10e-6, 400e3, 0.5
Vf = 0.7
DCR = 0.05  # 50mΩ

print("=" * 70)
print("Step 1c: Vf + DCR 迭代模型")
print("=" * 70)
print(f"参数: Vin={Vin}V, Vout={Vout}V, L={L*1e6}µH, fsw={fsw/1e3}kHz")
print(f"      Iout={Iout}A, Vf={Vf}V, DCR={DCR}Ω\n")

# --- Case 1: 仅 Vf ---
D1, IL1, dIL1, eta1 = boost_vf_only(Vin, Vout, Iout, L, fsw, Vf)
print(f"Case 1: 仅 Vf (解析)")
print(f"  D = {D1:.6f}, IL_avg = {IL1:.4f}A, η = {eta1*100:.2f}%\n")

# --- Case 2: Vf + DCR ---
r2 = boost_vf_dcr_iterate(Vin, Vout, Iout, L, fsw, Vf, DCR)
print(f"Case 2: Vf + DCR (迭代)")
print(f"  D = {r2['D']:.6f}, IL_avg = {r2['IL_avg']:.4f}A, η = {r2['eta']*100:.2f}%")
print(f"  ΔIL = {r2['dIL']:.4f}A")
print(f"  VL_ton = {r2['VL_ton']:.4f}V, VL_toff = {r2['VL_toff']:.4f}V")
print(f"  P_diode = {r2['P_diode']:.4f}W, P_DCR = {r2['P_DCR']:.4f}W")

# --- KCL 验证 ---
Iout_check = (1 - r2['D']) * r2['IL_avg']
print(f"\n  KCL: (1-D)×IL = {Iout_check:.8f} == {Iout} ? {abs(Iout_check-Iout)<1e-8} ✓")

# --- 伏秒验证 ---
vs = r2['VL_ton'] * r2['D'] + r2['VL_toff'] * (1 - r2['D'])
print(f"  伏秒: {vs:.10f} ≈ 0 ? {abs(vs)<1e-6} ✓")

# --- 收敛过程 ---
print(f"\n--- 迭代收敛 ---")
print(f"  {'迭代':<6} {'IL_avg(A)':<14} {'D':<12} {'误差':<12}")
for h in r2['history']:
    print(f"  {h['iter']:<6} {h['IL']:<14.8f} {h['D']:<12.8f} {h['err']:<12.2e}")

# --- 极限验证 ---
print(f"\n--- 极限验证 ---")
# DCR=0 → 应退化为 Case 1
r_dc = boost_vf_dcr_iterate(Vin, Vout, Iout, L, fsw, Vf, 0)
print(f"DCR=0: D={r_dc['D']:.6f} vs Case1 D={D1:.6f} ? {abs(r_dc['D']-D1)<1e-8} ✓")
print(f"       IL={r_dc['IL_avg']:.4f} vs Case1 IL={IL1:.4f} ? {abs(r_dc['IL_avg']-IL1)<1e-8} ✓")

# Vf=0, DCR=0 → 理想
r_id = boost_vf_dcr_iterate(Vin, Vout, Iout, L, fsw, 0, 0)
D_ideal = 1 - Vin/Vout
print(f"理想:  D={r_id['D']:.6f} vs {D_ideal:.6f} ? {abs(r_id['D']-D_ideal)<1e-8} ✓")

# --- DCR 敏感度 ---
print(f"\n--- DCR 敏感度 (Vf={Vf}V 固定) ---")
print(f"  {'DCR(mΩ)':<10} {'D':<12} {'IL_avg(A)':<12} {'η(%)':<10} {'ΔD':<10}")
for dcr_val in [0, 0.01, 0.02, 0.05, 0.1, 0.2]:
    ri = boost_vf_dcr_iterate(Vin, Vout, Iout, L, fsw, Vf, dcr_val)
    print(f"  {dcr_val*1000:<10.0f} {ri['D']:<12.6f} {ri['IL_avg']:<12.4f} "
          f"{ri['eta']*100:<10.2f} {ri['D']-D1:+.6f}")
