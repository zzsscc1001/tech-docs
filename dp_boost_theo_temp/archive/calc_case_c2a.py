"""
Case C2a 理论计算：DCM + Dd < 0.5 + D < 0.5 + D+Dd < 0.5
双相交错 180° 非同步 Boost

条件：t=0 时 D2 已归零，Phase 2 的 diode 在 Phase 2 off-time 内完成导通
同步方式：同步开沿（Phase 2 在 0.5Ts 开启）

输入参数：Vin, Vout, R, L, Vf, fs, eta
输出：D, Dd, IL_peak, 波形时间边界, Id(t) 波形图

用法：修改底部 if __name__ == "__main__" 中的参数后运行
"""

import math
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def solve_case_c2a(Vin, Vout, R, L, Vf, fs, eta):
    """
    Case C2a 求解器

    返回 dict:
        D: 占空比
        Dd: 二极管占空比 δ
        IL_peak: 二极管电流峰值 (A)
        m: TOFF 下降斜率 (A/s)
        t_boundaries: 关键时间点 (s)
        mode: "C2a" / "C2b" / "C1" / "A"
    """
    Ts = 1.0 / fs

    # --- Step 1: CCM 占空比（用于 CRM 边界计算）---
    D_ccm = 1 - Vin / (Vout + Vf)

    # --- Step 2: 纹波电流（CCM 值，用于 CRM 边界）---
    delta_IL = Vin * D_ccm * Ts / L

    # --- Step 3: CRM 边界 ---
    IL_avg_crm = delta_IL / 2
    Pin_crm = 2 * Vin * IL_avg_crm
    Pout_crm = eta * Pin_crm
    R_crm = Vout**2 / Pout_crm

    # --- Step 4: 判断工作模式 ---
    if R <= R_crm:
        # CCM
        Dd_ccm = 1 - D_ccm
        return {"mode": "A", "R_crm": R_crm, "D": D_ccm, "Dd": Dd_ccm}

    # DCM 求解
    lhs = Vout**2 - (Vin - Vf) * Vout
    rhs_coeff = R * eta * Vin**2 * Ts / L
    D_squared = lhs / rhs_coeff

    if D_squared < 0 or D_squared > 1:
        raise ValueError(f"D²={D_squared:.4f}，参数组合不合法")

    D_dcm = math.sqrt(D_squared)
    delta = D_dcm * Vin / (Vout + Vf - Vin)
    IL_peak = Vin * D_dcm * Ts / L
    m = (Vout + Vf - Vin) / L
    D_plus_Dd = D_dcm + delta

    # 子情况判定
    if D_dcm > 0.5:
        subcase = "C1"
    elif D_plus_Dd < 0.5:
        subcase = "C2a"
    else:
        subcase = "C2b"

    if subcase != "C2a":
        print(f"警告：当前工况是 {subcase}，不是 C2a")

    # --- Step 5: C2a 时间边界（同步开沿）---
    # D1: 下降斜坡 [DTs, (D+Dd)Ts]
    # D2: 下降斜坡 [(0.5+D)Ts, (0.5+D+Dd)Ts]
    t_d1_start = D_dcm * Ts
    t_d1_end = (D_dcm + delta) * Ts
    t_d2_start = (0.5 + D_dcm) * Ts
    t_d2_end = (0.5 + D_dcm + delta) * Ts

    return {
        "mode": subcase,
        "R_crm": R_crm,
        "D": D_dcm,
        "Dd": delta,
        "D_plus_Dd": D_plus_Dd,
        "IL_peak": IL_peak,
        "m": m,
        "D_ccm": D_ccm,
        "t_d1_start": t_d1_start,
        "t_d1_end": t_d1_end,
        "t_d2_start": t_d2_start,
        "t_d2_end": t_d2_end,
    }


def plot_Id_waveform(result, Vin, Vout, R, L, Vf, fs, eta, save_path):
    """画 Case C2a 的 Id(t) 波形"""
    Ts = 1.0 / fs
    D = result["D"]
    delta = result["Dd"]
    IL_peak = result["IL_peak"]
    m = result["m"]
    t_d1s = result["t_d1_start"]
    t_d1e = result["t_d1_end"]
    t_d2s = result["t_d2_start"]
    t_d2e = result["t_d2_end"]

    N = 2000
    t = np.linspace(0, Ts, N)
    Id1 = np.zeros(N)
    Id2 = np.zeros(N)

    for i in range(N):
        ti = t[i]
        # D1: 下降斜坡 [t_d1s, t_d1e]
        if t_d1s <= ti <= t_d1e:
            Id1[i] = IL_peak - m * (ti - t_d1s)
        # D2: 下降斜坡 [t_d2s, t_d2e]
        if t_d2s <= ti <= t_d2e:
            Id2[i] = IL_peak - m * (ti - t_d2s)

    Id = Id1 + Id2
    t_us = t * 1e6

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), facecolor='#1E1E1E')

    # 上图：分相电流
    ax1.set_facecolor('#1E1E1E')
    ax1.plot(t_us, Id1, color='#3b82f6', linewidth=2, label='$I_{d1}$ (Phase 1)')
    ax1.plot(t_us, Id2, color='#f97316', linewidth=2, label='$I_{d2}$ (Phase 2)')
    ax1.fill_between(t_us, Id1, alpha=0.2, color='#3b82f6')
    ax1.fill_between(t_us, Id2, alpha=0.2, color='#f97316')
    for tb in [t_d1s, t_d1e, t_d2s, t_d2e]:
        ax1.axvline(tb * 1e6, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    ax1.set_ylabel('Current (A)', color='#E0E0E0', fontsize=12)
    ax1.set_title(f'Phase Diode Currents — {result["mode"]}', color='#E0E0E0', fontsize=14)
    ax1.legend(loc='upper right', facecolor='#2E2E2E', edgecolor='gray', labelcolor='#E0E0E0')
    ax1.tick_params(colors='#E0E0E0')
    ax1.grid(True, alpha=0.2, color='gray')
    ax1.set_xlim(0, Ts * 1e6)
    ax1.set_ylim(-0.02, IL_peak * 1.4)

    # 下图：总电流
    ax2.set_facecolor('#1E1E1E')
    ax2.plot(t_us, Id, color='#22c55e', linewidth=2.5, label='$I_d = I_{d1}+I_{d2}$')
    ax2.fill_between(t_us, Id, alpha=0.15, color='#22c55e')

    # 参数标注
    params = (f'$V_{{in}}$={Vin}V  $V_{{out}}$={Vout}V  $R$={R}Ω  $L$={L*1e6}µH\n'
              f'$f_s$={fs/1e3}kHz  $\\eta$={eta}\n'
              f'$D$={D:.4f}  $D_d$={delta:.4f}  $D+D_d$={D+delta:.4f}')
    ax2.text(0.02, 0.98, params, transform=ax2.transAxes,
             fontsize=9, verticalalignment='top', fontfamily='monospace',
             color='#E0E0E0', bbox=dict(boxstyle='round', facecolor='#2E2E2E', alpha=0.8))

    # 区间标注（C2a 时序）
    regions = [
        ((0, t_d1s), 'Dead\nZone', '#888888'),
        ((t_d1s, t_d1e), 'D1\nfalling', '#3b82f6'),
        ((t_d1e, t_d2s), 'Dead\nZone', '#888888'),
        ((t_d2s, t_d2e), 'D2\nfalling', '#f97316'),
        ((t_d2e, Ts), 'Dead\nZone', '#888888'),
    ]
    for (t_start, t_end), label, color in regions:
        mid = (t_start + t_end) / 2 * 1e6
        width = (t_end - t_start) * 1e6
        if width > 0.1:  # only label if wide enough
            ax2.text(mid, IL_peak * 0.35, label, ha='center', va='center',
                     color=color, fontsize=9,
                     fontweight='bold' if color != '#888888' else 'normal')

    # 时间标记
    for tb, lbl in [(t_d1s, '$t_{D1,on}$'), (t_d1e, '$t_{D1,off}$'),
                    (t_d2s, '$t_{D2,on}$'), (t_d2e, '$t_{D2,off}$')]:
        ax2.axvline(tb * 1e6, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
        ax2.text(tb * 1e6, -0.015, f'{lbl}\n{tb*1e6:.3f}µs', color='#888888',
                 fontsize=7, ha='center')

    # Peak 标注
    peak_t = (t_d1s + t_d1e) / 2
    ax2.annotate(f'$I_{{L,peak}}$={IL_peak:.4f}A', xy=(t_d1s * 1e6, IL_peak),
                xytext=(0.5, IL_peak * 1.2),
                arrowprops=dict(arrowstyle='->', color='#E0E0E0'),
                color='#E0E0E0', fontsize=10)

    ax2.set_xlabel('Time (µs)', color='#E0E0E0', fontsize=12)
    ax2.set_ylabel('Current (A)', color='#E0E0E0', fontsize=12)
    ax2.set_title('Total Diode Current $I_d(t)$', color='#E0E0E0', fontsize=14)
    ax2.legend(loc='upper right', facecolor='#2E2E2E', edgecolor='gray', labelcolor='#E0E0E0')
    ax2.tick_params(colors='#E0E0E0')
    ax2.grid(True, alpha=0.2, color='gray')
    ax2.set_xlim(0, Ts * 1e6)
    ax2.set_ylim(-0.02, IL_peak * 1.4)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=200, bbox_inches='tight', facecolor='#1E1E1E')
    plt.close()
    return save_path


if __name__ == "__main__":
    # === 输入参数 ===
    Vin = 24.0      # V
    Vout = 40.0      # V
    R = 300.0        # Ω (总负载)
    L = 10e-6        # H (每相)
    Vf = 0.7         # V
    fs = 400e3       # Hz
    eta = 0.95       # 效率

    # === 求解 ===
    result = solve_case_c2a(Vin, Vout, R, L, Vf, fs, eta)

    # === 输出 ===
    print("=" * 50)
    print(f"Case {result['mode']} 理论计算结果")
    print("=" * 50)
    print(f"输入: Vin={Vin}V, Vout={Vout}V, R={R}Ω, L={L*1e6}µH, Vf={Vf}V, fs={fs/1e3}kHz, η={eta}")
    print(f"CRM 边界: R_crm = {result['R_crm']:.1f} Ω")
    print(f"D (CCM) = {result['D_ccm']:.6f}")
    print(f"D (DCM) = {result['D']:.6f}")
    print(f"Dd = δ = {result['Dd']:.6f}")
    print(f"D + Dd = {result['D_plus_Dd']:.6f}")
    print(f"IL_peak = {result['IL_peak']:.4f} A")
    print(f"m = {result['m']:.2e} A/s")
    print()
    print("波形时间边界 (C2a 同步开沿):")
    print(f"  死区①: [0, {result['t_d1_start']*1e6:.4f}] µs")
    print(f"  D1下降: [{result['t_d1_start']*1e6:.4f}, {result['t_d1_end']*1e6:.4f}] µs")
    print(f"  死区②: [{result['t_d1_end']*1e6:.4f}, {result['t_d2_start']*1e6:.4f}] µs")
    print(f"  D2下降: [{result['t_d2_start']*1e6:.4f}, {result['t_d2_end']*1e6:.4f}] µs")
    print(f"  死区③: [{result['t_d2_end']*1e6:.4f}, {1/fs*1e6:.4f}] µs")

    # === 验证 ===
    D = result['D']
    delta = result['Dd']
    IL_peak = result['IL_peak']
    Iout_sp = 0.5 * IL_peak * delta
    Iout_total = 2 * Iout_sp * eta
    Vout_check = Iout_total * R
    print()
    print("验证:")
    print(f"  Iout_sp = IL_peak·δ/2 = {Iout_sp:.4f} A")
    print(f"  Iout_total = 2·Iout_sp·η = {Iout_total:.4f} A")
    print(f"  Vout = Iout·R = {Vout_check:.2f} V (目标 {Vout}V)")

    # === 画图 ===
    out_path = '/tmp/latex_boost/case_c2a_theoretical.png'
    plot_Id_waveform(result, Vin, Vout, R, L, Vf, fs, eta, out_path)
    print(f"\n波形图已保存: {out_path}")
