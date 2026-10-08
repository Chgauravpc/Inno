import math

import pytest
from fastapi.testclient import TestClient

from api.index import app
from backend import benchmarks, engine, explain, fmt, twin
from backend.data import LOTS
from backend.tax_rules import RULES

c = TestClient(app)
SLABS = RULES["slabs"]


# ---------- deck numbers ----------
def test_deck_example_matches_slides():
    e = engine.example_stock()
    assert round(e["app_value"]) == 881171          # Rs 8.81 L
    assert abs(e["tax"] - 33302) < 5                # Rs 33.3K LTCG
    assert 900 < e["costs"] < 1100                  # ~Rs 1K STT & charges
    assert abs(e["real_value"] - 663554) < 5        # Rs 6.64 L
    assert round((e["app_value"] - e["amount"]) / 1e5, 2) == 3.81   # app gain
    assert round((e["real_value"] - e["amount"]) / 1e5, 2) == 1.64  # real gain


def test_bond_slab_example_matches_slides():
    assert round(engine.class_real_return("gsec", 30)["real_return"] * 100, 1) == 0.2
    assert round(engine.class_real_return("gsec", 0)["real_return"] * 100, 1) == 2.4


# ---------- engine invariants ----------
@pytest.mark.parametrize("slab", SLABS)
@pytest.mark.parametrize("infl", [2, 5, 9])
def test_portfolio_invariants(slab, infl):
    a = engine.analyse(slab, infl)
    t = a["totals"]
    assert math.isclose(sum(h["market_value"] for h in a["holdings"]), t["app_value"])
    assert math.isclose(sum(x["pct"] for x in a["allocation"]), 100, abs_tol=1e-6)
    assert math.isclose(sum(x["pct"] for x in a["brokers"]), 100, abs_tol=1e-6)
    assert math.isclose(sum(h["weight_pct"] for h in a["holdings"]), 100, abs_tol=1e-6)
    assert math.isclose(t["app_value"] - t["tax"] - t["costs"], t["after_tax"], rel_tol=1e-9)
    assert math.isclose(t["after_tax"] - t["inflation_erosion"], t["real_value"], rel_tol=1e-9)
    wf = a["waterfall"]
    assert math.isclose(wf[0]["value"] + sum(w["value"] for w in wf[1:4]), wf[4]["value"], rel_tol=1e-9)
    assert t["real_value"] < t["after_tax"] < t["app_value"]
    assert all(h["tax"] >= 0 and h["costs"] > 0 for h in a["holdings"])


def test_lots_merge_by_isin():
    a = engine.analyse()
    assert a["stats"]["lots"] == len(LOTS) == 13
    assert a["stats"]["holdings"] == len({lot[0] for lot in LOTS}) == 11
    assert a["stats"]["duplicates_merged"] == 2
    assert len({h["isin"] for h in a["holdings"]}) == 11
    rel = next(h for h in a["holdings"] if h["symbol"] == "RELIANCE")
    assert rel["qty"] == 120 and set(rel["brokers"]) == {"Zerodha", "Groww"} and rel["lots"] == 2


def test_short_term_lots_flagged_and_taxed_at_20pct():
    a = engine.analyse(30, 5)
    infy = next(h for h in a["holdings"] if h["symbol"] == "INFY")
    assert infy["short_lots"] == 1
    assert math.isclose(infy["tax"], infy["gain"] * 0.20 * 1.04, rel_tol=1e-9)
    assert any("Short-term" in i["title"] for i in a["insights"])


def test_bond_has_no_stt_and_ltcg_rate():
    a = engine.analyse(30, 5)
    rec = next(h for h in a["holdings"] if h["symbol"] == "RECNCD")
    assert math.isclose(rec["costs"], rec["market_value"] * RULES["other_charges"], rel_tol=1e-9)
    assert math.isclose(rec["tax"], rec["gain"] * 0.125 * 1.04, rel_tol=1e-9)


def test_exemption_never_exceeds_limit():
    a = engine.analyse(30, 5)
    eq_like = [h for h in a["holdings"] if h["type"] in ("EQUITY", "REIT", "INVIT") and h["short_lots"] == 0]
    full = sum(max(h["gain"], 0) for h in eq_like) * 0.125 * 1.04
    paid = sum(h["tax"] for h in eq_like)
    assert 0 < full - paid <= RULES["ltcg_exemption_112a"] * 0.125 * 1.04 + 1


def test_more_inflation_means_lower_real_value():
    vals = [engine.analyse(30, i)["totals"]["real_value"] for i in (2, 4, 6, 8)]
    assert vals == sorted(vals, reverse=True)


def test_equity_tax_independent_of_slab_but_income_is_not():
    a, b = engine.analyse(0, 5), engine.analyse(30, 5)
    ta = {h["symbol"]: h["tax"] for h in a["holdings"] if h["type"] == "EQUITY"}
    tb = {h["symbol"]: h["tax"] for h in b["holdings"] if h["type"] == "EQUITY"}
    assert ta == tb
    assert a["totals"]["annual_income_net"] > b["totals"]["annual_income_net"]


def test_slab_matrix_shape_and_monotone():
    m = engine.slab_matrix(5)
    assert m["slabs"] == SLABS and len(m["rows"]) == 5 and len(m["best"]) == 6
    for r in m["rows"]:
        assert len(r["values"]) == 6
        assert r["values"] == sorted(r["values"], reverse=True), r["key"]
    assert m["best"][0]["key"] == "gsec"
    assert m["best"][-1]["key"] == "nifty50"


# ---------- twin ----------
@pytest.mark.parametrize("shift", [10, 15, 20])
@pytest.mark.parametrize("slab", [0, 30])
def test_twin(shift, slab):
    t = twin.build(slab, 5, shift)
    assert math.isclose(sum(t["weights"]["you"]), 100, abs_tol=1e-6)
    assert math.isclose(sum(t["weights"]["twin"]), 100, abs_tol=1e-6)
    assert math.isclose(t["weights"]["you"][0] - t["weights"]["twin"][0], shift, abs_tol=1e-6)
    assert t["metrics"]["twin"]["vol"] < t["metrics"]["you"]["vol"]
    assert t["metrics"]["twin"]["top_pct"] < t["metrics"]["you"]["top_pct"]
    assert t["metrics"]["twin"]["income"] > t["metrics"]["you"]["income"]
    assert math.isclose(sum(h["twin"] for h in t["holdings"]), sum(h["you"] for h in t["holdings"]), rel_tol=1e-9)
    f = t["fan"]
    assert len(f["you"]) == 6 and f["you"][0]["p50"] == f["start"]
    for b in f["you"] + f["twin"]:
        assert b["p10"] <= b["p50"] <= b["p90"]
    assert 0 <= f["prob_twin_better"] <= 100
    assert len(t["tracker"]) == 13 and t["tracker"][0]["you"] == 100 == t["tracker"][0]["twin"]


def test_twin_is_deterministic():
    assert twin.build(30, 5, 15)["fan"] == twin.build(30, 5, 15)["fan"]


# ---------- benchmarks ----------
@pytest.mark.parametrize("months", [12, 24, 36, 60])
def test_benchmarks(months):
    b = benchmarks.build(30, 5, months)
    assert len(b["series"]) == months + 1
    assert b["series"][0]["nifty50_pre"] == 100 and b["series"][0]["gsec_index_real"] == 100
    for k in ("nifty50", "reit_invit_index", "gsec_index"):
        assert b["series"][-1][k + "_real"] < b["series"][-1][k + "_pre"]
    assert len(b["holdings"]) == 11


# ---------- explainer ----------
QS = {
    "en": {"why": "why is my real value lower", "ltcg": "how is capital gains tax calculated", "reit": "what are reits",
           "twin": "is my portfolio too risky", "inflation": "what about inflation", "slab": "which asset suits my slab"},
    "hi": {"why": "क्यों कम है", "ltcg": "टैक्स कैसे बनता है", "reit": "reit क्या है",
           "twin": "जोखिम कितना है", "inflation": "महंगाई का असर", "slab": "स्लैब के हिसाब से"},
    "mr": {"why": "का कमी आहे", "ltcg": "कर कसा ठरतो", "reit": "reit म्हणजे काय",
           "twin": "जोखीम किती", "inflation": "महागाई", "slab": "स्लॅब नुसार"},
}


@pytest.mark.parametrize("lang", ["en", "hi", "mr"])
@pytest.mark.parametrize("intent", ["why", "ltcg", "reit", "twin", "inflation", "slab"])
def test_explain_intents(lang, intent):
    r = explain.answer(QS[lang][intent], lang)
    assert r["intent"] == intent and r["lang"] == lang
    assert "{" not in r["answer"] and "}" not in r["answer"]


def test_explain_fallback_and_unknown_lang():
    assert explain.answer("zzz qqq", "en")["intent"] == "fallback"
    assert explain.answer("why", "xx")["lang"] == "en"


def test_explain_numbers_grounded():
    r = explain.answer("why is it lower", "en", 30, 5)
    assert fmt.inr(engine.analyse(30, 5)["totals"]["real_value"]) in r["answer"]


def test_indian_grouping_in_insights():
    import re
    for i in engine.analyse()["insights"]:
        assert not re.search(r"₹\d{1,3}(,\d{3}){2,}", i["text"])
    assert fmt.inr(1456042) == "₹14,56,042"
    assert fmt.inr(999) == "₹999" and fmt.inr(1000) == "₹1,000" and fmt.inr(12345678) == "₹1,23,45,678"
    assert fmt.inr(-2500) == "-₹2,500"



# ---------- HTTP API ----------
GETS = ["/api/py/health", "/api/py/profile", "/api/py/connect/fetch", "/api/py/portfolio", "/api/py/benchmarks",
        "/api/py/slab", "/api/py/twin", "/api/py/ownership", "/api/py/example"]


@pytest.mark.parametrize("url", GETS)
def test_get_endpoints_ok(url):
    r = c.get(url)
    assert r.status_code == 200 and r.json()


def test_post_endpoints():
    assert c.post("/api/py/connect/consent", json={}).json()["status"] == "ACTIVE"
    r = c.post("/api/py/explain", json={"question": "why", "lang": "hi", "slab": 20, "inflation": 6})
    assert r.status_code == 200 and r.json()["lang"] == "hi"
    assert c.post("/api/py/explain", json={}).status_code == 422


@pytest.mark.parametrize("url", [
    "/api/py/portfolio?slab=99", "/api/py/portfolio?slab=-1", "/api/py/portfolio?inflation=50",
    "/api/py/portfolio?slab=abc", "/api/py/twin?shift=5", "/api/py/twin?shift=40",
    "/api/py/benchmarks?months=3", "/api/py/benchmarks?months=999", "/api/py/example?years=0"])
def test_validation_rejects_bad_params(url):
    assert c.get(url).status_code == 422


def test_ownership_and_profile():
    o = c.get("/api/py/ownership").json()
    assert {i["symbol"] for i in o["items"]} == {"EMBASSY", "MINDSPACE", "IRBINVIT", "PGINVIT"}
    assert all(i["physical"] > 0 and i["income_year_net"] < i["income_year"] for i in o["items"])
    p = c.get("/api/py/profile").json()
    assert p["name"] == "Priya Sharma" and p["slabs"] == SLABS


def test_health_has_team():
    assert c.get("/api/py/health").json()["team"] == "Innovisionaries"
