from __future__ import annotations

from typing import Dict, List

from .assets import ASSETS, TWIN_CLASSES
from .engine import analyse, class_real_return
from . import market_data as md
from .market import class_paths
from .tax_rules import RULES, slab_rate

PROXY = {
    "nifty50": "Nifty 50 index (^NSEI)",
    "reit_invit_index": "equal-weight Embassy, Mindspace, IRB InvIT, PG InvIT (proxy for the index)",
    "gsec_index": "10-year G-Sec ETF (proxy for the index)",
}
LABELS = {"nifty50": "Nifty 50", "reit_invit_index": "Nifty REITs & InvITs", "gsec_index": "G-Sec index"}


def build(slab: float = 30, inflation: float = 5.0, months: int = 36) -> dict:
    months = max(12, min(60, months))
    paths = class_paths(60)
    real = md.index_ratios(months)
    s = slab_rate(slab)
    cess = 1 + RULES["cess"]
    series: List[dict] = []
    for m in range(0, months + 1):
        idx = 60 - months + m
        row: Dict[str, float] = dict(m=m - months)
        yrs = m / 12
        for k in TWIN_CLASSES:
            a = ASSETS[k]
            p = real[k][m] if k in real else paths[k][idx] / paths[k][60 - months]
            yld = 0.0 if (k == "gsec_index" and k in real) else a["yld"]  # G-Sec ETF price already accrues interest
            pre = (1 + yld) ** yrs * p
            y_at = (1 + yld * (1 - a["taxable"] * s)) ** yrs
            rate = RULES["ltcg_rate"] if yrs >= 1 else (RULES["stcg_rate_112a"] if a["cg"] == "112a" else s / cess)
            gain_tax = max(p - 1, 0) * rate * cess if a["cg"] != "none" else 0
            row[k + "_pre"] = pre * 100
            row[k + "_real"] = y_at * (p - gain_tax) / (1 + inflation / 100) ** yrs * 100
        series.append(row)
    a = analyse(slab, inflation)
    return dict(
        slab=slab, inflation=inflation, months=months, labels=LABELS, series=series,
        sources={k: ("Yahoo Finance: " + PROXY[k] if k in real else "Simulated (demo)") for k in TWIN_CLASSES},
        live=bool(real),
        summary=[dict(key=k, label=LABELS[k], pre_tax=series[-1][k + "_pre"] - 100,
                      real=series[-1][k + "_real"] - 100,
                      real_5y_cagr=class_real_return(k, slab, 5, inflation)["real_return"] * 100)
                 for k in TWIN_CLASSES],
        holdings=[dict(symbol=h["symbol"], name=h["name"], type=h["type"], app_return=h["app_return_pct"],
                       real_cagr=h["real_return_cagr_pct"], benchmark=h["benchmark_real_cagr_pct"],
                       delta=h["vs_benchmark_pct"]) for h in a["holdings"]],
    )
