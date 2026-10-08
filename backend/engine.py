"""Real Value engine: tax, costs and inflation applied to every lot, merged by ISIN."""
from __future__ import annotations

from collections import OrderedDict
from typing import Dict, List

from .assets import ASSETS, BENCHMARK_FOR
from . import market_data as md
from .data import LOTS, SECURITIES, OWNERSHIP
from .fmt import inr
from .tax_rules import RULES, slab_rate

YEAR = 365.25


def _is_112a(kind: str) -> bool:
    return kind in ("EQUITY", "REIT", "INVIT")


def class_real_return(asset_key: str, slab: float, years: float = 5, inflation: float = 5.0,
                      amount: float = 500000.0) -> Dict[str, float]:
    """Real, after-tax annual return of an asset class on a reference amount (income reinvested)."""
    a = ASSETS[asset_key]
    s = slab_rate(slab)
    infl = inflation / 100.0
    y_at = a["yld"] * (1 - a["taxable"] * s)
    basis = amount * (1 + y_at) ** years
    gross = basis * (1 + a["price_g"]) ** years
    gain = gross - basis
    tax = 0.0
    if a["cg"] == "112a":
        tax = max(gain - RULES["ltcg_exemption_112a"], 0) * RULES["ltcg_rate"] * (1 + RULES["cess"])
    elif a["cg"] == "debt":
        tax = max(gain, 0) * RULES["ltcg_rate"] * (1 + RULES["cess"])
    costs = 0.0 if a["cg"] in ("debt", "none") else gross * (RULES["stt_sell"] + RULES["other_charges"])
    after = gross - tax - costs
    real = (after / amount) ** (1 / years) / (1 + infl) - 1
    nominal_pre = ((1 + a["price_g"]) * (1 + a["yld"])) - 1
    return dict(gross=gross, tax=tax, costs=costs, after_tax=after, real_return=real,
                nominal_pre_tax=nominal_pre, after_tax_nominal=(after / amount) ** (1 / years) - 1)


def _lot_rows(slab: float, inflation: float) -> List[dict]:
    s = slab_rate(slab)
    cess = 1 + RULES["cess"]
    infl = inflation / 100.0
    rows = []
    for sym, broker, qty, avg, days in LOTS:
        sec = SECURITIES[sym]
        px, live = md.price(sym, sec["price"])
        if live:
            # real close on the purchase date; if Yahoo has no history that far back, keep the demo gain ratio
            avg_eff = md.buy_price(sym, days) or avg / sec["price"] * px
        else:
            avg_eff = avg
        mv = qty * px
        cost = qty * avg_eff
        rows.append(dict(sym=sym, broker=broker, qty=qty, avg=avg_eff, days=days, mv=mv, cost=cost, gain=mv - cost,
                         years=max(days / YEAR, 0.1), long=days >= RULES["long_term_days"],
                         kind=sec["type"], sec=sec, px=px, live=live,
                         inc=sec["income"] / sec["price"] * px))
    # Spread the yearly LTCG exemption in proportion to each long-term 112A gain.
    pool = sum(r["gain"] for r in rows if _is_112a(r["kind"]) and r["long"] and r["gain"] > 0)
    share = min(1.0, RULES["ltcg_exemption_112a"] / pool) if pool > 0 else 0.0
    for r in rows:
        g = max(r["gain"], 0.0)
        if _is_112a(r["kind"]):
            if r["long"]:
                tax = g * (1 - share) * RULES["ltcg_rate"] * cess
            else:
                tax = g * RULES["stcg_rate_112a"] * cess
        else:  # listed bonds
            tax = g * RULES["ltcg_rate"] * cess if r["long"] else g * s
        costs = 0.0 if r["kind"] == "BOND" else r["mv"] * RULES["stt_sell"]
        costs += r["mv"] * RULES["other_charges"]
        inc_gross = r["inc"] * r["qty"] * r["years"]
        inc_net = inc_gross * (1 - s)
        after = r["mv"] - tax - costs
        real = after / (1 + infl) ** r["years"]
        r.update(tax=tax, costs=costs, income_gross=inc_gross, income_net=inc_net, after_tax=after, real=real,
                 annual_income_net=r["inc"] * r["qty"] * (1 - s), annual_income_gross=r["inc"] * r["qty"])
    return rows


def analyse(slab: float = 30, inflation: float = 5.0) -> dict:
    lots = _lot_rows(slab, inflation)
    merged: "OrderedDict[str, dict]" = OrderedDict()
    for r in lots:
        m = merged.setdefault(r["sym"], dict(
            symbol=r["sym"], name=r["sec"]["name"], isin=r["sec"]["isin"], type=r["kind"], price=r["px"], live=r["live"],
            brokers=[], lots=0, qty=0, invested=0.0, market_value=0.0, tax=0.0, costs=0.0, after_tax=0.0,
            real_value=0.0, income_net=0.0, annual_income_net=0.0, annual_income_gross=0.0, _w_years=0.0, short_lots=0))
        if r["broker"] not in m["brokers"]:
            m["brokers"].append(r["broker"])
        m["lots"] += 1
        m["qty"] += r["qty"]
        m["invested"] += r["cost"]
        m["market_value"] += r["mv"]
        m["tax"] += r["tax"]
        m["costs"] += r["costs"]
        m["after_tax"] += r["after_tax"]
        m["real_value"] += r["real"]
        m["income_net"] += r["income_net"]
        m["annual_income_net"] += r["annual_income_net"]
        m["annual_income_gross"] += r["annual_income_gross"]
        m["_w_years"] += r["years"] * r["cost"]
        m["short_lots"] += 0 if r["long"] else 1

    holdings = []
    for m in merged.values():
        years = m.pop("_w_years") / m["invested"]
        m["years"] = round(years, 2)
        m["avg_price"] = m["invested"] / m["qty"]
        m["gain"] = m["market_value"] - m["invested"]
        m["app_return_pct"] = m["gain"] / m["invested"] * 100
        m["real_gain"] = m["real_value"] - m["invested"]
        total_after = m["after_tax"] + m["income_net"]
        m["real_return_cagr_pct"] = ((total_after / m["invested"]) ** (1 / years) / (1 + inflation / 100) - 1) * 100
        bench = class_real_return(BENCHMARK_FOR[m["type"]], slab, max(years, 1), inflation)
        m["benchmark_real_cagr_pct"] = bench["real_return"] * 100
        m["vs_benchmark_pct"] = m["real_return_cagr_pct"] - m["benchmark_real_cagr_pct"]
        holdings.append(m)

    def tot(k: str) -> float:
        return sum(h[k] for h in holdings)

    mv, invested = tot("market_value"), tot("invested")
    tax, costs, after, real = tot("tax"), tot("costs"), tot("after_tax"), tot("real_value")
    income_net = tot("annual_income_net")
    for h in holdings:
        h["weight_pct"] = h["market_value"] / mv * 100

    by_type: Dict[str, float] = {}
    by_broker: Dict[str, float] = {}
    for r in lots:
        by_type[r["kind"]] = by_type.get(r["kind"], 0.0) + r["mv"]
        by_broker[r["broker"]] = by_broker.get(r["broker"], 0.0) + r["mv"]
    top = max(holdings, key=lambda h: h["market_value"])
    equity_pct = by_type.get("EQUITY", 0) / mv * 100

    insights = [
        dict(tone="warn", title="Your app overstates your wealth",
             text=f"Apps show {inr(mv)}. After tax and costs it is {inr(after)}, and {inr(real)} in real terms."),
        dict(tone="info", title="Concentration check",
             text=f"{equity_pct:.0f}% of your money is in stocks, and {top['name']} alone is {top['weight_pct']:.0f}%."),
        dict(tone="good", title="Steady income is working",
             text=f"Your holdings pay about {inr(income_net)} a year after tax at your {slab:.0f}% slab."),
    ]
    short = [h for h in holdings if h["short_lots"]]
    if short:
        names = ", ".join(h["symbol"] for h in short)
        insights.append(dict(tone="info", title="Short-term lots found",
                             text=f"{names} include lots held under 12 months. Selling them early is taxed at 20%, not 12.5%."))

    return dict(
        slab=slab, inflation=inflation, rules_version=RULES["version"],
        totals=dict(invested=invested, app_value=mv, tax=tax, costs=costs, after_tax=after, real_value=real,
                    inflation_erosion=after - real, gain_app=mv - invested, gain_real=real - invested,
                    overstatement_pct=(mv - real) / mv * 100, annual_income_net=income_net),
        waterfall=[
            dict(label="App shows", value=mv, kind="total"),
            dict(label="Capital gains tax", value=-tax, kind="delta"),
            dict(label="STT & charges", value=-costs, kind="delta"),
            dict(label="Inflation", value=-(after - real), kind="delta"),
            dict(label="Real value", value=real, kind="total"),
        ],
        allocation=[dict(name=k, value=v, pct=v / mv * 100) for k, v in sorted(by_type.items(), key=lambda x: -x[1])],
        brokers=[dict(name=k, value=v, pct=v / mv * 100) for k, v in sorted(by_broker.items(), key=lambda x: -x[1])],
        holdings=sorted(holdings, key=lambda h: -h["market_value"]),
        stats=dict(holdings=len(holdings), lots=len(lots), duplicates_merged=len(lots) - len(holdings),
                   brokers=len(by_broker), equity_pct=equity_pct, top_symbol=top["symbol"], top_pct=top["weight_pct"]),
        insights=insights,
        data_source=dict(
            live=any(h["live"] for h in holdings), provider="Yahoo Finance", as_of=md.as_of(),
            live_symbols=[h["symbol"] for h in holdings if h["live"]],
            demo_symbols=[h["symbol"] for h in holdings if not h["live"]],
            cost_basis="real close on each purchase date" if any(h["live"] for h in holdings) else "demo purchase prices"),
    )


def slab_matrix(inflation: float = 5.0, years: int = 5) -> dict:
    slabs = RULES["slabs"]
    keys = ["nifty50", "reit", "invit", "gsec", "fd"]
    rows = []
    for k in keys:
        rows.append(dict(key=k, label=ASSETS[k]["label"],
                         pre_tax=class_real_return(k, 0, years, inflation)["nominal_pre_tax"] * 100,
                         values=[class_real_return(k, s, years, inflation)["real_return"] * 100 for s in slabs]))
    for r in rows:
        r["vol"] = ASSETS[r["key"]]["vol"] * 100
    best = []
    for i, s in enumerate(slabs):
        mk = [r for r in rows if r["key"] != "fd"]
        b = max(mk, key=lambda r: r["values"][i] / r["vol"])
        best.append(dict(slab=s, key=b["key"], label=b["label"], real=b["values"][i],
                         risk_adj=b["values"][i] / b["vol"]))
    example = class_real_return("nifty50", 30, 5, inflation)
    return dict(slabs=slabs, rows=rows, best=best, inflation=inflation, years=years, example=example)


def ownership(slab: float = 30, inflation: float = 5.0) -> dict:
    a = analyse(slab, inflation)
    items = []
    for h in a["holdings"]:
        o = OWNERSHIP.get(h["symbol"])
        if not o:
            continue
        items.append(dict(symbol=h["symbol"], name=h["name"], kind=o["kind"], units=h["qty"],
                          physical=h["qty"] * o["per_unit"], physical_unit=o["unit"],
                          income_year=h["annual_income_gross"],
                          income_year_net=h["annual_income_net"], value=h["market_value"]))
    return dict(items=items, note="Physical-asset equivalents are illustrative approximations for education.")


def example_stock(amount: float = 500000.0, growth: float = 12.0, years: int = 5, inflation: float = 5.0) -> dict:
    """The deck's headline example: one stock, no dividends, sold after `years`."""
    gross = amount * (1 + growth / 100) ** years
    gain = gross - amount
    tax = max(gain - RULES["ltcg_exemption_112a"], 0) * RULES["ltcg_rate"] * (1 + RULES["cess"])
    costs = gross * (RULES["stt_sell"] + RULES["other_charges"])
    after = gross - tax - costs
    real = after / (1 + inflation / 100) ** years
    return dict(amount=amount, growth=growth, years=years, inflation=inflation, app_value=gross, tax=tax,
                costs=costs, after_tax=after, real_value=real, inflation_erosion=after - real)
