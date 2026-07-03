"""
classifier.py — 工况判断模块

双相交错 180° 非同步 Boost 变换器工况分类。

分类逻辑（按优先级顺序）：
  1. 计算 CCM 占空比 D_ccm 和 CRM 临界负载 R_crm
  2. 若 R ≤ R_crm → CCM，当前仅支持 Case A（D_d < 0.5，即 D > 0.5）
  3. 若 R > R_crm → DCM，用能量平衡方程求解 D_dcm
     - D > 0.5              → Case C1
     - D ≤ 0.5, D+Dd < 0.5 → Case C2a
     - D ≤ 0.5, D+Dd ≥ 0.5 → Case C2b

公开接口：
  classify(Vin, Vout, R, L, Vf, fs, eta) -> CaseResult
"""

import math
from dataclasses import dataclass
from typing import Literal

CaseName = Literal["A", "C1", "C2a", "C2b"]


@dataclass
class CaseResult:
    """工况判断结果，包含分类信息和基础电气参数。"""

    # 工况名称
    case: CaseName

    # 基础参数（由输入直接导出）
    Ts: float          # 开关周期 (s)
    D_ccm: float       # CCM 占空比（伏秒平衡，含 Vf）
    R_crm: float       # CRM 临界负载 (Ω)

    # 工作点参数（CCM 时 D = D_ccm，DCM 时 D = D_dcm）
    D: float           # 实际占空比
    Dd: float          # 二极管占空比 δ
    D_plus_Dd: float   # D + Dd
    IL_peak: float     # 电感（二极管）电流峰值 (A)
    m: float           # TOFF 下降斜率 (A/s)，正值

    def is_ccm(self) -> bool:
        return self.case == "A"

    def is_dcm(self) -> bool:
        return self.case in ("C1", "C2a", "C2b")

    def summary(self) -> str:
        lines = [
            f"Case       : {self.case}",
            f"Mode       : {'CCM' if self.is_ccm() else 'DCM'}",
            f"Ts         : {self.Ts * 1e6:.4f} µs",
            f"D_ccm      : {self.D_ccm:.6f}",
            f"R_crm      : {self.R_crm:.2f} Ω",
            f"D          : {self.D:.6f}",
            f"Dd (δ)     : {self.Dd:.6f}",
            f"D + Dd     : {self.D_plus_Dd:.6f}",
            f"IL_peak    : {self.IL_peak:.4f} A",
            f"m          : {self.m:.4e} A/s",
        ]
        return "\n".join(lines)


def _calc_ccm_duty(Vin: float, Vout: float, Vf: float) -> float:
    """CCM 占空比（伏秒平衡，含二极管压降）。"""
    return 1.0 - Vin / (Vout + Vf)


def _calc_r_crm(Vin: float, Vout: float, L: float, Vf: float,
                fs: float, eta: float, D_ccm: float) -> float:
    """
    CRM 临界负载电阻。

    推导：
      CRM 边界 → IL_valley = 0 → IL_avg = ΔIL / 2
      ΔIL = Vin·D_ccm·Ts / L
      Pin_crm = 2·Vin·IL_avg_crm  （双相）
      Pout_crm = η·Pin_crm
      R_crm = Vout² / Pout_crm
    """
    Ts = 1.0 / fs
    delta_IL = Vin * D_ccm * Ts / L
    IL_avg_crm = delta_IL / 2.0
    Pout_crm = eta * 2.0 * Vin * IL_avg_crm
    return Vout ** 2 / Pout_crm


def _solve_dcm_duty(Vin: float, Vout: float, R: float, L: float,
                    Vf: float, fs: float, eta: float) -> float:
    """
    DCM 能量平衡方程求解占空比 D。

    方程：Vout² - (Vin - Vf)·Vout = R·η·Vin²·D²·Ts / L
    解：  D = sqrt( [Vout² - (Vin-Vf)·Vout] · L / (R·η·Vin²·Ts) )
    """
    Ts = 1.0 / fs
    numerator = (Vout ** 2 - (Vin - Vf) * Vout) * L
    denominator = R * eta * Vin ** 2 * Ts
    D_sq = numerator / denominator
    if D_sq < 0:
        raise ValueError(
            f"DCM 方程无解（D² = {D_sq:.4f} < 0）。"
            "请检查参数：Vout 是否大于 Vin - Vf？"
        )
    if D_sq > 1:
        raise ValueError(
            f"DCM 方程无解（D² = {D_sq:.4f} > 1）。"
            f"当前参数无法在 DCM 下维持 Vout = {Vout} V，请减小负载或增大电感。"
        )
    return math.sqrt(D_sq)


def classify(
    Vin: float,
    Vout: float,
    R: float,
    L: float,
    Vf: float,
    fs: float,
    eta: float,
) -> CaseResult:
    """
    判断双相交错 Boost 的工作工况。

    参数
    ----
    Vin   : 输入电压 (V)
    Vout  : 输出电压 (V)
    R     : 总负载电阻 (Ω)
    L     : 每相电感量 (H)
    Vf    : 二极管正向压降 (V)
    fs    : 开关频率 (Hz)
    eta   : 效率（0 < η ≤ 1）

    返回
    ----
    CaseResult  包含工况名称和基础电气参数
    """
    if not (0 < eta <= 1):
        raise ValueError(f"效率 η = {eta} 超出范围 (0, 1]")
    if Vout <= Vin:
        raise ValueError(f"Boost 变换器要求 Vout ({Vout}V) > Vin ({Vin}V)")

    Ts = 1.0 / fs
    m = (Vout + Vf - Vin) / L   # TOFF 下降斜率（正值）

    D_ccm = _calc_ccm_duty(Vin, Vout, Vf)
    R_crm = _calc_r_crm(Vin, Vout, L, Vf, fs, eta, D_ccm)

    if R <= R_crm:
        # ── CCM：Case A（D_d = 1 - D < 0.5，即 D > 0.5）──
        D = D_ccm
        Dd = 1.0 - D
        IL_peak = (Vin * D * Ts / L) / 2.0 + (Vout * Dd / (eta * 2.0 * Vin / Ts))
        # 用更直接的方式：IL_peak = IL_avg + ΔIL/2
        delta_IL = Vin * D * Ts / L
        # IL_avg 由功率守恒（单相）
        # Pout_sp = Vout²/(2R)，Pin_sp = Pout_sp/η，IL_avg = Pin_sp/Vin
        IL_avg = Vout ** 2 / (2.0 * R * eta * Vin)
        IL_peak = IL_avg + delta_IL / 2.0
        return CaseResult(
            case="A",
            Ts=Ts,
            D_ccm=D_ccm,
            R_crm=R_crm,
            D=D,
            Dd=Dd,
            D_plus_Dd=D + Dd,   # = 1.0 in CCM
            IL_peak=IL_peak,
            m=m,
        )

    # ── DCM ──
    D = _solve_dcm_duty(Vin, Vout, R, L, Vf, fs, eta)
    Dd = D * Vin / (Vout + Vf - Vin)
    D_plus_Dd = D + Dd
    IL_peak = Vin * D * Ts / L

    if D > 0.5:
        case: CaseName = "C1"
    elif D_plus_Dd < 0.5:
        case = "C2a"
    else:
        case = "C2b"

    return CaseResult(
        case=case,
        Ts=Ts,
        D_ccm=D_ccm,
        R_crm=R_crm,
        D=D,
        Dd=Dd,
        D_plus_Dd=D_plus_Dd,
        IL_peak=IL_peak,
        m=m,
    )
