"""Asset-class assumptions (illustrative, long-run) used by comparisons, the twin and the market simulator."""

ASSETS = {
    "nifty50": dict(label="Nifty 50 stocks", price_g=0.115, yld=0.013, taxable=1.0, cg="112a", vol=0.16),
    "reit": dict(label="REITs", price_g=0.030, yld=0.075, taxable=0.9, cg="112a", vol=0.11),
    "invit": dict(label="InvITs", price_g=0.010, yld=0.100, taxable=0.9, cg="112a", vol=0.09),
    "gsec": dict(label="G-Sec / bonds (7.5%)", price_g=0.0, yld=0.075, taxable=1.0, cg="debt", vol=0.03),
    "fd": dict(label="Bank FD (7%)", price_g=0.0, yld=0.070, taxable=1.0, cg="none", vol=0.0),
    # broad indices used as benchmarks and as the three twin building blocks
    "reit_invit_index": dict(label="Nifty REITs & InvITs", price_g=0.030, yld=0.080, taxable=0.9, cg="112a", vol=0.10),
    "gsec_index": dict(label="G-Sec index", price_g=0.0, yld=0.072, taxable=1.0, cg="debt", vol=0.03),
}

BENCHMARK_FOR = {"EQUITY": "nifty50", "REIT": "reit_invit_index", "INVIT": "reit_invit_index", "BOND": "gsec_index"}
CLASS_FOR = {"EQUITY": "nifty50", "REIT": "reit_invit_index", "INVIT": "reit_invit_index", "BOND": "gsec_index"}
TWIN_CLASSES = ["nifty50", "reit_invit_index", "gsec_index"]
CORR = {
    ("nifty50", "reit_invit_index"): 0.5,
    ("nifty50", "gsec_index"): 0.1,
    ("reit_invit_index", "gsec_index"): 0.2,
}


def corr(a: str, b: str) -> float:
    if a == b:
        return 1.0
    return CORR.get((a, b), CORR.get((b, a), 0.0))
