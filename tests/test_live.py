import io
import json
import time

import pytest
from fastapi.testclient import TestClient

from api.index import app
from backend import benchmarks, engine, explain, llm, market_data as md, twin
from backend.data import LOTS, SECURITIES, YF

c = TestClient(app)
WEEK = 7 * 86400


def series(start_price, end_price, weeks=262, listed_weeks=None):
    """Linear weekly closes ending now."""
    n = listed_weeks or weeks
    now = time.time()
    return [(int(now - (n - 1 - i) * WEEK), start_price + (end_price - start_price) * i / (n - 1)) for i in range(n)]


def fake_chart_factory(prices, fail=()):
    def fake(sym, rng="5y", interval="1wk", timeout=4.0):
        if sym in fail or sym not in prices:
            raise OSError("boom")
        start, end, *rest = prices[sym]
        pts = series(start, end, listed_weeks=rest[0] if rest else None)
        return dict(price=end, as_of=int(time.time()), points=pts)
    return fake


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setenv("LIVE_DATA", "1")
    md.clear_cache()
    yield monkeypatch
    md.clear_cache()


ALL = {y: (100.0, 200.0) for y in set(YF.values()) | {md.BENCH_NIFTY, md.BENCH_GSEC}}


# ---------------- Yahoo data ----------------
def test_live_prices_replace_demo_and_cost_basis_uses_history(live):
    live.setattr(md, "fetch_chart", fake_chart_factory(ALL))
    a = engine.analyse(30, 5)
    ds = a["data_source"]
    assert ds["live"] and set(ds["live_symbols"]) == set(YF) and set(ds["demo_symbols"]) == {"GS2033", "RECNCD"}
    rel = next(h for h in a["holdings"] if h["symbol"] == "RELIANCE")
    assert rel["price"] == 200.0 and rel["live"]
    # Zerodha lot bought 1500 days ago, Groww lot 520 days ago: linear 100->200 over 262 weeks
    expect_old = 100 + 100 * (262 - 1 - (1500 / 7)) / 261
    expect_new = 100 + 100 * (262 - 1 - (520 / 7)) / 261
    cost = 80 * expect_old + 40 * expect_new
    assert rel["invested"] == pytest.approx(cost, rel=0.02)
    bond = next(h for h in a["holdings"] if h["symbol"] == "GS2033")
    assert bond["price"] == SECURITIES["GS2033"]["price"] and not bond["live"]


def test_totals_still_reconcile_with_live_data(live):
    live.setattr(md, "fetch_chart", fake_chart_factory(ALL))
    a = engine.analyse(20, 6)
    t = a["totals"]
    assert t["app_value"] == pytest.approx(sum(h["market_value"] for h in a["holdings"]))
    assert t["app_value"] - t["tax"] - t["costs"] == pytest.approx(t["after_tax"])
    assert t["after_tax"] - t["inflation_erosion"] == pytest.approx(t["real_value"])
    assert sum(h["weight_pct"] for h in a["holdings"]) == pytest.approx(100)


def test_losses_are_not_taxed_and_income_scales_with_price(live):
    low = {y: (400.0, 50.0) for y in ALL}   # everything crashed
    live.setattr(md, "fetch_chart", fake_chart_factory(low))
    a = engine.analyse(30, 5)
    assert all(h["tax"] == 0 for h in a["holdings"] if h["live"])
    assert a["totals"]["gain_app"] < 0
    # yield is preserved: income/price constant, so a cheaper unit pays proportionally less
    emb = next(h for h in a["holdings"] if h["symbol"] == "EMBASSY")
    assert emb["annual_income_gross"] == pytest.approx(300 * 50 * SECURITIES["EMBASSY"]["income"] / SECURITIES["EMBASSY"]["price"])


def test_failed_symbols_fall_back_to_demo_per_symbol(live):
    live.setattr(md, "fetch_chart", fake_chart_factory(ALL, fail={"TCS.NS", "ITC.NS"}))
    ds = engine.analyse()["data_source"]
    assert ds["live"] and "TCS" in ds["demo_symbols"] and "ITC" in ds["demo_symbols"] and "INFY" in ds["live_symbols"]
    tcs = next(h for h in engine.analyse()["holdings"] if h["symbol"] == "TCS")
    assert tcs["price"] == SECURITIES["TCS"]["price"]


def test_total_outage_equals_demo_mode_and_retries_soon(live):
    live.setattr(md, "fetch_chart", fake_chart_factory({}))
    a = engine.analyse()
    assert not a["data_source"]["live"]
    assert md._cache["ttl"] == md.RETRY_AFTER      # failures are not cached for the full 15 minutes
    live.setenv("LIVE_DATA", "0")
    md.clear_cache()
    assert a["totals"] == engine.analyse()["totals"]


def test_snapshot_is_cached(live):
    calls = []
    inner = fake_chart_factory(ALL)
    live.setattr(md, "fetch_chart", lambda s, *a, **k: (calls.append(s), inner(s))[1])
    engine.analyse(); n = len(calls)
    engine.analyse(); engine.analyse(10, 3)
    assert n == len(set(md._all_symbols())) and len(calls) == n


def test_buy_price_none_when_history_too_short(live):
    short = dict(ALL); short["RELIANCE.NS"] = (100.0, 200.0, 40)   # only 40 weeks of history
    live.setattr(md, "fetch_chart", fake_chart_factory(short))
    assert md.buy_price("RELIANCE", 1500) is None
    rel = next(h for h in engine.analyse()["holdings"] if h["symbol"] == "RELIANCE")
    assert rel["invested"] > 0                      # falls back to the demo gain ratio instead of crashing


def test_value_at():
    pts = [(10, 1.0), (20, 2.0), (30, 3.0)]
    assert md.value_at(pts, 5) is None and md.value_at(pts, 10) == 1.0 and md.value_at(pts, 25) == 2.0 and md.value_at(pts, 99) == 3.0


def test_fetch_chart_parses_yahoo_payload(monkeypatch):
    payload = {"chart": {"result": [{"meta": {"regularMarketPrice": 123.4, "regularMarketTime": 1700000000},
                                     "timestamp": [1, 2, 3], "indicators": {"quote": [{"close": [1.0, None, 3.0]}]}}]}}
    monkeypatch.setattr(md.urllib.request, "urlopen", lambda req, timeout=0: io.BytesIO(json.dumps(payload).encode()))
    d = md.fetch_chart("X.NS")
    assert d["price"] == 123.4 and d["points"] == [(1, 1.0), (3, 3.0)] and d["as_of"] == 1700000000


def test_fetch_retries_other_host(monkeypatch):
    seen = []
    payload = {"chart": {"result": [{"meta": {"regularMarketPrice": 5}, "timestamp": [1], "indicators": {"quote": [{"close": [5.0]}]}}]}}

    def fake(req, timeout=0):
        seen.append(req.full_url.split("/")[2])
        if len(seen) == 1:
            raise OSError("429")
        return io.BytesIO(json.dumps(payload).encode())
    monkeypatch.setattr(md.urllib.request, "urlopen", fake)
    monkeypatch.setattr(md.time, "sleep", lambda s: None)
    assert md.fetch_chart("X.NS")["price"] == 5
    assert seen == ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]


def test_benchmarks_use_real_history_when_available(live):
    prices = dict(ALL)
    prices[md.BENCH_NIFTY] = (100.0, 150.0)
    live.setattr(md, "fetch_chart", fake_chart_factory(prices))
    b = benchmarks.build(30, 5, 24)
    assert b["live"] and b["sources"]["nifty50"].startswith("Yahoo Finance")
    n = b["series"]
    assert n[0]["nifty50_pre"] == 100 and n[-1]["nifty50_pre"] > 100
    assert len(n) == 25
    # linear 100 -> 150 over 261 weeks; 24 months back is ~104.35 weeks, so the price ratio is 150 / (150 - 50 * 104.35 / 261)
    ratio = 150 / (150 - 50 * (24 * 30.4375 / 7) / 261)
    assert n[-1]["nifty50_pre"] / 100 == pytest.approx((1.013 ** 2) * ratio, rel=0.01)


def test_benchmarks_gsec_falls_back_when_etf_history_short(live):
    prices = dict(ALL)
    prices[md.BENCH_GSEC] = (100.0, 110.0, 60)     # ~14 months of history
    live.setattr(md, "fetch_chart", fake_chart_factory(prices))
    b = benchmarks.build(30, 5, 36)
    assert b["sources"]["gsec_index"] == "Simulated (demo)" and b["sources"]["nifty50"].startswith("Yahoo")
    assert benchmarks.build(30, 5, 12)["sources"]["gsec_index"].startswith("Yahoo")


def test_twin_tracker_flag(live):
    live.setattr(md, "fetch_chart", fake_chart_factory(ALL))
    t = twin.build(30, 5, 15)
    assert t["tracker_live"] and len(t["tracker"]) == 13 and t["tracker"][0]["you"] == 100


# ---------------- OpenRouter ----------------
class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def llm_reply(text):
    return FakeResp(json.dumps({"choices": [{"message": {"content": text}}]}).encode())


@pytest.fixture
def keyed(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-123")
    monkeypatch.setenv("OPENROUTER_MODEL", "test/model")
    return monkeypatch


def test_no_key_uses_rules():
    r = explain.answer("why is it lower", "en")
    assert r["engine"] == "rules" and "model" not in r


def test_llm_request_shape_and_grounding(keyed):
    sent = {}

    def fake(req, timeout=0):
        sent["url"] = req.full_url
        sent["headers"] = {k.lower(): v for k, v in req.header_items()}
        sent["body"] = json.loads(req.data)
        return llm_reply("Your real value is lower because of tax and inflation.")
    keyed.setattr(llm.urllib.request, "urlopen", fake)
    r = explain.answer("why is it lower", "hi", 20, 6, [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi!"}])
    assert r["engine"] == "llm" and r["model"] == "test/model" and r["answer"].startswith("Your real value")
    assert sent["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert sent["headers"]["authorization"] == "Bearer sk-or-test-123" and sent["headers"]["x-title"] == "TrackFolio"
    b = sent["body"]
    assert b["model"] == "test/model" and b["temperature"] <= 0.5 and b["max_tokens"] <= 600
    roles = [m["role"] for m in b["messages"]]
    assert roles == ["system", "system", "user", "assistant", "user"]
    facts = json.loads(b["messages"][1]["content"].split("\n", 1)[1])
    assert facts["user_settings"] == {"tax_slab_pct": 20, "inflation_pct": 6}
    assert facts["totals"]["app_value"] == round(engine.analyse(20, 6)["totals"]["app_value"])
    assert len(facts["holdings"]) == 11 and "best_risk_adjusted_asset_at_your_slab" in facts
    assert "Hindi" in b["messages"][-1]["content"] and "why is it lower" in b["messages"][-1]["content"]
    assert "sk-or" not in json.dumps(b)             # the key never goes into the prompt


def test_llm_failures_fall_back_to_rules(keyed):
    for exc in (OSError("down"), ValueError("bad")):
        keyed.setattr(llm.urllib.request, "urlopen", lambda req, timeout=0, e=exc: (_ for _ in ()).throw(e))
        r = explain.answer("why is it lower", "en")
        assert r["engine"] == "rules" and "LLM unavailable" in r["note"] and "real terms" in r["answer"]
    keyed.setattr(llm.urllib.request, "urlopen", lambda req, timeout=0: llm_reply("   "))
    assert explain.answer("why", "en")["engine"] == "rules"
    keyed.setattr(llm.urllib.request, "urlopen", lambda req, timeout=0: FakeResp(b'{"error":{"message":"no credits"}}'))
    assert explain.answer("why", "en")["engine"] == "rules"


def test_history_is_trimmed_and_sanitised(keyed):
    sent = {}
    keyed.setattr(llm.urllib.request, "urlopen", lambda req, timeout=0: (sent.update(b=json.loads(req.data)), llm_reply("ok"))[1])
    hist = [{"role": "user", "content": "q%d" % i} for i in range(20)] + [{"role": "system", "content": "evil"}, {"role": "user", "content": "x" * 5000}]
    explain.answer("final", "en", 30, 5, hist)
    msgs = sent["b"]["messages"]
    assert len(msgs) == 2 + 6 + 1 and all(m["content"] != "evil" for m in msgs)
    assert all(len(m["content"]) <= 700 for m in msgs[2:])


def test_dotenv_loader_does_not_override(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text('# c\nFOO_TEST_KEY="abc"\nEXISTING_TEST=new\n', encoding="utf-8")
    monkeypatch.setattr(llm, "ROOT", tmp_path)
    monkeypatch.setenv("EXISTING_TEST", "old")
    monkeypatch.delenv("FOO_TEST_KEY", raising=False)
    llm._load_dotenv()
    import os
    assert os.environ["FOO_TEST_KEY"] == "abc" and os.environ["EXISTING_TEST"] == "old"


# ---------------- HTTP ----------------
def test_status_endpoint(keyed, live):
    live.setattr(md, "fetch_chart", fake_chart_factory(ALL))
    s = c.get("/api/py/status").json()
    assert s["llm"] == {"provider": "OpenRouter", "enabled": True, "model": "test/model"}
    assert s["market_data"]["enabled"] and s["market_data"]["symbols_live"] > 9 and s["market_data"]["as_of"]
    assert "sk-or" not in json.dumps(s)


def test_status_without_key():
    s = c.get("/api/py/status").json()
    assert s["llm"]["enabled"] is False and s["llm"]["model"] is None and s["market_data"]["enabled"] is False


def test_explain_endpoint_validation_and_llm(keyed):
    keyed.setattr(llm.urllib.request, "urlopen", lambda req, timeout=0: llm_reply("Hello from the model"))
    r = c.post("/api/py/explain", json={"question": "why", "lang": "mr", "history": [{"role": "user", "content": "a"}]}).json()
    assert r["engine"] == "llm" and r["answer"] == "Hello from the model"
    assert c.post("/api/py/explain", json={"question": ""}).status_code == 422
    assert c.post("/api/py/explain", json={"question": "x" * 401}).status_code == 422
    assert c.post("/api/py/explain", json={"question": "a", "history": [{"role": "user", "content": "b"}] * 13}).status_code == 422


def test_portfolio_endpoint_exposes_data_source(live):
    live.setattr(md, "fetch_chart", fake_chart_factory(ALL))
    p = c.get("/api/py/portfolio").json()
    assert p["data_source"]["live"] and p["data_source"]["provider"] == "Yahoo Finance" and p["data_source"]["as_of"]
    assert all("live" in h for h in p["holdings"])
    assert len(LOTS) == 13
