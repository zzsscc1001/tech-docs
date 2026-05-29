"""
Step 1b: 考虑二极管压降 Vf 的 Boost 稳态分析
=============================================
模型: Vf = 常数 (不随电流变化)

关键区别: Toff 期间电感两端电压从 (Vin-Vout) 变为 (Vin-Vout-Vf)

推导原则: 所有公式从伏秒平衡 + KCL 出发，互相验证一致性
"""

import math

# =====================================================================
#  公式 (含 Vf) — 从伏秒平衡推导出所有结果
# =====================================================================

def boost_duty_Vf(Vin, Vout, Vf):
    """
    占空比 — 从伏秒平衡推导
    ────────────────────────────────────────────────────────
    Ton:  VL = Vin
    Toff: VL = Vin - Vout - Vf   ← 二极管压降使去磁电压更负

    伏秒平衡: Vin·D + (Vin - Vout - Vf)·(1-D) = 0
    展开:     Vin·D + Vin - Vin·D - Vout + Vf·D - Vf + Vout·D + Vf·D = 0
    整理:     (Vin - Vf) + D·(Vout + Vf) = Vout + Vf... 不对，重新来

    Vin·D + (Vin - Vout - Vf)·(1-D) = 0
    Vin·D + Vin - Vin·D - (Vout+Vf)(1-D) = 0
    Vin - (Vout+Vf)(1-D) = 0
    (Vout+Vf)(1-D) = Vin
    1-D = Vin / (Vout+Vf)

    → D = 1 - Vin/(Vout+Vf)

    含义: Toff 期间有效输出电压为 (Vout+Vf)，占空比因此增大
    ────────────────────────────────────────────────────────
    """
    return 1 - Vin / (Vout + Vf)

def boost_IL_avg_Vf(Iout, Vin, Vout, Vf):
    """
    电感平均电流
    ────────────────────────────────────────────────────────
    从 KCL + 伏秒平衡推导:
        KCL:  Iout = (1-D) × IL_avg
        伏秒: (1-D) = Vin / (Vout + Vf)

        → IL_avg = Iout / (1-D) = Iout × (Vout + Vf) / Vin

    功率视角:
        Pin = Vin × IL_avg = Iout × (Vout + Vf)
        Pout = Vout × Iout
        P_diode_total = Vf × Iout  (二极管导通损耗)

        Pin = Pout + P_diode ✓
    ────────────────────────────────────────────────────────
    """
    return Iout * (Vout + Vf) / Vin

def boost_delta_IL_Vf(Vin, D, L, fsw):
    """
    电感纹波电流
    ────────────────────────────────────────────────────────
    公式形式不变: ΔIL = Vin × D / (L × fsw)
    (Ton 期间 Vf 不参与，VL = Vin 不变)

    但 D 增大 → ΔIL 数值增大
    ────────────────────────────────────────────────────────
    """
    return Vin * D / (L * fsw)

def boost_Lcrit_Vf(Vin, Vout, Vf, fsw, Iout):
    """
    临界电感
    ────────────────────────────────────────────────────────
    临界条件: IL_avg = ΔIL/2

    左边: IL_avg = Iout × (Vout + Vf) / Vin
    右边: ΔIL/2 = Vin × D / (2 × L × fsw)
                = Vin × [1 - Vin/(Vout+Vf)] / (2 × L × fsw)
                = Vin × (Vout+Vf-Vin) / [(Vout+Vf) × 2 × L × fsw]

    令两边相等:
    Iout(Vout+Vf)/Vin = Vin(Vout+Vf-Vin) / [(Vout+Vf)·2·Lcrit·fsw]

    → Lcrit = Vin² × (Vout+Vf-Vin) / [2 × (Vout+Vf)² × Iout × fsw]

    当 Vf=0 时 → Lcrit = Vin²(Vout-Vin)/(2·Vout²·Iout·fsw) ✓
    ────────────────────────────────────────────────────────
    """
    return Vin**2 * (Vout + Vf - Vin) / (2 * (Vout + Vf)**2 * Iout * fsw)

def boost_IQ_rms(IL_avg, delta_IL, D):
    """MOSFET RMS — 公式形式不变，数值因 IL_avg/D 变化而变"""
    return math.sqrt(D * (IL_avg**2 + delta_IL**2 / 12))

def boost_ID_rms(IL_avg, delta_IL, D):
    """二极管 RMS — 公式形式不变"""
    return math.sqrt((1 - D) * (IL_avg**2 + delta_IL**2 / 12))

def boost_IC_rms(ID_rms, Iout):
    """输出电容 RMS — 公式形式不变"""
    return math.sqrt(ID_rms**2 - Iout**2)


# =====================================================================
#  数值验证 & 交叉验证
# =====================================================================

Vin, Vout, L, fsw, Iout = 9.0, 30.0, 10e-6, 400e3, 0.5
Vf = 0.7

print("=" * 65)
print("Step 1b: 二极管压降 Vf 对 Boost 稳态的影响")
print("=" * 65)
print(f"参数: Vin={Vin}V, Vout={Vout}V, L={L*1e6}µH, fsw={fsw/1e3}kHz, Iout={Iout}A, Vf={Vf}V\n")

# --- 理想 ---
D_i = 1 - Vin / Vout
IL_i = Iout / (1 - D_i)
dIL_i = Vin * D_i / (L * fsw)

# --- 含 Vf ---
D_f = boost_duty_Vf(Vin, Vout, Vf)
IL_f = boost_IL_avg_Vf(Iout, Vin, Vout, Vf)
dIL_f = boost_delta_IL_Vf(Vin, D_f, L, fsw)
Lcrit_f = boost_Lcrit_Vf(Vin, Vout, Vf, fsw, Iout)
IQ_f = boost_IQ_rms(IL_f, dIL_f, D_f)
ID_f = boost_ID_rms(IL_f, dIL_f, D_f)
IC_f = boost_IC_rms(ID_f, Iout)

# --- 对比 ---
print(f"{'参数':<18} {'理想':<14} {'含Vf={Vf}V':<14} {'变化':<14}")
print("-" * 60)
print(f"{'D':<18} {D_i:<14.4f} {D_f:<14.4f} +{D_f-D_i:.4f}")
print(f"{'IL_avg (A)':<18} {IL_i:<14.4f} {IL_f:<14.4f} +{IL_f-IL_i:.4f}")
print(f"{'ΔIL (A)':<18} {dIL_i:<14.4f} {dIL_f:<14.4f} +{dIL_f-dIL_i:.4f}")
print(f"{'IL_peak (A)':<18} {IL_i+dIL_i/2:<14.4f} {IL_f+dIL_f/2:<14.4f} +{(IL_f-IL_i)+(dIL_f-dIL_i)/2:.4f}")
print(f"{'Lcrit (µH)':<18} {'—':<14} {Lcrit_f*1e6:<14.2f}")
print(f"{'IQ_rms (A)':<18} {'—':<14} {IQ_f:<14.4f}")
print(f"{'ID_rms (A)':<18} {'—':<14} {ID_f:<14.4f}")
print(f"{'IC_rms (A)':<18} {'—':<14} {IC_f:<14.4f}")
print(f"{'Pin (W)':<18} {Vin*IL_i:<14.4f} {Vin*IL_f:<14.4f}")
print(f"{'Pout (W)':<18} {Vout*Iout:<14.4f} {Vout*Iout:<14.4f}")
print(f"{'P_diode (W)':<18} {'0.0000':<14} {Vf*Iout:<14.4f}")
print(f"{'η (%)':<18} {'100.00':<14} {Vout/(Vout+Vf)*100:<14.2f}")

# --- 一致性验证 ---
print(f"\n{'='*65}")
print("一致性验证")
print(f"{'='*65}")

# 验证1: 功率平衡
Pin_f = Vin * IL_f
Pout_f = Vout * Iout
Pdiode_f = Vf * Iout
print(f"[功率] Pin={Pin_f:.4f}W == Pout+Pdiode={Pout_f+Pdiode_f:.4f}W ? {abs(Pin_f-Pout_f-Pdiode_f)<0.001} ✓")

# 验证2: KCL
IL_from_KCL = Iout / (1 - D_f)
print(f"[KCL]  IL_avg = Iout/(1-D) = {IL_from_KCL:.4f}A == {IL_f:.4f}A ? {abs(IL_from_KCL-IL_f)<0.001} ✓")

# 验证3: 伏秒平衡
vs_on = Vin * D_f
vs_off = (Vin - Vout - Vf) * (1 - D_f)
print(f"[伏秒] Vin·D={vs_on:.4f} + (Vin-Vout-Vf)·(1-D)={vs_off:.4f} = {vs_on+vs_off:.6f} ≈ 0 ? {abs(vs_on+vs_off)<0.001} ✓")

# 验证4: Lcrit 自洽 (代入 Lcrit 应得 IL_valley=0)
dIL_crit = boost_delta_IL_Vf(Vin, D_f, Lcrit_f, fsw)
IL_crit = boost_IL_avg_Vf(Iout, Vin, Vout, Vf)
IL_valley_crit = IL_crit - dIL_crit / 2
print(f"[Lcrit] 代入Lcrit → IL_valley = {IL_valley_crit:.8f} ≈ 0 ? {abs(IL_valley_crit)<0.01} ✓")
