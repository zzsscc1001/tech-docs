"""
Case C1 理论计算：DCM + 二极管占空比 Dd < 0.5（即 D > 0.5）
双相交错 180° 非同步 Boost

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


def solve_case_c1(Vin, Vout, R, L, Vf, fs, eta):
    """
    Case C1 求解器：DCM + Dd < 0.5

    返回 dict:
        D: 占空比
        Dd: 二极管占空比 δ
        IL_peak: 二极管电流峰值 (A)
        m: TOFF 下降斜率 (A/s)
        t_boundaries: 五段时间边界 (s)
        mode: "C1" / "A" / "CRM"
    """
    Ts = 1.0 / fs

    # --- Step 1: CCM 占空比（用于 CRM 边界计算）---
    D_ccm = 1 - Vin / (Vout + Vf)

    # --- Step 2: 纹波电流 ---
    delta_IL = Vin * D_ccm * Ts / L

    # --- Step 3: CRM 边界 ---
    # IL_avg_crm = delta_IL / 2
    # Pin_crm = 2 * Vin * IL_avg_crm
    # Pout_crm = eta * Pin_crm
    IL_avg_crm = delta_IL / 2
    Pin_crm = 2 * Vin * IL_avg_crm
    Pout_crm = eta * Pin_crm
    R_crm = Vout**2 / Pout_crm

    # --- Step 4: 判断工作模式 ---
    if R <= R_crm:
        # 负载比 CRM 重 → CCM (Case A)
        return {"mode": "A", "R_crm": R_crm, "D": D_ccm, "Dd": 1 - D_ccm}

    # R > R_crm → 进入 DCM，用 DCM 能量平衡方程求解 D
    # DCM 模型：
    #   IL_peak = Vin*D*Ts/L
    #   delta = D*Vin/(Vout+Vf-Vin)
    #   Iout_sp = (1/2)*IL_peak*delta
    #   Vout = R * 2 * Iout_sp * eta
    #
    # 整理得：Vout² - (Vin-Vf)*Vout = R*eta*Vin²*D²*Ts/L
    # 解出：D² = [Vout² - (Vin-Vf)*Vout] / [R*eta*Vin²*Ts/L]

    lhs = Vout**2 - (Vin - Vf) * Vout
    rhs_coeff = R * eta * Vin**2 * Ts / L
    D_squared = lhs / rhs_coeff

    if D_squared < 0:
        raise ValueError("无解：参数组合不合法")

    D_dcm = math.sqrt(D_squared)

    if D_dcm > 1:
        raise ValueError(f"D={D_dcm:.4f}>1，DCM 无法维持 Vout={Vout}V")

    # --- Step 5: DCM 参数 ---
    delta = D_dcm * Vin / (Vout + Vf - Vin)  # = Dd
    IL_peak = Vin * D_dcm * Ts / L
    m = (Vout + Vf - Vin) / L

    D_plus_Dd = D_dcm + delta

    # 判断 Case C1 还是 C2
    if D_dcm <= 0.5:
        subcase = "C2"
    else:
        subcase = "C1"

    # Case C1 时间边界（同步关沿）
    t1 = (D_dcm - 0.5) * Ts   # 死区①结束，D2 开始
    t2 = t1 + delta * Ts       # D2 结束，死区②开始
    t3 = D_dcm * Ts            # 死区②结束，D1 开始
    t4 = t3 + delta * Ts       # D1 结束，死区③开始

    return {
        "mode": subcase,
        "R_crm": R_crm,
        "D": D_dcm,
        "Dd": delta,
        "D_plus_Dd": D_plus_Dd,
        "IL_peak": IL_peak,
        "m": m,
        "dead_time": (1 - D_plus_Dd) * Ts,
        "t_boundaries": [0, t1, t2, t3, t4, Ts],
        "D_ccm": D_ccm,
    }


def plot_Id_waveform(result, Vin, Vout, R, L, Vf, fs, eta, save_path):
    """画 Case C1 的 Id(t) 波形"""
    Ts = 1.0 / fs
    D = result["D"]
    delta = result["Dd"]
    IL_peak = result["IL_peak"]
    m = result["m"]
    t1, t2, t3, t4 = result["t_boundaries"][1:5]

    N = 1000
    t = np.linspace(0, Ts, N)
    Id1 = np.zeros(N)
    Id2 = np.zeros(N)

    for i in range(N):
        ti = t[i]
        # D2: 下降斜坡 [t1, t2]
        if t1 <= ti <= t2:
            Id2[i] = IL_peak - m * (ti - t1)
        # D1: 下降斜坡 [t3, t4]
        if t3 <= ti <= t4:
            Id1[i] = IL_peak - m * (ti - t3)

    Id = Id1 + Id2
    t_us = t * 1e6

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), facecolor='#1E1E1E')

    # 上图：分相电流
    ax1.set_facecolor('#1E1E1E')
    ax1.plot(t_us, Id1, color='#3b82f6', linewidth=2, label='$I_{d1}$')
    ax1.plot(t_us, Id2, color='#f97316', linewidth=2, label='$I_{d2}$')
    ax1.fill_between(t_us, Id1, alpha=0.2, color='#3b82f6')
    ax1.fill_between(t_us, Id2, alpha=0.2, color='#f97316')
    for tb in [t1, t2, t3, t4]:
        ax1.axvline(tb * 1e6, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    ax1.set_ylabel('Current (A)', color='#E0E0E0', fontsize=12)
    ax1.set_title(f'Phase Diode Currents — {result["mode"]}', color='#E0E0E0', fontsize=14)
    ax1.legend(loc='upper right', facecolor='#2E2E2E', edgecolor='gray', labelcolor='#E0E0E0')
    ax1.tick_params(colors='#E0E0E0')
    ax1.grid(True, alpha=0.2, color='gray')
    ax1.set_xlim(0, Ts * 1e6)
    ax1.set_ylim(-0.05, IL_peak * 1.3)

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

    # 区间标注
    regions = [
        ((0, t1), 'Dead', '#888888'),
        ((t1, t2), 'D2\nfalling', '#f97316'),
        ((t2, t3), 'Dead\nZone', '#888888'),
        ((t3, t4), 'D1\nfalling', '#3b82f6'),
        ((t4, Ts), 'Dead', '#888888'),
    ]
    for (t_start, t_end), label, color in regions:
        ax2.text((t_start + t_end) / 2 * 1e6, IL_peak * 0.4,
                 label, ha='center', va='center', color=color, fontsize=10,
                 fontweight='bold' if color != '#888888' else 'normal')

    # 时间标记
    for tb, lbl in [(t1, '$t_1$'), (t2, '$t_2$'), (t3, '$t_3$'), (t4, '$t_4$')]:
        ax2.axvline(tb * 1e6, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
        ax2.text(tb * 1e6, -0.03, f'{lbl}={tb*1e6:.3f}µs', color='#888888', fontsize=8, ha='center')

    ax2.annotate(f'Peak={IL_peak:.3f}A', xy=((t1 + t2) / 2 * 1e6, IL_peak),
                xytext=(1.2, IL_peak * 1.15),
                arrowprops=dict(arrowstyle='->', color='#E0E0E0'),
                color='#E0E0E0', fontsize=10)

    ax2.set_xlabel('Time (µs)', color='#E0E0E0', fontsize=12)
    ax2.set_ylabel('Current (A)', color='#E0E0E0', fontsize=12)
    ax2.set_title('Total Diode Current $I_d(t)$', color='#E0E0E0', fontsize=14)
    ax2.legend(loc='upper right', facecolor='#2E2E2E', edgecolor='gray', labelcolor='#E0E0E0')
    ax2.tick_params(colors='#E0E0E0')
    ax2.grid(True, alpha=0.2, color='gray')
    ax2.set_xlim(0, Ts * 1e6)
    ax2.set_ylim(-0.05, IL_peak * 1.3)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=200, bbox_inches='tight', facecolor='#1E1E1E')
    plt.close()
    return save_path


if __name__ == "__main__":
    # === 输入参数 ===
    Vin = 6.0       # V
    Vout = 30.0      # V
    R = 200.0        # Ω (总负载)
    L = 10e-6        # H (每相)
    Vf = 0.7         # V
    fs = 400e3       # Hz
    eta = 0.95       # 效率

    # === 求解 ===
    result = solve_case_c1(Vin, Vout, R, L, Vf, fs, eta)

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
    print(f"死区 = {result['dead_time']*1e6:.4f} µs")
    print(f"IL_peak = {result['IL_peak']:.4f} A")
    print(f"m = {result['m']:.2e} A/s")
    print()
    print("波形时间边界:")
    labels = ["死区①", "D2(下降)", "死区②", "D1(下降)", "死区③"]
    for i, (label, tb) in enumerate(zip(labels, result['t_boundaries'])):
        print(f"  {label}: t = {tb*1e6:.4f} µs")

    # === 画图 ===
    out_path = '/tmp/latex_boost/case_c1_theoretical.png'
    plot_Id_waveform(result, Vin, Vout, R, L, Vf, fs, eta, out_path)
    print(f"\n波形图已保存: {out_path}")
