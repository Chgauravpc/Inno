"""Versioned tax rules. Update once per Union Budget; engine reads only from here."""

RULES = {
    "version": "FY2026-27 (Income Tax Act, 2025)",
    "cess": 0.04,
    "ltcg_rate": 0.125,            # listed shares, equity MFs, REIT/InvIT units, listed bonds (no indexation)
    "ltcg_exemption_112a": 125000,  # per year, equity-like assets only
    "stcg_rate_112a": 0.20,         # listed equity-like assets held < 12 months
    "long_term_days": 365,
    "stt_sell": 0.001,              # delivery sell side, not charged on bonds
    "other_charges": 0.00012,       # exchange, SEBI, stamp, GST on charges (approx.)
    "slabs": [0, 5, 10, 15, 20, 30],
    "default_inflation": 5.0,
}


def slab_rate(slab_pct: float) -> float:
    """Marginal slab rate including health & education cess."""
    return slab_pct / 100.0 * (1 + RULES["cess"])
