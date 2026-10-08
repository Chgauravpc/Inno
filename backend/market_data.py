"""Live market data from Yahoo Finance's public chart endpoint (stdlib only, so it stays small on Vercel).

One snapshot = 5y of weekly closes for every ticker we use, fetched in parallel and cached for 15 minutes.
Anything that fails falls back to demo values, and the API says which symbols were live.
"""
from __future__ import annotations

import json
import os
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .data import YF

HOSTS = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]
UA = {"User-Agent": "Mozilla/5.0 (TrackFolio demo)"}
TTL = 900
RETRY_AFTER = 60
DEADLINE = 7.0
BENCH_NIFTY = "^NSEI"
BENCH_GSEC = "GSEC10IETF.NS"
REIT_BASKET = ["EMBASSY.NS", "MINDSPACE.NS", "IRBINVIT.NS", "PGINVIT.NS"]

_lock = threading.Lock()
_cache: Dict[str, object] = {"ts": 0.0, "ttl": TTL, "data": None}


def enabled() -> bool:
    return os.environ.get("LIVE_DATA", "1") != "0"


def _get(sym: str, rng: str, interval: str, timeout: float) -> dict:
    last: Exception = RuntimeError("no attempt")
    for attempt in range(3):
        host = HOSTS[attempt % len(HOSTS)]
        url = f"https://{host}/v8/finance/chart/{urllib.parse.quote(sym, safe='')}?range={rng}&interval={interval}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return json.load(r)["chart"]["result"][0]
        except Exception as e:  # 429 / timeouts: back off and try the other host
            last = e
            time.sleep(0.5 * (attempt + 1))
    raise last


def fetch_chart(sym: str, rng: str = "5y", interval: str = "1wk", timeout: float = 4.0) -> dict:
    res = _get(sym, rng, interval, timeout)
    closes = res["indicators"]["quote"][0].get("close") or []
    pts = [(int(t), float(c)) for t, c in zip(res.get("timestamp") or [], closes) if c is not None]
    meta = res.get("meta", {})
    price = meta.get("regularMarketPrice") or (pts[-1][1] if pts else None)
    if not price:
        raise ValueError("no price")
    return dict(price=float(price), as_of=int(meta.get("regularMarketTime") or (pts[-1][0] if pts else time.time())), points=pts)


def _all_symbols() -> List[str]:
    return sorted(set(YF.values()) | {BENCH_NIFTY, BENCH_GSEC} | set(REIT_BASKET))


def snapshot() -> Dict[str, dict]:
    if not enabled():
        return {}
    with _lock:
        age = time.time() - float(_cache["ts"])  # type: ignore[arg-type]
        if _cache["data"] is not None and age < float(_cache["ttl"]):  # type: ignore[arg-type]
            return _cache["data"]  # type: ignore[return-value]

        syms = _all_symbols()
        got: Dict[str, dict] = {}
        ex = ThreadPoolExecutor(max_workers=4)
        futs = {ex.submit(fetch_chart, sym): sym for sym in syms}
        done, _ = wait(futs, timeout=DEADLINE)
        for f in done:
            try:
                got[futs[f]] = f.result()
            except Exception:
                pass
        ex.shutdown(wait=False, cancel_futures=True)  # slow stragglers fall back to demo values
        _cache["data"] = got
        _cache["ts"] = time.time()
        _cache["ttl"] = TTL if len(got) == len(syms) else RETRY_AFTER
        return got


def clear_cache() -> None:
    with _lock:
        _cache.update(ts=0.0, ttl=TTL, data=None)


def value_at(points: List[Tuple[int, float]], ts: float) -> Optional[float]:
    """Last close at or before ts; None if the series starts later (instrument not listed yet)."""
    best = None
    for t, c in points:
        if t <= ts:
            best = c
        else:
            break
    return best


def price(sym: str, default: float) -> Tuple[float, bool]:
    yf = YF.get(sym)
    s = snapshot().get(yf) if yf else None
    return (s["price"], True) if s else (default, False)


def buy_price(sym: str, days_ago: float) -> Optional[float]:
    """Real close on the purchase date, if Yahoo has history that far back."""
    yf = YF.get(sym)
    s = snapshot().get(yf) if yf else None
    if not s:
        return None
    ts = time.time() - days_ago * 86400
    if not s["points"] or ts < s["points"][0][0] - 7 * 86400:
        return None
    return value_at(s["points"], ts)


def iso(ts: Optional[float]) -> Optional[str]:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="minutes") if ts else None


def as_of() -> Optional[str]:
    snap = snapshot()
    used = [snap[y]["as_of"] for y in YF.values() if y in snap]
    return iso(max(used)) if used else None


def index_ratios(months: int) -> Dict[str, List[float]]:
    """Price ratios (start = 1.0), one per month, for the three benchmark classes over the last `months`.
    Classes without enough real history are left out; the caller falls back to simulated paths."""
    snap = snapshot()
    now = time.time()
    steps = [now - (months - m) * 30.4375 * 86400 for m in range(months + 1)]
    out: Dict[str, List[float]] = {}

    def single(sym: str) -> Optional[List[float]]:
        s = snap.get(sym)
        if not s:
            return None
        base = value_at(s["points"], steps[0])
        if not base:
            return None
        vals = [value_at(s["points"], t) if m < months else s["price"] for m, t in enumerate(steps)]
        if any(v is None for v in vals):
            return None
        return [v / base for v in vals]  # type: ignore[operator]

    n = single(BENCH_NIFTY)
    if n:
        out["nifty50"] = n
    g = single(BENCH_GSEC)
    if g:
        out["gsec_index"] = g
    basket = [r for r in (single(s) for s in REIT_BASKET) if r]
    if basket:
        out["reit_invit_index"] = [sum(b[i] for b in basket) / len(basket) for i in range(months + 1)]
    return out
