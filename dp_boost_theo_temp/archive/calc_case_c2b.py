"""
Case C2b 理论计算：DCM + Dd < 0.5 + D < 0.5 + D+Dd > 0.5
双相交错 180° 非同步 Boost

条件：t=0 时 Phase 2 二极管仍在导通（从上周期延续），D2 跨越周期边界
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


def solve_case_c2b(Vin, Vout, R, L, Vf, fs, eta):
    """
    Case C2b 求解器

    返回 dict:
        D: 占空比
        Dd: 二极管占空比 δ
        IL_peak: 二极管电流峰值 (A)
        m: TOFF 下降斜率 (A/s)
        时间边界和电流值
    """
    Ts = 1.0 / fs

    # DCM 求解（不经过 CCM D 公式）
    lhs = Vout**2 - (Vin - Vf) * Vout
    rhs_coeff = R * eta * Vin**2 * Ts / L
    D_squared = lhs / rhs_coeff

    if D_squared < 0 or D_squared > 1:
        raise ValueError(f"D²={D_squared:.4f}，参数组合不合法")

    D = math.sqrt(D_squared)
    Dd = D * Vin / (Vout + Vf - Vin)
    IL_peak = Vin * D * Ts / L
    m = (Vout + Vf - Vin) / L
    D_plus_Dd = D + Dd

    # 子情况判定
    if D > 0.5:
        subcase = "C1"
    elif D_plus_Dd < 0.5:
        subcase = "C2a"
    else:
        subcase = "C2b"

    if subcase != "C2b":
        print(f"警告：当前工况是 {subcase}，不是 C2b")

    # CRM 边界
    D_boundary = (Vout + Vf - Vin) / (Vout + Vf)
    R_crm = (Vout**2 - (Vin - Vf) * Vout) * L / (D_boundary**2 * eta * Vin**2 * Ts)

    # C2b 时间边界
    # D2 第一段（尾部）: [0, (D+Dd-0.5)Ts]，从 Id2_at_t0 衰减到 0
    t_d2_tail_end = (D + Dd - 0.5) * Ts
    Id2_at_t0 = IL_peak - m * (0.5 - D) * Ts  # t=0 时的 D2 电流

    # D1: [DTs, (D+Dd)Ts]
    t_d1_start = D * Ts
    t_d1_end = (D + Dd) * Ts

    # D2 第二段（主脉冲）: [(0.5+D)Ts, (0.5+D+Dd)Ts]，从 IL_peak 衰减到 0
    t_d2_main_start = (0.5 + D) * Ts
    t_d2_main_end = (0.5 + D + Dd) * Ts

    return {
        "mode": subcase,
        "R_crm": R_crm,
        "D": D,
        "Dd": Dd,
        "D_plus_Dd": D_plus_Dd,
        "IL_peak": IL_peak,
        "m": m,
        "Id2_at_t0": Id2_at_t0,
        "t_d2_tail_end": t_d2_tail_end,
        "t_d1_start": t_d1_start,
        "t_d1_end": t_d1_end,
        "t_d2_main_start": t_d2_main_start,
        "t_d2_main_end": t_d2_main_end,
    }


def plot_Id_waveform(result, Vin, Vout, R, L, Vf, fs, eta, save_path):
    """画 Case C2b 的 Id(t) 波形"""
    Ts = 1.0 / fs
    D = result["D"]
    Dd = result["Dd"]
    IL_peak = result["IL_peak"]
    m = result["m"]
    Id2_at_t0 = result["Id2_at_t0"]
    t_d2_tail_end = result["t_d2_tail_end"]
    t_d1_start = result["t_d1_start"]
    t_d1_end = result["t_d1_end"]
    t_d2_main_start = result["t_d2_main_start"]
    t_d2_main_end = result["t_d2_main_end"]

    N = 2000
    t = np.linspace(0, Ts, N)
    Id1 = np.zeros(N)
    Id2 = np.zeros(N)

    for i in range(N):
        ti = t[i]
        # D2 尾部: [0, t_d2_tail_end]，从 Id2_at_t0 线性降到 0
        if 0 <= ti <= t_d2_tail_end and t_d2_tail_end > 0:
            Id2[i] = Id2_at_t0 * (1 - ti / t_d2_tail_end)
        # D2 主脉冲: [t_d2_main_start, t_d2_main_end]，从 IL_peak 降到 0
        if t_d2_main_start <= ti <= t_d2_main_end:
            Id2[i] = IL_peak - m * (ti - t_d2_main_start)
        # D1: [t_d1_start, t_d1_end]，从 IL_peak 降到 0
        if t_d1_start <= ti <= t_d1_end:
            Id1[i] = IL_peak - m * (ti - t_d1_start)

    Id = Id1 + Id2
    t_us = t * 1e6

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), facecolor='#1E1E1E')

    # 上图：分相
    ax1.set_facecolor('#1E1E1E')
    ax1.plot(t_us, Id2, color='#f97316', linewidth=2, label='$I_{d2}$ (Phase 2)')
    ax1.plot(t_us, Id1, color='#3b82f6', linewidth=2, label='$I_{d1}$ (Phase 1)')
    ax1.fill_between(t_us, Id2, alpha=0.2, color='#f97316')
    ax1.fill_between(t_us, Id1, alpha=0.2, color='#3b82f6')
    for tb in [t_d2_tail_end, t_d1_start, t_d1_end, t_d2_main_start]:
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

    params = (f'$V_{{in}}$={Vin}V  $V_{{out}}$={Vout}V  $R$={R}Ω  $L$={L*1e6}µH\n'
              f'$f_s$={fs/1e3}kHz  $\\eta$={eta}\n'
              f'$D$={D:.4f}  $D_d$={Dd:.4f}  $D+D_d$={D+Dd:.4f}')
    ax2.text(0.02, 0.98, params, transform=ax2.transAxes,
             fontsize=9, verticalalignment='top', fontfamily='monospace',
             color='#E0E0E0', bbox=dict(boxstyle='round', facecolor='#2E2E2E', alpha=0.8))

    # 区间标注
    regions = [
        ((0, t_d2_tail_end), 'D2\ntail', '#f97316'),
        ((t_d2_tail_end, t_d1_start), 'Dead', '#888888'),
        ((t_d1_start, t_d1_end), 'D1\nfalling', '#3b82f6'),
        ((t_d1_end, t_d2_main_start), 'Dead', '#888888'),
        ((t_d2_main_start, min(t_d2_main_end, Ts)), 'D2\nfalling', '#f97316'),
    ]
    for (ts, te), label, color in regions:
        mid = (ts + te) / 2 * 1e6
        width = (te - ts) * 1e6
        if width > 0.12:
            ax2.text(mid, IL_peak * 0.35, label, ha='center', va='center',
                     color=color, fontsize=8,
                     fontweight='bold' if color != '#888888' else 'normal')

    # 时间标记
    for tb, lbl in [(t_d2_tail_end, '$t_{D2,tail}$'), (t_d1_start, '$t_{D1,on}$'),
                    (t_d1_end, '$t_{D1,off}$'), (t_d2_main_start, '$t_{D2,on}$')]:
        ax2.axvline(tb * 1e6, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
        ax2.text(tb * 1e6, -0.02, f'{lbl}\n{tb*1e6:.3f}µs', color='#888888',
                 fontsize=7, ha='center')

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
    Vout = 30.0      # V
    R = 100.0        # Ω (总负载)
    L = 10e-6        # H (每相)
    Vf = 0.7         # V
    fs = 400e3       # Hz
    eta = 0.95       # 效率

    # === 求解 ===
    result = solve_case_c2b(Vin, Vout, R, L, Vf, fs, eta)

    # === 输出 ===
    print("=" * 50)
    print(f"Case {result['mode']} 理论计算结果")
    print("=" * 50)
    print(f"输入: Vin={Vin}V, Vout={Vout}V, R={R}Ω, L={L*1e6}µH, Vf={Vf}V, fs={fs/1e3}kHz, η={eta}")
    print(f"CRM 边界: R_crm = {result['R_crm']:.1f} Ω")
    print(f"D = {result['D']:.6f}")
    print(f"Dd = δ = {result['Dd']:.6f}")
    print(f"D + Dd = {result['D_plus_Dd']:.6f}")
    print(f"IL_peak = {result['IL_peak']:.4f} A")
    print(f"m = {result['m']:.2e} A/s")
    print(f"Id2(t=0) = {result['Id2_at_t0']:.4f} A (尾部起始)")
    print()
    print("C2b 时序 (D2 跨越周期边界):")
    print(f"  D2 尾部:  [0, {result['t_d2_tail_end']*1e6:.4f}] µs")
    print(f"  死区:     [{result['t_d2_tail_end']*1e6:.4f}, {result['t_d1_start']*1e6:.4f}] µs")
    print(f"  D1 下降:  [{result['t_d1_start']*1e6:.4f}, {result['t_d1_end']*1e6:.4f}] µs")
    print(f"  死区:     [{result['t_d1_end']*1e6:.4f}, {result['t_d2_main_start']*1e6:.4f}] µs")
    print(f"  D2 主脉冲:[{result['t_d2_main_start']*1e6:.4f}, {result['t_d2_main_end']*1e6:.4f}] µs (跨越Ts)")

    # === 验证 ===
    D = result['D']
    Dd = result['Dd']
    IL_peak = result['IL_peak']
    IL_avg = IL_peak * Dd / 2
    Iout = 2 * IL_avg * eta
    print()
    print("验证:")
    print(f"  IL_avg = IL_peak·δ/2 = {IL_avg:.4f} A")
    print(f"  Iout = 2·IL_avg·η = {Iout:.4f} A")
    print(f"  Vout = Iout·R = {Iout*R:.2f}V (目标 {Vout}V)")

    # === 画图 ===
    out_path = '/tmp/latex_boost/case_c2b_theoretical.png'
    plot_Id_waveform(result, Vin, Vout, R, L, Vf, fs, eta, out_path)
    print(f"\n波形图已保存: {out_path}")
