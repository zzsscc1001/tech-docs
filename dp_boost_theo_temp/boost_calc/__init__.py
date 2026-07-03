# boost_calc — 双相交错 180° 非同步 Boost 理论计算包
#
# 模块结构：
#   classifier.py  — 工况判断（CCM/DCM 及子情况 A / C1 / C2a / C2b）
#   solvers.py     — 各工况公式计算（返回统一格式的结果 dict）
#   plotter.py     — 波形绘图（分相电流 + 总电流）
#   run_cases.py   — 计算用例入口（直接运行）

from .classifier import classify, CaseResult
from .solvers import solve
from .plotter import plot_waveform

__all__ = ["classify", "CaseResult", "solve", "plot_waveform"]
