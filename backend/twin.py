"""Portfolio Twin: a risk-aware copy of the portfolio with part of the equity moved to income assets."""
from __future__ import annotations

import math
import random
from typing import Dict, List

from .assets import ASSETS, TWIN_CLASSES, corr
from .engine import analyse, class_real_return
from . import market_data as md
from .market import class_paths, cholesky, corr_matrix, correlated_normals
from .tax_rules import slab_rate

CLASS_OF = {"EQUITY": "nifty50", "REIT": "reit_invit_index", "INVIT": "reit_invit_index", "BOND": "gsec_index"}


def _port_stats(w: List[float], mu: List[float]) -> Dict[str, float]:
    vols = [ASSETS[k]["vol"] for k in TWIN_CLASSES]
    var = sum(w[i] * w[j] * vols[i] * vols[j] * corr(TWIN_CLASSES[i], TWIN_CLASSES[j])
              for i in range(3) for j in range(3))
    return dict(mu=sum(w[i] * mu[i] for i in range(3)), vol=math.sqrt(var))


def _simulate(w_you: List[float], w_twin: List[float], mu: List[float], start: float, n: int = 600,
              months: int = 60, seed: int = 5) -> dict:
    rng = random.Random(seed)
    L = cholesky(corr_matrix(TWIN_CLASSES))
    mu_m = [math.log(1 + m) / 12 for m in mu]
    sig_m = [ASSETS[k]["vol"] / math.sqrt(12) for k in TWIN_CLASSES]
    you_paths: List[List[float]] = []
    twin_paths: List[List[float]] = []
    better = 0
    for _ in range(n):
        vy = vt = start
        py, pt = [start], [start]
        for t in range(months):
            z = correlated_normals(rng, L)
            g = [math.exp(mu_m[i] + sig_m[i] * z[i]) for i in range(3)]
            vy *= sum(w_you[i] * g[i] for i in range(3))
            vt *= sum(w_twin[i] * g[i] for i in range(3))
            if (t + 1) % 12 == 0:
                py.append(vy)
                pt.append(vt)
        you_paths.append(py)
        twin_paths.append(pt)
        better += vt > vy

    def band(paths: List[List[float]]) -> List[dict]:
        out = []
        for y in range(months // 12 + 1):
            col = sorted(p[y] for p in paths)

            def q(f: float) -> float:
                return col[min(int(f * (len(col) - 1) + 0.5), len(col) - 1)]
            out.append(dict(year=y, p10=q(0.1), p50=q(0.5), p90=q(0.9)))
        return out
    return dict(you=band(you_paths), twin=band(twin_paths), prob_twin_better=better / n * 100)


def build(slab: float = 30, inflation: float = 5.0, shift: float = 15.0) -> dict:
    a = analyse(slab, inflation)
    holdings = a["holdings"]
    total = a["totals"]["app_value"]
    s = slab_rate(slab)
    cls_val = {k: 0.0 for k in TWIN_CLASSES}
    for h in holdings:
        cls_val[CLASS_OF[h["type"]]] += h["market_value"]
    w_you = [cls_val[k] / total for k in TWIN_CLASSES]
    shift_w = min(shift / 100.0, w_you[0] * 0.9)
    mu = [class_real_return(k, slab, 5, inflation)["real_return"] for k in TWIN_CLASSES]

    # slab-aware optimiser: split of the moved money between REIT/InvIT and bonds (mean-variance, gamma = 3)
    best_a, best_obj = 0.0, -9e9
    for step in range(11):
        share = step / 10
        w = [w_you[0] - shift_w, w_you[1] + shift_w * share, w_you[2] + shift_w * (1 - share)]
        st = _port_stats(w, mu)
        obj = st["mu"] - 0.5 * 3.0 * st["vol"] ** 2
        if obj > best_obj:
            best_obj, best_a = obj, share
    w_twin = [w_you[0] - shift_w, w_you[1] + shift_w * best_a, w_you[2] + shift_w * (1 - best_a)]
    st_you, st_twin = _port_stats(w_you, mu), _port_stats(w_twin, mu)

    yld = [ASSETS[k]["yld"] * (1 - ASSETS[k]["taxable"] * s) for k in TWIN_CLASSES]
    income_you = sum(w_you[i] * total * yld[i] for i in range(3))
    income_twin = sum(w_twin[i] * total * yld[i] for i in range(3))

    eq_scale = w_twin[0] / w_you[0]
    twin_hold = []
    for h in holdings:
        v = h["market_value"] * (eq_scale if h["type"] == "EQUITY" else 1.0)
        twin_hold.append(dict(symbol=h["symbol"], name=h["name"], type=h["type"], you=h["market_value"], twin=v))
    twin_hold.append(dict(symbol="INCOME-1", name="REIT / InvIT basket (added)", type="REIT",
                          you=0.0, twin=shift_w * best_a * total))
    twin_hold.append(dict(symbol="INCOME-2", name="G-Sec / bond basket (added)", type="BOND",
                          you=0.0, twin=shift_w * (1 - best_a) * total))
    twin_hold = [t for t in twin_hold if t["you"] > 0 or t["twin"] > 1]
    top_you = max(h["market_value"] for h in holdings) / total * 100
    top_twin = max(t["twin"] for t in twin_hold) / total * 100

    sim = _simulate(w_you, w_twin, mu, total)
    infl = inflation / 100.0

    # tracker: last 12 months on the simulated market, both at today's weights, in real terms
    paths = class_paths(60)
    real = md.index_ratios(12)
    tr = []
    for m in range(0, 13):
        idx = 48 + m
        rel = [real[k][m] if k in real else paths[k][idx] / paths[k][48] for k in TWIN_CLASSES]
        acc = [(1 + (0.0 if (k == "gsec_index" and k in real) else yld[i])) ** (m / 12) for i, k in enumerate(TWIN_CLASSES)]
        d = (1 + infl) ** (m / 12)
        tr.append(dict(m=m, you=100 * sum(w_you[i] * rel[i] * acc[i] for i in range(3)) / d,
                       twin=100 * sum(w_twin[i] * rel[i] * acc[i] for i in range(3)) / d))
    return dict(
        slab=slab, inflation=inflation, shift=shift_w * 100, income_share_of_shift=best_a * 100,
        weights=dict(labels=["Stocks", "REITs & InvITs", "Bonds"], you=[x * 100 for x in w_you],
                     twin=[x * 100 for x in w_twin]),
        metrics=dict(
            you=dict(real_return=st_you["mu"] * 100, vol=st_you["vol"] * 100, income=income_you, top_pct=top_you),
            twin=dict(real_return=st_twin["mu"] * 100, vol=st_twin["vol"] * 100, income=income_twin, top_pct=top_twin)),
        class_real_returns=[dict(label=ASSETS[k]["label"], real=mu[i] * 100) for i, k in enumerate(TWIN_CLASSES)],
        holdings=twin_hold,
        fan=dict(you=sim["you"], twin=sim["twin"], prob_twin_better=sim["prob_twin_better"], start=total, years=5),
        tracker=tr, tracker_live=bool(real),
        disclaimer="Simulation using stated assumptions. Not a forecast, price target or investment advice.",
    )
