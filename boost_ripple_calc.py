# ============================================================
# 两相交错非同步 Boost 输出纹波计算器
# 纯 Python + Matplotlib 实现，可在 Jupyter Notebook 中运行
# ============================================================

import numpy as np
import matplotlib.pyplot as plt

# ────────────────────────────────────────────────────────────
# 第一步：定义输入参数
# ────────────────────────────────────────────────────────────

# --- 基础参数 ---
Vin  = 12       # 输入电压 (V)
Vout = 24       # 输出电压 (V)
Iout = 3        # 输出电流 (A)，即负载电流
fsw  = 300e3    # 开关频率 (Hz)，300kHz
eta  = 0.92     # 效率，考虑实际损耗

# --- 硬件参数 ---
L    = 10e-6    # 每相电感值 (H)，10µH
Cout = 47e-6    # 输出电容 (F)，47µF
ESR  = 15e-3    # 输出电容等效串联电阻 (Ω)，15mΩ
Vd   = 0.5      # 整流二极管正向压降 (V)

# --- 交错参数 ---
alpha = 0.5     # 主相电流比例，0.5 = 两相均分

# ────────────────────────────────────────────────────────────
# 第二步：计算基本电气参数
# ────────────────────────────────────────────────────────────

# 开关周期 (s)
T = 1 / fsw
print(f"开关周期 T = {T*1e6:.3f} µs")

# 占空比 D
# 推导：伏秒平衡 → V_in×D = (V_out+V_d)×(1-D)
# 加入效率修正后：D = 1 - V_in×η / (V_out+V_d)
D = 1 - (Vin * eta) / (Vout + Vd)
print(f"占空比 D = {D:.4f} ({D*100:.2f}%)")

# 总输入电流
# 功率守恒：V_out × I_out = V_in × I_in × η
Iin_total = (Vout * Iout) / (Vin * eta)
print(f"总输入电流 I_in = {Iin_total:.3f} A")

# 每相平均电流（按 alpha 分配）
IL1_avg = Iin_total * alpha        # 主相
IL2_avg = Iin_total * (1 - alpha)  # 辅相
print(f"主相电流 I_L1 = {IL1_avg:.3f} A, 辅相电流 I_L2 = {IL2_avg:.3f} A")

# 电感纹波电流（峰峰值）
# 推导：导通期间 di/dt = V_in/L，持续时间 = D×T
dIL = (Vin * D * T) / L
print(f"电感纹波电流 ΔI_L = {dIL:.3f} A ({dIL*1000:.1f} mA)")

# ────────────────────────────────────────────────────────────
# 第三步：仿真单相二极管电流波形
# ────────────────────────────────────────────────────────────

# 时间分辨率：一个开关周期内取 2000 个点
N = 2000
dt = T / N                          # 每个采样点的时间间隔 (s)
t_arr = np.linspace(0, T, N, endpoint=False)  # 时间轴数组

def calc_phase(Iavg, dI):
    """
    计算单相的二极管电流波形
    
    参数:
        Iavg: 该相的平均电感电流 (A)
        dI:   电感纹波电流峰峰值 (A)
    
    返回:
        Id:   二极管电流数组 (A)，长度 N
        mode: 'CCM' 或 'DCM'
        Ipeak, Ivalley, Ton, Toff2: 关键时间点参数
    """
    # ── CCM/DCM 判定 ──
    # 如果平均电流 > 纹波的一半，电流不会降到零 → CCM
    isCCM = Iavg > dI / 2
    
    if isCCM:
        # ── CCM 模式 ──
        mode = 'CCM'
        
        # 电感电流的峰值和谷值
        # 平均值叠加纹波的一半
        Ipeak  = Iavg + dI / 2
        Ivalley = Iavg - dI / 2
        
        # 导通时间和关断时间
        Ton   = D * T          # MOSFET 导通时间
        Toff2 = (1 - D) * T    # 二极管导通时间
        
        # 生成二极管电流波形
        Id = np.zeros(N)
        for i in range(N):
            t = t_arr[i]
            if t < Ton:
                # MOSFET 导通期间：二极管截止
                Id[i] = 0
            else:
                # 二极管导通期间：电流从 Ipeak 线性降到 Ivalley
                frac = (t - Ton) / (T - Ton)  # 归一化进度 [0, 1]
                Id[i] = Ipeak - frac * (Ipeak - Ivalley)
    else:
        # ── DCM 模式 ──
        mode = 'DCM'
        
        # DCM 下的峰值电流推导
        # 能量守恒：I_avg = 0.5 × I_peak × (T_on + T_off2) / T
        # 导通：I_peak = V_in × T_on / L  →  T_on = I_peak × L / V_in
        # 关断到零：I_peak = (V_out+V_d-V_in) × T_off2 / L
        # 联立求解：
        k = L * (1/Vin + 1/(Vout + Vd - Vin)) / T
        Ipeak = np.sqrt(2 * Iavg / k)
        
        # 由 Ipeak 反推各段时间
        Ton   = Ipeak * L / Vin                     # 导通时间
        Toff2 = Ipeak * L / (Vout + Vd - Vin)       # 二极管导通时间
        Ivalley = 0                                  # DCM 下电流降到零
        
        # 生成波形
        Id = np.zeros(N)
        for i in range(N):
            t = t_arr[i]
            if t < Ton:
                Id[i] = 0                            # MOSFET 导通
            elif t < Ton + Toff2:
                frac = (t - Ton) / Toff2
                Id[i] = Ipeak * (1 - frac)           # 二极管导通，线性下降
            else:
                Id[i] = 0                            # 死区时间
    
    return Id, mode, Ipeak, Ivalley, Ton, Toff2

# 计算两相的电流波形
ph1_Id, ph1_mode, ph1_Ipeak, ph1_Ivalley, ph1_Ton, ph1_Toff2 = calc_phase(IL1_avg, dIL)
ph2_Id, ph2_mode, ph2_Ipeak, ph2_Ivalley, ph2_Ton, ph2_Toff2 = calc_phase(IL2_avg, dIL)

print(f"\n--- Phase 1 ({ph1_mode}, α={alpha*100:.0f}%) ---")
print(f"  I_peak = {ph1_Ipeak:.3f} A, I_valley = {ph1_Ivalley:.3f} A")
print(f"  T_on = {ph1_Ton*1e6:.3f} µs, T_off2 = {ph1_Toff2*1e6:.3f} µs")

print(f"\n--- Phase 2 ({ph2_mode}, α={(1-alpha)*100:.0f}%) ---")
print(f"  I_peak = {ph2_Ipeak:.3f} A, I_valley = {ph2_Ivalley:.3f} A")
print(f"  T_on = {ph2_Ton*1e6:.3f} µs, T_off2 = {ph2_Toff2*1e6:.3f} µs")

# ────────────────────────────────────────────────────────────
# 第四步：180° 交错移相
# ────────────────────────────────────────────────────────────

# 交错 180° = 移动半个周期 = 移动 N/2 个采样点
shift = N // 2

# np.roll 将 Phase2 的波形向右移动 shift 个位置
# 这样 Phase2 的导通起点就比 Phase1 晚了 T/2
Id1 = ph1_Id
Id2 = np.roll(ph2_Id, shift)

print(f"交错移相：Phase2 延迟 {shift} 个采样点 = {shift*dt*1e6:.3f} µs (= T/2)")

# ────────────────────────────────────────────────────────────
# 第五步：叠加两相电流，计算电容电流
# ────────────────────────────────────────────────────────────

# 总二极管电流 = 两相之和
Id_total = Id1 + Id2

# 电容电流 = 总二极管电流 - 负载电流
# 基尔霍夫电流定律：电容吸收多余/补足不足
Ic = Id_total - Iout

print(f"\n总二极管电流范围：{Id_total.min():.3f} ~ {Id_total.max():.3f} A")
print(f"电容电流范围：{Ic.min():.3f} ~ {Ic.max():.3f} A")

# ────────────────────────────────────────────────────────────
# 第六步：计算电压纹波
# ────────────────────────────────────────────────────────────

# ① 电容电压纹波 V_C(t) = (1/C) × ∫ Ic dt
# 用累加代替积分（矩形法）
Vc = np.cumsum(Ic) * dt / Cout

# 减去均值，消除直流偏移（只关心交流纹波）
Vc -= Vc.mean()

# ② ESR 电压纹波 V_ESR(t) = Ic × ESR
Vesr = Ic * ESR

# ③ 总输出纹波 = 电容纹波 + ESR 纹波
Vripple = Vc + Vesr

# 计算峰峰值
Vc_pp     = Vc.max() - Vc.min()
Vesr_pp   = Vesr.max() - Vesr.min()
Vripple_pp = Vripple.max() - Vripple.min()

print(f"\n=== 纹波结果 ===")
print(f"电容纹波 V_C(p-p)    = {Vc_pp*1e3:.2f} mV")
print(f"ESR 纹波 V_ESR(p-p)  = {Vesr_pp*1e3:.2f} mV")
print(f"总输出纹波 V(p-p)    = {Vripple_pp*1e3:.2f} mV")

# ────────────────────────────────────────────────────────────
# 第七步：绘图 — 展示 5 个开关周期
# ────────────────────────────────────────────────────────────

# 将单周期波形重复 5 次，展示稳态行为
NCYCLES = 5

# 时间轴（单位 µs）
t_plot = np.tile(t_arr, NCYCLES) * 1e6  # 拼接 5 个周期，转 µs

# 拼接各波形
Id1_plot    = np.tile(Id1, NCYCLES)
Id2_plot    = np.tile(Id2, NCYCLES)
Idtot_plot  = np.tile(Id_total, NCYCLES)
Vc_plot     = np.tile(Vc, NCYCLES) * 1e3      # 转 mV
Vesr_plot   = np.tile(Vesr, NCYCLES) * 1e3    # 转 mV
Vrip_plot   = np.tile(Vripple, NCYCLES) * 1e3 # 转 mV

# 设置绘图风格
plt.rcParams.update({
    'font.size': 10,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'figure.facecolor': 'white',
})

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
fig.suptitle('两相交错非同步 Boost 输出纹波', fontsize=14, fontweight='bold')

# ── 图1：电流波形 ──
ax1 = axes[0]
ax1.plot(t_plot, Id1_plot,   label='I_d1 (主相)',   color='#0070f3', linewidth=1.2)
ax1.plot(t_plot, Id2_plot,   label='I_d2 (辅相)',   color='#de1d8d', linewidth=1.2)
ax1.plot(t_plot, Idtot_plot, label='I_d (总)',      color='#171717', linewidth=1.5)
ax1.axhline(y=Iout, color='gray', linestyle='--', linewidth=0.8, label=f'I_out = {Iout}A')
ax1.set_ylabel('电流 (A)')
ax1.legend(loc='upper right', fontsize=9)
ax1.set_title('① 电流时域交错波形')

# ── 图2：电压纹波分量 ──
ax2 = axes[1]
ax2.plot(t_plot, Vc_plot,   label='V_C (电容纹波)',   color='#0070f3', linewidth=1.2)
ax2.plot(t_plot, Vesr_plot, label='V_ESR (ESR纹波)',  color='#de1d8d', linewidth=1.2)
ax2.set_ylabel('电压纹波 (mV)')
ax2.legend(loc='upper right', fontsize=9)
ax2.set_title('② 电压纹波分量拆解')

# ── 图3：总输出纹波 ──
ax3 = axes[2]
ax3.plot(t_plot, Vrip_plot, label='V_ripple (总)', color='#171717', linewidth=1.5)
ax3.fill_between(t_plot, Vrip_plot, 0, alpha=0.08, color='#0070f3')
ax3.axhline(y=0, color='gray', linewidth=0.5)
ax3.set_xlabel('时间 (µs)')
ax3.set_ylabel('总纹波 (mV)')
ax3.legend(loc='upper right', fontsize=9)
ax3.set_title('③ 总输出电压纹波 V_ripple(t)')

plt.tight_layout()
plt.savefig('boost_ripple.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\n图片已保存为 boost_ripple.png")
