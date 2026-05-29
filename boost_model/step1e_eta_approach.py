"""
Step 1e: η 预设 + KCL 反推 + 精确 ΔIL 模型
=============================================
方法:
  1. η 预设 → IL_avg = Vout·Iout/(η·Vin)
  2. D = 1 - Iout/IL_avg  (KCL 反推，不依赖伏秒平衡)
  3. ΔIL 积分求解 (考虑 Rds+DCR 压降的梯形电压)
  4. 波形分析: 三角波近似 → RMS
  5. 损耗计算 → 验证 η
"""

import math

def boost_eta_model(Vin, Vout, Iout, L, fsw, Vf, DCR, Rds, eta_set):
    """
    η 预设模型

    ────────────────────────────────────────────────────────
    Step 1: IL_avg from η
        Pin = Pout/η = Vout·Iout/η
        IL_avg = Pin/Vin = Vout·Iout/(η·Vin)

    Step 2: D from KCL
        Iout = (1-D)·IL_avg
        D = 1 - Iout/IL_avg

    Step 3: ΔIL (精确积分)
        Ton 期间: VL(t) = Vin - i(t)·(Rds+DCR)
        i(t) = IL_valley + (ΔIL/Ton)·t

        令 R_ton = Rds + DCR
        ∫₀^Ton VL dt = Vin·Ton - R_ton·∫₀^Ton i(t) dt

        ∫₀^Ton i(t) dt = IL_valley·Ton + ΔIL·Ton/2
                        = (IL_avg - ΔIL/2)·Ton + ΔIL·Ton/2
                        = IL_avg·Ton

        → ΔIL = (Vin - IL_avg·R_ton)·D/(L·fsw)

        Toff 期间验证:
        ΔIL = (Vout + Vf - Vin + IL_avg·DCR)·(1-D)/(L·fsw)
        → 两个公式应一致 (自洽检查)

    Step 4: 波形 (三角波近似)
        IL(t) 在 Ton: IL_valley → IL_peak (线性)
        IL(t) 在 Toff: IL_peak → IL_valley (线性)

        i_MOS(t) = IL(t) during Ton, 0 during Toff
        i_D(t)   = 0 during Ton, IL(t) during Toff

    Step 5: RMS
        IQ_rms² = (1/T)·∫₀^Ton IL²(t) dt
                = D·(IL_avg² + ΔIL²/12)  (三角波 RMS 公式)

        ID_rms² = (1-D)·(IL_avg² + ΔIL²/12)

    Step 6: 损耗 & η 验证
        P_MOS = IQ_rms²·Rds
        P_DCR = IL_avg²·DCR
        P_diode = Vf·Iout
        Pin_actual = Vin·IL_avg
        Pout = Vout·Iout
        η_actual = Pout / Pin_actual
        P_sum = P_MOS + P_diode + P_DCR
        检查: Pin_actual - Pout ≈ P_sum ?
    ────────────────────────────────────────────────────────
    """
    # Step 1: IL_avg
    IL_avg = Vout * Iout / (eta_set * Vin)

    # Step 2: D (KCL)
    D = 1 - Iout / IL_avg

    # Step 3: ΔIL (考虑 Rds+DCR)
    R_ton = Rds + DCR
    dIL = (Vin - IL_avg * R_ton) * D / (L * fsw)

    # 验证: 从 Toff 侧算 ΔIL
    dIL_check = (Vout + Vf - Vin + IL_avg * DCR) * (1 - D) / (L * fsw)

    # Step 4: 峰值/谷值
    IL_peak = IL_avg + dIL / 2
    IL_valley = IL_avg - dIL / 2

    # Step 5: RMS
    IQ_rms = math.sqrt(D * (IL_avg**2 + dIL**2 / 12))
    ID_rms = math.sqrt((1 - D) * (IL_avg**2 + dIL**2 / 12))
    IC_rms = math.sqrt(ID_rms**2 - Iout**2)

    # Step 6: 损耗 & η
    P_MOS = IQ_rms**2 * Rds
    P_diode = Vf * Iout
    P_DCR = IL_avg**2 * DCR
    P_sum = P_MOS + P_diode + P_DCR
    Pin = Vin * IL_avg
    Pout = Vout * Iout
    eta_actual = Pout / Pin

    return {
        'D': D, 'IL_avg': IL_avg, 'dIL': dIL, 'dIL_check': dIL_check,
        'IL_peak': IL_peak, 'IL_valley': IL_valley,
        'IQ_rms': IQ_rms, 'ID_rms': ID_rms, 'IC_rms': IC_rms,
        'Pin': Pin, 'Pout': Pout,
        'eta_set': eta_set, 'eta_actual': eta_actual,
        'P_MOS': P_MOS, 'P_diode': P_diode, 'P_DCR': P_DCR,
        'P_sum': P_sum,
        'kcl_check': (1 - D) * IL_avg,
    }


def boost_iterate_eta(Vin, Vout, Iout, L, fsw, Vf, DCR, Rds, tol=1e-8, max_iter=100):
    """
    自洽迭代: 从 η 出发，算损耗，更新 η，直到收敛

    逻辑:
      η_n → IL_avg → D → ΔIL → RMS → 损耗
      η_{n+1} = Pout / (Pout + P_sum)
      收敛条件: |η_{n+1} - η_n| < tol
    """
    # 初始 η: 仅 Vf
    eta = Vout / (Vout + Vf)

    for i in range(max_iter):
        r = boost_eta_model(Vin, Vout, Iout, L, fsw, Vf, DCR, Rds, eta)
        eta_new = Vout * Iout / (Vout * Iout + r['P_sum'])

        if abs(eta_new - eta) < tol:
            return r, i + 1
        eta = eta_new

    return r, max_iter


# =====================================================================
#  验证
# =====================================================================

Vin, Vout, L, fsw, Iout = 9.0, 30.0, 10e-6, 400e3, 0.5
Vf = 0.7
DCR = 0.3
Rds = 0.3

print("=" * 70)
print("Step 1e: η 预设 + KCL 反推 + 精确 ΔIL")
print("=" * 70)
print(f"参数: Vin={Vin}V, Vout={Vout}V, L={L*1e6}µH, fsw={fsw/1e3}kHz")
print(f"      Iout={Iout}A, Vf={Vf}V, DCR={DCR*1000:.0f}mΩ, Rds={Rds*1000:.0f}mΩ\n")

# --- 自洽迭代 ---
r, n_iters = boost_iterate_eta(Vin, Vout, Iout, L, fsw, Vf, DCR, Rds)

print(f"--- 自洽结果 ({n_iters} 步) ---")
print(f"η (自洽)  = {r['eta_actual']*100:.4f}%")
print(f"D         = {r['D']:.6f}  (KCL 反推，不依赖伏秒)")
print(f"IL_avg    = {r['IL_avg']:.4f} A")
print(f"ΔIL       = {r['dIL']:.4f} A")
print(f"ΔIL_check = {r['dIL_check']:.4f} A  (Toff 侧验证)")
print(f"IL_peak   = {r['IL_peak']:.4f} A")
print(f"IL_valley = {r['IL_valley']:.4f} A")
print(f"IQ_rms    = {r['IQ_rms']:.4f} A")
print(f"ID_rms    = {r['ID_rms']:.4f} A")
print(f"IC_rms    = {r['IC_rms']:.4f} A")

print(f"\n--- 功率平衡 ---")
print(f"Pin     = {r['Pin']:.4f} W")
print(f"Pout    = {r['Pout']:.4f} W")
print(f"P_MOS   = {r['P_MOS']:.4f} W (Rds)")
print(f"P_diode = {r['P_diode']:.4f} W (Vf)")
print(f"P_DCR   = {r['P_DCR']:.4f} W (DCR)")
print(f"P_sum   = {r['P_sum']:.4f} W")
print(f"Pin-Pout= {r['Pin']-r['Pout']:.4f} W  (应 ≈ P_sum)")

# --- KCL 验证 ---
print(f"\n--- 验证 ---")
print(f"KCL: (1-D)×IL = {r['kcl_check']:.8f} == {Iout} ? {abs(r['kcl_check']-Iout)<1e-8}")
print(f"ΔIL: Ton侧={r['dIL']:.6f} vs Toff侧={r['dIL_check']:.6f} ? {abs(r['dIL']-r['dIL_check'])<1e-6}")

# --- ΔIL 中 Rds+DCR 的修正量 ---
dIL_ideal = Vin * r['D'] / (L * fsw)
print(f"\n--- ΔIL 修正 ---")
print(f"ΔIL (无 Rds/DCR) = {dIL_ideal:.6f} A")
print(f"ΔIL (有 Rds/DCR) = {r['dIL']:.6f} A")
print(f"修正量            = {r['dIL']-dIL_ideal:+.6f} A ({(r['dIL']/dIL_ideal-1)*100:+.2f}%)")

# --- 仿真对比 ---
print(f"\n{'='*70}")
print("仿真对比")
print(f"{'='*70}")
print(f"{'参数':<14} {'模型':<12} {'仿真':<12} {'误差':<10}")
print("-" * 48)
print(f"{'IL_peak(A)':<14} {r['IL_peak']:<12.4f} {'2.648':<12} {(r['IL_peak']-2.648)/2.648*100:+.2f}%")
print(f"{'IL_avg(A)':<14} {r['IL_avg']:<12.4f} {'1.933':<12} {(r['IL_avg']-1.933)/1.933*100:+.2f}%")
print(f"{'IL_valley(A)':<14} {r['IL_valley']:<12.4f} {'1.199':<12} {(r['IL_valley']-1.199)/1.199*100:+.2f}%")
D_sim = 1 - 0.5/1.933
print(f"{'D':<14} {r['D']:<12.4f} {D_sim:<12.4f} {(r['D']-D_sim)/D_sim*100:+.2f}%")
