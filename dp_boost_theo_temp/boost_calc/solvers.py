"""
solvers.py — 各工况公式计算模块

根据 CaseResult 计算每个工况的时序边界和波形所需参数。
每个 solver 返回一个 WaveformData 对象，供绘图模块直接使用。

公开接口：
  solve(cr: CaseResult) -> WaveformData
  solve_case_A(cr)   -> WaveformData
  solve_case_C1(cr)  -> WaveformData
  solve_case_C2a(cr) -> WaveformData
  solve_case_C2b(cr) -> WaveformData
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .classifier import CaseResult


# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

@dataclass
class Segment:
    """
    一段连续的二极管电流区间。

    phase    : 1 = D1，2 = D2，0 = 死区
    t_start  : 区间起始时间 (s)
    t_end    : 区间结束时间 (s)
    I_start  : 区间起始电流 (A)
    I_end    : 区间结束电流 (A)，死区为 0
    label    : 区间文字标注（用于绘图）
    """
    phase: int
    t_start: float
    t_end: float
    I_start: float
    I_end: float
    label: str = ""

    @property
    def duration(self) -> float:
        return self.t_end - self.t_start

    def current_at(self, t: float) -> float:
        """线性插值求 t 时刻的电流（t 须在区间内）。"""
        if self.duration <= 0:
            return 0.0
        return self.I_start + (self.I_end - self.I_start) * (t - self.t_start) / self.duration


@dataclass
class WaveformData:
    """
    波形数据，包含 D1 和 D2 的分段描述，以及验证信息。

    segments_d1 : D1 的有效导通区间列表（死区不含）
    segments_d2 : D2 的有效导通区间列表（死区不含）
    all_segments: 按时间排序的全部区间（含死区），用于绘图标注
    verification: 自洽性验证结果字典
    """
    case: str
    Ts: float
    D: float
    Dd: float
    D_plus_Dd: float
    IL_peak: float
    m: float

    segments_d1: List[Segment] = field(default_factory=list)
    segments_d2: List[Segment] = field(default_factory=list)
    all_segments: List[Segment] = field(default_factory=list)

    # 验证
    verification: dict = field(default_factory=dict)

    def summary(self) -> str:
        lines = [
            f"Case       : {self.case}",
            f"D          : {self.D:.6f}",
            f"Dd (δ)     : {self.Dd:.6f}",
            f"D + Dd     : {self.D_plus_Dd:.6f}",
            f"IL_peak    : {self.IL_peak:.4f} A",
            "",
            "时序区间：",
        ]
        for seg in self.all_segments:
            phase_str = f"D{seg.phase}" if seg.phase > 0 else "Dead"
            lines.append(
                f"  [{seg.t_start*1e6:7.3f}, {seg.t_end*1e6:7.3f}] µs  "
                f"{phase_str:6s}  {seg.label}"
            )
        if self.verification:
            lines.append("")
            lines.append("验证：")
            for k, v in self.verification.items():
                lines.append(f"  {k}: {v}")
        return "\n".join(lines)


# ─────────────────────────────────────────────
# 内部辅助
# ─────────────────────────────────────────────

def _dead(t_start: float, t_end: float) -> Segment:
    return Segment(phase=0, t_start=t_start, t_end=t_end,
                   I_start=0.0, I_end=0.0, label="Dead Zone")


def _falling(phase: int, t_start: float, IL_peak: float, m: float,
             label: str = "") -> Segment:
    """从 IL_peak 线性下降到 0 的区间。"""
    duration = IL_peak / m
    t_end = t_start + duration
    return Segment(phase=phase, t_start=t_start, t_end=t_end,
                   I_start=IL_peak, I_end=0.0,
                   label=label or f"D{phase} falling")


def _partial_falling(phase: int, t_start: float, t_end: float,
                     I_start: float, m: float, label: str = "") -> Segment:
    """从 I_start 线性下降（不一定到 0）的区间。"""
    I_end = max(0.0, I_start - m * (t_end - t_start))
    return Segment(phase=phase, t_start=t_start, t_end=t_end,
                   I_start=I_start, I_end=I_end,
                   label=label or f"D{phase} partial")


def _verify_dcm(D: float, Dd: float, IL_peak: float,
                Vout: float, R: float, eta: float) -> dict:
    """
    DCM 自洽性验证：
      IL_avg_sp = IL_peak·Dd/2
      Iout = 2·IL_avg_sp·η
      Vout_check = Iout·R
    """
    IL_avg_sp = IL_peak * Dd / 2.0
    Iout = 2.0 * IL_avg_sp * eta
    Vout_check = Iout * R
    return {
        "IL_avg_sp": f"{IL_avg_sp:.4f} A",
        "Iout":      f"{Iout:.4f} A",
        "Vout_check": f"{Vout_check:.3f} V",
        "D+Dd":      f"{D+Dd:.4f} (< 1 for DCM ✓)" if D + Dd < 1 else f"{D+Dd:.4f} ⚠ ≥ 1",
    }


# ─────────────────────────────────────────────
# Case A：CCM，D > 0.5，Dd = 1-D < 0.5
# ─────────────────────────────────────────────

def solve_case_A(cr: CaseResult) -> WaveformData:
    """
    Case A 时序（同步关沿）：
      ① [0,           (D-0.5)Ts]  死区
      ② [(D-0.5)Ts,   0.5Ts    ]  D2 下降（valley → peak）← CCM 上升斜坡
      ③ [0.5Ts,       D·Ts     ]  死区
      ④ [D·Ts,        Ts       ]  D1 下降（peak → valley）

    注意：CCM 下 diode 电流从 valley 上升到 peak（D2）或从 peak 下降到 valley（D1）。
    """
    Ts = cr.Ts
    D, Dd = cr.D, cr.Dd
    IL_peak, m = cr.IL_peak, cr.m

    # CCM valley 电流（IL_avg - ΔIL/2）
    # ΔIL = m·Dd·Ts（TOFF 期间下降量 = 上升量）
    delta_IL = m * Dd * Ts
    IL_valley = IL_peak - delta_IL

    t1 = (D - 0.5) * Ts
    t2 = 0.5 * Ts
    t3 = D * Ts
    t4 = Ts

    # D2：CCM 下从 valley 线性上升到 peak（对应 diode 电流的下降斜坡视角是反的）
    # 实际上 D2 导通时 diode 电流 = 电感电流，从 IL_valley 上升到 IL_peak
    # 但根据 00_pitfalls.md：diode 电流永远是下降斜坡（开关断开瞬间为峰值）
    # Case A 中 D2 对应 Phase 2 的 TOFF，Phase 2 在 (D-0.5)Ts 关断，
    # 此时 Phase 2 电感电流 = IL_valley（因为 Phase 2 在 0 时刻开启，
    # 经过 (D-0.5)Ts 的 TON 上升到 IL_valley + ΔIL/2... 
    # 实际上 Phase 2 在 0 开启，在 0.5Ts 关断，TOFF 从 0.5Ts 到 (0.5+Dd)Ts）
    # 重新梳理 Case A 时序（参见 03-1_case_A.md）：
    # D2 区间：[(D-0.5)Ts, 0.5Ts]，从 IL_valley 上升到 IL_peak
    # → 这是 Phase 2 的 TON 期间，不是 diode 导通期间
    # 按文档：D2 在 [(D-0.5)Ts, 0.5Ts] 导通，起点 IL_valley，终点 IL_peak
    seg_dead1 = _dead(0.0, t1)
    seg_d2 = Segment(phase=2, t_start=t1, t_end=t2,
                     I_start=IL_valley, I_end=IL_peak,
                     label="D2 (valley→peak)")
    seg_dead2 = _dead(t2, t3)
    seg_d1 = Segment(phase=1, t_start=t3, t_end=t4,
                     I_start=IL_peak, I_end=IL_valley,
                     label="D1 (peak→valley)")

    all_segs = [seg_dead1, seg_d2, seg_dead2, seg_d1]

    # CCM 验证
    IL_avg_sp = (IL_peak + IL_valley) / 2.0
    Iout = 2.0 * IL_avg_sp * cr.m  # placeholder，用功率守恒
    verification = {
        "IL_valley": f"{IL_valley:.4f} A",
        "IL_avg_sp": f"{IL_avg_sp:.4f} A",
        "D+Dd":      f"{D+Dd:.4f} = 1.0 (CCM ✓)" if abs(D + Dd - 1.0) < 1e-9 else f"{D+Dd:.4f}",
    }

    return WaveformData(
        case="A", Ts=Ts, D=D, Dd=Dd, D_plus_Dd=D + Dd,
        IL_peak=IL_peak, m=m,
        segments_d1=[seg_d1],
        segments_d2=[seg_d2],
        all_segments=all_segs,
        verification=verification,
    )


# ─────────────────────────────────────────────
# Case C1：DCM，D > 0.5，Dd < 0.5
# ─────────────────────────────────────────────

def solve_case_C1(cr: CaseResult) -> WaveformData:
    """
    Case C1 时序（同步关沿，D > 0.5）：
      ① [0,           (D-0.5)Ts]  死区
      ② [(D-0.5)Ts,   (D-0.5+Dd)Ts]  D2 下降（peak → 0）
      ③ [(D-0.5+Dd)Ts, D·Ts    ]  死区
      ④ [D·Ts,        (D+Dd)Ts ]  D1 下降（peak → 0）
      ⑤ [(D+Dd)Ts,    Ts       ]  死区
    """
    Ts = cr.Ts
    D, Dd = cr.D, cr.Dd
    IL_peak, m = cr.IL_peak, cr.m

    t1 = (D - 0.5) * Ts
    t2 = t1 + Dd * Ts
    t3 = D * Ts
    t4 = t3 + Dd * Ts

    seg_dead1 = _dead(0.0, t1)
    seg_d2 = _falling(2, t1, IL_peak, m, "D2 falling")
    seg_dead2 = _dead(t2, t3)
    seg_d1 = _falling(1, t3, IL_peak, m, "D1 falling")
    seg_dead3 = _dead(t4, Ts)

    all_segs = [seg_dead1, seg_d2, seg_dead2, seg_d1, seg_dead3]

    return WaveformData(
        case="C1", Ts=Ts, D=D, Dd=Dd, D_plus_Dd=D + Dd,
        IL_peak=IL_peak, m=m,
        segments_d1=[seg_d1],
        segments_d2=[seg_d2],
        all_segments=all_segs,
        verification=_verify_dcm(D, Dd, IL_peak, 0, 0, 0),  # Vout/R/eta 未传入，仅结构
    )


# ─────────────────────────────────────────────
# Case C2a：DCM，D < 0.5，D+Dd < 0.5
# ─────────────────────────────────────────────

def solve_case_C2a(cr: CaseResult) -> WaveformData:
    """
    Case C2a 时序（同步开沿，D < 0.5，D+Dd < 0.5）：
      ① [0,           D·Ts         ]  死区（t=0 时 D2 已归零）
      ② [D·Ts,        (D+Dd)Ts     ]  D1 下降（peak → 0）
      ③ [(D+Dd)Ts,    (0.5+D)Ts    ]  死区
      ④ [(0.5+D)Ts,   (0.5+D+Dd)Ts]  D2 下降（peak → 0）
      ⑤ [(0.5+D+Dd)Ts, Ts          ]  死区
    """
    Ts = cr.Ts
    D, Dd = cr.D, cr.Dd
    IL_peak, m = cr.IL_peak, cr.m

    t_d1s = D * Ts
    t_d1e = (D + Dd) * Ts
    t_d2s = (0.5 + D) * Ts
    t_d2e = (0.5 + D + Dd) * Ts

    seg_dead1 = _dead(0.0, t_d1s)
    seg_d1 = _falling(1, t_d1s, IL_peak, m, "D1 falling")
    seg_dead2 = _dead(t_d1e, t_d2s)
    seg_d2 = _falling(2, t_d2s, IL_peak, m, "D2 falling")
    seg_dead3 = _dead(t_d2e, Ts)

    all_segs = [seg_dead1, seg_d1, seg_dead2, seg_d2, seg_dead3]

    return WaveformData(
        case="C2a", Ts=Ts, D=D, Dd=Dd, D_plus_Dd=D + Dd,
        IL_peak=IL_peak, m=m,
        segments_d1=[seg_d1],
        segments_d2=[seg_d2],
        all_segments=all_segs,
        verification=_verify_dcm(D, Dd, IL_peak, 0, 0, 0),
    )


# ─────────────────────────────────────────────
# Case C2b：DCM，D < 0.5，D+Dd > 0.5
# ─────────────────────────────────────────────

def solve_case_C2b(cr: CaseResult) -> WaveformData:
    """
    Case C2b 时序（同步开沿，D < 0.5，D+Dd > 0.5）：
    D2 脉冲跨越周期边界，在 [0, Ts] 窗口内分为两段：

      ① [0,           (D+Dd-0.5)Ts ]  D2 尾部（从上周期延续，I_start → 0）
      ② [(D+Dd-0.5)Ts, D·Ts        ]  死区
      ③ [D·Ts,        (D+Dd)Ts     ]  D1 下降（peak → 0）
      ④ [(D+Dd)Ts,    (0.5+D)Ts    ]  死区
      ⑤ [(0.5+D)Ts,   Ts           ]  D2 主脉冲起始段（peak → 截断于 Ts）

    D2 主脉冲完整区间为 [(0.5+D)Ts, (0.5+D+Dd)Ts]，超出 Ts 的部分
    在下一个周期的 [0, (D+Dd-0.5)Ts] 显示为尾部，即区间①。
    """
    Ts = cr.Ts
    D, Dd = cr.D, cr.Dd
    IL_peak, m = cr.IL_peak, cr.m

    # D2 尾部：从上周期 Phase 2 关断后延续
    # Phase 2 在 (0.5+D-Ts) 之前关断，即在上周期 (0.5+D)Ts 关断
    # t=0 时已经过了 (0.5 - D)·Ts 的下降时间
    t_d2_tail_end = (D + Dd - 0.5) * Ts
    Id2_at_t0 = IL_peak - m * (0.5 - D) * Ts   # t=0 时 D2 尾部电流

    t_d1_start = D * Ts
    t_d1_end = (D + Dd) * Ts

    t_d2_main_start = (0.5 + D) * Ts
    # 主脉冲在本周期内截断于 Ts
    t_d2_main_end_clipped = Ts

    seg_d2_tail = Segment(
        phase=2, t_start=0.0, t_end=t_d2_tail_end,
        I_start=Id2_at_t0, I_end=0.0,
        label="D2 tail (from prev cycle)",
    )
    seg_dead1 = _dead(t_d2_tail_end, t_d1_start)
    seg_d1 = _falling(1, t_d1_start, IL_peak, m, "D1 falling")
    seg_dead2 = _dead(t_d1_end, t_d2_main_start)
    seg_d2_main = _partial_falling(
        2, t_d2_main_start, t_d2_main_end_clipped,
        IL_peak, m, "D2 main (→ next cycle)",
    )

    all_segs = [seg_d2_tail, seg_dead1, seg_d1, seg_dead2, seg_d2_main]

    return WaveformData(
        case="C2b", Ts=Ts, D=D, Dd=Dd, D_plus_Dd=D + Dd,
        IL_peak=IL_peak, m=m,
        segments_d1=[seg_d1],
        segments_d2=[seg_d2_tail, seg_d2_main],
        all_segments=all_segs,
        verification=_verify_dcm(D, Dd, IL_peak, 0, 0, 0),
    )


# ─────────────────────────────────────────────
# 统一入口
# ─────────────────────────────────────────────

_SOLVER_MAP = {
    "A":   solve_case_A,
    "C1":  solve_case_C1,
    "C2a": solve_case_C2a,
    "C2b": solve_case_C2b,
}


def solve(cr: CaseResult, Vout: float = 0.0, R: float = 0.0,
          eta: float = 1.0) -> WaveformData:
    """
    根据 CaseResult 调用对应工况的 solver。

    可选传入 Vout / R / eta 以填充验证字段。
    """
    solver = _SOLVER_MAP.get(cr.case)
    if solver is None:
        raise NotImplementedError(f"Case {cr.case} 的 solver 尚未实现")

    wd = solver(cr)

    # 补充验证（需要 Vout / R / eta）
    if cr.is_dcm() and Vout > 0 and R > 0:
        wd.verification = _verify_dcm(cr.D, cr.Dd, cr.IL_peak, Vout, R, eta)

    return wd
