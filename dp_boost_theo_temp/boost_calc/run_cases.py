"""
run_cases.py — 计算用例入口脚本

运行所有验证用例，输出理论计算结果并保存波形图。

用法：
  python -m boost_calc.run_cases
  或
  python run_cases.py   （在 dp_boost_theo_temp/ 目录下）

用例来源：00_pitfalls.md § 8 验证工况
  Case C1 : Vin=6V,  Vout=30V, R=200Ω
  Case C2a: Vin=24V, Vout=30V, R=300Ω
  Case C2b: Vin=24V, Vout=30V, R=100Ω
"""

import os
import sys

# 允许直接在 dp_boost_theo_temp/ 下运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from boost_calc.classifier import classify
from boost_calc.solvers import solve
from boost_calc.plotter import plot_waveform

# ─────────────────────────────────────────────
# 输出目录
# ─────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


# ─────────────────────────────────────────────
# 用例定义
# ─────────────────────────────────────────────
CASES = [
    {
        "name":  "Case C1",
        "Vin":   6.0,
        "Vout":  30.0,
        "R":     200.0,
        "L":     10e-6,
        "Vf":    0.7,
        "fs":    400e3,
        "eta":   0.95,
        "expected_case": "C1",
    },
    {
        "name":  "Case C2a",
        "Vin":   24.0,
        "Vout":  30.0,
        "R":     300.0,
        "L":     10e-6,
        "Vf":    0.7,
        "fs":    400e3,
        "eta":   0.95,
        "expected_case": "C2a",
    },
    {
        "name":  "Case C2b",
        "Vin":   24.0,
        "Vout":  30.0,
        "R":     100.0,
        "L":     10e-6,
        "Vf":    0.7,
        "fs":    400e3,
        "eta":   0.95,
        "expected_case": "C2b",
    },
]


# ─────────────────────────────────────────────
# 运行单个用例
# ─────────────────────────────────────────────
def run_case(case_def: dict) -> None:
    name = case_def["name"]
    params = {k: case_def[k] for k in ("Vin", "Vout", "R", "L", "Vf", "fs", "eta")}
    expected = case_def.get("expected_case")

    print("=" * 60)
    print(f"  {name}")
    print("=" * 60)
    print(
        f"  输入: Vin={params['Vin']}V  Vout={params['Vout']}V  "
        f"R={params['R']}Ω  L={params['L']*1e6:.0f}µH  "
        f"Vf={params['Vf']}V  fs={params['fs']/1e3:.0f}kHz  η={params['eta']}"
    )
    print()

    # 1. 工况判断
    cr = classify(**params)

    # 校验工况是否符合预期
    status = "✓" if cr.case == expected else f"⚠ 预期 {expected}"
    print(f"  [工况判断]  {cr.case}  {status}")
    print()
    print(cr.summary())
    print()

    # 2. 公式计算
    wd = solve(cr, Vout=params["Vout"], R=params["R"], eta=params["eta"])
    print("  [时序与验证]")
    print(wd.summary())
    print()

    # 3. 绘图
    img_name = f"{cr.case.lower()}_waveform.png"
    img_path = os.path.join(OUTPUT_DIR, img_name)
    plot_waveform(wd, params, img_path)
    print(f"  波形图已保存: {img_path}")
    print()


# ─────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────
def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print()
    print("双相交错 180° 非同步 Boost — 理论计算验证")
    print(f"输出目录: {OUTPUT_DIR}")
    print()

    for case_def in CASES:
        try:
            run_case(case_def)
        except Exception as exc:
            print(f"  [ERROR] {case_def['name']}: {exc}")
            print()

    print("=" * 60)
    print("全部用例运行完毕。")
    print("=" * 60)


if __name__ == "__main__":
    main()
