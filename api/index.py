import os
import sys
import time
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Query  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from backend import benchmarks, data, engine, explain, llm, twin
from backend import market_data  # noqa: E402
from backend.tax_rules import RULES  # noqa: E402

app = FastAPI(title="TrackFolio API", version="0.1.0",
              docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")


class Turn(BaseModel):
    role: str
    content: str


class Ask(BaseModel):
    question: str = Field(min_length=1, max_length=400)
    history: List[Turn] = Field(default_factory=list, max_length=12)
    lang: str = "en"
    slab: float = 30
    inflation: float = 5.0


class Consent(BaseModel):
    provider: Optional[str] = "sandbox-aa"


@app.get("/api/py/health")
def health():
    return {"status": "ok", "team": "Innovisionaries", "rules": RULES["version"], "ts": int(time.time())}


@app.get("/api/py/status")
def status():
    snap = market_data.snapshot()
    return {"market_data": {"provider": "Yahoo Finance", "enabled": market_data.enabled(), "symbols_live": len(snap),
                            "as_of": market_data.as_of()},
            "llm": {"provider": "OpenRouter", "enabled": llm.enabled(), "model": llm.model() if llm.enabled() else None}}


@app.get("/api/py/profile")
def profile():
    return {**data.PROFILE, "brokers": data.BROKERS, "slabs": RULES["slabs"]}


@app.post("/api/py/connect/consent")
def consent(body: Consent):
    return {"consent_id": "demo-consent-7f3a", "status": "ACTIVE", "scope": "Read-only holdings",
            "fips": ["NSDL", "CDSL"], "valid_days": 90, "sandbox": True}


@app.get("/api/py/connect/fetch")
def fetch():
    a = engine.analyse()
    return {"sandbox": True, "depositories": ["NSDL", "CDSL"], "brokers": a["brokers"],
            "lots": a["stats"]["lots"], "holdings": a["stats"]["holdings"],
            "duplicates_merged": a["stats"]["duplicates_merged"], "value": a["totals"]["app_value"]}


@app.get("/api/py/portfolio")
def portfolio(slab: float = Query(30, ge=0, le=30), inflation: float = Query(5.0, ge=0, le=15)):
    return engine.analyse(slab, inflation)


@app.get("/api/py/benchmarks")
def bench(slab: float = Query(30, ge=0, le=30), inflation: float = Query(5.0, ge=0, le=15),
          months: int = Query(36, ge=12, le=60)):
    return benchmarks.build(slab, inflation, months)


@app.get("/api/py/slab")
def slab_compare(inflation: float = Query(5.0, ge=0, le=15)):
    return engine.slab_matrix(inflation)


@app.get("/api/py/twin")
def portfolio_twin(slab: float = Query(30, ge=0, le=30), inflation: float = Query(5.0, ge=0, le=15),
                   shift: float = Query(15, ge=10, le=20)):
    return twin.build(slab, inflation, shift)


@app.get("/api/py/example")
def example(amount: float = Query(500000, ge=10000, le=100000000), growth: float = Query(12, ge=0, le=40),
            years: int = Query(5, ge=1, le=30), inflation: float = Query(5.0, ge=0, le=15)):
    return engine.example_stock(amount, growth, years, inflation)


@app.get("/api/py/ownership")
def own(slab: float = Query(30, ge=0, le=30), inflation: float = Query(5.0, ge=0, le=15)):
    return engine.ownership(slab, inflation)


@app.post("/api/py/explain")
def ask(body: Ask):
    return explain.answer(body.question, body.lang, body.slab, body.inflation, [t.model_dump() for t in body.history])
