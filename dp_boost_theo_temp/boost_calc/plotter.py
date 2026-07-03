"""
plotter.py — 波形绘图模块

接收 WaveformData，绘制：
  - 上图：D1 和 D2 分相电流
  - 下图：总二极管电流 Id = Id1 + Id2，含区间标注和参数框

公开接口：
  plot_waveform(wd, params, save_path, N=2000) -> str
    wd        : WaveformData（来自 solvers.py）
    params    : dict，包含 Vin/Vout/R/L/Vf/fs/eta（用于标注）
    save_path : 输出图片路径（自动创建目录）
    N         : 时间采样点数
    返回实际保存路径
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import AutoMinorLocator

from .solvers import WaveformData, Segment

# ─────────────────────────────────────────────
# 配色方案
# ─────────────────────────────────────────────
THEME = {
    "bg":       "#1E1E1E",
    "panel":    "#2A2A2A",
    "text":     "#E0E0E0",
    "subtext":  "#888888",
    "grid":     "#3A3A3A",
    "d1":       "#3b82f6",   # 蓝
    "d2":       "#f97316",   # 橙
    "total":    "#22c55e",   # 绿
    "dead":     "#555555",
    "vline":    "#606060",
}

PHASE_COLOR = {1: THEME["d1"], 2: THEME["d2"], 0: THEME["dead"]}
PHASE_LABEL = {1: "$I_{d1}$", 2: "$I_{d2}$"}


# ─────────────────────────────────────────────
# 波形采样
# ─────────────────────────────────────────────

def _sample_segments(segments: list[Segment], Ts: float, N: int) -> np.ndarray:
    """将 Segment 列表采样为 N 点电流数组。"""
    t = np.linspace(0, Ts, N)
    I = np.zeros(N)
    for seg in segments:
        if seg.phase == 0 or seg.duration <= 0:
            continue
        mask = (t >= seg.t_start) & (t <= seg.t_end)
        I[mask] = seg.I_start + (seg.I_end - seg.I_start) * (
            (t[mask] - seg.t_start) / seg.duration
        )
    return I


# ─────────────────────────────────────────────
# 辅助绘图函数
# ─────────────────────────────────────────────

def _apply_dark_style(ax):
    ax.set_facecolor(THEME["bg"])
    ax.tick_params(colors=THEME["text"], which="both")
    ax.yaxis.label.set_color(THEME["text"])
    ax.xaxis.label.set_color(THEME["text"])
    ax.title.set_color(THEME["text"])
    for spine in ax.spines.values():
        spine.set_edgecolor(THEME["grid"])
    ax.grid(True, color=THEME["grid"], linewidth=0.6, alpha=0.8)
    ax.grid(True, which="minor", color=THEME["grid"], linewidth=0.3, alpha=0.4)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())


def _draw_vlines(ax, times_s: list[float], Ts: float):
    """在关键时间点画竖虚线。"""
    for t in times_s:
        ax.axvline(t * 1e6, color=THEME["vline"], linestyle="--",
                   linewidth=0.8, alpha=0.7)


def _annotate_regions(ax, wd: WaveformData, y_pos: float):
    """在下图标注各区间名称。"""
    for seg in wd.all_segments:
        if seg.duration < wd.Ts * 0.02:   # 太窄不标注
            continue
        mid_us = (seg.t_start + seg.t_end) / 2 * 1e6
        color = PHASE_COLOR.get(seg.phase, THEME["dead"])
        ax.text(mid_us, y_pos, seg.label,
                ha="center", va="center",
                color=color, fontsize=8,
                fontweight="bold" if seg.phase > 0 else "normal",
                alpha=0.9)


def _annotate_times(ax, wd: WaveformData, y_bottom: float):
    """在 x 轴下方标注关键时间点。"""
    seen = set()
    for seg in wd.all_segments:
        for t in (seg.t_start, seg.t_end):
            if t in seen or t <= 0 or t >= wd.Ts:
                continue
            seen.add(t)
            ax.axvline(t * 1e6, color=THEME["vline"], linestyle="--",
                       linewidth=0.8, alpha=0.6)
            ax.text(t * 1e6, y_bottom, f"{t*1e6:.3f}µs",
                    color=THEME["subtext"], fontsize=7,
                    ha="center", va="top", rotation=45)


def _params_box(ax, params: dict, wd: WaveformData):
    """在右上角绘制参数标注框（四行，避免与箭头重叠）。"""
    Vin  = params.get("Vin", "?")
    Vout = params.get("Vout", "?")
    R    = params.get("R", "?")
    L_uH = params.get("L", 0) * 1e6
    Vf   = params.get("Vf", "?")
    fs_k = params.get("fs", 0) / 1e3
    eta  = params.get("eta", "?")

    text = (
        f"$V_{{in}}$={Vin}V   $V_{{out}}$={Vout}V   "
        f"$R$={R}Ω   $L$={L_uH:.1f}µH\n"
        f"$f_s$={fs_k:.0f}kHz   $V_f$={Vf}V   $\\eta$={eta}\n"
        f"$D$={wd.D:.4f}   $D_d$={wd.Dd:.4f}\n"
        f"$D+D_d$={wd.D_plus_Dd:.4f}   "
        f"$I_{{L,peak}}$={wd.IL_peak:.4f} A"
    )
    ax.text(0.98, 0.97, text,
            transform=ax.transAxes,
            fontsize=9, verticalalignment="top", horizontalalignment="right",
            fontfamily="monospace", color=THEME["text"],
            bbox=dict(boxstyle="round,pad=0.4",
                      facecolor=THEME["panel"], alpha=0.85,
                      edgecolor=THEME["grid"]))


# ─────────────────────────────────────────────
# 主绘图函数
# ─────────────────────────────────────────────

def plot_waveform(
    wd: WaveformData,
    params: dict,
    save_path: str,
    N: int = 2000,
) -> str:
    """
    绘制双相交错 Boost 的二极管电流波形图。

    参数
    ----
    wd        : WaveformData（来自 solvers.solve()）
    params    : 电路参数字典，键：Vin / Vout / R / L / Vf / fs / eta
    save_path : 图片保存路径（.png）
    N         : 时间采样点数（默认 2000）

    返回
    ----
    实际保存路径字符串
    """
    Ts = wd.Ts
    t_us = np.linspace(0, Ts, N) * 1e6

    # 采样各相电流
    Id1 = _sample_segments(wd.segments_d1, Ts, N)
    Id2 = _sample_segments(wd.segments_d2, Ts, N)
    Id  = Id1 + Id2

    IL_peak = wd.IL_peak
    y_max = IL_peak * 1.45
    y_min = -IL_peak * 0.08

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 9),
        facecolor=THEME["bg"],
        gridspec_kw={"hspace": 0.38},
    )

    # ── 上图：分相电流 ──────────────────────────
    _apply_dark_style(ax1)

    ax1.plot(t_us, Id1, color=THEME["d1"], linewidth=2.0,
             label="$I_{d1}$ (Phase 1)")
    ax1.plot(t_us, Id2, color=THEME["d2"], linewidth=2.0,
             label="$I_{d2}$ (Phase 2)")
    ax1.fill_between(t_us, Id1, alpha=0.18, color=THEME["d1"])
    ax1.fill_between(t_us, Id2, alpha=0.18, color=THEME["d2"])

    # 关键时间竖线
    key_times = sorted({seg.t_start for seg in wd.all_segments}
                       | {seg.t_end for seg in wd.all_segments}
                       - {0.0, Ts})
    _draw_vlines(ax1, key_times, Ts)

    ax1.set_xlim(0, Ts * 1e6)
    ax1.set_ylim(y_min, y_max)
    ax1.set_ylabel("Current (A)", fontsize=12)
    ax1.set_title(
        f"Phase Diode Currents — Case {wd.case}",
        fontsize=14, pad=8,
    )
    ax1.legend(
        loc="upper right",
        facecolor=THEME["panel"], edgecolor=THEME["grid"],
        labelcolor=THEME["text"], fontsize=11,
    )

    # ── 下图：总电流 ────────────────────────────
    _apply_dark_style(ax2)

    ax2.plot(t_us, Id, color=THEME["total"], linewidth=2.5,
             label="$I_d = I_{d1}+I_{d2}$")
    ax2.fill_between(t_us, Id, alpha=0.15, color=THEME["total"])

    _draw_vlines(ax2, key_times, Ts)
    _annotate_regions(ax2, wd, IL_peak * 0.38)
    _annotate_times(ax2, wd, y_min * 0.6)
    _params_box(ax2, params, wd)

    # IL_peak 标注箭头
    # 找第一个非死区区间的起始时间
    first_active = next(
        (seg for seg in wd.all_segments if seg.phase > 0), None
    )
    if first_active:
        arrow_x = first_active.t_start * 1e6
        ax2.annotate(
            f"$I_{{L,peak}}$ = {IL_peak:.3f} A",
            xy=(arrow_x, IL_peak),
            xytext=(arrow_x + Ts * 1e6 * 0.08, IL_peak * 1.18),
            arrowprops=dict(arrowstyle="->", color=THEME["text"], lw=1.2),
            color=THEME["text"], fontsize=10,
        )

    ax2.set_xlim(0, Ts * 1e6)
    ax2.set_ylim(y_min, y_max)
    ax2.set_xlabel("Time (µs)", fontsize=12)
    ax2.set_ylabel("Current (A)", fontsize=12)
    ax2.set_title("Total Diode Current $I_d(t)$", fontsize=14, pad=8)
    ax2.legend(
        loc="upper right",
        facecolor=THEME["panel"], edgecolor=THEME["grid"],
        labelcolor=THEME["text"], fontsize=11,
    )

    # 保存
    os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
    plt.savefig(save_path, dpi=200, bbox_inches="tight",
                facecolor=THEME["bg"])
    plt.close(fig)
    return save_path
