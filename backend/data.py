"""Demo investor 'Priya Sharma' as returned by a sandbox Account Aggregator fetch.

All figures are illustrative demo data, not live market data or advice.
Lots are per broker, per purchase; the engine merges them by ISIN.
"""

PROFILE = {
    "name": "Priya Sharma",
    "age": 34,
    "city": "Pune",
    "slab": 30,
    "pan_masked": "ABCPS••••K",
    "consent": {"provider": "Sandbox AA (demo)", "scope": "Read-only holdings", "valid_days": 90},
}

BROKERS = ["Zerodha", "Groww", "Angel One"]

# symbol, name, isin, type, income/unit/yr, price
SECURITIES = {
    "RELIANCE": dict(name="Reliance Industries", isin="INE002A01018", type="EQUITY", income=10.0, price=1420.0),
    "TCS": dict(name="Tata Consultancy Services", isin="INE467B01029", type="EQUITY", income=60.0, price=3980.0),
    "HDFCBANK": dict(name="HDFC Bank", isin="INE040A01034", type="EQUITY", income=22.0, price=1710.0),
    "INFY": dict(name="Infosys", isin="INE009A01021", type="EQUITY", income=43.0, price=1610.0),
    "ITC": dict(name="ITC Ltd", isin="INE154A01025", type="EQUITY", income=14.0, price=468.0),
    "EMBASSY": dict(name="Embassy Office Parks REIT", isin="DEMO0REIT001", type="REIT", income=25.0, price=402.0),
    "MINDSPACE": dict(name="Mindspace Business Parks REIT", isin="DEMO0REIT002", type="REIT", income=25.5, price=372.0),
    "IRBINVIT": dict(name="IRB InvIT Fund", isin="DEMO0INVT001", type="INVIT", income=6.5, price=68.0),
    "PGINVIT": dict(name="Powergrid Infrastructure InvIT", isin="DEMO0INVT002", type="INVIT", income=9.5, price=93.0),
    "GS2033": dict(name="7.18% G-Sec 2033", isin="DEMO0GSEC001", type="BOND", income=7.18, price=103.0),
    "RECNCD": dict(name="REC Ltd 7.5% NCD", isin="DEMO0BOND001", type="BOND", income=75.0, price=1018.0),
}

# symbol, broker, qty, avg buy price, days held
LOTS = [
    ("RELIANCE", "Zerodha", 80, 880.0, 1500),
    ("RELIANCE", "Groww", 40, 1260.0, 520),
    ("TCS", "Groww", 45, 2900.0, 1600),
    ("HDFCBANK", "Zerodha", 200, 1250.0, 1000),
    ("INFY", "Angel One", 90, 1520.0, 190),
    ("ITC", "Groww", 400, 330.0, 1300),
    ("ITC", "Zerodha", 150, 455.0, 300),
    ("EMBASSY", "Zerodha", 300, 330.0, 1000),
    ("MINDSPACE", "Angel One", 150, 300.0, 800),
    ("IRBINVIT", "Groww", 2000, 50.0, 900),
    ("PGINVIT", "Zerodha", 1500, 78.0, 700),
    ("GS2033", "Zerodha", 300, 101.0, 700),
    ("RECNCD", "Angel One", 100, 1000.0, 430),
]

# Illustrative "what you actually own" factors (per unit)
OWNERSHIP = {
    "EMBASSY": dict(kind="office", per_unit=0.045, unit="sq ft of Grade-A office space"),
    "MINDSPACE": dict(kind="office", per_unit=0.056, unit="sq ft of Grade-A office space"),
    "IRBINVIT": dict(kind="road", per_unit=0.004, unit="metres of toll highway"),
    "PGINVIT": dict(kind="power", per_unit=0.0025, unit="metres of transmission line"),
}

# Yahoo Finance tickers (bonds have none and stay on demo values)
YF = {
    "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS", "HDFCBANK": "HDFCBANK.NS", "INFY": "INFY.NS", "ITC": "ITC.NS",
    "EMBASSY": "EMBASSY.NS", "MINDSPACE": "MINDSPACE.NS", "IRBINVIT": "IRBINVIT.NS", "PGINVIT": "PGINVIT.NS",
}
