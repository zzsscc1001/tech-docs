"""
Step 1: 单相 Boost 稳态工作点 — 通用公式推导 (修正版)
======================================================
目标: 建立完整的稳态分析公式体系
验证: 代入 Vin=9V, Vout=30V, L=10µH, fsw=400kHz, Iout=0.5A

修正记录:
  v1 → v2: Lcrit 公式错误，原文使用了 Iout 代入 IL_avg 的公式
           正确推导应从 IL_avg = ΔIL/2 出发，不经过 Iout
"""

import math

# =====================================================================
#  通用公式 — 理想 CCM Boost
# =====================================================================

def boost_duty_cycle(Vin, Vout):
    """
    占空比 (CCM)
    ────────────────────────────────────────────────────────
    推导: 电感伏秒平衡
        Ton 期间:  VL = Vin            (Q导通，L充磁，电流上升)
        Toff期间:  VL = Vin - Vout     (D导通，L去磁，电流下降)
        伏秒平衡:  Vin·D·T + (Vin-Vout)·(1-D)·T = 0
        解出:      D = 1 - Vin/Vout
    ────────────────────────────────────────────────────────
    """
    return 1 - Vin / Vout

def boost_IL_avg(Iout, D):
    """
    电感平均电流 (= 输入平均电流)
    ────────────────────────────────────────────────────────
    推导: 输出节点 KCL (平均值)
        电感电流仅在 (1-D)T 期间流过二极管到达输出
        I_out = IL_avg × (1-D)
        → IL_avg = Iout / (1-D)
    ────────────────────────────────────────────────────────
    """
    return Iout / (1 - D)

def boost_delta_IL(Vin, D, L, fsw):
    """
    电感电流纹波 (峰峰值)
    ────────────────────────────────────────────────────────
    推导: Q导通期间，电感两端电压 = Vin
        VL = L × di/dt  →  ΔIL = Vin × Ton / L
        Ton = D / fsw
        → ΔIL = Vin × D / (L × fsw)
    ────────────────────────────────────────────────────────
    """
    return Vin * D / (L * fsw)

def boost_IL_peak(IL_avg, delta_IL):
    """电感峰值电流 = IL_avg + ΔIL/2"""
    return IL_avg + delta_IL / 2

def boost_IL_valley(IL_avg, delta_IL):
    """电感谷值电流 = IL_avg - ΔIL/2"""
    return IL_avg - delta_IL / 2

def boost_CCM_check(IL_avg, delta_IL):
    """
    CCM 判据
    ────────────────────────────────────────────────────────
    CCM: IL_valley > 0  ⟺  IL_avg > ΔIL/2
    临界: IL_avg = ΔIL/2
    DCM: IL_valley = 0 (电流降到零后保持为零)
    ────────────────────────────────────────────────────────
    """
    return IL_avg > delta_IL / 2

def boost_Lcrit(Vin, Vout, fsw, Iout):
    """
    临界电感 (CCM/DCM 边界)
    ────────────────────────────────────────────────────────
    推导: 从临界条件 IL_avg = ΔIL/2 出发

        左边: IL_avg = Iout / (1-D)
        右边: ΔIL/2 = Vin·D / (2·L·fsw)

        临界时: Iout/(1-D) = Vin·D/(2·Lcrit·fsw)
        → Lcrit = Vin·D·(1-D) / (2·Iout·fsw)

        代入 D = 1-Vin/Vout:
            D·(1-D) = (1-Vin/Vout)·(Vin/Vout) = Vin(Vout-Vin)/Vout²
        → Lcrit = Vin²·(Vout-Vin) / (2·Vout²·Iout·fsw)

        **注意**: 公式中有 Vout² 而非 Vout，这是 v1 版本的错误来源

        判据: L > Lcrit → CCM;  L < Lcrit → DCM
    ────────────────────────────────────────────────────────
    """
    return Vin**2 * (Vout - Vin) / (2 * Vout**2 * Iout * fsw)

def boost_IQ_rms(IL_avg, delta_IL, D):
    """
    MOSFET 电流有效值
    ────────────────────────────────────────────────────────
    推导: Q 仅在 DT 期间导通，电流 = IL(t)
        I_Q² = (1/T) × ∫₀^DT IL²(t) dt

        IL(t) 在 Ton 内为三角波，对称于 IL_avg
        积分结果: I_Q² = D × (IL_avg² + ΔIL²/12)
        → I_Q_rms = √[ D × (IL_avg² + ΔIL²/12) ]

        简化近似 (纹波小时): I_Q_rms ≈ IL_avg × √D
    ────────────────────────────────────────────────────────
    """
    return math.sqrt(D * (IL_avg**2 + delta_IL**2 / 12))

def boost_ID_rms(IL_avg, delta_IL, D):
    """
    二极管电流有效值
    ────────────────────────────────────────────────────────
    推导: D 仅在 (1-D)T 期间导通，电流 = IL(t)
        I_D² = (1/T) × ∫_{DT}^T IL²(t) dt
        → I_D_rms² = (1-D) × (IL_avg² + ΔIL²/12)
    ────────────────────────────────────────────────────────
    """
    return math.sqrt((1 - D) * (IL_avg**2 + delta_IL**2 / 12))

def boost_ID_avg(IL_avg, D):
    """二极管平均电流 = Iout (由输出KCL直接得出)"""
    return IL_avg * (1 - D)

def boost_ICout_rms(ID_rms, Iout):
    """
    输出电容纹波电流有效值
    ────────────────────────────────────────────────────────
    推导: 电容电流 = 二极管电流 - 负载电流
        iC(t) = iD(t) - Iout

        RMS: IC² = <(iD - Iout)²> = <iD²> - 2·Iout·<iD> + Iout²
             = ID_rms² - 2·Iout·ID_avg + Iout²
             = ID_rms² - 2·Iout² + Iout²     (因为 ID_avg = Iout)
             = ID_rms² - Iout²
        → IC_rms = √(ID_rms² - Iout²)
    ────────────────────────────────────────────────────────
    """
    return math.sqrt(ID_rms**2 - Iout**2)


# =====================================================================
#  数值验证
# =====================================================================

print("=" * 60)
print("Step 1: 单相 Boost 稳态工作点 — 公式验证")
print("=" * 60)

Vin, Vout, L, fsw, Iout = 9.0, 30.0, 10e-6, 400e3, 0.5
print(f"\n参数: Vin={Vin}V, Vout={Vout}V, L={L*1e6}µH, fsw={fsw/1e3}kHz, Iout={Iout}A\n")

D = boost_duty_cycle(Vin, Vout)
print(f"[1] D = 1 - Vin/Vout = {D:.4f}")

IL_avg = boost_IL_avg(Iout, D)
print(f"[2] IL_avg = Iout/(1-D) = {IL_avg:.4f} A")

delta_IL = boost_delta_IL(Vin, D, L, fsw)
print(f"[3] ΔIL = Vin·D/(L·fsw) = {delta_IL:.4f} A")

IL_peak = boost_IL_peak(IL_avg, delta_IL)
IL_valley = boost_IL_valley(IL_avg, delta_IL)
print(f"[4] IL_peak  = {IL_peak:.4f} A")
print(f"    IL_valley = {IL_valley:.4f} A")

is_CCM = boost_CCM_check(IL_avg, delta_IL)
print(f"[5] CCM? IL_avg({IL_avg:.4f}) > ΔIL/2({delta_IL/2:.4f}) → {is_CCM}")

Lcrit = boost_Lcrit(Vin, Vout, fsw, Iout)
print(f"[6] Lcrit = Vin²(Vout-Vin)/(2·Vout²·Iout·fsw) = {Lcrit*1e6:.4f} µH")
print(f"    L({L*1e6:.0f}µH) {'>' if L > Lcrit else '<'} Lcrit({Lcrit*1e6:.2f}µH) → {'CCM' if L > Lcrit else 'DCM'}")

# 验证 Lcrit 自洽性: 代入 Lcrit 应得到 IL_valley = 0
delta_IL_crit = boost_delta_IL(Vin, D, Lcrit, fsw)
IL_avg_crit = boost_IL_avg(Iout, D)
IL_valley_crit = boost_IL_valley(IL_avg_crit, delta_IL_crit)
print(f"    验证: 代入 Lcrit → IL_valley = {IL_valley_crit:.8f} ≈ 0 ✓")

IQ_rms = boost_IQ_rms(IL_avg, delta_IL, D)
ID_rms = boost_ID_rms(IL_avg, delta_IL, D)
ID_avg = boost_ID_avg(IL_avg, D)
IC_rms = boost_ICout_rms(ID_rms, Iout)
print(f"[7] IQ_rms={IQ_rms:.4f}A  ID_rms={ID_rms:.4f}A  ID_avg={ID_avg:.4f}A  IC_rms={IC_rms:.4f}A")

Pin, Pout = Vin * IL_avg, Vout * Iout
print(f"[8] Pin={Pin:.4f}W  Pout={Pout:.4f}W  (理想 η=100%)")
